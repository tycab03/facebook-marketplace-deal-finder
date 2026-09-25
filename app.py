import streamlit as st

st.set_page_config(
    page_title="Facebook Marketplace Deal Finder",
    page_icon="🔎",
    layout="wide"
)

st.title("Facebook Marketplace Deal Finder")
st.write("Search for items and find potential deals on Facebook Marketplace.")

st.divider()

search_query = st.text_input(
    "Search for an item",
    placeholder="e.g. iPhone 15 Pro, RTX 4070, Toyota Hilux"
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
    placeholder="e.g. Townsville"
)

if st.button("Find Deals", type="primary"):
    if not search_query:
        st.warning("Enter an item to search for.")
    elif max_price > 0 and min_price > max_price:
        st.warning("Minimum price cannot be greater than maximum price.")
    else:
        st.info(
            f"Searching for '{search_query}' between "
            f"${min_price:,} and ${max_price:,}..."
        )
