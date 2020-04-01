from bot import DiscordExtension, ExecutionContext
from player import Player
import asyncio
import discord

class PlayerExtension(DiscordExtension):
    def __init__(self, player):
        super().__init__()
        self.player = player

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

        elif (ctx.cmd == 'skip'):
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
                await ctx.msg_callback(f'Skipped to item #{final_index + 1}')

        elif (ctx.cmd == 'stop'):
            player.stop()

        elif (ctx.cmd == 'repeat'):
            is_repeat = not player.is_repeat_mode
            await ctx.msg_callback(f'Repeat: {"On" if is_repeat else "Off"}')
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

            embed = discord.Embed()
            embed.description = queue
            await ctx.msg_callback(queue, embed=embed)

    def list_commands(self):
        return ['join', 'disc', 'skip', 'stop', 'repeat', 'queue']

    async def initialize(self, bot):
        player = self.player
        player.initialize(bot)

        prev_voice = bot.guilds[0].get_member(bot.user.id).voice
        if (prev_voice != None):
            await player.join_channel(prev_voice.channel)

        asyncio.create_task(player.loop())