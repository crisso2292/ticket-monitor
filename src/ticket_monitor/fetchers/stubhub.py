import logging
from datetime import datetime, timezone

from apify_client import ApifyClientAsync

from ticket_monitor.config import Settings
from ticket_monitor.models import Listing

logger = logging.getLogger(__name__)

ACTOR_ID = "consummate_mandala/stubhub-ticket-price-scraper"


async def fetch_stubhub(config: Settings) -> list[Listing]:
    try:
        client = ApifyClientAsync(config.apify_token)
        run_input = {"eventUrl": config.stubhub_event_url}
        run = await client.actor(ACTOR_ID).call(run_input=run_input, timeout_secs=120)
        items = (await client.dataset(run["defaultDatasetId"]).list_items()).items
    except Exception as exc:
        logger.error("StubHub fetch failed: %s", exc)
        return []

    listings: list[Listing] = []
    now = datetime.now(timezone.utc)

    for item in items:
        try:
            listing_id = item.get("listingId")
            raw_price = item.get("price") or item.get("priceWithFees")
            if not listing_id or raw_price is None:
                logger.warning("Skipping StubHub item with missing listingId or price: %s", item)
                continue
            price = float(raw_price)
            if price > 50000:
                logger.warning("StubHub price $%.0f seems pre-fee or anomalous for listing %s", price, listing_id)
            listings.append(
                Listing(
                    marketplace="stubhub",
                    listing_id=str(listing_id),
                    price_each=price,
                    quantity=int(item.get("quantity", 1)),
                    section=item.get("section"),
                    row=item.get("row"),
                    buy_url=item.get("listingUrl") or config.stubhub_event_url,
                    fetched_at=now,
                )
            )
        except (ValueError, TypeError) as exc:
            logger.warning("Skipping malformed StubHub item: %s", exc)

    logger.info("Fetched %d StubHub listings", len(listings))
    return listings
