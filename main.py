import os
from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv

# 1. Define your data structure
class KeyInsights(BaseModel):
    market_sentiment: str
    top_picks: str
    reasoning: str

class StocksRecommendation(BaseModel):
    buy_stocks: list[str]
    sell_stocks: list[str]
    hold_stocks: list[str]
    key_insights: KeyInsights

# Initialize the Gemini API client
load_dotenv()
CLIENT = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def main():
    video_url = "https://www.youtube.com/watch?v=UL5wRqEFLJ4"

    # Request structured output
    response = CLIENT.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            genai.types.Part.from_uri(file_uri=video_url, mime_type="video/mp4"),
            "Give me a review of which stocks the financial influencer in this video is likely to buy, sell, or hold.",
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": StocksRecommendation,
        },
    )

    # Read the parsed data
    review: StocksRecommendation = response.parsed
    print(f"Buy: {review.buy_stocks}")
    print(f"Sell: {review.sell_stocks}")
    print(f"Hold: {review.hold_stocks}")
    print(f"Market Sentiment: {review.key_insights.market_sentiment}")
    print(f"Top Picks: {review.key_insights.top_picks}")
    print(f"Reasoning: {review.key_insights.reasoning}")


main()
