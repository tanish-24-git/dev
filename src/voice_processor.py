import logging
import speech_recognition as sr
import queue
import threading
import time
import pyaudio
import io
from scipy.io import wavfile

logger = logging.getLogger(__name__)

class VoiceProcessor:
    def __init__(self, enable_continuous_listening=True):
        """Initialize voice processor with speech recognizer."""
        self.recognizer = sr.Recognizer()
        self.command_queue = queue.Queue()
        self.running = True
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024
        self.pyaudio = pyaudio.PyAudio()
        self.lock = threading.Lock()  # Ensure exclusive microphone access
        self.enable_continuous_listening = enable_continuous_listening
        if self.enable_continuous_listening:
            self.thread = threading.Thread(target=self._continuous_listen, daemon=True)
            self.thread.start()

    def _continuous_listen(self):
        """Continuously listen for voice commands with hotword detection."""
        while self.running:
            with self.lock:
                try:
                    stream = self.pyaudio.open(
                        format=self.audio_format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk
                    )
                    logger.info("Listening for voice input...")
                    frames = []
                    silence_count = 0
                    max_silence = 5  # Seconds of silence before stopping
                    while self.running:
                        data = stream.read(self.chunk, exception_on_overflow=False)
                        frames.append(data)
                        audio_data = sr.AudioData(b''.join(frames[-int(self.rate/self.chunk*5):]), self.rate, 2)
                        try:
                            text = self.recognizer.recognize_google(audio_data, show_all=False)
                            if text and "hey assistant" in text.lower():
                                command = text.lower().replace("hey assistant", "").strip()
                                self.command_queue.put(command)
                                logger.info(f"Queued command: {command}")
                                frames = []  # Reset after command
                            silence_count = 0
                        except (sr.UnknownValueError, sr.RequestError):
                            silence_count += self.chunk / self.rate
                            if silence_count > max_silence:
                                break
                        time.sleep(self.chunk / self.rate)
                    stream.stop_stream()
                    stream.close()
                except Exception as e:
                    logger.error(f"Error in continuous listening: {e}")
                    time.sleep(1)

    def capture_voice(self, timeout=5, phrase_time_limit=5):
        """Capture single voice input for testing or GUI."""
        with self.lock:
            try:
                stream = self.pyaudio.open(
                    format=self.audio_format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk
                )
                logger.info("Listening for voice input...")
                frames = []
                start_time = time.time()
                while time.time() - start_time < timeout:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    frames.append(data)
                    if len(frames) * self.chunk / self.rate >= phrase_time_limit:
                        break
                stream.stop_stream()
                stream.close()
                audio_data = sr.AudioData(b''.join(frames), self.rate, 2)
                text = self.recognizer.recognize_google(audio_data)
                logger.info(f"Transcribed voice input: {text}")
                return text
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
            temp_file = io.BytesIO(audio_data)
            temp_file.seek(0)
            sample_rate, data = wavfile.read(temp_file)
            if len(data.shape) > 1:
                data = data[:, 0]
            audio = sr.AudioData(data.tobytes(), sample_rate, 2)
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
        self.pyaudio.terminate()