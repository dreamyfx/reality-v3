# modules/installed_software.py - Extract installed software list from registry

import winreg
from config import log

BANNER = r"""  _____            _ _ _         
 |  __ \          | (_) |        
 | |__) |___  __ _| |_| |_ _   _ 
 |  _  // _ \/ _` | | | __| | | |
 | | \ \  __/ (_| | | | |_| |_| |
 |_|  \_\___|\__,_|_|_|\__|\__, |
                            __/ |
                           |___/ 
"""

def get_installed_software():
    """Extract installed software from Windows registry"""
    software_list = []
    
    # Registry paths to check
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    
    for hkey, path in registry_paths:
        try:
            key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
            
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    
                    try:
                        name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        version = ""
                        
                        try:
                            version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                        except:
                            pass
                        
                        if name:
                            entry = f"{name}"
                            if version:
                                entry += f" [{version}]"
                            
                            if entry not in software_list:
                                software_list.append(entry)
                        
                        winreg.CloseKey(subkey)
                    except:
                        winreg.CloseKey(subkey)
                        continue
                except:
                    continue
            
            winreg.CloseKey(key)
        except:
            continue
    
    return sorted(software_list)

def grab():
    """Main function to gather installed software"""
    log("Gathering installed software...")
    
    software = get_installed_software()
    
    # Format output
    output = BANNER
    for idx, app in enumerate(software, 1):
        output += f"{idx}) {app}\n"
    
    log(f"Found {len(software)} installed applications")
    return output