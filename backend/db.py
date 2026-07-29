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
            CREATE TABLE IF NOT EXISTS backtest_scores (
                ticker TEXT NOT NULL,
                date   TEXT NOT NULL,
                price  REAL NOT NULL,
                score  INTEGER NOT NULL,
                sma200 REAL,
                PRIMARY KEY (ticker, date)
            );
            CREATE TABLE IF NOT EXISTS positions (
                ticker     TEXT PRIMARY KEY,
                quantity   REAL NOT NULL,
                avg_cost   REAL NOT NULL,
                note       TEXT,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        # Migration: add sma200 to pre-existing backtest_scores tables.
        cols = {r[1] for r in conn.execute("PRAGMA table_info(backtest_scores)").fetchall()}
        if "sma200" not in cols:
            conn.execute("ALTER TABLE backtest_scores ADD COLUMN sma200 REAL")


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


# ── Backtest scores (deterministic per-date cache) ──────────────────
def get_backtest_scores(ticker: str) -> dict:
    """Return stored scores for a ticker: ``{date: (price, score, sma200)}``."""
    code = ticker.strip().upper()
    if not code:
        return {}
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT date, price, score, sma200 FROM backtest_scores WHERE ticker = ?",
            (code,),
        ).fetchall()
    return {d: (p, s, sma) for d, p, s, sma in rows}


def save_backtest_scores(ticker: str, rows: list) -> None:
    """Upsert a batch of ``(date, price, score, sma200)`` rows for a ticker."""
    code = ticker.strip().upper()
    if not code or not rows:
        return
    payload = [
        (code, str(d), float(p), int(s), None if sma is None else float(sma))
        for d, p, s, sma in rows
    ]
    with _lock, _connect() as conn:
        conn.executemany(
            "INSERT INTO backtest_scores (ticker, date, price, score, sma200) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(ticker, date) DO UPDATE SET "
            "price = excluded.price, score = excluded.score, sma200 = excluded.sma200",
            payload,
        )


# ── Positions (portfolio) ──────────────────────────────────
def get_positions() -> list:
    """Return the stored positions: ``[{ticker, quantity, avg_cost, note, updated_at}]``."""
    with _lock, _connect() as conn:
        rows = conn.execute(
            "SELECT ticker, quantity, avg_cost, note, updated_at "
            "FROM positions ORDER BY updated_at DESC"
        ).fetchall()
    return [
        {"ticker": t, "quantity": q, "avg_cost": a, "note": n, "updated_at": u}
        for t, q, a, n, u in rows
    ]


def upsert_position(ticker: str, quantity: float, avg_cost: float, note: str | None = None) -> None:
    """Insert or update a single position (one aggregated lot per ticker)."""
    code = ticker.strip().upper()
    if not code:
        return
    clean_note = (note or "").strip() or None
    with _lock, _connect() as conn:
        conn.execute(
            "INSERT INTO positions (ticker, quantity, avg_cost, note) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(ticker) DO UPDATE SET quantity = excluded.quantity, "
            "avg_cost = excluded.avg_cost, note = excluded.note, updated_at = datetime('now')",
            (code, float(quantity), float(avg_cost), clean_note),
        )


def remove_position(ticker: str) -> bool:
    """Remove a position. Return ``True`` if it existed."""
    code = ticker.strip().upper()
    with _lock, _connect() as conn:
        cur = conn.execute("DELETE FROM positions WHERE ticker = ?", (code,))
        return cur.rowcount > 0


# ── Maintenance ─────────────────────────────────────────────────────
def reset_data(
    favorites: bool = False,
    positions: bool = False,
    backtest_scores: bool = False,
    ticker_names: bool = False,
) -> dict:
    """Delete rows from the selected tables only. Return rows deleted per table.

    Each flag maps to a table: ``favorites`` (watchlist), ``positions``
    (portfolio), ``backtest_scores`` (stored backtests) and ``ticker_names``
    (the name/ISIN lookup dictionary). Unselected tables are left untouched.
    """
    wanted = {
        "favorites": favorites,
        "positions": positions,
        "backtest_scores": backtest_scores,
        "ticker_names": ticker_names,
    }
    tables = [name for name, on in wanted.items() if on]
    counts: dict = {}
    if not tables:
        return counts
    with _lock, _connect() as conn:
        for table in tables:
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            conn.execute(f"DELETE FROM {table}")
            counts[table] = n
    return counts

