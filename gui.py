import tkinter as tk
from tkinter import scrolledtext, filedialog
import requests
from src.voice_processor import VoiceProcessor

class AssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Assistant")

        # Text input for commands
        self.command_entry = tk.Entry(root, width=50)
        self.command_entry.pack(pady=10)

        # Button to submit text command
        self.submit_button = tk.Button(root, text="Submit", command=self.submit_command)
        self.submit_button.pack(pady=5)

        # Button for voice input
        self.voice_button = tk.Button(root, text="Voice Input", command=self.voice_input)
        self.voice_button.pack(pady=5)

        # Button for image upload
        self.image_button = tk.Button(root, text="Upload Image", command=self.upload_image)
        self.image_button.pack(pady=5)

        # Text area for output
        self.output_area = scrolledtext.ScrolledText(root, width=60, height=20)
        self.output_area.pack(pady=10)

        # Initialize VoiceProcessor
        self.voice_processor = VoiceProcessor()

    def submit_command(self):
        """Handle text command submission."""
        command = self.command_entry.get().strip()
        if command:
            self.output_area.insert(tk.END, f"Processing: {command}\n")
            response = self.send_command(command)
            self.display_response(response)
            self.command_entry.delete(0, tk.END)  # Clear input field

    def voice_input(self):
        """Handle voice command input."""
        self.output_area.insert(tk.END, "Listening for voice input...\n")
        command = self.voice_processor.capture_voice()
        if command:
            self.output_area.insert(tk.END, f"Recognized: {command}\n")
            response = self.send_command(command)
            self.display_response(response)

    def upload_image(self):
        """Handle image upload."""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.gif")])
        if file_path:
            self.output_area.insert(tk.END, f"Uploading image: {file_path}\n")
            response = self.send_image(file_path)
            self.display_response(response)

    def send_command(self, command):
        """Send command to FastAPI backend."""
        try:
            response = requests.post(
                "http://localhost:8000/command",
                json={"command": command},
                timeout=5  # Temporary timeout setting
            )
            response.raise_for_status()
            try:
                return response.json()  # Attempt to parse JSON
            except ValueError:
                return response.text  # Fallback to text if not JSON
        except requests.RequestException as e:
            return {"error": f"Backend error: {str(e)}"}

    def send_image(self, file_path):
        """Send image to FastAPI backend."""
        try:
            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(
                    "http://localhost:8000/upload_image",
                    files=files
                )
            response.raise_for_status()
            try:
                return response.json()  # Attempt to parse JSON
            except ValueError:
                return response.text  # Fallback to text if not JSON
        except requests.RequestException as e:
            return {"error": f"Backend error: {str(e)}"}

    def display_response(self, response):
        """Display the backend response in the output area."""
        self.output_area.delete(1.0, tk.END)  # Clear previous content (optional)
        if isinstance(response, str):
            self.output_area.insert(tk.END, f"Response: {response}\n\n")
        elif isinstance(response, dict):
            if "error" in response:
                self.output_area.insert(tk.END, f"Error: {response['error']}\n\n")
            else:
                self.output_area.insert(tk.END, f"Command: {response.get('command', '')}\n")
                self.output_area.insert(tk.END, f"Result: {response.get('result', '')}\n\n")
        else:
            self.output_area.insert(tk.END, f"Unexpected response: {response}\n\n")
        self.output_area.see(tk.END)  # Scroll to the end

if __name__ == "__main__":
    root = tk.Tk()
    app = AssistantGUI(root)
    root.mainloop()