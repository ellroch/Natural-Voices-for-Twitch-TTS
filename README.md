Below is a sample **README.md** layout you could use on GitHub for your application. It’s organized to be clear and concise, with headings, bulleted lists, and code blocks for easy reference.

---

# Narrator Chat TTS

This application assigns each user in a Twitch chat a Windows 11 **Natural Voice** (installed on your system) based on an index derived from their username. It then reads their messages aloud in that voice.

## Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [System Tray Controls](#system-tray-controls)
7. [Credits](#credits)

---

## Introduction
Windows 11 provides advanced **Natural Voice** options for text-to-speech. By filtering out non-natural voices, this application selects a unique voice for each chat user, creating an immersive, voice-driven Twitch chat experience.

---

## Prerequisites

1. **Windows 11**  
   - Ensure you have **Natural Voice** packs installed. Go to:  
     **Settings** > **Accessibility** > **Narrator** > **Narrator's Voice** > **Add Natural Voices**

2. **Python 3**  
   - Make sure Python 3 is installed on your Windows 11 system.

3. **Python Dependencies**  
   Install these via pip:
   ```bash
   pip install pywin32
   pip install pystray
   pip install pillow
   ```

4. **NaturalVoiceSAPIAdapter**  
   - Download and install **[NaturalVoiceSAPIAdapter](https://github.com/gexgd0419/NaturalVoiceSAPIAdapter?tab=readme-ov-file)**.  
   - This includes a build of [TTSApplicationSample](https://github.com/gexgd0419/TTSApplicationSample/tree/6c48276b66900a9db99763c7ed7a90bf4df1b62f) plus a DLL we need to register.

5. **Twitch Bot Account & OAuth Token**  
   - Create or use an existing user account on Twitch dedicated as your bot.
   - Generate a valid OAuth token for that account via:  
     [https://twitchtokengenerator.com/](https://twitchtokengenerator.com/)

---

## Installation

1. **Install the Python Dependencies**  
   ```bash
   pip install pywin32
   pip install pystray
   pip install pillow
   ```

2. **Set Up NaturalVoiceSAPIAdapter**  
   - Open a shell/command prompt inside the **NaturalVoiceSAPIAdapter** installation directory.
   - Register the DLL:
     ```bash
     regsvr32 /i NaturalVoiceSAPIAdapter.dll
     ```
   - This step is critical so that the **Natural** voices show up properly in SAPI.

3. **Download or Clone This Repository**  
   - Place the files (including **narrator.pyw**) on your Windows 11 system.

---

## Configuration

In **narrator.pyw**, locate the configuration section near the top and update the following variables:

```python
TWITCH_OAUTH    = "oauth:xxxxxxxxxxxxxxxxxx"
TWITCH_USERNAME = "your_bot_username"
TWITCH_CHANNEL  = "#your_channel_name"
VOICE_INDEX_SHIFT = 0  # Adjust to reshuffle voice assignments
```

- **TWITCH_OAUTH**: The OAuth token for your bot account.
- **TWITCH_USERNAME**: The Twitch username of the bot.
- **TWITCH_CHANNEL**: Your channel name, with **#** prefix.
- **VOICE_INDEX_SHIFT** (optional): Change the offset if you’d like to alter how voices are assigned.

---

## Usage

1. **Ensure Requirements Are Met**  
   - Natural Voice packs installed on Windows 11.  
   - Python 3 installed.  
   - Dependencies installed.  
   - DLL registered.

2. **Launch the Application**  
   - Double-click **narrator.pyw**.  
   - The script runs without opening a visible window—look for the NC (Narrator Chat) icon in the system tray.

3. **Join Your Twitch Channel**  
   - The application connects to Twitch chat using the provided credentials (OAuth, username, channel).

4. **Voice Assignment**  
   - Each user in the channel is mapped to a natural voice based on an index derived from their username.
   - Chat messages are then spoken in real-time with the selected voice.

---

## System Tray Controls

- **Right-click** the NC (Narrator Chat) icon in the system tray:
  - Click **Exit** to close the application.

---

## Credits

- [TTSApplicationSample](https://github.com/gexgd0419/TTSApplicationSample/tree/6c48276b66900a9db99763c7ed7a90bf4df1b62f) – The foundation that inspired this project.
- [NaturalVoiceSAPIAdapter](https://github.com/gexgd0419/NaturalVoiceSAPIAdapter) – Used to enable narrator voices in TTS contexts.

---

**Enjoy your new voice-driven Twitch chat experience!** If you have any questions or suggestions, feel free to open an issue or submit a pull request.
