# NarratorChat TTS Bot

A Windows tray application that assigns each Twitch chat user one of your installed **Natural** Windows voices and reads their messages aloud in that voice.

---

## Features

- **Automatic voice assignment** based on a stable hash of usernames
- **Natural Windows voices** only (installed via Windows Accessibility settings)
- **Dynamic TTS toggle** and **Reconnect** from the system tray
- **Crash resilience** with automatic restart on unexpected errors

---

## Prerequisites

1. **Windows 11** with Python 3.x installed.
2. **Natural Voices** installed:
   - Go to **Settings > Accessibility > Narrator > Narrator’s Voice > Add Natural Voices**
3. **Python dependencies** (install via `pip`):
   ```bash
   pip install pywin32 pystray pillow
   ```
4. **NaturalVoiceSAPIAdapter** (enables natural voices in SAPI):
   ```bash
   git clone https://github.com/gexgd0419/NaturalVoiceSAPIAdapter.git
   cd NaturalVoiceSAPIAdapter
   regsvr32 /i NaturalVoiceSAPIAdapter.dll
   ```

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/you/NarratorChat.git
   cd NarratorChat
   ```
2. **Install in editable mode**:
   ```bash
   pip install -e .
   ```

---

## Configuration

On first run, a default config file is generated at:

```
%APPDATA%\NarratorChat\config.json
```

Edit that file to set your Twitch credentials and preferences:

```json
{
  "irc": {
    "channel": "#your_channel",
    "username": "your_bot_username",
    "oauth": "oauth:your_token_here"
  },
  "voice_index": 10,          // Offset for voice assignment (optional)
  "tts_enabled": true,
  "substitutions": [ ... ]
}
```

Obtain a Twitch OAuth token for your bot account at:

> [https://twitchtokengenerator.com/](https://twitchtokengenerator.com/)

---

## Usage

1. **Launch the tray app**:
   - Double-click `launch.pyw` (no console window)

2. **Use the system tray icon**:
   - **Toggle TTS**: Enable or disable speech output
   - **Reconnect**: Re-establish Twitch chat connection
   - **Test Voices**: Test the SAPI connection for natural voices
   - **Exit**: Stop the bot and remove the tray icon

---

## Uninstallation

```bash
pip uninstall narratorchat
```

Then delete the `%APPDATA%\NarratorChat` folder (if desired) and remove the `NarratorChat.egg-info` directory.

---

*Enjoy your personalized Twitch TTS experience!*

