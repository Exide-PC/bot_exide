import os
import sys
import io
import bot
import youtube
import json
import logging
from bot import BotExide
from dotenv import load_dotenv
from player import Player
from gachi_service import GachiService
from youtube import YoutubeService
from executors.PlayerExtension import PlayerExtension
from executors.GachiExtension import GachiExtension
from executors.YoutubeExtension import YoutubeExtension
from executors.AliasExtension import AliasExtension
from executors.BotExideExtension import BotExideExtension
from executors.BrowserExtension import BrowserExtension
from repositories.configRepository import ConfigRepository
from repositories.vkCacheRepository import VkCacheRepository
from browser import Browser

def set_logger():
    class LogFilter(logging.Filter):
        def filter(self, record):
            return not (
                record.name.startswith('discord.') or 
                record.name.startswith('websockets.') or 
                record.name.startswith('urllib3.')
            # ) or (
            #     record.levelno >= 30 # Warning
            )

    logFormatter = logging.Formatter('[%(asctime)s %(levelname)s] %(message)s') # %(pathname)s
    logFilter = LogFilter()

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    fileHandler = logging.FileHandler('log.txt', 'a', 'utf-8')
    fileHandler.addFilter(logFilter)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.addFilter(logFilter)
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

set_logger()
env = load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')

if (discord_token == None):
    raise Exception('Ensure .env file exists')

gachi_playlist1 = 'PL-VMa2rh7q_ZQvmRt0dqidd9GUC-_42pG'
gachi_playlist2 = 'PL0gU26yd_WJtO4z6KCXxrLlQlYaqnvXZF'

cfg_path = 'bot.cfg'
cfg = None

def update_cfg(cfg: dict):
    with open(cfg_path, 'w') as f:
        json.dump(cfg, f, indent=4)

if (not os.path.exists(cfg_path)):
    with open(cfg_path, 'w') as f:
        """ default cfg """
        cfg = {
            'gachi': 
                youtube.playlist_items(gachi_playlist1) + 
                youtube.playlist_items(gachi_playlist2),
            'aliases': [],
            'admins': [],
            'video-titles': []
        }
        json.dump(cfg, f, indent=4)
else:
    with open(cfg_path, 'r') as f:
        cfg = json.load(f)

configRepo = ConfigRepository(cfg, update_cfg)
player = Player()
gachi = GachiService(player, configRepo)
youtube = YoutubeService(player, configRepo)
vkCacheRepo = VkCacheRepository()
browser = Browser()

def reboot_handler():
    browser.quit()
    os.system('youtube-dl --rm-cache-dir')
    os.system('git pull')
    os.system('start startup.py')
    sys.exit()

extensions = [
    PlayerExtension(player),
    YoutubeExtension(youtube),
    GachiExtension(gachi),
    AliasExtension(configRepo),
    BotExideExtension(reboot_handler),
    BrowserExtension(browser, player, vkCacheRepo)
]

bot = BotExide(extensions, configRepo)
bot.run(discord_token)