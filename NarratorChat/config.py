### config.py
import os
import json
import time
from datetime import datetime
import threading

_config_lock = threading.Lock()
_ASSIGNED_LOCK = threading.Lock()
APPDATA = os.getenv("APPDATA") or os.path.expanduser("~")
CONFIG_FOLDER = os.path.join(APPDATA, "NarratorChat")
CONFIG_PATH = os.path.join(CONFIG_FOLDER, "config.json")
ASSIGNED_PATH = os.path.join(CONFIG_FOLDER, "AssignedVoices.json")
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

def load_assigned_voices() -> dict[str, int]:
    """
    Load or initialize AssignedVoices.json in CONFIG_FOLDER.
    If missing, create with examples. On corruption, back up and regenerate.
    Returns a dict mapping usernames to voice indices.
    """
    default = {"chatter1": 0, "chatter2": 1}
    with _ASSIGNED_LOCK:
        os.makedirs(CONFIG_FOLDER, exist_ok=True)
        if not os.path.isfile(ASSIGNED_PATH):
            try:
                with open(ASSIGNED_PATH, "w", encoding="utf-8") as f:
                    json.dump(default, f, indent=2)
                log_service_message("Created default AssignedVoices.json")
            except Exception as e:
                log_service_message(f"Failed to create AssignedVoices.json: {e}")
            return default.copy()
        try:
            with open(ASSIGNED_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            corrupted = ASSIGNED_PATH + f".corrupted_{ts}"
            try:
                os.rename(ASSIGNED_PATH, corrupted)
                log_service_message(f"Backed up corrupted AssignedVoices.json to {corrupted}")
            except Exception as e:
                log_service_message(f"Failed to back up corrupted AssignedVoices.json: {e}")
            try:
                with open(ASSIGNED_PATH, "w", encoding="utf-8") as f:
                    json.dump(default, f, indent=2)
                log_service_message("Recreated default AssignedVoices.json after corruption")
            except Exception as e:
                log_service_message(f"Failed to recreate AssignedVoices.json: {e}")
            return default.copy()
        except Exception as e:
            log_service_message(f"Error loading AssignedVoices.json: {e}")
            return default.copy()

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
