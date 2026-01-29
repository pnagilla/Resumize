import sqlite3
import hashlib
import secrets
import os
import logging
from datetime import datetime
from typing import Optional

import bcrypt

logger = logging.getLogger(__name__)

DATABASE_PATH = os.getenv("DATABASE_PATH", "../data/resumize.db")


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
    """Hash a password using bcrypt with per-user salt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash. Supports bcrypt and legacy SHA-256."""
    # bcrypt hashes start with $2b$
    if password_hash.startswith("$2b$"):
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    else:
        # Legacy SHA-256 fallback for existing accounts
        legacy_salt = "resumize_salt_2024"
        legacy_hash = hashlib.sha256(f"{password}{legacy_salt}".encode()).hexdigest()
        return secrets.compare_digest(legacy_hash, password_hash)


def _upgrade_password_hash(user_id: int, password: str):
    """Upgrade a legacy SHA-256 hash to bcrypt on successful login."""
    conn = get_connection()
    cursor = conn.cursor()
    new_hash = hash_password(password)
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (new_hash, user_id)
    )
    conn.commit()
    conn.close()


def generate_token() -> str:
    """Generate a random token."""
    return secrets.token_urlsafe(32)


def create_user(name: str, username: str, email: str, password: str) -> Optional[dict]:
    """Create a new user."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        pw_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (name, username, email, password_hash) VALUES (?, ?, ?, ?)",
            (name, username.lower(), email.lower(), pw_hash)
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

    # Fetch user by email only (verify password in Python for constant-time comparison)
    cursor.execute(
        "SELECT id, name, username, email, password_hash FROM users WHERE email = ?",
        (email.lower(),)
    )
    row = cursor.fetchone()

    if not row:
        # Perform a dummy hash to prevent timing attacks on user enumeration
        bcrypt.hashpw(b"dummy_password", bcrypt.gensalt(rounds=4))
        conn.close()
        return None

    if not verify_password(password, row["password_hash"]):
        conn.close()
        return None

    user_id = row["id"]

    # Upgrade legacy SHA-256 hashes to bcrypt on successful login
    if not row["password_hash"].startswith("$2b$"):
        try:
            _upgrade_password_hash(user_id, password)
        except Exception:
            pass  # Non-critical, will upgrade on next login

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
