from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ticket_monitor.config import Settings
from ticket_monitor.fetchers.gametime import fetch_gametime
from ticket_monitor.fetchers.stubhub import fetch_stubhub


def _make_config(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("STUBHUB_EVENT_URL", "https://stubhub.com/e/1")
    monkeypatch.setenv("GAMETIME_EVENT_URL", "https://gametime.co/e/1")
    return Settings()


@pytest.mark.asyncio
async def test_fetch_stubhub_parses_items(monkeypatch):
    config = _make_config(monkeypatch)

    mock_items = [
        {
            "listingId": "sh1",
            "price": 5200.0,
            "quantity": 2,
            "section": "200",
            "row": "B",
            "listingUrl": "https://stubhub.com/listing/sh1",
        }
    ]

    mock_dataset = AsyncMock()
    mock_dataset.list_items.return_value = MagicMock(items=mock_items)

    mock_actor = AsyncMock()
    mock_actor.call.return_value = {"defaultDatasetId": "ds1"}

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.return_value = mock_dataset

    with patch("ticket_monitor.fetchers.stubhub.ApifyClientAsync", return_value=mock_client):
        listings = await fetch_stubhub(config)

    assert len(listings) == 1
    assert listings[0].marketplace == "stubhub"
    assert listings[0].listing_id == "sh1"
    assert listings[0].price_each == 5200.0
    assert listings[0].quantity == 2


@pytest.mark.asyncio
async def test_fetch_stubhub_returns_empty_on_failure(monkeypatch):
    config = _make_config(monkeypatch)

    with patch("ticket_monitor.fetchers.stubhub.ApifyClientAsync", side_effect=RuntimeError("network")):
        listings = await fetch_stubhub(config)

    assert listings == []


@pytest.mark.asyncio
async def test_fetch_gametime_parses_items(monkeypatch):
    config = _make_config(monkeypatch)

    mock_items = [
        {
            "id": "gt1",
            "price": 4800.0,
            "quantity": 3,
            "section": "105",
            "row": "C",
            "url": "https://gametime.co/listing/gt1",
        }
    ]

    mock_dataset = AsyncMock()
    mock_dataset.list_items.return_value = MagicMock(items=mock_items)

    mock_actor = AsyncMock()
    mock_actor.call.return_value = {"defaultDatasetId": "ds2"}

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.return_value = mock_dataset

    with patch("ticket_monitor.fetchers.gametime.ApifyClientAsync", return_value=mock_client):
        listings = await fetch_gametime(config)

    assert len(listings) == 1
    assert listings[0].marketplace == "gametime"
    assert listings[0].listing_id == "gt1"
    assert listings[0].price_each == 4800.0


@pytest.mark.asyncio
async def test_fetch_gametime_returns_empty_on_failure(monkeypatch):
    config = _make_config(monkeypatch)

    with patch("ticket_monitor.fetchers.gametime.ApifyClientAsync", side_effect=RuntimeError("timeout")):
        listings = await fetch_gametime(config)

    assert listings == []


@pytest.mark.asyncio
async def test_fetch_stubhub_skips_items_missing_id_or_price(monkeypatch):
    config = _make_config(monkeypatch)

    mock_items = [
        {"price": 5000.0, "quantity": 2},
        {"listingId": "sh2", "quantity": 2},
        {"listingId": "sh3", "price": 4500.0, "quantity": 2, "section": "A", "row": "1", "listingUrl": "https://stubhub.com/sh3"},
    ]

    mock_dataset = AsyncMock()
    mock_dataset.list_items.return_value = MagicMock(items=mock_items)

    mock_actor = AsyncMock()
    mock_actor.call.return_value = {"defaultDatasetId": "ds1"}

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.return_value = mock_dataset

    with patch("ticket_monitor.fetchers.stubhub.ApifyClientAsync", return_value=mock_client):
        listings = await fetch_stubhub(config)

    assert len(listings) == 1
    assert listings[0].listing_id == "sh3"


@pytest.mark.asyncio
async def test_fetch_gametime_skips_items_missing_id_or_price(monkeypatch):
    config = _make_config(monkeypatch)

    mock_items = [
        {"price": 3000.0, "quantity": 2},
        {"id": "gt2", "quantity": 2},
        {"id": "gt3", "price": 4000.0, "quantity": 3, "section": "B", "row": "2", "url": "https://gametime.co/gt3"},
    ]

    mock_dataset = AsyncMock()
    mock_dataset.list_items.return_value = MagicMock(items=mock_items)

    mock_actor = AsyncMock()
    mock_actor.call.return_value = {"defaultDatasetId": "ds2"}

    mock_client = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_client.dataset.return_value = mock_dataset

    with patch("ticket_monitor.fetchers.gametime.ApifyClientAsync", return_value=mock_client):
        listings = await fetch_gametime(config)

    assert len(listings) == 1
    assert listings[0].listing_id == "gt3"
