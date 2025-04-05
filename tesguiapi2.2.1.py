import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, Menu
import threading
import os
from google import genai
from gtts import gTTS
import time
from datetime import datetime
from PIL import Image, ImageTk
from flask import Flask, request, jsonify, render_template
from flask_sock import Sock
import json
import ctypes as ct
import playsound
import aigenerator
import shutil

lora_models = [
    ("theresa_arknights_v2.0_for_IL-000012")
    #("LoraModel2.safetensors", 0.5)
]

from flask import Flask, send_from_directory

app = Flask(__name__, static_folder="static")

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory("static", filename)


class GeminiChatApp:
    

    
    
    def __init__(self, root):
        """Initialize the Gemini Chat application."""
        self.root = root
        self.root.title("Adele-Bot")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        self.personalities = {
        "default": {
            "name": "Adele",
            "rules_file": "rules\rules.txt",
            "icon_path": "output-onlinepngtools.png",
            "bubble_color": "#E29AB2",
            "web_icon_url": "https://i.imgur.com/7zL5vug.png"
        },
        "reed": {
            "name": "Reed",
            "rules_file": "rules\rules1.txt",
            "icon_path": "icon/arknights-reed.png",
            "bubble_color": "#EBC072",
            "web_icon_url": "https://i.imgur.com/bobicon.png"
        },
        "wis'adel": {
            "name": "Wis",
            "rules_file": "rules\rules2.txt",
            "icon_path": "icon/output-onlinepngtools1.png",
            "bubble_color": "#B43231",
            "web_icon_url": "https://i.imgur.com/aliceicon.png"
        }
    }
        
        
        
        # Variables
        self.api_key = "AIzaSyAe6UbUZN1msgYnx7J9BtlrJsW8vWogFoY"  # Default API key
        self.identity = None  # Default personality
        if self.identity not in self.personalities:
            self.identity = "default"  # Fallback to default if invalid
        self.bot_icon = self.personalities[self.identity]["icon_path"]
        self.rules_file = self.personalities[self.identity]["rules_file"]
        self.rules_content = self.access_file(self.rules_file)
        self.client = None
        self.language = tk.StringVar(value="en")
        self.status_var = tk.StringVar()
        self.chat_history = []  # To store chat history
        
        self.cache_file = "chatcache.txt"
        # Clear the content of the cache file
        with open(self.cache_file, 'w') as file:
            file.write("Previous chat (Memory):")  # Clears and writes in one step
        self.launchcounter = 0
        
        
        
        


        
        self.bot_icon = Image.open(r"icon/output-onlinepngtools1.png")
        self.bot_icon = self.bot_icon.resize((70, 70), Image.LANCZOS)  # Resize the image if necessary
        self.bot_icon = ImageTk.PhotoImage(self.bot_icon)
       
       
        
        
        
        # Create GUI components
        self.create_widgets()
        
        # Apply a simple theme
        self.apply_theme()
        
        # Create and initialize the client
        self.initialize_client()

        self.start_flask_server()
        
        # Welcome message
        self.add_bot_message("Stand ready for my arrival, Worm.")

        image_pathopening = r"photo/stand-ready-for-my-arrival-worm.jpg"
    
        self.add_bot_image(image_pathopening)



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
            return render_template('webui.html')
        
        @app.route('/about')
        def about():
            return render_template_string('webui.html')

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
        message_frame.pack(fill=tk.X, pady=5, padx=10)

        # Timestamp label
        timestamp = datetime.now().strftime("%H:%M")
        ttk.Label(message_frame, text=timestamp, font=('Arial', 7), 
                foreground='black', background="#736488").pack(side=tk.RIGHT, padx=(0, 5))
        
        #ttk.Label(message_frame, image=self.bot_icon, background="#000000").pack(side=tk.RIGHT, padx=10)
        #ttk.Label(message_frame, text=timestamp, font=('Arial', 7), foreground='black', background="#736488").pack(side=tk.BOTTOM)


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
        bubble_frame = tk.Frame(message_frame, bg=self.personalities[self.identity]["bubble_color"], padx=10, pady=5, 
                                highlightbackground="black", highlightthickness=1, bd=0, relief="solid")
        bubble_frame.pack(side=tk.LEFT, padx=(5, 5), pady=0, anchor='w')

        # Add message using tk.Label
        msg_label = tk.Label(
            bubble_frame,
            text=message,
            font=("Noto Sans", 15),
            wraplength=500,  # Maximum width before wrapping
            bg=self.personalities[self.identity]["bubble_color"],
            anchor="w", 
            justify="left"  # Align text to the left
        )
        msg_label.pack()

        # Speak button
        action_frame = ttk.Frame(message_frame)
        action_frame.pack(side=tk.LEFT, anchor="w", padx=10)

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
            bubble_frame = tk.Frame(message_frame, bg=self.personalities[self.identity]["bubble_color"], padx=10, pady=5, 
                                    highlightbackground="black", highlightthickness=1, bd=0, relief="solid")
            bubble_frame.pack(side=tk.LEFT, padx=(5, 5), pady=0, anchor='w')

            # Load and resize image
            img = Image.open(image_path)
            img = img.resize((200, 200))  # Adjust size as needed
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

    
    def called_identity(self, user_input):

        if "reed" in user_input.lower():
              
            self.identity = "reed"        
        elif "wis" in user_input.lower():  # Gunakan `elif` agar hanya satu yang dipilih
            self.identity = "wis'adel"   
        else:
            self.identity = "default"

        filename = self.personalities[self.identity]["rules_file"]    
        self.rules_content = self.access_file(filename)

        self.bot_icon = Image.open(self.personalities[self.identity]["icon_path"])
        self.bot_icon = self.bot_icon.resize((70, 70), Image.LANCZOS)  # Resize the image if necessary
        self.bot_icon = ImageTk.PhotoImage(self.bot_icon)

        return self.identity, self.bot_icon

    
    def process_input(self, from_web=False):

        """Process the user input and get a response from the Gemini AI."""
        # Get user input
        user_input = self.input_text.get("1.0", tk.END).strip()

        self.called_identity(user_input)
        print(f"AI identity [{self.identity}]")  
        

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
            image_path = "artworks-IDl2hpyAbd8R2IVf-vyEd2A-t500x500.jpg"
            self.add_bot_image(image_path)
            
            # If from web, store the response
            if from_web:
                self.latest_web_response = message
                self.has_new_response = True
                self.waiting_for_response = False

            # Clear input
            self.input_text.delete("1.0", tk.END)
            return
        
        if "generate" in user_input.lower():
            
            print(self.launchcounter)
            if self.launchcounter == 0:
                os.system(r'start "" "C:\\Users\\matth\\OneDrive\\Desktop\\Stable Diffusion.lnk"')
                self.launchcounter += 1  # Update x locally
                

            self.add_user_message(user_input)
            user_input = user_input.replace("generate", "").strip()
            print(user_input)
            
            image_path = "output.png"
            destination_path = "static/images/generated.png"

            def generate_and_display():
                aigenerator.generate_and_save_image(user_input, image_path, lora_models)
                self.add_bot_image(image_path)
                print("Image generated")


            shutil.copy(image_path, destination_path)
            # Run the function in a new thread
            #thread = threading.Thread(target=generate_and_display)
            #thread.start()
            generate_and_display()

            shutil.copy(image_path, destination_path)
            self.add_bot_image(image_path)
            
            if from_web:
                self.latest_web_response = message
                self.has_new_response = True
                self.waiting_for_response = False


            #Clear input
            self.input_text.delete("1.0", tk.END)
            
            return self.launchcounter
            

         
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

        typing_label = tk.Frame(typing_frame, bg=self.personalities["wis'adel"]["bubble_color"], padx=10, pady=5, 
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

        return self.identity
    
    def cache_response(self, user_input, response, mode):
        """
        Handles caching and retrieval of chatbot responses.

        mode 1: Append user input + bot response.
        mode 2: Retrieve the last saved response.
        """

        if mode == 1:
            if user_input is None or response is None:
                raise ValueError("user_input and response must be provided in mode 1")

            # Append chat history instead of overwriting
            
            chat_entry = f"\n- User: {user_input}\n- LLM: {response.text}"

            with open(self.cache_file, "a") as file:  # "a" appends instead of overwriting
                file.write(chat_entry)

            return "Response cached."

        elif mode == 2:
            try:
                with open(self.cache_file, "r") as file:
                    previous_response = file.read()
                return previous_response
            except FileNotFoundError:
                return "No previous response found."

        else:
            return "Invalid mode."
    
    
    def get_ai_response(self, user_input, typing_frame, from_web=False):
        """Get response from Gemini AI in a separate thread with previous chat context."""
        try:
            # Retrieve last saved conversation from cache (mode=2)
            previous_conversation = self.cache_response(None, None, mode=2)

            # If there's no previous conversation, just use user input
            full_prompt = self.rules_content + previous_conversation + "\nCurret chat (Focus to this):\n-User: " + user_input
            print ("-==========================\n",full_prompt,"\n======================================\n")
            # Call AI model with previous context + new input
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-lite", contents=full_prompt
            )

            # Handle cases where response is missing
            ai_text = response.text.strip() if response and hasattr(response, "text") else "Error: No valid response from AI."

            # Store response in cache
            self.cache_response(user_input, response, mode=1)

            # Automatic text-to-speech
            threading.Thread(target=self.speak_message, args=(ai_text,), daemon=True).start()

            #print(f"User: {user_input}")
            #print(f"Bot: {ai_text}")

            # Destroy the "typing" indicator
            self.root.after(0, typing_frame.destroy)

            # Update the chat UI
            self.root.after(0, lambda: self.add_bot_message(ai_text))
            self.root.after(0, lambda: self.status_var.set("Response received"))
            self.root.after(0, lambda: self.submit_button.config(state="normal"))

            # If called from web, store response
            if from_web:
                self.latest_web_response = ai_text
                self.has_new_response = True
                self.waiting_for_response = False

        except Exception as e:
            # Destroy typing indicator
            self.root.after(0, typing_frame.destroy)

            # Error message
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            print(error_msg)

            self.root.after(0, lambda: self.add_bot_message(error_msg))
            self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)}"))
            self.root.after(0, lambda: self.submit_button.config(state="normal"))

            # If called from web, store error
            if from_web:
                self.latest_web_response = error_msg
                self.has_new_response = True
                self.waiting_for_response = False

            # Log errors for debugging
            with open("error_log.txt", "a") as err_file:
                err_file.write(f"Error: {str(e)}\n")


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
        """Convert text to speech and play directly."""
        try:
            language = self.language.get()
            myobj = gTTS(text=text, lang=language, slow=False)
            filename = "response.mp3"
            myobj.save(filename)
            
            # Play the audio
            playsound.playsound(filename)

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