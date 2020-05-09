from models.DiscordExtension import DiscordExtension
from models.ExecutionContext import ExecutionContext
from browser import Browser, SearchResultHandle, MusicEntry
from player import Player
import asyncio
import discord
import os
import sys
import logging
from utils.execute_blocking import execute_blocking
from repositories.vkCacheRepository import VkCacheRepository
from models.MusicEntry import MusicEntry

class BrowserExtension(DiscordExtension):
    
    _browser: Browser = None
    _player: Player = None
    _vkCacheRepository: VkCacheRepository = None

    def __init__(self, browser, player, vkCacheRepository):
        self._browser = browser
        self._player = player
        self._vkCacheRepository = vkCacheRepository
        super().__init__()

    @property
    def name(self):
        return 'VK commands'

    def isserving(self, ctx: ExecutionContext):
        return ctx.cmd in ['vk']

    async def execute(self, ctx: ExecutionContext):
        browser = self._browser
        cmd = ctx.cmd

        if (self._browser.isbusy):
            await ctx.send_message('Service is currently busy')
            return

        if (cmd == 'vk'):
            search_finished_event = asyncio.Event()
            ctx.loading_callback(search_finished_event, 'Searching')
            handle: SearchResultHandle = await execute_blocking(browser.search, ctx.args)
            search_finished_event.set()

            try:
                options = list(map(lambda r: f"{r.author} - {r.title} [{r.duration}]", handle.results))
                options = options[:15]

                if (len(options) == 0):
                    await ctx.send_message('Nothing was found :<')
                    return

                index = await ctx.choice_callback(options)
                if (index != None):
                    result: MusicEntry = handle.results[index]
                    title = f'{result.author} - {result.title}'

                    cached_path = self._vkCacheRepository.try_get(result)
                    if (not cached_path):
                        logging.info(f'No cache for vm music {title} was not found, downloading...')
                        loaded_event = asyncio.Event()

                        ctx.loading_callback(loaded_event)
                        actual_path = await execute_blocking(handle.download, index)
                        loaded_event.set()

                        cached_path = self._vkCacheRepository.cache(actual_path, result)

                    if (self._player.is_playing()):
                        await ctx.send_message('Your music was added to queue')

                    self._player.enqueue_with_path(cached_path, title, ctx)
            finally:
                handle.reset()

    def list_commands(self, ctx: ExecutionContext):
        return ['vk <music query>']

    async def initialize(self, bot):
        pass