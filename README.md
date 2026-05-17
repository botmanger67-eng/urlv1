# URL Shortener

A simple, self-hosted URL shortener built with Flask and SQLite. It allows users to submit long URLs and receive a shortened version that redirects to the original. Each shortened URL tracks the number of clicks.

## Features

- Shorten long URLs with a unique, user-friendly path.
- Redirect from short URL to original URL.
- Track click counts for each shortened link.
- Responsive UI using Bootstrap.
- Lightweight SQLite database – no external dependencies.

## Tech Stack

- **Backend:** Python 3, Flask
- **Database:** SQLite (via Python’s `sqlite3`)
- **Frontend:** HTML, CSS (Bootstrap 5)

## Setup

### Prerequisites

- Python 3.7+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/url-shortener.git
   cd url-shortener
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install flask
   ```

4. Initialize the database:
   ```bash
   python init_db.py
   ```
   (If `init_db.py` is not provided, the application will create the database automatically on first run.)

### Running the App

Start the Flask development server:
```bash
python app.py
```

The application will be available at `http://127.0.0.1:5000`.

## Usage

### Shortening a URL

1. Open the web interface at `http://127.0.0.1:5000`.
2. Enter a valid URL (e.g., `https://example.com/very/long/url`).
3. Click the **Shorten** button.
4. Your shortened URL will be displayed (e.g., `http://127.0.0.1:5000/abc123`).

### Redirect

- Visit the shortened URL in any browser; you will be automatically redirected to the original URL.

### Viewing Analytics

- Click counts are stored in the database. A simple dashboard may be included to list all shortened links and their statistics (if implemented). By default, the home page shows your recent shortened URLs.

## API Endpoints (optional)

If the app exposes an API, you can shorten URLs programmatically:

- `POST /shorten` – Submit JSON `{"url": "<long_url>"}` to get a shortened URL.
- `GET /<short_id>` – Redirects to the original URL.

Example using `curl`:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"url":"https://example.com"}' http://127.0.0.1:5000/shorten
```

## Database

The application uses an SQLite database (`urls.db`) with a single table:

```sql
CREATE TABLE urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_url TEXT NOT NULL,
    short_code TEXT NOT NULL UNIQUE,
    clicks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Error Handling

- **Invalid URL:** If the submitted URL is malformed or empty, an error message is shown.
- **Duplicate short codes:** The system generates unique short codes using random hashes; collisions are handled gracefully.
- **Nonexistent short URL:** Visiting an unknown short link returns a 404 error with a friendly message.
- **Database errors:** All database operations are wrapped in try-except blocks; any failure logs an error and returns an appropriate response.

## Deployment

For production, consider:

- Use a production WSGI server such as Gunicorn or Waitress.
- Set `app.config['SECRET_KEY']` to a random value.
- Disable debug mode: `app.run(debug=False)`.
- Use an environment variable for the database path.
- Serve static files via a reverse proxy (nginx, Apache) for better performance.

Example Gunicorn command:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.