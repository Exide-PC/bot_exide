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

    # message preprocessing to handle shortcuts
    if (message.content.lower() == 'gachi depression'):
        message.content = 'play https://www.youtube.com/watch?v=nbzFQD2Q3rs'
    if (message.content.lower() == 'kekw'):
        message.content = 'play https://www.youtube.com/watch?v=7wivOEXlL9s'
    if (message.content.lower() == 'fits'):
        message.content = 'play https://www.youtube.com/watch?v=zxriE8aVY1M'
    if (message.content.lower() == 'knock'):
        message.content = 'play https://www.youtube.com/watch?v=ir-pKzGsKPQ'
    if (message.content.lower() == 'sax'):
        message.content = 'play https://www.youtube.com/watch?v=uiDVSYa8IPw'

    # we also need the 'voice' property which is not being
    # passed in case the message was received via PM
    author = bot.guilds[0].get_member(message.author.id)
    author_vc = author.voice.channel if author.voice != None else None
    
    msg = message.content.lower()
    global player

    if (msg.lower() == 'gachi radio'):
        if (author_vc == None):
            return
        await player.join_channel(author_vc)
        gachi.radio(send_message)
    
    elif (msg == 'gachi skip'):
        gachi.skip()
    
    elif (msg == 'gachi stop'):
        gachi.stop()
    
    elif (msg.startswith('gachi')):
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

    elif (msg == 'join'):
        if (author_vc == None): return
        await player.join_channel(author_vc)

    elif (msg == 'disc'):
        await player.disconnect()

    elif (msg.startswith('play')):
        if (author_vc == None):
            return
        cmd = message.content[len('play') + 1:]
        await youtube.parse_cmd(cmd, author_vc, send_message)

    elif (msg.startswith('search')):
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
        youtube.enqueue(video_id, video['title'], author_vc, send_message)

    elif (msg == 'skip'):
        if (gachi.is_radio):
            gachi.skip()
        else:
            player.skip()

    elif (msg.startswith('skip')):
        index = msg[len('skip'):].strip()
        if (len(index) == 0):
            return
        # we dont remove actually needed item
        final_index = int(index) - 1
        player.queue = player.queue[final_index:]
        player.skip()
        await send_message(f'Skipped to item #{final_index + 1}')

    elif (msg == 'stop'):
        if (gachi.is_radio):
            gachi.stop()
        else:
            player.stop()

    elif (msg == 'repeat'):
        is_repeat = not player.is_repeat_mode
        await send_message(f'Repeat: {"On" if is_repeat else "Off"}')
        player.is_repeat_mode = is_repeat

    elif (msg == 'queue'):
        items = player.queue
        queue = ''
        for i in range(len(items)): # 01234
            if (len(queue) > 1000):
                queue += f'... {len(items) - i + 1} more\n'
                break
            queue += f'{i + 1}. {items[i].title}\n'
        await send_message(queue)

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