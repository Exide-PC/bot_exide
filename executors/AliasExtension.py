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
            self.add_alias(alias, replacer, ctx)
            await ctx.send_message(f'Alias "{alias}" has been successfully added')
        else:
            if (not ctx.isadmin):
                await ctx.send_message('Only admin users can remove aliases')
                return
            config = self.configRepo.config
            config['aliases'] = list(filter(lambda a: a[0].lower() != args.lower(), config['aliases']))
            self.configRepo.update_config(config)
            await ctx.send_message(f'Alias "{ctx.args}" was successfully removed')

    def list_commands(self, ctx: ExecutionContext):
        array = ['alias <alias> <replacer>']
        aliases = 'list: '
        for alias in self.configRepo.config['aliases']:
            aliases += f' {alias[0]}'
        array.append(aliases)
        array.append('alias-remove <alias>')
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