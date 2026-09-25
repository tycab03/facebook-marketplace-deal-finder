import streamlit as st

from marketplace_finder import MarketplaceListing, filter_listings
from deal_analyzer import calculate_deal


st.set_page_config(
    page_title="Facebook Marketplace Deal Finder",
    page_icon="🔎",
    layout="wide"
)

st.title("Facebook Marketplace Deal Finder")
st.write("Search for items and find potential deals on Facebook Marketplace.")

st.divider()


# Temporary test listings
# These will later be replaced with real Marketplace data.
TEST_LISTINGS = [
    {
        "listing": MarketplaceListing(
            title="Apple iPhone 15 Pro 256GB",
            price=700,
            location="Townsville",
            url="https://example.com/iphone15"
        ),
        "estimated_value": 1000
    },
    {
        "listing": MarketplaceListing(
            title="iPhone 13 128GB",
            price=450,
            location="Townsville",
            url="https://example.com/iphone13"
        ),
        "estimated_value": 650
    },
    {
        "listing": MarketplaceListing(
            title="Gaming PC RTX 4070",
            price=1200,
            location="Townsville",
            url="https://example.com/gamingpc"
        ),
        "estimated_value": 1700
    },
    {
        "listing": MarketplaceListing(
            title="Toyota Hilux",
            price=18000,
            location="Townsville",
            url="https://example.com/hilux"
        ),
        "estimated_value": 22000
    },
]


# Search controls
search_query = st.text_input(
    "Search for an item",
    placeholder="e.g. iPhone, RTX 4070, Toyota Hilux"
)

col1, col2 = st.columns(2)

with col1:
    min_price = st.number_input(
        "Minimum price ($)",
        min_value=0,
        value=0,
        step=50
    )

with col2:
    max_price = st.number_input(
        "Maximum price ($)",
        min_value=0,
        value=1000,
        step=50
    )

location = st.text_input(
    "Location",
    value="Townsville"
)


if st.button("Find Deals", type="primary"):

    if not search_query:
        st.warning("Enter an item to search for.")

    elif max_price > 0 and min_price > max_price:
        st.warning("Minimum price cannot be greater than maximum price.")

    else:

        listings = [item["listing"] for item in TEST_LISTINGS]

        results = filter_listings(
            listings,
            search_query,
            min_price,
            max_price
        )

        # Location filtering
        if location:
            results = [
                listing
                for listing in results
                if location.lower() in listing.location.lower()
            ]

        st.divider()

        if not results:
            st.warning("No listings found.")

        else:
            st.subheader(f"Found {len(results)} listing(s)")

            for listing in results:

                estimated_value = next(
                    item["estimated_value"]
                    for item in TEST_LISTINGS
                    if item["listing"].url == listing.url
                )

                deal = calculate_deal(
                    listing.price,
                    estimated_value
                )

                with st.container(border=True):

                    st.subheader(listing.title)

                    st.caption(f"📍 {listing.location}")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Asking Price",
                            f"${listing.price:,.0f}"
                        )

                    with col2:
                        st.metric(
                            "Estimated Value",
                            f"${deal['estimated_value']:,.0f}"
                        )

                    with col3:
                        st.metric(
                            "Potential Saving",
                            f"${deal['saving']:,.0f}"
                        )

                    st.write(
                        f"**Below market:** "
                        f"{deal['discount_percent']}%"
                    )

                    st.write(
                        f"**Deal Score:** "
                        f"{deal['deal_score']} / 10"
                    )

                    st.link_button(
                        "View Listing",
                        listing.url
                    )
