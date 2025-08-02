from decimal import Decimal
import sqlite3
from typing import List, Optional, Tuple
from src.database import get_db_connection
from src.models import Transaction
import bcrypt
import re

MAX_DEPOSIT = Decimal("1000000")
MAX_WITHDRAW = Decimal("500000")
MAX_LOCK = Decimal("1000000")

def sanitize_description(description: Optional[str]) -> Optional[str]:
    """Sanitize description to prevent SQL injection"""
    if not description:
        return None
    description = re.sub(r'[;\"\'\\]', '', description.strip())
    return description[:100] if description else None

def deposit(account_id: int, amount: Decimal, description: Optional[str] = None) -> Tuple[bool, str]:
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

def lock_funds(account_id: int, amount: Decimal, pin: str, description: Optional[str] = None) -> Tuple[bool, str]:
    if not isinstance(amount, Decimal) or amount <= 0:
        return False, "Please enter a positive amount"
    if amount > MAX_LOCK:
        return False, f"Lock amount exceeds maximum limit of ₹{MAX_LOCK:,.2f}"
    if not pin:
        return False, "PIN is required"
    
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
                return False, f"Insufficient funds to lock ₹{amount:,.2f}"
            
            pin_hash = bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()
            
            cursor.execute(
                """INSERT INTO locked_funds 
                (account_id, amount, pin_hash, description)
                VALUES (?, ?, ?, ?)""",
                (account_id, str(amount), pin_hash, description or "Locked funds")
            )
            
            cursor.execute(
                "UPDATE accounts SET balance = balance - ? WHERE id = ?",
                (str(amount), account_id)
            )
            
            conn.commit()
            return True, f"Successfully locked ₹{amount:,.2f}"
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Lock funds failed: Database error ({str(e)})"

def unlock_funds(lock_id: int, account_id: int, pin: str) -> Tuple[bool, str]:
    if not pin:
        return False, "PIN is required"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute(
                """SELECT amount, pin_hash, is_unlocked 
                FROM locked_funds 
                WHERE id = ? AND account_id = ?""",
                (lock_id, account_id)
            )
            result = cursor.fetchone()
            if not result:
                conn.rollback()
                return False, "Locked funds not found"
                
            if result["is_unlocked"]:
                conn.rollback()
                return False, "Funds already unlocked"
                
            stored_pin_hash = result["pin_hash"].encode()
            if not bcrypt.checkpw(pin.encode(), stored_pin_hash):
                conn.rollback()
                return False, "Incorrect PIN"
                
            amount = Decimal(result["amount"])
            
            cursor.execute(
                "UPDATE locked_funds SET is_unlocked = 1 WHERE id = ?",
                (lock_id,)
            )
            
            cursor.execute(
                "UPDATE accounts SET balance = balance + ? WHERE id = ?",
                (str(amount), account_id)
            )
            
            cursor.execute(
                """INSERT INTO transactions 
                (account_id, type, amount, description, status)
                VALUES (?, ?, ?, ?, ?)""",
                (account_id, "unlock", str(amount), "Unlocked funds", "completed")
            )
            
            conn.commit()
            return True, f"Successfully unlocked ₹{amount:,.2f}"
        except sqlite3.Error as e:
            conn.rollback()
            return False, f"Unlock funds failed: Database error ({str(e)})"

def get_account_transactions(account_id: int, limit: int = None) -> List[Transaction]:
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

def get_locked_funds(account_id: int) -> List[dict]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """SELECT id, amount, description, created_at 
                FROM locked_funds 
                WHERE account_id = ? AND is_unlocked = 0""",
                (account_id,)
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Get locked funds error for account ID {account_id}: {e}")
            return []