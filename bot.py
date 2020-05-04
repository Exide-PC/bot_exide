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
from messageFormatter import MessageFormatter, MessageType
from utils.execute_blocking import execute_blocking

# https://discordpy.readthedocs.io/en/latest/api.html

class BotExide(discord.Client):

    _executors = None
    _strictMode = False
    _configRepo = None
    _formatter = MessageFormatter()

    def __init__(self, executors, configRepo, loop=None, **options):
        self._executors = executors
        self._configRepo = configRepo
        super().__init__(loop=loop, **options)

    @property
    def strictMode(self):
        return self._strictMode

    @strictMode.setter
    def strictMode(self, value):
        self._strictMode = value

    async def choice(self, options: [], user_id, send_message):
        choice_hint = ""
        for i in range(len(options)):
            choice_hint += f'{i + 1}. {options[i]}'
            choice_hint += '\n' if i != len(options) - 1 else ''

        await send_message(choice_hint)
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
            await self.wait_for('message', check=check, timeout=20)
            return result
        except asyncio.TimeoutError:
            await send_message('Choice timeout')
            pass

    def find_replacer(self, msg):
        while(True):
            msg = msg.strip()
            replacer = None
            for alias in self._configRepo.config['aliases']:
                if (alias[0].lower() == msg.lower()):
                    replacer = alias[1]
                    logging.info(f'Found suitable alias. Replacing "{alias[0]}" with "{alias[1]}"')
            
            if (replacer == None):
                break
            else:
                msg = replacer

        return msg

    async def on_voice_state_update(self, member, before, after):
        protected_members = [
            286920219912306688,
            229987174857179136
        ]
        shved = self.guilds[0].get_member(
            402848249658081307
        )

        if (before.channel == None or after.channel == None): return
        if (member.id not in protected_members or shved.voice == None): return
        if (before.channel.name == after.channel.name): return
        if ('Бочка' not in after.channel.name and 'AFK' not in after.channel.name): return

        after_copy = after.channel # after arguments mutates somehow, idk why

        await member.move_to(before.channel)
        await shved.move_to(after_copy)

    async def on_message(self, message):
        if (message.channel.type.name != 'private' and 
            message.channel.name != 'bot-exide' or
            message.author == self.user): return

        final_message = self.find_replacer(message.content)

        # we also need the 'voice' property which is not being
        # passed in case the message was received via PM
        author = self.guilds[0].get_member(message.author.id)
        author_vc = author.voice.channel if author.voice != None else None
        
        cmd = final_message.split(' ')[0].lower()
        args = final_message[len(cmd) + 1:].strip()

        async def send_message(payload, messageType: MessageType = MessageType.Common):
            (content, embed) = self._formatter.format(payload, messageType)
            logging.info(f'Sending message "{payload}"')
            return await message.channel.send(content=content, embed=embed)

        async def choice_callback(options: []):
            return await self.choice(options, author.id, send_message)

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
            author.id in self._configRepo.config['admins']
        )

        if (context.cmd == 'help'):
            text = ''
            for i in range(len(self._executors)):
                executor = self._executors[i]
                text += f'{i + 1}. {executor.name}\n'
                for command in executor.list_commands(context):
                    text += f'- {command}\n'
                text += '\n'
            await context.send_message(text, MessageType.Embed)
            return

        for executor in self._executors:
            if (not executor.isserving(context)):
                continue
            if (self.strictMode and not context.isadmin):
                await context.send_message('Bot is in strict mode. Only admins can run commands')
                return
            logging.info(f'{author.display_name} is executing command "{message.content}"')
            try:
                await executor.execute(context)
            except ExecutionException as e:
                await context.send_message(e)
                logging.error(f'Error occured during message processing: {e}')
            except Exception as e:
                logging.error(f'Unknown error occured during "{context.msg}" message processing. {e}')
                await context.send_message('Unknown error occured. Contact <@!286920219912306688>')
            
    async def on_ready(self):
        logging.info('Initializing extensions...')
        for executor in self._executors:
            await executor.initialize(self)
        logging.info('Finished extensions initialization')
        logging.info(f'{self.user} has connected')