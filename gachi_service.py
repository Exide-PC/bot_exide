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
    _gachi_list = None
    _player = None
    _queue = []
    message_callback = None

    def search(self, keyword: str) -> []:
        if (keyword == None):
            return []

        return list(filter(
            lambda g: keyword.lower() in g['title'].lower(), 
            self._gachi_list
        ))

    async def enqueue(self, gachi, channel, msg_callback):
        self.message_callback = msg_callback
        
        if (gachi == None):
            gachi = random.choice(self._gachi_list)

        video_id = gachi['videoId']
        title = gachi["title"]

        async def item_callback():
            await self._player.join_channel(channel)
            await msg_callback(f'Now playing: {title}')
            return youtube.download_sound(video_id)
        self._player.enqueue(item_callback, title)

        if (self._player.is_playing()):
            await msg_callback(f'{title} was added to queue')

    async def _radio_loop(self):
        # deactivate queue mode while radio is active
        self._player.is_queue_mode = False

        while (self.is_radio and self._player.is_connected()):
            next_gachi = random.choice(self._gachi_list)

            await self.message_callback(f'Now playing: {next_gachi["title"]}')
            file_path = youtube.download_sound(next_gachi['videoId'])

            await self._player.play_async(file_path)
            await asyncio.sleep(1)
        self._player.is_queue_mode = True

    async def radio(self, channel, message_callback=None):
        is_radio = not self.is_radio
        await message_callback(f'Gachi radio is {"On" if is_radio else "Off"}')

        if (is_radio):
            await self._player.join_channel(channel)
            self.message_callback = message_callback
            asyncio.create_task(self._radio_loop())
        else:
            self.stop()
        self.is_radio = is_radio

    def skip(self):
        self._player.skip()

    def stop(self):
        self.is_radio = False
        self._player.skip()

    def __init__(self, player: Player, gachi_list: []):
        self._player = player
        self._gachi_list = gachi_list