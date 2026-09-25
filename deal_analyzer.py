from statistics import median
from typing import List

from marketplace_finder import MarketplaceListing


def estimate_market_value(
    listings: List[MarketplaceListing],
) -> float:
    """
    Estimate market value using the median asking
    price of the collected Marketplace listings.
    """

    prices = [
        listing.price
        for listing in listings
        if listing.price > 0
    ]

    if not prices:
        return 0.0

    return round(
        median(prices),
        2,
    )


def calculate_deal(
    listing_price: float,
    estimated_value: float,
) -> dict:
    """
    Compare a listing's asking price against
    estimated market value.
    """

    if estimated_value <= 0:

        return {
            "estimated_value": 0,
            "saving": 0,
            "discount_percent": 0,
            "deal_score": 0,
        }

    saving = (
        estimated_value
        - listing_price
    )

    discount_percent = (
        saving
        / estimated_value
    ) * 100

    # 50% below estimated value = score of 10.
    deal_score = (
        discount_percent / 5
    )

    deal_score = max(
        0,
        min(
            10,
            deal_score,
        ),
    )

    return {
        "estimated_value": round(
            estimated_value,
            2,
        ),
        "saving": round(
            saving,
            2,
        ),
        "discount_percent": round(
            discount_percent,
            1,
        ),
        "deal_score": round(
            deal_score,
            1,
        ),
    }


def rank_deals(
    listings: List[MarketplaceListing],
) -> list:
    """
    Estimate market value and rank listings
    from strongest deal to weakest deal.
    """

    estimated_value = estimate_market_value(
        listings
    )

    ranked = []

    for listing in listings:

        analysis = calculate_deal(
            listing_price=listing.price,
            estimated_value=estimated_value,
        )

        ranked.append(
            {
                "listing": listing,
                "analysis": analysis,
            }
        )

    ranked.sort(
        key=lambda item: item["analysis"]["deal_score"],
        reverse=True,
    )

    return ranked
