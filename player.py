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
    def __init__(self):
        self.stop_event = asyncio.Event()
        self.stop_event.set()
        self.bot = None

    def is_connected(self): return self._get_client() != None
    def is_playing(self): return self.is_connected() and self._get_client().is_playing()

    def _get_client(self):
        if (len(self.bot.voice_clients) != 1):
            return None
        return self.bot.voice_clients[0]

    async def play_async(self, file_path: str):
        logging.debug(f'Starting playing {file_path}')

        client = self._get_client()
        client.stop()

        logging.debug(f'Stop event is {"not" if not self.stop_event.is_set() else ""}set')
        await self.stop_event.wait()
        self.stop_event.clear()
        
        loop = asyncio.get_event_loop()
        def after(error):
            if error:
                logging.error(error)
            def clear():
                self.stop_event.set()
            loop.call_soon_threadsafe(clear)

        audio = PCMVolumeTransformer(discord.FFmpegPCMAudio(file_path), 1)
        client.play(audio, after=after)

        await self.stop_event.wait()
        logging.debug(f'Finished playing {file_path}')

    async def join_channel(self, voice_channel):
        if (voice_channel == None): return

        if (self.is_connected()):
            if (self._get_client().is_connected()):
                await self._get_client().move_to(voice_channel)
            else:
                logging.warning('Not connected voice client encountered, something bad is going to happen...')
                self.stop_event.set()
                await self._get_client().move_to(voice_channel)
                await self.disconnect()
                await voice_channel.connect()
                pass # TODO do something here probably on server switch
        else:
            await voice_channel.connect()

    def stop(self):
        client = self._get_client()
        if (client == None): return
        client.stop()

    async def disconnect(self):
        client = self._get_client()
        if (client == None):
            return

        await client.disconnect(force=True)

    def initialize(self, bot):
        self.bot = bot

class Player(Voice):
    is_queue_mode = True
    is_repeat_mode = False
    queue = []
    current_item = None

    def __init__(self):
        super().__init__()
        # asyncio.create_task(self.loop())
        
    async def loop(self):
        logging.info('Starting player loop')
        while (True):
            try:
                while (self.is_queue_mode and (len(self.queue) > 0)):
                    while (self.bot.ws.closed):
                        await asyncio.sleep(1)

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
            except Exception as e:
                logging.error('Unhandled error bellow occured in player loop')
                logging.error(e)
            finally:
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
        super().stop()

    def stop(self):
        self.is_repeat_mode = False
        self.queue.clear()
        self.skip()

    async def disconnect(self):
        self.stop()
        await super().disconnect()