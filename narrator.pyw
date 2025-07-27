import sys
import io
import socket
import threading
import hashlib
import pythoncom
import win32com.client as wincl

import pystray
from pystray import MenuItem as item
from PIL import Image
import os

# Set stdout to use UTF-8 encoding to handle special characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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

def test_all_voices():
    """
    Iterates over all available voices and tests them by speaking a predefined message.
    This helps identify any problematic voices before the bot starts.
    """
    pythoncom.CoInitialize()
    try:
        voice_probe = wincl.Dispatch("SAPI.SpVoice")
        all_voices = voice_probe.GetVoices()
        test_message = "Testing voice functionality."

        print("Starting voice test...")
        for i, voice in enumerate(all_voices):
            try:
                try:
                    description = voice.GetDescription()
                except Exception as e:
                    description = f"Unknown (Error: {e})"
                voice_probe.Voice = voice
                print(f"Testing voice {i + 1}/{len(all_voices)}: {description}")
                voice_probe.Speak(test_message)
            except Exception as e:
                print(f"[Error] Voice {i + 1} ({description}) failed: {e}")
        print("Voice test completed.")
    finally:
        pythoncom.CoUninitialize()

def main_bot_loop(shutdown_event):
    """
    The main Twitch bot logic goes here. 
    We continuously read chat and speak messages, 
    but we also regularly check if 'shutdown_event' is set.
    """
    pythoncom.CoInitialize()

    # Temp voice object to get available voices
    voice_probe = wincl.Dispatch("SAPI.SpVoice")
    all_voices = voice_probe.GetVoices()
    natural_voices = [v for v in all_voices if "(Natural)" in v.GetDescription()]
    if not natural_voices:
        print("[Error] No '(Natural)' voices found. Using default voices.")
        natural_voices = all_voices  # Fallback to all available voices

    # This dict maps raw_user -> (voice_token, voice_instance)
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
            s.settimeout(0.5)
            try:
                raw_data = s.recv(2048)
            except socket.timeout:
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
                    user_and_host, _, msg_content = line.partition("PRIVMSG")
                    raw_user = user_and_host.lstrip(":").split("!")[0]
                    parts = msg_content.split(" :")
                    chat_text = parts[1] if len(parts) > 1 else ""

                    # Skip messages from the bot/streamer account
                    if raw_user.lower() == TWITCH_USERNAME.lower():
                        continue

                    # Assign a voice and voice instance for this user if not already
                    if raw_user not in user_voice_map:
                        if len(natural_voices) > 0:
                            idx = (stable_hash(raw_user) + VOICE_INDEX_SHIFT) % len(natural_voices)
                            voice_token = natural_voices[idx]
                            user_voice_instance = wincl.Dispatch("SAPI.SpVoice")
                            user_voice_instance.Voice = voice_token
                            user_voice_map[raw_user] = (voice_token, user_voice_instance)
                        else:
                            print("[Error] No voices available to assign.")
                            continue  # Skip processing this user

                    voice_token, user_voice_instance = user_voice_map[raw_user]
                    print(f"Speaking as {raw_user} with voice {voice_token.GetDescription()}: {chat_text}")
                    
                    try:
                        user_voice_instance.Speak(chat_text)
                    except Exception as e:
                        print(f"[Error] Failed to speak message for {raw_user}: {e}")

    except KeyboardInterrupt:
        print("\n[Info] Bot interrupted via keyboard.")
    finally:
        s.close()
        pythoncom.CoUninitialize()
        print("Bot has shut down.")

def main():
    # 1) Test all voices at startup
    # test_all_voices()

    # 2) Create an Event to signal shutdown
    shutdown_event = threading.Event()

    # 3) Launch tray icon in a separate thread
    tray_thread = threading.Thread(target=tray_icon_thread, args=(shutdown_event,), daemon=True)
    tray_thread.start()

    # 4) Run the main bot loop
    main_bot_loop(shutdown_event)

    # 5) Once the bot loop ends, if the tray is still running, we can stop it
    shutdown_event.set()  # signal tray to close
    print("Main function exit.")

if __name__ == "__main__":
    main()
