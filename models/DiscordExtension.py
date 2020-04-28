import abc
from models.ExecutionContext import ExecutionContext

class DiscordExtension(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self):
        pass

    @abc.abstractmethod
    def isserving(self, ctx: ExecutionContext):
        pass

    @abc.abstractmethod
    async def execute(self, ctx: ExecutionContext):
        pass

    @abc.abstractmethod
    def list_commands(self, ctx: ExecutionContext):
        pass

    async def initialize(self, bot):
        pass