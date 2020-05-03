from models.DiscordExtension import DiscordExtension
from models.ExecutionContext import ExecutionContext
from player import Player
import asyncio
import discord
import logging
from messageFormatter import MessageType

class PlayerExtension(DiscordExtension):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.task = None

    @property
    def name(self):
        return 'Music player commands'

    def isserving(self, ctx: ExecutionContext):
        return ctx.cmd in ['join', 'disc', 'skip', 'stop', 'repeat', 'queue']

    async def execute(self, ctx: ExecutionContext):
        player = self.player

        if (ctx.cmd == 'join'):
            await player.join_channel(ctx.author_vc)

        elif (ctx.cmd == 'disc'):
            await player.disconnect()

        elif (ctx.cmd in ['skip', 'next']):
            if (ctx.msg == 'skip'):
                player.skip()
            else:
                index = ctx.msg[len('skip'):].strip()
                if (len(index) == 0):
                    return
                # we dont remove actually needed item
                final_index = int(index) - 1
                player.queue = player.queue[final_index:]
                player.skip()
                await ctx.send_message(f'Skipped to item #{final_index + 1}')

        elif (ctx.cmd == 'stop'):
            player.stop()

        elif (ctx.cmd == 'repeat'):
            is_repeat = not player.is_repeat_mode
            await ctx.send_message(f'Repeat: {"On" if is_repeat else "Off"}')
            player.is_repeat_mode = is_repeat

        elif (ctx.cmd == 'queue'):
            items = player.queue
            if (player.current_item == None):
                queue = 'Nothing is being played currently\n'
            else:
                queue = f'Currently playing: {player.current_item.title}\n'

            for i in range(len(items)):
                if (len(queue) > 1000):
                    queue += f'\n... {len(items) - i + 1} more'
                    break
                queue += f'\n{i + 1}. {items[i].title}'

            await ctx.send_message(queue, MessageType.Embed)

    def list_commands(self, ctx: ExecutionContext):
        return ['join', 'disc', 'skip / next', 'stop', 'repeat', 'queue']

    async def initialize(self, bot):
        player = self.player
        player.initialize(bot)

        prev_voice = bot.guilds[0].get_member(bot.user.id).voice
        if (prev_voice != None):
            await player.join_channel(prev_voice.channel)

        if (self.task):
            logging.debug('Encountered already running player loop:')
            logging.debug(self.task)
        else:
            self.task = player.loop()
            asyncio.create_task(self.task)