import os
from googleapiclient.discovery import build
from google import genai
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))
GEMINI_API = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GEMINI_MODEL = "gemini-2.5-flash"
CHANNEL_IDS = [
    "@jeremylefebvre-clips",
    "@EverythingMoney",
]
