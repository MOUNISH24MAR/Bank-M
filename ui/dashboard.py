import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from decimal import Decimal
from typing import Optional
from src.database import get_db_connection
from src.models import Account
from src.transactions import deposit, withdraw, get_account_transactions, get_account_balance, lock_funds, unlock_funds, get_locked_funds, transfer_funds
from datetime import datetime

class UserDashboard(ttk.Frame):
    def __init__(self, parent, user, on_logout):
        super().__init__(parent)
        self.user = user
        self.on_logout = on_logout
        self.account = self._get_user_account()
        self.setup_ui()
    
    def _get_user_account(self) -> Account:
        """Get the user's primary account"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, user_id, account_number, balance, account_type FROM accounts WHERE user_id = ?",
                (self.user.id,)
            )
            account_data = cursor.fetchone()
            if account_data:
                return Account(**account_data)
            messagebox.showerror("Error", "No account found. Please contact support.")
            self.on_logout()
            raise ValueError("No account found for user")
    
    def setup_ui(self):
        """Set up the UI"""
        self.pack(expand=True, fill=BOTH, padx=30, pady=30)
        
        self.container = ttk.Frame(self, bootstyle="light")
        self.container.place(relx=0.5, rely=0.5, anchor=CENTER, relwidth=0.9, relheight=0.9)
        
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure((0, 1, 2, 3), weight=1)
        
        # Header
        self.header = ttk.Frame(self.container)
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 30))
        
        ttk.Label(
            self.header,
            text=f"Welcome, {self.user.full_name or self.user.username}",
            font=('Helvetica', 24, 'bold'),
            foreground="#191970"
        ).pack(side=LEFT)
        
        logout_btn = ttk.Button(
            self.header,
            text="Logout",
            command=self.on_logout,
            bootstyle=DANGER,
            width=12,
            style="Custom.TButton"
        )
        logout_btn.pack(side=RIGHT)
        
        # Account info
        self.account_frame = ttk.Labelframe(
            self.container,
            text="Account Information",
            padding=20,
            style="Custom.TLabelframe"
        )
        self.account_frame.grid(row=1, column=0, sticky="ew", padx=150, pady=20)
        
        ttk.Label(
            self.account_frame,
            text=f"Account Number: {self.account.account_number}",
            font=('Helvetica', 16)
        ).pack(anchor="w", pady=8)
        
        self.balance_label = ttk.Label(
            self.account_frame,
            text=f"Balance: ₹{self.account.balance:,.2f}",
            font=('Helvetica', 18, 'bold'),
            foreground="#191970"
        )
        self.balance_label.pack(anchor="w", pady=8)
        
        # Actions
        self.actions_frame = ttk.Frame(self.container)
        self.actions_frame.grid(row=2, column=0, sticky="ew", pady=30)
        # Configure the actions_frame to wrap buttons if needed
        self.actions_frame.grid_columnconfigure(0, weight=1)
        
        # Create a subframe to wrap buttons
        self.button_wrapper = ttk.Frame(self.actions_frame)
        self.button_wrapper.pack(fill=X, expand=True)
        
        buttons = [
            ("Deposit", self.handle_deposit, SUCCESS),
            ("Withdraw", self.handle_withdraw, WARNING),
            ("Lock Funds", self.handle_lock_funds, PRIMARY),
            ("Unlock Funds", self.handle_unlock_funds, INFO),
            ("Pay", self.handle_pay, SUCCESS),  # Added Pay button
            ("Transactions", self.show_transactions, SECONDARY)
        ]
        
        # Pack buttons in a way that allows wrapping
        for i, (text, command, style) in enumerate(buttons):
            btn = ttk.Button(
                self.button_wrapper,
                text=text,
                command=command,
                bootstyle=style,
                width=15,
                style="Custom.TButton"
            )
            btn.grid(row=i//3, column=i%3, padx=10, pady=5, sticky="ew")
        
        # Custom styles
        style = ttk.Style()
        style.configure("Custom.TButton", font=("Helvetica", 14), padding=10)
        style.configure("Custom.TLabelframe", relief="groove", borderwidth=2)
        style.configure("Custom.TLabelframe.Label", font=("Helvetica", 16, "bold"), foreground="#191970")
    
    def handle_deposit(self):
        """Handle deposit action with custom dialog"""
        amount = self._get_amount("Deposit Amount", "Enter amount to deposit (e.g., 1000.00)")
        if not amount:
            return
        description = self._get_description("Deposit Description", "Enter description (optional)")
        success, message = deposit(self.account.id, amount, description)
        messagebox.showinfo("Success", message) if success else messagebox.showerror("Error", message)
        if success:
            self._refresh_balance()
    
    def handle_withdraw(self):
        """Handle withdrawal action with custom dialog"""
        amount = self._get_amount("Withdraw Amount", "Enter amount to withdraw (e.g., 1000.00)")
        if not amount:
            return
        current_balance = get_account_balance(self.account.id)
        if amount > current_balance:
            messagebox.showerror("Error", f"Insufficient funds. Available: ₹{current_balance:,.2f}")
            return
        description = self._get_description("Withdrawal Description", "Enter description (optional)")
        success, message = withdraw(self.account.id, amount, description)
        messagebox.showinfo("Success", message) if success else messagebox.showerror("Error", message)
        if success:
            self._refresh_balance()
    
    def handle_lock_funds(self):
        """Handle locking funds with confirmation"""
        amount = self._get_amount("Lock Funds", "Enter amount to lock (e.g., 1000.00)")
        if not amount:
            return
        current_balance = get_account_balance(self.account.id)
        if amount > current_balance:
            messagebox.showerror("Error", f"Insufficient funds. Available: ₹{current_balance:,.2f}")
            return
        pin = self._get_pin("Lock Funds PIN", "Enter a 4+ character PIN")
        if not pin:
            return
        description = self._get_description("Lock Description", "Enter description (optional)")
        if messagebox.askyesno("Confirm Lock", f"Lock ₹{amount:,.2f}? This amount will be unavailable until unlocked."):
            success, message = lock_funds(self.account.id, amount, pin, description)
            messagebox.showinfo("Success", message) if success else messagebox.showerror("Error", message)
            if success:
                self._refresh_balance()
    
    def handle_unlock_funds(self):
        """Handle unlocking funds with improved selection"""
        locked_funds = get_locked_funds(self.account.id)
        if not locked_funds:
            messagebox.showinfo("Info", "No locked funds available to unlock.")
            return
        
        win = ttk.Toplevel(self)
        win.title("Select Locked Funds")
        win.geometry("700x500")
        win.transient(self)
        win.grab_set()
        
        columns = ('id', 'amount', 'description', 'created_at')
        tree = ttk.Treeview(
            win,
            columns=columns,
            show='headings',
            bootstyle=PRIMARY
        )
        
        tree.heading('id', text='Lock ID')
        tree.heading('amount', text='Amount (₹)')
        tree.heading('description', text='Description')
        tree.heading('created_at', text='Locked On')
        
        tree.column('id', width=80, anchor=CENTER)
        tree.column('amount', width=120, anchor=E)
        tree.column('description', width=250, anchor=W)
        tree.column('created_at', width=150, anchor=W)
        
        for fund in locked_funds:
            created_at = datetime.strptime(fund['created_at'], "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M")
            tree.insert('', END, values=(
                fund['id'],
                f"{fund['amount']:,.2f}",
                fund['description'] or "No description",
                created_at
            ))
        
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame,
            text="Unlock Selected",
            command=lambda: self._process_unlock(tree, win),
            bootstyle=SUCCESS,
            style="Custom.TButton"
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancel",
            command=win.destroy,
            bootstyle=SECONDARY,
            style="Custom.TButton"
        ).pack(side=RIGHT, padx=5)
    
    def handle_pay(self):
        """Handle pay action to transfer money to another account"""
        # Prompt for recipient account number
        receiver_account_number = simpledialog.askstring(
            "Recipient Account",
            "Enter recipient's account number:",
            parent=self,
            initialvalue=""
        )
        if not receiver_account_number:
            return
        
        # Prompt for amount
        amount = self._get_amount("Pay Amount", "Enter amount to pay (e.g., 1000.00)")
        if not amount:
            return
        
        # Check balance
        current_balance = get_account_balance(self.account.id)
        if amount > current_balance:
            messagebox.showerror("Error", f"Insufficient funds. Available: ₹{current_balance:,.2f}")
            return
        
        # Prompt for description
        description = self._get_description("Pay Description", "Enter description (optional)")
        
        # Confirm the payment
        if messagebox.askyesno("Confirm Payment", f"Pay ₹{amount:,.2f} to account {receiver_account_number}?"):
            success, message = transfer_funds(self.account.id, receiver_account_number, amount, description)
            messagebox.showinfo("Success", message) if success else messagebox.showerror("Error", message)
            if success:
                self._refresh_balance()
    
    def _process_unlock(self, tree, win):
        """Process unlocking selected funds"""
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a locked fund to unlock.")
            return
        lock_id = int(tree.item(selected[0])['values'][0])
        locked_amount = Decimal(str(tree.item(selected[0])['values'][1]).replace(",", ""))
        
        amount_str = self._get_amount(
            "Unlock Amount",
            f"Enter amount to unlock (max ₹{locked_amount:,.2f})",
            max_value=locked_amount
        )
        if not amount_str:
            return
        
        pin = self._get_pin("Unlock PIN", "Enter the PIN to unlock funds")
        if not pin:
            return
        
        if messagebox.askyesno("Confirm Unlock", f"Unlock ₹{amount_str:,.2f} from lock #{lock_id}?"):
            success, message = unlock_funds(lock_id, self.account.id, pin, amount_str)
            messagebox.showinfo("Success", message) if success else messagebox.showerror("Error", message)
            if success:
                self._refresh_balance()
                win.destroy()
    
    def show_transactions(self):
        """Show transaction history with sorting"""
        transactions = get_account_transactions(self.account.id, limit=50)
        
        win = ttk.Toplevel(self)
        win.title("Transaction History")
        win.geometry("800x600")
        win.transient(self)
        win.grab_set()
        
        columns = ('date', 'type', 'amount', 'description')
        tree = ttk.Treeview(
            win,
            columns=columns,
            show='headings',
            bootstyle=PRIMARY
        )
        
        tree.heading('date', text='Date', command=lambda: self._sort_tree(tree, 'date', False))
        tree.heading('type', text='Type', command=lambda: self._sort_tree(tree, 'type', False))
        tree.heading('amount', text='Amount (₹)', command=lambda: self._sort_tree(tree, 'amount', False))
        tree.heading('description', text='Description')
        
        tree.column('date', width=150, anchor=W)
        tree.column('type', width=100, anchor=CENTER)
        tree.column('amount', width=120, anchor=E)
        tree.column('description', width=350, anchor=W)
        
        self.transaction_data = []
        for txn in transactions:
            created_at = datetime.strptime(txn.created_at, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M")
            self.transaction_data.append({
                'date': created_at,
                'type': txn.type.capitalize(),
                'amount': txn.amount,
                'description': txn.description or "No description"
            })
            tree.insert('', END, values=(
                created_at,
                txn.type.capitalize(),
                f"{txn.amount:,.2f}",
                txn.description or "No description"
            ))
        
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        ttk.Button(
            win,
            text="Close",
            command=win.destroy,
            bootstyle=SECONDARY,
            style="Custom.TButton"
        ).pack(pady=10)
    
    def _sort_tree(self, tree, col, reverse):
        """Sort Treeview by column"""
        items = [(tree.set(k, col), k) for k in tree.get_children('')]
        if col == 'amount':
            items.sort(key=lambda x: float(x[0].replace(",", "")), reverse=reverse)
        else:
            items.sort(key=lambda x: x[0], reverse=reverse)
        
        for index, (_, k) in enumerate(items):
            tree.move(k, '', index)
        
        tree.heading(col, command=lambda: self._sort_tree(tree, col, not reverse))
    
    def _refresh_balance(self):
        """Refresh the displayed balance"""
        self.account.balance = get_account_balance(self.account.id)
        self.balance_label.config(text=f"Balance: ₹{self.account.balance:,.2f}")
    
    def _get_amount(self, title, placeholder, max_value=None) -> Optional[Decimal]:
        """Custom dialog for amount input"""
        while True:
            amount_str = simpledialog.askstring(
                title,
                f"{placeholder}:",
                parent=self,
                initialvalue=""
            )
            if amount_str is None:
                return None
            try:
                amount = Decimal(amount_str)
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be positive")
                    continue
                if max_value and amount > max_value:
                    messagebox.showerror("Error", f"Amount cannot exceed ₹{max_value:,.2f}")
                    continue
                return amount
            except:
                messagebox.showerror("Error", "Please enter a valid number")
                continue
    
    def _get_pin(self, title, placeholder) -> Optional[str]:
        """Custom dialog for PIN input"""
        while True:
            pin = simpledialog.askstring(
                title,
                f"{placeholder}:",
                parent=self,
                show="*",
                initialvalue=""
            )
            if pin is None:
                return None
            if len(pin) < 4:
                messagebox.showerror("Error", "PIN must be at least 4 characters")
                continue
            return pin
    
    def _get_description(self, title, placeholder) -> Optional[str]:
        """Custom dialog for description input"""
        description = simpledialog.askstring(
            title,
            f"{placeholder}:",
            parent=self,
            initialvalue=""
        )
        return description.strip() if description else None