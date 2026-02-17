import os
import json
import re
from pydantic import BaseModel
from typing import List
from config import YOUTUBE_API

CACHE_FILE = "videos_cache.json"

# Data schema
class YouTubeVideo(BaseModel):
    id: str
    url: str
    title: str
    date: str


def get_all_video_urls(channel_id: str, use_cache: bool = False) -> List[YouTubeVideo]:
    if use_cache:
        cached = load_videos()
        if cached:
            return cached

    # Get the "Uploads" Playlist ID for the channel
    if channel_id.startswith("@"):
        ch_request = YOUTUBE_API.channels().list(part="contentDetails", forHandle=channel_id)
    else:
        ch_request = YOUTUBE_API.channels().list(part="contentDetails", id=channel_id)
    ch_response = ch_request.execute()

    if not ch_response.get('items'):
        raise ValueError(f"No channel found for: {channel_id}")
    
    uploads_playlist_id = ch_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    # Fetch videos from that playlist
    videos = []
    next_page_token = None
    
    while True:
        pl_request = YOUTUBE_API.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        pl_response = pl_request.execute()
        
        for item in pl_response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            video_data = YouTubeVideo(
                id=video_id,
                url=f"https://www.youtube.com/watch?v={video_id}",
                title=item['snippet']['title'],
                date=item['snippet']['publishedAt'],
            )
            videos.append(video_data)
        
        next_page_token = pl_response.get('nextPageToken')
        if not next_page_token:
            break

    save_videos(videos)
    return videos


def filter_out_shorts(videos: List[YouTubeVideo]) -> List[YouTubeVideo]:
    short_ids = set()
    for i in range(0, len(videos), 50):
        resp = YOUTUBE_API.videos().list(part="contentDetails", id=",".join(v.id for v in videos[i:i+50])).execute()

        def parse_duration(duration):
            # Duration comes in as an ISO 8601 string like 'PT33M8S'
            pattern = re.compile(
                r'PT'                                  # starts with 'PT'
                r'(?:(?P<hours>\d+)H)?'                # hours
                r'(?:(?P<minutes>\d+)M)?'              # minutes
                r'(?:(?P<seconds>\d+)S)?'              # seconds
            )
            match = pattern.fullmatch(duration)
            if not match:
                return 0
            parts = match.groupdict()
            hours = int(parts["hours"] or 0)
            minutes = int(parts["minutes"] or 0)
            seconds = int(parts["seconds"] or 0)
            return hours * 3600 + minutes * 60 + seconds

        for item in resp["items"]:
            total_seconds = parse_duration(item["contentDetails"]["duration"])
            if total_seconds < 300: # 5 minutes
                short_ids.add(item["id"])
    videos = [v for v in videos if v.id not in short_ids]
    return videos


def load_videos() -> List[YouTubeVideo] | None:
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE) as f:
        return [YouTubeVideo(**v) for v in json.load(f)]


def save_videos(videos: List[YouTubeVideo]):
    with open(CACHE_FILE, "w") as f:
        json.dump([v.model_dump() for v in videos], f, indent=4)


def main():
    channel_id = "@jeremylefebvre-clips"
    all_videos = get_all_video_urls(channel_id, use_cache=True) 
    print(f"Found {len(all_videos)} videos")
    all_videos = filter_out_shorts(all_videos)
    print(f"Found {len(all_videos)} videos after filtering out shorts")
    for v in all_videos[:10]:
        print(f"{v.date} - {v.title}: {v.url}")


if __name__ == "__main__":
    main()
