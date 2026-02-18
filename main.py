from youtube import get_all_video_urls, filter_out_shorts
from config import CHANNEL_IDS
from analyse_videos import get_stocks_recommendation


def main():
    for channel_id in CHANNEL_IDS:
        all_videos = get_all_video_urls(channel_id)[:10]
        all_videos = filter_out_shorts(all_videos)
        print(f"Found {len(all_videos)} videos for {channel_id}")
        for v in all_videos:
            print(f"{v.date} - {v.title}: {v.url}")
            review = get_stocks_recommendation(v.url)
            print(f"Review: {review}")

if __name__ == "__main__":
    main()