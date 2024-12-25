this application will assign users in chat one of the natural voices you have installed on windows 11, based on an index derived from their name, and read their messages in that voice.

Prerequisites

You must have natural voice packs installed already. this application filters out the voices that are not natural voices. Natural voices can be installed from windows settings > accessibility > narrator > Narrator's Voice > Add Natural Voices

You will need a Windows 11 machine with a python3 installation.
dependencies:
    pip install pywin32
    pip install pystray pillow

install https://github.com/gexgd0419/NaturalVoiceSAPIAdapter?tab=readme-ov-file
this comes with a build of https://github.com/gexgd0419/TTSApplicationSample/tree/6c48276b66900a9db99763c7ed7a90bf4df1b62f 
which inspired this project, and a DLL which we will need to register to allow use of narrator voices in TTS contexts.

from within the NaturalVoiceSAPIAdapter installation directory open a shell and enter the command:
    regsvr32 /i NaturalVoiceSAPIAdapter.dll
This allows the newly installed voices to show up in SAPI enumeration.


A bot account (create a basic user account on twitch)
A valid Twitch OAuth token for your bot account. while logged into the account visit:
https://twitchtokengenerator.com/



How to use:
after all prerequisites have been completed, you can enter the information into the config variables in the configuragion section at the top of narrator.pyw

TWITCH_OAUTH    = "oauth:xxxxxxxxxxxxxxxxxx"  
TWITCH_USERNAME = "your_bot_username" 
TWITCH_CHANNEL  = "#your_channel_name"

optionally you can modify the value of VOICE_INDEX_SHIFT to reshuffle the voice assignments.


You can then
double click the narrator.pyw file to launch.
it will open without a window, and should appear as an NC icon in the system tray.
you can close the file by right clicking this systray icon and clicking "exit".