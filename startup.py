import os
import sys
import io
import bot
import youtube
import json
import logging
from dotenv import load_dotenv
from player import Player
from gachi_service import GachiService
from youtube import YoutubeService
from executors.PlayerExtension import PlayerExtension
from executors.GachiExtension import GachiExtension
from executors.YoutubeExtension import YoutubeExtension
from executors.AliasExtension import AliasExtension

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
    rootLogger.setLevel(logging.DEBUG)

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
            'admins': []
        }
        json.dump(cfg, f, indent=4)
else:
    with open(cfg_path, 'r') as f:
        cfg = json.load(f)

player = Player()
gachi = GachiService(player, cfg['gachi'])
youtube = YoutubeService(player)

executors = [
    PlayerExtension(player),
    YoutubeExtension(youtube),
    GachiExtension(gachi),
    AliasExtension()
]

bot.start(discord_token, cfg, executors, update_cfg)