import os
from dotenv import load_dotenv

class Environment:
    def __init__(self):
        self.discord_token = os.getenv('DISCORD_TOKEN')
        self.vk_login = os.getenv('VK_LOGIN')
        self.vk_password = os.getenv('VK_PASSWORD')
        self.google_token = os.getenv('GOOGLE_TOKEN')
        self.is_production = bool(os.getenv('PRODUCTION'))

load_dotenv()
env = Environment()