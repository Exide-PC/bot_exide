import os, json
import requests
from requests.models import PreparedRequest
from dotenv import load_dotenv
import youtube_dl
from player import Player
from urllib.parse import urlparse, parse_qs
import re
import html

load_dotenv()
token = os.getenv('GOOGLE_TOKEN')

class YoutubeService:
    _player = None

    def __init__(self, player: Player):
        self._player = player

    async def search(self, query, ctx):
        selected_index = None
        if (' & ' in query):
            offset = query.find(' & ')
            selected_index = int(query[offset + len(' & '):]) - 1
            query = query[:offset]
            
        search_results = _search(query)
        if (len(search_results) == 0):
            await ctx.msg_callback('Nothing was found :c')
            return

        if (selected_index == None): # not specified explicitly
            selected_index = await ctx.choice_callback(list(map(
                lambda item:
                    item['title'] + (f' [playlist]' if item['isPlaylist'] else ''),
                search_results
            )))
            if (selected_index == None):
                return

        selected = search_results[selected_index]
        result_id = selected['id']

        if (selected['isPlaylist']):
            await self.enqueue_playlist(result_id, ctx)
        else:
            await self.enqueue_video(result_id, selected['title'], ctx)

    async def play(self, args, ctx):
        if (args == None or ctx.author_vc == None):
            return

        parts = list(filter(None, args.split(' ')))
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
            await ctx.msg_callback('Wrong url')

        # only video id was found
        if (playlist == None):
            await self.enqueue_video(video_id[0], None, ctx, time_code)
        else:
            index = index and int(index[0])
            await self.enqueue_playlist(playlist[0], ctx, index)

    async def enqueue_video(self, video_id, title, ctx, time_code=None):
        self._enqueue(video_id, title, ctx, time_code)
        if (self._player.is_playing()):
            await ctx.msg_callback(f'Your video was added to queue')

    async def enqueue_playlist(self, playlistId, ctx, index = None):
        index = index - 2 if index != None else 0
        items = playlist_items(playlistId)[index:]

        for i in range(len(items)):
            item = items[i]
            self._enqueue(
                item['videoId'],
                f'{item["title"]} (#{index + i + 1} in playlist)',
                ctx
            )
        await ctx.msg_callback(f'Enqueued {len(items)} playlist items :>')

    def _enqueue(self, video_id, title, ctx, time_code=None):
        if (title == None):
            title = f'#{video_id}'
            
        async def item_callback():
            attempt_counter = 0
            file_path = None

            while (attempt_counter < 3):
                try:
                    if (time_code == None):
                        file_path = await ctx.execute_blocking(download_sound, video_id)
                    else:
                        try:
                            file_path = await ctx.execute_blocking(downlad_and_trunc_sound, video_id, time_code)
                        except ValueError:
                            await ctx.msg_callback('Incorrent timecode input')
                            return
                    break
                except Exception:
                    attempt_counter += 1

            if (file_path == None):
                await ctx.msg_callback(f'Download failed after {attempt_counter} retries :c')
                return
            
            await ctx.msg_callback(f'Now playing: {title}')
            await self._player.join_channel(ctx.author_vc)
            return file_path

        self._player.enqueue(item_callback, title)


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
                'title': html.unescape(item['snippet']['title'])
            })

        if (nextPageToken == None):
            break

    return videos

def _search(query: str):
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
        videoId = item['id'].get('videoId')
        playlistId = item['id'].get('playlistId')
        if (not videoId and not playlistId): continue
        results.append({
            'id': videoId if videoId != None else playlistId,
            'title': html.unescape(item['snippet']['title']),
            'isPlaylist': playlistId != None
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
        ydl.download([video_url])

    return file_name

def downlad_and_trunc_sound(video_id: str, time_code: str) -> str:
    file_path = download_sound(video_id)
    return _trunc(file_path, time_code)

def _trunc(file_path: str, time_code: str) -> str:
    to_specified = '-' in time_code
    if (to_specified):
        left = time_code.split('-')[0]
        right = time_code.split('-')[1]
    else:
        left = time_code

    file_suffix = ''
    args = ''
    
    minute, second, millis = _extract(left)
    file_suffix += f'{minute}-{second}-{millis}'
    args += f'-ss 00:{minute}:{second}.{millis}'

    if (to_specified):
        minute, second, millis = _extract(right)
        file_suffix += f'_{minute}-{second}-{millis}'
        args += f' -to 00:{minute}:{second}.{millis}'

    cut_file = "{0}_{2}.{1}".format(*file_path.rsplit('.', 1) + [file_suffix])

    if (not os.path.exists(cut_file)):
        os.system(f"ffmpeg -i {file_path} {args} {cut_file}")

    return cut_file

def _extract(string: str):
    milliseconds = '0'
    if ('.' in string):
        parts = string.split('.')
        string = parts[0]
        milliseconds = parts[1]

    parts = string.split(':')
    minute, second = f'{int(parts[0]):02}', f'{int(parts[1]):02}'
    
    return minute, second, milliseconds

if (__name__ == '__main__'):
    _trunc('music/7wtfhZwyrcc.webm', '1:01')
    # download_sound('7wtfhZwyrcc&t=60')
    # items = playlist_items('PL-VMa2rh7q_ZQvmRt0dqidd9GUC-_42pG')