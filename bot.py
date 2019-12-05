import os
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.voice_client import VoiceClient
from discord.opus import load_opus
from dotenv import load_dotenv
import random
import asyncio
import youtube
from voice_service import VoiceService
from gachi_service import GachiService
import re

# https://discordpy.readthedocs.io/en/latest/api.html

bot = commands.Bot(command_prefix = 'cb!')
# bot = discord.Client()
# voice_client = None
config = None
config_update_callback = None

voice = None
gachi = None

gachi_queue = []
is_gachi_radio = False

def update_cfg(new_cfg: dict):
    global config
    config_update_callback(new_cfg)
    config = new_cfg

@bot.event
async def on_message(message):
    if (message.channel.type.name != 'private' and 
        message.channel.name != 'bot-exide' or
        message.author == bot.user): return

    async def message_callback(msg: str):
        await message.channel.send(msg)

    is_max_volume = False

    # message preprocessing to handle shortcuts
    if (message.content.lower() == 'gachi depression'):
        message.content = 'play https://www.youtube.com/watch?v=nbzFQD2Q3rs'
    if (message.content.lower() == 'kekw'):
        message.content = 'play https://www.youtube.com/watch?v=7wivOEXlL9s'
    if (message.content.lower() == 'knock'):
        message.content = 'play https://www.youtube.com/watch?v=ir-pKzGsKPQ'
        is_max_volume = True

    # we also need the 'voice' property which is not being
    # passed in case the message was received via PM
    author = bot.guilds[0].get_member(message.author.id)
    author_vc = author.voice.channel if author.voice != None else None
    
    msg = message.content
    global voice, is_gachi_radio

    if (msg.lower() == 'gachi radio'):
        if (not voice.is_connected() and author_vc != None):
            await voice.join_channel(author_vc, message.channel)
        gachi.is_radio = True
    elif (msg.lower() == 'gachi skip'):
        voice.stop()
    elif (msg.lower() == 'gachi stop'):
        gachi.is_radio = False
        voice.stop()
    elif (msg.lower() == 'gachi current'):
        await message.channel.send(f'Now playing: {gachi.current}')
    elif (msg.lower() == 'gachi help'):
        await message.channel.send('Commands: gachi [radio,skip,stop,current,*search value*]')
    elif (msg.lower().startswith('gachi')):
        search_value = msg[len('gachi'):].strip()
        is_added = await gachi.enqueue(search_value, message_callback)
        if (is_added and author_vc != None):
            await voice.join_channel(author_vc, message.channel)
    elif (msg.lower() == 'join'):
        if (author_vc == None): return
        await voice.join_channel(author_vc, message.channel)
    elif (msg.lower() == 'disc'):
        if (not voice.is_connected()): return
        await voice.disconnect()
    elif (msg.lower().startswith('play')):
        matches = re.findall(r'v=[\w-]+', msg[len('play'):].strip())
        if (len(matches) != 1):
            await message.channel.send('Wrong youtube video url')
            return
        video_id = matches[0][2:] # skipping v=
        file_path = youtube.download_sound(video_id)
        await voice.join_channel(author_vc, message.channel)
        await voice.play_async(file_path, is_max_volume)
    elif (msg.lower() == 'skip'):
        voice.stop()

@bot.event
async def on_ready():
    global voice, gachi
    voice = VoiceService()
    gachi = GachiService(voice, config['gachi'])
    print(f'{bot.user} has connected\n')

def start(token: str, cfg: dict, cfg_update_callback):
    global config, config_update_callback
    config, config_update_callback = cfg, cfg_update_callback
    bot.run(token)