import discord
import time
import asyncio
from discord.voice_client import VoiceClient
from threading import Thread
from discord.player import PCMVolumeTransformer

class Player:
    client = None
    channel = None
    current_file = None

    def is_connected(self): return self.client != None and self.client.is_connected()
    def is_playing(self): return self.is_connected() and self.client.is_playing()

    def _play(self, file_path: str, is_max_volume=False):
        if (self.client == None):
            raise Exception('Voice client does not exist')
        if (not self.is_connected()):
            raise Exception('Voice client is not connected')
        if (self.client.is_playing()):
            self.stop()

        audio = PCMVolumeTransformer(
            discord.FFmpegPCMAudio(file_path), 
            2 if is_max_volume else 1
        )
        self.current_file = file_path
        self.client.play(audio)

    def play(self, file_path: str, is_max_volume=False, after=None):
        def thread():
            self._play(file_path, is_max_volume)

            while (True): # post-condition blocking loop
                time.sleep(1)
                if (not self.client.is_playing() or file_path != self.current_file):
                    break
            if (self.current_file == file_path):
                self.current_file = None
            if (after != None): after()
            # self.client.stop()

        Thread(target=thread).start()

    async def play_async(self, file_path: str, is_max_volume=False):
        self._play(file_path, is_max_volume)

        while (True): # post-condition async loop
            await asyncio.sleep(1)
            if (not self.client.is_playing() or file_path != self.current_file):
                break
        if (self.current_file == file_path):
            self.current_file = None
            # self.client.stop()

    async def join_channel(self, voice_channel, reconnect=False):
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
        if (self.client.is_playing()):
            raise Exception('Can\'t disconnect while something is playing')
            
        await self.client.disconnect()
        self.client = None
