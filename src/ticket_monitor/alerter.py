import logging

import httpx

from ticket_monitor.config import Settings
from ticket_monitor.models import Listing

logger = logging.getLogger(__name__)


async def send_alert(listing: Listing, config: Settings) -> bool:
    text = (
        f"🎫 PRICE ALERT: ${listing.price_each:,.0f}/each\n\n"
        f"FIFA World Cup Final\n"
        f"📍 Section {listing.section or '?'}, Row {listing.row or '?'}\n"
        f"🎟️ {listing.quantity} tickets available\n"
        f"🏪 {listing.marketplace.title()}\n\n"
        f"🔗 {listing.buy_url}"
    )

    url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": config.telegram_chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                logger.info("Alert sent for %s listing %s", listing.marketplace, listing.listing_id)
                return True
            logger.error("Telegram API returned %d: %s", resp.status_code, resp.text)
            return False
        except httpx.HTTPError as exc:
            logger.error("Telegram request failed: %s", exc)
            return False


async def send_health_alert(config: Settings, message: str) -> bool:
    url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": config.telegram_chat_id,
        "text": message,
        "disable_web_page_preview": True,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
        except httpx.HTTPError:
            return False
