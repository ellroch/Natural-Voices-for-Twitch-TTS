# launch.pyw
import os, sys

# ensure current folder is on sys.path
sys.path.insert(0, os.path.dirname(__file__))

from NarratorChat.tray_app import run_tray

if __name__ == "__main__":
    run_tray()
