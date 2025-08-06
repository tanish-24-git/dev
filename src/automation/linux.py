import logging
import subprocess

logger = logging.getLogger(__name__)

class LinuxAutomation:
    def __init__(self):
        """Initialize Linux automation module."""
        self.command_map = {
            "open chrome": "google-chrome",
            "open notepad": "gedit",
            "shut down": "shutdown -h now",
            "order food": "xdg-open https://www.ubereats.com",
            "order clothes": "xdg-open https://www.amazon.com/s?k=clothing",
            "do something on browser": "xdg-open https://www.google.com"
        }

    def execute(self, command: str):
        """Execute a command on Linux."""
        try:
            command_lower = command.lower()
            system_command = self.command_map.get(command_lower)
            if system_command:
                subprocess.run(system_command, shell=True)
                return f"Executed: {command}"
            elif command_lower.startswith("open http"):
                subprocess.run(f"xdg-open {command_lower[5:]}", shell=True)
                return f"Opened: {command_lower[5:]}"
            else:
                logger.warning(f"Unknown command: {command}")
                return f"Command not recognized: {command}"
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return f"Error: {str(e)}"

    def send_email(self, to: str, subject: str, body: str):
        """Send an email (not implemented)."""
        logger.warning("Linux email sending not implemented")
        return "Linux email sending not implemented"