# modules/screenshot.py - Screenshot capture (returns file path)

import os
from PIL import ImageGrab
from config import log

def grab():
    """Capture screenshot and return file path"""
    log("Capturing screenshot...")
    
    try:
        # Capture screenshot
        screenshot = ImageGrab.grab()
        
        # Save to temp file
        temp_path = os.path.join(os.getenv('TEMP'), 'screenshot.png')
        screenshot.save(temp_path, 'PNG')
        
        log("Screenshot captured")
        return temp_path
    
    except Exception as e:
        log(f"Screenshot failed: {e}")
        return None