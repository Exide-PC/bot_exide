import os, json
import requests
from requests.models import PreparedRequest
from dotenv import load_dotenv
import youtube_dl
from player import Player
from urllib.parse import urlparse, parse_qs
import re

load_dotenv()
token = os.getenv('GOOGLE_TOKEN')

class YoutubeService:
    _player = None

    def __init__(self, player: Player):
        self._player = player

    async def parse_cmd(self, cmd, channel, msg_callback):
        parts = list(filter(None, cmd.split(' ')))
        if (len(parts) == 0):
            return

        video_url = None
        time_code = None

        if (len(parts) == 1):
            video_url = parts[0]
        if (len(parts) == 2):
            time_code = parts[0]
            video_url = parts[1]

        # 00:15 https://www.youtube.com/watch?v=tFwcBdHXNOQ
        # https://www.youtube.com/playlist?list=PL0gU26yd_WJtO4z6KCXxrLlQlYaqnvXZF
        # https://www.youtube.com/watch?v=tFwcBdHXNOQ&list=PL0gU26yd_WJtO4z6KCXxrLlQlYaqnvXZF&index=1

        parsed_url = urlparse(video_url)
        query = parse_qs(parsed_url.query)

        video_id = query.get('v')
        playlist = query.get('list')
        index = query.get('index')

        if (playlist == None and video_id == None):
            await msg_callback('Wrong url')

        # only video id was found
        if (playlist == None):
            self.enqueue(video_id[0], None, channel, msg_callback, time_code)
            if (self._player.is_playing()):
                await msg_callback(f'Your video was added to queue')
            return

        index = int(index[0]) - 2 if index != None else 0
        items = playlist_items(playlist[0])[index:]

        for i in range(len(items)):
            item = items[i]
            self.enqueue(
                item['videoId'],
                f'{item["title"]} (#{index + i + 1} in playlist)',
                channel,
                msg_callback
            )
        await msg_callback(f'Enqueued {len(items)} playlist items :>')

    def enqueue(self, video_id, title, channel, msg_callback, time_code=None):
        async def item_callback():
            attempt_counter = 0
            file_path = None

            while (attempt_counter < 3):
                try:
                    if (time_code == None):
                        file_path = download_sound(video_id)
                    else:
                        try:
                            file_path = downlad_and_trunc_sound(video_id, time_code)
                        except ValueError:
                            await msg_callback('Incorrent timecode input')
                            return
                    break
                except Exception:
                    attempt_counter += 1

            if (file_path == None):
                await msg_callback(f'Download failed after {attempt_counter} retries :c')
                return
                
            if (title != None):
                await msg_callback(f'Now playing: {title}')

            await self._player.join_channel(channel)
            return file_path

        self._player.queue.append(item_callback)


def playlist_items(listId: str) -> []:
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    videos = []
    nextPageToken = None

    while (True):
        params = {
            'key': token,
            'playlistId': listId,
            'part': 'contentDetails,snippet',
            'maxResults': 50,
            'pageToken': nextPageToken
        }
        req = PreparedRequest()
        req.prepare_url(url, params)

        json = requests.get(req.url).json()
        nextPageToken = json.get('nextPageToken')
        
        for item in json['items']:
            videos.append({
                'videoId': item['contentDetails']['videoId'],
                'title': item['snippet']['title']
            })

        if (nextPageToken == None):
            break

    return videos

def search(query: str):
    url = "https://www.googleapis.com/youtube/v3/search"
    results = []

    params = {
        'key': token,
        'part': 'snippet',
        'q': query,
        'maxResults': 15
    }
    req = PreparedRequest()
    req.prepare_url(url, params)

    json = requests.get(req.url).json()

    for item in json['items']:
        if (not item['id'].get('videoId')): continue
        results.append({
            'videoId': item['id']['videoId'],
            'title': item['snippet']['title']
        })

    return results

def download_sound(video_id: str) -> str:
    ext = 'webm'
    file_name: str = f'music/{video_id}.{ext}'

    if (os.path.exists(file_name)):
        return file_name

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': file_name
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        ydl.download([video_url]) # TODO: try ... except

    return file_name

def downlad_and_trunc_sound(video_id: str, start: str) -> str:
    file_path = download_sound(video_id)
    return _trunc(file_path, start)

def _trunc(file_path: str, start: str) -> str:
    parts = start.split(':')
    minute, second = f'{int(parts[0]):02}', f'{int(parts[1]):02}'

    cut_file = "{0}_{2}.{1}".format(*file_path.rsplit('.', 1) + [f'{minute}-{second}'])

    if (not os.path.exists(cut_file)):
        os.system(f"ffmpeg -i {file_path} -ss 00:{minute}:{second} {cut_file}")

    return cut_file

if (__name__ == '__main__'):
    _trunc('music/7wtfhZwyrcc.webm', '1:01')
    # download_sound('7wtfhZwyrcc&t=60')
    # items = playlist_items('PL-VMa2rh7q_ZQvmRt0dqidd9GUC-_42pG')