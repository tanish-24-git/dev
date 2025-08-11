import logging
from src.llms.llm_grok import GrokClient
from src.llms.llm_gpt import GPTClient
from src.llms.llm_gemini import GeminiClient
from src.settings import settings

logger = logging.getLogger(__name__)

class LLMManager:
    def __init__(self):
        self.clients = []
        if settings.grok_api_key:
            self.clients.append(GrokClient(settings.grok_api_key))
        if settings.openai_api_key:
            self.clients.append(GPTClient(settings.openai_api_key))
        if settings.gemini_api_key:
            self.clients.append(GeminiClient(settings.gemini_api_key))

    async def query(self, command: str, context: dict) -> str:
        if not self.clients:
            raise Exception("No LLM clients configured")
        context_str = "\n".join([f"{key}: {value}" for key, value in context.items()])
        messages = [
            {"role": "system", "content": f"Current context:\n{context_str}"},
            {"role": "user", "content": command}
        ]
        for client in self.clients:
            try:
                result = await client.query(messages)
                return result
            except Exception as e:
                logger.error(f"Error with {client.__class__.__name__}: {e}")
                continue
        raise Exception("All LLM clients failed")