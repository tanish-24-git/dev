from abc import ABC, abstractmethod
import logging
import httpx
import asyncio
from src.settings import settings

logger = logging.getLogger(__name__)

class LLMClient(ABC):
    @abstractmethod
    async def query(self, messages: list[dict]) -> str:
        pass

class OpenAIClient(LLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def query(self, messages: list[dict]) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "gpt-4",
                    "messages": messages
                }
            )
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} {response.text}")
            try:
                return response.json()["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as e:
                raise Exception(f"Failed to parse OpenAI response: {e}")

class GeminiClient(LLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key

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

class LLMManager:
    def __init__(self):
        self.clients = []
        if settings.openai_api_key:
            self.clients.append(OpenAIClient(settings.openai_api_key))
        if settings.gemini_api_key:
            self.clients.append(GeminiClient(settings.gemini_api_key))

    async def query(self, command: str, context: dict, timeout=10) -> str:
        if not self.clients:
            raise Exception("No LLM clients configured")
        context_str = "\n".join([f"{key}: {value}" for key, value in context.items()])
        messages = [
            {"role": "system", "content": f"Current context:\n{context_str}"},
            {"role": "user", "content": command}
        ]
        for client in self.clients:
            try:
                result = await asyncio.wait_for(client.query(messages), timeout=timeout)
                return result
            except asyncio.TimeoutError:
                logger.error(f"Timeout with {client.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error with {client.__class__.__name__}: {e}")
                continue
        raise Exception("All LLM clients failed")