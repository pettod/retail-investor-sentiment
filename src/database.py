import json
import sqlite3
from typing import List
from src.config import YouTubeVideo, StocksRecommendation, DB_FILE


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                duration INTEGER DEFAULT 0,
                recommendation TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel_id)")


init_db()


def save_video(video: YouTubeVideo, channel_id: str):
    rec_json = json.dumps(video.recommendation.model_dump()) if video.recommendation else None
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO videos (id, channel_id, url, title, date, duration, recommendation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                url=excluded.url,
                title=excluded.title,
                date=excluded.date,
                duration=excluded.duration,
                recommendation=COALESCE(excluded.recommendation, videos.recommendation)
        """, (video.id, channel_id, video.url, video.title, video.date, video.duration, rec_json))


def save_videos(channel_id: str, videos: List[YouTubeVideo]):
    with get_connection() as conn:
        for video in videos:
            rec_json = json.dumps(video.recommendation.model_dump()) if video.recommendation else None
            conn.execute("""
                INSERT INTO videos (id, channel_id, url, title, date, duration, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    url=excluded.url,
                    title=excluded.title,
                    date=excluded.date,
                    duration=excluded.duration,
                    recommendation=COALESCE(excluded.recommendation, videos.recommendation)
            """, (video.id, channel_id, video.url, video.title, video.date, video.duration, rec_json))


def _row_to_video(row: sqlite3.Row) -> YouTubeVideo:
    rec = json.loads(row["recommendation"]) if row["recommendation"] else None
    return YouTubeVideo(
        id=row["id"],
        url=row["url"],
        title=row["title"],
        date=row["date"],
        duration=row["duration"],
        recommendation=rec,
    )


def load_videos(channel_id: str) -> List[YouTubeVideo] | None:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM videos WHERE channel_id = ? ORDER BY date DESC", (channel_id,)
        ).fetchall()
    if not rows:
        return None
    return [_row_to_video(row) for row in rows]


def get_video(video_id: str) -> YouTubeVideo | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if not row:
        return None
    return _row_to_video(row)


def save_recommendation(video_id: str, recommendation: StocksRecommendation):
    rec_json = json.dumps(recommendation.model_dump())
    with get_connection() as conn:
        conn.execute(
            "UPDATE videos SET recommendation = ? WHERE id = ?",
            (rec_json, video_id),
        )


def get_unanalyzed_videos(channel_id: str = None) -> List[YouTubeVideo]:
    with get_connection() as conn:
        if channel_id:
            rows = conn.execute(
                "SELECT * FROM videos WHERE recommendation IS NULL AND channel_id = ? ORDER BY date DESC",
                (channel_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM videos WHERE recommendation IS NULL ORDER BY date DESC"
            ).fetchall()
    return [_row_to_video(row) for row in rows]


def import_from_json(json_path: str):
    with open(json_path) as f:
        data = json.load(f)

    count = 0
    if isinstance(data, dict):
        for channel_id, videos in data.items():
            for v in videos:
                video = YouTubeVideo(**v)
                save_video(video, channel_id)
                count += 1
    elif isinstance(data, list):
        for v in data:
            video = YouTubeVideo(**v)
            save_video(video, "unknown")
            count += 1

    print(f"Imported {count} videos from {json_path}")


def export_to_json(output_path: str = "videos_export.json"):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM videos ORDER BY channel_id, date DESC").fetchall()

    data = {}
    for row in rows:
        channel = row["channel_id"]
        video = _row_to_video(row).model_dump()
        data.setdefault(channel, []).append(video)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)

    total = sum(len(v) for v in data.values())
    print(f"Exported {total} videos across {len(data)} channels to {output_path}")


if __name__ == "__main__":
    export_to_json()
