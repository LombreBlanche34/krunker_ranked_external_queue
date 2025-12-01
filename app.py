import customtkinter as ctk
import json
import os
import requests
import websocket
import threading
from pathlib import Path
import time
from datetime import datetime
import re
import base64
from playsound3 import playsound

class KrunkerQueueApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window configuration
        self.title("Krunker.io External Queue")
        self.geometry("870x870")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Variables
        self.access_token = None
        self.ws = None
        self.timer_running = False
        self.elapsed_time = 0
        self.timer_thread = None
        self.ws_thread = None
        
        # Custom clients
        self.custom_clients = {
            "Crankshaft": str(Path.home() / "AppData/Roaming/crankshaft/Local Storage/leveldb"),
            "PC7": str(Path.home() / "AppData/Roaming/pc7/Local Storage/leveldb")
        }
        
        self.create_widgets()
        self.log("Application started")
        
    def log(self, message, level="INFO"):
        """Displays a message in the console with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def create_widgets(self):
        # Title with pixelated style
        title_label = ctk.CTkLabel(self, text="🎮 KRUNKER QUEUE", 
                                    font=ctk.CTkFont(size=32, weight="bold"))
        title_label.pack(pady=20)
        
        # Main frame with tabs
        self.tabview = ctk.CTkTabview(self, width=700, height=650)
        self.tabview.pack(pady=10, padx=20)
        
        # Creating tabs
        self.tabview.add("🔑 Auth")
        self.tabview.add("🎯 Queue")
        self.tabview.add("⚙️ Settings")
        
        self.create_auth_tab()
        self.create_queue_tab()
        self.create_settings_tab()
        
    def create_styled_button(self, parent, text, command, color, hover_color, width=180, height=50):
        """Creates a styled button like in the image"""
        button = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            corner_radius=10,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=color,
            hover_color=hover_color,
            border_width=0
        )
        return button
        
    def create_auth_tab(self):
        auth_frame = self.tabview.tab("🔑 Auth")
        
        # Client Section
        client_section = ctk.CTkFrame(auth_frame, corner_radius=15)
        client_section.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(client_section, text="📁 Client Authentication", 
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        self.client_combo = ctk.CTkComboBox(
            client_section, 
            values=list(self.custom_clients.keys()),
            width=350,
            height=40,
            font=ctk.CTkFont(size=14),
            corner_radius=10
        )
        self.client_combo.pack(pady=10)
        self.client_combo.set("Crankshaft")
        
        # Styled blue button
        client_btn = self.create_styled_button(
            client_section,
            "🔍 Get Token",
            self.get_token_from_client,
            "#3498db",  # Blue
            "#2980b9",  # Dark blue on hover
            width=250
        )
        client_btn.pack(pady=15)
        
        # Separator
        separator = ctk.CTkFrame(auth_frame, height=2, fg_color="gray30")
        separator.pack(pady=15, padx=40, fill="x")
        ctk.CTkLabel(separator, text="OR", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)
        
        # Login Section
        login_section = ctk.CTkFrame(auth_frame, corner_radius=15)
        login_section.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(login_section, text="👤 Login Authentication (if client dosent work)", 
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        self.username_entry = ctk.CTkEntry(
            login_section,
            placeholder_text="Username",
            width=350,
            height=40,
            font=ctk.CTkFont(size=14),
            corner_radius=10
        )
        self.username_entry.pack(pady=5)
        
        self.password_entry = ctk.CTkEntry(
            login_section,
            placeholder_text="Password",
            show="●",
            width=350,
            height=40,
            font=ctk.CTkFont(size=14),
            corner_radius=10
        )
        self.password_entry.pack(pady=5)
        
        self.twofa_entry = ctk.CTkEntry(
            login_section,
            placeholder_text="2FA Code (if needed)",
            width=350,
            height=40,
            font=ctk.CTkFont(size=14),
            corner_radius=10
        )
        self.twofa_entry.pack(pady=5)
        
        # Styled purple button
        login_btn = self.create_styled_button(
            login_section,
            "🔐 Login",
            self.login_with_credentials,
            "#9b59b6",  # Purple
            "#8e44ad",  # Dark purple on hover
            width=250
        )
        login_btn.pack(pady=15)
        
        # Separator
        separator2 = ctk.CTkFrame(auth_frame, height=2, fg_color="gray30")
        separator2.pack(pady=15, padx=40, fill="x")
        ctk.CTkLabel(separator2, text="OR", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=15)
        
        # Manual Token Section
        manual_section = ctk.CTkFrame(auth_frame, corner_radius=15)
        manual_section.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(manual_section, text="✍️ Manual Token (for advanced user, need __FRVR_auth_access_token)", 
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        self.manual_token_entry = ctk.CTkEntry(
            manual_section,
            placeholder_text="Paste your token here",
            width=450,
            height=40,
            font=ctk.CTkFont(size=12),
            corner_radius=10
        )
        self.manual_token_entry.pack(pady=10)
        
        # Styled orange button
        manual_btn = self.create_styled_button(
            manual_section,
            "📋 Use Token",
            self.use_manual_token,
            "#e67e22",  # Orange
            "#d35400",  # Dark orange on hover
            width=250
        )
        manual_btn.pack(pady=15)
        
        # Status
        self.auth_status = ctk.CTkLabel(
            auth_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=10
        )
        self.auth_status.pack(pady=15)
        
    def create_queue_tab(self):
        queue_frame = self.tabview.tab("🎯 Queue")
        
        # Regions
        region_frame = ctk.CTkFrame(queue_frame, corner_radius=15)
        region_frame.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(region_frame, text="🌍 Regions", 
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        self.regions = {}
        regions_list = [("Asia", "as"), ("🇪🇺 Europe", "eu"), ("🇺🇸 North America", "na")]
        
        region_checkboxes = ctk.CTkFrame(region_frame, fg_color="transparent")
        region_checkboxes.pack(pady=10)
        
        for idx, (name, code) in enumerate(regions_list):
            var = ctk.BooleanVar(value=(code == "eu"))
            cb = ctk.CTkCheckBox(
                region_checkboxes,
                text=name,
                variable=var,
                font=ctk.CTkFont(size=14),
                corner_radius=8,
                checkbox_width=25,
                checkbox_height=25
            )
            cb.grid(row=0, column=idx, padx=15, pady=5)
            self.regions[code] = var
        
        # Maps
        map_frame = ctk.CTkFrame(queue_frame, corner_radius=15)
        map_frame.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(map_frame, text="🗺️ Maps", 
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        self.maps = {}
        maps_list = [
            ("Burg", "burg_new"),
            ("Sandstorm", "sandstorm_v3"),
            ("Undergrowth", "undergrowth"),
            ("Industry", "industry"),
            ("Site", "site"),
            ("Bureau", "bureau"),
            ("Eterno", "eterno_sim")
        ]
        
        map_checkboxes = ctk.CTkFrame(map_frame, fg_color="transparent")
        map_checkboxes.pack(pady=10)
        
        for idx, (name, code) in enumerate(maps_list):
            var = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(
                map_checkboxes,
                text=name,
                variable=var,
                font=ctk.CTkFont(size=13),
                corner_radius=8,
                checkbox_width=22,
                checkbox_height=22
            )
            cb.grid(row=idx // 3, column=idx % 3, padx=15, pady=8, sticky="w")
            self.maps[code] = var
        
        # Timer and controls
        control_frame = ctk.CTkFrame(queue_frame, corner_radius=15)
        control_frame.pack(pady=20, padx=20, fill="x")
        
        self.timer_label = ctk.CTkLabel(
            control_frame,
            text="00:00",
            font=ctk.CTkFont(size=56, weight="bold"),
            text_color="#3498db"
        )
        self.timer_label.pack(pady=15)
        
        self.queue_status_label = ctk.CTkLabel(
            control_frame,
            text="Not Connected",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.queue_status_label.pack(pady=10)
        
        # Control buttons
        button_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_frame.pack(pady=20)
        
        # Start button (green)
        self.start_button = self.create_styled_button(
            button_frame,
            "▶️ Start Queue",
            self.start_queue,
            "#27ae60",  # Green
            "#229954",  # Dark green on hover
            width=220,
            height=55
        )
        self.start_button.grid(row=0, column=0, padx=10)
        
        # Stop button (red)
        self.stop_button = self.create_styled_button(
            button_frame,
            "⏹️ Stop",
            self.stop_queue,
            "#e74c3c",  # Red
            "#c0392b",  # Dark red on hover
            width=220,
            height=55
        )
        self.stop_button.grid(row=0, column=1, padx=10)
        self.stop_button.configure(state="disabled")
        
    def create_settings_tab(self):
        settings_frame = self.tabview.tab("⚙️ Settings")
        
        # Add custom client
        client_frame = ctk.CTkFrame(settings_frame, corner_radius=15)
        client_frame.pack(pady=15, padx=20, fill="x")
        
        ctk.CTkLabel(client_frame, text="Add Custom Client", 
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        self.new_client_name = ctk.CTkEntry(
            client_frame,
            placeholder_text="Client Name",
            width=400,
            height=40,
            font=ctk.CTkFont(size=14),
            corner_radius=10
        )
        self.new_client_name.pack(pady=8)
        
        self.new_client_path = ctk.CTkEntry(
            client_frame,
            placeholder_text="Path to Local Storage/leveldb",
            width=400,
            height=40,
            font=ctk.CTkFont(size=14),
            corner_radius=10
        )
        self.new_client_path.pack(pady=8)
        
        add_btn = self.create_styled_button(
            client_frame,
            "➕ Add Client",
            self.add_custom_client,
            "#16a085",  # Turquoise
            "#138d75",  # Dark turquoise
            width=220
        )
        add_btn.pack(pady=15)
        
        # Client list
        ctk.CTkLabel(settings_frame, text="Configured Clients", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.clients_list = ctk.CTkTextbox(
            settings_frame,
            height=250,
            width=500,
            font=ctk.CTkFont(size=12),
            corner_radius=10
        )
        self.clients_list.pack(pady=10)
        self.update_clients_list()
    
    def switch_to_queue_tab(self):
        """Switches to the Queue tab"""
        self.log("Switching to Queue tab")
        self.tabview.set("🎯 Queue")
    
    def validate_jwt_token(self, token):
        """Validates the structure of a JWT token"""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                self.log(f"Invalid token: {len(parts)} parts instead of 3", "ERROR")
                return False
            
            for i, part in enumerate(parts[:2]):
                try:
                    padded = part + '=' * (4 - len(part) % 4)
                    decoded = base64.urlsafe_b64decode(padded)
                    json.loads(decoded)
                    self.log(f"JWT part {i+1} validated", "SUCCESS")
                except Exception as e:
                    self.log(f"Validation error part {i+1}: {str(e)}", "ERROR")
                    return False
            
            self.log("Valid JWT token!", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Token validation error: {str(e)}", "ERROR")
            return False
    
    def use_manual_token(self):
        """Uses a manually entered token"""
        token = self.manual_token_entry.get().strip()
        
        self.log("Attempting to use manual token")
        
        if not token:
            self.log("Empty token", "WARNING")
            self.auth_status.configure(text="❌ Enter a token", text_color="#e74c3c")
            return
        
        if self.validate_jwt_token(token):
            self.access_token = token
            self.log("Manual token accepted", "SUCCESS")
            self.auth_status.configure(text="✅ Token Accepted!", text_color="#27ae60")
            self.after(1000, self.switch_to_queue_tab)
        else:
            self.log("Invalid manual token", "ERROR")
            self.auth_status.configure(text="❌ Invalid Token", text_color="#e74c3c")
        
    def get_token_from_client(self):
        """Retrieves the token from the client's localStorage"""
        try:
            client_name = self.client_combo.get()
            client_path = self.custom_clients.get(client_name)
            
            self.log(f"Attempting to retrieve token for client: {client_name}")
            self.log(f"Path: {client_path}")
            
            if not client_path or not os.path.exists(client_path):
                self.log(f"Invalid or non-existent path: {client_path}", "ERROR")
                self.auth_status.configure(text="❌ Invalid Client Path", text_color="#e74c3c")
                return
            
            token = self.read_leveldb_token(client_path)
            
            if token:
                if self.validate_jwt_token(token):
                    self.access_token = token
                    self.log(f"Token retrieved and validated successfully!", "SUCCESS")
                    self.auth_status.configure(text=f"✅ Token Retrieved!", text_color="#27ae60")
                    self.after(1000, self.switch_to_queue_tab)
                else:
                    self.log("Token retrieved but invalid", "ERROR")
                    self.auth_status.configure(text="❌ Invalid Token", text_color="#e74c3c")
            else:
                self.log("Token not found in client files", "ERROR")
                self.auth_status.configure(text="❌ Token Not Found", text_color="#e74c3c")
                
        except Exception as e:
            self.log(f"Error retrieving token: {str(e)}", "ERROR")
            self.auth_status.configure(text=f"❌ Error: {str(e)}", text_color="#e74c3c")
    
    def read_leveldb_token(self, path):
        """Reads the token from LevelDB files"""
        try:
            self.log(f"Reading files in: {path}")
            files = os.listdir(path)
            self.log(f"Number of files found: {len(files)}")
            
            jwt_pattern = re.compile(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+')
            
            for filename in files:
                if filename.endswith('.log') or filename.endswith('.ldb'):
                    filepath = os.path.join(path, filename)
                    self.log(f"Analyzing file: {filename}")
                    try:
                        with open(filepath, 'rb') as f:
                            content = f.read()
                            content_str = content.decode('utf-8', errors='ignore')
                            
                            if '__FRVR_auth_access_token' in content_str:
                                self.log(f"Key '__FRVR_auth_access_token' found in {filename}")
                                
                                tokens = jwt_pattern.findall(content_str)
                                
                                if tokens:
                                    self.log(f"{len(tokens)} JWT token(s) found")
                                    token = tokens[-1]
                                    self.log(f"Extracted token: {token[:50]}...{token[-50:]}")
                                    return token
                    except Exception as e:
                        self.log(f"Error reading {filename}: {str(e)}", "WARNING")
                        continue
            
            self.log("No token found in files", "WARNING")
            return None
        except Exception as e:
            self.log(f"Error reading LevelDB: {str(e)}", "ERROR")
            return None
    
    def login_with_credentials(self):
        """Login with username and password"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        self.log(f"Login attempt for user: {username}")
        
        if not username or not password:
            self.log("Empty username or password fields", "WARNING")
            self.auth_status.configure(text="❌ Fill All Fields", text_color="#e74c3c")
            return
        
        try:
            headers = {
                'authority': 'gapi.svc.krunker.io',
                'accept': 'application/json',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.0 Electron/12.0.0-nightly.20201116 Safari/537.36',
                'content-type': 'application/json',
                'origin': 'https://krunker.io',
                'referer': 'https://krunker.io/'
            }
            
            data = {"username": username, "password": password}
            
            self.log("Sending login request to API...")
            
            response = requests.post('https://gapi.svc.krunker.io/auth/login/username',
                                    headers=headers, json=data)
            
            self.log(f"HTTP status code: {response.status_code}")
            result = response.json()
            
            if result.get('data', {}).get('type') == 'login_ok':
                token = result['data']['access_token']
                if self.validate_jwt_token(token):
                    self.access_token = token
                    self.log("Login successful and token validated!", "SUCCESS")
                    self.auth_status.configure(text="✅ Login Successful!", text_color="#27ae60")
                    self.after(1000, self.switch_to_queue_tab)
                else:
                    self.log("Token received but invalid", "ERROR")
                    self.auth_status.configure(text="❌ Invalid Token", text_color="#e74c3c")
                
            elif result.get('data', {}).get('type') == 'check_2fa':
                challenge_id = result['data']['challenge_id']
                self.log(f"2FA required. Challenge ID: {challenge_id}", "INFO")
                self.handle_2fa(challenge_id)
                
            else:
                self.log(f"Unexpected response: {result}", "ERROR")
                self.auth_status.configure(text=f"❌ Login Failed", text_color="#e74c3c")
                
        except Exception as e:
            self.log(f"Login error: {str(e)}", "ERROR")
            self.auth_status.configure(text=f"❌ Error: {str(e)}", text_color="#e74c3c")
    
    def handle_2fa(self, challenge_id):
        """Handles 2FA authentication"""
        self.auth_status.configure(text="🔐 2FA Required - Enter Code", text_color="#f39c12")
        self.challenge_id = challenge_id
        
        def submit_2fa():
            code = self.twofa_entry.get()
            self.log(f"Submitting 2FA code: {code}")
            
            if not code:
                self.log("Empty 2FA code", "WARNING")
                self.auth_status.configure(text="❌ Enter 2FA Code", text_color="#e74c3c")
                return
            
            try:
                headers = {
                    'authority': 'gapi.svc.krunker.io',
                    'accept': 'application/json',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'content-type': 'application/json',
                    'origin': 'https://krunker.io'
                }
                
                data = {"code": code}
                url = f'https://gapi.svc.krunker.io/auth/2fa/challenge/{challenge_id}'
                
                response = requests.post(url, headers=headers, json=data)
                result = response.json()
                
                if result.get('data', {}).get('type') == 'login_ok':
                    token = result['data']['access_token']
                    if self.validate_jwt_token(token):
                        self.access_token = token
                        self.log("2FA login successful and token validated!", "SUCCESS")
                        self.auth_status.configure(text="✅ 2FA Login Successful!", text_color="#27ae60")
                        self.after(1000, self.switch_to_queue_tab)
                    else:
                        self.log("2FA token received but invalid", "ERROR")
                        self.auth_status.configure(text="❌ Invalid Token", text_color="#e74c3c")
                else:
                    self.log(f"Incorrect 2FA code: {result}", "ERROR")
                    self.auth_status.configure(text="❌ Wrong 2FA Code", text_color="#e74c3c")
                    
            except Exception as e:
                self.log(f"2FA verification error: {str(e)}", "ERROR")
                self.auth_status.configure(text=f"❌ 2FA Error: {str(e)}", text_color="#e74c3c")
        
        self.twofa_entry.bind('<Return>', lambda e: submit_2fa())
    
    def add_custom_client(self):
        """Adds a custom client"""
        name = self.new_client_name.get()
        path = self.new_client_path.get()
        
        self.log(f"Adding custom client: {name} -> {path}")
        
        if name and path:
            self.custom_clients[name] = path
            self.client_combo.configure(values=list(self.custom_clients.keys()))
            self.update_clients_list()
            self.new_client_name.delete(0, 'end')
            self.new_client_path.delete(0, 'end')
            self.log(f"Client '{name}' added successfully", "SUCCESS")
        else:
            self.log("Empty client name or path", "WARNING")
    
    def update_clients_list(self):
        """Updates the client list"""
        self.clients_list.delete("1.0", "end")
        for name, path in self.custom_clients.items():
            self.clients_list.insert("end", f"📁 {name}:\n   {path}\n\n")
    
    def start_queue(self):
        """Starts the queue"""
        self.log("=== STARTING QUEUE ===")
        
        if not self.access_token:
            self.log("No access token available", "ERROR")
            self.queue_status_label.configure(text="❌ Please Authenticate First!", text_color="#e74c3c")
            return
        
        if not self.validate_jwt_token(self.access_token):
            self.log("Current token is invalid", "ERROR")
            self.queue_status_label.configure(text="❌ Invalid Token!", text_color="#e74c3c")
            return
        
        selected_regions = [code for code, var in self.regions.items() if var.get()]
        self.log(f"Selected regions: {selected_regions}")
        
        if not selected_regions:
            self.log("No region selected", "ERROR")
            self.queue_status_label.configure(text="❌ Select At Least One Region!", text_color="#e74c3c")
            return
        
        selected_maps = [code for code, var in self.maps.items() if var.get()]
        self.log(f"Selected maps: {selected_maps}")
        
        if not selected_maps:
            self.log("No map selected", "ERROR")
            self.queue_status_label.configure(text="❌ Select At Least One Map!", text_color="#e74c3c")
            return
        
        regions_str = ','.join(selected_regions)
        maps_str = ','.join(selected_maps)
        
        ws_url = f"wss://gamefrontend.svc.krunker.io/v1/matchmaking/queue?token={self.access_token}&maps={maps_str}&regions={regions_str}"
        
        self.log("=== WEBSOCKET URL ===")
        self.log(f"Full URL: {ws_url}")
        self.log("=====================")
        
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        
        self.ws_thread = threading.Thread(target=self.connect_websocket, args=(ws_url,), daemon=True)
        self.ws_thread.start()
    
    def connect_websocket(self, url):
        """WebSocket connection"""
        self.log("Initializing WebSocket connection...")
        
        def on_message(ws, message):
            self.log(f"[WS] Message received: {message}", "WS_MESSAGE")
            try:
                data = json.loads(message)
                
                if data.get('type') == 'QUEUE_STATUS':
                    status = data.get('payload', {}).get('status')
                    self.log(f"[WS] Queue status: {status}", "WS_STATUS")
                    
                    if status == 'QUEUED':
                        self.log("[WS] Waiting for match...", "WS_STATUS")
                        self.queue_status_label.configure(text="🔄 Searching for Match...", text_color="#f39c12")
                        if not self.timer_running:
                            self.start_timer()
                    
                    elif status == 'MATCHED':
                        playsound("https://files.catbox.moe/qprgrz.mp3")
                        assignment = data.get('payload', {}).get('assignment', {})
                        map_name = assignment.get('extensions', {}).get('map', 'Unknown')
                        region = assignment.get('extensions', {}).get('region', 'Unknown')
                        connection = assignment.get('connection', 'Unknown')
                        
                        self.log(f"[WS] 🎉 MATCH FOUND! 🎉", "SUCCESS")
                        self.log(f"[WS] Map: {map_name}", "SUCCESS")
                        self.log(f"[WS] Region: {region}", "SUCCESS")
                        self.log(f"[WS] Server: {connection}", "SUCCESS")
                        
                        self.queue_status_label.configure(
                            text=f"✅ Match Found! {map_name} | {region}",
                            text_color="#27ae60"
                        )
                        self.stop_timer()
                        ws.close()
                        self.after(5000, self.reset_queue_ui)
                        
            except json.JSONDecodeError as e:
                self.log(f"[WS] JSON parsing error: {str(e)}", "ERROR")
            except Exception as e:
                self.log(f"[WS] Error in on_message: {str(e)}", "ERROR")
        
        def on_error(ws, error):
            self.log(f"[WS] ❌ WebSocket ERROR: {error}", "ERROR")
            self.queue_status_label.configure(text=f"❌ Error: {error}", text_color="#e74c3c")
            self.stop_timer()
        
        def on_close(ws, close_status_code, close_msg):
            self.log(f"[WS] Connection closed", "INFO")
            if self.timer_running:
                self.queue_status_label.configure(text="⚠️ Disconnected", text_color="#f39c12")
        
        def on_open(ws):
            self.log(f"[WS] ✅ WebSocket connection established!", "SUCCESS")
            self.queue_status_label.configure(text="🔗 Connected...", text_color="#3498db")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.0 Electron/12.0.0-nightly.20201116 Safari/537.36',
            'Origin': 'https://krunker.io'
        }
        
        self.ws = websocket.WebSocketApp(url,
                                         header=headers,
                                         on_message=on_message,
                                         on_error=on_error,
                                         on_close=on_close,
                                         on_open=on_open)
        
        try:
            self.ws.run_forever()
        except Exception as e:
            self.log(f"[WS] Exception: {str(e)}", "ERROR")
    
    def stop_queue(self):
        """Stops the queue"""
        self.log("Queue stop requested")
        if self.ws:
            self.ws.close()
        self.stop_timer()
        self.reset_queue_ui()
    
    def reset_queue_ui(self):
        """Resets the queue interface"""
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.queue_status_label.configure(text="Not Connected", text_color="white")
    
    def start_timer(self):
        """Starts the timer"""
        self.log("Timer started")
        self.timer_running = True
        self.elapsed_time = 0
        self.timer_thread = threading.Thread(target=self.update_timer, daemon=True)
        self.timer_thread.start()
    
    def stop_timer(self):
        """Stops the timer"""
        self.log(f"Timer stopped (elapsed time: {self.elapsed_time}s)")
        self.timer_running = False
        self.elapsed_time = 0
        self.timer_label.configure(text="00:00")
    
    def update_timer(self):
        """Updates the timer"""
        while self.timer_running:
            time.sleep(1)
            self.elapsed_time += 1
            minutes = self.elapsed_time // 60
            seconds = self.elapsed_time % 60
            time_str = f"{minutes:02d}:{seconds:02d}"
            self.timer_label.configure(text=time_str)
    
    def on_closing(self):
        """Handles application closing"""
        self.log("Closing application...")
        if self.ws:
            self.ws.close()
        self.stop_timer()
        self.destroy()

if __name__ == "__main__":
    print("="*60)
    print("KRUNKER.IO QUEUE MANAGER - DEBUG CONSOLE")
    print("="*60)
    print()
    
    app = KrunkerQueueApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
