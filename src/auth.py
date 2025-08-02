from typing import Optional
from src.models import User
from src.database import get_db_connection
import sqlite3

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user and return User object if successful"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, role, full_name, email, created_at FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        user_data = cursor.fetchone()
        
        if user_data:
            return User(**user_data)
        return None

def register_user(username: str, password: str, full_name: str = None, email: str = None) -> Optional[User]:
    """Register a new user and return User object if successful"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO users (username, password, full_name, email) VALUES (?, ?, ?, ?)",
                (username, password, full_name, email)
            )
            user_id = cursor.lastrowid
            
            account_number = f"AC{user_id:08d}"
            cursor.execute(
                "INSERT INTO accounts (user_id, account_number) VALUES (?, ?)",
                (user_id, account_number)
            )
            
            conn.commit()
            return get_user_by_id(user_id)
    except sqlite3.IntegrityError:
        return None

def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, role, full_name, email, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        user_data = cursor.fetchone()
        return User(**user_data) if user_data else None