from models.DiscordExtension import DiscordExtension
from models.ExecutionContext import ExecutionContext
from player import Player
import asyncio
import discord
import os
import sys
import logging

class BotExideExtension(DiscordExtension):
    def __init__(self, reboot_handler):
        self._reboot_handler = reboot_handler
        super().__init__()

    @property
    def name(self):
        return 'Common bot commands'

    def isserving(self, ctx: ExecutionContext):
        return ctx.cmd in ['strict', 'reboot']

    async def execute(self, ctx: ExecutionContext):
        cmd = ctx.cmd

        if (cmd == 'reboot'):
            if (ctx.isadmin):
                logging.info(f'{ctx.author.display_name} invoked reboot')
                self._reboot_handler()
            else:
                logging.info(f'Unathorized reboot attempt from {ctx.author.display_name}, kicking...')
                await ctx.send_message('Hey buddy, i think you got the wrong door, the leather-club is two blocks down')
                await asyncio.sleep(2)
                await ctx.author.move_to(None)

        elif (cmd == 'strict'):
            if (ctx.isadmin):
                self.bot.strictMode = not self.bot.strictMode
                await ctx.send_message(f'Strict mode: {"On" if self.bot.strictMode else "Off"}')

    def list_commands(self, ctx: ExecutionContext):
        return [
            'reboot',
            'strict'
        ]

    async def initialize(self, bot):
        self.bot = bot