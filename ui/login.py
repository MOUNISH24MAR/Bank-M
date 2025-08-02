import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import re
from src.auth import authenticate_user
from src.database import get_db_connection

class FormFrame(ttk.Frame):
    def __init__(self, parent, padding=(20, 20), bootstyle="light"):
        super().__init__(parent, padding=padding, bootstyle=bootstyle)
        self.configure(style="Custom.TFrame")
        self.style = ttk.Style()
        self.style.configure("Custom.TFrame", relief="groove", borderwidth=2, background="#ffffff")
        self.main_frame = ttk.Frame(self, padding=10, bootstyle="light", width=400)
        self.main_frame.pack(expand=True, pady=20)
        self.form_frame = ttk.Frame(self.main_frame, padding=10, style="Custom.TFrame")
        self.form_frame.pack(padx=10, pady=10)

    def create_labeled_entry(self, parent, label_text, placeholder, is_password=False):
        frame = ttk.Frame(parent)
        frame.pack(fill=X, pady=10)
        label = ttk.Label(frame, text=label_text, font=("Helvetica", 12), foreground="#191970")
        label.pack(side=LEFT, padx=5)
        
        entry = ttk.Entry(frame, font=("Helvetica", 12), show="*" if is_password else "", width=25)
        entry.pack(side=RIGHT, padx=5, pady=5)
        
        entry.insert(0, placeholder)
        entry.config(foreground="grey")
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(foreground="black")
                if is_password:
                    entry.config(show="*")
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(foreground="grey")
                if is_password:
                    entry.config(show="")
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
        
        entry.placeholder = placeholder
        return entry

class LoginFrame(FormFrame):
    def __init__(self, parent, on_login_success, on_register_click):
        super().__init__(parent, padding=(20, 20), bootstyle="light")
        self.on_login_success = on_login_success
        self.on_register_click = on_register_click
        self.setup_ui()

    def setup_ui(self):
        title_label = ttk.Label(
            self.form_frame,
            text="Welcome to RRM Bank",
            font=('Helvetica', 20, 'bold'),
            foreground="#191970"
        )
        title_label.pack(pady=(0, 20))

        self.username_entry = self.create_labeled_entry(
            self.form_frame, "Username", "Enter your username"
        )
        self.password_entry = self.create_labeled_entry(
            self.form_frame, "Password", "Enter your password", is_password=True
        )
        
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus_set())
        self.password_entry.bind("<Return>", lambda e: self.handle_login())
        
        self.btn_frame = ttk.Frame(self.form_frame)
        self.btn_frame.pack(pady=20, fill=X)
        
        self.style.configure("Custom.TButton", font=("Helvetica", 12), padding=10)
        
        self.login_btn = ttk.Button(
            self.btn_frame,
            text="Sign In",
            command=self.handle_login,
            style="Custom.TButton",
            width=12
        )
        self.login_btn.pack(side=LEFT, padx=5)
        
        self.register_btn = ttk.Button(
            self.btn_frame,
            text="Create Account",
            command=self.on_register_click,
            bootstyle=(LINK, PRIMARY),
            width=15
        )
        self.register_btn.pack(side=RIGHT, padx=5)
        
        self.forgot_btn = ttk.Button(
            self.form_frame,
            text="Forgot Password?",
            command=lambda: messagebox.showinfo("Info", "Password recovery not available. Contact support."),
            bootstyle=(LINK, SECONDARY),
            width=15
        )
        self.forgot_btn.pack(pady=10)

    def validate_username(self, username):
        return bool(username and re.match(r"^[a-zA-Z0-9_]+$", username))

    def handle_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if username == self.username_entry.placeholder or not username.strip():
            messagebox.showerror("Error", "Please enter a valid username")
            return
        if password == self.password_entry.placeholder or not password:
            messagebox.showerror("Error", "Please enter a password")
            return
        if not self.validate_username(username):
            messagebox.showerror("Error", "Username can only contain letters, numbers, and underscores")
            return
        
        try:
            user = authenticate_user(username, password)
            if user:
                # Check if any of the user's accounts are blocked
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT is_blocked FROM accounts WHERE user_id = ?",
                        (user.id,)
                    )
                    accounts = cursor.fetchall()

                # If any account is blocked, show a message and prevent login
                if any(account["is_blocked"] == 1 for account in accounts):
                    messagebox.showerror("Account Blocked", "Your account is blocked. Please contact the admin.")
                    return

                # Proceed to dashboard if no accounts are blocked
                self.on_login_success(user)
            else:
                messagebox.showerror("Error", "Incorrect username or password")
        except Exception as e:
            messagebox.showerror("Error", f"Login failed: {str(e)}")