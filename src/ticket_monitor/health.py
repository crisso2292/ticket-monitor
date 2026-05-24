import json
import logging
from pathlib import Path

from ticket_monitor.alerter import send_health_alert
from ticket_monitor.config import Settings

logger = logging.getLogger(__name__)

HEALTH_FILENAME = "health.json"
FAILURE_THRESHOLD = 3


def _health_path(config: Settings) -> Path:
    return config.data_dir / HEALTH_FILENAME


def _read_health(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {"consecutive_failures": 0, "alerted": False}


def _write_health(state: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state))


async def record_success(config: Settings) -> None:
    _write_health({"consecutive_failures": 0, "alerted": False}, _health_path(config))


async def record_failure(config: Settings) -> None:
    path = _health_path(config)
    state = _read_health(path)
    state["consecutive_failures"] += 1
    if state["consecutive_failures"] >= FAILURE_THRESHOLD and not state["alerted"]:
        logger.warning("Monitor has failed %d consecutive times, sending health alert", state["consecutive_failures"])
        sent = await send_health_alert(config, f"⚠️ Monitor down — {state['consecutive_failures']} consecutive fetch failures")
        if sent:
            state["alerted"] = True
    _write_health(state, path)
