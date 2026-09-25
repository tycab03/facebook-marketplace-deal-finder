from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote_plus
import re

from playwright.sync_api import sync_playwright


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

# Facebook Marketplace location ID for Townsville
TOWNSVILLE_LOCATION_ID = "109177059102294"


# --------------------------------------------------
# LISTING MODEL
# --------------------------------------------------

@dataclass
class MarketplaceListing:
    title: str
    price: float
    location: str
    url: str
    image_url: str = ""
    description: str = ""


# --------------------------------------------------
# PRICE HELPERS
# --------------------------------------------------

def clean_price(price_text: str) -> Optional[float]:
    """
    Convert Facebook Marketplace price text into a number.

    Examples:
    "$500" -> 500.0
    "AU$700" -> 700.0
    "$1,200" -> 1200.0
    "Free" -> 0.0
    """

    if not price_text:
        return None

    price_text = str(price_text).strip()

    if price_text.lower() == "free":
        return 0.0

    match = re.search(
        r"(?:AU)?\$\s*([\d,]+(?:\.\d{1,2})?)",
        price_text,
        re.IGNORECASE,
    )

    if not match:
        return None

    try:
        return float(
            match.group(1).replace(",", "")
        )

    except ValueError:
        return None


def is_price_line(text: str) -> bool:
    """
    Check whether a line looks like a Marketplace price.
    """

    if not text:
        return False

    text = text.strip()

    if text.lower() == "free":
        return True

    return bool(
        re.fullmatch(
            r"(?:AU)?\$\s*[\d,]+(?:\.\d{1,2})?",
            text,
            re.IGNORECASE,
        )
    )


# --------------------------------------------------
# BUILD SEARCH URL
# --------------------------------------------------

def build_search_url(
    search_query: str,
    location_id: str = TOWNSVILLE_LOCATION_ID,
) -> str:
    """
    Build the Facebook Marketplace search URL.
    """

    query = quote_plus(
        search_query.strip()
    )

    return (
        "https://www.facebook.com/"
        f"marketplace/{location_id}/search/"
        f"?query={query}"
    )


# --------------------------------------------------
# PARSE LISTING CARD
# --------------------------------------------------

def parse_listing_card(
    lines: List[str],
):
    """
    Extract price, title and location from
    a Facebook Marketplace listing card.

    Handles normal listings:

    AU$600
    PS5 Digital Edition
    Townsville, QLD

    And discounted listings:

    AU$800
    AU$700
    PS5 Slim Digital
    Townsville, QLD
    """

    if not lines:
        return None

    first_price_index = None

    # --------------------------------------------------
    # FIND FIRST PRICE
    # --------------------------------------------------

    for index, line in enumerate(lines):

        if is_price_line(line):

            first_price_index = index
            break

    if first_price_index is None:
        return None

    # --------------------------------------------------
    # COLLECT CONSECUTIVE PRICE LINES
    # --------------------------------------------------

    price_lines = []

    index = first_price_index

    while (
        index < len(lines)
        and is_price_line(lines[index])
    ):

        price_lines.append(
            lines[index]
        )

        index += 1

    if not price_lines:
        return None

    # --------------------------------------------------
    # CURRENT PRICE
    # --------------------------------------------------

    # Facebook may show an old price followed by
    # the new price. The final displayed price is
    # treated as the current asking price.

    price = clean_price(
        price_lines[-1]
    )

    if price is None:
        return None

    # --------------------------------------------------
    # TITLE
    # --------------------------------------------------

    if index >= len(lines):
        return None

    title = (
        lines[index]
        .strip()
    )

    if not title:
        return None

    index += 1

    # --------------------------------------------------
    # LOCATION
    # --------------------------------------------------

    location = ""

    if index < len(lines):

        location = (
            lines[index]
            .strip()
        )

    return {
        "title": title,
        "price": price,
        "location": location,
    }


# --------------------------------------------------
# COLLECT MARKETPLACE LISTINGS
# --------------------------------------------------

def collect_listings(
    search_query: str,
    location_id: str = TOWNSVILLE_LOCATION_ID,
    max_listings: int = 30,
) -> List[MarketplaceListing]:
    """
    Open Facebook Marketplace using Playwright
    and collect listing information.

    The local .facebook_browser directory stores
    the browser session so Facebook login can
    persist between runs.
    """

    search_url = build_search_url(
        search_query=search_query,
        location_id=location_id,
    )

    listings = []

    with sync_playwright() as playwright:

        # --------------------------------------------------
        # OPEN BROWSER
        # --------------------------------------------------

        context = playwright.chromium.launch_persistent_context(
            user_data_dir=".facebook_browser",
            headless=False,
            viewport={
                "width": 1400,
                "height": 900,
            },
        )

        if context.pages:

            page = context.pages[0]

        else:

            page = context.new_page()

        print()
        print("----------------------------------------")
        print("FACEBOOK MARKETPLACE")
        print("----------------------------------------")
        print()

        print("Opening:")
        print(search_url)
        print()

        # --------------------------------------------------
        # OPEN MARKETPLACE
        # --------------------------------------------------

        page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        print("Browser opened.")
        print()

        # Give Facebook time to render the page
        page.wait_for_timeout(
            3000
        )

        # --------------------------------------------------
        # SCROLL TO LOAD MORE RESULTS
        # --------------------------------------------------

        print(
            "Loading Marketplace listings..."
        )

        for _ in range(5):

            page.mouse.wheel(
                0,
                2500,
            )

            page.wait_for_timeout(
                1500
            )

        # --------------------------------------------------
        # FIND MARKETPLACE LINKS
        # --------------------------------------------------

        links = page.locator(
            'a[href*="/marketplace/item/"]'
        )

        link_count = links.count()

        print(
            f"Found {link_count} Marketplace links."
        )

        seen_urls = set()

        # --------------------------------------------------
        # PARSE RESULTS
        # --------------------------------------------------

        for link_index in range(
            link_count
        ):

            if len(listings) >= max_listings:
                break

            link = links.nth(
                link_index
            )

            try:

                # ------------------------------------------
                # URL
                # ------------------------------------------

                href = link.get_attribute(
                    "href"
                )

                if not href:
                    continue

                if href.startswith("/"):

                    href = (
                        "https://www.facebook.com"
                        + href
                    )

                # Remove tracking parameters
                href = href.split("?")[0]

                # Skip duplicate listings
                if href in seen_urls:
                    continue

                seen_urls.add(
                    href
                )

                # ------------------------------------------
                # LISTING TEXT
                # ------------------------------------------

                text = (
                    link
                    .inner_text()
                    .strip()
                )

                if not text:
                    continue

                lines = [
                    line.strip()
                    for line in text.splitlines()
                    if line.strip()
                ]

                parsed = parse_listing_card(
                    lines
                )

                if not parsed:
                    continue

                # ------------------------------------------
                # IMAGE
                # ------------------------------------------

                image_url = ""

                images = link.locator(
                    "img"
                )

                if images.count() > 0:

                    image_url = (
                        images
                        .first
                        .get_attribute("src")
                        or ""
                    )

                # ------------------------------------------
                # CREATE LISTING
                # ------------------------------------------

                listing = MarketplaceListing(
                    title=parsed["title"],
                    price=parsed["price"],
                    location=parsed["location"],
                    url=href,
                    image_url=image_url,
                )

                listings.append(
                    listing
                )

            except Exception as error:

                print(
                    f"Skipped listing {link_index}: "
                    f"{error}"
                )

        context.close()

    return listings


# --------------------------------------------------
# FILTER LISTINGS
# --------------------------------------------------

def filter_listings(
    listings: List[MarketplaceListing],
    search_query: str,
    min_price: float = 0,
    max_price: float = 0,
) -> List[MarketplaceListing]:
    """
    Filter Marketplace listings by:

    - search relevance
    - obvious accessory listings
    - minimum price
    - maximum price
    """

    query = (
        search_query
        .lower()
        .strip()
    )

    results = []

    # --------------------------------------------------
    # NORMALISE PRODUCT SEARCH
    # --------------------------------------------------

    ps5_search = query in [
        "ps5",
        "playstation 5",
        "playstation5",
    ]

    # --------------------------------------------------
    # PS5 ACCESSORY EXCLUSIONS
    # --------------------------------------------------

    ps5_exclusion_words = [
        "controller",
        "controllers",
        "stand",
        "stands",
        "headphone",
        "headphones",
        "headset",
        "headsets",
        "game",
        "games",
        "charging",
        "charger",
        "dock",
        "case",
        "cover",
        "skin",
        "cable",
        "cables",
        "hdmi",
        "remote",
        "portal",
        "ps portal",
        "vr",
        "psvr",
        "faceplate",
        "faceplates",
        "disc drive",
        "disk drive",
    ]

    # --------------------------------------------------
    # FILTER EACH LISTING
    # --------------------------------------------------

    for listing in listings:

        title = (
            listing.title
            .lower()
            .strip()
        )

        # --------------------------------------------------
        # SEARCH RELEVANCE
        # --------------------------------------------------

        if ps5_search:

            relevant = (
                "ps5" in title
                or "playstation 5" in title
            )

            if not relevant:
                continue

        elif query:

            if query not in title:
                continue

        # --------------------------------------------------
        # REMOVE PS5 ACCESSORIES
        # --------------------------------------------------

        if ps5_search:

            contains_accessory_word = any(
                word in title
                for word in ps5_exclusion_words
            )

            if contains_accessory_word:
                continue

        # --------------------------------------------------
        # MINIMUM PRICE
        # --------------------------------------------------

        if listing.price < min_price:
            continue

        # --------------------------------------------------
        # MAXIMUM PRICE
        # --------------------------------------------------

        if (
            max_price > 0
            and listing.price > max_price
        ):
            continue

        # --------------------------------------------------
        # KEEP LISTING
        # --------------------------------------------------

        results.append(
            listing
        )

    return results


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    results = collect_listings(
        search_query="PS5",
        max_listings=30,
    )

    filtered_results = filter_listings(
        listings=results,
        search_query="PS5",
    )

    print()
    print("----------------------------------------")
    print("FILTERED RESULTS")
    print("----------------------------------------")

    print()
    print(
        f"{len(filtered_results)} relevant listings found."
    )

    for number, listing in enumerate(
        filtered_results,
        start=1,
    ):

        print()
        print(
            f"Listing {number}"
        )

        print(
            "Title:",
            listing.title,
        )

        print(
            "Price:",
            listing.price,
        )

        print(
            "Location:",
            listing.location,
        )

        print(
            "URL:",
            listing.url,
        )