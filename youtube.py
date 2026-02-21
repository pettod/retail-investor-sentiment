import re
from typing import List
from config import YOUTUBE_API, YouTubeVideo
from database import load_videos, save_videos


def get_all_video_urls(channel_id: str, use_cache: bool = False) -> List[YouTubeVideo]:
    if use_cache:
        cached = load_videos(channel_id)
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

    video_map = {v.id: v for v in videos}
    for i in range(0, len(videos), 50):
        batch = videos[i:i+50]
        resp = YOUTUBE_API.videos().list(
            part="contentDetails",
            id=",".join(v.id for v in batch),
        ).execute()
        for item in resp["items"]:
            video_map[item["id"]].duration = parse_duration(item["contentDetails"]["duration"])

    save_videos(channel_id, videos)
    return videos


def parse_duration(duration: str) -> int:
    pattern = re.compile(
        r'PT'
        r'(?:(?P<hours>\d+)H)?'
        r'(?:(?P<minutes>\d+)M)?'
        r'(?:(?P<seconds>\d+)S)?'
    )
    match = pattern.fullmatch(duration)
    if not match:
        return 0
    parts = match.groupdict()
    return int(parts["hours"] or 0) * 3600 + int(parts["minutes"] or 0) * 60 + int(parts["seconds"] or 0)


def filter_out_shorts(videos: List[YouTubeVideo], min_seconds: int = 300) -> List[YouTubeVideo]:
    return [v for v in videos if v.duration >= min_seconds]


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
