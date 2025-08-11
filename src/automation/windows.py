import logging
import subprocess
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

class WindowsAutomation:
    def __init__(self):
        """Initialize Windows automation module."""
        self.command_map = {
            "open chrome": "start chrome",
            "open notepad": "notepad",
            "shut down": "shutdown /s /t 0",
            "order food": "start https://www.ubereats.com",
            "order clothes": "start https://www.amazon.com/s?k=clothing",
            "do something on browser": "start https://www.google.com"
        }

    def execute(self, command: str):
        """Execute a command on Windows."""
        try:
            command_lower = command.lower()
            system_command = self.command_map.get(command_lower)
            if system_command:
                subprocess.run(system_command, shell=True)
                return f"Executed: {command}"
            elif command_lower.startswith("open http"):
                subprocess.run(f"start {command_lower[5:]}", shell=True)
                return f"Opened: {command_lower[5:]}"
            else:
                # General app launch
                if command_lower.startswith("open "):
                    app = command_lower[5:]
                    subprocess.run(f"start {app}", shell=True)
                    return f"Opened: {app}"
                logger.warning(f"Unknown command: {command}")
                return f"Command not recognized: {command}"
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return f"Error: {str(e)}"

    def send_email(self, to: str, subject: str, body: str):
        """Send an email using Gmail API."""
        try:
            creds = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", ["https://www.googleapis.com/auth/gmail.send"]
            ).run_local_server(port=0)
            service = build("gmail", "v1", credentials=creds)
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service.users().messages().send(userId="me", body={"raw": raw}).execute()
            return "Email sent successfully"
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return f"Error sending email: {str(e)}"