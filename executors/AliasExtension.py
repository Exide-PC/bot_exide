from bot import DiscordExtension, ExecutionContext
from player import Player
import asyncio
import discord
import logging

class AliasExtension(DiscordExtension):
    def __init__(self, cfg, update_cfg):
        super().__init__()
        self.cfg = cfg
        self.update_cfg = update_cfg

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
        self.add_alias(alias, replacer)
        await ctx.msg_callback(f'Alias "{alias}" has been successfully added')

    def list_commands(self):
        array = ['alias <alias> <replacer>']
        for alias in self.cfg['aliases']:
            array.append(f'{alias[0]} -> {alias[1]}')
        return array

    async def initialize(self, bot):
        pass

    def add_alias(self, cmd: str, replacer: str):
        current_aliases = list(map(lambda a: a[0], self.cfg['aliases']))

        index = -1
        if (cmd in current_aliases):
            index = current_aliases.index(cmd)

        alias = [cmd, replacer]
        if (index == -1):
            self.cfg['aliases'].append(alias)
        else:
            self.cfg['aliases'][index] = alias
            
        self.update_cfg(self.cfg)