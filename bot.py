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
import re

bot = commands.Bot(command_prefix = 'cb!')
# bot = discord.Client()
# voice_client = None
config = None
config_update_callback = None

voice = None

gachi_queue = []
is_gachi_radio = False

def update_cfg(new_cfg: dict):
    global config
    config_update_callback(new_cfg)
    config = new_cfg

async def connect_to(user):
    global voice
    voice_channel = user.voice.channel
    if (voice_channel == None): return

    if (not voice.is_connected()):
        voice_client = await voice_channel.connect()
        voice.set_client(voice_client)
    else:
        await voice.client.move_to(voice_channel)

async def gachi_loop(message, search_value=None):
    gachi_list = config['gachi']
    if (search_value != None and len(search_value) > 0):
        gachi_list = list(filter(
            lambda g: search_value.lower() in g['title'].lower(), 
            gachi_list
        ))
    if (len(gachi_list) == 0):
        await message.channel.send(f'Nothing was found by keyphrase "{search_value}"')
        return

    global voice
    # TODO hold info about the channel to join for each queue entry
    await connect_to(message.author)

    chosen_gachi = random.choice(gachi_list)
    gachi_queue.append(chosen_gachi)
    
    if (voice.is_playing()):
        if (not is_gachi_radio):
            await message.channel.send(f'{chosen_gachi["title"]} was added to queue')
        else:
            await message.channel.send(f'Gachi radio is already active')
        return

    while (len(gachi_queue) > 0 or is_gachi_radio):
        next_gachi = gachi_queue[0] if not is_gachi_radio else random.choice(gachi_list)

        await message.channel.send(f'Now playing: {next_gachi["title"]}')
        file_path = youtube.download_sound(next_gachi['videoId'])

        await voice.play_async(file_path)

        if (len(gachi_queue) > 0):
            gachi_queue.pop(0)

    await voice.disconnect()

@bot.event
async def on_message(message):
    if (message.author == bot.user):
        return
    
    msg = message.content
    global voice, is_gachi_radio

    # message mapping if necessary
    if (msg.lower() == 'gachi depression'):
        msg = 'play https://www.youtube.com/watch?v=nbzFQD2Q3rs'

    if (msg.lower() == 'gachi radio'):
        is_gachi_radio = True
        await gachi_loop(message)
    elif (msg.lower() == 'gachi skip'):
        voice.stop()
    elif (msg.lower() == 'gachi stop'):
        if (voice.is_connected() and voice.is_playing()):
            is_gachi_radio = False
            voice.stop()
    elif (msg.lower() == 'gachi help'):
        await message.channel.send('Commands: gachi [radio,skip,stop,*search value*]')
    elif (msg.lower().startswith('gachi')):
        search = msg[len('gachi'):].strip()
        await gachi_loop(message, search)
    elif (msg.lower() == 'join'):
        if (message.channel.type.name != 'private'): return
        member = bot.guilds[0].get_member(message.author.id)
        if (member.voice == None): return
        voice_client = await member.voice.channel.connect(timeout = 10)
    elif (msg.lower() == 'disc'):
        if (message.channel.type.name != 'private' or voice_client == None): return
        await voice_client.disconnect()
    elif (msg.lower().startswith('play')):
        matches = re.findall('v=[\w-]+', msg[len('play'):].strip())
        if (len(matches) != 1):
            await message.channel.send('Wrong youtube video url')
            return
        video_id = matches[0][2:] # skipping v=
        file_path = youtube.download_sound(video_id)
        await connect_to(message.author)
        await voice.play_async(file_path)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected\n')

def start(token: str, cfg: dict, cfg_update_callback):
    global config, config_update_callback, voice
    config, config_update_callback = cfg, cfg_update_callback
    voice = VoiceService()
    bot.run(token)