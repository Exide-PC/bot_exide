from models.DiscordExtension import DiscordExtension
from models.ExecutionContext import ExecutionContext
from player import Player
import asyncio
import discord
import logging
from utils.execute_blocking import execute_blocking

class SyncTubeExtension(DiscordExtension):
    def __init__(self, browser):
        self._browser = browser
        super().__init__()

    @property
    def name(self):
        return 'SyncTube'

    def isserving(self, ctx: ExecutionContext):
        return ctx.cmd in ['room']

    async def execute(self, ctx: ExecutionContext):
        video_url = ctx.args

        room_url = await execute_blocking(self._browser.create_room, video_url)
        await ctx.send_message(f'Room is created: {room_url}')

    def list_commands(self, ctx: ExecutionContext):
        return ['room <url>']

    async def initialize(self, bot):
        pass