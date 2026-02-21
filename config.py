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

class StocksRecommendation(BaseModel):
    buy_stocks: list[str]
    sell_stocks: list[str]
    hold_stocks: list[str]
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
YOUTUBE_API = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))
GEMINI_API = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-2.5-flash"
CHANNEL_IDS = [
    "@jeremylefebvre-clips",
    "@EverythingMoney",
]
