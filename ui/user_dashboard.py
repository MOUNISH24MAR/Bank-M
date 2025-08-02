import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from decimal import Decimal
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from src.models import User
from src.transactions import deposit, withdraw, get_account_balance, get_account_transactions, lock_funds, unlock_funds, get_locked_funds, transfer_funds
from src.admin import get_user_accounts
from src.database import get_db_connection
from datetime import datetime

class UserDashboard(ttk.Frame):
    def __init__(self, parent, user: User, on_logout):
        super().__init__(parent, padding=(20, 10))
        self.user = user
        self.on_logout = on_logout
        self.accounts = get_user_accounts(self.user.id)
        self.selected_account = tk.StringVar(value=self.accounts[0].id if self.accounts else "")
        self.setup_ui()

    def setup_ui(self):
        self.header = ttk.Frame(self)
        self.header.pack(fill=X, pady=10)
        
        ttk.Label(
            self.header,
            text=f"Welcome, {self.user.full_name or self.user.username}",
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
        
        self.account_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.account_tab, text="Account")
        self.setup_account_tab()
        
        self.transactions_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.transactions_tab, text="Transactions")
        self.setup_transactions_tab()
        
        self.transfer_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.transfer_tab, text="Transfer")
        self.setup_transfer_tab()
        
        self.lock_funds_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.lock_funds_tab, text="Lock Funds")
        self.setup_lock_funds_tab()

    def setup_account_tab(self):
        if not self.accounts:
            ttk.Label(self.account_tab, text="No accounts found").pack(pady=20)
            return
        
        ttk.Label(
            self.account_tab,
            text="Select Account:",
            font=('Helvetica', 12)
        ).pack(anchor=W, padx=10, pady=5)
        
        account_menu = ttk.Combobox(
            self.account_tab,
            textvariable=self.selected_account,
            values=[str(acc.id) for acc in self.accounts],
            state="readonly",
            width=20
        )
        account_menu.pack(anchor=W, padx=10, pady=5)
        account_menu.bind('<<ComboboxSelected>>', self.update_balance)
        
        self.balance_label = ttk.Label(
            self.account_tab,
            text="Balance: ₹0.00",
            font=('Helvetica', 14)
        ).pack(anchor=W, padx=10, pady=10)
        
        ttk.Label(
            self.account_tab,
            text="Amount:",
            font=('Helvetica', 12)
        ).pack(anchor=W, padx=10, pady=5)
        
        self.amount_entry = ttk.Entry(self.account_tab, font=('Helvetica', 12), width=20)
        self.amount_entry.pack(anchor=W, padx=10, pady=5)
        
        ttk.Label(
            self.account_tab,
            text="Description:",
            font=('Helvetica', 12)
        ).pack(anchor=W, padx=10, pady=5)
        
        self.desc_entry = ttk.Entry(self.account_tab, font=('Helvetica', 12), width=30)
        self.desc_entry.pack(anchor=W, padx=10, pady=5)
        
        btn_frame = ttk.Frame(self.account_tab)
        btn_frame.pack(fill=X, padx=10, pady=10)
        
        ttk.Button(
            btn_frame,
            text="Deposit",
            command=self.handle_deposit,
            bootstyle=SUCCESS,
            width=15
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Withdraw",
            command=self.handle_withdraw,
            bootstyle=DANGER,
            width=15
        ).pack(side=LEFT, padx=5)
        
        self.update_balance()

    def setup_transactions_tab(self):
        columns = ('id', 'type', 'amount', 'status', 'created_at')
        self.txn_tree = ttk.Treeview(
            self.transactions_tab, 
            columns=columns, 
            show='headings',
            bootstyle=PRIMARY
        )
        
        self.txn_tree.heading('id', text='ID')
        self.txn_tree.heading('type', text='Type')
        self.txn_tree.heading('amount', text='Amount')
        self.txn_tree.heading('status', text='Status')
        self.txn_tree.heading('created_at', text='Date')
        
        self.txn_tree.column('id', width=50, anchor=CENTER)
        self.txn_tree.column('type', width=100, anchor=CENTER)
        self.txn_tree.column('amount', width=100, anchor=E)
        self.txn_tree.column('status', width=100, anchor=CENTER)
        self.txn_tree.column('created_at', width=150, anchor=W)
        
        self.update_transactions()
        
        self.txn_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        ttk.Button(
            self.transactions_tab,
            text="Refresh",
            command=self.update_transactions,
            bootstyle=SECONDARY,
            width=15
        ).pack(pady=5)

    def setup_transfer_tab(self):
        ttk.Label(
            self.transfer_tab,
            text="Select Account:",
            font=('Helvetica', 12)
        ).pack(anchor=W, padx=10, pady=5)
        
        account_menu = ttk.Combobox(
            self.transfer_tab,
            textvariable=self.selected_account,
            values=[str(acc.id) for acc in self.accounts],
            state="readonly",
            width=20
        )
        account_menu.pack(anchor=W, padx=10, pady=5)
        
        ttk.Label(
            self.transfer_tab,
            text="Recipient Account Number:",
            font=('Helvetica', 12)
        ).pack(anchor=W, padx=10, pady=5)
        
        self.transfer_account_entry = ttk.Entry(self.transfer_tab, font=('Helvetica', 12), width=20)
        self.transfer_account_entry.pack(anchor=W, padx=10, pady=5)
        
        ttk.Label(
            self.transfer_tab,
            text="Amount:",
            font=('Helvetica', 12)
        ).pack(anchor=W, padx=10, pady=5)
        
        self.transfer_amount_entry = ttk.Entry(self.transfer_tab, font=('Helvetica', 12), width=20)
        self.transfer_amount_entry.pack(anchor=W, padx=10, pady=5)
        
        ttk.Label(
            self.transfer_tab,
            text="Description:",
            font=('Helvetica', 12)
        ).pack(anchor=W, padx=10, pady=5)
        
        self.transfer_desc_entry = ttk.Entry(self.transfer_tab, font=('Helvetica', 12), width=30)
        self.transfer_desc_entry.pack(anchor=W, padx=10, pady=5)
        
        ttk.Button(
            self.transfer_tab,
            text="Pay",
            command=self.handle_transfer,
            bootstyle=INFO,
            width=15
        ).pack(pady=10)

    def setup_lock_funds_tab(self):
        ttk.Label(
            self.lock_funds_tab,
            text="Lock Funds",
            font=('Helvetica', 14, 'bold')
        ).pack(pady=10)
        
        ttk.Label(
            self.lock_funds_tab,
            text="Select Account:",
            font=('Helvetica', 12)
        ).pack(anchor=W, padx=10, pady=5)
        
        account_menu = ttk.Combobox(
            self.lock_funds_tab,
            textvariable=self.selected_account,
            values=[str(acc.id) for acc in self.accounts],
            state="readonly",
            width=20
        )
        account_menu.pack(anchor=W, padx=10, pady=5)
        
        ttk.Label(
            self.lock_funds_tab,
            text="Amount:",
            font=('Helvetica', 12)
        ).pack(anchor=W, padx=10, pady=5)
        
        self.lock_amount_entry = ttk.Entry(self.lock_funds_tab, font=('Helvetica', 12), width=20)
        self.lock_amount_entry.pack(anchor=W, padx=10, pady=5)
        
        ttk.Label(
            self.lock_funds_tab,
            text="PIN:",
            font=('Helvetica', 12)
        ).pack(anchor=W, padx=10, pady=5)
        
        self.pin_entry = ttk.Entry(self.lock_funds_tab, font=('Helvetica', 12), show="*", width=20)
        self.pin_entry.pack(anchor=W, padx=10, pady=5)
        
        ttk.Button(
            self.lock_funds_tab,
            text="Lock Funds",
            command=self.handle_lock_funds,
            bootstyle=PRIMARY,
            width=15
        ).pack(pady=10)
        
        ttk.Label(
            self.lock_funds_tab,
            text="Locked Funds",
            font=('Helvetica', 14, 'bold')
        ).pack(pady=10)
        
        columns = ('id', 'amount', 'created_at')
        self.locked_tree = ttk.Treeview(
            self.lock_funds_tab, 
            columns=columns, 
            show='headings',
            bootstyle=PRIMARY
        )
        
        self.locked_tree.heading('id', text='Lock ID')
        self.locked_tree.heading('amount', text='Amount')
        self.locked_tree.heading('created_at', text='Locked At')
        
        self.locked_tree.column('id', width=50, anchor=CENTER)
        self.locked_tree.column('amount', width=100, anchor=E)
        self.locked_tree.column('created_at', width=150, anchor=W)
        
        self.update_locked_funds()
        
        self.locked_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(
            self.lock_funds_tab,
            text="Unlock PIN:",
            font=('Helvetica', 12)
        ).pack(anchor=W, padx=10, pady=5)
        
        self.unlock_pin_entry = ttk.Entry(self.lock_funds_tab, font=('Helvetica', 12), show="*", width=20)
        self.unlock_pin_entry.pack(anchor=W, padx=10, pady=5)
        
        ttk.Button(
            self.lock_funds_tab,
            text="Unlock Funds",
            command=self.handle_unlock_funds,
            bootstyle=WARNING,
            width=15
        ).pack(pady=10)

    def update_balance(self, event=None):
        if self.accounts:
            account_id = int(self.selected_account.get())
            balance = get_account_balance(account_id)
            self.balance_label.config(text=f"Balance: ₹{balance:,.2f}")

    def update_transactions(self):
        for item in self.txn_tree.get_children():
            self.txn_tree.delete(item)
        
        if self.accounts:
            account_id = int(self.selected_account.get())
            transactions = get_account_transactions(account_id, limit=50)
            for txn in transactions:
                self.txn_tree.insert('', END, values=(
                    txn.id,
                    txn.type.capitalize(),
                    f"₹{txn.amount:,.2f}",
                    txn.status.capitalize(),
                    txn.created_at
                ))

    def update_locked_funds(self):
        for item in self.locked_tree.get_children():
            self.locked_tree.delete(item)
        
        if self.accounts:
            account_id = int(self.selected_account.get())
            locked_funds = get_locked_funds(account_id)
            for fund in locked_funds:
                self.locked_tree.insert('', END, values=(
                    fund['id'],
                    f"₹{fund['amount']:,.2f}",
                    fund['created_at']
                ))

    def handle_deposit(self):
        try:
            amount = Decimal(self.amount_entry.get())
            description = self.desc_entry.get().strip()
            account_id = int(self.selected_account.get())
            
            success, message = deposit(account_id, amount, description)
            messagebox.showinfo("Deposit", message) if success else messagebox.showerror("Error", message)
            self.update_balance()
            self.update_transactions()
            self.amount_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")

    def handle_withdraw(self):
        try:
            amount = Decimal(self.amount_entry.get())
            description = self.desc_entry.get().strip()
            account_id = int(self.selected_account.get())
            
            success, message = withdraw(account_id, amount, description)
            messagebox.showinfo("Withdraw", message) if success else messagebox.showerror("Error", message)
            self.update_balance()
            self.update_transactions()
            self.amount_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")

    def handle_transfer(self):
        try:
            receiver_account_number = self.transfer_account_entry.get().strip()
            amount = Decimal(self.transfer_amount_entry.get())
            description = self.transfer_desc_entry.get().strip()
            sender_account_id = int(self.selected_account.get())
            
            if not receiver_account_number:
                messagebox.showerror("Error", "Please enter a recipient account number")
                return
                
            success, message = transfer_funds(sender_account_id, receiver_account_number, amount, description)
            
            if success:
                # Fetch transaction details for the receipt
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    # Get the sender's account details
                    cursor.execute(
                        """
                        SELECT a.account_number, u.username, u.full_name
                        FROM accounts a
                        JOIN users u ON a.user_id = u.id
                        WHERE a.id = ?
                        """,
                        (sender_account_id,)
                    )
                    sender_details = cursor.fetchone()
                    
                    # Get the receiver's account details
                    cursor.execute(
                        """
                        SELECT a.id, a.account_number, u.username, u.full_name
                        FROM accounts a
                        JOIN users u ON a.user_id = u.id
                        WHERE a.account_number = ?
                        """,
                        (receiver_account_number,)
                    )
                    receiver_details = cursor.fetchone()
                    receiver_account_id = receiver_details["id"]
                    
                    # Get the latest withdrawal transaction for the sender
                    cursor.execute(
                        """
                        SELECT id, created_at
                        FROM transactions
                        WHERE account_id = ? AND type = 'withdrawal' AND reference = ?
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        (sender_account_id, receiver_account_number)
                    )
                    withdrawal_txn = cursor.fetchone()
                    
                    # Get the latest deposit transaction for the receiver
                    cursor.execute(
                        """
                        SELECT id
                        FROM transactions
                        WHERE account_id = ? AND type = 'deposit' AND reference = ?
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        (receiver_account_id, sender_details["account_number"])
                    )
                    deposit_txn = cursor.fetchone()

                # Generate plain text receipt
                receipt_text = self.generate_transfer_receipt(
                    amount=amount,
                    payer_account_number=sender_details["account_number"],
                    payer_name=sender_details["full_name"] or sender_details["username"],
                    payee_account_number=receiver_account_number,
                    payee_name=receiver_details["full_name"] or receiver_details["username"],
                    transaction_date=withdrawal_txn["created_at"],
                    withdrawal_txn_id=withdrawal_txn["id"],
                    deposit_txn_id=deposit_txn["id"]
                )

                # Show the receipt in a new window
                self.show_receipt_window(receipt_text)

                messagebox.showinfo("Pay", "Transfer completed successfully. Receipt generated.")
            else:
                messagebox.showerror("Error", message)
            
            self.update_balance()
            self.update_transactions()
            self.transfer_account_entry.delete(0, tk.END)
            self.transfer_amount_entry.delete(0, tk.END)
            self.transfer_desc_entry.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")

    def generate_transfer_receipt(self, amount, payer_account_number, payer_name,
                                payee_account_number, payee_name, transaction_date,
                                withdrawal_txn_id, deposit_txn_id):
        # Generate a plain text receipt
        receipt = (
            "RRM Bank\n"
            "Transaction Receipt\n"
            "----------------------------------------\n\n"
            f"Transaction Date: {transaction_date}\n"
            f"Withdrawal Transaction ID: {withdrawal_txn_id}\n"
            f"Deposit Transaction ID: {deposit_txn_id}\n\n"
            f"Amount Transferred: ₹{float(amount):,.2f}\n\n"
            "Payer Details:\n"
            f"  Account Number: {payer_account_number}\n"
            f"  Name: {payer_name}\n\n"
            "Payee Details:\n"
            f"  Account Number: {payee_account_number}\n"
            f"  Name: {payee_name}\n\n"
            "----------------------------------------\n"
            "This is an official receipt from RRM Bank. Please keep it for your records.\n"
        )
        return receipt

    def show_receipt_window(self, receipt_text):
        # Create a new window to display the receipt
        receipt_window = tk.Toplevel(self)
        receipt_window.title("Transaction Receipt")
        receipt_window.geometry("400x500")
        receipt_window.resizable(False, False)

        # Create a Text widget to display the receipt
        text_area = tk.Text(
            receipt_window,
            wrap=tk.WORD,
            font=('Courier', 12),
            height=20,
            width=50
        )
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, receipt_text)
        text_area.config(state=tk.DISABLED)  # Make the text read-only

        # Add a "Save as Text" button
        def save_receipt():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                title="Save Receipt As",
                initialfile=f"Transfer_Receipt_{withdrawal_txn_id}.txt"
            )
            if file_path:
                with open(file_path, "w") as f:
                    f.write(receipt_text)
                messagebox.showinfo("Success", "Receipt saved successfully!")

        ttk.Button(
            receipt_window,
            text="Save as Text",
            command=save_receipt,
            bootstyle=INFO,
            width=15
        ).pack(pady=10)

    def handle_lock_funds(self):
        try:
            amount = Decimal(self.lock_amount_entry.get())
            pin = self.pin_entry.get().strip()
            account_id = int(self.selected_account.get())
            description = "Locked funds"
            
            success, message = lock_funds(account_id, amount, pin, description)
            messagebox.showinfo("Lock Funds", message) if success else messagebox.showerror("Error", message)
            self.update_balance()
            self.update_locked_funds()
            self.lock_amount_entry.delete(0, tk.END)
            self.pin_entry.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")

    def handle_unlock_funds(self):
        selected = self.locked_tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select a locked fund")
            return
        
        try:
            lock_id = int(self.locked_tree.item(selected)['values'][0])
            pin = self.unlock_pin_entry.get().strip()
            account_id = int(self.selected_account.get())
            
            success, message = unlock_funds(lock_id, account_id, pin)
            messagebox.showinfo("Unlock Funds", message) if success else messagebox.showerror("Error", message)
            self.update_balance()
            self.update_locked_funds()
            self.unlock_pin_entry.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Invalid input")