import win32com.client as wincl


# this script can be called from the command line to enumerate the voices available on the system.
# this application filters out the voices that are not natural voices. 
# Natural voices can be installed from windows settings > accessibility > narrator > Narrator's Voice > Add Natural Voices
voice = wincl.Dispatch("SAPI.SpVoice")
voices = voice.GetVoices()
for i in range(voices.Count):
    v = voices.Item(i)
    print(v.GetDescription())
