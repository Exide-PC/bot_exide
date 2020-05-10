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
from utils.linq import first
from utils.env import env

# https://discordpy.readthedocs.io/en/latest/api.html

class BotExide(discord.Client):

    _extensions = None
    _strictMode = False
    _configRepo = None
    _formatter = MessageFormatter()
    _initialized = False

    def __init__(self, extensions, configRepo, loop=None, **options):
        self._extensions = extensions
        self._configRepo = configRepo
        super().__init__(loop=loop, **options)

    @property
    def strictMode(self):
        return self._strictMode

    @strictMode.setter
    def strictMode(self, value):
        self._strictMode = value

    def __create_send_message(self, channel):
        async def send_message(payload, messageType: MessageType = MessageType.Common):
            (content, embed) = self._formatter.format(payload, messageType)
            logging.info(f'Sending message "{payload}"')
            return await channel.send(content=content, embed=embed)

        return send_message

    def __create_choice_dialog(self, author_id, send_message):
        async def choice_dialog_impl(options: []):
            options_content = ""
            for i in range(len(options)):
                content_preview = options_content + f'{i + 1}. {options[i]}'
                content_preview += '\n' if i != len(options) - 1 else ''
                if (len(content_preview) >= 1900): # 2000 max, but remaining some chars for service stuff
                    logging.info('Choice options take more than 2000 chars, truncating...')
                    break
                options_content = content_preview

            await send_message(options_content)
            result = None

            def check(m):
                if (m.author.id != author_id): return False
                if (m.content == 'cancel'): return True
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

        return choice_dialog_impl

    def __create_loading(self, send_message):
        def loading_impl(stop_event, message='Loading'):
            async def loading_async():
                await asyncio.sleep(2)
                if (stop_event.is_set()): return

                messageType = MessageType.Italic
                status_message = await send_message(message, messageType)

                counter = 0
                while (not stop_event.is_set()):
                    dots = counter % 3 + 1
                    (content, embed) = self._formatter.format(f'{message}{"." * dots}', messageType)
                    await status_message.edit(content=content, embed=embed)
                    await asyncio.sleep(1)
                    counter += 1
                await status_message.delete()

            loop = asyncio.get_event_loop()
            loop.create_task(loading_async())

        return loading_impl

    def __find_replacer(self, msg):
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

        final_message = self.__find_replacer(message.content)
        author = self.guilds[0].get_member(message.author.id)
        
        cmd = final_message.split(' ')[0].lower()
        args = final_message[len(cmd) + 1:].strip()

        send_message = self.__create_send_message(message.channel)
        choice_dialog = self.__create_choice_dialog(author.id, send_message)
        loading = self.__create_loading(send_message)

        context = ExecutionContext(
            cmd,
            args if len(args) > 0 else None,
            final_message,
            author,
            send_message,
            choice_dialog,
            loading,
            author.id in self._configRepo.config['admins']
        )

        if (context.cmd == 'help'):
            text = ''
            for i in range(len(self._extensions)):
                executor = self._extensions[i]
                text += f'{i + 1}. {executor.name}\n'
                for command in executor.list_commands(context):
                    text += f'- {command}\n'
                text += '\n'
            await context.send_message(text, MessageType.Embed)
            return

        for executor in self._extensions:
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
        if (self._initialized):
            return

        logging.info('Initializing extensions...')
        for executor in self._extensions:
            await executor.initialize(self)
        logging.info('Finished extensions initialization')
        logging.info(f'{self.user} has connected')

        if (env.is_production):
            channel = first(self.guilds[0].channels, lambda c: c.name == 'bot-exide')
            (content, embed) = self._formatter.format('Bot connected', MessageType.Italic)
            await channel.send(content=content, embed=embed)

        self._initialized = True