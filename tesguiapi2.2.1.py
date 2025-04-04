import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, Menu, messagebox
import threading
import os
import sys # For determining base path if frozen
import json # For potential config file
import time
from datetime import datetime
from PIL import Image, ImageTk
from flask import Flask, request, jsonify, render_template, send_from_directory
# from flask_sock import Sock # Removed as it's not used
import ctypes as ct
import playsound
import tempfile # For temporary TTS files
import shutil

# Assuming aigenerator is a local module in the same directory or installed
try:
    import aigenerator
except ImportError:
    print("Warning: 'aigenerator' module not found. 'generate' command will not work.")
    aigenerator = None # Define it as None to avoid NameErrors later

# --- Configuration ---
# Use relative paths or paths derived from the script location
# Determine base path (works for both script and frozen executable)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
STATIC_FOLDER = os.path.join(BASE_DIR, "static")
DEFAULT_ICON_PATH = os.path.join(BASE_DIR, "icon", "default_icon.png") # Add a default fallback
DEFAULT_RULES_PATH = os.path.join(BASE_DIR, "rules", "default_rules.txt")

# --- Lora Models (Keep as is or load from config) ---
lora_models = [
    ("theresa_arknights_v2.0_for_IL-000012")
    #("LoraModel2.safetensors", 0.5)
]

# --- Flask App Setup ---
# Ensure static folder exists
if not os.path.exists(STATIC_FOLDER):
    os.makedirs(os.path.join(STATIC_FOLDER, "images"), exist_ok=True)

# Initialize Flask app here, but routes will be added within the class method
flask_app = Flask(__name__, static_folder=STATIC_FOLDER, template_folder=BASE_DIR)
# sock = Sock(flask_app) # Removed

# Global variable to hold the Tkinter app instance for Flask routes
tk_app_instance = None

# --- Helper Function ---
def load_config():
    """Loads configuration from config.json."""
    default_config = {
        "api_key": "YOUR_API_KEY_HERE", # Prompt user if not set
        "default_personality": "default",
        "personalities": {
            "default": {
                "name": "Adele",
                "rules_file": os.path.join("rules", "rules.txt"), # Relative paths
                "icon_file": os.path.join("icon", "output-onlinepngtools.png"),
                "bubble_color": "#E29AB2",
                "web_icon_url": "/static/images/default_web_icon.png" # Use relative URL
            },
            "reed": {
                "name": "Reed",
                "rules_file": os.path.join("rules", "rules1.txt"),
                "icon_file": os.path.join("icon", "arknights-reed.png"),
                "bubble_color": "#EBC072",
                "web_icon_url": "/static/images/reed_web_icon.png"
            },
            "wis'adel": {
                "name": "Wis",
                "rules_file": os.path.join("rules", "rules2.txt"),
                "icon_file": os.path.join("icon", "output-onlinepngtools1.png"),
                "bubble_color": "#B43231",
                "web_icon_url": "/static/images/wis_web_icon.png"
            }
        },
        "stable_diffusion_shortcut": r"C:\Users\matth\OneDrive\Desktop\Stable Diffusion.lnk" # Keep specific if needed, but better in config
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Ensure all keys exist, merging with defaults
                config.update({k: default_config[k] for k in default_config if k not in config})
                # Make paths absolute based on BASE_DIR
                for p_key, p_data in config.get("personalities", {}).items():
                    if "rules_file" in p_data:
                         p_data["rules_file"] = os.path.join(BASE_DIR, p_data["rules_file"])
                    if "icon_file" in p_data:
                         p_data["icon_file"] = os.path.join(BASE_DIR, p_data["icon_file"])
                return config
        except json.JSONDecodeError:
            print(f"Error reading {CONFIG_FILE}. Using default configuration.")
            return default_config
        except Exception as e:
            print(f"Error loading config: {e}. Using default configuration.")
            return default_config
    else:
        print(f"{CONFIG_FILE} not found. Creating with default values.")
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(default_config, f, indent=4)
            # Make paths absolute for the current run
            for p_key, p_data in default_config.get("personalities", {}).items():
                 if "rules_file" in p_data:
                     p_data["rules_file"] = os.path.join(BASE_DIR, p_data["rules_file"])
                 if "icon_file" in p_data:
                     p_data["icon_file"] = os.path.join(BASE_DIR, p_data["icon_file"])
            return default_config
        except Exception as e:
            print(f"Error creating default config file: {e}")
            # Manually construct absolute paths for defaults if file creation fails
            for p_key, p_data in default_config.get("personalities", {}).items():
                 if "rules_file" in p_data:
                     p_data["rules_file"] = os.path.join(BASE_DIR, p_data["rules_file"])
                 if "icon_file" in p_data:
                     p_data["icon_file"] = os.path.join(BASE_DIR, p_data["icon_file"])
            return default_config

# --- Main Application Class ---
class GeminiChatApp:
    def __init__(self, root):
        """Initialize the Gemini Chat application."""
        global tk_app_instance # Allow Flask routes to access this instance
        tk_app_instance = self

        self.root = root
        self.root.title("Adele-Bot")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        # --- Load Configuration ---
        self.config = load_config()
        self.api_key = "AIzaSyAe6UbUZN1msgYnx7J9BtlrJsW8vWogFoY"
        self.personalities = self.config.get("personalities", {})
        self.stable_diffusion_shortcut = self.config.get("stable_diffusion_shortcut", "")

        # --- Variables ---
        self.current_personality_key = self.config.get("default_personality", "default")
        if self.current_personality_key not in self.personalities:
            self.current_personality_key = next(iter(self.personalities)) # Fallback to first available

        self.client = None
        self.language = tk.StringVar(value="en")
        self.status_var = tk.StringVar()
        self.chat_history = []
        self.launchcounter = 0
        self.last_bot_response = "" # Store last response text for TTS

        # Response tracking for Flask polling (simple approach)
        self.web_responses = {} # Dictionary to store responses {request_id: response_text}
        self.web_responses_lock = threading.Lock() # Lock for thread safety

        # Load initial personality data
        self.bot_icon_image = None # Pillow Image object
        self.bot_icon_photo = None # ImageTk PhotoImage object
        self.rules_content = ""
        self.load_personality(self.current_personality_key) # Load initial personality

        # Check for API Key
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
            self.prompt_for_api_key()

        # Create GUI components
        self.create_widgets()
        self.apply_theme()
        self.initialize_client()
        self.start_flask_server()

        # Add initial message only after widgets are created
        self.add_bot_message("Stand ready for my arrival, Worm.")
        opening_image_path = os.path.join(BASE_DIR, "photo", "stand-ready-for-my-arrival-worm.jpg")
        self.add_bot_image(opening_image_path)

    def load_personality(self, personality_key):
        """Loads rules, icon, and settings for the given personality."""
        if personality_key not in self.personalities:
            print(f"Warning: Personality '{personality_key}' not found in config. Using default.")
            personality_key = self.config.get("default_personality", "default")
            if personality_key not in self.personalities: # Still not found?
                 personality_key = next(iter(self.personalities)) # Fallback

        self.current_personality_key = personality_key
        personality_data = self.personalities[self.current_personality_key]

        # Load Rules
        rules_path = personality_data.get("rules_file", DEFAULT_RULES_PATH)
        if not os.path.isabs(rules_path):
             rules_path = os.path.join(BASE_DIR, rules_path)
        self.rules_content = self.access_file(rules_path)
        if not self.rules_content:
             print(f"Warning: Rules file not found or empty: {rules_path}")
             self.update_status(f"Warning: Rules file missing for {personality_key}", "orange")


        # Load Icon
        icon_path = personality_data.get("icon_file", DEFAULT_ICON_PATH)
        if not os.path.isabs(icon_path):
            icon_path = os.path.join(BASE_DIR, icon_path)

        try:
            self.bot_icon_image = Image.open(icon_path)
            self.bot_icon_image = self.bot_icon_image.resize((50, 50), Image.LANCZOS) # Smaller icon?
            self.bot_icon_photo = ImageTk.PhotoImage(self.bot_icon_image)
        except FileNotFoundError:
            print(f"Warning: Icon file not found: {icon_path}. Using fallback.")
            self.update_status(f"Warning: Icon file missing for {personality_key}", "orange")
            try: # Try loading a default fallback
                default_icon_full_path = os.path.join(BASE_DIR, DEFAULT_ICON_PATH)
                self.bot_icon_image = Image.open(default_icon_full_path)
                self.bot_icon_image = self.bot_icon_image.resize((50, 50), Image.LANCZOS)
                self.bot_icon_photo = ImageTk.PhotoImage(self.bot_icon_image)
            except FileNotFoundError:
                 print("Error: Default icon file not found either!")
                 self.bot_icon_photo = None # No icon
        except Exception as e:
            print(f"Error loading icon {icon_path}: {e}")
            self.bot_icon_photo = None

        # Update UI elements if they exist
        if hasattr(self, 'chat_title_label'):
             self.chat_title_label.config(text=personality_data.get("name", "Chat"))
        # Note: Existing messages won't change their icon/color. Only new ones will.
        self.update_status(f"Personality set to: {personality_data.get('name', personality_key)}", "blue")


    def get_current_personality_data(self):
        """Returns the dictionary for the current personality."""
        return self.personalities.get(self.current_personality_key, {})

    def prompt_for_api_key(self):
        """Prompts the user to enter the API key if not found."""
        # Simple dialog, consider a more secure input method if needed
        key = tk.simpledialog.askstring("API Key Required", "Please enter your Google Gemini API Key:", show='*')
        if key:
            self.api_key = key
            self.config['api_key'] = key # Update config dictionary
            self.save_config() # Save to file
            self.initialize_client()
        else:
            messagebox.showerror("API Key Error", "API Key is required to run the application. Exiting.")
            self.root.quit() # Or handle differently

    def save_config(self):
        """Saves the current configuration back to config.json."""
        # Convert absolute paths back to relative for saving
        config_to_save = json.loads(json.dumps(self.config)) # Deep copy
        try:
            for p_key, p_data in config_to_save.get("personalities", {}).items():
                if "rules_file" in p_data and os.path.isabs(p_data["rules_file"]):
                    p_data["rules_file"] = os.path.relpath(p_data["rules_file"], BASE_DIR)
                if "icon_file" in p_data and os.path.isabs(p_data["icon_file"]):
                     p_data["icon_file"] = os.path.relpath(p_data["icon_file"], BASE_DIR)

            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_to_save, f, indent=4)
            self.update_status("Configuration saved.", "green")
        except Exception as e:
            print(f"Error saving config: {e}")
            self.update_status(f"Error saving config: {e}", "red")


    def start_flask_server(self):
        """Start the Flask web server in a separate thread."""

        # --- Flask Routes Definition ---
        # Define routes here where they have access to 'self' (the tk_app_instance)

        @flask_app.route('/')
        def home():
            # Pass personality data to the template
            personalities_web = {
                key: {
                    "name": data.get("name", key),
                    "web_icon_url": data.get("web_icon_url", "/static/images/default_web_icon.png")
                } for key, data in tk_app_instance.personalities.items()
            }
            return render_template(
                'webui.html',
                initial_personality=tk_app_instance.current_personality_key,
                personalities=personalities_web
            )

        # Flask automatically serves files from the 'static_folder' at the '/static' URL path
        # So, the @app.route('/static/...') is usually not needed.
        # Ensure your static files (CSS, JS, images) are in the 'static' folder.

        @flask_app.route('/submit', methods=['POST'])
        def submit():
            if not tk_app_instance: return jsonify({"status": "error", "message": "Chatbot not ready"}), 500

            data = request.json
            user_input = data.get('input', '')
            personality = data.get('personality', tk_app_instance.current_personality_key)
            request_id = data.get('request_id', f"web_{time.time()}") # Unique ID for tracking response

            if user_input:
                # Process the input in the main Tkinter thread via root.after
                # Pass necessary info like request_id and personality
                tk_app_instance.root.after(0, tk_app_instance.process_web_input, user_input, request_id, personality)
                return jsonify({"status": "processing", "request_id": request_id})
            else:
                return jsonify({"status": "error", "message": "No input provided"}), 400

        @flask_app.route('/get_response/<request_id>', methods=['GET'])
        def get_response(request_id):
            if not tk_app_instance: return jsonify({"status": "error", "message": "Chatbot not ready"}), 500

            with tk_app_instance.web_responses_lock:
                response_data = tk_app_instance.web_responses.pop(request_id, None) # Get and remove

            if response_data:
                return jsonify({
                    "status": "success",
                    "message": response_data.get("message", ""),
                    "image_url": response_data.get("image_url", None), # Send image URL if generated
                    "personality": response_data.get("personality", tk_app_instance.current_personality_key)
                })
            else:
                # Response not ready yet or invalid request_id
                return jsonify({"status": "pending"}), 202 # HTTP 202 Accepted (still processing)


        # --- Start Flask Thread ---
        self.flask_thread = threading.Thread(
            target=lambda: flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False),
            daemon=True
        )
        self.flask_thread.start()
        self.update_status("Flask server started on http://localhost:5000", "blue")

    def update_status(self, message, color="black"):
        """Update the status bar in the main thread."""
        def _update():
            self.status_var.set(message)
            self.status_bar.config(foreground=color)
        # Always schedule UI updates from the main thread
        if self.root:
             self.root.after(0, _update)

    def process_web_input(self, user_input, request_id, personality_key):
        """Process input received from the web interface (called via root.after)."""
        # Set personality if different
        if personality_key != self.current_personality_key:
            self.load_personality(personality_key)
            # Optionally, add a message to the Tkinter UI indicating the change
            # self.add_system_message(f"Personality changed to {personality_key} via web.")

        # Simulate input in Tkinter UI (optional, could just process directly)
        # self.input_text.delete("1.0", tk.END)
        # self.input_text.insert(tk.END, user_input)

        # Process the input, passing the request_id for web response tracking
        self.process_input(text_input=user_input, from_web=True, web_request_id=request_id)


    def access_file(self, filename):
        """Reads the content of a file."""
        try:
            if os.path.exists(filename):
                with open(filename, "r", encoding='utf-8') as file:
                    return file.read()
            else:
                self.update_status(f"Warning: File not found - {os.path.basename(filename)}", "orange")
                return ""
        except Exception as e:
            self.update_status(f"Error reading file {os.path.basename(filename)}: {e}", "red")
            return ""

    def initialize_client(self):
        """Initialize the Gemini AI client."""
        if not self.api_key or self.api_key == "YOUR_API_KEY_HERE":
             self.update_status("API Key not set. Please configure in Settings.", "red")
             return
        try:
            # Dynamically import genai here to avoid error if not installed initially
            from google import genai
            genai.configure(api_key=self.api_key) # Use configure method
            # Test connection (optional but recommended)
            # models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # if not models:
            #      raise ConnectionError("No suitable models found. Check API key and permissions.")
            # self.client = genai.GenerativeModel('gemini-pro') # Or the specific model you use
            # For simple generation, configure might be enough, or use specific model
            self.client = genai # Use the configured module directly for generate_content if simpler API allows
            self.update_status("Gemini AI Client initialized successfully.", "green")
        except ImportError:
             self.update_status("Error: 'google-generativeai' library not installed.", "red")
             messagebox.showerror("Initialization Error", "The 'google-generativeai' library is required.\nPlease install it using: pip install google-generativeai")
             self.client = None
        except Exception as e:
            self.update_status(f"Error initializing client: {e}", "red")
            self.add_bot_message(f"⚠️ Error: Could not initialize Gemini AI. Check API key/connection.")
            self.client = None


    def create_widgets(self):
        """Create all GUI widgets."""
        main_frame = ttk.Frame(self.root, padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_menu_bar()
        self.create_chat_display(main_frame)
        self.create_input_area(main_frame)

        self.status_bar = tk.Label(main_frame, textvariable=self.status_var, relief="flat", anchor=tk.W, font=('Consolas', 9), background="#8bd450", foreground="black")
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

        # Bind Enter key (only when input has focus)
        self.input_text.bind('<Return>', self.process_input_event)
        # Allow Shift+Enter for newline
        self.input_text.bind('<Shift-Return>', self.insert_newline)

    def process_input_event(self, event=None):
        """Wrapper for handling the Enter key event."""
        self.process_input()
        return "break" # Prevent default newline insertion

    def insert_newline(self, event=None):
         """Inserts a newline character on Shift+Enter."""
         self.input_text.insert(tk.INSERT, "\n")
         return "break" # Prevent the default behavior or the process_input binding

    def create_menu_bar(self):
        """Create the menu bar."""
        menu_bar = Menu(self.root)
        self.root.config(menu=menu_bar)

        settings_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Change API Key", command=self.show_api_dialog)
        # Removing rules file selection, managed via personality/config
        # settings_menu.add_command(label="Select Rules File", command=self.show_rules_dialog)
        settings_menu.add_command(label="Language Settings", command=self.show_language_dialog)
        settings_menu.add_command(label="Select Personality", command=self.show_personality_dialog)
        settings_menu.add_separator()
        settings_menu.add_command(label="Save Configuration", command=self.save_config)


        actions_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Actions", menu=actions_menu)
        actions_menu.add_command(label="Clear Chat", command=self.clear_chat)
        actions_menu.add_command(label="Save Chat History", command=self.save_chat_history)

        help_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_chat_display(self, parent):
        """Create the chat display area."""
        personality_name = self.get_current_personality_data().get("name", "Chat")
        chat_frame = ttk.LabelFrame(parent, text=personality_name, padding=0)
        # Store reference to update title later
        self.chat_title_label = chat_frame # Use the frame itself for the label property
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))

        self.chat_canvas = tk.Canvas(chat_frame, highlightthickness=0, background="#736488")
        chat_scrollbar = ttk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=chat_scrollbar.set)

        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.messages_frame = ttk.Frame(self.chat_canvas, style="Messages.TFrame") # Custom style
        self.messages_frame_id = self.chat_canvas.create_window((0, 0), window=self.messages_frame, anchor=tk.NW)

        self.messages_frame.bind("<Configure>", self.on_frame_configure)
        self.chat_canvas.bind("<Configure>", self.on_canvas_configure)
        # Bind mouse wheel scrolling
        self.chat_canvas.bind_all("<MouseWheel>", self.on_mouse_wheel) # Windows/macOS
        self.chat_canvas.bind_all("<Button-4>", self.on_mouse_wheel) # Linux (scroll up)
        self.chat_canvas.bind_all("<Button-5>", self.on_mouse_wheel) # Linux (scroll down)


    def on_frame_configure(self, event=None):
        """Reset the scroll region."""
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """Update the frame width inside the canvas."""
        self.chat_canvas.itemconfig(self.messages_frame_id, width=event.width)
        # Scroll to bottom when window resizes significantly (optional)
        # self.root.after(100, lambda: self.chat_canvas.yview_moveto(1.0))


    def on_mouse_wheel(self, event):
         """Handle mouse wheel scrolling on the canvas."""
         # Determine scroll direction and amount
         if event.num == 5 or event.delta < 0: # Scroll down
             self.chat_canvas.yview_scroll(1, "units")
         elif event.num == 4 or event.delta > 0: # Scroll up
             self.chat_canvas.yview_scroll(-1, "units")


    def scroll_to_bottom(self):
        """Scrolls the chat canvas to the bottom."""
        # Needs to be deferred slightly after updates
        self.root.after(50, lambda: self.chat_canvas.yview_moveto(1.0))


    def create_input_area(self, parent):
        """Create the input area."""
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))

        self.input_text = tk.Text(input_frame, wrap=tk.WORD, height=3, background="#E29AB2", font=("Noto Sans", 12), borderwidth=2, relief="raised") # Slightly smaller font?
        self.input_text.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0,5))
        # Add scrollbar for input text if it gets long
        input_scrollbar = ttk.Scrollbar(input_frame, orient=tk.VERTICAL, command=self.input_text.yview)
        # Temporarily commented out input scrollbar - pack geometry conflict? Check layout if needed.
        # input_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.input_text['yscrollcommand'] = input_scrollbar.set


        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.RIGHT)

        self.submit_button = ttk.Button(button_frame, text="⬆", command=self.process_input, width=3)
        self.submit_button.pack(fill=tk.X, pady=(0, 2))

        self.speak_button = ttk.Button(button_frame, text="🔊", width=3, command=self.speak_last_response)
        self.speak_button.pack(fill=tk.X)

    def apply_theme(self):
        """Apply visual theme."""
        self.root.configure(bg="#F0F0F0") # Light gray background

        style = ttk.Style()
        style.theme_use('clam') # Or 'alt', 'default', 'classic'

        # Frame backgrounds
        style.configure("TFrame", background="#F0F0F0")
        style.configure("Messages.TFrame", background="#736488") # Inner message frame
        style.configure("TLabelframe", background="#F0F0F0", borderwidth=1, relief="groove")
        style.configure("TLabelframe.Label", background="#F0F0F0", foreground="#333", font=('Arial', 10, 'bold'))

        # Buttons
        style.configure("TButton", padding=5, relief="flat", background="#AEDFF7", foreground="black")
        style.map("TButton",
            background=[('active', '#88CFF0'), ('pressed', '#6FBADE')],
            relief=[('pressed', 'sunken'), ('!pressed', 'raised')])

        # Status bar style (using tk.Label, styled directly)
        self.status_bar.config(background="#D0D0D0", foreground="black")

        # Bubble colors (defined in config, accessed via get_current_personality_data)
        self.user_bubble_bg = "#DCF8C6"
        self.user_bubble_fg = "#000000"
        # Bot bubble color is dynamic based on personality


    def show_api_dialog(self):
        """Show dialog to change API key."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Change API Key")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Enter your Gemini API Key:").pack(pady=(20, 5))
        api_entry = ttk.Entry(dialog, width=50, show="*")
        api_entry.pack(pady=5, padx=20)
        api_entry.insert(0, self.api_key)

        def save_api():
            new_key = api_entry.get().strip()
            if new_key:
                self.api_key = new_key
                self.config['api_key'] = new_key # Update config dict
                self.initialize_client() # Re-initialize
                self.save_config() # Save updated key
                dialog.destroy()
                self.update_status("API key updated and saved.", "green")
            else:
                messagebox.showerror("Error", "API key cannot be empty", parent=dialog)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Save", command=save_api).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        dialog.wait_window()


    def show_language_dialog(self):
        """Show dialog to select TTS language."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Language Settings")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Select Text-to-Speech Language:").pack(pady=(20, 10))
        languages = ["en", "id", "fr", "es", "de", "it", "ja", "ko", "pt", "ru", "zh-CN"]
        lang_dropdown = ttk.Combobox(dialog, textvariable=self.language, values=languages, state="readonly", width=10)
        lang_dropdown.pack(pady=5)
        lang_dropdown.set(self.language.get()) # Ensure current selection is shown

        ttk.Button(dialog, text="OK", command=dialog.destroy).pack(pady=20)
        dialog.wait_window()

    def show_personality_dialog(self):
        """Show dialog to select personality."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Personality")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Choose a personality:").pack(pady=(20, 10))

        personality_keys = list(self.personalities.keys())
        selected_personality = tk.StringVar(value=self.current_personality_key)

        combo = ttk.Combobox(dialog, textvariable=selected_personality, values=personality_keys, state="readonly", width=25)
        combo.pack(pady=5)

        def apply_personality():
            new_key = selected_personality.get()
            if new_key != self.current_personality_key:
                self.load_personality(new_key)
                # Optionally add a system message
                self.add_system_message(f"Personality changed to {self.get_current_personality_data().get('name', new_key)}")
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        ttk.Button(button_frame, text="Select", command=apply_personality).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        dialog.wait_window()


    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo("About Adele-Bot",
                            "Adele-Bot\n"
                            "A chat interface for Google's Gemini AI.\n"
                            "Version 1.1 (Optimized)\n\n"
                            "Uses Tkinter, Flask, gTTS, Pillow, google-generativeai.")


    def _add_message_bubble(self, message, role, image_path=None):
        """Internal helper to add a message bubble."""
        is_user = role == "user"
        personality_data = self.get_current_personality_data()

        message_frame = ttk.Frame(self.messages_frame, style="Messages.TFrame") # Use styled frame
        message_frame.pack(fill=tk.X, pady=2, padx=5, anchor='e' if is_user else 'w')

        timestamp = datetime.now().strftime("%H:%M")

        # --- Bubble Frame ---
        bubble_bg = self.user_bubble_bg if is_user else personality_data.get("bubble_color", "#FFFFFF")
        bubble_fg = self.user_bubble_fg if is_user else "#000000" # Default black text for bot

        bubble_container = ttk.Frame(message_frame, style="Messages.TFrame") # Container for bubble + timestamp/icon
        bubble_container.pack(side=tk.RIGHT if is_user else tk.LEFT, padx=(50 if is_user else 5, 5 if is_user else 50), anchor='se' if is_user else 'sw')

        # --- Icon / Spacer ---
        if not is_user:
            icon_label = ttk.Label(bubble_container, image=self.bot_icon_photo, background="#736488") # Match canvas bg
            if self.bot_icon_photo:
                 icon_label.pack(side=tk.LEFT, anchor='n', padx=(0, 5), pady=(0,0))
            else: # Add padding if no icon
                 ttk.Frame(bubble_container, width=50, style="Messages.TFrame").pack(side=tk.LEFT) # Spacer

        # --- Bubble Content Frame ---
        bubble_content_frame = tk.Frame(bubble_container, bg=bubble_bg, padx=8, pady=4,
                                     highlightbackground="#AAAAAA", highlightthickness=1, bd=0)
        bubble_content_frame.pack(side=tk.LEFT if not is_user else tk.RIGHT, anchor='w')


        # --- Message Text or Image ---
        if image_path:
            try:
                img = Image.open(image_path)
                # Simple fixed size for now, could calculate aspect ratio
                img.thumbnail((200, 200), Image.LANCZOS)
                img_photo = ImageTk.PhotoImage(img)

                img_label = tk.Label(bubble_content_frame, image=img_photo, bg=bubble_bg)
                img_label.image = img_photo # Keep reference!
                img_label.pack()
                # Store image path in chat history maybe?
                content_for_history = f"[Image: {os.path.basename(image_path)}]"
            except FileNotFoundError:
                 print(f"Error: Image file not found for display: {image_path}")
                 msg_text_widget = tk.Label(bubble_content_frame, text=f"[Error: Image not found]",
                                           font=("Noto Sans", 10), wraplength=450, justify=tk.LEFT,
                                           bg=bubble_bg, fg=bubble_fg)
                 msg_text_widget.pack(anchor='w')
                 content_for_history = f"[Error loading image: {os.path.basename(image_path)}]"
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")
                msg_text_widget = tk.Label(bubble_content_frame, text=f"[Error loading image]",
                                           font=("Noto Sans", 10), wraplength=450, justify=tk.LEFT,
                                           bg=bubble_bg, fg=bubble_fg)
                msg_text_widget.pack(anchor='w')
                content_for_history = f"[Error loading image: {os.path.basename(image_path)}]"

        else: # Regular text message
            # Use Label for non-selectable, simpler text display
            # wraplength controls width before wrapping
            msg_label = tk.Label(bubble_content_frame, text=message, font=("Noto Sans", 11),
                                 wraplength=450, justify=tk.LEFT, anchor='w',
                                 bg=bubble_bg, fg=bubble_fg)
            msg_label.pack(anchor='w')
            content_for_history = message
            self.last_bot_response = message # Store for TTS


        # --- Timestamp & Speak Button ---
        details_frame = ttk.Frame(bubble_container, style="Messages.TFrame")
        details_frame.pack(side=tk.BOTTOM, anchor='se' if is_user else 'sw', padx=5, pady=(2,0))

        ttk.Label(details_frame, text=timestamp, font=('Arial', 7),
                  foreground='#555555', background="#736488").pack(side=tk.LEFT if not is_user else tk.RIGHT, padx=2)

        if not is_user and not image_path: # Add speak button only for bot text messages
             speak_btn = tk.Button(details_frame, text="🔊", width=2, height=1, relief="flat", bd=0,
                                   bg="#736488", activebackground="#9486a9", fg="#333", activeforeground="#000",
                                   command=lambda m=message: self.speak_message(m))
             speak_btn.pack(side=tk.LEFT if not is_user else tk.RIGHT, padx=2)


        # --- Add to History ---
        self.chat_history.append({
            "role": role,
            "content": content_for_history, # Store text or image placeholder
            "timestamp": timestamp,
            "personality": self.current_personality_key # Record personality at time of message
        })

        # --- Auto Scroll ---
        self.scroll_to_bottom()


    def add_user_message(self, message):
        """Add a user message bubble."""
        self._add_message_bubble(message, "user")

    def add_bot_message(self, message):
        """Add a bot message bubble."""
        self._add_message_bubble(message, "bot")
        # Update last response for the main speak button
        self.last_bot_response = message


    def add_bot_image(self, image_path):
        """Add a bot image bubble."""
        self._add_message_bubble(None, "bot", image_path=image_path)
        # Potentially return URL for web response
        # web_image_path = self.copy_image_to_static(image_path)
        # return web_image_path # Return the URL for the static file


    def add_system_message(self, message):
         """Adds a centered system message (e.g., personality change)."""
         message_frame = ttk.Frame(self.messages_frame, style="Messages.TFrame")
         message_frame.pack(fill=tk.X, pady=5, padx=10)

         ttk.Label(message_frame, text=message, font=('Arial', 9, 'italic'),
                   foreground='#666666', background="#736488", anchor=tk.CENTER).pack(fill=tk.X)

         # Auto Scroll
         self.scroll_to_bottom()


    def copy_image_to_static(self, source_path):
         """Copies an image to the static folder and returns its web URL."""
         if not os.path.exists(source_path):
             return None
         try:
             # Create a unique filename for the static dir to avoid conflicts
             base, ext = os.path.splitext(os.path.basename(source_path))
             # Include timestamp for uniqueness, replace invalid chars if needed
             safe_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
             static_filename = f"generated_{safe_timestamp}{ext}"
             destination_path = os.path.join(STATIC_FOLDER, "images", static_filename)

             # Ensure the target directory exists
             os.makedirs(os.path.dirname(destination_path), exist_ok=True)

             shutil.copy2(source_path, destination_path) # copy2 preserves metadata
             web_url = f"/static/images/{static_filename}"
             print(f"Copied image to static: {web_url}")
             return web_url
         except Exception as e:
             print(f"Error copying image to static folder: {e}")
             return None

    def check_and_set_personality(self, user_input):
        """Checks input for personality keywords and loads if found."""
        original_key = self.current_personality_key
        new_key = original_key # Default to current

        # More robust check - avoid partial word matches like "wise" for "wis"
        words = user_input.lower().split()
        if "reed" in words:
             new_key = "reed"
        elif "wis'adel" in words or "wis" in words : # Check multiple variations
             new_key = "wis'adel"
        # Add more checks if needed, or use a more sophisticated NLU approach
        elif "adele" in words: # Allow switching back explicitly
             new_key = "default"


        if new_key != original_key and new_key in self.personalities:
            print(f"Personality keyword detected. Switching to: {new_key}")
            self.load_personality(new_key)
            self.add_system_message(f"Personality switched to {self.get_current_personality_data().get('name', new_key)}")
            return True # Indicate personality changed
        return False # Personality did not change


    def process_input(self, event=None, text_input=None, from_web=False, web_request_id=None):
        """Process user input from GUI or web."""
        if text_input is None:
            user_input = self.input_text.get("1.0", tk.END).strip()
        else:
            user_input = text_input # Use provided text (from web)

        if not user_input:
            self.update_status("Please enter some input")
            if from_web: # Respond to web request immediately if input is empty
                 with self.web_responses_lock:
                     self.web_responses[web_request_id] = {"message": "Error: No input provided.", "personality": self.current_personality_key}
            return

        # Clear GUI input field only if input came from GUI
        if not from_web:
             self.input_text.delete("1.0", tk.END)

        # --- Handle Special Commands ---
        if user_input.lower() == "stop":
            self.update_status("Shutdown command received.")
            self.add_bot_message("Shutting down...")
            self.root.after(1000, self.root.quit) # Use quit instead of destroy for cleaner exit
            return

        # Add user message to GUI chat
        self.add_user_message(user_input)

        # Check for personality change *before* processing command/sending to AI
        self.check_and_set_personality(user_input)

        if "bing chilling" in user_input.lower():
            message = ("Zǎoshang hǎo zhōngguó xiànzài wǒ yǒu BING CHILLING 🥶🍦\n"
                       "wǒ hěn xǐhuān BING CHILLING 🥶🍦\n"
                       "dànshì sùdù yǔ jīqíng 9 bǐ BING CHILLING 🥶🍦\n"
                       "sùdù yǔ jīqíng sùdù yǔ jīqíng 9 wǒ zuì xǐhuān")
            self.add_bot_message(message)
            img_path = os.path.join(BASE_DIR, "artworks-IDl2hpyAbd8R2IVf-vyEd2A-t500x500.jpg")
            web_image_url = self.copy_image_to_static(img_path) # Copy for web access
            self.add_bot_image(img_path) # Display in Tkinter

            if from_web: # Respond to web request
                 with self.web_responses_lock:
                     self.web_responses[web_request_id] = {
                          "message": message,
                          "image_url": web_image_url,
                          "personality": self.current_personality_key
                          }
            return # Command handled

        if "generate" in user_input.lower() and aigenerator:
            if self.launchcounter == 0 and self.stable_diffusion_shortcut:
                try:
                    os.startfile(self.stable_diffusion_shortcut) # More reliable than os.system
                    self.launchcounter += 1
                except FileNotFoundError:
                     self.update_status("Stable Diffusion shortcut not found.", "orange")
                except Exception as e:
                     self.update_status(f"Error launching Stable Diffusion: {e}", "red")

            prompt = user_input.replace("generate", "", 1).strip() # Replace only first instance
            if not prompt:
                self.add_bot_message("Please provide a prompt after 'generate'.")
                if from_web:
                     with self.web_responses_lock:
                          self.web_responses[web_request_id] = {"message": "Please provide a prompt after 'generate'.", "personality": self.current_personality_key}
                return

            # Define paths
            # Use a timestamp in the output filename to avoid overwriting
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"output_{timestamp_str}.png"
            output_path = os.path.join(BASE_DIR, output_filename)

            # Add a "Generating..." message
            generating_msg = self.add_bot_message(f"Generating image for: '{prompt}'...")

            # Start generation in a thread
            threading.Thread(
                target=self.run_image_generation,
                args=(prompt, output_path, from_web, web_request_id, generating_msg), # Pass necessary context
                daemon=True
            ).start()
            return # Handled by thread

        # --- Default AI Processing ---
        self.submit_button.config(state="disabled")
        self.update_status("Processing request...")

        # Add "typing" indicator (optional, can be complex to manage perfectly)
        typing_indicator = self.add_bot_message("...") # Simple indicator

        # Start AI response thread
        threading.Thread(
            target=self.get_ai_response,
            args=(user_input, from_web, web_request_id, typing_indicator),
            daemon=True
        ).start()


    def run_image_generation(self, prompt, output_path, from_web, web_request_id, generating_msg_widget):
        """Runs image generation in a thread and updates UI/Web."""
        if not aigenerator:
            self.root.after(0, lambda: self.add_bot_message("Image generation module not available."))
            if from_web:
                with self.web_responses_lock:
                    self.web_responses[web_request_id] = {"message": "Image generation module not available.", "personality": self.current_personality_key}
            # Remove "Generating..." message
            if generating_msg_widget:
                 self.root.after(0, generating_msg_widget.destroy)
            return

        web_image_url = None
        try:
            self.update_status(f"Generating image: {prompt[:30]}...", "blue")
            aigenerator.generate_and_save_image(prompt, output_path, lora_models)
            self.update_status("Image generation complete.", "green")

            # Copy to static *after* generation is successful
            web_image_url = self.copy_image_to_static(output_path)

            # Update Tkinter UI (replace "Generating..." or add image)
            # Option 1: Replace the "Generating..." message text with the image
            # self.root.after(0, lambda: self.update_message_with_image(generating_msg_widget, output_path))

            # Option 2: Remove "Generating..." and add new image bubble (simpler)
            if generating_msg_widget:
                 self.root.after(0, generating_msg_widget.destroy) # Remove indicator
            self.root.after(0, lambda: self.add_bot_image(output_path)) # Add image

            # Prepare web response
            if from_web:
                with self.web_responses_lock:
                    self.web_responses[web_request_id] = {
                        "message": f"Generated image for: '{prompt}'", # Add confirmation text
                        "image_url": web_image_url,
                         "personality": self.current_personality_key
                         }

        except Exception as e:
            error_msg = f"Error during image generation: {e}"
            print(error_msg)
            self.update_status(error_msg, "red")
             # Update Tkinter UI
            if generating_msg_widget:
                self.root.after(0, generating_msg_widget.destroy)
            self.root.after(0, lambda: self.add_bot_message(f"Sorry, I couldn't generate the image. {e}"))
             # Prepare web response
            if from_web:
                with self.web_responses_lock:
                    self.web_responses[web_request_id] = {"message": error_msg, "personality": self.current_personality_key}

        finally:
             # Clean up temporary output file if desired, or keep it
             # os.remove(output_path) # Optional cleanup
             pass


    def get_ai_response(self, user_input, from_web, web_request_id, typing_indicator):
        """Get response from Gemini AI in a thread."""
        if not self.client:
            error_msg = "Gemini AI client is not initialized."
            self.root.after(0, self._handle_ai_response, error_msg, None, from_web, web_request_id, typing_indicator)
            return

        try:
            # Construct the prompt using rules + history + input (optional history)
            # Simple approach: rules + current input
            full_prompt = self.rules_content + "\n\nUser: " + user_input + "\nAI:"

            # More complex: include recent history
            # history_context = "\n".join([f"{'User' if msg['role']=='user' else 'AI'}: {msg['content']}"
            #                              for msg in self.chat_history[-5:]]) # Last 5 messages
            # full_prompt = self.rules_content + "\n\n" + history_context + "\n\nUser: " + user_input + "\nAI:"


            # Use the correct method based on how genai was initialized
            # Assuming genai.configure was used and we use the top-level generate_content
            from google import genai # Ensure import is available in thread
            model = genai.GenerativeModel('gemini-pro') # Or the model name you intend to use
            response = model.generate_content(full_prompt)

            # Check for blocked content or other issues
            if not response.candidates or not response.candidates[0].content.parts:
                 # Handle safety blocks or empty responses
                 safety_feedback = response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'No details provided.'
                 error_msg = f"Response blocked or empty. Reason: {safety_feedback}"
                 # Log the full response for debugging
                 print(f"Blocked/Empty Response Details: {response}")
                 raise ValueError(error_msg)

            response_text = response.text

            # Start TTS in a separate thread *after* getting the response
            threading.Thread(target=self.text_to_speech, args=(response_text,), daemon=True).start()

            # Schedule UI update back on the main thread
            self.root.after(0, self._handle_ai_response, response_text, None, from_web, web_request_id, typing_indicator)

        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {e}"
            print(f"AI Error: {e}") # Log detailed error
            # Schedule UI update back on the main thread
            self.root.after(0, self._handle_ai_response, error_msg, e, from_web, web_request_id, typing_indicator)


    def _handle_ai_response(self, response_text, error, from_web, web_request_id, typing_indicator):
        """Handles updating the UI and web response after AI call (runs in main thread)."""
        # Remove "typing" indicator
        if typing_indicator:
            # Need a way to reliably find and destroy the indicator frame/widget
            # This is tricky if other messages arrived. A direct reference is best.
            # For now, let's assume it's the last widget. This is fragile.
            # children = self.messages_frame.winfo_children()
            # if children and children[-1] == typing_indicator: # Simple check
            #     typing_indicator.destroy()
            # Safer: Pass the actual widget reference if possible, or use IDs.
            # If we passed the Frame widget:
             try:
                  typing_indicator.destroy()
             except tk.TclError: # Widget might already be gone
                  pass


        # Add the actual bot message (or error)
        self.add_bot_message(response_text)
        self.update_status("Response received" if not error else f"Error: {error}", "black" if not error else "red")
        self.submit_button.config(state="normal") # Re-enable button

        # Store response for web client
        if from_web:
            with self.web_responses_lock:
                self.web_responses[web_request_id] = {"message": response_text, "personality": self.current_personality_key}


    def speak_message(self, message):
        """Convert a specific message to speech."""
        if not message: return
        self.update_status("Converting to speech...")
        threading.Thread(target=self.text_to_speech, args=(message,), daemon=True).start()

    def speak_last_response(self):
        """Speak the last recorded bot text response."""
        if self.last_bot_response:
            self.speak_message(self.last_bot_response)
        else:
            self.update_status("No bot messages logged to speak")

    def text_to_speech(self, text):
        """Convert text to speech using a temporary file."""
        if not text: return
        try:
            # Dynamically import gTTS here if it's optional
            from gtts import gTTS
            language = self.language.get()

            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_filename = fp.name
                tts = gTTS(text=text, lang=language, slow=False)
                tts.save(temp_filename)

            self.update_status("Playing speech...")
            # Use playsound (ensure it's installed and compatible)
            playsound.playsound(temp_filename, True) # True blocks until finished
            self.update_status("Speech finished.")

        except ImportError:
             self.update_status("gTTS library not found. Cannot speak.", "red")
        except Exception as e:
            error_msg = f"Error in TTS: {e}"
            print(error_msg)
            self.update_status(error_msg, "red")
        finally:
            # Clean up the temporary file
            if 'temp_filename' in locals() and os.path.exists(temp_filename):
                os.remove(temp_filename)


    def clear_chat(self):
        """Clear the chat display and history."""
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        self.chat_history = []
        self.add_bot_message("Chat history cleared.") # Provide feedback
        self.update_status("Chat cleared.")

    def save_chat_history(self):
        """Save chat history to a file."""
        if not self.chat_history:
            self.update_status("No chat history to save")
            return

        filename = filedialog.asksaveasfilename(
            title="Save Chat History",
            defaultextension=".txt",
            filetypes=(("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")),
            initialdir=BASE_DIR
        )
        if not filename: return

        try:
            file_ext = os.path.splitext(filename)[1].lower()
            with open(filename, "w", encoding="utf-8") as f:
                if file_ext == ".json":
                    # Save as JSON
                    json.dump({
                         "saved_at": datetime.now().isoformat(),
                         "history": self.chat_history # Already includes role, content, timestamp, personality
                         }, f, indent=2)
                else:
                    # Save as Text
                    f.write(f"=== Chat History ({self.get_current_personality_data().get('name', self.current_personality_key)}) ===\n")
                    f.write(f"Saved at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    for msg in self.chat_history:
                        role_name = "You" if msg["role"] == "user" else self.personalities.get(msg["personality"], {}).get("name", msg["personality"])
                        f.write(f"[{msg['timestamp']}] ({role_name}):\n{msg['content']}\n\n")

            self.update_status(f"Chat history saved to {os.path.basename(filename)}", "green")

        except Exception as e:
            self.update_status(f"Error saving chat history: {e}", "red")
            messagebox.showerror("Save Error", f"Could not save chat history:\n{e}")

# --- Dark Title Bar (Windows Specific) ---
def set_dark_title_bar(window):
    """Sets dark title bar on Windows 10/11. Safe to call on other platforms."""
    if sys.platform != "win32":
        return # Only works on Windows
    try:
        window.update()
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
        get_parent = ct.windll.user32.GetParent
        hwnd = get_parent(window.winfo_id())
        value = 2 # Default value for dark mode
        value = ct.c_int(value)
        set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ct.byref(value), ct.sizeof(value))
        print("Attempted to set dark title bar.")
    except Exception as e:
        print(f"Could not set dark title bar: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    # Apply dark title bar before GeminiChatApp initializes fully
    set_dark_title_bar(root)
    app = GeminiChatApp(root)
    root.mainloop()