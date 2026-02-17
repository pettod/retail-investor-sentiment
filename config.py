import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))
