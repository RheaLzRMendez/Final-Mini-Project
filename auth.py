"""
auth.py - User accounts engine (SQLite + PBKDF2 Hashing).
Handles database initialization, account registration, and secure authentication checks.
"""

import hashlib
import hmac
import os
import re
import sqlite3

from Database import DB_FILE

ITERATIONS = 200_000
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,20}$")
EMAIL_PATTERN = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
MIN_PASSWORD_LENGTH = 8


def init_user_db():
    """Creates the users table (and migrates older versions if missing the email column)."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                            email TEXT COLLATE NOCASE,
                            salt BLOB NOT NULL,
                            password_hash BLOB NOT NULL)""")
        columns = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
        if "email" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT COLLATE NOCASE")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email "
                     "ON users(email COLLATE NOCASE)")


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)


def register_user(username, email, password, confirm):
    """Registers a new user account. Returns (ok: bool, message: str)."""
    username, email = username.strip(), email.strip()
    if not USERNAME_PATTERN.match(username):
        return False, "Username must be 3 to 20 letters, numbers or underscores."
    if not EMAIL_PATTERN.match(email):
        return False, "Enter a valid email address."
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if password != confirm:
        return False, "The two passwords do not match."

    salt = os.urandom(16)
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT INTO users (username, email, salt, password_hash) "
                         "VALUES (?, ?, ?, ?)",
                         (username, email, salt, hash_password(password, salt)))
    except sqlite3.IntegrityError:
        with sqlite3.connect(DB_FILE) as conn:
            taken = conn.execute("SELECT 1 FROM users WHERE username = ?",
                                 (username,)).fetchone()
        return False, ("That username is already taken." if taken
                       else "That email is already registered.")
    return True, "Account created successfully. You can log in now."


def verify_login(identifier, password):
    """Verifies credentials. Returns matching username if valid, else None."""
    identifier = identifier.strip()
    with sqlite3.connect(DB_FILE) as conn:
        row = conn.execute("SELECT username, salt, password_hash FROM users "
                           "WHERE username = ? OR email = ?",
                           (identifier, identifier)).fetchone()
    if row is None:
        hash_password(password, b"0" * 16)
        return None

    username, salt, stored_hash = row
    if hmac.compare_digest(stored_hash, hash_password(password, salt)):
        return username
    return None