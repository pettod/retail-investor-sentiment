from youtube import get_all_video_urls, filter_out_shorts, save_videos
from config import CHANNEL_IDS
from analyse_videos import get_stocks_recommendation


def main():
    for channel_id in CHANNEL_IDS:
        all_videos = get_all_video_urls(channel_id)[:10]
        all_videos = filter_out_shorts(all_videos)
        print(f"Found {len(all_videos)} videos for {channel_id}")
        for v in all_videos:
            if v.recommendation is not None:
                print(f"Skipping (already analyzed): {v.title}")
                continue
            print(f"{v.date} - {v.title}: {v.url}")
            review = get_stocks_recommendation(v.url)
            v.recommendation = review
            print(f"Review: {review}")
        save_videos(channel_id, all_videos)


if __name__ == "__main__":
    main()