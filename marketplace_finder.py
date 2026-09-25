from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote_plus
import re

from playwright.sync_api import sync_playwright


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

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
    Return True when a line looks like a Marketplace price.
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
# SEARCH URL
# --------------------------------------------------

def build_search_url(
    search_query: str,
    location_id: str = TOWNSVILLE_LOCATION_ID,
) -> str:

    query = quote_plus(
        search_query.strip()
    )

    return (
        "https://www.facebook.com/"
        f"marketplace/{location_id}/search/"
        f"?query={query}"
    )


# --------------------------------------------------
# PARSE ONE MARKETPLACE CARD
# --------------------------------------------------

def parse_listing_card(
    lines: List[str],
):
    """
    Extract price, title and location from the text
    contained in a Facebook Marketplace result card.

    Handles cards such as:

    AU$800
    AU$700
    PS5 Slim Digital
    Townsville, QLD

    as well as:

    AU$600
    PS5 Digital Edition
    Mareeba, QLD
    """

    if not lines:
        return None

    first_price_index = None

    # Find the first price line.
    for index, line in enumerate(lines):

        if is_price_line(line):
            first_price_index = index
            break

    if first_price_index is None:
        return None

    price_lines = []

    index = first_price_index

    # Facebook may show:
    #
    # old price
    # new price
    # title
    #
    # Collect every consecutive price line first.
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

    # The last displayed price is treated as
    # the current asking price.
    price = clean_price(
        price_lines[-1]
    )

    if price is None:
        return None

    # First non-price line after the price(s)
    # should be the listing title.
    if index >= len(lines):
        return None

    title = lines[index].strip()

    index += 1

    if not title:
        return None

    # Next line normally contains location.
    location = ""

    if index < len(lines):
        location = lines[index].strip()

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
    max_listings: int = 20,
) -> List[MarketplaceListing]:

    search_url = build_search_url(
        search_query=search_query,
        location_id=location_id,
    )

    listings = []

    with sync_playwright() as playwright:

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

        page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        print("Browser opened.")
        print()

        
        page.wait_for_timeout(2000)

        print()
        print("Loading Marketplace listings...")

        for _ in range(5):

            page.mouse.wheel(
                0,
                2500,
            )

            page.wait_for_timeout(
                1500
            )

        links = page.locator(
            'a[href*="/marketplace/item/"]'
        )

        link_count = links.count()

        print(
            f"Found {link_count} Marketplace links."
        )

        seen_urls = set()

        for link_index in range(link_count):

            if len(listings) >= max_listings:
                break

            link = links.nth(
                link_index
            )

            try:

                # ----------------------------------
                # URL
                # ----------------------------------

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

                href = href.split("?")[0]

                if href in seen_urls:
                    continue

                seen_urls.add(
                    href
                )

                # ----------------------------------
                # CARD TEXT
                # ----------------------------------

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

                # ----------------------------------
                # IMAGE
                # ----------------------------------

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

                # ----------------------------------
                # CREATE LISTING
                # ----------------------------------

                listings.append(
                    MarketplaceListing(
                        title=parsed["title"],
                        price=parsed["price"],
                        location=parsed["location"],
                        url=href,
                        image_url=image_url,
                    )
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

    query = (
        search_query
        .lower()
        .strip()
    )

    results = []

    for listing in listings:

        if (
            query
            and query not in listing.title.lower()
        ):
            continue

        if listing.price < min_price:
            continue

        if (
            max_price > 0
            and listing.price > max_price
        ):
            continue

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
        max_listings=10,
    )

    print()
    print("----------------------------------------")
    print("RESULTS")
    print("----------------------------------------")

    if not results:

        print()
        print("No listings were collected.")

    else:

        for number, listing in enumerate(
            results,
            start=1,
        ):

            print()
            print(f"Listing {number}")
            print("Title:", listing.title)
            print("Price:", listing.price)
            print("Location:", listing.location)
            print("URL:", listing.url)