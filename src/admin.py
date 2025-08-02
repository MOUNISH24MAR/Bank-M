from typing import List
from src.database import get_db_connection
from src.models import User, Account, Transaction

def get_all_users() -> List[User]:
    """Get all registered users"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, role, full_name, email, created_at FROM users"
        )
        return [User(**row) for row in cursor.fetchall()]

def get_all_transactions(limit: int = None) -> List[Transaction]:
    """Get all system transactions"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """SELECT id, account_id, type, amount, description, reference, 
                  status, created_at FROM transactions 
                  ORDER BY created_at DESC"""
        if limit is not None:
            query += " LIMIT ?"
            cursor.execute(query, (limit,))
        else:
            cursor.execute(query)
        return [Transaction(**row) for row in cursor.fetchall()]

def get_user_accounts(user_id: int) -> List[Account]:
    """Get all accounts for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, user_id, account_number, balance, account_type, is_blocked 
            FROM accounts WHERE user_id = ?""",
            (user_id,)
        )
        return [Account(**row) for row in cursor.fetchall()]

def get_transactions_with_user_details(limit: int = None) -> List[dict]:
    """Get all transactions with associated user details"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT t.id, t.account_id, t.type, t.amount, t.description, t.status, t.created_at,
                   u.username, u.full_name
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            JOIN users u ON a.user_id = u.id
            ORDER BY t.created_at DESC
        """
        params = []
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def block_unblock_account(account_id: int, block: bool) -> bool:
    """Block or unblock an account"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE accounts SET is_blocked = ? WHERE id = ?",
                (1 if block else 0, account_id)
            )
            if cursor.rowcount == 0:
                return False
            conn.commit()
            return True
        except sqlite3.Error:
            return False