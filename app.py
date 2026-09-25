import streamlit as st

from marketplace_finder import (
    MarketplaceListing,
    filter_listings,
)

from deal_analyzer import calculate_deal


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Facebook Marketplace Deal Finder",
    page_icon="🔎",
    layout="wide",
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("Facebook Marketplace Deal Finder")

st.write(
    "Search Facebook Marketplace and identify "
    "potentially underpriced listings."
)

st.divider()


# --------------------------------------------------
# SEARCH
# --------------------------------------------------

search_query = st.text_input(
    "Search",
    placeholder="e.g. PS5, iPhone 15 Pro, RTX 4070",
)


location_col, radius_col = st.columns(2)


with location_col:

    location = st.text_input(
        "Location",
        value="Townsville",
    )


with radius_col:

    radius = st.selectbox(
        "Search radius",
        options=[
            20,
            40,
            60,
            100,
            250,
            500,
        ],
        index=3,
        format_func=lambda value: f"{value} km",
    )


price_col1, price_col2 = st.columns(2)


with price_col1:

    min_price = st.number_input(
        "Minimum price ($)",
        min_value=0,
        value=0,
        step=50,
    )


with price_col2:

    max_price = st.number_input(
        "Maximum price ($)",
        min_value=0,
        value=1000,
        step=50,
    )


# --------------------------------------------------
# TEMPORARY TEST DATA
# --------------------------------------------------

TEST_LISTINGS = [

    {
        "listing": MarketplaceListing(
            title="Sony PlayStation 5 Disc Edition",
            price=350,
            location="Townsville",
            url="https://example.com/ps5-1",
        ),
        "estimated_value": 550,
    },

    {
        "listing": MarketplaceListing(
            title="PS5 Slim Disc Edition",
            price=500,
            location="Townsville",
            url="https://example.com/ps5-2",
        ),
        "estimated_value": 650,
    },

    {
        "listing": MarketplaceListing(
            title="Apple iPhone 15 Pro 256GB",
            price=700,
            location="Townsville",
            url="https://example.com/iphone15",
        ),
        "estimated_value": 1000,
    },

    {
        "listing": MarketplaceListing(
            title="iPhone 13 128GB",
            price=450,
            location="Townsville",
            url="https://example.com/iphone13",
        ),
        "estimated_value": 650,
    },

    {
        "listing": MarketplaceListing(
            title="Gaming PC RTX 4070",
            price=1200,
            location="Townsville",
            url="https://example.com/gamingpc",
        ),
        "estimated_value": 1700,
    },

]


# --------------------------------------------------
# FIND DEALS
# --------------------------------------------------

if st.button(
    "Find Deals",
    type="primary",
    use_container_width=True,
):

    if not search_query:

        st.warning("Enter something to search for.")

    elif max_price > 0 and min_price > max_price:

        st.warning(
            "Minimum price cannot be greater than maximum price."
        )

    else:

        listings = [
            item["listing"]
            for item in TEST_LISTINGS
        ]


        results = filter_listings(
            listings=listings,
            search_query=search_query,
            min_price=min_price,
            max_price=max_price,
            location=location,
        )


        st.divider()


        # ------------------------------------------
        # NO RESULTS
        # ------------------------------------------

        if not results:

            st.warning("No listings found.")


        # ------------------------------------------
        # RESULTS
        # ------------------------------------------

        else:

            analysed_results = []


            for listing in results:

                estimated_value = next(
                    item["estimated_value"]
                    for item in TEST_LISTINGS
                    if item["listing"].url == listing.url
                )


                deal = calculate_deal(
                    listing_price=listing.price,
                    estimated_value=estimated_value,
                )


                analysed_results.append(
                    {
                        "listing": listing,
                        "deal": deal,
                    }
                )


            # Best deals first
            analysed_results.sort(
                key=lambda item: item["deal"]["deal_score"],
                reverse=True,
            )


            st.subheader(
                f"Found {len(analysed_results)} deal(s)"
            )


            # --------------------------------------
            # DISPLAY DEALS
            # --------------------------------------

            for item in analysed_results:

                listing = item["listing"]
                deal = item["deal"]


                with st.container(border=True):

                    title_col, score_col = st.columns(
                        [4, 1]
                    )


                    with title_col:

                        st.subheader(
                            listing.title
                        )

                        st.caption(
                            f"📍 {listing.location}"
                        )


                    with score_col:

                        st.metric(
                            "Deal Score",
                            f"{deal['deal_score']} / 10",
                        )


                    price_col, value_col, saving_col = (
                        st.columns(3)
                    )


                    with price_col:

                        st.metric(
                            "Asking Price",
                            f"${listing.price:,.0f}",
                        )


                    with value_col:

                        st.metric(
                            "Estimated Value",
                            f"${deal['estimated_value']:,.0f}",
                        )


                    with saving_col:

                        st.metric(
                            "Potential Saving",
                            f"${deal['saving']:,.0f}",
                        )


                    st.write(
                        f"**{deal['discount_percent']}% "
                        f"below estimated market value**"
                    )


                    st.link_button(
                        "View on Marketplace",
                        listing.url,
                    )