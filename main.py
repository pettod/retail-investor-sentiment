from youtube import get_all_video_urls, filter_out_shorts
from database import save_recommendation, get_unanalyzed_videos, save_videos
from config import CHANNEL_IDS
from analyse_videos import get_stocks_recommendation


def main():
    for channel_id in CHANNEL_IDS:
        all_videos = get_all_video_urls(channel_id)
        all_videos = filter_out_shorts(all_videos)
        save_videos(channel_id, all_videos)
        print(f"Found {len(all_videos)} videos for {channel_id}")

        unanalyzed = get_unanalyzed_videos(channel_id)
        print(f"{len(unanalyzed)} videos to analyze")

        for v in unanalyzed:
            print(f"{v.date} - {v.title}: {v.url}")
            review = get_stocks_recommendation(v.url)
            save_recommendation(v.id, review)
            print(f"Review: {review}")
            return # One video for testing


if __name__ == "__main__":
    main()