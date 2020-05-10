import requests
from requests.models import PreparedRequest
from browser import Browser, SearchHandle, MusicEntry
from repositories.vkCacheRepository import VkCacheRepository
from player import Player
from utils.env import env
import asyncio
from utils.execute_blocking import execute_blocking
import logging

class VkService:

    _browser: Browser = None
    _player: Player = None
    _vkCacheRepository: VkCacheRepository = None

    def __init__(self, browser, player, vkCacheRepository):
        self._browser = browser
        self._player = player
        self._vkCacheRepository = vkCacheRepository

    async def search(self, query, ctx):
        if (self._browser.isbusy):
            await ctx.send_message('Service is currently busy')
            return

        search_finished_event = asyncio.Event()
        ctx.loading_callback(search_finished_event, 'Searching')
        try:
            handle: SearchHandle = await execute_blocking(self._browser.search, ctx.args)
        finally:
            search_finished_event.set()

        with handle:
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
                    try:
                        actual_path = await execute_blocking(handle.download, index)
                    finally:
                        loaded_event.set()

                    cached_path = self._vkCacheRepository.cache(actual_path, result)

                if (self._player.is_playing()):
                    await ctx.send_message('Your music was added to queue')

                self._player.enqueue_with_path(cached_path, title, ctx)

