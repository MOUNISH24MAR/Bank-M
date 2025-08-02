import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from src.database import initialize_database
from ui.login import LoginFrame
from ui.register import RegisterFrame
from ui.dashboard import UserDashboard
from ui.admin import AdminDashboard

class BankApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="litera")
        self.title("RRM Bank - Secure Banking")
        self.attributes('-fullscreen', True)
        initialize_database()
        self.update_idletasks()
        
        self.container = ttk.Frame(self, bootstyle="light")
        self.container.place(relx=0.5, rely=0.5, anchor=CENTER, relwidth=1.0, relheight=1.0)
        
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=2)
        self.container.grid_rowconfigure(0, weight=1)
        
        self.left_frame = ttk.Frame(self.container, bootstyle="light")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)
        
        self.content_frame = ttk.Frame(self.container, bootstyle="light")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        ttk.Label(
            self.left_frame,
            text="RRM Bank",
            font=("Helvetica", 40, "bold"),
            foreground="#191970"
        ).grid(row=0, column=0, pady=20, sticky="s")
        
        self.new_quote_frame = ttk.Frame(self.left_frame)
        self.new_quote_frame.grid(row=1, column=0, pady=10, sticky="n")
        
        new_quote = "“MAKE A TRUST AND BE COMMIT”"
        ttk.Label(
            self.new_quote_frame,
            text=new_quote,
            font=("Helvetica", 14, "italic"),
            foreground="gray"
        ).pack()
        
        self.quotes_frame = ttk.Frame(self.left_frame)
        self.quotes_frame.grid(row=2, column=0, pady=10, sticky="n")
        
        quote = "“Bank with trust, grow with us.”"
        ttk.Label(
            self.quotes_frame,
            text=quote,
            font=("Helvetica", 14, "italic"),
            foreground="gray"
        ).pack()
        
        self.features_frame = ttk.Frame(self.left_frame)
        self.features_frame.grid(row=3, column=0, pady=10, sticky="n")
        
        features = [
            "🔒 Unbreakable Security",
            "💰 Guaranteed Safety",
            "✅ Proven Reliability"
        ]
        for feature in features:
            ttk.Label(
                self.features_frame,
                text=feature,
                font=("Helvetica", 16),
                foreground="gray"
            ).pack(pady=8)
        
        self.show_login()
    
    def show_login(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.login_frame = LoginFrame(
            self.content_frame,
            on_login_success=self.handle_login_success,
            on_register_click=self.show_register
        )
        self.login_frame.pack(expand=True, fill=BOTH)
    
    def show_register(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        self.register_frame = RegisterFrame(
            self.content_frame,
            on_back_to_login=self.show_login,
            on_register_success=self.handle_login_success
        )
        self.register_frame.pack(expand=True, fill=BOTH)
    
    def handle_login_success(self, user):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if user.role == "admin":
            self.dashboard = AdminDashboard(self.content_frame, user, on_logout=self.show_login)
        else:
            self.dashboard = UserDashboard(self.content_frame, user, on_logout=self.show_login)
        
        self.dashboard.pack(expand=True, fill=BOTH)

if __name__ == "__main__":
    app = BankApp()
    app.mainloop()