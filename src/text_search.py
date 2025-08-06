import logging
from googlesearch import search
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import pdfplumber
import io

logger = logging.getLogger(__name__)

class TextSearch:
    def __init__(self):
        """Initialize text search module."""
        pass

    def search(self, command: str, context: dict):
        """Perform web and local context search."""
        try:
            query = command.lower().replace("search for", "").strip()
            results = []

            # Web search using googlesearch
            logger.info(f"Performing web search for: {query}")
            web_results = list(search(query, num_results=3))
            results.append(f"Web results for '{query}': {', '.join(web_results)}")

            # Local context search (screen content)
            screen_content = context.get("screen_content", "")
            if query in screen_content.lower():
                results.append(f"Found '{query}' in screen content: {screen_content[:100]}...")

            return "\n".join(results) if results else "No results found"
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return f"Search error: {str(e)}"

    def fetch_web_content(self, url: str):
        """Fetch and extract text content from a web page."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            text = ' '.join(p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3']))
            return text.strip()[:5000] or "No content extracted"
        except Exception as e:
            logger.error(f"Error fetching web content: {e}")
            return None

    def get_youtube_transcript(self, screen_content: str):
        """Fetch YouTube video transcript."""
        try:
            # Extract video ID from URL
            video_id = None
            for url in screen_content.split():
                if "youtube.com/watch?v=" in url:
                    video_id = url.split("v=")[1].split("&")[0]
                    break
            if video_id:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                return " ".join([entry["text"] for entry in transcript])
            return None
        except Exception as e:
            logger.error(f"Error fetching YouTube transcript: {e}")
            return None

    def extract_pdf_text(self, screen_content: str):
        """Extract text from a PDF URL."""
        try:
            # Find PDF URL in screen content
            pdf_url = None
            for url in screen_content.split():
                if url.endswith(".pdf"):
                    pdf_url = url
                    break
            if pdf_url:
                response = requests.get(pdf_url, timeout=10)
                response.raise_for_status()
                with pdfplumber.open(io.BytesIO(response.content)) as pdf:
                    text = "".join(page.extract_text() or "" for page in pdf.pages)
                return text.strip()[:5000] or "No text extracted"
            return None
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return None