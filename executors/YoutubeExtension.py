from models.DiscordExtension import DiscordExtension
from models.ExecutionContext import ExecutionContext
from player import Player
import asyncio
import discord
from youtube import YoutubeService

class YoutubeExtension(DiscordExtension):

    def __init__(self, player: Player, configRepo):
        super().__init__()
        self._service = YoutubeService(player, configRepo)

    @property
    def name(self):
        return 'Youtube commands'

    def isserving(self, ctx: ExecutionContext):
        return ctx.cmd in ['play', 'search']

    async def execute(self, ctx: ExecutionContext):
        service = self._service
        cmd = ctx.cmd
        args = ctx.args

        if (cmd == 'play'):
            await service.play(args, ctx)

        elif (cmd == 'search'):
            await service.search(args, ctx)

    def list_commands(self, ctx: ExecutionContext):
        return [
            'play <video url>',
            'play <timecode> <video url> (timecodes: 13:37, 13:37-14:56)',
            'play <playlist url>',
            'search <query>'
        ]

    async def initialize(self, bot):
        pass