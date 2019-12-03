
import discord
import time
import asyncio
from discord.voice_client import VoiceClient
from threading import Thread

class VoiceService:
    def __init__(self, voice_client: VoiceClient = None):
        self.set_client(voice_client)

    def set_client(self, voice_client: VoiceClient):
        self.client = voice_client

    def is_connected(self): return self.client != None and self.client.is_connected()
    def is_playing(self): return self.is_connected() and self.client.is_playing()

    def _play(self, file_path: str):
        if (not self.client.is_connected()):
            raise Exception('Voice client is not initialized')
        if (self.client.is_playing()):
            raise Exception('Voice client is already busy')

        audio = discord.FFmpegPCMAudio(file_path)
        self.client.play(
            audio, 
            after=lambda exc: print(str(exc) if exc != None else 'Finished ok')
        )

    def play(self, file_path: str, after):
        def thread():
            self._play(file_path)

            while (True): # post-condition loop
                time.sleep(1)
                if (not self.client.is_playing()):
                    break
            self.client.stop()

        Thread(target=thread).start()

    async def play_async(self, file_path: str):
        self._play(file_path)

        while (True): # post-condition loop
            await asyncio.sleep(1)
            if (not self.client.is_playing()):
                break
        self.client.stop()

    def stop(self):
        self.client.stop()

    async def disconnect(self):
        await self.client.disconnect()
        self.client = None
