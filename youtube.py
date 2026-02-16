import os
from googleapiclient.discovery import build
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

# Data schema
class YouTubeVideo(BaseModel):
    id: str
    url: str
    title: str
    date: str

# Setup API
load_dotenv()
YOUTUBE = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))


def get_all_video_urls(channel_id: str) -> List[YouTubeVideo]:
    # A. Get the "Uploads" Playlist ID for the channel
    if channel_id.startswith("@"):
        ch_request = YOUTUBE.channels().list(part="contentDetails", forHandle=channel_id)
    else:
        ch_request = YOUTUBE.channels().list(part="contentDetails", id=channel_id)
    ch_response = ch_request.execute()

    if not ch_response.get('items'):
        raise ValueError(f"No channel found for: {channel_id}")
    
    uploads_playlist_id = ch_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    # B. Fetch videos from that playlist
    videos = []
    next_page_token = None
    
    while True:
        pl_request = YOUTUBE.playlistItems().list(
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
            
    return videos


def main():
    channel_id = "@jeremylefebvre-clips"
    all_videos = get_all_video_urls(channel_id) 
    print(f"Found {len(all_videos)} videos")
    for v in all_videos[:10]:
        print(f"{v.date} - {v.title}: {v.url}")


if __name__ == "__main__":
    main()
