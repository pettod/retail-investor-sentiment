import os
from googleapiclient.discovery import build
from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv


# Data structure
class KeyInsights(BaseModel):
    market_sentiment: str
    top_picks: str
    reasoning: str

class Stock(BaseModel):
    company_name: str
    ticker_symbol: str

class StocksRecommendation(BaseModel):
    buy_stocks: list[Stock]
    sell_stocks: list[Stock]
    hold_stocks: list[Stock]
    key_insights: KeyInsights

class YouTubeVideo(BaseModel):
    id: str
    url: str
    title: str
    date: str
    duration: int = 0
    recommendation: StocksRecommendation | None = None


# Configuration
load_dotenv()
DB_FILE = "videos.db"
YOUTUBE_API = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))
GEMINI_API = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-2.5-flash"
CHANNEL_IDS = [
    "@jeremylefebvre-clips",
    "@EverythingMoney",
]
