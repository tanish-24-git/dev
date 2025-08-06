import unittest
from src.voice_processor import VoiceProcessor
import logging

logger = logging.getLogger(__name__)

class TestVoiceProcessor(unittest.TestCase):
    def setUp(self):
        self.voice_processor = VoiceProcessor(enable_continuous_listening=False)

    def test_classify_command(self):
        self.assertEqual(self.voice_processor.classify_command("open chrome"), "automation")
        self.assertEqual(self.voice_processor.classify_command("summarize this"), "query")
        self.assertEqual(self.voice_processor.classify_command("unknown"), "unknown")

    def test_stop(self):
        self.voice_processor.stop()
        self.assertFalse(self.voice_processor.running)

if __name__ == "__main__":
    unittest.main()