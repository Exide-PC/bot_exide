import os
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.voice_client import VoiceClient
from discord.opus import load_opus
from dotenv import load_dotenv
import random
import asyncio
from youtube import YoutubeService, search
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
youtube = None

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
async def on_voice_state_update(member, before, after):
    exide_id = 286920219912306688
    shved_id = 402848249658081307

    exide = bot.guilds[0].get_member(exide_id)
    shved = bot.guilds[0].get_member(shved_id)

    if (before.channel == None or after.channel == None): return
    if (member.id != exide_id or shved == None): return
    if (before.channel.name == after.channel.name): return
    if ('Бочка' not in after.channel.name and 'AFK' not in after.channel.name): return

    after_copy = after.channel # after arguments mutates somehow, idk why

    await exide.move_to(before.channel)
    await shved.move_to(after_copy)

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
    global player

    if (msg.lower() == 'gachi radio'):
        if (author_vc == None):
            return
        await player.join_channel(author_vc)
        gachi.radio(send_message)
    
    elif (msg.lower() == 'gachi skip'):
        gachi.skip()
    
    elif (msg.lower() == 'gachi stop'):
        gachi.stop()
    
    elif (msg.lower().startswith('gachi')):
        if (author_vc == None):
            return

        search_value = msg[len('gachi'):].strip()
        selected_gachi = None

        if (len(search_value) > 0):
            search_results = gachi.search(search_value)
            if (len(search_results) == 0):
                await send_message('Nothing was found :c')
                return

            options = list(map(lambda g: g['title'], search_results))
            selected_index = await choice(options, author.id, send_message)
            if (selected_index == None):
                return
            selected_gachi = search_results[selected_index]
        
        await gachi.enqueue(selected_gachi, author_vc, send_message)

    elif (msg.lower() == 'join'):
        if (author_vc == None): return
        await player.join_channel(author_vc)

    elif (msg.lower() == 'disc'):
        await player.disconnect()

    elif (msg.lower().startswith('play')):
        if (author_vc == None):
            return
        parts = list(filter(None, msg.split(' ')))
        time_code = None
        if (len(parts) == 1): return
        if (len(parts) == 2):
            video_url = parts[1]
        if (len(parts) == 3):
            time_code = parts[1]
            video_url = parts[2]
        await youtube.play(video_url, True, None, author_vc, send_message, is_max_volume, time_code)

    elif (msg.lower().startswith('search')):
        query = msg[len('search'):].strip()
        search_results = search(query)
        if (len(search_results) == 0):
            await send_message('Nothing was found :c')
            return
        selected_index = await choice(list(map(lambda v: v['title'], search_results)), author.id, send_message)
        if (selected_index == None):
            return
        video = search_results[selected_index]
        video_id = video['videoId']

        await youtube.play(video_id, False, video['title'], author_vc, send_message, is_max_volume)

    elif (msg.lower() == 'skip'):
        if (gachi.is_radio):
            gachi.skip()
        else:
            player.skip()

    elif (msg.lower() == 'stop'):
        if (gachi.is_radio):
            gachi.stop()
        else:
            player.stop()

    elif (msg.lower() == 'repeat'):
        is_repeat = not player.is_repeat_mode
        await send_message(f'Repeat: {"On" if is_repeat else "Off"}')
        player.is_repeat_mode = is_repeat

@bot.event
async def on_ready():
    global player, gachi, youtube
    player = Player()
    gachi = GachiService(player, config['gachi'])
    youtube = YoutubeService(player)

    prev_voice = bot.guilds[0].get_member(bot.user.id).voice
    if (prev_voice != None):
        await player.join_channel(prev_voice.channel, True)

    print(f'{bot.user} has connected\n')

def start(token: str, cfg: dict, cfg_update_callback):
    global config, config_update_callback
    config, config_update_callback = cfg, cfg_update_callback
    bot.run(token)