from models.DiscordExtension import DiscordExtension
from models.ExecutionContext import ExecutionContext
from browser import Browser, SearchHandle, MusicEntry
from player import Player
import asyncio
import discord
import os
import sys
import logging
from utils.execute_blocking import execute_blocking
from repositories.vkCacheRepository import VkCacheRepository
from models.MusicEntry import MusicEntry
from services.vkService import VkService

class VkExtension(DiscordExtension):

    def __init__(self, browser, player, vkCacheRepo):
        self._browser = browser
        self._player = player
        self._vkCacheRepo = vkCacheRepo

    @property
    def name(self):
        return 'VK commands'

    def isserving(self, ctx: ExecutionContext):
        return ctx.cmd in ['vk']

    async def execute(self, ctx: ExecutionContext):
        cmd = ctx.cmd

        if (cmd == 'vk'):
            await self._vkService.search(ctx.args, ctx)

    def list_commands(self, ctx: ExecutionContext):
        return ['vk <music query>']

    async def initialize(self, bot):
        self._vkService = VkService(
            self._browser,
            self._player,
            self._vkCacheRepo
        )