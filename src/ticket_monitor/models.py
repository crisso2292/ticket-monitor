from dataclasses import dataclass
from datetime import datetime


@dataclass
class Listing:
    marketplace: str
    listing_id: str
    price_each: float
    quantity: int
    section: str | None
    row: str | None
    buy_url: str
    fetched_at: datetime
