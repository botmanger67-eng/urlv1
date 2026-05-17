import sqlite3
from typing import Optional, Tuple
from datetime import datetime
import string
import random

DB_PATH = 'shortener.db'

def get_db() -> sqlite3.Connection:
    """Get a database connection to the configured SQLite database.

    Returns:
        sqlite3.Connection: Database connection object.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to connect to database: {e}")

def init_db() -> None:
    """Initialize the database by creating the required tables if they don't exist."""
    try:
        with get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_url TEXT NOT NULL,
                    short_code TEXT NOT NULL UNIQUE,
                    clicks INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_short_code ON urls(short_code)
            """)
            conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to initialize database: {e}")

def _generate_short_code(length: int = 6) -> str:
    """Generate a random alphanumeric short code.

    Args:
        length (int): Length of the short code (default 6).

    Returns:
        str: Generated short code.
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def create_short_url(original_url: str) -> str:
    """Create a new shortened URL entry and return its short code.

    Args:
        original_url (str): The original long URL.

    Returns:
        str: The generated short code.

    Raises:
        ValueError: If original_url is empty or invalid.
        RuntimeError: If database operation fails.
    """
    if not original_url or not isinstance(original_url, str):
        raise ValueError("original_url must be a non-empty string")

    # Basic URL validation (allow any scheme)
    if not original_url.startswith(('http://', 'https://', 'ftp://')):
        raise ValueError("original_url must start with http://, https://, or ftp://")

    try:
        with get_db() as conn:
            # Generate unique short code with collision check
            short_code = _generate_short_code()
            while conn.execute(
                "SELECT 1 FROM urls WHERE short_code = ?", (short_code,)
            ).fetchone() is not None:
                short_code = _generate_short_code()

            conn.execute(
                "INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
                (original_url, short_code)
            )
            conn.commit()
            return short_code
    except sqlite3.IntegrityError:
        # Very rare collision after retry, retry once more
        return create_short_url(original_url)
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to create shortened URL: {e}")

def get_original_url(short_code: str) -> Optional[str]:
    """Retrieve the original URL for a given short code.

    Args:
        short_code (str): The short code to look up.

    Returns:
        Optional[str]: The original URL if found, else None.

    Raises:
        RuntimeError: If database operation fails.
    """
    if not short_code or not isinstance(short_code, str):
        return None

    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT original_url FROM urls WHERE short_code = ?",
                (short_code,)
            ).fetchone()
            return row['original_url'] if row else None
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to retrieve URL: {e}")

def increment_clicks(short_code: str) -> None:
    """Increment the click count for a given short code.

    Args:
        short_code (str): The short code to update.

    Raises:
        RuntimeError: If database operation fails.
    """
    if not short_code or not isinstance(short_code, str):
        return

    try:
        with get_db() as conn:
            conn.execute(
                "UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?",
                (short_code,)
            )
            conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to increment clicks: {e}")

def get_url_stats(short_code: str) -> Optional[Tuple[str, int, datetime]]:
    """Get statistics for a given short code.

    Args:
        short_code (str): The short code to query.

    Returns:
        Optional[Tuple[str, int, datetime]]: Tuple of (original_url, clicks, created_at) if found, else None.

    Raises:
        RuntimeError: If database operation fails.
    """
    if not short_code or not isinstance(short_code, str):
        return None

    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT original_url, clicks, created_at FROM urls WHERE short_code = ?",
                (short_code,)
            ).fetchone()
            if row:
                return (row['original_url'], row['clicks'], row['created_at'])
            return None
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to retrieve stats: {e}")