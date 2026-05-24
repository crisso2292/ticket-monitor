import os

import pytest

from ticket_monitor.config import Settings


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("STUBHUB_EVENT_URL", "https://stubhub.com/e/1")
    monkeypatch.setenv("GAMETIME_EVENT_URL", "https://gametime.co/e/1")

    s = Settings()
    assert s.apify_token == "tok"
    assert s.price_threshold == 6000.0
    assert s.min_quantity == 2


def test_settings_missing_required(monkeypatch):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("STUBHUB_EVENT_URL", raising=False)
    monkeypatch.delenv("GAMETIME_EVENT_URL", raising=False)

    with pytest.raises(Exception):
        Settings()
