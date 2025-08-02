from decimal import Decimal, InvalidOperation
from typing import Optional

def validate_amount(amount_str: str) -> Optional[Decimal]:
    """Validate and convert amount string to Decimal"""
    try:
        amount = Decimal(amount_str)
        if amount <= 0:
            return None
        return amount
    except (InvalidOperation, ValueError):
        return None

def format_currency(amount: Decimal) -> str:
    """Format Decimal amount as currency string"""
    return f"₹{amount:,.2f}"

def generate_account_number(user_id: int) -> str:
    """Generate account number from user ID"""
    return f"AC{user_id:08d}"