import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, Menu
import threading
import os
from google import genai
from gtts import gTTS
import time
from datetime import datetime
from PIL import Image, ImageTk


class GeminiChatApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Adele-Bot")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        
        # Variables
        self.api_key = "x"  # Default API key
        self.rules_file = "rules.txt"
        self.rules_content = self.access_file(self.rules_file)
        self.client = None
        self.language = tk.StringVar(value="en")
        self.status_var = tk.StringVar()
        self.chat_history = []  # To store chat history
        
        self.bot_icon = Image.open("output-onlinepngtools.png")  # Replace with the path to your PNG file
        self.bot_icon = self.bot_icon.resize((70, 70), Image.ANTIALIAS)  # Resize the image if necessary
        self.bot_icon = ImageTk.PhotoImage(self.bot_icon)
        
        # Create GUI components
        self.create_widgets()
        
        # Apply a simple theme
        self.apply_theme()
        
        # Create and initialize the client
        self.initialize_client()
        
        # Welcome message
        self.add_bot_message("Hello! How can I help you today?")
        
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
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create chat display area (conversation history)
        self.create_chat_display(main_frame)
        
        # Create input area at bottom
        self.create_input_area(main_frame)
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
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
        chat_frame = ttk.LabelFrame(parent, text="Conversation", padding=0)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create a canvas with scrollbar for the chat history
        self.chat_canvas = tk.Canvas(chat_frame, highlightthickness=0,background="#736488")
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for the canvas
        chat_scrollbar = ttk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.chat_canvas.yview,)
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
        self.input_text = tk.Text(input_frame, wrap=tk.WORD, height=3,background="#E29AB2",font=("Noto Sans", 15))
        self.input_text.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        # Button frame for submit and TTS
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Send button
        self.submit_button = ttk.Button(button_frame, text="Send", command=self.process_input)
        self.submit_button.pack(fill=tk.X, pady=(0, 5))
        
        # Speak button
        self.speak_button = ttk.Button(button_frame, text="🔊", width=3, command=self.speak_last_response)
        self.speak_button.pack(fill=tk.X)
    
    def apply_theme(self):
        """Apply a modern chat-like theme to the GUI."""
        self.root.configure(bg="#f0f0f0")
        
        style = ttk.Style()
        style.configure("TFrame", background="#736488")
        style.configure("TLabelframe", background="#312F32")
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
        
        # Timestamp label [Kotak Waktu]
        timestamp = datetime.now().strftime("%H:%M")
        ttk.Label(message_frame, text=timestamp, font=('Arial', 7), foreground='black',background="#736488").pack(side=tk.RIGHT, padx=(0, 5))
        
        # Message bubble frame
        bubble_frame = ttk.Frame(message_frame)
        bubble_frame.pack(side=tk.RIGHT, padx=(50, 10))
        
        # Create the bubble with relief and background color
        msg_label = tk.Text(bubble_frame, wrap=tk.WORD, width=40, height=1, 
                           bg=self.user_bubble_bg, fg=self.user_bubble_fg, 
                           relief=tk.SOLID, borderwidth=1, padx=10, pady=5,background="#8bd450",font=("Noto Sans", 12))
        msg_label.pack(side=tk.RIGHT)
        msg_label.insert(tk.END, message)
        msg_label.config(state=tk.DISABLED)
        
        # Adjust height to fit content
        lines = int(msg_label.index('end-1c').split('.')[0])
        msg_label.config(height=lines)
        
        # Update the chat history
        self.chat_history.append({"role": "user", "content": message, "timestamp": timestamp})
        
        # Auto scroll to the bottom
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
        ttk.Label(timestamp_frame, text=timestamp, font=('Arial', 7), foreground='black',background="#736488").pack(side=tk.BOTTOM)

        # Bot message bubble with border
        bubble_frame = tk.Frame(message_frame, bg="#FFCCCC", padx=10, pady=5, 
                                highlightbackground="black", highlightthickness=1, bd=0, relief="solid")
        bubble_frame.pack(side=tk.LEFT, padx=(5, 5), pady=2, anchor='w')

        # Create message label with monospaced font
        msg_label = tk.Label(bubble_frame, text=message, font=("Noto Sans", 15), 
                            wraplength=350, justify="left", bg="#FFCCCC")
        msg_label.pack()

        # Timestamp
        ttk.Label(timestamp_frame, font=('Arial', 7), foreground='gray').pack(side=tk.BOTTOM)

        # Speak button
        action_frame = ttk.Frame(message_frame)
        action_frame.pack(side=tk.RIGHT, anchor="ne")

        speak_btn = ttk.Button(action_frame, text="🔊", width=2, 
                            command=lambda m=message: self.speak_message(m))
        speak_btn.pack(side=tk.TOP)

        # Auto scroll to bottom
        self.messages_frame.update_idletasks()
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    
    def process_input(self):
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
        timestamp_frame.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(timestamp_frame, image=self.bot_icon, background="#736488").pack(side=tk.TOP)
        
        typing_label = ttk.Label(typing_frame, text="Let me think...", font=('Arial', 9, 'italic'))
        typing_label.pack(side=tk.LEFT, padx=10)
        
        # Update the display
        self.messages_frame.update_idletasks()
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
        
        # Start a separate thread to avoid freezing the UI
        threading.Thread(
            target=self.get_ai_response, 
            args=(user_input, typing_frame),
            daemon=True
        ).start()
    
    def get_ai_response(self, user_input, typing_frame):
        """Get response from Gemini AI in a separate thread."""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-lite", contents=self.rules_content + user_input
            )
            
            # Destroy the "typing" indicator
            self.root.after(0, typing_frame.destroy)
            
            # Update the chat with the response
            self.root.after(0, lambda: self.add_bot_message(response.text))
            self.root.after(0, lambda: self.status_var.set("Response received"))
            self.root.after(0, lambda: self.submit_button.config(state="normal"))
            
        except Exception as e:
            # Destroy the "typing" indicator
            self.root.after(0, typing_frame.destroy)
            
            # Show error message
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            self.root.after(0, lambda: self.add_bot_message(error_msg))
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            self.root.after(0, lambda: self.submit_button.config(state="normal"))
    
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

if __name__ == "__main__":
    
    root = tk.Tk()
    app = GeminiChatApp(root)
    root.mainloop()