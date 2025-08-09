# tray_app.py
import threading
import os
import sys
import time
import traceback
import pystray
from pystray import MenuItem as item
from PIL import Image
from .config import load_config, save_config, log_service_message, CONFIG_FOLDER
from .bot_logic import test_voice_indices, speak_voice_index, get_voice_lists, TwitchBot

# Global bot instance and thread handles
global_bot_instance: TwitchBot | None = None
bot_thread: threading.Thread | None = None
bot_shutdown_event: threading.Event | None = None

icon_path = os.path.join(os.path.dirname(__file__), "Asset 3@4x.ico")
try:
    icon_image = Image.open(icon_path)
except Exception:
    icon_image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))


def start_bot_thread():
    global bot_thread, bot_shutdown_event, global_bot_instance
    if bot_thread and bot_thread.is_alive():
        return
    bot_shutdown_event = threading.Event()
    global_bot_instance = TwitchBot(bot_shutdown_event)
    bot_thread = threading.Thread(target=global_bot_instance.start, daemon=True)
    bot_thread.start()
    log_service_message("Bot thread started.")


def stop_bot_thread():
    global bot_thread, bot_shutdown_event, global_bot_instance
    if bot_shutdown_event:
        bot_shutdown_event.set()
    if bot_thread:
        bot_thread.join(timeout=5)
    bot_thread = None
    bot_shutdown_event = None
    global_bot_instance = None
    log_service_message("Bot thread stopped.")


def reconnect_bot():
    if global_bot_instance:
        threading.Thread(target=global_bot_instance.reconnect, daemon=True).start()



def open_config_folder():
    try:
        os.startfile(CONFIG_FOLDER)
        log_service_message(f"Opened config folder: {CONFIG_FOLDER}")
    except Exception as e:
        log_service_message(f"Failed to open config folder: {e}")


def prompt_and_speak():
    try:
        import tkinter as tk
        from tkinter import ttk

        preferred, fallback = get_voice_lists()
        pool = preferred if preferred else fallback
        choices = [f"{i}: {pool[i].GetDescription()}" for i in range(len(pool))]

        root = tk.Tk()
        root.title("Select Voice")
        tk.Label(root, text="Choose a voice:").pack(padx=10, pady=5)
        var = tk.StringVar(value=choices[0])
        combo = ttk.Combobox(root, values=choices, textvariable=var,
                             state="readonly", width=60)
        combo.pack(padx=10, pady=5)
        def on_ok():
            root.quit()
        tk.Button(root, text="OK", command=on_ok).pack(pady=(0,10))
        root.mainloop()
        selection = var.get()
        root.destroy()

        if not selection:
            return
        idx = int(selection.split(":", 1)[0])
        desc = pool[idx].GetDescription()
        speak_voice_index(idx, extra_text=f"This is {desc}")
    except Exception as e:
        log_service_message(f"Speak voice input error: {e}")


def run_tray():
    start_bot_thread()

    def on_exit(icon, _):
        stop_bot_thread()
        icon.stop()

    def toggle_tts(icon, _):
        cfg = load_config()
        cfg["tts_enabled"] = not cfg.get("tts_enabled", True)
        save_config(cfg)
        if global_bot_instance:
            global_bot_instance.tts_enabled = cfg["tts_enabled"]

    def tts_text(_):
        return "Disable TTS" if load_config().get("tts_enabled", True) else "Enable TTS"

    menu = (
        item(tts_text, toggle_tts),
        item("Reconnect", lambda i, j: reconnect_bot()),
        item("Test Voice Indices", lambda i, j: threading.Thread(
            target=test_voice_indices, daemon=True).start()),
        item("Speak Voice by Index...", lambda i, j: threading.Thread(
            target=prompt_and_speak, daemon=True).start()),
        item("Open Config Folder", lambda i, j: open_config_folder()),
        item("Exit", on_exit),
    )

    icon = pystray.Icon("TTSBot", icon_image,
                        "NarratorChat TTS", pystray.Menu(*menu))
    icon.run()


if __name__ == "__main__":
    def handle_exception(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        log_service_message(
            "Uncaught exception: "
            + "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        )
    sys.excepthook = handle_exception

    exit_flag = False
    while not exit_flag:
        try:
            run_tray()
            exit_flag = True
        except Exception:
            log_service_message("Exception in run_tray: " + traceback.format_exc())
            stop_bot_thread()
            time.sleep(5)

