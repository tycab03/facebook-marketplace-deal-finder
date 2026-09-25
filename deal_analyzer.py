from statistics import median
from typing import List, Optional

from marketplace_finder import MarketplaceListing


# --------------------------------------------------
# PS5 VARIANT DETECTION
# --------------------------------------------------

def detect_ps5_variant(title: str) -> Optional[str]:
    """
    Determine which PS5 model a listing most likely is.

    Possible variants:

    - PS5 Pro
    - PS5 Slim Digital
    - PS5 Slim Disc
    - PS5 Slim Unknown
    - PS5 Digital
    - PS5 Disc
    - PS5 Unknown
    """

    title = title.lower().strip()

    is_ps5 = (
        "ps5" in title
        or "playstation 5" in title
    )

    if not is_ps5:
        return None

    # ----------------------------------------------
    # PRO
    # ----------------------------------------------

    if "pro" in title:
        return "PS5 Pro"

    # ----------------------------------------------
    # SLIM
    # ----------------------------------------------

    if "slim" in title:

        if "digital" in title:
            return "PS5 Slim Digital"

        if (
            "disc" in title
            or "disk" in title
        ):
            return "PS5 Slim Disc"

        return "PS5 Slim Unknown"

    # ----------------------------------------------
    # ORIGINAL / UNSPECIFIED
    # ----------------------------------------------

    if "digital" in title:
        return "PS5 Digital"

    if (
        "disc" in title
        or "disk" in title
    ):
        return "PS5 Disc"

    return "PS5 Unknown"


# --------------------------------------------------
# ESTIMATE MARKET VALUE
# --------------------------------------------------

def estimate_market_value(
    listings: List[MarketplaceListing],
) -> float:
    """
    Estimate market value using the median asking
    price of comparable listings.
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


# --------------------------------------------------
# CALCULATE DEAL
# --------------------------------------------------

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

    # 50% below estimated market value = 10/10.
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


# --------------------------------------------------
# FIND COMPARABLE LISTINGS
# --------------------------------------------------

def find_comparable_listings(
    target_listing: MarketplaceListing,
    all_listings: List[MarketplaceListing],
) -> List[MarketplaceListing]:
    """
    Find listings that are comparable to the
    target listing.

    For PS5 searches, prefer listings of the
    same detected PS5 variant.
    """

    target_variant = detect_ps5_variant(
        target_listing.title
    )

    # If this isn't recognised as a PS5,
    # fall back to all listings.
    if target_variant is None:
        return all_listings

    same_variant = []

    for listing in all_listings:

        variant = detect_ps5_variant(
            listing.title
        )

        if variant == target_variant:

            same_variant.append(
                listing
            )

    # ----------------------------------------------
    # ENOUGH COMPARABLE DATA
    # ----------------------------------------------

    # Ideally use at least 2 listings of the
    # same model.
    if len(same_variant) >= 2:

        return same_variant

    # ----------------------------------------------
    # FALLBACK
    # ----------------------------------------------

    # If Marketplace does not give us enough
    # examples of that exact model, use all
    # relevant PS5 listings rather than trying
    # to estimate value from one listing alone.

    return all_listings


# --------------------------------------------------
# RANK DEALS
# --------------------------------------------------

def rank_deals(
    listings: List[MarketplaceListing],
) -> list:
    """
    Rank Marketplace listings by deal score.

    Each listing is compared against listings
    of the same detected PS5 variant whenever
    enough comparable listings are available.
    """

    ranked = []

    for listing in listings:

        # ------------------------------------------
        # DETECT VARIANT
        # ------------------------------------------

        variant = detect_ps5_variant(
            listing.title
        )

        # ------------------------------------------
        # FIND COMPARABLES
        # ------------------------------------------

        comparable_listings = find_comparable_listings(
            target_listing=listing,
            all_listings=listings,
        )

        # ------------------------------------------
        # ESTIMATE VALUE
        # ------------------------------------------

        estimated_value = estimate_market_value(
            comparable_listings
        )

        # ------------------------------------------
        # ANALYSE DEAL
        # ------------------------------------------

        analysis = calculate_deal(
            listing_price=listing.price,
            estimated_value=estimated_value,
        )

        # Add extra information for the UI.
        analysis["variant"] = (
            variant
            if variant
            else "Unknown"
        )

        analysis["comparable_count"] = len(
            comparable_listings
        )

        ranked.append(
            {
                "listing": listing,
                "analysis": analysis,
            }
        )

    # ----------------------------------------------
    # BEST DEAL FIRST
    # ----------------------------------------------

    ranked.sort(
        key=lambda item: item["analysis"]["deal_score"],
        reverse=True,
    )

    return ranked


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    test_listings = [
        MarketplaceListing(
            "PS5 Digital Edition",
            500,
            "Townsville",
            "test1",
        ),
        MarketplaceListing(
            "PS5 Digital",
            600,
            "Townsville",
            "test2",
        ),
        MarketplaceListing(
            "PS5 Slim Digital",
            650,
            "Townsville",
            "test3",
        ),
        MarketplaceListing(
            "PlayStation 5 Slim Digital Edition",
            800,
            "Townsville",
            "test4",
        ),
        MarketplaceListing(
            "PS5 Disk",
            700,
            "Townsville",
            "test5",
        ),
        MarketplaceListing(
            "PS5 Disc Edition",
            900,
            "Townsville",
            "test6",
        ),
        MarketplaceListing(
            "PS5 Pro",
            1000,
            "Townsville",
            "test7",
        ),
        MarketplaceListing(
            "PS5 Pro Bundle",
            1400,
            "Townsville",
            "test8",
        ),
    ]

    results = rank_deals(
        test_listings
    )

    for result in results:

        listing = result["listing"]
        analysis = result["analysis"]

        print()
        print(
            "Title:",
            listing.title,
        )

        print(
            "Variant:",
            analysis["variant"],
        )

        print(
            "Price:",
            listing.price,
        )

        print(
            "Estimated value:",
            analysis["estimated_value"],
        )

        print(
            "Comparable listings:",
            analysis["comparable_count"],
        )

        print(
            "Saving:",
            analysis["saving"],
        )

        print(
            "Deal score:",
            analysis["deal_score"],
        )