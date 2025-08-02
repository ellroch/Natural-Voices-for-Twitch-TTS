### config.py
import os
import json
import time
from datetime import datetime
import threading

_config_lock = threading.Lock()
APPDATA = os.getenv("APPDATA") or os.path.expanduser("~")
CONFIG_FOLDER = os.path.join(APPDATA, "NarratorChat")
CONFIG_PATH = os.path.join(CONFIG_FOLDER, "config.json")
LOG_FILE = os.path.join(CONFIG_FOLDER, "service.log")

DEFAULT_CONFIG = {
    "tts_enabled": True,
    "voice_index": 10,
    "irc": {
        "channel": "#yourchannel",
        "username": "yourbotname",
        "oauth": "oauth:replace_with_your_token"
    },
    "substitutions": [
        {
            "pattern": "(?:https?://)?(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)",
            "replacement": "link"
        },
        {
            "pattern": "\\b(badword1|badword2)\\b",
            "replacement": "censored"
        }
    ],
}



def save_config(data: dict) -> None:
    with _config_lock:
        temp_path = CONFIG_PATH + ".tmp"
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, CONFIG_PATH)
        except Exception as e:
            print(f"[Error] Failed to save config: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

# Ensure config directory exists
os.makedirs(CONFIG_FOLDER, exist_ok=True)

# Create default config if missing
if not os.path.isfile(CONFIG_PATH):
    save_config(DEFAULT_CONFIG.copy())

def load_config() -> dict:
    with _config_lock:
        if not os.path.isfile(CONFIG_PATH):
            save_config(DEFAULT_CONFIG.copy())
            return DEFAULT_CONFIG.copy()
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            corrupted = f"{CONFIG_PATH}.corrupted_{timestamp}"
            os.rename(CONFIG_PATH, corrupted)
            save_config(DEFAULT_CONFIG.copy())
            return DEFAULT_CONFIG.copy()
        except Exception:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            corrupted = f"{CONFIG_PATH}.corrupted_{timestamp}"
            try:
                os.rename(CONFIG_PATH, corrupted)
            except:
                pass
            save_config(DEFAULT_CONFIG.copy())
            return DEFAULT_CONFIG.copy()


def log_service_message(msg: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    line = f"[{timestamp}] {msg}\n"
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line)
    except:
        pass
