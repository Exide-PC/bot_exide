import os, json
import requests
from requests.models import PreparedRequest
from dotenv import load_dotenv
import youtube_dl

load_dotenv()
token = os.getenv('GOOGLE_TOKEN')

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