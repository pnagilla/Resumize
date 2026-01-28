import sqlite3
import hashlib
import secrets
import os
from datetime import datetime
from typing import Optional

DATABASE_PATH = "../data/resumize.db"


def get_connection():
    """Get database connection."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_users_table():
    """Initialize users table."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt."""
    salt = "resumize_salt_2024"  # In production, use unique salt per user
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def generate_token() -> str:
    """Generate a random token."""
    return secrets.token_urlsafe(32)


def create_user(name: str, username: str, email: str, password: str) -> Optional[dict]:
    """Create a new user."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (name, username, email, password_hash) VALUES (?, ?, ?, ?)",
            (name, username.lower(), email.lower(), password_hash)
        )
        user_id = cursor.lastrowid

        # Generate token
        token = generate_token()
        cursor.execute(
            "INSERT INTO tokens (user_id, token) VALUES (?, ?)",
            (user_id, token)
        )

        conn.commit()

        return {
            "user": {
                "id": user_id,
                "name": name,
                "username": username.lower(),
                "email": email.lower()
            },
            "token": token
        }
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate a user and return user data with token."""
    conn = get_connection()
    cursor = conn.cursor()

    password_hash = hash_password(password)
    cursor.execute(
        "SELECT id, name, username, email FROM users WHERE email = ? AND password_hash = ?",
        (email.lower(), password_hash)
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    user_id = row["id"]

    # Generate new token
    token = generate_token()
    cursor.execute(
        "INSERT INTO tokens (user_id, token) VALUES (?, ?)",
        (user_id, token)
    )
    conn.commit()
    conn.close()

    return {
        "user": {
            "id": user_id,
            "name": row["name"],
            "username": row["username"],
            "email": row["email"]
        },
        "token": token
    }


def validate_token(token: str) -> Optional[dict]:
    """Validate a token and return user data."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id, u.name, u.username, u.email
        FROM users u
        JOIN tokens t ON u.id = t.user_id
        WHERE t.token = ?
    """, (token,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "username": row["username"],
        "email": row["email"]
    }


def delete_token(token: str) -> bool:
    """Delete a token (logout)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tokens WHERE token = ?", (token,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return deleted


# Initialize users table on module load
init_users_table()
