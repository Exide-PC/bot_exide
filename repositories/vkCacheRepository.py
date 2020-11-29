from os import path
from utils.replaceForbidden import replace_forbidden
from models.MusicEntry import MusicEntry
import os
import shutil

class VkCacheRepository:

    __cache_path = 'cache/vk'

    def __init__(self):
        if (not path.exists(self.__cache_path)):
            os.makedirs(self.__cache_path, exist_ok=True)

    def cache(self, source_path, music: MusicEntry):
        newPath = self.__get_path(music)
        shutil.move(source_path, newPath)
        return newPath

    def try_get(self, music: MusicEntry):
        return None
        # Not using for now due to id collision issue from vk side
        # newPath = self.__get_path(music)
        # return newPath if path.exists(newPath) else None

    def __get_path(self, music: MusicEntry):
        name = replace_forbidden(f'{music.author} - {music.title} - {music.duration}.mp3')
        return os.path.join(os.getcwd(), self.__cache_path, name)

    def cache_v2(self, id, content):
        cached_path = self.__get_path_v2(id)
        with open(cached_path, 'wb') as f:
            f.write(content)
        return cached_path

    def try_get_v2(self, id):
        cached_path = self.__get_path_v2(id)
        return cached_path if path.exists(cached_path) else None

    def __get_path_v2(self, id):
        return os.path.join(os.getcwd(), self.__cache_path, f'{id}.mp3')