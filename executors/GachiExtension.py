from models.DiscordExtension import DiscordExtension
from models.ExecutionContext import ExecutionContext
from player import Player
import asyncio
import discord

class GachiExtension(DiscordExtension):
    def __init__(self, gachi_service):
        super().__init__()
        self.service = gachi_service

    @property
    def name(self):
        return 'Gachi commands'

    def isserving(self, ctx: ExecutionContext):
        return ctx.cmd in ['gachi', 'skip', 'stop']

    async def execute(self, ctx: ExecutionContext):
        service = self.service
        cmd = ctx.cmd
        args = ctx.args

        if (cmd == 'gachi'):
            if (args == 'radio'):
                    await service.radio(ctx)
            elif (args == 'skip'):
                service.skip()
            elif (args == 'stop'):
                service.stop()
            elif (args != None):
                await service.search(args, ctx)
            elif (args == None):
                await service.enqueue(None, ctx)

        elif (cmd == 'skip' and service.is_radio):
            service.skip()

        elif (cmd == 'stop' and service.is_radio):
            service.stop()

    def list_commands(self, ctx: ExecutionContext):
        return ['gachi', 'skip', 'stop']

    async def initialize(self, bot):
        pass