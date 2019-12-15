import os, json
import requests
from requests.models import PreparedRequest
from dotenv import load_dotenv
import youtube_dl
from player import Player
import re

load_dotenv()
token = os.getenv('GOOGLE_TOKEN')

class YoutubeService:
    _player = None

    def __init__(self, player: Player):
        self._player = player

    async def play(self, source, is_url, title, channel, msg_callback, is_max_volume, time_code=None):
        video_id = source

        if (is_url):
            matches = re.findall(r'v=[\w-]+', source)
            if (len(matches) != 1):
                await msg_callback('Wrong youtube video url')
                return
            video_id = matches[0][2:] # skipping v=

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
            await self._player.play_async(file_path, is_max_volume)

        if (self._player.is_playing()):
            await msg_callback(f'Your video was added to queue')
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