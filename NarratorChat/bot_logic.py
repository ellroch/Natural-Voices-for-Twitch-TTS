### bot_logic.py
import threading
import time
import traceback
import pythoncom
import socket
import hashlib
import win32com.client as wincl
import re
from .config import log_service_message, load_config

TWITCH_HOST = "irc.chat.twitch.tv"
TWITCH_PORT = 6667


def apply_substitutions(text: str) -> str:
    cfg = load_config()
    for rule in cfg.get("substitutions", []):
        try:
            text = re.sub(rule["pattern"], rule["replacement"], text, flags=re.IGNORECASE)
        except re.error as e:
            log_service_message(f"Regex error in substitution rule: {e}")
    return text


def stable_hash(username: str) -> int:
    md5_hex = hashlib.md5(username.encode("utf-8")).hexdigest()
    return int(md5_hex, 16)

class TwitchBot:
    def __init__(self, shutdown_event: threading.Event):
        self.shutdown_event = shutdown_event
        self.config = load_config()
        self.tts_enabled = self.config.get("tts_enabled", True)
        self.socket: socket.socket | None = None
        self.connected = False
        self.natural_voices: list = []
        self.voice_index_shift = self.config.get("voice_index", 0)
        self.user_voice_map: dict[str, any] = {}
        self.listen_thread: threading.Thread | None = None

    def start(self):
        log_service_message("TwitchBot starting")
        try:
            log_service_message("Calling pythoncom.CoInitialize")
            pythoncom.CoInitialize()
        except Exception as e:
            log_service_message(f"CoInitialize error: {e}")
        self.config = load_config()
        self.tts_enabled = self.config.get("tts_enabled", True)
        self._setup_tts()
        self._connect_to_twitch()
        if self.connected:
            self._start_listening()

    def _setup_tts(self):
        try:
            probe = wincl.Dispatch("SAPI.SpVoice")
            voices = probe.GetVoices()
            naturals = [v for v in voices if "(Natural)" in v.GetDescription()]
            self.natural_voices = naturals or list(voices)
            log_service_message(f"Loaded {len(self.natural_voices)} voices")
        except Exception as e:
            log_service_message(f"TTS setup failed: {e}")
            self.natural_voices = []

    def _connect_to_twitch(self):
        try:
            self.socket = socket.socket()
            self.socket.connect((TWITCH_HOST, TWITCH_PORT))
            self.socket.sendall(f"PASS {self.config['irc']['oauth']}\r\n".encode())
            self.socket.sendall(f"NICK {self.config['irc']['username']}\r\n".encode())
            self.socket.sendall(f"JOIN {self.config['irc']['channel']}\r\n".encode())
            self.connected = True
            log_service_message(f"Connected to {self.config['irc']['channel']}")
        except Exception as e:
            log_service_message(f"Connection/Auth failed: {e}")
            self.connected = False

    def _start_listening(self):
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()

    def _listen_loop(self):
        buffer = ""
        while not self.shutdown_event.is_set():
            try:
                data = self.socket.recv(2048).decode("utf-8", errors="ignore")
            except Exception as e:
                log_service_message(f"Socket recv error: {e}")
                break
            buffer += data
            lines = buffer.split("\r\n")
            buffer = lines.pop()
            for line in lines:
                try:
                    if line.startswith("PING"):
                        self.socket.sendall("PONG :tmi.twitch.tv\r\n".encode())
                        continue
                    if "PRIVMSG" in line:
                        prefix, _, msg = line.partition("PRIVMSG")
                        raw_user = prefix.lstrip(":").split("!")[0]
                        chat_text = msg.split(" :", 1)[1] if " :" in msg else ""
                        chat_text = apply_substitutions(chat_text)
                        if raw_user.lower() == self.config["irc"]["username"].lower():
                            continue
                        if raw_user not in self.user_voice_map and self.natural_voices:
                            idx = (stable_hash(raw_user) + self.voice_index_shift) % len(self.natural_voices)
                            voice = self.natural_voices[idx]
                            inst = wincl.Dispatch("SAPI.SpVoice")
                            inst.Voice = voice
                            self.user_voice_map[raw_user] = inst
                        if load_config().get("tts_enabled", True):
                            self.user_voice_map[raw_user].Speak(chat_text)
                except Exception:
                    log_service_message("Error in message handling: " + traceback.format_exc())
        self._cleanup()

    def reconnect(self):
        log_service_message("Reconnecting TwitchBot...")
        self.shutdown_event.set()
        if self.listen_thread:
            self.listen_thread.join(timeout=5)
        time.sleep(2)
        self.shutdown_event.clear()
        self.user_voice_map.clear()
        self.start()

    def _cleanup(self):
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                log_service_message(f"Socket close error: {e}")
        try:
            log_service_message("Calling pythoncom.CoUninitialize")
            pythoncom.CoUninitialize()
        except Exception as e:
            log_service_message(f"CoUninitialize error: {e}")
        log_service_message("Bot loop exiting")


def test_all_voices():
    try:
        pythoncom.CoInitialize()
        probe = wincl.Dispatch("SAPI.SpVoice")
        voices = probe.GetVoices()
        for idx, v in enumerate(voices, 1):
            desc = v.GetDescription()
            probe.Voice = v
            probe.Speak("Testing voice functionality.")
            print(f"Tested voice {idx}: {desc}")
    except Exception as e:
        log_service_message(f"Voice test failed: {e}")
    finally:
        try:
            pythoncom.CoUninitialize()
        except:
            pass


def main_bot_loop(shutdown_event: threading.Event):
    bot = TwitchBot(shutdown_event)
    bot.start()
    shutdown_event.wait()
    bot._cleanup()