import discord
import time
import asyncio
import random
import youtube
from discord.voice_client import VoiceClient
from threading import Thread
from discord.player import PCMVolumeTransformer
from player import Player

class GachiService:
    is_radio = False
    msg_callback = None
    current = None
    _gachi_list = None
    _player = None
    _queue = []
    message_callback = None

    def search(self, search: str) -> []:
        if (search == None):
            return []

        return list(filter(
            lambda g: search.lower() in g['title'].lower(), 
            self._gachi_list
        ))

    async def enqueue(self, search: str, msg_callback):
        self.message_callback = msg_callback
        
        if (search != None and len(search) > 0):
            search_results = search(search)
        else:
            search_results = [random.choice(self._gachi_list)]
            
        if (len(search_results) == 0):
            await msg_callback(f'Nothing was found by keyphrase "{search}"')
            return False

        chosen_gachi = search_results[0] # TODO: Add search results dialog
        self._queue.append(chosen_gachi)

        if (self._player.is_playing()):
            if (not self.is_radio):
                await msg_callback(f'{chosen_gachi["title"]} was added to queue')
            else:
                await msg_callback(f'Gachi radio is already active')
        
        return True

    async def _loop(self):
        while (True):
            while (self._player.is_connected() and (len(self._queue) > 0 or self.is_radio)):
                next_gachi = random.choice(self._gachi_list) if self.is_radio else self._queue.pop(0)
                self.current = next_gachi['title']

                await self.message_callback(f'Now playing: {next_gachi["title"]}')
                file_path = youtube.download_sound(next_gachi['videoId'])

                await self._player.play_async(file_path)
            await asyncio.sleep(1)

    def radio(self, is_active: bool, message_callback=None):
        self.message_callback = message_callback
        self.is_radio = is_active
    
    def entry(self):
        asyncio.run(self._loop())

    def __init__(self, player: Player, gachi_list: []):
        self._player = player
        self._gachi_list = gachi_list

        asyncio.create_task(self._loop())