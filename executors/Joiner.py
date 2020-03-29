from bot import CommandExecutor, ExecutionContext

class Joiner(CommandExecutor):
    @property
    def name(self):
        return 'Voice state control'

    def isserving(self, ctx: ExecutionContext):
        return ctx.cmd in ['join', 'disc']

    async def execute(self, ctx: ExecutionContext):
        if (ctx.cmd == 'join'):
            await ctx.player.join_channel(ctx.author_vc)
        elif (ctx.cmd == 'disc'):
            await ctx.player.disconnect()

    def list_commands(self):
        return ['join', 'disc']