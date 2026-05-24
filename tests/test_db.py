from datetime import datetime, timezone
from pathlib import Path

from ticket_monitor.db import init_db, mark_alert_sent, save_listings, was_alert_sent
from ticket_monitor.models import Listing


def test_init_db_creates_tables(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    import sqlite3

    conn = sqlite3.connect(str(db))
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "listings" in tables
    assert "alerts_sent" in tables
    conn.close()


def test_save_and_query_listing(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    listing = Listing(
        marketplace="stubhub",
        listing_id="abc123",
        price_each=5500.0,
        quantity=2,
        section="101",
        row="A",
        buy_url="https://stubhub.com/listing/abc123",
        fetched_at=datetime.now(timezone.utc),
    )
    save_listings([listing], db)

    import sqlite3

    conn = sqlite3.connect(str(db))
    rows = conn.execute("SELECT * FROM listings").fetchall()
    assert len(rows) == 1
    assert rows[0][2] == "abc123"
    conn.close()


def test_save_multiple_listings(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    listings = [
        Listing(
            marketplace="stubhub",
            listing_id=f"id{i}",
            price_each=5000.0 + i,
            quantity=2,
            section="100",
            row="A",
            buy_url=f"https://stubhub.com/{i}",
            fetched_at=datetime.now(timezone.utc),
        )
        for i in range(5)
    ]
    save_listings(listings, db)

    import sqlite3

    conn = sqlite3.connect(str(db))
    count = conn.execute("SELECT count(*) FROM listings").fetchone()[0]
    assert count == 5
    conn.close()


def test_alert_dedup(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    assert not was_alert_sent("stubhub", "x1", db)
    mark_alert_sent("stubhub", "x1", db)
    assert was_alert_sent("stubhub", "x1", db)
    assert not was_alert_sent("gametime", "x1", db)
