import requests
from requests.models import PreparedRequest
from browser import Browser, SearchHandle, MusicEntry
from repositories.vkCacheRepository import VkCacheRepository
from player import Player
from utils.env import env
import asyncio
from utils.execute_blocking import execute_blocking
from bot import BotExide
import logging
from models.ExecutionException import ExecutionException

class VkService:

    _bot: BotExide = None
    _browser: Browser = None
    _player: Player = None
    _vkCacheRepository: VkCacheRepository = None

    def __init__(self, bot, browser, player, vkCacheRepository, configRepo):
        self._bot = bot
        self._browser = browser
        self._player = player
        self._vkCacheRepository = vkCacheRepository
        self._configRepo = configRepo

        self.__establish_connection()
        asyncio.create_task(self.__loop())

    async def __enqueue_audio(self, audio, ctx):
        if (ctx.voice_channel() == None):
            return

        async def item_callback():
            id = audio['id']
            cached_path = self._vkCacheRepository.try_get_v2(id)
            if (cached_path):
                return cached_path

            loaded_event = asyncio.Event()
            ctx.loading_callback(loaded_event)
            try:
                doc = await execute_blocking(requests.get, audio['url'])
            finally:
                loaded_event.set()

            return self._vkCacheRepository.cache_v2(id, doc.content)

        author = ctx.author.display_name
        title = f'{audio["artist"]} - {audio["title"]}'

        await ctx.send_message(f'Music "{title}" was added to queue by vk pm from {author}')
        self._player.enqueue(item_callback, title, ctx)

    async def __loop(self):
        while (True):
            try:
                events = await execute_blocking(self.__poll_events)

                for event in events:
                    if (event['type'] != 'message_new'):
                        continue
                    if (not event['object'].get('attachments')):
                        continue
                    message = event['object']['body']
                    audio_attachments = list(filter(lambda a: a['type'] == 'audio', event['object']['attachments']))
                    audio_objects = list(map(lambda a: a['audio'], audio_attachments))

                    vk_user_id = event['object']['user_id']
                    discord_user_id = self._configRepo.get_discord_user_id_bound_to_vk(vk_user_id)
                    if (not discord_user_id):
                        logging.info(f'Vk user id {vk_user_id} has not bound discord profile')
                        continue

                    context = self._bot.create_user_context(discord_user_id)
                    if (context.voice_channel() == None):
                        logging.info(f'Discord user id {discord_user_id} has requested the song via vk pm not being on the server')
                        continue

                    logging.info(f'Discord user id {discord_user_id} has requested the song via vk pm')
                    for audio in audio_objects:
                        await self.__enqueue_audio(audio, context)
            except Exception as e:
                logging.error(f'Error occured during vk events polling')
                logging.error(e)

    def __poll_events(self):
        def poll_impl():
            return requests.get(self._server, params={
                'act': 'a_check',
                'key': self._sessionKey,
                'ts': self._eventId,
                'wait': 25
            }).json()

        json = poll_impl()

        failed_code = json.get('failed')
        if (failed_code):
            logging.info(f'Failed polling attempt encountered. Response: {json}')
            if (failed_code == 1):
                self._eventId = json['ts']
            else:
                self.__establish_connection()
            json = poll_impl()

        self._eventId = json['ts']
        return json['updates']

    def __establish_connection(self):
        json = requests.get('https://api.vk.com/method/groups.getLongPollServer', params={
            'group_id': env.vk_group_id,
            'access_token': env.vk_token,
            'v': '5.103'
        }).json()['response']

        self._server = json['server']
        self._sessionKey = json['key']
        self._eventId = json['ts']

        logging.info(f'Established vk api connection. Response: {json}')

    async def search(self, query, ctx):
        if (self._browser.isbusy):
            await ctx.send_message('Service is currently busy')
            return

        search_finished_event = asyncio.Event()
        ctx.loading_callback(search_finished_event, 'Searching')
        try:
            handle: SearchHandle = await execute_blocking(self._browser.search, ctx.args)
        finally:
            search_finished_event.set()

        with handle:
            options = list(map(lambda r: f"{r.author} - {r.title} [{r.duration}]", handle.results))
            options = options[:15]

            if (len(options) == 0):
                await ctx.send_message('Nothing was found :<')
                return

            index = await ctx.choice_callback(options)
            if (index != None):
                result: MusicEntry = handle.results[index]
                title = f'{result.author} - {result.title}'

                cached_path = self._vkCacheRepository.try_get(result)
                if (not cached_path):
                    logging.info(f'No cache for vm music {title} was not found, downloading...')
                    loaded_event = asyncio.Event()
                    ctx.loading_callback(loaded_event)
                    try:
                        actual_path = await execute_blocking(handle.download, index)
                    finally:
                        loaded_event.set()

                    cached_path = self._vkCacheRepository.cache(actual_path, result)

                if (self._player.is_playing()):
                    await ctx.send_message('Your music was added to queue')

                self._player.enqueue_with_path(cached_path, title, ctx)

    async def bind_user(self, vk_user_id, discord_user_id, ctx):
        self._configRepo.bind_vk_user(vk_user_id, discord_user_id)
        message_id = self._configRepo.get_next_vk_message_id()
        json = requests.get('https://api.vk.com/method/messages.send', params={
            'peer_id': vk_user_id,
            'access_token': env.vk_token,
            'v': '5.103',
            'message': 'Готов включать твой музончик',
            'random_id': message_id
        }).json()

        
        await ctx.send_message("Your VK profile was successfully registered. Now you can send music via pm to https://vk.com/exideprod")