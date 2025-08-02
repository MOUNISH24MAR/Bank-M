import pytest
from src.admin import get_all_users, get_all_transactions, get_user_accounts
from src.database import get_db_connection

@pytest.fixture
def setup_db():
    """Setup test database with sample data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create test users
    cursor.executemany(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        [
            ("admin1", "adminpass", "admin"),
            ("user1", "userpass", "user"),
            ("user2", "userpass", "user")
        ]
    )
    
    # Create test accounts
    cursor.executemany(
        "INSERT INTO accounts (user_id, account_number, balance) VALUES (?, ?, ?)",
        [
            (1, "ACADMIN01", 5000.00),
            (2, "ACUSER001", 1000.00),
            (3, "ACUSER002", 2000.00)
        ]
    )
    
    # Create test transactions
    cursor.executemany(
        """INSERT INTO transactions 
        (account_id, type, amount, description) 
        VALUES (?, ?, ?, ?)""",
        [
            (1, "deposit", 5000.00, "Initial deposit"),
            (2, "deposit", 1000.00, "Initial deposit"),
            (3, "deposit", 2000.00, "Initial deposit"),
            (2, "withdrawal", 200.00, "ATM withdrawal")
        ]
    )
    
    conn.commit()
    yield
    conn.close()

def test_get_all_users(setup_db):
    """Test retrieving all users"""
    users = get_all_users()
    assert len(users) == 3
    assert any(user.username == "admin1" for user in users)
    assert any(user.username == "user1" for user in users)

def test_get_all_transactions(setup_db):
    """Test retrieving all transactions"""
    transactions = get_all_transactions()
    assert len(transactions) == 4
    assert any(txn.type == "withdrawal" for txn in transactions)

def test_get_user_accounts(setup_db):
    """Test retrieving user accounts"""
    accounts = get_user_accounts(2)
    assert len(accounts) == 1
    assert accounts[0].account_number == "ACUSER001"