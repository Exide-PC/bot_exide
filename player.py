import asyncio
import discord
import time
from discord.voice_client import VoiceClient
from threading import Thread
from discord.player import PCMVolumeTransformer
import logging
import uuid
from models.ExecutionContext import ExecutionContext

class Item:
    def __init__(self, path_callback, short_title, context, payload=None, message_type=None):
        # base
        self.path_callback = path_callback
        self.short_title = short_title
        self.context: ExecutionContext = context
        # rich
        self.payload = payload
        self.message_type = message_type

    def is_formatted(self):
        return self.payload and self.message_type

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
        client = self._get_client()
        client.stop()

        await self.stop_event.wait()
        self.stop_event.clear()

        logging.info(f'Starting playing {file_path}')
        
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
        logging.info(f'Finished playing {file_path}')

    async def join_channel(self, voice_channel):
        if (voice_channel == None): return

        if (self.is_connected()):
            if (self._get_client().is_connected()):
                await self._get_client().move_to(voice_channel)
            else:
                logging.error('Not connected voice client encountered, should never get here!')
                self.stop_event.set()
                await self._get_client().move_to(voice_channel)
                await self.disconnect()
                await voice_channel.connect()
                pass # TODO do something here probably on server switch
        else:
            await voice_channel.connect()
        await asyncio.sleep(0.5)

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
    loop_id = None

    def __init__(self):
        super().__init__()
        # asyncio.create_task(self.loop())
        
    async def loop(self):
        counter = 0
        loop_id = uuid.uuid4().__str__()
        short_id = loop_id[0:8]
        logging.info(f'Starting player loop ({loop_id})')
        while (True):
            try:
                while (self.is_queue_mode and (len(self.queue) > 0)):

                    item: Item = self.queue.pop(0)
                    self.current_item = item
                    logging.info(f'Dequeued item {item.short_title} ({short_id})')

                    if (not item.context.voice_channel()):
                        logging.info(f'{item.context.author.name} requested a song not being in voice channel')
                        continue

                    await self.ensure_connection()
                    file_path = await self.get_path(item)

                    logging.info(f'Received file path: {file_path} ({short_id})')
                    if (file_path == None):
                        continue

                    await self.ensure_connection()
                    await self.join_channel(item.context.voice_channel())
                    await self.notify_playing(item)

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
                await self.ensure_connection()
                counter += 1
                if (counter % 1200 == 0):
                    logging.debug(f'Loop guid: {short_id}')

    async def get_path(self, item: Item):
        attempt_limit = 5

        for i in range(attempt_limit):
            try:
                return await item.path_callback()
            except Exception as e:
                delay = i * 3 + 1
                if (i != attempt_limit - 1):
                    logging.warning(f'Retrying to load item {item.short_title} in {delay} second(s)...')
                    await asyncio.sleep(delay)
                else:
                    logging.error(e)
                    logging.error(f'Could not load item {item.short_title} after {i + 1} retries')
                    return None

    async def ensure_connection(self):
        # waiting for connection establishment
        while (True):
            socket_ok = not self.bot.ws.closed
            client = self._get_client()
            voice_ok = client == None or client.is_connected()

            if (socket_ok and voice_ok):
                break

            if (not socket_ok):
                logging.warning(f'Closed socket state encountered')
            if (not voice_ok):
                logging.warning(f'Invalid voice client encountered')

            await asyncio.sleep(3)

    async def notify_playing(self, item: Item):
        if (item.is_formatted()):
            await item.context.send_message(item.payload, item.message_type)
        else:
            await item.context.send_message(f'Now playing: {item.short_title}')

    def enqueue(self, path_callback, short_title, ctx):
        item = Item(path_callback, short_title, ctx)
        self.queue.append(item)

    def enqueue_with_path(self, path, short_title, ctx):
        async def path_wrapper():
            return path
        self.enqueue(path_wrapper, short_title, ctx)

    def enqueue_rich(self, path_callback, short_title, ctx, payload, message_type):
        item = Item(path_callback, short_title, ctx, payload, message_type)
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