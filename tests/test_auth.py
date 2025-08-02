import pytest
from src.auth import authenticate_user, register_user
from src.database import get_db_connection

@pytest.fixture
def setup_db():
    """Setup test database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create test tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        full_name TEXT,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        account_number TEXT UNIQUE NOT NULL,
        balance REAL DEFAULT 0,
        account_type TEXT DEFAULT 'savings',
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    # Add test user
    cursor.execute(
        "INSERT INTO users (username, password, full_name) VALUES (?, ?, ?)",
        ("testuser", "testpass", "Test User")
    )
    user_id = cursor.lastrowid
    
    cursor.execute(
        "INSERT INTO accounts (user_id, account_number) VALUES (?, ?)",
        (user_id, "AC00000001")
    )
    
    conn.commit()
    yield
    conn.close()

def test_authenticate_user_success(setup_db):
    """Test successful authentication"""
    user = authenticate_user("testuser", "testpass")
    assert user is not None
    assert user.username == "testuser"
    assert user.full_name == "Test User"

def test_authenticate_user_failure(setup_db):
    """Test failed authentication"""
    assert authenticate_user("testuser", "wrongpass") is None
    assert authenticate_user("nonexistent", "testpass") is None

def test_register_user_success(setup_db):
    """Test successful user registration"""
    user = register_user("newuser", "newpass", "New User", "new@example.com")
    assert user is not None
    assert user.username == "newuser"
    assert user.email == "new@example.com"

def test_register_user_duplicate(setup_db):
    """Test duplicate username registration"""
    register_user("duplicate", "pass", "Duplicate User")
    assert register_user("duplicate", "pass") is None