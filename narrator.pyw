import sys
import socket
import threading
import hashlib
import pythoncom
import win32com.client as wincl

import pystray
from pystray import MenuItem as item
from PIL import Image
import os

# =======================
# Configuration
# =======================
TWITCH_HOST = "irc.chat.twitch.tv"
TWITCH_PORT = 6667

TWITCH_OAUTH    = "oauth:xxxxxxxxxxxxxxxxxx"  # e.g. "oauth:abcd1234..." --- this is the "access code" from https://twitchtokengenerator.com/ on your bot account prefixed with "oauth:"
TWITCH_USERNAME = "your_bot_username"       # e.g. "myBot"
TWITCH_CHANNEL  = "#your_channel_name"      # Must include '#'

VOICE_INDEX_SHIFT = 10  # Shift the voice index by this amount to change the voice assignment

# Ensure the file path is correct
icon_path = os.path.join(os.path.dirname(__file__), "Asset 3@4x.ico")

# Verify the image is being loaded correctly
try:
    icon_image = Image.open(icon_path)
    print(f"Icon image loaded successfully from {icon_path}")
except Exception as e:
    print(f"[Error] Could not load icon image: {e}")
    icon_image = Image.new('RGBA', (16, 16), (0, 0, 0, 0))  # Create a transparent image as a fallback

def stable_hash(username: str) -> int:
    md5_hex = hashlib.md5(username.encode("utf-8")).hexdigest()
    return int(md5_hex, 16)

def create_tray_icon(shutdown_event):
    """
    Creates a system tray icon with an 'Exit' menu item.
    When 'Exit' is clicked, we signal the main thread to shut down.
    """
    def on_exit_clicked(icon, _):
        """
        Called when the user clicks 'Exit' in the tray menu.
        We stop the icon and set the shutdown event for the main loop.
        """
        icon.stop()  # removes the tray icon
        shutdown_event.set()

    menu = (item('Exit', on_exit_clicked),)
    icon = pystray.Icon("TTS_Bot", icon_image, "TTS Bot", pystray.Menu(*menu))
    return icon

def tray_icon_thread(shutdown_event):
    """
    Runs the tray icon in this background thread.
    """
    icon = create_tray_icon(shutdown_event)
    icon.run()

def main_bot_loop(shutdown_event):
    """
    The main Twitch bot logic goes here. 
    We continuously read chat and speak messages, 
    but we also regularly check if 'shutdown_event' is set.
    """
    pythoncom.CoInitialize()

    # Create SAPI voice object
    voice = wincl.Dispatch("SAPI.SpVoice")

    # Filter for "(Natural)" voices
    all_voices = voice.GetVoices()
    natural_voices = [v for v in all_voices if "(Natural)" in v.GetDescription()]
    if not natural_voices:
        print("[Error] No '(Natural)' voices found.")
        pythoncom.CoUninitialize()
        return

    user_voice_map = {}

    # Attempt to connect to Twitch
    try:
        s = socket.socket()
        print(f"Connecting to Twitch IRC at {TWITCH_HOST}:{TWITCH_PORT}...")
        s.connect((TWITCH_HOST, TWITCH_PORT))
    except Exception as e:
        print(f"[Error] Could not connect: {e}")
        pythoncom.CoUninitialize()
        return

    try:
        s.sendall(f"PASS {TWITCH_OAUTH}\r\n".encode("utf-8"))
        s.sendall(f"NICK {TWITCH_USERNAME}\r\n".encode("utf-8"))
        s.sendall(f"JOIN {TWITCH_CHANNEL}\r\n".encode("utf-8"))
    except Exception as e:
        print(f"[Error] Auth error: {e}")
        s.close()
        pythoncom.CoUninitialize()
        return

    print(f"Joined {TWITCH_CHANNEL}. Bot is running...")

    try:
        while not shutdown_event.is_set():
            # Non-blocking read with a small timeout or check
            s.settimeout(0.5)
            try:
                raw_data = s.recv(2048)
            except socket.timeout:
                # No data received in this interval, check event again
                continue

            if not raw_data:
                print("[Error] Connection lost or closed by server.")
                break

            raw_response = raw_data.decode("utf-8", errors="ignore")

            for line in raw_response.split("\r\n"):
                line = line.strip()
                if not line:
                    continue

                # Respond to PING
                if line.startswith("PING"):
                    s.sendall("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
                    continue

                if "PRIVMSG" in line:
                    # e.g. :username!username@username.tmi.twitch.tv PRIVMSG #channel :Hello
                    user_and_host, _, msg_content = line.partition("PRIVMSG")
                    raw_user = user_and_host.lstrip(":").split("!")[0]
                    parts = msg_content.split(" :")
                    chat_text = parts[1] if len(parts) > 1 else ""

                    # Assign a voice for this user if not already
                    if raw_user not in user_voice_map:
                        idx = (stable_hash(raw_user) + VOICE_INDEX_SHIFT) % len(natural_voices)
                        user_voice_map[raw_user] = natural_voices[idx]

                    voice.Voice = user_voice_map[raw_user]
                    print(f"Speaking as {raw_user} with voice {voice.Voice.GetDescription()}: {chat_text}")
                    voice.Speak(chat_text)

    except KeyboardInterrupt:
        print("\n[Info] Bot interrupted via keyboard.")
    finally:
        # Clean up
        s.close()
        pythoncom.CoUninitialize()
        print("Bot has shut down.")

def main():
    # 1) Create an Event to signal shutdown
    shutdown_event = threading.Event()

    # 2) Launch tray icon in a separate thread
    tray_thread = threading.Thread(target=tray_icon_thread, args=(shutdown_event,), daemon=True)
    tray_thread.start()

    # 3) Run the main bot loop
    main_bot_loop(shutdown_event)

    # 4) Once the bot loop ends, if the tray is still running, we can stop it
    shutdown_event.set()  # signal tray to close
    print("Main function exit.")

if __name__ == "__main__":
    main()
