from google import genai
from src.config import GEMINI_API, GEMINI_MODEL, StocksRecommendation


def get_stocks_recommendation(video_url: str) -> StocksRecommendation:
    response = GEMINI_API.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            genai.types.Part.from_uri(file_uri=video_url, mime_type="video/mp4"),
            "Give me a review of which stocks the financial influencer in this video is likely to buy, sell, or hold. A stock can only be in one category.",
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": StocksRecommendation,
        },
    )

    review: StocksRecommendation = response.parsed
    return review
