import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from src.admin import get_all_users, get_all_transactions, get_user_accounts, get_transactions_with_user_details, block_unblock_account
from src.models import User, Transaction
from src.database import get_db_connection

class AdminDashboard(ttk.Frame):
    def __init__(self, parent, user: User, on_logout):
        super().__init__(parent, padding=(20, 10))
        self.user = user
        self.on_logout = on_logout
        self.setup_ui()
    
    def setup_ui(self):
        self.header = ttk.Frame(self)
        self.header.pack(fill=X, pady=10)
        
        ttk.Label(
            self.header,
            text=f"Admin Dashboard - {self.user.username}",
            font=('Helvetica', 16),
            bootstyle=PRIMARY
        ).pack(side=LEFT)
        
        ttk.Button(
            self.header,
            text="Logout",
            command=self.on_logout,
            bootstyle=DANGER,
            width=10
        ).pack(side=RIGHT)
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=True, pady=10)
        
        self.users_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.users_tab, text="Users")
        self.setup_users_tab()
        
        self.transactions_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.transactions_tab, text="Transactions")
        self.setup_transactions_tab()
    
    def setup_users_tab(self):
        users = get_all_users()
        
        columns = ('id', 'username', 'role', 'full_name', 'email', 'created_at')
        self.users_tree = ttk.Treeview(
            self.users_tab, 
            columns=columns, 
            show='headings',
            bootstyle=PRIMARY
        )
        
        self.users_tree.heading('id', text='ID')
        self.users_tree.heading('username', text='Username')
        self.users_tree.heading('role', text='Role')
        self.users_tree.heading('full_name', text='Full Name')
        self.users_tree.heading('email', text='Email')
        self.users_tree.heading('created_at', text='Created At')
        
        self.users_tree.column('id', width=50, anchor=CENTER)
        self.users_tree.column('username', width=100, anchor=W)
        self.users_tree.column('role', width=80, anchor=CENTER)
        self.users_tree.column('full_name', width=150, anchor=W)
        self.users_tree.column('email', width=150, anchor=W)
        self.users_tree.column('created_at', width=120, anchor=W)
        
        for user in users:
            self.users_tree.insert('', END, values=(
                user.id,
                user.username,
                user.role,
                user.full_name or "",
                user.email or "",
                user.created_at
            ))
        
        self.users_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        btn_frame = ttk.Frame(self.users_tab)
        btn_frame.pack(fill=X, padx=10, pady=5)
        
        ttk.Button(
            btn_frame,
            text="View Accounts",
            command=self.view_user_accounts,
            bootstyle=INFO,
            width=15
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Refresh",
            command=self.refresh_users,
            bootstyle=SECONDARY,
            width=15
        ).pack(side=RIGHT, padx=5)
    
    def setup_transactions_tab(self):
        transactions = get_all_transactions(limit=50)
        
        columns = ('id', 'account_id', 'type', 'amount', 'status', 'created_at')
        self.txn_tree = ttk.Treeview(
            self.transactions_tab, 
            columns=columns, 
            show='headings',
            bootstyle=PRIMARY
        )
        
        self.txn_tree.heading('id', text='ID')
        self.txn_tree.heading('account_id', text='Account ID')
        self.txn_tree.heading('type', text='Type')
        self.txn_tree.heading('amount', text='Amount')
        self.txn_tree.heading('status', text='Status')
        self.txn_tree.heading('created_at', text='Date')
        
        self.txn_tree.column('id', width=50, anchor=CENTER)
        self.txn_tree.column('account_id', width=80, anchor=CENTER)
        self.txn_tree.column('type', width=100, anchor=CENTER)
        self.txn_tree.column('amount', width=100, anchor=E)
        self.txn_tree.column('status', width=100, anchor=CENTER)
        self.txn_tree.column('created_at', width=150, anchor=W)
        
        for txn in transactions:
            self.txn_tree.insert('', END, values=(
                txn.id,
                txn.account_id,
                txn.type.capitalize(),
                f"₹{txn.amount:,.2f}",
                txn.status.capitalize(),
                txn.created_at
            ))
        
        self.txn_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Bind double-click to show transaction details with user info
        self.txn_tree.bind('<Double-1>', self.show_transaction_details)
        
        ttk.Button(
            self.transactions_tab,
            text="Refresh",
            command=self.refresh_transactions,
            bootstyle=SECONDARY,
            width=15
        ).pack(pady=5)
    
    def show_transaction_details(self, event):
        selected = self.txn_tree.focus()
        if not selected:
            return
        
        txn_data = self.txn_tree.item(selected)['values']
        txn_id = txn_data[0]
        
        # Fetch transaction with user details
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT t.id, t.account_id, t.type, t.amount, t.description, t.status, t.created_at,
                       u.username, u.full_name
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                JOIN users u ON a.user_id = u.id
                WHERE t.id = ?
                """,
                (txn_id,)
            )
            result = cursor.fetchone()
        
        if not result:
            messagebox.showerror("Error", "Transaction details not found")
            return
        
        # Create pop-up window
        win = ttk.Toplevel(self)
        win.title(f"Transaction ID: {txn_id}")
        win.geometry("400x300")
        
        ttk.Label(win, text="Transaction Details", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        details = [
            ("ID", result["id"]),
            ("Account ID", result["account_id"]),
            ("Username", result["username"]),
            ("Full Name", result["full_name"] or "N/A"),
            ("Type", result["type"].capitalize()),
            ("Amount", f"₹{result['amount']:,.2f}"),
            ("Status", result["status"].capitalize()),
            ("Date", result["created_at"]),
            ("Description", result["description"] or "N/A")
        ]
        
        for label, value in details:
            frame = ttk.Frame(win)
            frame.pack(fill=X, padx=10, pady=5)
            ttk.Label(frame, text=f"{label}:", font=('Helvetica', 10, 'bold'), width=15).pack(side=LEFT)
            ttk.Label(frame, text=value, font=('Helvetica', 10)).pack(side=LEFT)
        
        ttk.Button(win, text="Close", command=win.destroy, bootstyle=SECONDARY).pack(pady=10)
    
    def view_user_accounts(self):
        selected = self.users_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select a user first")
            return
        
        user_data = self.users_tree.item(selected)['values']
        user_id = user_data[0]
        accounts = get_user_accounts(user_id)
        
        win = ttk.Toplevel(self)
        win.title(f"Accounts for User ID: {user_id}")
        win.geometry("600x300")
        
        if not accounts:
            ttk.Label(win, text="No accounts found for this user").pack(pady=20)
            return
        
        columns = ('id', 'account_number', 'balance', 'account_type', 'is_blocked')
        tree = ttk.Treeview(
            win, 
            columns=columns, 
            show='headings',
            bootstyle=PRIMARY
        )
        
        tree.heading('id', text='ID')
        tree.heading('account_number', text='Account Number')
        tree.heading('balance', text='Balance')
        tree.heading('account_type', text='Type')
        tree.heading('is_blocked', text='Blocked')
        
        tree.column('id', width=50, anchor=CENTER)
        tree.column('account_number', width=150, anchor=W)
        tree.column('balance', width=100, anchor=E)
        tree.column('account_type', width=100, anchor=CENTER)
        tree.column('is_blocked', width=80, anchor=CENTER)
        
        for acc in accounts:
            tree.insert('', END, values=(
                acc.id,
                acc.account_number,
                f"₹{acc.balance:,.2f}",
                acc.account_type.capitalize(),
                "Yes" if acc.is_blocked else "No"
            ))
        
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill=X, padx=10, pady=5)
        
        ttk.Button(
            btn_frame,
            text="Block/Unblock Account",
            command=lambda: self.toggle_block_account(tree, user_id, win),
            bootstyle=WARNING,
            width=20
        ).pack(side=LEFT, padx=5)
    
    def toggle_block_account(self, tree, user_id, window):
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select an account first")
            return
        
        account_data = tree.item(selected)['values']
        account_id = account_data[0]
        current_status = account_data[4]  # "Yes" or "No"
        block = current_status == "No"  # Block if not blocked, unblock if blocked
        
        success = block_unblock_account(account_id, block)
        if success:
            messagebox.showinfo("Success", f"Account {'blocked' if block else 'unblocked'} successfully")
            # Refresh the accounts list
            for item in tree.get_children():
                tree.delete(item)
            accounts = get_user_accounts(user_id)
            for acc in accounts:
                tree.insert('', END, values=(
                    acc.id,
                    acc.account_number,
                    f"₹{acc.balance:,.2f}",
                    acc.account_type.capitalize(),
                    "Yes" if acc.is_blocked else "No"
                ))
        else:
            messagebox.showerror("Error", f"Failed to {'block' if block else 'unblock'} account")
    
    def refresh_users(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        users = get_all_users()
        for user in users:
            self.users_tree.insert('', END, values=(
                user.id,
                user.username,
                user.role,
                user.full_name or "",
                user.email or "",
                user.created_at
            ))
    
    def refresh_transactions(self):
        for item in self.txn_tree.get_children():
            self.txn_tree.delete(item)
        
        transactions = get_all_transactions(limit=50)
        for txn in transactions:
            self.txn_tree.insert('', END, values=(
                txn.id,
                txn.account_id,
                txn.type.capitalize(),
                f"₹{txn.amount:,.2f}",
                txn.status.capitalize(),
                txn.created_at
            ))