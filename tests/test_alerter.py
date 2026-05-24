from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ticket_monitor.alerter import send_alert
from ticket_monitor.config import Settings
from ticket_monitor.models import Listing


def _make_config(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "456")
    monkeypatch.setenv("STUBHUB_EVENT_URL", "https://stubhub.com/e/1")
    monkeypatch.setenv("GAMETIME_EVENT_URL", "https://gametime.co/e/1")
    return Settings()


@pytest.mark.asyncio
async def test_send_alert_success(monkeypatch):
    config = _make_config(monkeypatch)
    listing = Listing(
        marketplace="stubhub",
        listing_id="s1",
        price_each=5500.0,
        quantity=2,
        section="100",
        row="A",
        buy_url="https://stubhub.com/s1",
        fetched_at=datetime.now(timezone.utc),
    )

    mock_response = httpx.Response(200, json={"ok": True})
    with patch("ticket_monitor.alerter.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        result = await send_alert(listing, config)

    assert result is True
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "bot123" in call_args[0][0]
    assert call_args[1]["json"]["chat_id"] == "456"


@pytest.mark.asyncio
async def test_send_alert_failure(monkeypatch):
    config = _make_config(monkeypatch)
    listing = Listing(
        marketplace="gametime",
        listing_id="g1",
        price_each=4000.0,
        quantity=3,
        section="200",
        row="B",
        buy_url="https://gametime.co/g1",
        fetched_at=datetime.now(timezone.utc),
    )

    mock_response = httpx.Response(500, text="error")
    with patch("ticket_monitor.alerter.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_cls.return_value = mock_client

        result = await send_alert(listing, config)

    assert result is False
