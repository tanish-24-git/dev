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
        self.assertTrue("active_app" in context or not context)  # Empty dict allowed initially
        self.assertTrue("screen_content" in context or not context)

    def test_stop_monitoring(self):
        self.context_manager.stop()
        self.assertFalse(self.context_manager.running)

if __name__ == "__main__":
    unittest.main()