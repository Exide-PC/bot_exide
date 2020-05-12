from models.DiscordExtension import DiscordExtension
from models.ExecutionContext import ExecutionContext
from player import Player
import asyncio
import discord
import logging

class AliasExtension(DiscordExtension):
    def __init__(self, configRepo):
        self.configRepo = configRepo
        super().__init__()

    @property
    def name(self):
        return 'Aliases'

    def isserving(self, ctx: ExecutionContext):
        return ctx.cmd in ['alias', 'alias-remove']

    async def execute(self, ctx: ExecutionContext):
        cmd = ctx.cmd
        args = ctx.args

        if (cmd == 'alias'):
            separator = args.find(' ')
            if (separator == -1):
                await ctx.send_message('Wrong alias syntax. Use "alias <alias> <replacer>"')
                return
            alias = args[:separator]
            replacer = args[separator + 1:]
            self.configRepo.add_alias(alias, replacer)
            await ctx.send_message(f'Alias "{alias}" has been successfully added')
        else:
            if (ctx.isadmin):
                self.configRepo.remove_alias(args)
                await ctx.send_message(f'Alias "{ctx.args}" was successfully removed')
            else:
                await ctx.send_message('Only admin users can remove aliases')

    def list_commands(self, ctx: ExecutionContext):
        array = ['alias <alias> <replacer>']
        aliases = 'list: '
        for alias in self.configRepo.get_aliases():
            aliases += f' {alias[0]}'
        array.append(aliases)
        array.append('alias-remove <alias>')
        return array

    async def initialize(self, bot):
        pass