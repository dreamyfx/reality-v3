import customtkinter as ctk
from tkinter import messagebox
import uuid
import time
from datetime import datetime, timedelta
import requests
from firebase_config import FIREBASE_CONFIG

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DATABASE_URL = FIREBASE_CONFIG['databaseURL']

class AdminPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("reality 3 database")
        self.root.geometry("1000x700")
        
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        self.header = ctk.CTkLabel(root, text="RealityV3users", 
                                 font=ctk.CTkFont(size=24, weight="bold"))
        self.header.grid(row=0, column=0, padx=20, pady=20)
        
        main_container = ctk.CTkFrame(root)
        main_container.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)
        
        add_frame = ctk.CTkFrame(main_container)
        add_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        add_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(add_frame, text="User ID:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.user_id_var = ctk.StringVar(value=self.generate_user_id())
        self.user_id_entry = ctk.CTkEntry(add_frame, textvariable=self.user_id_var, width=400)
        self.user_id_entry.grid(row=0, column=1, padx=10, pady=5, sticky='ew')
        
        ctk.CTkLabel(add_frame, text="Telegram Chat ID:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.tg_chat_id = ctk.CTkEntry(add_frame, width=400)
        self.tg_chat_id.grid(row=1, column=1, padx=10, pady=5, sticky='ew')
        
        ctk.CTkLabel(add_frame, text="Telegram Bot Token:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.tg_bot_token = ctk.CTkEntry(add_frame, width=400)
        self.tg_bot_token.grid(row=2, column=1, padx=10, pady=5, sticky='ew')
        
        ctk.CTkLabel(add_frame, text="Discord Webhook:").grid(row=3, column=0, sticky='w', padx=10, pady=5)
        self.dc_webhook = ctk.CTkEntry(add_frame, width=400)
        self.dc_webhook.grid(row=3, column=1, padx=10, pady=5, sticky='ew')
        
        ctk.CTkLabel(add_frame, text="Subscription Days:").grid(row=4, column=0, sticky='w', padx=10, pady=5)
        self.days_var = ctk.IntVar(value=30)
        
        spinbox_frame = ctk.CTkFrame(add_frame, fg_color="transparent")
        spinbox_frame.grid(row=4, column=1, padx=10, pady=5, sticky='w')
        
        import tkinter as tk
        self.days_spinbox = tk.Spinbox(spinbox_frame, from_=1, to=365, textvariable=self.days_var, width=10, 
                                      bg='#2b2b2b', fg='white', buttonbackground='#3b3b3b', 
                                      highlightthickness=0, relief='flat')
        self.days_spinbox.pack()
        
        ctk.CTkLabel(add_frame, text="Expires (Unix):").grid(row=5, column=0, sticky='w', padx=10, pady=5)
        self.expire_label = ctk.CTkLabel(add_frame, text="", font=ctk.CTkFont(family="Courier", size=10))
        self.expire_label.grid(row=5, column=1, padx=10, pady=5, sticky='w')
        
        self.days_var.trace('w', self.update_expiration)
        self.update_expiration()
        
        self.add_user_btn = ctk.CTkButton(add_frame, text="Add User", command=self.add_user,
                                        height=40, font=ctk.CTkFont(size=16, weight="bold"))
        self.add_user_btn.grid(row=6, column=0, columnspan=2, padx=10, pady=20)
        
        list_frame = ctk.CTkFrame(main_container)
        list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        
        tree_frame = ctk.CTkFrame(list_frame)
        tree_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        import tkinter as tk
        from tkinter import ttk
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', background='#2b2b2b', foreground='white', fieldbackground='#2b2b2b')
        style.configure('Treeview.Heading', background='#3b3b3b', foreground='white')
        
        columns = ('User ID', 'TG Chat ID', 'Expires', 'Status')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
        
        self.tree.heading('User ID', text='User ID')
        self.tree.heading('TG Chat ID', text='TG Chat ID')
        self.tree.heading('Expires', text='Expires')
        self.tree.heading('Status', text='Status')
        
        self.tree.column('User ID', width=350)
        self.tree.column('TG Chat ID', width=150)
        self.tree.column('Expires', width=150)
        self.tree.column('Status', width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        btn_frame = ctk.CTkFrame(list_frame)
        btn_frame.grid(row=1, column=0, padx=10, pady=10, sticky='ew')
        
        self.refresh_btn = ctk.CTkButton(btn_frame, text="🔄 Refresh", command=self.load_users,
                                        width=120, height=35)
        self.refresh_btn.pack(side='left', padx=10, pady=10)
        
        self.delete_btn = ctk.CTkButton(btn_frame, text="🗑️ Delete User", command=self.delete_user,
                                        width=120, height=35, fg_color="red", hover_color="darkred")
        self.delete_btn.pack(side='left', padx=10, pady=10)
        
        self.copy_btn = ctk.CTkButton(btn_frame, text="📋 Copy User ID", command=self.copy_user_id,
                                      width=120, height=35, fg_color="blue", hover_color="darkblue")
        self.copy_btn.pack(side='left', padx=10, pady=10)
        
        self.load_users()
    
    def generate_user_id(self):
        return str(uuid.uuid4())
    
    def update_expiration(self, *args):
        days = self.days_var.get()
        expire_time = int((datetime.now() + timedelta(days=days)).timestamp())
        expire_date = datetime.fromtimestamp(expire_time).strftime('%Y-%m-%d %H:%M:%S')
        self.expire_label.configure(text=f"{expire_time} ({expire_date})")
    
    def add_user(self):
        user_id = self.user_id_var.get()
        tg_chat = self.tg_chat_id.get().strip()
        tg_token = self.tg_bot_token.get().strip()
        webhook = self.dc_webhook.get().strip()
        days = self.days_var.get()
        
        if not tg_chat or not tg_token or not webhook:
            messagebox.showerror("Error", "All fields are required")
            return
        
        expire_time = int((datetime.now() + timedelta(days=days)).timestamp())
        
        try:
            url = f"{DATABASE_URL}/users/{user_id}.json"
            data = {
                'telegram_chat_id': tg_chat,
                'telegram_bot_token': tg_token,
                'discord_webhook': webhook,
                'expiration': expire_time,
                'created': int(time.time()),
                'active': True
            }
            
            response = requests.put(url, json=data)
            
            if response.status_code == 200:
                self.root.clipboard_clear()
                self.root.clipboard_append(user_id)
                
                messagebox.showinfo("Success", f"User added\n\nUser ID:\n{user_id}\n\nThe id has been added copied to your clipboard.")
                
                self.user_id_var.set(self.generate_user_id())
                self.tg_chat_id.delete(0, 'end')
                self.tg_bot_token.delete(0, 'end')
                self.dc_webhook.delete(0, 'end')
                
                self.load_users()
                self.show_notification("User added successfully!", "success")
            else:
                messagebox.showerror("Error", f"Failed to add user: {response.status_code}")
            
        except Exception as e:
            self.show_notification(f"Failed to add user: {e}", "error")
    
    def load_users(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            url = f"{DATABASE_URL}/users.json"
            print(f"Fetching from: {url}")  
            response = requests.get(url)
            
            print(f"Response status: {response.status_code}")  
            print(f"Response content: {response.text[:200]}...")  
            
            if response.status_code == 200:
                users = response.json()
                print(f"Users data: {users}")  
                
                if users:
                    current_time = int(time.time())
                    user_count = 0
                    
                    for user_id, data in users.items():
                        tg_chat = data.get('telegram_chat_id', 'N/A')
                        expiration = data.get('expiration', 0)
                        
                        if expiration > current_time:
                            status = "Active"
                            expire_str = datetime.fromtimestamp(expiration).strftime('%Y-%m-%d')
                        else:
                            status = "Expired"
                            expire_str = "EXPIRED"
                        
                        self.tree.insert('', 'end', values=(user_id, tg_chat, expire_str, status))
                        user_count += 1
                    
                    self.show_notification(f"Loaded {user_count} users", "info")
                else:
                    self.show_notification("No users found", "info")
            else:
                self.show_notification(f"HTTP Error: {response.status_code}", "error")
        
        except Exception as e:
            print(f"Exception in load_users: {e}")  
            self.show_notification(f"Failed to load users: {e}", "error")
    
    def delete_user(self):
        selected = self.tree.selection()
        if not selected:
            self.show_notification("Select a user to delete!", "warning")
            return
        
        user_id = self.tree.item(selected[0])['values'][0]
        
        if self.show_confirm_dialog(f"Delete user {user_id}?"):
            try:
                url = f"{DATABASE_URL}/users/{user_id}.json"
                response = requests.delete(url)
                
                if response.status_code == 200:
                    self.show_notification("User deleted successfully", "success")
                    self.load_users()
                else:
                    self.show_notification(f"Failed to delete: {response.status_code}", "error")
            except Exception as e:
                self.show_notification(f"Failed to delete user: {e}", "error")
    
    def copy_user_id(self):
        selected = self.tree.selection()
        if not selected:
            self.show_notification("Select a user first!", "warning")
            return
        
        user_id = self.tree.item(selected[0])['values'][0]
        self.root.clipboard_clear()
        self.root.clipboard_append(user_id)
        self.show_notification(f"User ID copied: {user_id[:20]}...", "success")

    def show_notification(self, message, notification_type="info"):
        notification = ctk.CTkLabel(self.root, text=message, 
                                   fg_color=("gray75", "gray25") if notification_type == "info" else 
                                           ("green", "darkgreen") if notification_type == "success" else
                                           ("red", "darkred") if notification_type == "error" else
                                           ("orange", "darkorange"),
                                   corner_radius=8)
        notification.place(relx=0.5, rely=0.05, anchor="center")
        self.root.after(3000, notification.destroy)
    
    def show_confirm_dialog(self, message):
        dialog = ctk.CTkInputDialog(text=message, title="Confirm")
        return dialog.get_input() is not None

if __name__ == "__main__":
    root = ctk.CTk()
    app = AdminPanel(root)
    root.mainloop()
