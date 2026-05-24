import sqlite3
from contextlib import contextmanager
from pathlib import Path

from ticket_monitor.models import Listing

DB_NAME = "prices.db"


@contextmanager
def _connect(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Path) -> None:
    with _connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                marketplace TEXT NOT NULL,
                listing_id TEXT NOT NULL,
                price_each REAL NOT NULL,
                quantity INTEGER NOT NULL,
                section TEXT,
                row TEXT,
                buy_url TEXT NOT NULL,
                fetched_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alerts_sent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                marketplace TEXT NOT NULL,
                listing_id TEXT NOT NULL,
                sent_at TEXT NOT NULL,
                UNIQUE(marketplace, listing_id)
            );
        """)


def save_listings(listings: list[Listing], db_path: Path) -> None:
    with _connect(db_path) as conn:
        conn.executemany(
            """INSERT INTO listings (marketplace, listing_id, price_each, quantity, section, row, buy_url, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    l.marketplace,
                    l.listing_id,
                    l.price_each,
                    l.quantity,
                    l.section,
                    l.row,
                    l.buy_url,
                    l.fetched_at.isoformat(),
                )
                for l in listings
            ],
        )
        conn.commit()


def was_alert_sent(marketplace: str, listing_id: str, db_path: Path) -> bool:
    with _connect(db_path) as conn:
        cur = conn.execute(
            "SELECT 1 FROM alerts_sent WHERE marketplace = ? AND listing_id = ?",
            (marketplace, listing_id),
        )
        return cur.fetchone() is not None


def mark_alert_sent(marketplace: str, listing_id: str, db_path: Path) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO alerts_sent (marketplace, listing_id, sent_at) VALUES (?, ?, datetime('now'))",
            (marketplace, listing_id),
        )
        conn.commit()
