from utils.linq import first
import json
import os

class ConfigRepository:
    _filename = 'bot.cfg'
    _config = None
    
    def __init__(self, default_config_strategy):
        if (not os.path.exists(self._filename)):
            with open(self._filename, 'w') as f:
                default_config = default_config_strategy()
                json.dump(default_config, f, indent=4)
                self._config = default_config
        else:
            with open(self._filename, 'r') as f:
                self._config = json.load(f)

    def bind_vk_user(self, vk_user_id, discord_user_id):
        self._config['discord_vk_map'] = list(filter(
            lambda b: b[0] != vk_user_id and b[1] != discord_user_id,
            self._config['discord_vk_map']
        ))
        self._config['discord_vk_map'].append([vk_user_id, discord_user_id])
        self.__update_config()

    def get_discord_user_id_bound_to_vk(self, vk_user_id):
        array = self._config['discord_vk_map']
        matching = first(array, lambda b: b[0] == vk_user_id)
        return matching and matching[1]

    def get_next_vk_message_id(self):
        next_id = self._config['vk_last_message_id'] + 1
        self._config['vk_last_message_id'] = next_id
        self.__update_config()
        return next_id

    def get_admin_users(self):
        return self._config['admins']

    def get_youtube_title_cache(self, videoId):
        cached_titles = self._config['video-titles']
        return next((ct[1] for ct in cached_titles if ct[0] == videoId), None)

    def cache_youtube_title(self, videoId, title):
        self._config['video-titles'].append([videoId, title])
        self.__update_config()

    def get_gachi_list(self):
        return self._config['gachi']

    def get_aliases(self):
        return self._config['aliases']

    def add_alias(self, alias, replacer):
        alias = alias.strip()
        replacer = replacer.strip()
        aliases = self._config['aliases']
        aliases = list(filter(lambda a: a[0].lower() != alias, aliases))
        aliases.append([alias, replacer])
        self._config['aliases'] = aliases
        self.__update_config()

    def remove_alias(self, alias):
        alias = alias.lower().strip()
        aliases = self._config['aliases']
        aliases = list(filter(lambda a: a[0].lower() != alias, aliases))
        self._config['aliases'] = aliases
        self.__update_config()

    def __update_config(self):
        with open(self._filename, 'w') as f:
            json.dump(self._config, f, indent=4)