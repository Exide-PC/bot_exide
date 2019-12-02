import os
import io
import bot
import youtube
import json
from dotenv import load_dotenv

load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')

gachi_playlist = 'PL-VMa2rh7q_ZQvmRt0dqidd9GUC-_42pG'
cfg_path = 'bot.cfg'
cfg = None

def update_cfg(cfg: dict):
    with open(cfg_path, 'w') as f:
        json.dump(cfg, f, indent=4)

if (not os.path.exists(cfg_path)):
    with open(cfg_path, 'w') as f:
        """ default cfg """
        cfg = {
            'gachi': youtube.playlist_items(gachi_playlist)
        }
        json.dump(cfg, f, indent=4)
else:
    with open(cfg_path, 'r') as f:
        cfg = json.load(f)

bot.start(discord_token, cfg, update_cfg)