from flask import Flask, request, redirect, render_template, abort, jsonify, url_for
import sqlite3
import string
import random
import datetime
from typing import Optional, Tuple

app = Flask(__name__)
DATABASE = 'urls.db'

def get_db() -> sqlite3.Connection:
    """Return a database connection with row factory set."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Create the urls table if it doesn't exist."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_url TEXT NOT NULL,
                short_code TEXT UNIQUE NOT NULL,
                clicks INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def generate_short_code(length: int = 6) -> str:
    """Generate a random alphanumeric short code of given length."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def get_short_code(original_url: str) -> Optional[str]:
    """Retrieve existing short code for a URL, return None if not found."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT short_code FROM urls WHERE original_url = ?', (original_url,))
        row = cursor.fetchone()
        return row['short_code'] if row else None
    except sqlite3.Error:
        return None
    finally:
        if conn:
            conn.close()

def insert_url(original_url: str, short_code: str) -> bool:
    """Insert a new URL record. Returns True on success, False on failure."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO urls (original_url, short_code, clicks, created_at) VALUES (?, ?, 0, ?)',
            (original_url, short_code, datetime.datetime.utcnow().isoformat())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # short_code collision – extremely unlikely, but safe
        return False
    except sqlite3.Error:
        return False
    finally:
        if conn:
            conn.close()

def get_original_url(short_code: str) -> Optional[Tuple[str, int]]:
    """
    Retrieve original URL and click count for a short code.
    Returns (original_url, clicks) if found, else None.
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT original_url, clicks FROM urls WHERE short_code = ?', (short_code,))
        row = cursor.fetchone()
        return (row['original_url'], row['clicks']) if row else None
    except sqlite3.Error:
        return None
    finally:
        if conn:
            conn.close()

def increment_clicks(short_code: str) -> bool:
    """Increment click count by 1 for a given short code."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?', (short_code,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        return False
    finally:
        if conn:
            conn.close()

@app.route('/')
def index():
    """Render the main page with the URL submission form."""
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten():
    """Handle URL shortening request and return the short URL. JSON response for API usage."""
    original_url = request.form.get('url') or request.json.get('url')
    if not original_url:
        abort(400, description="Missing URL parameter")
    
    # Validate URL (basic)
    if not original_url.startswith(('http://', 'https://')):
        abort(400, description="Invalid URL: must start with http:// or https://")
    
    # Check if already shortened
    existing_code = get_short_code(original_url)
    if existing_code:
        short_url = url_for('redirect_to_url', short_code=existing_code, _external=True)
        if request.is_json:
            return jsonify({'original_url': original_url, 'short_url': short_url})
        return render_template('index.html', short_url=short_url)
    
    # Generate unique short code
    max_attempts = 10
    for _ in range(max_attempts):
        code = generate_short_code()
        if insert_url(original_url, code):
            short_url = url_for('redirect_to_url', short_code=code, _external=True)
            if request.is_json:
                return jsonify({'original_url': original_url, 'short_url': short_url})
            return render_template('index.html', short_url=short_url)
    
    # Should not happen, but handle gracefully
    abort(500, description="Failed to generate a unique short code. Please try again.")

@app.route('/<short_code>')
def redirect_to_url(short_code: str):
    """Redirect to the original URL and increment click count."""
    record = get_original_url(short_code)
    if not record:
        abort(404, description="Short URL not found")
    
    original_url, clicks = record
    if not increment_clicks(short_code):
        # non-critical: log but still redirect
        app.logger.warning(f"Failed to increment clicks for {short_code}")
    
    return redirect(original_url, code=302)

@app.errorhandler(404)
def not_found(error):
    """Return a 404 error page."""
    if request.is_json:
        return jsonify({'error': 'Not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Return a 500 error page."""
    if request.is_json:
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=False)