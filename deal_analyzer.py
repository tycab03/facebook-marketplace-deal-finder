def calculate_deal(listing_price: float, estimated_value: float) -> dict:
    """
    Analyse a Marketplace listing against its estimated market value.
    """

    if estimated_value <= 0:
        return {
            "estimated_value": 0,
            "saving": 0,
            "discount_percent": 0,
            "deal_score": 0,
        }

    saving = estimated_value - listing_price
    discount_percent = (saving / estimated_value) * 100

    # Deal score is based on percentage below estimated market value.
    # 50% or more below market value receives a maximum score of 10.
    deal_score = max(0, min(10, discount_percent / 5))

    return {
        "estimated_value": round(estimated_value, 2),
        "saving": round(saving, 2),
        "discount_percent": round(discount_percent, 1),
        "deal_score": round(deal_score, 1),
    }
