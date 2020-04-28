import os
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.voice_client import VoiceClient
from discord.opus import load_opus
from dotenv import load_dotenv
import random
import asyncio
from youtube import YoutubeService
from player import Player
from gachi_service import GachiService
import re
import logging
import os
import sys
from concurrent.futures.thread import ThreadPoolExecutor
from models.DiscordExtension import DiscordExtension
from models.ExecutionContext import ExecutionContext
from models.ExecutionException import ExecutionException

# https://discordpy.readthedocs.io/en/latest/api.html

bot = commands.Bot(command_prefix = '')
_executors = None
_configRepo = None
_strictMode = False

async def choice(options: [], user_id, msg_callback):
    choice_hint = ""
    for i in range(len(options)):
        choice_hint += f'{i + 1}. {options[i]}'
        choice_hint += '\n' if i != len(options) - 1 else ''

    await msg_callback(choice_hint)
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
        await msg_callback('Choice timeout')
        pass

def find_replacer(msg):
    while(True):
        replacer = None
        for alias in _configRepo.config['aliases']:
            if (alias[0].lower() == msg.lower()):
                replacer = alias[1]
                logging.info(f'Found suitable alias. Replacing "{alias[0]}" with "{alias[1]}"')
        
        if (replacer == None):
            break
        else:
            msg = replacer

    return msg

@bot.event
async def on_voice_state_update(member, before, after):
    protected_members = [
        286920219912306688,
        229987174857179136
    ]
    shved = bot.guilds[0].get_member(
        402848249658081307
    )

    if (before.channel == None or after.channel == None): return
    if (member.id not in protected_members or shved.voice == None): return
    if (before.channel.name == after.channel.name): return
    if ('Бочка' not in after.channel.name and 'AFK' not in after.channel.name): return

    after_copy = after.channel # after arguments mutates somehow, idk why

    await member.move_to(before.channel)
    await shved.move_to(after_copy)

async def execute_blocking(fun, *args):
    logging.info('Executing blocking function...')
    executor = ThreadPoolExecutor(1)
    loop = asyncio.get_event_loop()
    blocking_tasks = [loop.run_in_executor(executor, fun, *args)]
    completed, pending = await asyncio.wait(blocking_tasks)
    for t in completed:
        result = t.result()
        logging.info(f'Executed blocking function. Result: {result}')
        return result

@bot.event
async def on_message(message):
    if (message.channel.type.name != 'private' and 
        message.channel.name != 'bot-exide' or
        message.author == bot.user): return

    final_message = find_replacer(message.content).strip()

    # we also need the 'voice' property which is not being
    # passed in case the message was received via PM
    author = bot.guilds[0].get_member(message.author.id)
    author_vc = author.voice.channel if author.voice != None else None
    
    cmd = final_message.split(' ')[0].lower()
    args = final_message[len(cmd) + 1:].strip()

    async def send_message(msg: str = None, embed: discord.Embed = None):
        logging.info(f'Sending message "{msg}" {"(with embed)" if embed else ""}')
        return await message.channel.send(content=msg, embed=embed)

    async def choice_callback(options: []):
        return await choice(options, author.id, send_message)

    def loading_callback(stop_event):
        async def loading_async():
            await asyncio.sleep(3)
            if (stop_event.is_set()): return
            
            status_message = await send_message('Loading')
            counter = 0
            while (not stop_event.is_set()):
                dots = counter % 3 + 1
                await status_message.edit(content=f'Loading{"." * dots}')
                await asyncio.sleep(1)
                counter += 1
            await status_message.delete()

        loop = asyncio.get_event_loop()
        loop.create_task(loading_async())

    context = ExecutionContext(
        cmd,
        args if len(args) > 0 else None,
        final_message,
        author,
        author_vc,
        send_message,
        choice_callback,
        loading_callback,
        execute_blocking,
        author.id in _configRepo.config['admins']
    )

    if (context.cmd == 'help'):
        text = ''
        for i in range(len(_executors)):
            executor = _executors[i]
            text += f'{i + 1}. {executor.name}\n'
            for command in executor.list_commands(context):
                text += f'- {command}\n'
            text += '\n'
        embed = discord.Embed()
        embed.description = text
        await context.msg_callback(None, embed)
        return
    
    elif (context.cmd == 'reboot'):
        if (context.isadmin):
            logging.info(f'{context.author.display_name} invoked reboot')
            os.system('git pull')
            os.system('start startup.py')
            sys.exit()
        else:
            logging.info(f'Unathorized reboot attempt from {context.author.display_name}, kicking...')
            await context.msg_callback('Hey buddy, i think you got the wrong door, the leather-club is two blocks down')
            await asyncio.sleep(2)
            await context.author.move_to(None)

    elif (context.cmd == 'strict'):
        if (context.isadmin):
            _strictMode = not _strictMode
            await context.msg_callback(f'Strict mode: {"On" if _strictMode else "Off"}')

    if (_strictMode and not context.isadmin):
        return

    for executor in _executors:
        if (not executor.isserving(context)):
            continue
        logging.info(f'{author.display_name} is executing command "{message.content}"')
        try:
            await executor.execute(context)
        except ExecutionException as e:
            await context.msg_callback(e)
            logging.error(f'Error occured during message processing: {e}')
        except Exception as e:
            logging.error(f'Unknown error occured during "{context.msg}" message processing. {e}')
        
@bot.event
async def on_ready():
    for executor in _executors:
        await executor.initialize(bot)

    logging.info(f'{bot.user} has connected')

def start(token: str, executors, configRepo):
    global _executors, _configRepo
    _executors, _configRepo = executors, configRepo
    bot.run(token)