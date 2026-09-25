import re
from statistics import median
from typing import List, Set, Dict, Optional

from marketplace_finder import MarketplaceListing


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

STOP_WORDS = {
    "a", "an", "and", "the", "for", "with", "in", "on",
    "of", "to", "from", "by", "brand", "new", "used",
    "good", "great", "excellent", "condition", "sale",
    "selling", "sell", "pickup", "pick", "up", "only",
    "negotiable", "ono", "firm", "price", "cheap",
    "bargain", "mint", "like", "perfect", "near",
    "unused", "sealed", "boxed", "box",
}

ACCESSORY_WORDS = {
    "case", "cases", "cover", "covers",
    "stand", "stands", "holder", "holders",
    "charger", "chargers", "charging",
    "cable", "cables", "adapter", "adaptor",
    "dock", "docking",
    "controller", "controllers",
    "headset", "headsets",
    "headphone", "headphones",
    "earbuds",
    "screen", "protector", "protectors",
    "skin", "skins", "sleeve",
    "bag", "bags",
    "mount", "mounts",
    "remote", "faceplate", "faceplates",
}

VARIANT_WORDS = {
    "pro",
    "max",
    "plus",
    "ultra",
    "mini",
    "slim",
    "digital",
    "disc",
    "disk",
    "lite",
    "air",
    "ti",
    "super",
    "xt",
    "xtx",
    "se",
    "fe",
    "oled",
    "elite",
    "premium",
}

# Units that usually represent meaningful product specifications.
SPEC_UNITS = {
    "gb",
    "tb",
    "mb",
    "hz",
    "mhz",
    "ghz",
    "inch",
    "inches",
    "mm",
    "cm",
    "mah",
    "w",
    "kw",
}


# --------------------------------------------------
# NORMALISE TEXT
# --------------------------------------------------

def normalise_text(text: str) -> str:
    """
    Normalise Marketplace text so titles written
    slightly differently can still be compared.
    """

    text = str(text).lower()

    # Standardise common formatting.
    text = text.replace("play station", "playstation")

    # Convert:
    # 256 gb -> 256gb
    # 1 tb   -> 1tb
    # 144 hz -> 144hz
    text = re.sub(
        r"\b(\d+(?:\.\d+)?)\s+"
        r"(gb|tb|mb|hz|mhz|ghz|inch|inches|mm|cm|mah|kw|w)\b",
        r"\1\2",
        text,
    )

    # Remove punctuation.
    text = re.sub(
        r"[^a-z0-9]+",
        " ",
        text,
    )

    return " ".join(
        text.split()
    )


# --------------------------------------------------
# TOKENISE
# --------------------------------------------------

def tokenize(text: str) -> List[str]:

    normalised = normalise_text(
        text
    )

    return [
        token
        for token in normalised.split()
        if token
    ]


def meaningful_tokens(
    text: str,
) -> Set[str]:

    return {
        token
        for token in tokenize(text)
        if (
            token not in STOP_WORDS
            and len(token) > 1
        )
    }


# --------------------------------------------------
# MODEL IDENTIFIERS
# --------------------------------------------------

def is_model_identifier(
    token: str,
) -> bool:
    """
    Detect tokens likely to represent product models.

    Examples:

    15
    4070
    s24
    m2
    dhp486
    a55
    65c845
    """

    token = token.lower()

    # Ignore specification tokens such as 256gb.
    if is_spec_token(token):
        return False

    # Pure numbers.
    if token.isdigit():

        number = int(token)

        # Very small numbers are often versions/models:
        # iPhone 15, M 2, etc.
        #
        # Larger numbers are commonly GPU/model numbers:
        # 4070, 4080, etc.

        if number >= 2:
            return True

    # Mixed letters + numbers.
    has_letter = bool(
        re.search(
            r"[a-z]",
            token,
        )
    )

    has_number = bool(
        re.search(
            r"\d",
            token,
        )
    )

    if has_letter and has_number:

        return True

    return False


def extract_model_identifiers(
    text: str,
) -> Set[str]:

    return {
        token
        for token in tokenize(text)
        if is_model_identifier(token)
    }


# --------------------------------------------------
# VARIANTS
# --------------------------------------------------

def extract_variants(
    text: str,
) -> Set[str]:

    tokens = set(
        tokenize(text)
    )

    variants = (
        tokens
        & VARIANT_WORDS
    )

    # Treat disc/disk as the same thing.
    if "disk" in variants:

        variants.remove(
            "disk"
        )

        variants.add(
            "disc"
        )

    return variants


# --------------------------------------------------
# SPECIFICATIONS
# --------------------------------------------------

def is_spec_token(
    token: str,
) -> bool:

    token = token.lower()

    for unit in SPEC_UNITS:

        if re.fullmatch(
            rf"\d+(?:\.\d+)?{unit}",
            token,
        ):

            return True

    return False


def extract_specs(
    text: str,
) -> Set[str]:

    return {
        token
        for token in tokenize(text)
        if is_spec_token(token)
    }


# --------------------------------------------------
# PRODUCT PROFILE
# --------------------------------------------------

def build_product_profile(
    text: str,
) -> Dict[str, Set[str]]:
    """
    Convert a title/search into a generic
    structured product profile.
    """

    return {
        "tokens": meaningful_tokens(
            text
        ),
        "models": extract_model_identifiers(
            text
        ),
        "variants": extract_variants(
            text
        ),
        "specs": extract_specs(
            text
        ),
    }


# --------------------------------------------------
# ACCESSORY DETECTION
# --------------------------------------------------

def is_likely_accessory(
    title: str,
    search_query: str,
) -> bool:

    title_tokens = meaningful_tokens(
        title
    )

    search_tokens = meaningful_tokens(
        search_query
    )

    # User explicitly searched for an accessory.
    if search_tokens & ACCESSORY_WORDS:

        return False

    # Listing contains an accessory term while the
    # user's search does not.
    if title_tokens & ACCESSORY_WORDS:

        return True

    return False


# --------------------------------------------------
# SEARCH RELEVANCE
# --------------------------------------------------

def is_relevant_to_search(
    title: str,
    search_query: str,
) -> bool:
    """
    Determine whether a Marketplace result is
    compatible with the user's search.

    This is generic and does not know specific
    product categories.
    """

    search = build_product_profile(
        search_query
    )

    listing = build_product_profile(
        title
    )

    if not search["tokens"]:
        return True

    # ----------------------------------------------
    # ACCESSORIES
    # ----------------------------------------------

    if is_likely_accessory(
        title,
        search_query,
    ):

        return False

    # ----------------------------------------------
    # CORE SEARCH TERMS
    # ----------------------------------------------

    core_search_tokens = (
        search["tokens"]
        - search["models"]
        - search["variants"]
        - search["specs"]
    )

    core_listing_tokens = (
        listing["tokens"]
        - listing["models"]
        - listing["variants"]
        - listing["specs"]
    )

    if core_search_tokens:

        shared_core = (
            core_search_tokens
            & core_listing_tokens
        )

        if not shared_core:
            return False

    # ----------------------------------------------
    # MODEL CONFLICT
    # ----------------------------------------------

    # If the search specifies model identifiers,
    # listings containing different model identifiers
    # should normally be rejected.
    #
    # Example:
    #
    # Search:   iPhone 15
    # Listing:  iPhone 16 Pro Max
    #
    # 15 != 16 -> reject

    if search["models"]:

        listing_models = (
            listing["models"]
        )

        if listing_models:

            if not (
                search["models"]
                & listing_models
            ):

                return False

    # ----------------------------------------------
    # SEARCH VARIANT REQUIREMENTS
    # ----------------------------------------------

    # If the USER explicitly searches:
    #
    # iPhone 15 Pro
    #
    # then a plain iPhone 15 should not be treated
    # as equally relevant.

    if search["variants"]:

        if not search["variants"].issubset(
            listing["variants"]
        ):

            return False

    # ----------------------------------------------
    # SEARCH SPEC REQUIREMENTS
    # ----------------------------------------------

    # If user explicitly searches 256GB, require
    # that specification when the listing provides
    # conflicting storage/spec information.

    if search["specs"] and listing["specs"]:

        if not (
            search["specs"]
            & listing["specs"]
        ):

            return False

    return True


# --------------------------------------------------
# COMPATIBILITY SCORE
# --------------------------------------------------

def calculate_compatibility(
    target_title: str,
    candidate_title: str,
    search_query: str,
) -> float:
    """
    Score how comparable two Marketplace listings are.

    0.0 = incompatible
    1.0 = extremely similar
    """

    target = build_product_profile(
        target_title
    )

    candidate = build_product_profile(
        candidate_title
    )

    search = build_product_profile(
        search_query
    )

    # ----------------------------------------------
    # MODEL CONFLICTS
    # ----------------------------------------------

    if (
        target["models"]
        and candidate["models"]
    ):

        shared_models = (
            target["models"]
            & candidate["models"]
        )

        if not shared_models:
            return 0.0

    # ----------------------------------------------
    # VARIANT CONFLICTS
    # ----------------------------------------------

    target_variants = (
        target["variants"]
        - search["variants"]
    )

    candidate_variants = (
        candidate["variants"]
        - search["variants"]
    )

    # If both listings clearly state variants and
    # they disagree, heavily separate them.
    if (
        target_variants
        and candidate_variants
        and target_variants != candidate_variants
    ):

        return 0.0

    # A detailed variant vs an unspecified listing
    # may still be useful, but with lower confidence.

    variant_score = 1.0

    if target_variants != candidate_variants:

        variant_score = 0.55

    # ----------------------------------------------
    # SPECIFICATION MATCH
    # ----------------------------------------------

    spec_score = 1.0

    if (
        target["specs"]
        and candidate["specs"]
    ):

        shared_specs = (
            target["specs"]
            & candidate["specs"]
        )

        if not shared_specs:

            spec_score = 0.35

    elif (
        target["specs"]
        or candidate["specs"]
    ):

        spec_score = 0.70

    # ----------------------------------------------
    # TITLE SIMILARITY
    # ----------------------------------------------

    target_tokens = (
        target["tokens"]
        - search["tokens"]
        - ACCESSORY_WORDS
    )

    candidate_tokens = (
        candidate["tokens"]
        - search["tokens"]
        - ACCESSORY_WORDS
    )

    if (
        not target_tokens
        and not candidate_tokens
    ):

        title_score = 1.0

    elif (
        not target_tokens
        or not candidate_tokens
    ):

        title_score = 0.65

    else:

        intersection = (
            target_tokens
            & candidate_tokens
        )

        union = (
            target_tokens
            | candidate_tokens
        )

        if union:

            title_score = (
                len(intersection)
                / len(union)
            )

        else:

            title_score = 0.0

    # ----------------------------------------------
    # FINAL SCORE
    # ----------------------------------------------

    score = (
        title_score * 0.40
        + variant_score * 0.35
        + spec_score * 0.25
    )

    return round(
        score,
        3,
    )


# --------------------------------------------------
# FIND COMPARABLES
# --------------------------------------------------

def find_comparable_listings(
    target_listing: MarketplaceListing,
    all_listings: List[MarketplaceListing],
    search_query: str,
) -> List[MarketplaceListing]:

    scored = []

    for candidate in all_listings:

        if is_likely_accessory(
            candidate.title,
            search_query,
        ):

            continue

        if not is_relevant_to_search(
            candidate.title,
            search_query,
        ):

            continue

        compatibility = calculate_compatibility(
            target_listing.title,
            candidate.title,
            search_query,
        )

        if compatibility >= 0.55:

            scored.append(
                (
                    compatibility,
                    candidate,
                )
            )

    # Highest compatibility first.
    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    comparables = [
        listing
        for score, listing in scored
    ]

    # If we found enough strong matches, use them.
    if len(comparables) >= 2:

        return comparables

    # ----------------------------------------------
    # FALLBACK
    # ----------------------------------------------

    # Only fall back to listings that are genuinely
    # relevant to the user's search.

    fallback = [
        listing
        for listing in all_listings
        if (
            not is_likely_accessory(
                listing.title,
                search_query,
            )
            and is_relevant_to_search(
                listing.title,
                search_query,
            )
        )
    ]

    return fallback


# --------------------------------------------------
# PRICE OUTLIER REMOVAL
# --------------------------------------------------

def remove_price_outliers(
    listings: List[MarketplaceListing],
) -> List[MarketplaceListing]:
    """
    Remove extreme price outliers using the
    interquartile range (IQR) method.

    Requires at least 4 listings.
    """

    valid = [
        listing
        for listing in listings
        if listing.price > 0
    ]

    if len(valid) < 4:
        return valid

    ordered = sorted(
        valid,
        key=lambda listing: listing.price,
    )

    prices = [
        listing.price
        for listing in ordered
    ]

    midpoint = len(prices) // 2

    if len(prices) % 2 == 0:

        lower_half = prices[:midpoint]
        upper_half = prices[midpoint:]

    else:

        lower_half = prices[:midpoint]
        upper_half = prices[midpoint + 1:]

    q1 = median(
        lower_half
    )

    q3 = median(
        upper_half
    )

    iqr = q3 - q1

    # If all prices are very similar, no useful
    # outlier calculation is necessary.
    if iqr <= 0:
        return valid

    lower_bound = (
        q1
        - 1.5 * iqr
    )

    upper_bound = (
        q3
        + 1.5 * iqr
    )

    return [
        listing
        for listing in valid
        if (
            lower_bound
            <= listing.price
            <= upper_bound
        )
    ]


# --------------------------------------------------
# MARKET VALUE
# --------------------------------------------------

def estimate_market_value(
    listings: List[MarketplaceListing],
) -> float:

    cleaned = remove_price_outliers(
        listings
    )

    prices = [
        listing.price
        for listing in cleaned
        if listing.price > 0
    ]

    if not prices:
        return 0.0

    return round(
        median(prices),
        2,
    )


# --------------------------------------------------
# PRICE RANGE
# --------------------------------------------------

def calculate_price_range(
    listings: List[MarketplaceListing],
) -> Dict[str, float]:

    cleaned = remove_price_outliers(
        listings
    )

    prices = [
        listing.price
        for listing in cleaned
        if listing.price > 0
    ]

    if not prices:

        return {
            "low": 0,
            "high": 0,
        }

    return {
        "low": round(
            min(prices),
            2,
        ),
        "high": round(
            max(prices),
            2,
        ),
    }


# --------------------------------------------------
# CONFIDENCE
# --------------------------------------------------

def calculate_confidence(
    comparable_count: int,
    compatibility_scores: Optional[List[float]] = None,
) -> str:

    if comparable_count >= 6:

        return "High"

    if comparable_count >= 3:

        return "Medium"

    return "Low"


# --------------------------------------------------
# DEAL CALCULATION
# --------------------------------------------------

def calculate_deal(
    listing_price: float,
    estimated_value: float,
) -> dict:

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

    # 50% below estimated asking value = 10/10.
    deal_score = (
        discount_percent
        / 5
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
# RANK DEALS
# --------------------------------------------------

def rank_deals(
    listings: List[MarketplaceListing],
    search_query: str,
) -> list:

    # ----------------------------------------------
    # REMOVE IRRELEVANT RESULTS FIRST
    # ----------------------------------------------

    relevant_listings = [
        listing
        for listing in listings
        if is_relevant_to_search(
            listing.title,
            search_query,
        )
    ]

    ranked = []

    for listing in relevant_listings:

        # ------------------------------------------
        # COMPARABLES
        # ------------------------------------------

        comparables = find_comparable_listings(
            target_listing=listing,
            all_listings=relevant_listings,
            search_query=search_query,
        )

        # ------------------------------------------
        # REMOVE PRICE OUTLIERS
        # ------------------------------------------

        cleaned_comparables = remove_price_outliers(
            comparables
        )

        # ------------------------------------------
        # MARKET VALUE
        # ------------------------------------------

        estimated_value = estimate_market_value(
            cleaned_comparables
        )

        # ------------------------------------------
        # RANGE
        # ------------------------------------------

        price_range = calculate_price_range(
            cleaned_comparables
        )

        # ------------------------------------------
        # DEAL SCORE
        # ------------------------------------------

        analysis = calculate_deal(
            listing_price=listing.price,
            estimated_value=estimated_value,
        )

        # ------------------------------------------
        # CONFIDENCE
        # ------------------------------------------

        comparable_count = len(
            cleaned_comparables
        )

        confidence = calculate_confidence(
            comparable_count
        )

        analysis["comparable_count"] = (
            comparable_count
        )

        analysis["confidence"] = (
            confidence
        )

        analysis["price_range_low"] = (
            price_range["low"]
        )

        analysis["price_range_high"] = (
            price_range["high"]
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
        key=lambda item: (
            item["analysis"]["deal_score"],
            item["analysis"]["comparable_count"],
        ),
        reverse=True,
    )

    return ranked


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    test_listings = [

        MarketplaceListing(
            "Apple iPhone 15 Pro Max 256GB",
            1000,
            "Townsville",
            "1",
        ),

        MarketplaceListing(
            "iPhone 15 Pro Max 256 GB Black",
            1100,
            "Townsville",
            "2",
        ),

        MarketplaceListing(
            "iPhone 15 Pro Max 256GB",
            1050,
            "Townsville",
            "3",
        ),

        MarketplaceListing(
            "iPhone 15 Pro Max 512GB",
            1250,
            "Townsville",
            "4",
        ),

        MarketplaceListing(
            "iPhone 15 Pro 256GB",
            900,
            "Townsville",
            "5",
        ),

        MarketplaceListing(
            "iPhone 15",
            700,
            "Townsville",
            "6",
        ),

        MarketplaceListing(
            "iPhone 16 Pro Max 512GB",
            215,
            "Townsville",
            "7",
        ),

        MarketplaceListing(
            "iPhone 15 Case",
            20,
            "Townsville",
            "8",
        ),
    ]

    results = rank_deals(
        listings=test_listings,
        search_query="iPhone 15",
    )

    print()
    print("----------------------------------------")
    print("GENERIC DEAL ANALYZER TEST")
    print("----------------------------------------")

    for result in results:

        listing = result["listing"]
        analysis = result["analysis"]

        print()
        print(
            "Title:",
            listing.title,
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
            "Confidence:",
            analysis["confidence"],
        )

        print(
            "Normal price range:",
            f"${analysis['price_range_low']}"
            f" - "
            f"${analysis['price_range_high']}",
        )

        print(
            "Saving:",
            analysis["saving"],
        )

        print(
            "Deal score:",
            analysis["deal_score"],
        )