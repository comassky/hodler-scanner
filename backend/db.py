"""
SQLite persistence — ticker names cache + favorites (watchlist).
Replaces the former flat ``tickers.txt`` file.

The database is stored at ``DB_PATH`` (default ``/app/data/hodler.db``).
"""
import os
import sqlite3
import threading
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "/app/data/hodler.db")

_lock = threading.Lock()


@contextmanager
def _connect():
    """Open a SQLite connection (create the parent folder if needed)."""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the tables if they do not exist."""
    with _lock, _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ticker_names (
                ticker TEXT PRIMARY KEY,
                name   TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS favorites (
                ticker   TEXT PRIMARY KEY,
                position INTEGER NOT NULL DEFAULT 0,
                added_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )


# ── Ticker names cache ──────────────────────────────────────────────
def get_names() -> dict:
    """Return the whole names cache: ``{TICKER: Name}``."""
    with _lock, _connect() as conn:
        rows = conn.execute("SELECT ticker, name FROM ticker_names").fetchall()
    return {t: n for t, n in rows}


def save_names(names: dict) -> None:
    """Insert or update a batch of ticker names."""
    if not names:
        return
    rows = [(t.strip().upper(), str(n).strip()) for t, n in names.items() if t]
    with _lock, _connect() as conn:
        conn.executemany(
            "INSERT INTO ticker_names (ticker, name) VALUES (?, ?) "
            "ON CONFLICT(ticker) DO UPDATE SET name = excluded.name",
            rows,
        )


def upsert_name(ticker: str, name: str) -> None:
    """Insert or update a single ticker name."""
    if not ticker or not name:
        return
    save_names({ticker: name})


# ── Favorites (watchlist) ───────────────────────────────────────────
def get_favorites() -> list:
    """Return the ordered list of favorite tickers."""
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT ticker FROM favorites ORDER BY position, added_at"
        ).fetchall()
    return [r[0] for r in rows]


def add_favorite(ticker: str) -> bool:
    """Add a favorite. Return ``True`` if inserted, ``False`` if it already existed."""
    code = ticker.strip().upper()
    if not code:
        return False
    with _lock, _connect() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO favorites (ticker, position) "
            "VALUES (?, COALESCE((SELECT MAX(position) + 1 FROM favorites), 0))",
            (code,),
        )
        return cur.rowcount > 0


def remove_favorite(ticker: str) -> bool:
    """Remove a favorite. Return ``True`` if it existed."""
    code = ticker.strip().upper()
    with _lock, _connect() as conn:
        cur = conn.execute("DELETE FROM favorites WHERE ticker = ?", (code,))
        return cur.rowcount > 0


def set_favorites(tickers: list) -> list:
    """Fully replace the favorites list (used for import/migration)."""
    seen, ordered = set(), []
    for t in tickers:
        code = t.strip().upper()
        if code and code not in seen:
            seen.add(code)
            ordered.append(code)
    with _lock, _connect() as conn:
        conn.execute("DELETE FROM favorites")
        conn.executemany(
            "INSERT INTO favorites (ticker, position) VALUES (?, ?)",
            [(code, i) for i, code in enumerate(ordered)],
        )
    return ordered
