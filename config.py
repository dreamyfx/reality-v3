USER_ID = "Set from Builder"

DEBUG = True

import os
import tempfile
LOCAL = os.getenv('LOCALAPPDATA')
ROAMING = os.getenv('APPDATA')
TEMP = tempfile.gettempdir()
def log(msg):
    if DEBUG:
        print(f"[DEBUGING RealityV3] {msg}")
