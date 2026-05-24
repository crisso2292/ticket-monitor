import json
from unittest.mock import AsyncMock, patch

import pytest

from ticket_monitor.config import Settings
from ticket_monitor.health import _health_path, record_failure, record_success


def _make_config(monkeypatch, tmp_path):
    monkeypatch.setenv("APIFY_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setenv("STUBHUB_EVENT_URL", "https://stubhub.com/e/1")
    monkeypatch.setenv("GAMETIME_EVENT_URL", "https://gametime.co/e/1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    return Settings()


@pytest.mark.asyncio
async def test_record_success_resets_failures(monkeypatch, tmp_path):
    config = _make_config(monkeypatch, tmp_path)
    hf = _health_path(config)
    hf.parent.mkdir(parents=True, exist_ok=True)
    hf.write_text(json.dumps({"consecutive_failures": 2, "alerted": False}))

    await record_success(config)

    state = json.loads(hf.read_text())
    assert state["consecutive_failures"] == 0
    assert state["alerted"] is False


@pytest.mark.asyncio
async def test_record_failure_triggers_alert_at_threshold(monkeypatch, tmp_path):
    config = _make_config(monkeypatch, tmp_path)
    hf = _health_path(config)
    hf.parent.mkdir(parents=True, exist_ok=True)
    hf.write_text(json.dumps({"consecutive_failures": 2, "alerted": False}))

    with patch("ticket_monitor.health.send_health_alert", new_callable=AsyncMock, return_value=True) as mock_alert:
        await record_failure(config)

    mock_alert.assert_called_once()
    state = json.loads(hf.read_text())
    assert state["consecutive_failures"] == 3
    assert state["alerted"] is True


@pytest.mark.asyncio
async def test_record_failure_no_double_alert(monkeypatch, tmp_path):
    config = _make_config(monkeypatch, tmp_path)
    hf = _health_path(config)
    hf.parent.mkdir(parents=True, exist_ok=True)
    hf.write_text(json.dumps({"consecutive_failures": 5, "alerted": True}))

    with patch("ticket_monitor.health.send_health_alert", new_callable=AsyncMock) as mock_alert:
        await record_failure(config)

    mock_alert.assert_not_called()
    state = json.loads(hf.read_text())
    assert state["consecutive_failures"] == 6


@pytest.mark.asyncio
async def test_record_failure_retries_if_alert_send_fails(monkeypatch, tmp_path):
    config = _make_config(monkeypatch, tmp_path)
    hf = _health_path(config)
    hf.parent.mkdir(parents=True, exist_ok=True)
    hf.write_text(json.dumps({"consecutive_failures": 2, "alerted": False}))

    with patch("ticket_monitor.health.send_health_alert", new_callable=AsyncMock, return_value=False):
        await record_failure(config)

    state = json.loads(hf.read_text())
    assert state["consecutive_failures"] == 3
    assert state["alerted"] is False
