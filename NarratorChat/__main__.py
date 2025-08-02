import sys
from .tray_app import run_tray
from .config import log_service_message

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "tray":
        log_service_message("Launching tray manually.")
        run_tray()
    else:
        print("Usage:")
        print("  python -m __main__.py tray")
