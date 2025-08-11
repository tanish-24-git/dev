import logging
import platform
from mss import mss
import pytesseract
from PIL import Image
import numpy as np
import cv2
import threading
import time
import re
import pywinauto
import psutil
import win32gui
import win32process
from selenium import webdriver

logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self):
        """Initialize context monitoring with platform-specific setup."""
        self.context = {}
        self.last_gray_img = None
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._continuous_monitor, daemon=True)
        self.thread.start()

        self.selenium_driver = None
        if platform.system() == "Windows":
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        elif platform.system() in ("Linux", "Darwin"):
            pass  # Assume tesseract is in PATH
        else:
            logger.warning("Unsupported platform for screen monitoring")

    def capture_screen(self):
        """Capture the current screen as a grayscale NumPy array."""
        try:
            with mss() as sct:
                screenshot = sct.grab(sct.monitors[1])  # Primary monitor
                img = np.array(screenshot)
                # Convert BGRA to grayscale
                b, g, r, a = cv2.split(img)
                gray = 0.114 * b + 0.587 * g + 0.299 * r
                return gray.astype(np.uint8)
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return None

    def preprocess_image(self, gray_img):
        """Preprocess grayscale image for OCR."""
        try:
            # Resize to half size
            scale = 0.5
            resized = cv2.resize(gray_img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(resized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            return thresh
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return gray_img

    def extract_text(self, image):
        """Extract text from an image using OCR."""
        try:
            pil_image = Image.fromarray(image)
            text = pytesseract.image_to_string(pil_image, config='--psm 6')
            return text.strip() if text else "No text detected"
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return "OCR failed"

    def get_active_app(self):
        """Retrieve the currently active application."""
        try:
            # Get the active window from the desktop
            desktop = Desktop(backend="uia")
            active_window = desktop.window(topmost=True, active=True)
            
            # Ensure the window exists and is valid
            if not active_window.exists():
                logger.error("No active window found.")
                return None
            
            # Retrieve the process ID directly (not as a method call)
            pid = active_window.process_id
            logger.debug(f"Active window process ID: {pid}")
            
            # Connect to the application using the process ID
            app = Application(backend="uia").connect(process=pid)
            app_name = app.top_window().window_text() or "Unknown Application"
            logger.info(f"Active application: {app_name}")
            return app_name
            
        except Exception as e:
            logger.error(f"Error getting active app: {str(e)}")
            # Fallback: return a default value or attempt another method
            return "Unknown Application"

    def is_screen_changed(self, new_img, old_img, threshold=100):
        """Check if the screen has changed significantly."""
        if old_img is None:
            return True
        mse = np.mean((new_img.astype(np.int16) - old_img.astype(np.int16)) ** 2)
        return mse > threshold

    def is_youtube_video(self, screen_content, active_app):
        """Detect if a YouTube video is active."""
        return "chrome" in active_app.lower() and "youtube.com/watch" in screen_content.lower()

    def is_pdf_open(self, screen_content, active_app):
        """Detect if a PDF is open."""
        return "adobe acrobat" in active_app.lower() or (".pdf" in screen_content.lower() and "chrome" in active_app.lower())

    def is_email_open(self, screen_content, active_app):
        """Detect if an email client is open."""
        return "gmail" in active_app.lower() or "outlook" in active_app.lower()

    def _continuous_monitor(self):
        """Continuously monitor the screen and update context."""
        while self.running:
            gray_img = self.capture_screen()
            if gray_img is not None:
                with self.lock:
                    if self.is_screen_changed(gray_img, self.last_gray_img):
                        processed_img = self.preprocess_image(gray_img)
                        text = self.extract_text(processed_img)
                        active_app = self.get_active_app()
                        self.context = {
                            "active_app": active_app,
                            "screen_content": text,
                            "is_youtube": self.is_youtube_video(text, active_app),
                            "is_pdf": self.is_pdf_open(text, active_app),
                            "is_email": self.is_email_open(text, active_app)
                        }
                        self.last_gray_img = gray_img.copy()
            time.sleep(5)  # Every 5 seconds

    def get_context(self):
        """Retrieve the latest context."""
        with self.lock:
            return self.context.copy()

    def stop(self):
        """Stop continuous monitoring."""
        self.running = False