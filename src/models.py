from datetime import datetime
from typing import Optional

class User:
    def __init__(self, id: int, username: str, role: str, 
                 full_name: Optional[str] = None, 
                 email: Optional[str] = None,
                 created_at: Optional[datetime] = None):
        self.id = id
        self.username = username
        self.role = role
        self.full_name = full_name
        self.email = email
        self.created_at = created_at

class Account:
    def __init__(self, id: int, user_id: int, account_number: str, 
                 balance: float, account_type: str = "savings",
                 is_blocked: bool = False):
        self.id = id
        self.user_id = user_id
        self.account_number = account_number
        self.balance = balance
        self.account_type = account_type
        self.is_blocked = is_blocked

class Transaction:
    def __init__(self, id: int, account_id: int, type: str, 
                 amount: float, description: Optional[str] = None,
                 reference: Optional[str] = None, status: str = "completed",
                 created_at: Optional[datetime] = None):
        self.id = id
        self.account_id = account_id
        self.type = type
        self.amount = amount
        self.description = description
        self.reference = reference
        self.status = status
        self.created_at = created_at