from models.DiscordExtension import DiscordExtension
from models.ExecutionContext import ExecutionContext
from browser import Browser, SearchResultProvider
from player import Player
import asyncio
import discord
import os
import sys
import logging
from utils.execute_blocking import execute_blocking

class BrowserExtension(DiscordExtension):
    
    _browser: Browser = None

    def __init__(self, browser):
        self._browser = browser
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
            result: SearchResultProvider = await execute_blocking(browser.search, ctx.args)
            options = list(map(lambda r: f"{r['author']} - {r['title']} [{r['duration']}]", result.results))
            options = options[:15]

            try:
                index = await ctx.choice_callback(options)
                if (index != -1):
                    await ctx.send_message(index)
            finally:
                result.reset()

    def list_commands(self, ctx: ExecutionContext):
        return ['vk <music query>']

    async def initialize(self, bot):
        pass