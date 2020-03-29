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

# https://discordpy.readthedocs.io/en/latest/api.html

bot = commands.Bot(command_prefix = '')
config = None
executors = None

class ExecutionContext:
    def __init__(self, cmd, args, msg, author, author_vc, msg_callback, choice_callback):
        self.cmd = cmd
        self.args = args
        self.msg = msg
        self.author = author
        self.author_vc = author_vc
        self.msg_callback = msg_callback
        self.choice_callback = choice_callback

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
    def list_commands(self):
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

@bot.event
async def on_message(message):
    if (message.channel.type.name != 'private' and 
        message.channel.name != 'bot-exide' or
        message.author == bot.user): return

    message.content = find_replacer(message.content).strip()

    # we also need the 'voice' property which is not being
    # passed in case the message was received via PM
    author = bot.guilds[0].get_member(message.author.id)
    author_vc = author.voice.channel if author.voice != None else None
    
    msg = message.content.lower()
    logging.info(f'{author.display_name} is executing command "{msg}"')

    cmd = message.content.split(' ')[0].lower()
    args = message.content[len(cmd) + 1:].strip()

    async def send_message(msg: str = None, embed: discord.Embed = None):
        logging.info(f'Sending message "{msg}" {"(with embed)" if embed else ""}')
        await message.channel.send(content=msg, embed=embed)

    async def choice_callback(options: []):
        return await choice(options, author.id, send_message)    

    context = ExecutionContext(
        cmd,
        args if len(args) > 0 else None,
        message.content,
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
            for command in executor.list_commands():
                text += f'- {command}\n'
            text += '\n'
        embed = discord.Embed()
        embed.description = text
        await context.msg_callback(None, embed)
        return

    for executor in executors:
        if (not executor.isserving(context)):
            continue
        try:
            await executor.execute(context)
        except Exception as e:
            logging.error(f'Error occured during "{context.msg}" message processing. {e}')
        
@bot.event
async def on_ready():
    for executor in executors:
        await executor.initialize(bot)

    logging.info(f'{bot.user} has connected')

def start(token: str, cfg, command_executors):
    global config, executors
    config, executors = cfg, command_executors
    bot.run(token)