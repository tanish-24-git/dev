import logging
import os

def setup_logger():
    """Configure logging to output to both console and a file."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear any existing handlers to avoid duplicate logs
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assistant.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger