from decimal import Decimal
import sqlite3
from typing import List, Optional, Tuple
from src.database import get_db_connection
from src.models import Transaction
import bcrypt
import re

MAX_DEPOSIT = Decimal("1000000")  # ₹10,00,000
MAX_WITHDRAW = Decimal("500000")  # ₹5,00,000
MAX_LOCK = Decimal("1000000")    # ₹10,00,000
MAX_TRANSFER = Decimal("500000") # ₹5,00,000

def sanitize_description(description: Optional[str]) -> Optional[str]:
    """Sanitize description to prevent SQL injection"""
    if not description:
        return None
    description = re.sub(r'[;\"\'\\]', '', description.strip())
    return description[:100] if description else None

def get_account_by_number(account_number: str) -> Optional[dict]:
    """
    Get an account by its account number
    Args:
        account_number: The account number to look up
    Returns:
        dict: Account details if found, None otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """SELECT id, user_id, account_number, balance, account_type 
                   FROM accounts WHERE account_number = ?""",
                (account_number,)
            )
            result = cursor.fetchone()
            if result:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, result))
            return None
        except sqlite3.Error as e:
            print(f"Get account error for account number {account_number}: {e}")
            return None

def deposit(account_id: int, amount: Decimal, description: Optional[str] = None) -> Tuple[bool, str]:
    """
    Deposit funds into an account
    Args:
        account_id: The account ID to deposit to
        amount: The amount to deposit (must be positive)
        description: Optional description of the deposit
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not isinstance(amount, Decimal) or amount <= 0:
        return False, "Please enter a positive amount"
    if amount > MAX_DEPOSIT:
        return False, f"Deposit exceeds maximum limit of ₹{MAX_DEPOSIT:,.2f}"
    
    description = sanitize_description(description)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                (str(amount), account_id)
            )
            if cursor.rowcount == 0:
                conn.rollback()
                return False, f"Account ID {account_id} not found"
            
            cursor.execute(
                """INSERT INTO transactions 
                (account_id, type, amount, description, status)
                VALUES (?, ?, ?, ?, ?)""",
                (account_id, "deposit", str(amount), description or "Deposit", "completed")
            )
            
            conn.commit()
            return True, f"Successfully deposited ₹{amount:,.2f}"
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Deposit failed for account ID {account_id}: Database error ({str(e)})"

def withdraw(account_id: int, amount: Decimal, description: Optional[str] = None) -> Tuple[bool, str]:
    """
    Withdraw funds from an account
    Args:
        account_id: The account ID to withdraw from
        amount: The amount to withdraw (must be positive)
        description: Optional description of the withdrawal
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not isinstance(amount, Decimal) or amount <= 0:
        return False, "Please enter a positive amount"
    if amount > MAX_WITHDRAW:
        return False, f"Withdrawal exceeds maximum limit of ₹{MAX_WITHDRAW:,.2f}"
    
    description = sanitize_description(description)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute(
                "SELECT balance FROM accounts WHERE id = ?",
                (account_id,)
            )
            result = cursor.fetchone()
            if not result:
                conn.rollback()
                return False, f"Account ID {account_id} not found"
                
            balance = Decimal(result["balance"])
            if balance < amount:
                conn.rollback()
                return False, f"Insufficient funds in account ID {account_id}"
            
            cursor.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                (str(amount), account_id)
            )
            
            cursor.execute(
                """INSERT INTO transactions 
                (account_id, type, amount, description, status)
                VALUES (?, ?, ?, ?, ?)""",
                (account_id, "withdraw", str(amount), description or "Withdrawal", "completed")
            )
            
            conn.commit()
            return True, f"Successfully withdrawn ₹{amount:,.2f}"
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Withdrawal failed for account ID {account_id}: Database error ({str(e)})"

def transfer_funds(sender_account_id: int, receiver_account_number: str, amount: Decimal, description: Optional[str] = None) -> Tuple[bool, str]:
    """
    Transfer funds from one account to another
    Args:
        sender_account_id: The account ID of the sender
        receiver_account_number: The account number of the receiver
        amount: The amount to transfer (must be positive)
        description: Optional description of the transfer
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not isinstance(amount, Decimal) or amount <= 0:
        return False, "Please enter a positive amount"
    if amount > MAX_TRANSFER:
        return False, f"Transfer exceeds maximum limit of ₹{MAX_TRANSFER:,.2f}"

    description = sanitize_description(description)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")

            # Check sender's balance
            cursor.execute(
                "SELECT balance FROM accounts WHERE id = ?",
                (sender_account_id,)
            )
            sender_result = cursor.fetchone()
            if not sender_result:
                conn.rollback()
                return False, f"Sender account ID {sender_account_id} not found"
            
            sender_balance = Decimal(sender_result["balance"])
            if sender_balance < amount:
                conn.rollback()
                return False, f"Insufficient funds in sender account ID {sender_account_id}"

            # Get receiver's account
            receiver = get_account_by_number(receiver_account_number)
            if not receiver:
                conn.rollback()
                return False, f"Receiver account number {receiver_account_number} not found"
            
            receiver_account_id = receiver["id"]

            # Prevent self-transfer
            if sender_account_id == receiver_account_id:
                conn.rollback()
                return False, "Cannot transfer to the same account"

            # Update sender's balance
            cursor.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                (str(amount), sender_account_id)
            )
            if cursor.rowcount == 0:
                conn.rollback()
                return False, f"Failed to update sender account ID {sender_account_id}"

            # Update receiver's balance
            cursor.execute(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                (str(amount), receiver_account_id)
            )
            if cursor.rowcount == 0:
                conn.rollback()
                return False, f"Failed to update receiver account ID {receiver_account_id}"

            # Record sender's transaction
            sender_desc = description or f"Transfer to {receiver_account_number}"
            cursor.execute(
                """INSERT INTO transactions 
                (account_id, type, amount, description, reference, status)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (sender_account_id, "transfer_out", str(amount), sender_desc, receiver_account_number, "completed")
            )
            sender_txn_id = cursor.lastrowid

            # Record receiver's transaction
            receiver_desc = description or f"Transfer from sender"
            cursor.execute(
                """INSERT INTO transactions 
                (account_id, type, amount, description, reference, status)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (receiver_account_id, "transfer_in", str(amount), receiver_desc, f"sender_txn_{sender_txn_id}", "completed")
            )

            conn.commit()
            return True, f"Successfully transferred ₹{amount:,.2f} to {receiver_account_number}"
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Transfer failed: Database error ({str(e)})"

def get_account_transactions(account_id: int, limit: int = None) -> List[Transaction]:
    """
    Get transactions for an account
    Args:
        account_id: The account ID to get transactions for
        limit: Optional limit on number of transactions to return
    Returns:
        List[Transaction]: List of transaction objects
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            query = """
                SELECT id, account_id, type, amount, description, status, created_at
                FROM transactions
                WHERE account_id = ?
                ORDER BY created_at DESC
            """
            params = [account_id]
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            transactions = [
                Transaction(
                    id=row[0],
                    account_id=row[1],
                    type=row[2],
                    amount=Decimal(row[3]),
                    description=row[4],
                    status=row[5],
                    created_at=row[6]
                ) for row in cursor.fetchall()
            ]
            return transactions
        except sqlite3.Error as e:
            print(f"Get transactions error for account ID {account_id}: {e}")
            return []

def get_account_balance(account_id: int) -> Decimal:
    """
    Get the current balance of an account
    Args:
        account_id: The account ID to get balance for
    Returns:
        Decimal: The account balance
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT balance FROM accounts WHERE id = ?",
                (account_id,)
            )
            result = cursor.fetchone()
            return Decimal(result["balance"]) if result else Decimal("0")
        except sqlite3.Error as e:
            print(f"Get balance error for account ID {account_id}: {e}")
            return Decimal("0")

def lock_funds(account_id: int, amount: Decimal, pin: str, description: Optional[str] = None) -> Tuple[bool, str]:
    """
    Lock funds from account balance with a PIN
    Args:
        account_id: The account ID to lock funds from
        amount: The amount to lock (must be positive)
        pin: The PIN to secure the locked funds
        description: Optional description of the lock
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not isinstance(amount, Decimal) or amount <= 0:
        return False, "Please enter a positive amount"
    if amount > MAX_LOCK:
        return False, f"Lock amount exceeds maximum limit of ₹{MAX_LOCK:,.2f}"
    if not pin or len(pin) < 4:
        return False, "PIN must be at least 4 characters"
    
    description = sanitize_description(description)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute(
                "SELECT balance FROM accounts WHERE id = ?",
                (account_id,)
            )
            result = cursor.fetchone()
            if not result:
                conn.rollback()
                return False, f"Account ID {account_id} not found"
                
            balance = Decimal(result["balance"])
            if balance < amount:
                conn.rollback()
                return False, f"Insufficient funds in account ID {account_id}"
            
            cursor.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                (str(amount), account_id)
            )
            
            cursor.execute(
                """INSERT INTO transactions 
                (account_id, type, amount, description, status)
                VALUES (?, ?, ?, ?, ?)""",
                (account_id, "lock", str(amount), description or "Funds locked", "completed")
            )
            
            pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
            
            cursor.execute(
                """
                INSERT INTO locked_funds 
                (account_id, amount, pin_hash, description) 
                VALUES (?, ?, ?, ?)
                """,
                (account_id, str(amount), pin_hash, description)
            )
            
            conn.commit()
            return True, f"Successfully locked ₹{amount:,.2f}"
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Locking failed for account ID {account_id}: Database error ({str(e)})"

def get_locked_funds(account_id: int) -> List[dict]:
    """
    Get all locked funds for an account
    Args:
        account_id: The account ID to get locked funds for
    Returns:
        List[dict]: List of locked funds as dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, amount, description, created_at 
                FROM locked_funds 
                WHERE account_id = ? AND is_unlocked = 0
                ORDER BY created_at DESC
                """,
                (account_id,)
            )
            columns = [col[0] for col in cursor.description]
            funds = [dict(zip(columns, row)) for row in cursor.fetchall()]
            for fund in funds:
                fund['amount'] = Decimal(fund['amount'])
            return funds
        except sqlite3.Error as e:
            print(f"Error getting locked funds for account ID {account_id}: {e}")
            return []

def unlock_funds(lock_id: int, account_id: int, pin: str, amount_to_unlock: Optional[Decimal] = None) -> Tuple[bool, str]:
    """
    Unlock funds with the correct PIN
    Args:
        lock_id: The ID of the locked funds record
        account_id: The account ID associated with the lock
        pin: The PIN to verify
        amount_to_unlock: Optional amount to unlock (if None, unlocks all)
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not pin:
        return False, "PIN is required"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute(
                """
                SELECT amount, pin_hash 
                FROM locked_funds 
                WHERE id = ? AND account_id = ? AND is_unlocked = 0
                """,
                (lock_id, account_id)
            )
            result = cursor.fetchone()
            if not result:
                conn.rollback()
                return False, "Locked funds not found or already unlocked"
            
            locked_amount = Decimal(result["amount"])
            stored_pin_hash = result["pin_hash"]
            
            if not bcrypt.checkpw(pin.encode(), stored_pin_hash.encode()):
                conn.rollback()
                return False, "Incorrect PIN"
            
            amount_to_unlock = amount_to_unlock or locked_amount
            if not isinstance(amount_to_unlock, Decimal) or amount_to_unlock <= 0:
                conn.rollback()
                return False, "Please enter a positive amount"
            if amount_to_unlock > locked_amount:
                conn.rollback()
                return False, f"Amount exceeds locked funds (₹{locked_amount:,.2f})"
            
            remaining_locked = locked_amount - amount_to_unlock
            if remaining_locked > 0:
                cursor.execute(
                    "UPDATE locked_funds SET amount = ? WHERE id = ?",
                    (str(remaining_locked), lock_id)
                )
            else:
                cursor.execute(
                    "UPDATE locked_funds SET is_unlocked = 1, amount = 0 WHERE id = ?",
                    (lock_id,)
                )
            
            cursor.execute(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                (str(amount_to_unlock), account_id)
            )
            
            cursor.execute(
                """INSERT INTO transactions 
                (account_id, type, amount, description, status)
                VALUES (?, ?, ?, ?, ?)""",
                (account_id, "unlock", str(amount_to_unlock), f"Funds unlocked from lock #{lock_id}", "completed")
            )
            
            conn.commit()
            return True, f"Successfully unlocked ₹{amount_to_unlock:,.2f}"
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Unlocking failed for lock ID {lock_id}: Database error ({str(e)})"