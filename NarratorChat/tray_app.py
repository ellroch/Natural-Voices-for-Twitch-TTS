### tray_app.py
import threading
import os
import sys
import time
import traceback
import pystray
from pystray import MenuItem as item
from PIL import Image
from .config import load_config, save_config, log_service_message
from .bot_logic import test_all_voices, TwitchBot

# Global bot instance and thread handles
global_bot_instance: TwitchBot | None = None
bot_thread: threading.Thread | None = None
bot_shutdown_event: threading.Event | None = None

icon_path = os.path.join(os.path.dirname(__file__), "Asset 3@4x.ico")
try:
    icon_image = Image.open(icon_path)
except Exception:
    icon_image = Image.new('RGBA', (16, 16), (0, 0, 0, 0))


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
        global_bot_instance.reconnect()


def run_tray():
    # Initialize and launch bot thread
    start_bot_thread()

    def on_exit(icon, _):
        stop_bot_thread()
        icon.stop()

    def toggle_tts(icon, _):
        cfg = load_config()
        new_state = not cfg.get("tts_enabled", True)
        cfg["tts_enabled"] = new_state
        save_config(cfg)
        if global_bot_instance:
            global_bot_instance.tts_enabled = new_state

    def tts_text(_):
        cfg = load_config()
        return "Disable TTS" if cfg.get("tts_enabled", True) else "Enable TTS"

    menu = (
        item(tts_text, toggle_tts),
        item("Reconnect", lambda icon, item: reconnect_bot()),
        item("Test Voices", lambda icon, item: threading.Thread(target=test_all_voices, daemon=True).start()),
        item("Exit", on_exit),
    )

    icon = pystray.Icon("TTSBot", icon_image, "NarratorChat TTS", pystray.Menu(*menu))
    icon.run()


if __name__ == "__main__":
    # Uncaught exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        log_service_message("Uncaught exception: " + ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    sys.excepthook = handle_exception

    exit_flag = False
    while not exit_flag:
        try:
            run_tray()
            # Normal exit via tray menu
            exit_flag = True
        except Exception:
            log_service_message("Exception in run_tray: " + traceback.format_exc())
            stop_bot_thread()
            # Wait before restart
            time.sleep(5)