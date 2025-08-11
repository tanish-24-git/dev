from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Settings:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.grok_api_key = os.getenv("GROK_API_KEY")
        self.spline_api_key = os.getenv("SPLINE_API_KEY")
        self.telnyx_api_key = os.getenv("TELNYX_API_KEY")
        self.astica_api_key = os.getenv("ASTICA_API_KEY")
        if not self.openai_api_key and not self.gemini_api_key:
            logger.warning("No API keys found in .env")

settings = Settings()