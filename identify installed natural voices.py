import pythoncom
import win32com.client as wincl

def list_natural_voices():
    pythoncom.CoInitialize()
    try:
        probe = wincl.Dispatch("SAPI.SpVoice")
        tokens = probe.GetVoices()
        naturals = []
        for i in range(tokens.Count):
            desc = tokens.Item(i).GetDescription()
            if "(Natural)" in desc:
                naturals.append(desc)
        return naturals
    finally:
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    for idx, name in enumerate(list_natural_voices()):
        print(f"{idx}: {name}")
