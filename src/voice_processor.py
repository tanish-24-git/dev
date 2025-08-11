import logging
import speech_recognition as sr
import io
from scipy.io import wavfile
import threading
import queue
import os
import requests
from src.settings import settings

logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self):
        """Initialize voice processor with speech recognizer."""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.command_queue = queue.Queue()
        self.running = True
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        self.thread = threading.Thread(target=self._continuous_listen, daemon=True)
        self.thread.start()

    def _continuous_listen(self):
        """Continuously listen for voice commands with hotword detection."""
        while self.running:
            try:
                with self.microphone as source:
                    logger.info("Listening for voice input...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                text = self.use_voice_api(audio)
                if text and "hey assistant" in text.lower():
                    command = text.lower().replace("hey assistant", "").strip()
                    self.command_queue.put(command)
                    logger.info(f"Queued command: {command}")
            except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError):
                continue
            except Exception as e:
                logger.error(f"Error in continuous listening: {e}")

    def use_voice_api(self, audio):
        """Use Spline, Telnyx, Astica for voice transcription."""
        try:
            # Spline API (placeholder)
            response = requests.post(
                "https://api.spline.design/v1/voice",  # Replace with actual Spline endpoint
                data=audio.get_wav_data(),
                headers={"Authorization": f"Bearer {settings.spline_api_key}"}
            )
            text = response.json().get("text")
            if text:
                return text

            # Telnyx API (placeholder)
            response = requests.post(
                "https://api.telnyx.com/v2/voice",  # Replace with actual Telnyx endpoint
                data=audio.get_wav_data(),
                headers={"Authorization": f"Bearer {settings.telnyx_api_key}"}
            )
            text = response.json().get("text")
            if text:
                return text

            # Astica API (placeholder)
            response = requests.post(
                "https://api.astica.ai/v1/voice",  # Replace with actual Astica endpoint
                data=audio.get_wav_data(),
                headers={"Authorization": f"Bearer {settings.astica_api_key}"}
            )
            text = response.json().get("text")
            if text:
                return text
            return self.recognizer.recognize_google(audio)  # Fallback
        except Exception as e:
            logger.error(f"Error using voice API: {e}")
            return None

    def capture_voice(self, timeout=5, phrase_time_limit=5):
        """Capture single voice input for testing."""
        try:
            with self.microphone as source:
                logger.info("Listening for voice input...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = self.use_voice_api(audio)
            logger.info(f"Transcribed voice input: {text}")
            return text
        except sr.WaitTimeoutError:
            logger.warning("No voice input detected within timeout")
            return None
        except sr.UnknownValueError:
            logger.error("Could not understand voice input")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during voice capture: {e}")
            return None

    def process_audio(self, audio_data: bytes):
        """Process audio data from file and convert to text."""
        try:
            temp_file = "temp_audio.wav"
            with open(temp_file, "wb") as f:
                f.write(audio_data)
            try:
                sample_rate, data = wavfile.read(temp_file)
                if len(data.shape) > 1:
                    data = data[:, 0]
            except Exception as e:
                logger.error(f"Invalid WAV file: {e}")
                return None
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            audio = sr.AudioData(data.tobytes(), sample_rate, sample_width=2)
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Transcribed audio file: {text}")
            return text
        except sr.UnknownValueError:
            logger.error("Could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during audio processing: {e}")
            return None

    def classify_command(self, command):
        """Classify command type for routing."""
        if not command:
            return "unknown"
        command_lower = command.lower()
        if any(keyword in command_lower for keyword in ["open", "change", "reject", "order", "shut down"]):
            if "summarize" in command_lower and "http" in command_lower:
                return "web_summary"
            return "automation"
        elif any(keyword in command_lower for keyword in ["read", "summarize", "what"]):
            return "query"
        elif "search for" in command_lower:
            return "search"
        elif "reply to this" in command_lower:
            return "email_reply"
        logger.warning(f"Unrecognized command: {command}")
        return "unknown"

    def get_command(self):
        """Retrieve a command from the queue."""
        try:
            return self.command_queue.get_nowait()
        except queue.Empty:
            return None

    def stop(self):
        """Stop continuous listening."""
        self.running = False