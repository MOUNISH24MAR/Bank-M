import pytest
from decimal import Decimal
from src.transactions import deposit, withdraw, get_account_balance
from src.database import get_db_connection

@pytest.fixture
def setup_db():
    """Setup test database with an account"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create test user and account
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        ("txnuser", "txnpass")
    )
    user_id = cursor.lastrowid
    
    cursor.execute(
        "INSERT INTO accounts (user_id, account_number, balance) VALUES (?, ?, ?)",
        (user_id, "ACTXN0001", 1000.00)
    )
    account_id = cursor.lastrowid
    
    conn.commit()
    yield account_id
    conn.close()

def test_deposit_success(setup_db):
    """Test successful deposit"""
    account_id = setup_db
    assert deposit(account_id, Decimal("500.00"), "Test deposit")
    balance = get_account_balance(account_id)
    assert balance == Decimal("1500.00")

def test_deposit_invalid_amount(setup_db):
    """Test deposit with invalid amount"""
    account_id = setup_db
    assert not deposit(account_id, Decimal("-100.00"))
    assert not deposit(account_id, Decimal("0.00"))

def test_withdraw_success(setup_db):
    """Test successful withdrawal"""
    account_id = setup_db
    assert withdraw(account_id, Decimal("200.00"), "Test withdrawal")
    balance = get_account_balance(account_id)
    assert balance == Decimal("800.00")

def test_withdraw_insufficient_funds(setup_db):
    """Test withdrawal with insufficient funds"""
    account_id = setup_db
    assert not withdraw(account_id, Decimal("2000.00"))
    balance = get_account_balance(account_id)
    assert balance == Decimal("1000.00")  # Balance unchanged