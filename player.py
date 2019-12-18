import asyncio
import discord
import time
from discord.voice_client import VoiceClient
from threading import Thread
from discord.player import PCMVolumeTransformer

class Voice:
    client = None
    channel = None
    current_file = None

    def is_connected(self): return self.client != None and self.client.is_connected()
    def is_playing(self): return self.is_connected() and self.client.is_playing()

    async def _play(self, file_path: str, is_max_volume=False):
        if (self.client == None):
            raise Exception('Voice client does not exist')
        if (not self.is_connected()):
            raise Exception('Voice client is not connected')
        if (self.is_playing()):
            self.stop()

        audio = PCMVolumeTransformer(
            discord.FFmpegPCMAudio(file_path), 
            2 if is_max_volume else 1
        )
        self.current_file = file_path
        self.client.play(audio)

        while (not self.is_playing()):
            await asyncio.sleep(100)

    async def play_async(self, file_path: str, is_max_volume=False):
        await self._play(file_path, is_max_volume)

        while (True): # post-condition async loop
            await asyncio.sleep(1)
            if (not self.is_playing() or file_path != self.current_file):
                break
        if (self.current_file == file_path):
            self.current_file = None

    async def join_channel(self, voice_channel, reconnect: bool = False):
        if (voice_channel == None): return
        self.channel = voice_channel

        if (not self.is_connected()):
            if (reconnect):
                prev_client = await voice_channel.connect()
                await prev_client.disconnect()
            voice_client = await voice_channel.connect()
            self.client = voice_client
        else:
            await self.client.move_to(voice_channel)

    def stop(self):
        self.current_file = None
        self.client.stop()

    async def disconnect(self):
        if (not self.is_connected()):
            return

        await self.client.disconnect()
        self.client = None
        self.channel = None
        self.current_file = None

class Player(Voice):
    is_queue_mode = True
    is_repeat_mode = False
    queue = []

    def __init__(self):
        super().__init__()
        asyncio.create_task(self._loop())
        
    async def _loop(self):
        while (True):
            while (self.is_queue_mode and (len(self.queue) > 0)):
                item_callback = self.queue.pop(0)
                file_path = await item_callback()
                if (file_path == None): continue

                # post-condition loop to play music at least one
                while (True):
                    await self.play_async(file_path)
                    if (not self.is_repeat_mode): break
            await asyncio.sleep(1)

    def enqueue(self, item_callback):
        self.queue.append(item_callback)

    def skip(self):
        self.stop()