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
        return ctx.cmd in ['alias']

    async def execute(self, ctx: ExecutionContext):
        args = ctx.args

        separator = args.find(' ')
        if (separator == -1):
            await ctx.msg_callback('Wrong alias syntax. Use "alias <alias> <replacer>"')
            return
        alias = args[:separator]
        replacer = args[separator + 1:]
        self.add_alias(alias, replacer, ctx)
        await ctx.msg_callback(f'Alias "{alias}" has been successfully added')

    def list_commands(self, ctx: ExecutionContext):
        array = ['alias <alias> <replacer>']
        aliases = 'list: '
        for alias in self.configRepo.config['aliases']:
            aliases += f' {alias[0]}'
        array.append(aliases)
        return array

    async def initialize(self, bot):
        pass

    def add_alias(self, cmd: str, replacer: str, ctx: ExecutionContext):
        cfg = self.configRepo.config
        current_aliases = list(map(lambda a: a[0], cfg['aliases']))

        index = -1
        if (cmd in current_aliases):
            index = current_aliases.index(cmd)

        alias = [cmd, replacer]
        if (index == -1):

            cfg['aliases'].append(alias)
        else:
            cfg['aliases'][index] = alias

        self.configRepo.update_config(cfg)