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
from executors.PlayerExtension import PlayerExtension
from executors.GachiExtension import GachiExtension
from executors.YoutubeExtension import YoutubeExtension
from executors.AliasExtension import AliasExtension
from executors.BotExideExtension import BotExideExtension
from executors.VkExtension import VkExtension
from repositories.configRepository import ConfigRepository
from repositories.vkCacheRepository import VkCacheRepository
from browser import Browser
from utils.env import env
from services.vkService import VkService

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

    logFormatter = logging.Formatter('[%(asctime)s %(levelname)s, %(filename)s ln: %(lineno)d] %(message)s')
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

if (env.discord_token == None):
    raise Exception('Ensure .env file exists')

def default_config_strategy():
    return {
        'gachi': 
            youtube.playlist_items('PL-VMa2rh7q_ZQvmRt0dqidd9GUC-_42pG') + 
            youtube.playlist_items('PL0gU26yd_WJtO4z6KCXxrLlQlYaqnvXZF'),
        'aliases': [],
        'admins': [],
        'discord_vk_map': [],
        'vk_last_message_id': 125,
        'video-titles': []
    }

configRepo = ConfigRepository(default_config_strategy)
player = Player()
browser = None # Browser()

def reboot_handler():
    # browser.quit()
    os.system('youtube-dl --rm-cache-dir')
    os.system('git pull')
    os.system('start startup.py')
    sys.exit()

extensions = [
    PlayerExtension(player),
    YoutubeExtension(player, configRepo),
    GachiExtension(player, configRepo),
    AliasExtension(configRepo),
    BotExideExtension(reboot_handler),
    VkExtension(browser, player, configRepo)
]

bot = BotExide(extensions, configRepo)
try:
    bot.run(env.discord_token)
finally:
    pass
    # browser.quit()