import streamlit as st

from marketplace_finder import (
    collect_listings,
    filter_listings,
)

from deal_analyzer import rank_deals


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

st.title(
    "Facebook Marketplace Deal Finder"
)

st.write(
    "Search Facebook Marketplace around Townsville "
    "and automatically find potentially underpriced listings."
)

st.caption(
    "Values are estimates based on comparable Marketplace "
    "asking prices, not confirmed sale prices."
)

st.divider()


# --------------------------------------------------
# SEARCH FORM
# --------------------------------------------------

with st.form(
    "marketplace_search"
):

    search_query = st.text_input(
        "What are you looking for?",
        placeholder=(
            "e.g. iPhone 15, RTX 4070, "
            "MacBook Air M2, PS5"
        ),
    )

    col1, col2 = st.columns(
        2
    )

    with col1:

        min_price = st.number_input(
            "Minimum price",
            min_value=0,
            value=0,
            step=50,
        )

    with col2:

        max_price = st.number_input(
            "Maximum price",
            min_value=0,
            value=1000,
            step=50,
        )

    search_button = st.form_submit_button(
        "Search Marketplace",
        type="primary",
    )


# --------------------------------------------------
# SEARCH
# --------------------------------------------------

if search_button:

    # ----------------------------------------------
    # VALIDATION
    # ----------------------------------------------

    search_query = (
        search_query.strip()
    )

    if not search_query:

        st.warning(
            "Enter something to search for."
        )

        st.stop()

    if (
        max_price > 0
        and min_price > max_price
    ):

        st.warning(
            "Minimum price cannot be greater "
            "than maximum price."
        )

        st.stop()

    # ----------------------------------------------
    # COLLECT FACEBOOK RESULTS
    # ----------------------------------------------

    with st.spinner(
        "Searching Facebook Marketplace..."
    ):

        try:

            listings = collect_listings(
                search_query=search_query,
                max_listings=50,
            )

        except Exception as error:

            st.error(
                f"Marketplace search failed: {error}"
            )

            st.stop()

    # ----------------------------------------------
    # BASIC MARKETPLACE FILTERING
    # ----------------------------------------------
    #
    # Do NOT apply the user's price range yet.
    #
    # Higher-priced listings are still useful when
    # estimating the normal market value.
    # ----------------------------------------------

    market_listings = filter_listings(
        listings=listings,
        search_query=search_query,
        min_price=0,
        max_price=0,
    )

    # ----------------------------------------------
    # NO RESULTS
    # ----------------------------------------------

    if not market_listings:

        st.divider()

        st.subheader(
            f"Results for '{search_query}'"
        )

        st.info(
            "No relevant Marketplace listings "
            "were found."
        )

        st.stop()

    # ----------------------------------------------
    # GENERIC DEAL ANALYSIS
    # ----------------------------------------------

    ranked_deals = rank_deals(
        listings=market_listings,
        search_query=search_query,
    )

    # ----------------------------------------------
    # APPLY USER PRICE RANGE AFTER ANALYSIS
    # ----------------------------------------------

    ranked_deals = [
        deal
        for deal in ranked_deals
        if (
            deal["listing"].price
            >= float(min_price)
        )
        and (
            max_price == 0
            or deal["listing"].price
            <= float(max_price)
        )
    ]

    # ----------------------------------------------
    # RESULTS HEADER
    # ----------------------------------------------

    st.divider()

    st.subheader(
        f"Best deals for '{search_query}'"
    )

    st.caption(
        f"{len(ranked_deals)} matching listings "
        f"from {len(market_listings)} Marketplace results."
    )

    # ----------------------------------------------
    # NOTHING IN PRICE RANGE
    # ----------------------------------------------

    if not ranked_deals:

        st.info(
            "Marketplace listings were found, "
            "but none matched your selected "
            "price range."
        )

        st.stop()

    # ----------------------------------------------
    # DISPLAY RESULTS
    # ----------------------------------------------

    for position, deal in enumerate(
        ranked_deals,
        start=1,
    ):

        listing = (
            deal["listing"]
        )

        analysis = (
            deal["analysis"]
        )

        with st.container(
            border=True
        ):

            st.markdown(
                f"### #{position} Deal"
            )

            image_column, info_column = st.columns(
                [1, 2]
            )

            # --------------------------------------
            # IMAGE
            # --------------------------------------

            with image_column:

                if listing.image_url:

                    st.image(
                        listing.image_url,
                        width=300,
                    )

                else:

                    st.caption(
                        "No image available"
                    )

            # --------------------------------------
            # INFORMATION
            # --------------------------------------

            with info_column:

                st.subheader(
                    listing.title
                )

                # ----------------------------------
                # MAIN METRICS
                # ----------------------------------

                price_col, value_col, score_col = (
                    st.columns(3)
                )

                with price_col:

                    st.metric(
                        "Asking Price",
                        f"${listing.price:,.0f}",
                    )

                with value_col:

                    st.metric(
                        "Estimated Asking Value",
                        (
                            f"${analysis['estimated_value']:,.0f}"
                        ),
                    )

                with score_col:

                    st.metric(
                        "Deal Score",
                        (
                            f"{analysis['deal_score']}/10"
                        ),
                    )

                # ----------------------------------
                # SAVING
                # ----------------------------------

                if analysis["saving"] > 0:

                    st.success(
                        f"Potential saving: "
                        f"${analysis['saving']:,.0f} "
                        f"("
                        f"{analysis['discount_percent']:.1f}% "
                        f"below estimated asking value"
                        f")"
                    )

                elif analysis["saving"] == 0:

                    st.caption(
                        "Listed around the estimated "
                        "asking-market value."
                    )

                else:

                    amount_over = abs(
                        analysis["saving"]
                    )

                    st.caption(
                        f"${amount_over:,.0f} above "
                        f"estimated asking value."
                    )

                # ----------------------------------
                # COMPARABLE INFORMATION
                # ----------------------------------

                comparable_count = analysis.get(
                    "comparable_count",
                    0,
                )

                confidence = analysis.get(
                    "confidence",
                    "Low",
                )

                range_low = analysis.get(
                    "price_range_low",
                    0,
                )

                range_high = analysis.get(
                    "price_range_high",
                    0,
                )

                details_col1, details_col2 = (
                    st.columns(2)
                )

                with details_col1:

                    st.write(
                        f"**Comparables:** "
                        f"{comparable_count}"
                    )

                    st.write(
                        f"**Confidence:** "
                        f"{confidence}"
                    )

                with details_col2:

                    if (
                        range_low > 0
                        and range_high > 0
                    ):

                        st.write(
                            "**Comparable price range:** "
                            f"${range_low:,.0f} – "
                            f"${range_high:,.0f}"
                        )

                # ----------------------------------
                # LOW CONFIDENCE WARNING
                # ----------------------------------

                if confidence == "Low":

                    st.warning(
                        "Limited comparable data. "
                        "Treat this valuation with caution."
                    )

                # ----------------------------------
                # LOCATION
                # ----------------------------------

                if listing.location:

                    st.write(
                        f"📍 {listing.location}"
                    )

                # ----------------------------------
                # FACEBOOK LINK
                # ----------------------------------

                st.link_button(
                    "View on Facebook Marketplace",
                    listing.url,
                )