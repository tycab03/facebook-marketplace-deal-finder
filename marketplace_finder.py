from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class MarketplaceListing:
    title: str
    price: float
    location: str
    url: str
    image_url: str = ""
    description: str = ""


def clean_price(price_text: str) -> Optional[float]:
    """
    Convert price text into a number.

    Examples:
    "$1,200" -> 1200.0
    "$850" -> 850.0
    "Free" -> 0.0
    """

    if not price_text:
        return None

    price_text = price_text.strip()

    if price_text.lower() == "free":
        return 0.0

    cleaned = re.sub(r"[^\d.]", "", price_text)

    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def filter_listings(
    listings: List[MarketplaceListing],
    search_query: str,
    min_price: float = 0,
    max_price: float = 0,
    location: str = "",
) -> List[MarketplaceListing]:
    """
    Filter listings by search term, price and location.
    """

    query = search_query.lower().strip()
    location_query = location.lower().strip()

    results = []

    for listing in listings:

        if query and query not in listing.title.lower():
            continue

        if listing.price < min_price:
            continue

        if max_price > 0 and listing.price > max_price:
            continue

        if location_query and location_query not in listing.location.lower():
            continue

        results.append(listing)

    return results