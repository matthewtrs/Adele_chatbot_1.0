import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog
import threading
import os
from google import genai
from gtts import gTTS

class GeminiAIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini AI with Text-to-Speech")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Variables
        self.api_key = "AIzaSyAe6UbUZN1msgYnx7J9BtlrJsW8vWogFoY"  # Default API key
        self.rules_file = "rules.txt"
        self.rules_content = self.access_file(self.rules_file)
        self.client = None
        self.language = tk.StringVar(value="en")
        
        # Initialize status_var before we use it
        self.status_var = tk.StringVar()
        
        # Create GUI components
        self.create_widgets()
        
        # Apply a simple theme
        self.apply_theme()
        
        # Create and initialize the client AFTER creating widgets
        self.initialize_client()
        
    def access_file(self, filename):
        """Reads the content of a file if it exists, otherwise returns an empty string."""
        if os.path.exists(filename):
            with open(filename, "r") as file:
                return file.read()
        return ""  # Return empty string if file doesn't exist
    
    def initialize_client(self):
        """Initialize the Gemini AI client with the API key."""
        try:
            self.client = genai.Client(api_key=self.api_key)
            self.update_status("Client initialized successfully", "green")
        except Exception as e:
            self.update_status(f"Error initializing client: {str(e)}", "red")
    
    def create_widgets(self):
        """Create all GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create top frame for settings
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding=5)
        settings_frame.pack(fill=tk.X, pady=5)
        
        # API Key
        api_frame = ttk.Frame(settings_frame)
        api_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(api_frame, text="API Key:").pack(side=tk.LEFT, padx=5)
        self.api_entry = ttk.Entry(api_frame, width=40, show="*")
        self.api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.api_entry.insert(0, self.api_key)
        
        ttk.Button(api_frame, text="Update", command=self.update_api_key).pack(side=tk.LEFT, padx=5)
        
        # Rules File
        rules_frame = ttk.Frame(settings_frame)
        rules_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(rules_frame, text="Rules File:").pack(side=tk.LEFT, padx=5)
        self.rules_entry = ttk.Entry(rules_frame, width=40)
        self.rules_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.rules_entry.insert(0, self.rules_file)
        
        ttk.Button(rules_frame, text="Browse", command=self.browse_rules_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(rules_frame, text="Load", command=self.load_rules_file).pack(side=tk.LEFT, padx=5)
        
        # Language selection
        lang_frame = ttk.Frame(settings_frame)
        lang_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(lang_frame, text="Language:").pack(side=tk.LEFT, padx=5)
        languages = ["en", "id", "fr", "es", "de", "it", "ja", "ko", "pt", "ru", "zh-CN"]
        lang_dropdown = ttk.Combobox(lang_frame, textvariable=self.language, values=languages, width=5)
        lang_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Create middle frame for input
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding=5)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=5)
        self.input_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create bottom frame for output
        output_frame = ttk.LabelFrame(main_frame, text="Response", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=10, state="disabled")
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.submit_button = ttk.Button(button_frame, text="Submit", command=self.process_input)
        self.submit_button.pack(side=tk.LEFT, padx=5)
        
        self.speak_button = ttk.Button(button_frame, text="Speak Response", command=self.speak_response)
        self.speak_button.pack(side=tk.LEFT, padx=5)
        self.speak_button.config(state="disabled")
        
        ttk.Button(button_frame, text="Clear Input", command=self.clear_input).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        self.status_bar.config(background="lightgrey")
        
        # Bind Enter key to submit
        self.root.bind('<Return>', lambda event: self.process_input())
        
        # Initial status message
        self.update_status(f"Rules loaded: {len(self.rules_content)} characters", "blue")
    
    def apply_theme(self):
        """Apply a simple theme to the GUI."""
        self.root.configure(bg="#f5f5f5")
        style = ttk.Style()
        style.configure("TFrame", background="#000000")
        style.configure("TLabelframe", background="#3f3f3f")
        style.configure("TLabelframe.Label", background="#3f3f3f")
        style.configure("TButton", background="#595959", foreground="black", padding=5)
    
    def update_status(self, message, color="black"):
        """Update the status bar with a message and color."""
        self.status_var.set(message)
        self.status_bar.config(foreground=color)
    
    def update_api_key(self):
        """Update the API key and reinitialize the client."""
        new_key = self.api_entry.get().strip()
        if new_key:
            self.api_key = new_key
            self.initialize_client()
        else:
            self.update_status("API key cannot be empty", "red")
    
    def browse_rules_file(self):
        """Open a file dialog to select the rules file."""
        filename = filedialog.askopenfilename(
            title="Select Rules File",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filename:
            self.rules_entry.delete(0, tk.END)
            self.rules_entry.insert(0, filename)
    
    def load_rules_file(self):
        """Load the rules from the specified file."""
        filename = self.rules_entry.get().strip()
        self.rules_file = filename
        self.rules_content = self.access_file(filename)
        self.update_status(f"Rules loaded: {len(self.rules_content)} characters", "blue")
    
    def clear_input(self):
        """Clear the input text area."""
        self.input_text.delete("1.0", tk.END)
    
    def clear_output(self):
        """Clear the output text area."""
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state="disabled")
        self.speak_button.config(state="disabled")
    
    def process_input(self):
        """Process the user input and get a response from the Gemini AI."""
        # Get user input
        user_input = self.input_text.get("1.0", tk.END).strip()
        
        if not user_input:
            self.update_status("Please enter some input", "red")
            return
        
        if "stop" in user_input.lower():
            self.update_status("End program command received", "blue")
            self.root.after(1000, self.root.destroy)
            return
        
        # Disable submit button during processing
        self.submit_button.config(state="disabled")
        self.update_status("Processing request...", "blue")
        
        # Start a separate thread to avoid freezing the UI
        threading.Thread(target=self.get_ai_response, args=(user_input,), daemon=True).start()
    
    def get_ai_response(self, user_input):
        """Get response from Gemini AI in a separate thread."""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-lite", contents=self.rules_content + user_input
            )
            
            # Update the output text
            self.root.after(0, self.update_output, response.text)
            
        except Exception as e:
            self.root.after(0, self.update_status, f"Error: {str(e)}", "red")
            self.root.after(0, lambda: self.submit_button.config(state="normal"))
    
    def update_output(self, response_text):
        """Update the output text area with the AI response."""
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, response_text)
        self.output_text.config(state="disabled")
        
        # Enable speak button and submit button
        self.speak_button.config(state="normal")
        self.submit_button.config(state="normal")
        
        self.update_status("Response received", "green")
    
    def speak_response(self):
        """Convert the AI response to speech and play it."""
        response_text = self.output_text.get("1.0", tk.END).strip()
        if not response_text:
            self.update_status("No response to speak", "red")
            return
        
        self.update_status("Converting to speech...", "blue")
        self.speak_button.config(state="disabled")
        
        # Start a separate thread for TTS
        threading.Thread(target=self.text_to_speech, args=(response_text,), daemon=True).start()
    
    def text_to_speech(self, text):
        """Convert text to speech in a separate thread."""
        try:
            language = self.language.get()
            myobj = gTTS(text=text, lang=language, slow=False)
            myobj.save("response.mp3")
            
            # Play the audio
            os.system("start response.mp3")
            
            self.root.after(0, self.update_status, "Speech playing", "green")
            self.root.after(0, lambda: self.speak_button.config(state="normal"))
            
        except Exception as e:
            self.root.after(0, self.update_status, f"Error in text-to-speech: {str(e)}", "red")
            self.root.after(0, lambda: self.speak_button.config(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    app = GeminiAIApp(root)
    root.mainloop()