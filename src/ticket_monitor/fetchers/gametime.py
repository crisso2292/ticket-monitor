import logging
from datetime import datetime, timedelta, timezone

from apify_client import ApifyClientAsync

from ticket_monitor.config import Settings
from ticket_monitor.models import Listing

logger = logging.getLogger(__name__)

ACTOR_ID = "lexis-solutions/gametime-scraper"


async def fetch_gametime(config: Settings) -> list[Listing]:
    try:
        client = ApifyClientAsync(config.apify_token)
        run_input = {"startUrls": [{"url": config.gametime_event_url}]}
        run = await client.actor(ACTOR_ID).call(run_input=run_input, run_timeout=timedelta(seconds=120))
        items = (await client.dataset(run.default_dataset_id).list_items()).items
    except Exception as exc:
        logger.error("Gametime fetch failed: %s", exc)
        return []

    listings: list[Listing] = []
    now = datetime.now(timezone.utc)

    for item in items:
        ticket_listings = item.get("listings", [])
        if not ticket_listings:
            continue
        for ticket in ticket_listings:
            try:
                listing_id = ticket.get("listingId")
                price_cents = ticket.get("priceCents")
                if not listing_id or price_cents is None:
                    continue
                price = float(price_cents) / 100.0
                listings.append(
                    Listing(
                        marketplace="gametime",
                        listing_id=str(listing_id),
                        price_each=price,
                        quantity=int(ticket.get("seats", 1)),
                        section=ticket.get("section"),
                        row=ticket.get("row"),
                        buy_url=ticket.get("url") or config.gametime_event_url,
                        fetched_at=now,
                    )
                )
            except (ValueError, TypeError) as exc:
                logger.warning("Skipping malformed Gametime item: %s", exc)

    logger.info("Fetched %d Gametime listings", len(listings))
    return listings
