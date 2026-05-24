import logging
from datetime import datetime, timezone

from apify_client import ApifyClientAsync

from ticket_monitor.config import Settings
from ticket_monitor.models import Listing

logger = logging.getLogger(__name__)

ACTOR_ID = "lexis-solutions/gametime-scraper"


async def fetch_gametime(config: Settings) -> list[Listing]:
    try:
        client = ApifyClientAsync(config.apify_token)
        run_input = {"urls": [config.gametime_event_url]}
        run = await client.actor(ACTOR_ID).call(run_input=run_input, timeout_secs=120)
        items = (await client.dataset(run["defaultDatasetId"]).list_items()).items
    except Exception as exc:
        logger.error("Gametime fetch failed: %s", exc)
        return []

    listings: list[Listing] = []
    now = datetime.now(timezone.utc)

    for item in items:
        try:
            listing_id = item.get("id") or item.get("listingId")
            raw_price = item.get("price") or item.get("totalPrice")
            if not listing_id or raw_price is None:
                logger.warning("Skipping Gametime item with missing id or price: %s", item)
                continue
            price = float(raw_price)
            listings.append(
                Listing(
                    marketplace="gametime",
                    listing_id=str(listing_id),
                    price_each=price,
                    quantity=int(item.get("quantity", 1)),
                    section=item.get("section"),
                    row=item.get("row"),
                    buy_url=item.get("url") or config.gametime_event_url,
                    fetched_at=now,
                )
            )
        except (ValueError, TypeError) as exc:
            logger.warning("Skipping malformed Gametime item: %s", exc)

    logger.info("Fetched %d Gametime listings", len(listings))
    return listings
