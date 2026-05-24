from pathlib import Path

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = {"env_file": str(PROJECT_ROOT / ".env"), "env_file_encoding": "utf-8"}

    apify_token: str
    telegram_bot_token: str
    telegram_chat_id: str
    price_threshold: float = 6000.0
    min_quantity: int = 2
    stubhub_event_url: str
    gametime_event_url: str
    data_dir: Path = PROJECT_ROOT / "data"
