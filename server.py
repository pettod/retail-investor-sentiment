import json
import sqlite3
from collections import Counter
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
import uvicorn

DB_FILE = "videos_demo.db"

app = FastAPI(title="Retail Investor Sentiment API")


@app.middleware("http")
async def no_cache_api(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store"
    return response


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    if d.get("recommendation"):
        d["recommendation"] = json.loads(d["recommendation"])
    return d


@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


@app.get("/api/channels")
def get_channels():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT channel_id, COUNT(*) as video_count,
                   SUM(CASE WHEN recommendation IS NOT NULL THEN 1 ELSE 0 END) as analyzed_count
            FROM videos GROUP BY channel_id ORDER BY channel_id
        """).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/videos")
def get_videos(
    channel_id: Optional[str] = Query(None),
    analyzed: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    query = "SELECT * FROM videos WHERE 1=1"
    params = []

    if channel_id:
        query += " AND channel_id = ?"
        params.append(channel_id)
    if analyzed is True:
        query += " AND recommendation IS NOT NULL"
    elif analyzed is False:
        query += " AND recommendation IS NULL"

    query += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        total = conn.execute(
            query.replace("SELECT *", "SELECT COUNT(*)").split("ORDER BY")[0],
            params[:-2],
        ).fetchone()[0]

    return {"total": total, "videos": [row_to_dict(r) for r in rows]}


@app.get("/api/videos/{video_id}")
def get_video(video_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Video not found")
    return row_to_dict(row)


@app.get("/api/stats")
def get_stats():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT recommendation FROM videos WHERE recommendation IS NOT NULL"
        ).fetchall()

    buy_counts: Counter = Counter()
    sell_counts: Counter = Counter()
    hold_counts: Counter = Counter()
    sentiments: Counter = Counter()

    for row in rows:
        rec = json.loads(row["recommendation"])
        for stock in rec.get("buy_stocks", []):
            ticker = stock.get("ticker_symbol", stock) if isinstance(stock, dict) else stock
            buy_counts[ticker] += 1
        for stock in rec.get("sell_stocks", []):
            ticker = stock.get("ticker_symbol", stock) if isinstance(stock, dict) else stock
            sell_counts[ticker] += 1
        for stock in rec.get("hold_stocks", []):
            ticker = stock.get("ticker_symbol", stock) if isinstance(stock, dict) else stock
            hold_counts[ticker] += 1
        sentiment = rec.get("key_insights", {}).get("market_sentiment", "unknown")
        sentiments[sentiment] += 1

    return {
        "total_videos": len(rows),
        "top_buys": buy_counts.most_common(20),
        "top_sells": sell_counts.most_common(20),
        "top_holds": hold_counts.most_common(20),
        "sentiment_distribution": dict(sentiments),
    }


@app.get("/api/stock/{ticker}")
def get_stock_mentions(ticker: str):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM videos WHERE recommendation IS NOT NULL ORDER BY date DESC"
        ).fetchall()

    mentions = []
    ticker_upper = ticker.upper()
    for row in rows:
        rec = json.loads(row["recommendation"])
        for category in ["buy_stocks", "sell_stocks", "hold_stocks"]:
            for stock in rec.get(category, []):
                t = stock.get("ticker_symbol", stock) if isinstance(stock, dict) else stock
                if t.upper() == ticker_upper:
                    action = category.replace("_stocks", "")
                    mentions.append({
                        "video_id": row["id"],
                        "title": row["title"],
                        "date": row["date"],
                        "channel_id": row["channel_id"],
                        "action": action,
                        "company_name": stock.get("company_name", "") if isinstance(stock, dict) else "",
                    })
    return {"ticker": ticker_upper, "total_mentions": len(mentions), "mentions": mentions}


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
