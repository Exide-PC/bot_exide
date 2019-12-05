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

if (__name__ == '__main__'):
    # download_sound('y3YHnkCDnKY')
    # items = playlist_items('PL-VMa2rh7q_ZQvmRt0dqidd9GUC-_42pG')
    search('exide')