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

    def __init__(self, browser, player, configRepo):
        self._browser = browser
        self._player = player
        self._vkCacheRepo = VkCacheRepository()
        self._configRepo = configRepo

    @property
    def name(self):
        return 'VK commands'

    def isserving(self, ctx: ExecutionContext):
        return ctx.cmd in ['vk', 'vk-add']

    async def execute(self, ctx: ExecutionContext):
        cmd = ctx.cmd

        if (cmd == 'vk'):
            # await self._vkService.search(ctx.args, ctx)
            await ctx.send_message('Vk music search is currently disabled, use command "vk-add <vk_user_id>"')
        elif (cmd == 'vk-add'):
            try:
                vk_user_id  = int(ctx.args)
                discord_user_id = ctx.author.id
                await self._vkService.bind_user(vk_user_id, discord_user_id, ctx)
            except ValueError:
                await ctx.send_message('Incorrect vk user id')

    def list_commands(self, ctx: ExecutionContext):
        return [
            'vk <music query>',
            'vk-add <vk_user_id> - bind vk user id'
        ]

    async def initialize(self, bot):
        self._vkService = VkService(
            bot,
            self._browser,
            self._player,
            self._vkCacheRepo,
            self._configRepo
        )