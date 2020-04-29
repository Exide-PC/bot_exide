from enum import Enum
from discord import Embed

class MessageType(Enum):
    Common = 0,
    Embed = 1

class MessageFormatter:
    def format(self, payload, type: MessageType):
        content = None
        embed = None

        if (type == MessageType.Common):
            content = f'**{payload}**'
        elif (type == MessageType.Embed):
            embed = Embed()
            embed.description = payload

        return (content, embed)