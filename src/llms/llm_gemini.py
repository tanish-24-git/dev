import logging
import httpx

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-1.5-pro"  # Model name for Gemini LLM

    async def query(self, messages: list[dict]) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                headers={"x-goog-api-key": self.api_key},
                json={"contents": [{"parts": [{"text": messages[-1]["content"]}]}]}
            )
            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.status_code} {response.text}")
            try:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError) as e:
                raise Exception(f"Failed to parse Gemini response: {e}")