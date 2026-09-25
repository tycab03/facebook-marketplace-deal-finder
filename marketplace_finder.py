from dataclasses import dataclass
from typing import List


@dataclass
class MarketplaceListing:
    title: str
    price: float
    location: str
    url: str
    image_url: str = ""
    description: str = ""


def filter_listings(
    listings: List[MarketplaceListing],
    search_query: str,
    min_price: float = 0,
    max_price: float = 0,
) -> List[MarketplaceListing]:

    query = search_query.lower().strip()

    filtered = []

    for listing in listings:

        if query and query not in listing.title.lower():
            continue

        if listing.price < min_price:
            continue

        if max_price > 0 and listing.price > max_price:
            continue

        filtered.append(listing)

    return filtered
