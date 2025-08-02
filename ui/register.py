import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import re
from src.auth import register_user

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

class RegisterFrame(FormFrame):
    def __init__(self, parent, on_back_to_login, on_register_success):
        super().__init__(parent, padding=(20, 20), bootstyle="light")
        self.on_back_to_login = on_back_to_login
        self.on_register_success = on_register_success
        self.setup_ui()

    def setup_ui(self):
        ttk.Label(
            self.form_frame,
            text="Create New Account",
            font=('Helvetica', 20, 'bold'),
            foreground="#191970"
        ).pack(pady=(0, 20))

        fields = [
            ("Username", "username_entry", False, "Enter your username"),
            ("Password", "password_entry", True, "Enter your password"),
            ("Confirm Password", "confirm_password_entry", True, "Confirm your password"),
            ("Full Name", "full_name_entry", False, "Enter your full name"),
            ("Email", "email_entry", False, "Enter your email")
        ]

        for label_text, var_name, is_password, placeholder in fields:
            entry = self.create_labeled_entry(self.form_frame, label_text, placeholder, is_password)
            setattr(self, var_name, entry)

        self.btn_frame = ttk.Frame(self.form_frame)
        self.btn_frame.pack(pady=20, fill=X)

        self.style.configure("Custom.TButton", font=("Helvetica", 12), padding=10)

        self.back_btn = ttk.Button(
            self.btn_frame,
            text="Back",
            command=self.on_back_to_login,
            style="Custom.TButton",
            width=8
        )
        self.back_btn.pack(side=LEFT, padx=5)

        self.register_btn = ttk.Button(
            self.btn_frame,
            text="Register",
            command=self.handle_register,
            style="Custom.TButton",
            width=12
        )
        self.register_btn.pack(side=RIGHT, padx=5)

    def validate_email(self, email):
        return bool(email and re.match(r"[^@]+@[^@]+\.[^@]+", email))

    def validate_password(self, password):
        return bool(password and len(password) >= 8 and any(c.isupper() for c in password))

    def validate_username(self, username):
        return bool(username and re.match(r"^[a-zA-Z0-9_]+$", username))

    def handle_register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        full_name = self.full_name_entry.get()
        email = self.email_entry.get()

        if any(entry.get() == entry.placeholder for entry in [
            self.username_entry, self.password_entry, self.confirm_password_entry,
            self.full_name_entry, self.email_entry]):
            messagebox.showerror("Error", "Please fill in all fields")
            return
        
        if not self.validate_username(username):
            messagebox.showerror("Error", "Username can only contain letters, numbers, and underscores")
            return
        if not self.validate_password(password):
            messagebox.showerror("Error", "Password must be at least 8 characters with an uppercase letter")
            return
        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            return
        if not self.validate_email(email):
            messagebox.showerror("Error", "Please enter a valid email address")
            return
        if len(full_name.strip()) < 2:
            messagebox.showerror("Error", "Please enter a valid full name")
            return

        try:
            user = register_user(username, password, full_name, email)
            if user:
                messagebox.showinfo("Success", f"Welcome, {full_name}! Your account has been created.")
                self.on_register_success(user)
            else:
                messagebox.showerror("Error", "Username or email already exists")
        except Exception as e:
            messagebox.showerror("Error", f"Registration failed: {str(e)}")