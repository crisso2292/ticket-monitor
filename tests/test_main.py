import sqlite3
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from ticket_monitor.main import main
from ticket_monitor.models import Listing


def _stub_listings(marketplace, count, price_each=5000.0, quantity=2):
    return [
        Listing(
            marketplace=marketplace,
            listing_id=f"{marketplace}_{i}",
            price_each=price_each,
            quantity=quantity,
            section="100",
            row="A",
            buy_url=f"https://example.com/{marketplace}/{i}",
            fetched_at=datetime.now(timezone.utc),
        )
        for i in range(count)
    ]


@pytest.mark.asyncio
async def test_main_full_cycle(monkeypatch, tmp_path):
    monkeypatch.setenv("APIFY_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("STUBHUB_EVENT_URL", "https://stubhub.com/e/1")
    monkeypatch.setenv("GAMETIME_EVENT_URL", "https://gametime.co/e/1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRICE_THRESHOLD", "6000")

    stubhub = _stub_listings("stubhub", 2, price_each=5500.0)
    gametime = _stub_listings("gametime", 1, price_each=4500.0)

    with (
        patch("ticket_monitor.main.fetch_stubhub", new_callable=AsyncMock, return_value=stubhub),
        patch("ticket_monitor.main.fetch_gametime", new_callable=AsyncMock, return_value=gametime),
        patch("ticket_monitor.main.send_alert", new_callable=AsyncMock, return_value=True) as mock_alert,
    ):
        await main()

    assert mock_alert.call_count == 3

    db_path = tmp_path / "prices.db"
    conn = sqlite3.connect(str(db_path))
    listing_count = conn.execute("SELECT count(*) FROM listings").fetchone()[0]
    alert_count = conn.execute("SELECT count(*) FROM alerts_sent").fetchone()[0]
    conn.close()
    assert listing_count == 3
    assert alert_count == 3


@pytest.mark.asyncio
async def test_main_filters_by_price_and_quantity(monkeypatch, tmp_path):
    monkeypatch.setenv("APIFY_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("STUBHUB_EVENT_URL", "https://stubhub.com/e/1")
    monkeypatch.setenv("GAMETIME_EVENT_URL", "https://gametime.co/e/1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRICE_THRESHOLD", "5000")
    monkeypatch.setenv("MIN_QUANTITY", "3")

    too_expensive = _stub_listings("stubhub", 1, price_each=5500.0, quantity=4)
    too_few = _stub_listings("gametime", 1, price_each=4000.0, quantity=1)
    qualifying = _stub_listings("stubhub", 1, price_each=4000.0, quantity=3)
    qualifying[0].listing_id = "qualifying_0"

    all_stubhub = too_expensive + qualifying
    all_gametime = too_few

    with (
        patch("ticket_monitor.main.fetch_stubhub", new_callable=AsyncMock, return_value=all_stubhub),
        patch("ticket_monitor.main.fetch_gametime", new_callable=AsyncMock, return_value=all_gametime),
        patch("ticket_monitor.main.send_alert", new_callable=AsyncMock, return_value=True) as mock_alert,
    ):
        await main()

    assert mock_alert.call_count == 1
    alerted_listing = mock_alert.call_args[0][0]
    assert alerted_listing.listing_id == "qualifying_0"


@pytest.mark.asyncio
async def test_main_deduplicates_alerts(monkeypatch, tmp_path):
    monkeypatch.setenv("APIFY_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("STUBHUB_EVENT_URL", "https://stubhub.com/e/1")
    monkeypatch.setenv("GAMETIME_EVENT_URL", "https://gametime.co/e/1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    listings = _stub_listings("stubhub", 2, price_each=5000.0)

    with (
        patch("ticket_monitor.main.fetch_stubhub", new_callable=AsyncMock, return_value=listings),
        patch("ticket_monitor.main.fetch_gametime", new_callable=AsyncMock, return_value=[]),
        patch("ticket_monitor.main.send_alert", new_callable=AsyncMock, return_value=True) as mock_alert,
    ):
        await main()
        first_count = mock_alert.call_count
        await main()
        second_count = mock_alert.call_count - first_count

    assert first_count == 2
    assert second_count == 0


@pytest.mark.asyncio
async def test_main_records_failure_when_both_empty(monkeypatch, tmp_path):
    monkeypatch.setenv("APIFY_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("STUBHUB_EVENT_URL", "https://stubhub.com/e/1")
    monkeypatch.setenv("GAMETIME_EVENT_URL", "https://gametime.co/e/1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    with (
        patch("ticket_monitor.main.fetch_stubhub", new_callable=AsyncMock, return_value=[]),
        patch("ticket_monitor.main.fetch_gametime", new_callable=AsyncMock, return_value=[]),
        patch("ticket_monitor.main.record_failure", new_callable=AsyncMock) as mock_fail,
        patch("ticket_monitor.main.record_success", new_callable=AsyncMock) as mock_success,
    ):
        await main()

    mock_fail.assert_called_once()
    mock_success.assert_not_called()
