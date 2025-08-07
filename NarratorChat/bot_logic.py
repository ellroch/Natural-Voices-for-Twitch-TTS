# bot_logic.py
import os
import json
import threading
import time
import traceback
import pythoncom
import socket
import hashlib
import win32com.client as wincl
import re
from datetime import datetime
from .config import log_service_message, load_config, load_assigned_voices

TWITCH_HOST = "irc.chat.twitch.tv"
TWITCH_PORT = 6667

def apply_substitutions(text: str) -> str:
    for rule in load_config().get("substitutions", []):
        try:
            text = re.sub(rule["pattern"], rule["replacement"], text, flags=re.IGNORECASE)
        except re.error as e:
            log_service_message(f"Regex error: {e}")
    return text


def stable_hash(username: str) -> int:
    return int(hashlib.md5(username.encode("utf-8")).hexdigest(), 16)


def get_voice_lists():
    """
    Returns two lists of SAPI tokens:
      - preferred: voices whose description contains "(Natural)" and "Online"
      - fallback: all remaining voices
    """
    pythoncom.CoInitialize()
    try:
        probe = wincl.Dispatch("SAPI.SpVoice")
        tokens = probe.GetVoices()
        preferred, fallback = [], []
        for i in range(tokens.Count):
            tok = tokens.Item(i)
            desc = tok.GetDescription()
            if "(Natural)" in desc and "Online" in desc:
                preferred.append(tok)
            else:
                fallback.append(tok)
        return preferred, fallback
    finally:
        pythoncom.CoUninitialize()


def test_voice_indices():
    """
    Announce totals and then speak each 'preferred' voice by index.
    """
    preferred, fallback = get_voice_lists()
    pool = preferred if preferred else fallback
    pref_count = len(preferred)
    fall_count = len(fallback)
    total = pref_count + fall_count

    pythoncom.CoInitialize()
    try:
        probe = wincl.Dispatch("SAPI.SpVoice")
        probe.Speak(f"Voice check: {total} total; {pref_count} preferred; {fall_count} others")
        time.sleep(0.5)
        for idx, voice in enumerate(pool):
            desc = voice.GetDescription()
            try:
                probe.Voice = voice
                probe.Speak(f"Voice {idx}: {desc}")
                log_service_message(f"Spoke index {idx}: '{desc}'")
            except Exception as e:
                log_service_message(f"Failed voice {idx} '{desc}': {e}")
            time.sleep(0.3)
        log_service_message(
            f"Completed voice index test using {'preferred' if preferred else 'fallback'} pool (size {len(pool)})"
        )
    finally:
        pythoncom.CoUninitialize()


def speak_voice_index(index: int, extra_text: str = ""):
    """
    Speak 'Voice {index}' from preferred pool (or fallback),
    appending any extra_text provided.
    """
    preferred, fallback = get_voice_lists()
    pool = preferred if preferred else fallback
    count = len(pool)
    if index < 0 or index >= count:
        log_service_message(f"Invalid voice index: {index}")
        return

    pythoncom.CoInitialize()
    try:
        probe = wincl.Dispatch("SAPI.SpVoice")
        voice = pool[index]
        desc = voice.GetDescription()
        probe.Voice = voice
        message = f"Voice {index}: {desc}"
        if extra_text:
            message += f". {extra_text}"
        probe.Speak(message)
        log_service_message(f"Spoken voice index {index}: '{message}'")
    finally:
        pythoncom.CoUninitialize()


class TwitchBot:
    def __init__(self, shutdown_event: threading.Event):
        self.shutdown_event = shutdown_event
        self.config = load_config()
        self.tts_enabled = self.config.get("tts_enabled", True)
        self.socket: socket.socket | None = None
        self.connected = False
        # load manual assignments (read-only afterwards)
        self.assigned_voices = load_assigned_voices()
        # load preferred list for chat assignments
        self.preferred_voices, _ = get_voice_lists()
        self.voice_index_shift = self.config.get("voice_index", 0)
        self.user_voice_map: dict[str, wincl.CDispatch] = {}
        self.listen_thread: threading.Thread | None = None

    def start(self):
        log_service_message("TwitchBot starting")
        pythoncom.CoInitialize()
        self.config = load_config()
        self.tts_enabled = self.config.get("tts_enabled", True)
        self._connect_to_twitch()
        if self.connected:
            self._start_listening()

    def _connect_to_twitch(self):
        try:
            self.socket = socket.socket()
            self.socket.connect((TWITCH_HOST, TWITCH_PORT))
            irc = self.config["irc"]
            self.socket.sendall(f"PASS {irc['oauth']}\r\n".encode())
            self.socket.sendall(f"NICK {irc['username']}\r\n".encode())
            self.socket.sendall(f"JOIN {irc['channel']}\r\n".encode())
            self.connected = True
            log_service_message(f"Connected to {irc['channel']}")
        except Exception as e:
            log_service_message(f"Connection/Auth failed: {e}")

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
                if line.startswith("PING"):
                    self.socket.sendall("PONG :tmi.twitch.tv\r\n".encode())
                    continue
                if "PRIVMSG" in line:
                    user_host, _, msg = line.partition("PRIVMSG")
                    username = user_host.lstrip(":").split("!")[0]
                    chat = msg.split(" :", 1)[1] if " :" in msg else ""
                    chat = apply_substitutions(chat)

                    # skip self
                    if username.lower() == self.config["irc"]["username"].lower():
                        continue

                    # choose voice: manual assignment first
                    if username in self.assigned_voices:
                        idx = self.assigned_voices[username]
                        if idx < 0:
                            log_service_message(f"Skipping negative index for @{username}(filterd)")
                            continue
                    else:
                        idx = (stable_hash(username) + self.voice_index_shift) % len(self.preferred_voices)

                    voice = self.preferred_voices[idx]
                    log_service_message(f"TTS assign @{username} -> idx={idx}")

                    # create or reuse voice instance
                    try:
                        if username not in self.user_voice_map:
                            inst = wincl.Dispatch("SAPI.SpVoice")
                            inst.Voice = voice
                            self.user_voice_map[username] = inst
                        speaker = self.user_voice_map[username]
                    except Exception as e:
                        log_service_message(f"Error instantiating voice for @{username}: {e}")
                        continue

                    if self.tts_enabled:
                        try:
                            speaker.Speak(chat)
                        except Exception as e:
                            log_service_message(f"TTS speak error @{username}: {e}")

        # cleanup
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        pythoncom.CoUninitialize()
        log_service_message("Bot loop exiting")
