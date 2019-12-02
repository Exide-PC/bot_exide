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

# bot = commands.Bot()
bot = discord.Client()
voice_client = None
config = None
config_update_callback = None

gachi_queue = []
is_gachi_radio = False

def update_cfg(new_cfg: dict):
    global config
    config_update_callback(new_cfg)
    config = new_cfg

async def gachi_loop(message, search_value=None):
    # grab user's voice channel
    voice_channel = message.author.voice.channel
    if (voice_channel == None):
        return

    gachi_list = config['gachi']
    if (search_value != None and len(search_value) > 0):
        gachi_list = list(filter(
            lambda g: search_value.lower() in g['title'].lower(), 
            gachi_list
        ))
    if (len(gachi_list) == 0):
        await message.channel.send(f'Nothing was found by keyphrase "{search_value}"')
        return

    global voice_client
    # TODO hold info about the channel to join for each queue entry
    if (voice_client == None):
        voice_client = await voice_channel.connect()
    else:
        await voice_client.move_to(voice_channel)

    chosen_gachi = random.choice(gachi_list)
    gachi_queue.append(chosen_gachi)
    
    if (voice_client.is_playing()):
        await message.channel.send(f'{chosen_gachi["title"]} was added to queue')
        return

    while (len(gachi_queue) > 0 or is_gachi_radio):
        next_gachi = gachi_queue[0] if not is_gachi_radio else random.choice(gachi_list)

        await message.channel.send(f'Now playing: {next_gachi["title"]}')
        file_path = youtube.download_sound(next_gachi['videoId'])

        audio = discord.FFmpegPCMAudio(file_path)
        voice_client.play(
            audio, 
            after=lambda exc: print(str(exc) if exc != None else 'Finished ok')
        )
        
        while (voice_client.is_playing()):
            await asyncio.sleep(1)

        if (len(gachi_queue) > 0):
            gachi_queue.pop(0)
        voice_client.stop()

    await voice_client.disconnect()
    voice_client = None

@bot.event
async def on_message(message):
    if (message.author == bot.user):
        return
    
    msg = message.content
    global voice_client, is_gachi_radio

    if (msg.lower() == 'gachi radio'):
        is_gachi_radio = True
        await gachi_loop(message)
    if (msg.lower() == 'gachi skip'):
        voice_client.stop()
    elif (msg.lower() == 'gachi stop'):
        if (voice_client != None and voice_client.is_playing()):
            is_gachi_radio = False
            voice_client.stop()
    elif (msg.lower() == 'gachi help'):
        await message.channel.send('Commands: gachi [radio,skip,stop,*search value*]')
    elif (msg.lower().startswith('gachi')):
        search = msg[len('gachi'):].strip()
        await gachi_loop(message, search)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected\n')

def start(token: str, cfg: dict, cfg_update_callback):
    global config, config_update_callback
    config, config_update_callback = cfg, cfg_update_callback
    bot.run(token)