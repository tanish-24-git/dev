import unittest
from src.context_manager import ContextManager
import logging

logger = logging.getLogger(__name__)

class TestContextManager(unittest.TestCase):
    def setUp(self):
        self.context_manager = ContextManager()

    def test_get_context(self):
        context = self.context_manager.get_context()
        self.assertIsInstance(context, dict)
        self.assertIn("active_app", context)
        self.assertIn("screen_content", context)

    def test_stop_monitoring(self):
        self.context_manager.stop()
        self.assertFalse(self.context_manager.running)

if __name__ == "__main__":
    unittest.main()