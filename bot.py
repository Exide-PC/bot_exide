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

bot = commands.Bot(command_prefix = 'cb!')
# bot = discord.Client()
# voice_client = None
config = None
config_update_callback = None
executors = None

player = None
gachi = None
youtube = None

class ExecutionContext:
    def __init__(self, cmd, args, msg, author, author_vc, msg_callback, choice_callback, player):
        self.cmd = cmd
        self.args = args
        self.msg = msg
        self.author = author
        self.author_vc = author_vc
        self.msg_callback = msg_callback
        self.choice_callback = choice_callback
        self.player = player

class CommandExecutor(abc.ABC):
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

def update_cfg(new_cfg: dict):
    global config
    config_update_callback(new_cfg)
    config = new_cfg

def add_alias(cmd: str, replacer: str):
    global config
    current_aliases = list(map(lambda a: a[0], config['aliases']))

    index = -1
    if (cmd in current_aliases):
        index = current_aliases.index(cmd)

    alias = [cmd, replacer]
    if (index == -1):
        config['aliases'].append(alias)
    else:
        config['aliases'][index] = alias
        
    update_cfg(config)

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
    try:
        if (message.channel.type.name != 'private' and 
            message.channel.name != 'bot-exide' or
            message.author == bot.user): return

        message.content = find_replacer(message.content).strip()

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
        logging.info(f'{author.display_name} is executing command "{msg}"')

        cmd = message.content.split(' ')[0].lower()
        args = message.content[len(cmd) + 1:].strip()

        async def send_message(msg: str = None, embed: discord.Embed = None):
            logging.info(f'Sending message "{msg}" {"(with embed)" if embed else ""}')
            await message.channel.send(content=msg, embed=embed)

        async def choice_callback(options: []):
            return await choice(options, author.id, send_message)    

        global player

        context = ExecutionContext(
            cmd,
            args if len(args) > 0 else None,
            message.content,
            author,
            author_vc,
            send_message,
            choice_callback,
            player
        )

        for executor in executors:
            if (executor.isserving(context)):
                try:
                    await executor.execute(context)
                except Exception as e:
                    logging.error(f'Error occured during command execution. {e}')
                finally:
                    return

        if (cmd == 'gachi'):
            if (args == 'radio'):
                await gachi.radio(context)
            elif (args == 'skip'):
                gachi.skip()
            elif (args == 'stop'):
                gachi.stop()
            elif (args != None):
                await gachi.search(context.args, context)
            elif (args == None):
                await gachi.enqueue(None, context)

        elif (msg.startswith('play')):
            await youtube.play(context.args, context)

        elif (msg.startswith('search')):
            await youtube.search(context.args, context)

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
            if (player.current_item == None):
                queue = 'Nothing is being played currently\n'
            else:
                queue = f'Currently playing: {player.current_item.title}\n'

            for i in range(len(items)):
                if (len(queue) > 1000):
                    queue += f'\n... {len(items) - i + 1} more'
                    break
                queue += f'\n{i + 1}. {items[i].title}'

            embed = discord.Embed()
            embed.description = queue
            await send_message(queue, embed=embed)
        
        elif (msg.startswith('alias')):
            args = message.content[len('alias'):].strip()
            separator = args.find(' ')
            if (separator == -1):
                await send_message('Wrong alias syntax. Use "alias <alias> <replacer>"')
                return
            alias = args[:separator]
            replacer = args[separator + 1:]
            add_alias(alias, replacer)
            await send_message(f'Alias "{alias}" has been successfully added')
    except Exception as e:
        logging.exception(e)
        

@bot.event
async def on_ready():
    global player, gachi, youtube
    player = player or Player(bot)
    gachi = gachi or GachiService(player, config['gachi'])
    youtube = youtube or YoutubeService(player)

    prev_voice = bot.guilds[0].get_member(bot.user.id).voice
    if (prev_voice != None):
        await player.join_channel(prev_voice.channel)

    asyncio.create_task(player.loop())

    logging.info(f'{bot.user} has connected')

def start(token: str, cfg: dict, cfg_update_callback, command_executors):
    global config, config_update_callback, executors
    config, config_update_callback, executors = cfg, cfg_update_callback, command_executors
    bot.run(token)