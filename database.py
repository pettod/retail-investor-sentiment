import os
import json
from typing import List
from config import YouTubeVideo

CACHE_FILE = "videos_cache.json"


def load_videos(channel_id: str) -> List[YouTubeVideo] | None:
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE) as f:
        data = json.load(f)
    if channel_id not in data:
        return None
    return [YouTubeVideo(**v) for v in data[channel_id]]


def save_videos(channel_id: str, videos: List[YouTubeVideo]):
    data = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            data = json.load(f)
    data[channel_id] = [v.model_dump() for v in videos]
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=4)
