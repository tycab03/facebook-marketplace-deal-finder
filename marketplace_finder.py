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
# PRICE CLEANING
# --------------------------------------------------

def clean_price(price_text: str) -> Optional[float]:
    """
    Convert Marketplace price text into a number.

    Examples:
    "$500" -> 500.0
    "$1,200" -> 1200.0
    "Free" -> 0.0
    """

    if not price_text:
        return None

    price_text = str(price_text).strip()

    if price_text.lower() == "free":
        return 0.0

    match = re.search(
        r"\$?\s*([\d,]+(?:\.\d{1,2})?)",
        price_text,
    )

    if not match:
        return None

    try:
        return float(
            match.group(1).replace(",", "")
        )

    except ValueError:
        return None


# --------------------------------------------------
# BUILD FACEBOOK SEARCH URL
# --------------------------------------------------

def build_search_url(
    search_query: str,
    location_id: str = TOWNSVILLE_LOCATION_ID,
) -> str:
    """
    Build a Facebook Marketplace search URL.
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
# COLLECT MARKETPLACE LISTINGS
# --------------------------------------------------

def collect_listings(
    search_query: str,
    location_id: str = TOWNSVILLE_LOCATION_ID,
    max_listings: int = 20,
) -> List[MarketplaceListing]:
    """
    Open Facebook Marketplace using Playwright
    and collect Marketplace listings.

    A local browser profile is used so the Facebook
    login session can persist between runs.
    """

    search_url = build_search_url(
        search_query=search_query,
        location_id=location_id,
    )

    listings = []

    with sync_playwright() as playwright:

        # ------------------------------------------
        # OPEN CHROMIUM
        # ------------------------------------------

        context = playwright.chromium.launch_persistent_context(
            user_data_dir=".facebook_browser",
            headless=False,
            viewport={
                "width": 1400,
                "height": 900,
            },
        )

        # Use the existing page or create one
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

        # ------------------------------------------
        # OPEN MARKETPLACE
        # ------------------------------------------

        page.goto(
            search_url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        print("Browser opened.")
        print()
        print(
            "If Facebook asks you to log in, "
            "log in normally in the Chromium window."
        )
        print()

        input(
            "Once Marketplace listings are visible, "
            "press Return here..."
        )

        # Give Marketplace a moment to finish rendering
        page.wait_for_timeout(2000)

        # ------------------------------------------
        # SCROLL TO LOAD MORE RESULTS
        # ------------------------------------------

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

        # ------------------------------------------
        # FIND LISTING LINKS
        # ------------------------------------------

        links = page.locator(
            'a[href*="/marketplace/item/"]'
        )

        link_count = links.count()

        print(
            f"Found {link_count} Marketplace links."
        )

        seen_urls = set()

        # ------------------------------------------
        # PARSE LISTINGS
        # ------------------------------------------

        for index in range(link_count):

            if len(listings) >= max_listings:
                break

            link = links.nth(index)

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

                # Remove Facebook tracking parameters
                href = href.split("?")[0]

                if href in seen_urls:
                    continue

                seen_urls.add(href)

                # ----------------------------------
                # CARD TEXT
                # ----------------------------------

                text = link.inner_text().strip()

                if not text:
                    continue

                lines = [
                    line.strip()
                    for line in text.splitlines()
                    if line.strip()
                ]

                if not lines:
                    continue

                # ----------------------------------
                # PRICE
                # ----------------------------------

                price = None
                price_line_index = None

                for line_index, line in enumerate(lines):

                    if "$" not in line:
                        continue

                    possible_price = clean_price(
                        line
                    )

                    if possible_price is not None:

                        price = possible_price
                        price_line_index = line_index
                        break

                if price is None:
                    continue

                # ----------------------------------
                # TITLE
                # ----------------------------------

                title = ""

                if (
                    price_line_index is not None
                    and price_line_index + 1 < len(lines)
                ):
                    title = lines[
                        price_line_index + 1
                    ]

                if not title:
                    title = "Marketplace Listing"

                # ----------------------------------
                # LOCATION
                # ----------------------------------

                location = ""

                if (
                    price_line_index is not None
                    and price_line_index + 2 < len(lines)
                ):
                    location = lines[
                        price_line_index + 2
                    ]

                # ----------------------------------
                # IMAGE
                # ----------------------------------

                image_url = ""

                images = link.locator("img")

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

                listing = MarketplaceListing(
                    title=title,
                    price=price,
                    location=location,
                    url=href,
                    image_url=image_url,
                )

                listings.append(
                    listing
                )

            except Exception as error:

                print(
                    f"Skipped listing {index}: "
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
    Filter Marketplace listings by search query
    and price.
    """

    query = (
        search_query
        .lower()
        .strip()
    )

    results = []

    for listing in listings:

        # Search term
        if (
            query
            and query not in listing.title.lower()
        ):
            continue

        # Minimum price
        if listing.price < min_price:
            continue

        # Maximum price
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

            print(
                "Image:",
                listing.image_url,
            )