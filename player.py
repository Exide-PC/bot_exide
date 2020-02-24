import asyncio
import discord
import time
from discord.voice_client import VoiceClient
from threading import Thread
from discord.player import PCMVolumeTransformer
import logging
class Item:
    def __init__(self, path_callback, title):
        self.path_callback = path_callback
        self.title = title

class Voice:
    bot = None

    def __init__(self, bot):
        self.bot = bot

    def is_connected(self): return len(self.bot.voice_clients) == 1
    def is_playing(self): return self.is_connected() and self._get_client().is_playing()

    def _get_client(self):
        if (not self.is_connected()):
            return None
        return self.bot.voice_clients[0]

    async def play_async(self, file_path: str):
        logging.debug(f'Starting playing {file_path}')
        if (not self.is_connected()):
            raise Exception('Voice client is not connected')

        client = self._get_client()
        if (client.is_playing()):
            client.stop()

        audio = PCMVolumeTransformer(discord.FFmpegPCMAudio(file_path), 1)
        client.play(audio)

        # waiting for audio to start playing
        while (not client.is_playing()):
            await asyncio.sleep(100)
        # waiting for audio to end

        logging.debug(f'Waiting for {file_path} to end')

        while (client.is_playing()): # post-condition async loop
            await asyncio.sleep(1)
        logging.debug(f'Finished playing {file_path}')

    async def join_channel(self, voice_channel, reconnect: bool = False):
        if (voice_channel == None): return

        if (not self.is_connected()):
            if (reconnect):
                prev_client = await voice_channel.connect()
                await prev_client.disconnect()
            await voice_channel.connect(reconnect=True)
        else:
            await self._get_client().move_to(voice_channel)

    def stop(self):
        client = self._get_client()
        if (client == None): return
        client.stop()

    async def disconnect(self):
        client = self._get_client()
        if (client == None):
            return

        await client.disconnect()

class Player(Voice):
    is_queue_mode = True
    is_repeat_mode = False
    queue = []
    current_item = None

    def __init__(self, bot):
        super().__init__(bot)
        asyncio.create_task(self._loop())
        
    async def _loop(self):
        while (True):
            while (self.is_queue_mode and (len(self.queue) > 0)):
                self.current_item = self.queue.pop(0)
                logging.info(f'Dequeued item {self.current_item.title}')

                file_path = await self.get_path(self.current_item)
                logging.info(f'Received file path: {file_path if file_path != None else "None"}')
                if (file_path == None):
                    continue

                # post-condition loop to play music at least one
                while (True):
                    await self.play_async(file_path)
                    if (not self.is_repeat_mode): break
                    
            self.current_item = None
            await asyncio.sleep(1)

    async def get_path(self, item: Item):
        attempt_limit = 3

        for i in range(attempt_limit):
            try:
                return await item.path_callback()
            except Exception as e:
                if (i != attempt_limit - 1):
                    logging.error(f'Retrying to load item {item.title}...')
                else:
                    logging.error(e)
                    logging.error(f'Could not load item {item.title} after {i + 1} retries')
                    return None

    def enqueue(self, path_callback, title):
        item = Item(path_callback, title)
        self.queue.append(item)

    def skip(self):
        self.current_item = None
        super().stop()

    def stop(self):
        self.queue.clear()
        self.skip()

    async def disconnect(self):
        self.stop()
        await super().disconnect()