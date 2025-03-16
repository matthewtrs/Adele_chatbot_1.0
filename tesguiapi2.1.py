import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, Menu
import threading
import os
from google import genai
from gtts import gTTS
import time
from datetime import datetime
from PIL import Image, ImageTk
from flask import Flask, request, jsonify
from flask_sock import Sock
import json
import ctypes as ct


class GeminiChatApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Adele-Bot")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        
        # Variables
        self.api_key = "AIzaSyAe6UbUZN1msgYnx7J9BtlrJsW8vWogFoY"  # Default API key
        self.rules_file = "C:\\Altair\\codes\\python\\tesapi\\rules.txt"
        self.rules_content = self.access_file(self.rules_file)
        self.client = None
        self.language = tk.StringVar(value="en")
        self.status_var = tk.StringVar()
        self.chat_history = []  # To store chat history
        
        self.bot_icon = Image.open("C:\\Altair\\codes\\python\\tesapi\\output-onlinepngtools.png")  # Replace with the path to your PNG file
        self.bot_icon = self.bot_icon.resize((70, 70), Image.ANTIALIAS)  # Resize the image if necessary
        self.bot_icon = ImageTk.PhotoImage(self.bot_icon)
        
        # Create GUI components
        self.create_widgets()
        
        # Apply a simple theme
        self.apply_theme()
        
        # Create and initialize the client
        self.initialize_client()

        self.start_flask_server()
        
        # Welcome message
        self.add_bot_message("Hello! How can I help you today?")



    # ... (keep all previous imports and class definition the same)


    def start_flask_server(self):
        """Start the Flask web server in a separate thread."""
        from flask import Flask, request, jsonify, render_template_string
        self.flask_app = Flask(__name__)
        
        # Add these variables to track responses
        self.latest_web_response = ""
        self.has_new_response = False
        self.waiting_for_response = False
        
        @self.flask_app.route('/')
        def home():
            return render_template_string(r"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Adele-Bot</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: #736488;
                        color: #333;
                        display: flex;
                        flex-direction: column;
                        height: 100vh;
                    }
                    .chat-container {
                        flex: 1;
                        max-width: 800px;
                        width: 100%;
                        margin: 0 auto;
                        padding: 10px;
                        display: flex;
                        flex-direction: column;
                        overflow: hidden;
                        background-color: #736488;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    }
                    .header {
                        text-align: center;
                        padding: 10px;
                        background-color: #736488;
                        color: white;
                        margin-bottom: 10px;
                    }
                    .messages-area {
                        flex: 1;
                        overflow-y: auto;
                        padding: 10px;
                        background-color: #736488;
                        margin-bottom: 10px;
                        display: flex;
                        flex-direction: column;
                        border: 1px solid #5a4e70;
                    }
                    .message {
                        margin-bottom: 10px;
                        max-width: 85%;
                        word-wrap: break-word;
                        position: relative;
                        display: flex;
                    }
                    .message-content {
                        padding: 8px 12px;
                        border-radius: 5px;
                        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
                    }
                    .bot-message {
                        align-self: flex-start;
                        flex-direction: row;
                    }
                    .bot-icon {
                        width: 40px;
                        height: 40px;
                        background-image: url('https://i.imgur.com/7zL5vug.png');
                        background-size: cover;
                        border-radius: 50%;
                        margin-right: 8px;
                        flex-shrink: 0;
                    }
                    .bot-content {
                        background-color: #E29AB2;
                        border: 1px solid black;
                        color: black;
                    }
                    .user-message {
                        align-self: flex-end;
                        flex-direction: row-reverse;
                    }
                    .user-content {
                        background-color: #8bd450;
                        border: 1px solid black;
                        color: black;
                    }
                    .input-area {
                        display: flex;
                        padding: 10px;
                        background: #736488;
                        border-top: 1px solid #5a4e70;
                    }
                    #userInput {
                        flex: 1;
                        border: 1px solid #5a4e70;
                        padding: 8px 12px;
                        border-radius: 3px;
                        margin-right: 10px;
                        font-size: 14px;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: #8bd450;
                        color: black;
                    }
                    #submitBtn {
                        background-color: #E29AB2;
                        color: black;
                        border: 1px solid #5a4e70;
                        padding: 8px 15px;
                        border-radius: 3px;
                        cursor: pointer;
                        font-size: 14px;
                        font-weight: bold;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    }
                    #submitBtn:hover {
                        background-color: #d685a0;
                    }
                    pre {
                        background-color: #f5f5f5;
                        padding: 8px;
                        border-radius: 3px;
                        border: 1px solid #ddd;
                        overflow-x: auto;
                        white-space: pre-wrap;
                        font-family: Consolas, monospace;
                        font-size: 13px;
                    }
                    code {
                        font-family: Consolas, monospace;
                        background-color: #f5f5f5;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-size: 13px;
                    }
                    .loading {
                        display: inline-block;
                        width: 16px;
                        height: 16px;
                        border: 3px solid rgba(255, 255, 255, 0.3);
                        border-radius: 50%;
                        border-top-color: #fff;
                        animation: spin 1s ease-in-out infinite;
                        margin-right: 8px;
                    }
                    @keyframes spin {
                        to { transform: rotate(360deg); }
                    }
                    .timestamp {
                        font-size: 10px;
                        margin-top: 4px;
                        text-align: right;
                        color: #f0f0f0;
                    }
                    .thinking {
                        font-style: italic;
                        color: #ddd;
                    }
                    .status-bar {
                        padding: 5px 10px;
                        background-color: #634d7b;
                        border-top: 1px solid #5a4e70;
                        font-size: 12px;
                        color: white;
                    }
                </style>
            </head>
            <body>
                <div class="chat-container">
                    <div class="header">
                        <h2>Adele-Bot</h2>
                    </div>
                    
                    <div id="messages" class="messages-area">
                        <!-- Messages will be added here -->
                        <div class="message bot-message">
                            <div class="bot-icon"></div>
                            <div class="message-content bot-content">
                                Hello! How can I help you today?
                                <div class="timestamp">Now</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="input-area">
                        <input type="text" id="userInput" placeholder="Type your message here..." autofocus>
                        <button id="submitBtn">Send</button>
                    </div>
                    
                    <div class="status-bar" id="statusBar">Ready</div>
                </div>
                
                <script>
                    document.addEventListener('DOMContentLoaded', function() {
                        const messagesArea = document.getElementById('messages');
                        const userInput = document.getElementById('userInput');
                        const submitBtn = document.getElementById('submitBtn');
                        const statusBar = document.getElementById('statusBar');
                        let waitingForResponse = false;
                        
                        // Function to update status bar
                        function updateStatus(text, color = 'white') {
                            statusBar.textContent = text;
                            statusBar.style.color = color;
                        }
                        
                        // Function to add a message to the chat
                        function addMessage(text, isUser = false, isThinking = false) {
                            const messageDiv = document.createElement('div');
                            messageDiv.className = isUser ? 'message user-message' : 'message bot-message';
                            
                            if (!isUser) {
                                const botIcon = document.createElement('div');
                                botIcon.className = 'bot-icon';
                                messageDiv.appendChild(botIcon);
                            }
                            
                            const contentDiv = document.createElement('div');
                            contentDiv.className = isUser ? 'message-content user-content' : 'message-content bot-content';
                            if (isThinking) {
                                contentDiv.className += ' thinking';
                            }
                            
                            contentDiv.textContent = text;
                            
                            // Add timestamp
                            const timestamp = document.createElement('div');
                            timestamp.className = 'timestamp';
                            timestamp.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                            contentDiv.appendChild(timestamp);
                            
                            messageDiv.appendChild(contentDiv);
                            messagesArea.appendChild(messageDiv);
                            messagesArea.scrollTop = messagesArea.scrollHeight; // Scroll to bottom
                            return contentDiv; // Return the content div for updating later
                        }
                        
                        // Function to format bot responses (handling code blocks)
                        function formatBotResponse(element, text) {
                            // Clear existing content but keep the timestamp
                            const timestamp = element.querySelector('.timestamp');
                            element.innerHTML = '';
                            
                            // If response contains code blocks
                            if (text.includes('```')) {
                                let segments = text.split(/```/g);
                                for (let i = 0; i < segments.length; i++) {
                                    if (i % 2 === 0) { // Text segment
                                        const textNode = document.createTextNode(segments[i]);
                                        element.appendChild(textNode);
                                    } else { // Code segment
                                        const pre = document.createElement('pre');
                                        pre.textContent = segments[i];
                                        element.appendChild(pre);
                                    }
                                }
                            } else {
                                element.textContent = text;
                            }
                            
                            // Re-add the timestamp
                            element.appendChild(timestamp);
                        }
                        
                        // Function to check for response
                        function checkForResponse(thinkingMsg) {
                            fetch('/get_latest_response')
                            .then(response => response.json())
                            .then(data => {
                                if (data.has_new && data.message) {
                                    // Replace the thinking message content with actual response
                                    thinkingMsg.classList.remove('thinking');
                                    formatBotResponse(thinkingMsg, data.message);
                                    waitingForResponse = false;
                                    updateStatus('Response received', '#8bd450');
                                } else {
                                    // Continue polling
                                    setTimeout(() => checkForResponse(thinkingMsg), 1000);
                                }
                            })
                            .catch(error => {
                                console.error('Error checking for messages:', error);
                                // Update thinking message to show error
                                thinkingMsg.textContent = "Sorry, there was an error retrieving the response.";
                                thinkingMsg.classList.remove('thinking');
                                waitingForResponse = false;
                                updateStatus('Error retrieving response', '#ff6b6b');
                            });
                        }
                        
                        // Handle form submission
                        function handleSubmit() {
                            const text = userInput.value.trim();
                            if (!text || waitingForResponse) return;
                            
                            // Add user message to chat
                            addMessage(text, true);
                            
                            // Clear input
                            userInput.value = '';
                            
                            // Show loading state
                            submitBtn.innerHTML = '<span class="loading"></span>';
                            submitBtn.disabled = true;
                            waitingForResponse = true;
                            updateStatus('Processing request...', '#E29AB2');
                            
                            // Add thinking indicator that will be replaced later
                            const thinkingMsg = addMessage("Processing your request...", false, true);
                            
                            // Send to backend
                            fetch('/submit', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({ input: text })
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.status === 'success') {
                                    // Poll for the response
                                    checkForResponse(thinkingMsg);
                                } else {
                                    // Update thinking message to show error
                                    thinkingMsg.textContent = "Sorry, there was an error processing your request.";
                                    thinkingMsg.classList.remove('thinking');
                                    waitingForResponse = false;
                                    updateStatus('Error processing request', '#ff6b6b');
                                }
                            })
                            .catch(error => {
                                // Update thinking message to show error
                                thinkingMsg.textContent = "Sorry, there was an error connecting to the server.";
                                thinkingMsg.classList.remove('thinking');
                                console.error('Error:', error);
                                waitingForResponse = false;
                                updateStatus('Connection error', '#ff6b6b');
                            })
                            .finally(() => {
                                // Reset button state
                                submitBtn.innerHTML = 'Send';
                                submitBtn.disabled = false;
                            });
                        }
                        
                        // Event listeners
                        submitBtn.addEventListener('click', handleSubmit);
                        userInput.addEventListener('keypress', function(e) {
                            if (e.key === 'Enter') {
                                handleSubmit();
                            }
                        });
                        
                        // Focus input on load
                        userInput.focus();
                    });
                </script>
            </body>
            </html>
            """)

        @self.flask_app.route('/submit', methods=['POST'])
        def submit():
            data = request.json if request.is_json else request.form
            user_input = data.get('input', '')
            if user_input:
                # Reset response flags
                self.has_new_response = False
                self.waiting_for_response = True
                # Process the input in the main thread
                self.root.after(0, self.process_web_input, user_input)
                return jsonify({"status": "success", "message": "Input received and processing started"})
            return jsonify({"status": "error", "message": "No input provided"}), 400
            
        @self.flask_app.route('/get_latest_response', methods=['GET'])
        def get_latest_response():
            response = {"has_new": self.has_new_response, "message": self.latest_web_response}
            if self.has_new_response:
                self.has_new_response = False  # Reset flag after sending
            return jsonify(response)

        # Start the Flask server in a separate thread
        self.flask_thread = threading.Thread(
            target=self.flask_app.run,
            kwargs={'host': '0.0.0.0', 'port': 5000, 'debug': False},
            daemon=True
        )
        self.flask_thread.start()
        self.update_status("Flask server started on port 5000", "blue")
    # ... (rest of the code remains the same)

    def update_status(self, message, color="black"):
        """Update the status bar with a message and color."""
        self.status_var.set(message)
        self.status_bar.config(foreground=color)
    
    def process_web_input(self, user_input):
        """Process input received from the web interface."""
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, user_input)
        self.process_input(from_web=True)  
        
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
            self.status_var.set("Client initialized successfully")
        except Exception as e:
            self.status_var.set(f"Error initializing client: {str(e)}")
            self.add_bot_message(f"⚠️ Error: Could not initialize Gemini AI. Please check your API key in settings.")
    
    def create_widgets(self):
        """Create all GUI widgets."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create chat display area (conversation history)
        self.create_chat_display(main_frame)
        
        # Create input area at bottom
        self.create_input_area(main_frame)
        
        # Status bar
        self.status_bar = tk.Label(main_frame, textvariable=self.status_var, relief="flat", anchor=tk.W, font=('Consolas', 9), background= "#8bd450", foreground="black")
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        # Bind Enter key to submit
        self.root.bind('<Return>', lambda event: self.process_input())
    
    def create_menu_bar(self):
        """Create a menu bar with settings options."""
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)
        
        # Settings menu
        settings_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Change API Key", command=self.show_api_dialog)
        settings_menu.add_command(label="Select Rules File", command=self.show_rules_dialog)
        settings_menu.add_command(label="Language Settings", command=self.show_language_dialog)
        
        # Actions menu
        actions_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Actions", menu=actions_menu)
        actions_menu.add_command(label="Clear Chat", command=self.clear_chat)
        actions_menu.add_command(label="Save Chat History", command=self.save_chat_history)
        
        # Help menu
        help_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_chat_display(self, parent):
        """Create the chat display area with a canvas and frame for messages."""
        # Create a frame with chat title
        chat_frame = ttk.LabelFrame(parent, text="Adele", padding=0)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        
        # Create a canvas with scrollbar for the chat history
        self.chat_canvas = tk.Canvas(chat_frame, highlightthickness=0,background="#736488")
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for the canvas
        chat_scrollbar = ttk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.chat_canvas.yview)
        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas.configure(yscrollcommand=chat_scrollbar.set)
        
        # Frame inside canvas to hold messages
        self.messages_frame = ttk.Frame(self.chat_canvas)
        self.messages_frame_id = self.chat_canvas.create_window((0, 0), window=self.messages_frame, anchor=tk.NW, width=self.chat_canvas.winfo_width())
        
        # Configure canvas scrolling
        self.messages_frame.bind("<Configure>", self.on_frame_configure)
        self.chat_canvas.bind("<Configure>", self.on_canvas_configure)
    
    def on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame."""
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        # Auto scroll to bottom
        self.chat_canvas.yview_moveto(1.0)
    
    def on_canvas_configure(self, event):
        """Update the width of the frame inside the canvas when the canvas changes size."""
        self.chat_canvas.itemconfig(self.messages_frame_id, width=event.width)
    
    def create_input_area(self, parent):
        """Create the input area at the bottom of the GUI."""
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        # Text entry with scrollbar
        self.input_text = tk.Text(input_frame, wrap=tk.WORD, height=3,background="#E29AB2",font=("Noto Sans", 15),borderwidth=3, relief="raised")
        self.input_text.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        # Button frame for submit and TTS
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Send button
        self.submit_button = ttk.Button(button_frame, text="⬆", command=self.process_input)
        self.submit_button.pack(fill=tk.X, pady=(0, 5))
        
        # Speak button
        self.speak_button = ttk.Button(button_frame, text="🔊", width=3, command=self.speak_last_response)
        self.speak_button.pack(fill=tk.X)
    
        
    def apply_theme(self):

        """Apply a modern chat-like theme to the GUI."""

        self.root.configure(bg="#000000")
        
        style = ttk.Style()
        style.configure("TFrame", background="#736488")
        style.configure("TLabelframe", background="#736488")
        style.configure("TLabelframe.Label", background="#736488", font=('Arial', 10, 'bold'))
        style.configure("TButton", background="#736488", foreground="black", padding=1)
        
        # User message bubble style
        self.user_bubble_bg = "#DCF8C6"  # Light green like WhatsApp
        self.user_bubble_fg = "#3D0301"
        
        # Bot message bubble style
        self.bot_bubble_bg = "#FFC0CB"  # White background
        self.bot_bubble_fg = "#3D0301"
    
    def show_api_dialog(self):
        """Show a dialog to change the API key."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Change API Key")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Enter your Gemini API Key:").pack(pady=(20, 5))
        
        api_entry = ttk.Entry(dialog, width=50, show="*")
        api_entry.pack(pady=5, padx=20)
        api_entry.insert(0, self.api_key)
        
        def save_api_key():
            new_key = api_entry.get().strip()
            if new_key:
                self.api_key = new_key
                self.initialize_client()
                dialog.destroy()
                self.add_bot_message("API key updated successfully.")
            else:
                tk.messagebox.showerror("Error", "API key cannot be empty")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Save", command=save_api_key).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def show_rules_dialog(self):
        """Show a dialog to select rules file."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Rules File Settings")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Rules File Path:").pack(pady=(20, 5))
        
        file_frame = ttk.Frame(dialog)
        file_frame.pack(fill=tk.X, padx=20, pady=5)
        
        file_entry = ttk.Entry(file_frame, width=40)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        file_entry.insert(0, self.rules_file)
        
        def browse_file():
            filename = filedialog.askopenfilename(
                title="Select Rules File",
                filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
            )
            if filename:
                file_entry.delete(0, tk.END)
                file_entry.insert(0, filename)
        
        ttk.Button(file_frame, text="Browse", command=browse_file).pack(side=tk.RIGHT, padx=(5, 0))
        
        def save_rules():
            filename = file_entry.get().strip()
            if filename:
                self.rules_file = filename
                self.rules_content = self.access_file(filename)
                dialog.destroy()
                self.add_bot_message(f"Rules file updated. {len(self.rules_content)} characters loaded.")
            else:
                tk.messagebox.showerror("Error", "File path cannot be empty")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Save", command=save_rules).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def show_language_dialog(self):
        """Show a dialog to select TTS language."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Language Settings")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select Text-to-Speech Language:").pack(pady=(20, 10))
        
        languages = ["en", "id", "fr", "es", "de", "it", "ja", "ko", "pt", "ru", "zh-CN"]
        lang_dropdown = ttk.Combobox(dialog, textvariable=self.language, values=languages, width=5)
        lang_dropdown.pack(pady=5)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Save", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def show_about(self):
        """Show about dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title("About")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Gemini AI Chat", font=('Arial', 14, 'bold')).pack(pady=(20, 5))
        ttk.Label(dialog, text="A simple chat interface for Google's Gemini AI").pack()
        ttk.Label(dialog, text="Version 1.0").pack(pady=(10, 20))
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack()
    
    def add_user_message(self, message):
        """Add a user message bubble to the chat display."""
        message_frame = ttk.Frame(self.messages_frame)
        message_frame.pack(fill=tk.X, pady=5)

        # Timestamp label
        timestamp = datetime.now().strftime("%H:%M")
        ttk.Label(message_frame, text=timestamp, font=('Arial', 7), 
                foreground='black', background="#736488").pack(side=tk.RIGHT, padx=(0, 5))

        # Message bubble frame
        bubble_frame = tk.Frame(message_frame, bg="#8bd450", padx=10, pady=5, 
                                highlightbackground="black", highlightthickness=1, bd=0, relief="solid")
        bubble_frame.pack(side=tk.RIGHT, padx=(50, 10))

        # Auto-width calculation
        max_width = 1000
        estimated_width = min(max_width, len(message) * 7)  

        # Use tk.Text for selectable text (but styled like Label)
        msg_text = tk.Text(bubble_frame, font=("Noto Sans", 15), wrap="word", 
                        bg="#8bd450", height=1, width=int(estimated_width / 7),
                        borderwidth=0, highlightthickness=0, relief="flat")
        msg_text.insert("1.0", message)
        msg_text.config(state="disabled")  # Make it read-only

        # Auto-adjust height
        msg_text.update_idletasks()
        num_lines = int(msg_text.index("end-1c").split(".")[0])
        msg_text.config(height=num_lines)

        msg_text.pack()

        # Update chat history
        self.chat_history.append({"role": "user", "content": message, "timestamp": timestamp})

        # Auto scroll to bottom
        self.messages_frame.update_idletasks()
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)


    
    def add_bot_message(self, message):
        message_frame = ttk.Frame(self.messages_frame)
        message_frame.pack(fill=tk.X, pady=5, padx=10, anchor='w')

        # Timestamp and bot icon
        timestamp = datetime.now().strftime("%H:%M")
        timestamp_frame = ttk.Frame(message_frame)
        timestamp_frame.pack(side=tk.LEFT, anchor="n")

        ttk.Label(timestamp_frame, image=self.bot_icon, background="#736488").pack(side=tk.TOP, padx=5)
        ttk.Label(timestamp_frame, text=timestamp, font=('Arial', 7), foreground='black', background="#736488").pack(side=tk.BOTTOM)

        # Message bubble frame
        bubble_frame = tk.Frame(message_frame, bg="#FFCCCC", padx=10, pady=5, 
                                highlightbackground="black", highlightthickness=1, bd=0, relief="solid")
        bubble_frame.pack(side=tk.LEFT, padx=(5, 5), pady=0, anchor='w')

        # Auto-width calculation
        max_width = 500
        estimated_width = min(max_width, len(message) * 7)  

        # Use tk.Text for selectable text (but styled like Label)
        msg_text = tk.Text(bubble_frame, font=("Noto Sans", 15), wrap="word", 
                        bg="#FFCCCC", height=1, width=int(estimated_width / 7),
                        borderwidth=0, highlightthickness=0, relief="flat")
        msg_text.insert("1.0", message)
        msg_text.config(state="disabled")  # Make it read-only

        # Auto-adjust height
        msg_text.update_idletasks()
        num_lines = int(msg_text.index("end-1c").split(".")[0])
        msg_text.config(height=num_lines)

        msg_text.pack()

        # Speak button
        action_frame = ttk.Frame(message_frame)
        action_frame.pack(side=tk.RIGHT, anchor="ne")

        speak_btn = tk.Button(action_frame, text="🔊", width=2, 
                            command=lambda m=message: self.speak_message(m))
        speak_btn.pack(side=tk.TOP)

        # Auto scroll to bottom
        self.messages_frame.update_idletasks()
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    

    def add_bot_image(self, image_path):
        """Display an image as a bot response, positioned like add_bot_message()."""
        try:
            # Create message frame (same as text messages)
            message_frame = ttk.Frame(self.messages_frame)
            message_frame.pack(fill=tk.X, pady=5, padx=10, anchor='w')

            # Timestamp and bot icon
            timestamp = datetime.now().strftime("%H:%M")
            timestamp_frame = ttk.Frame(message_frame)
            timestamp_frame.pack(side=tk.LEFT, anchor="n")

            ttk.Label(timestamp_frame, image=self.bot_icon, background="#736488").pack(side=tk.TOP, padx=5)
            ttk.Label(timestamp_frame, text=timestamp, font=('Arial', 7), foreground='black', background="#736488").pack(side=tk.BOTTOM)

            # Image bubble frame (same as text bubble)
            bubble_frame = tk.Frame(message_frame, bg="#FFCCCC", padx=10, pady=5, 
                                    highlightbackground="black", highlightthickness=1, bd=0, relief="solid")
            bubble_frame.pack(side=tk.LEFT, padx=(5, 5), pady=0, anchor='w')

            # Load and resize image
            img = Image.open(image_path)
            img = img.resize((100, 100))  # Adjust size as needed
            img = ImageTk.PhotoImage(img)

            # Create label for image inside bubble frame
            image_label = tk.Label(bubble_frame, image=img, bg="#FFCCCC")
            image_label.image = img  # Prevent garbage collection
            image_label.pack()

            # Auto scroll to bottom
            self.messages_frame.update_idletasks()
            self.chat_canvas.update_idletasks()
            self.chat_canvas.yview_moveto(1.0)

        except Exception as e:
            print(f"Error loading image: {e}")



    
    def process_input(self, from_web=False):
        """Process the user input and get a response from the Gemini AI."""
        # Get user input
        user_input = self.input_text.get("1.0", tk.END).strip()
        
        if not user_input:
            self.status_var.set("Please enter some input")
            return
        
        if "stop" in user_input.lower():
            self.status_var.set("End program command received")
            self.add_bot_message("Shutting down...")
            self.root.after(1000, self.root.destroy)
            return
        
        if "bing chilling" in user_input.lower():
            self.add_user_message(user_input)

            # Add bot text message
            message = "Zǎoshang hǎo zhōngguó xiànzài wǒ yǒu BING CHILLING 🥶🍦 \n" \
                    "wǒ hěn xǐhuān BING CHILLING 🥶🍦 \n" \
                    "dànshì sùdù yǔ jīqíng 9 bǐ BING CHILLING 🥶🍦 \n" \
                    "sùdù yǔ jīqíng sùdù yǔ jīqíng 9 wǒ zuì xǐhuān"
            
            self.add_bot_message(message)

            # Load image
            image_path = "C:\\Altair\\codes\\python\\tesapi\\artworks-IDl2hpyAbd8R2IVf-vyEd2A-t500x500.jpg"
            self.add_bot_image(image_path)
            
            # If from web, store the response
            if from_web:
                self.latest_web_response = message
                self.has_new_response = True
                self.waiting_for_response = False

            # Clear input
            self.input_text.delete("1.0", tk.END)
            return
        
        # Add user message to chat
        self.add_user_message(user_input)
    
        # Clear input
        self.input_text.delete("1.0", tk.END)
        
        # Disable submit button during processing
        self.submit_button.config(state="disabled")
        self.status_var.set("Processing request...")
        
        # Show a "Bot is typing..." message
        typing_frame = ttk.Frame(self.messages_frame)
        typing_frame.pack(fill=tk.X, pady=5)
        
        timestamp_frame = ttk.Frame(typing_frame)
        timestamp_frame.pack(side=tk.LEFT, padx=(15, 5))
        ttk.Label(timestamp_frame, image=self.bot_icon, background="#736488").pack(side=tk.TOP)

        typing_label = tk.Frame(typing_frame, bg="#FFCCCC", padx=10, pady=5, 
                                highlightbackground="black", highlightthickness=1, bd=0, relief="solid")
        typing_label.pack(side=tk.LEFT, padx=(5, 5), pady=0, anchor='w')
        
        # Update the display
        self.messages_frame.update_idletasks()
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
        
        # Start a separate thread to avoid freezing the UI
        # Pass the from_web parameter to get_ai_response
        threading.Thread(
            target=self.get_ai_response, 
            args=(user_input, typing_frame, from_web),
            daemon=True
        ).start()
    
    def get_ai_response(self, user_input, typing_frame, from_web=False):
        """Get response from Gemini AI in a separate thread."""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-lite", contents=self.rules_content + user_input
            )
            print(user_input)
            
            # Destroy the "typing" indicator
            self.root.after(0, typing_frame.destroy)
            
            # Update the chat with the response
            self.root.after(0, lambda: self.add_bot_message(response.text))
            self.root.after(0, lambda: self.status_var.set("Response received"))
            self.root.after(0, lambda: self.submit_button.config(state="normal"))
            print(response.text)
            
            # If this was called from the web interface, store the response
            if from_web:
                self.latest_web_response = response.text
                self.has_new_response = True
                self.waiting_for_response = False
            
        except Exception as e:
            # Destroy the "typing" indicator
            self.root.after(0, typing_frame.destroy)
            
            # Show error message
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self.root.after(0, lambda: self.add_bot_message(error_msg))
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            self.root.after(0, lambda: self.submit_button.config(state="normal"))
            
            # If this was called from the web interface, store the error
            if from_web:
                self.latest_web_response = error_msg
                self.has_new_response = True
                self.waiting_for_response = False

    def speak_message(self, message):
        """Convert a specific message to speech and play it."""
        self.status_var.set("Converting to speech...")
        
        # Start a separate thread for TTS
        threading.Thread(target=self.text_to_speech, args=(message,), daemon=True).start()
    
    def speak_last_response(self):
        """Speak the last bot message in the chat history."""
        # Find the last bot message
        for message in reversed(self.chat_history):
            if message["role"] == "bot":
                self.speak_message(message["content"])
                return
        
        self.status_var.set("No bot messages to speak")
    
    def text_to_speech(self, text):
        """Convert text to speech in a separate thread."""
        try:
            language = self.language.get()
            myobj = gTTS(text=text, lang=language, slow=False)
            myobj.save("response.mp3")
            
            # Play the audio
            os.system("start response.mp3")
            
            self.root.after(0, lambda: self.status_var.set("Speech playing"))
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error in text-to-speech: {str(e)}"))
    
    def clear_chat(self):
        """Clear the chat history."""
        # Destroy all widgets in the messages frame
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        
        # Clear the chat history list
        self.chat_history = []
        
        # Add welcome message
        self.add_bot_message("Chat history cleared. How can I help you?")
    
    def save_chat_history(self):
        """Save the chat history to a text file."""
        if not self.chat_history:
            self.status_var.set("No chat history to save")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Chat History",
            defaultextension=".txt",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        
        if not filename:
            return
        
        try:
            with open(filename, "w", encoding="utf-8") as file:
                file.write("=== Gemini AI Chat History ===\n\n")
                for message in self.chat_history:
                    role = "You" if message["role"] == "user" else "Gemini AI"
                    file.write(f"[{message['timestamp']}] {role}:\n{message['content']}\n\n")
            
            self.status_var.set(f"Chat history saved to {filename}")
            
        except Exception as e:
            self.status_var.set(f"Error saving chat history: {str(e)}")

def dark_title_bar(window):
        """
        MORE INFO:
        https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute
        """
        window.update()
        set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ct.windll.user32.GetParent
        hwnd = get_parent(window.winfo_id())
        value = 2
        value = ct.c_int(value)
        set_window_attribute(hwnd, 20, ct.byref(value),
                         5)

if __name__ == "__main__":
    
    root = tk.Tk()
    dark_title_bar(root)
    app = GeminiChatApp(root)
    root.mainloop()