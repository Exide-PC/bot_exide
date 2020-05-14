from enum import Enum
from discord import Embed
from math import trunc

class MessageType(Enum):
    Common = 0
    Embed = 1
    Italic = 2
    RichMedia = 3

class MessageFormatter:
    def format(self, payload, type: MessageType):
        content = None
        embed = None

        if (type == MessageType.Common):
            content = f'**{payload}**'
        elif (type == MessageType.Embed):
            embed = Embed()
            embed.description = payload
        elif (type == MessageType.Italic):
            content = f'***{payload}***'
        elif (type == MessageType.RichMedia):
            embed = Embed()
            embed.set_author(name = f'{payload["user"]} added to queue', icon_url=payload['avatar'])
            embed.title = payload['title']
            embed.add_field(name='Channel', value=payload['channel'])
            embed.add_field(name='Duration', value=self.__format_duration(payload['duration']))
            embed.add_field(name='Source', value=payload['source'])

        return (content, embed)

    def __format_duration(self, duration):
        hours = trunc(duration / (60 * 60))
        duration -= hours * 60 * 60
        minutes = trunc(duration / 60)
        seconds = duration - minutes * 60
        formatted = f'{hours:02}:' if hours else ''
        formatted += f'{minutes:02}:'
        formatted += f'{seconds:02}'
        return formatted