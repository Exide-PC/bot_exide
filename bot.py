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
import abc
import os
import sys
from concurrent.futures.thread import ThreadPoolExecutor
from models.ExecutionException import ExecutionException

# https://discordpy.readthedocs.io/en/latest/api.html

bot = commands.Bot(command_prefix = '')
config = None
update_config = (lambda cfg: None)
executors = None

class ExecutionContext:
    def __init__(self, cmd, args, msg, author, author_vc, msg_callback, choice_callback):
        global execute_blocking, config
        self.cmd = cmd
        self.args = args
        self.msg = msg
        self.author = author
        self.author_vc = author_vc
        self.msg_callback = msg_callback
        self.choice_callback = choice_callback
        self.execute_blocking = execute_blocking
        self.config = config

    def update_config(self, new_cfg):
        global update_config
        update_config(new_cfg)
        self.config = new_cfg

class DiscordExtension(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self):
        pass

    @abc.abstractmethod
    def isserving(self, ctx: ExecutionContext):
        pass

    @abc.abstractmethod
    async def execute(self, ctx: ExecutionContext):
        pass

    @abc.abstractmethod
    def list_commands(self, ctx: ExecutionContext):
        pass

    async def initialize(self, bot):
        pass

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
        for alias in config['aliases']:
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
        await message.channel.send(content=msg, embed=embed)

    async def choice_callback(options: []):
        return await choice(options, author.id, send_message)    

    context = ExecutionContext(
        cmd,
        args if len(args) > 0 else None,
        final_message,
        author,
        author_vc,
        send_message,
        choice_callback
    )

    if (context.cmd == 'help'):
        text = ''
        for i in range(len(executors)):
            executor = executors[i]
            text += f'{i + 1}. {executor.name}\n'
            for command in executor.list_commands(context):
                text += f'- {command}\n'
            text += '\n'
        embed = discord.Embed()
        embed.description = text
        await context.msg_callback(None, embed)
        return
    
    elif (context.cmd == 'reboot'):
        if (context.author.id in config['admins']):
            logging.info(f'{context.author.display_name} invoked reboot')
            os.system('start startup.py')
            sys.exit()
        else:
            logging.info(f'Unathorized reboot attempt from {context.author.display_name}, kicking...')
            await context.msg_callback('Hey buddy, i think you got the wrong door, the leather-club is two blocks down')
            await asyncio.sleep(2)
            await context.author.move_to(None)

    for executor in executors:
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
    for executor in executors:
        await executor.initialize(bot)

    logging.info(f'{bot.user} has connected')

def start(token: str, cfg, command_executors, update_cfg):
    global config, executors, update_config
    config, executors, update_config = cfg, command_executors, update_cfg
    bot.run(token)