from os import path
from utils.replaceForbidden import replace_forbidden
import os
import shutil

class VkCacheRepository:

    __cache_path = 'cache/vk'

    def __init__(self):
        if (not path.exists(self.__cache_path)):
            os.makedirs(self.__cache_path, exist_ok=True)

    def cache(self, source_path, author, title, duration):
        newPath = self.get_path(author, title, duration)
        shutil.move(source_path, newPath)
        return newPath

    def try_get(self, author, title, duration):
        newPath = self.get_path(author, title, duration)
        return newPath if path.exists(newPath) else None

    def get_path(self, author, title, duration):
        name = replace_forbidden(f'{author} - {title} - {duration}.mp3')
        return os.path.join(os.getcwd(), self.__cache_path, name) 