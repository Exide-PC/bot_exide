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
    send_message = None
    _gachi_list = None
    _player = None
    _queue = []
    message_callback = None

    async def enqueue(self, gachi, ctx):
        self.message_callback = ctx.send_message
        
        if (gachi == None):
            gachi = random.choice(self._gachi_list)

        video_id = gachi['videoId']
        title = gachi["title"]

        async def item_callback():
            return youtube.download_sound(video_id)

        self._player.enqueue(item_callback, title, ctx)

        if (self._player.is_playing()):
            await ctx.send_message(f'{title} was added to queue')

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

    async def radio(self, ctx):
        if (ctx.voice_channel() == None):
            return

        is_radio = not self.is_radio
        await ctx.send_message(f'Gachi radio is {"On" if is_radio else "Off"}')

        if (is_radio):
            await self._player.join_channel(ctx.voice_channel())
            self.message_callback = ctx.send_message
            asyncio.create_task(self._radio_loop())
        else:
            self.stop()
        self.is_radio = is_radio

    async def search(self, query, ctx):
        if (ctx.voice_channel() == None):
            return

        search_results = self._search(query)
        if (len(search_results) == 0):
            await ctx.send_message('Nothing was found :c')
            return

        options = list(map(lambda g: g['title'], search_results))
        selected_index = await ctx.choice_callback(options)
        if (selected_index == None):
            return
        selected_gachi = search_results[selected_index]
        
        await self.enqueue(selected_gachi, ctx)

    def _search(self, keyword: str) -> []:
        if (keyword == None):
            return []

        return list(filter(
            lambda g: keyword.lower() in g['title'].lower(), 
            self._gachi_list
        ))

    def skip(self):
        self._player.skip()

    def stop(self):
        self.is_radio = False
        self._player.skip()

    def __init__(self, player: Player, configRepo):
        self._player = player
        self._gachi_list = configRepo.get_gachi_list()