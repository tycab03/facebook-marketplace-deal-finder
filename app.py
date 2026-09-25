import streamlit as st

from marketplace_finder import (
    collect_listings,
    filter_listings,
)


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
    "Search Facebook Marketplace around Townsville "
    "and find listings that match your price range."
)

st.divider()


# --------------------------------------------------
# SEARCH FORM
# --------------------------------------------------

with st.form("marketplace_search"):

    search_query = st.text_input(
        "What are you looking for?",
        placeholder="e.g. PS5, iPhone 15, RTX 4070",
    )

    col1, col2 = st.columns(2)

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

    if not search_query.strip():

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
    # COLLECT LISTINGS
    # ----------------------------------------------

    with st.spinner(
        "Opening Facebook Marketplace..."
    ):

        try:

            listings = collect_listings(
                search_query=search_query,
                max_listings=30,
            )

        except Exception as error:

            st.error(
                f"Marketplace search failed: {error}"
            )

            st.stop()

    # ----------------------------------------------
    # FILTER RESULTS
    # ----------------------------------------------

    filtered_listings = filter_listings(
        listings=listings,
        search_query=search_query,
        min_price=float(min_price),
        max_price=float(max_price),
    )

    # ----------------------------------------------
    # RESULTS HEADER
    # ----------------------------------------------

    st.divider()

    st.subheader(
        f"Results for '{search_query}'"
    )

    st.caption(
        f"{len(filtered_listings)} matching listings found"
    )

    # ----------------------------------------------
    # NO RESULTS
    # ----------------------------------------------

    if not filtered_listings:

        st.info(
            "No matching listings were found."
        )

    # ----------------------------------------------
    # DISPLAY RESULTS
    # ----------------------------------------------

    else:

        for listing in filtered_listings:

            with st.container(
                border=True
            ):

                image_column, info_column = st.columns(
                    [1, 2]
                )

                # ------------------------------
                # IMAGE
                # ------------------------------

                with image_column:

                    if listing.image_url:

                        st.image(listing.image_url,
                                 width=300,
                                 )

                    else:

                        st.write(
                            "No image available"
                        )

                # ------------------------------
                # INFORMATION
                # ------------------------------

                with info_column:

                    st.subheader(
                        listing.title
                    )

                    st.metric(
                        "Asking Price",
                        f"${listing.price:,.0f}",
                    )

                    if listing.location:

                        st.write(
                            f"📍 {listing.location}"
                        )

                    st.link_button(
                        "View on Facebook Marketplace",
                        listing.url,
                    )