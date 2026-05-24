import asyncio
import logging
import sys

from ticket_monitor.alerter import send_alert
from ticket_monitor.config import Settings
from ticket_monitor.db import DB_NAME, init_db, mark_alert_sent, save_listings, was_alert_sent
from ticket_monitor.fetchers.gametime import fetch_gametime
from ticket_monitor.fetchers.stubhub import fetch_stubhub
from ticket_monitor.health import record_failure, record_success

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config = Settings()
    db_path = config.data_dir / DB_NAME
    init_db(db_path)

    stubhub_listings, gametime_listings = await asyncio.gather(
        fetch_stubhub(config),
        fetch_gametime(config),
    )

    all_listings = stubhub_listings + gametime_listings

    if not stubhub_listings and not gametime_listings:
        await record_failure(config)
    else:
        await record_success(config)

    alerts_sent = 0
    for listing in all_listings:
        if listing.price_each < config.price_threshold and listing.quantity >= config.min_quantity:
            if not was_alert_sent(listing.marketplace, listing.listing_id, db_path):
                success = await send_alert(listing, config)
                if success:
                    mark_alert_sent(listing.marketplace, listing.listing_id, db_path)
                    alerts_sent += 1

    save_listings(all_listings, db_path)

    logger.info(
        "Cycle complete: %d listings fetched (%d StubHub, %d Gametime), %d alerts sent",
        len(all_listings),
        len(stubhub_listings),
        len(gametime_listings),
        alerts_sent,
    )


def cli() -> None:
    try:
        asyncio.run(asyncio.wait_for(main(), timeout=180))
    except TimeoutError:
        logger.error("Global timeout (180s) exceeded")
        sys.exit(1)


if __name__ == "__main__":
    cli()
