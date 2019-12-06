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
from player import Player
from gachi_service import GachiService
import re

# https://discordpy.readthedocs.io/en/latest/api.html

bot = commands.Bot(command_prefix = 'cb!')
# bot = discord.Client()
# voice_client = None
config = None
config_update_callback = None

player = None
gachi = None

gachi_queue = []
is_gachi_radio = False

def update_cfg(new_cfg: dict):
    global config
    config_update_callback(new_cfg)
    config = new_cfg

async def choice(options: [], user_id, message_callback):
    choice_hint = ""
    for i in range(len(options)):
        choice_hint += f'{i + 1}. {options[i]}'
        choice_hint += '\n' if i != len(options) - 1 else ''

    await message_callback(choice_hint)
    result = None

    def check(m):
        if (m.author.id != user_id): return False
        try:
            i = int(m.content) - 1
            if (i < 0 or i >= len(options)): return False
            nonlocal result
            result = i
            return True
        except ValueError:
            return False

    try:
        await bot.wait_for('message', check=check, timeout=20)
        return result
    except asyncio.TimeoutError:
        pass

@bot.event
async def on_message(message):
    if (message.channel.type.name != 'private' and 
        message.channel.name != 'bot-exide' or
        message.author == bot.user): return

    async def send_message(msg: str):
        await message.channel.send(msg)

    is_max_volume = False

    # message preprocessing to handle shortcuts
    if (message.content.lower() == 'gachi depression'):
        message.content = 'play https://www.youtube.com/watch?v=nbzFQD2Q3rs'
    if (message.content.lower() == 'kekw'):
        message.content = 'play https://www.youtube.com/watch?v=7wivOEXlL9s'
    if (message.content.lower() == 'fits'):
        message.content = 'play https://www.youtube.com/watch?v=zxriE8aVY1M'
    if (message.content.lower() == 'knock'):
        message.content = 'play https://www.youtube.com/watch?v=ir-pKzGsKPQ'
        is_max_volume = True

    # we also need the 'voice' property which is not being
    # passed in case the message was received via PM
    author = bot.guilds[0].get_member(message.author.id)
    author_vc = author.voice.channel if author.voice != None else None
    
    msg = message.content
    global player, is_gachi_radio

    if (msg.lower() == 'gachi radio'):
        if (not player.is_connected() and author_vc != None):
            await player.join_channel(author_vc, message.channel)
        gachi.radio(True, send_message)
    
    elif (msg.lower() == 'gachi skip'):
        player.stop()
    
    elif (msg.lower() == 'gachi stop'):
        gachi.is_radio = False
        player.stop()
    
    elif (msg.lower() == 'gachi current'):
        await message.channel.send(f'Now playing: {gachi.current}')
    
    elif (msg.lower() == 'gachi help'):
        await message.channel.send('Commands: gachi [radio,skip,stop,current,*search value*]')
    
    elif (msg.lower().startswith('gachi')):
        search_value = msg[len('gachi'):].strip()
        is_added = await gachi.enqueue(search_value, send_message)
        if (is_added and author_vc != None):
            await player.join_channel(author_vc, message.channel)

    elif (msg.lower() == 'join'):
        if (author_vc == None): return
        await player.join_channel(author_vc, message.channel)

    elif (msg.lower() == 'disc'):
        if (not player.is_connected()): return
        await player.disconnect()

    elif (msg.lower().startswith('play')):
        parts = list(filter(None, msg.split(' ')))
        if (len(parts) == 1): return
        if (len(parts) == 2): video_url = parts[1]
        if (len(parts) == 3): video_url = parts[2]

        matches = re.findall(r'v=[\w-]+', video_url)
        if (len(matches) != 1):
            await message.channel.send('Wrong youtube video url')
            return
        video_id = matches[0][2:] # skipping v=

        if (len(parts) == 2):
            file_path = youtube.download_sound(video_id)
        elif (len(parts) == 3):
            try:
                file_path = youtube.downlad_and_trunc_sound(video_id, parts[1])
            except ValueError:
                await send_message('Incorrent timecode input')
                return

        if (gachi.is_radio):
            gachi.is_radio = False
        await player.join_channel(author_vc, message.channel)
        await player.play_async(file_path, is_max_volume)

    elif (msg.lower().startswith('search')):
        query = msg[len('search'):].strip()
        search_results = youtube.search(query)
        if (len(search_results) == 0):
            await send_message('Nothing was found :c')
            return
        selected_index = await choice(list(map(lambda v: v['title'], search_results)), author.id, send_message)
        if (selected_index == None): return
        video = search_results[selected_index]
        video_id = video['videoId']
        await message.channel.send(f'Playing: {video["title"]}')
        file_path = youtube.download_sound(video_id)
        if (gachi.is_radio):
            gachi.is_radio = False
        await player.join_channel(author_vc, message.channel)
        await player.play_async(file_path, is_max_volume)

    elif (msg.lower() in ['skip', 'stop']):
        player.stop()

    elif (msg.lower() == 'choice'):
        options = ['Swallow', 'My', 'Cum']
        result = await choice(options, author.id, send_message)
        await send_message(f'Your choice is: {options[result]}' if result != None else 'Choice timeout :c')

@bot.event
async def on_ready():
    global player, gachi
    player = Player()
    gachi = GachiService(player, config['gachi'])

    prev_voice = bot.guilds[0].get_member(bot.user.id).voice
    if (prev_voice != None):
        await player.join_channel(prev_voice.channel, True)

    print(f'{bot.user} has connected\n')

def start(token: str, cfg: dict, cfg_update_callback):
    global config, config_update_callback
    config, config_update_callback = cfg, cfg_update_callback
    bot.run(token)