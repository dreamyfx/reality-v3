# modules/installed_browsers.py - Detect installed browsers

import os
from pathlib import Path
from config import LOCAL, ROAMING, log

BANNER = r"""  _____            _ _ _         
 |  __ \          | (_) |        
 | |__) |___  __ _| |_| |_ _   _ 
 |  _  // _ \/ _` | | | __| | | |
 | | \ \  __/ (_| | | | |_| |_| |
 |_|  \_\___|\__,_|_|_|\__|\__, |
                            __/ |
                           |___/ 
"""

def check_browser_installed(name, paths):
    """Check if a browser is installed"""
    for path in paths:
        if os.path.exists(path):
            return True
    return False

def get_browser_version(version_file_path):
    """Try to extract browser version from known files"""
    try:
        if os.path.exists(version_file_path):
            # For Chrome-based browsers, check Local State
            import json
            with open(version_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                # Chrome stores version info differently, this is a simplified check
                return "Installed"
    except:
        pass
    return "Installed"

def grab():
    """Detect installed browsers"""
    log("Detecting installed browsers...")
    
    browsers = []
    
    # Browser definitions: name and possible install paths
    browser_checks = {
        'Google Chrome': [
            LOCAL + r"\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ],
        'Microsoft Edge': [
            LOCAL + r"\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        ],
        'Mozilla Firefox': [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
        ],
        'Opera': [
            ROAMING + r"\Opera Software\Opera Stable\opera.exe",
            LOCAL + r"\Programs\Opera\launcher.exe"
        ],
        'Opera GX': [
            ROAMING + r"\Opera Software\Opera GX Stable\opera.exe"
        ],
        'Brave': [
            LOCAL + r"\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
        ],
        'Vivaldi': [
            LOCAL + r"\Vivaldi\Application\vivaldi.exe"
        ],
        'Yandex': [
            LOCAL + r"\Yandex\YandexBrowser\Application\browser.exe"
        ],
        'Tor Browser': [
            LOCAL + r"\Tor Browser\Browser\firefox.exe",
            r"C:\Program Files\Tor Browser\Browser\firefox.exe"
        ]
    }
    
    for browser_name, paths in browser_checks.items():
        if check_browser_installed(browser_name, paths):
            browsers.append(browser_name)
    
    # Format output
    output = BANNER
    if browsers:
        for idx, browser in enumerate(browsers, 1):
            output += f"{idx}) {browser}\n"
    else:
        output += "No browsers detected\n"
    
    log(f"Detected {len(browsers)} browsers")
    return output