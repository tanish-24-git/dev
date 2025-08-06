import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import platform
import re
from src.config import config
from src.context_manager import ContextManager
from src.llm_manager import LLMManager
from src.voice_processor import VoiceProcessor
from src.text_search import TextSearch
from src.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Assistant Backend")

# Configure CORS
origins = [
    "http://localhost:3000",  # Flutter web dev
    "http://localhost:8080",  # Flutter mobile dev
    "https://your-production-domain.com"  # Production frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components with optional hardware features
context_manager = ContextManager()
llm_manager = LLMManager()
voice_processor = VoiceProcessor(enable_continuous_listening=config.get("ENABLE_CONTINUOUS_LISTENING", False))
text_search = TextSearch()

# Load platform-specific automation
if platform.system() == "Windows":
    from src.automation.windows import WindowsAutomation
    automation = WindowsAutomation()
elif platform.system() == "Darwin":
    from src.automation.macos import MacOSAutomation
    automation = MacOSAutomation()
elif platform.system() == "Linux":
    from src.automation.linux import LinuxAutomation
    automation = LinuxAutomation()
else:
    raise NotImplementedError("Unsupported platform")

# Define request model for text commands
class CommandRequest(BaseModel):
    command: str

# Health check endpoint
@app.get("/ping")
async def ping():
    """Check if the backend is running."""
    logger.info("Ping received")
    return {"message": "pong"}

# Text command processing endpoint
@app.post("/command")
async def process_command(request: CommandRequest):
    """Process text commands and return results."""
    try:
        command = request.command
        logger.info(f"Processing text command: {command}")
        return await process_command_logic(command)
    except Exception as e:
        logger.error(f"Error processing text command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Voice command processing endpoint
@app.post("/voice")
async def process_voice(file: UploadFile = File(...)):
    """Process voice commands from uploaded audio file."""
    try:
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Invalid file type; must be audio")
        audio_data = await file.read()
        command = voice_processor.process_audio(audio_data)
        if not command:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
        logger.info(f"Processing voice command: {command}")
        return await process_command_logic(command)
    except Exception as e:
        logger.error(f"Error processing voice command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for continuous text chatting
@app.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """Handle continuous text-based chatting."""
    await websocket.accept()
    try:
        while True:
            command = await websocket.receive_text()
            result = await process_command_logic(command)
            await websocket.send_json({"result": result})
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

async def process_command_logic(command: str):
    """Common logic for processing text or voice commands."""
    try:
        action_type = voice_processor.classify_command(command)
        context = context_manager.get_context()

        if action_type == "web_summary":
            url_match = re.search(r'(https?://[^\s]+)', command)
            if url_match:
                url = url_match.group(1)
                automation.execute(f"open {url}")
                web_content = text_search.fetch_web_content(url)
                if web_content:
                    context["web_content"] = web_content
                result = await llm_manager.query("Summarize this content", context)
            else:
                result = "No valid URL found in command"
        elif action_type == "search":
            search_results = text_search.search(command, context)
            context["search_results"] = search_results
            result = await llm_manager.query(command, context)
        elif action_type == "automation":
            result = automation.execute(command)
        elif action_type == "query":
            if command.lower() == "summarize this":
                if context.get("is_youtube"):
                    transcript = text_search.get_youtube_transcript(context.get("screen_content", ""))
                    if transcript:
                        context["youtube_transcript"] = transcript
                elif context.get("is_pdf"):
                    pdf_content = text_search.extract_pdf_text(context.get("screen_content", ""))
                    if pdf_content:
                        context["pdf_content"] = pdf_content
                elif context.get("is_email"):
                    email_content = context.get("screen_content", "")  # Fallback to screen content
                    context["email_content"] = email_content
            result = await llm_manager.query(command, context)
        elif action_type == "email_reply":
            email_content = context.get("screen_content", "")
            context["email_content"] = email_content
            reply = await llm_manager.query("Generate a reply to this email", context)
            result = automation.send_email(to="recipient@example.com", subject="Re: Email", body=reply)
        else:
            result = "Command not recognized"

        logger.info(f"Command result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in command processing: {e}")
        return f"Error: {str(e)}"

# Poll voice commands (for continuous listening)
@app.get("/voice_commands")
async def get_voice_commands():
    """Retrieve queued voice commands."""
    command = voice_processor.get_command()
    if command:
        return await process_command_logic(command)
    return {"result": "No voice command available"}

# Cleanup on shutdown
@app.on_event("shutdown")
def shutdown_event():
    """Stop threads and cleanup resources."""
    logger.info("Shutting down resources")
    context_manager.stop()
    voice_processor.stop()

# Run the app locally
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server on localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)