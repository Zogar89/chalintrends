import pandas as pd

from chalintrends import analytics
from chalintrends.analytics import latest_offers


def test_latest_offers_compares_against_30_day_reference_and_recent_median():
    df = pd.DataFrame(
        [
            {
                "date": "2026-03-29",
                "price_list": "salon",
                "product_id": "asado",
                "product_name": "Asado",
                "category": "Carnes",
                "price": 18000,
            },
            {
                "date": "2026-04-27",
                "price_list": "salon",
                "product_id": "asado",
                "product_name": "Asado",
                "category": "Carnes",
                "price": 17000,
            },
            {
                "date": "2026-04-28",
                "price_list": "salon",
                "product_id": "asado",
                "product_name": "Asado",
                "category": "Carnes",
                "price": 15000,
            },
            {
                "date": "2026-03-29",
                "price_list": "salon",
                "product_id": "lomo",
                "product_name": "Lomo",
                "category": "Carnes",
                "price": 24000,
            },
            {
                "date": "2026-04-27",
                "price_list": "salon",
                "product_id": "lomo",
                "product_name": "Lomo",
                "category": "Carnes",
                "price": 24500,
            },
            {
                "date": "2026-04-28",
                "price_list": "salon",
                "product_id": "lomo",
                "product_name": "Lomo",
                "category": "Carnes",
                "price": 25000,
            },
        ]
    )

    offers = latest_offers(df, price_list="salon", window_days=30)

    asado = offers.loc[offers["product_id"] == "asado"].iloc[0]
    lomo = offers.loc[offers["product_id"] == "lomo"].iloc[0]
    assert bool(asado["dropped_today"]) is True
    assert bool(asado["dropped_since_comparison"]) is True
    assert bool(asado["below_recent_median"]) is True
    assert asado["change"] == -3000
    assert round(asado["change_pct"], 2) == -16.67
    assert bool(lomo["dropped_today"]) is False


def test_salon_delivery_average_surcharge_uses_latest_items_with_both_prices():
    df = pd.DataFrame(
        [
            {
                "date": "2026-04-27",
                "price_list": "salon",
                "product_id": "asado",
                "product_name": "Asado",
                "category": "Carnes",
                "price": 900,
            },
            {
                "date": "2026-04-27",
                "price_list": "delivery",
                "product_id": "asado",
                "product_name": "Asado",
                "category": "Carnes",
                "price": 990,
            },
            {
                "date": "2026-04-28",
                "price_list": "salon",
                "product_id": "asado",
                "product_name": "Asado",
                "category": "Carnes",
                "price": 1000,
            },
            {
                "date": "2026-04-28",
                "price_list": "delivery",
                "product_id": "asado",
                "product_name": "Asado",
                "category": "Carnes",
                "price": 1100,
            },
            {
                "date": "2026-04-28",
                "price_list": "salon",
                "product_id": "lomo",
                "product_name": "Lomo",
                "category": "Carnes",
                "price": 2000,
            },
            {
                "date": "2026-04-28",
                "price_list": "delivery",
                "product_id": "lomo",
                "product_name": "Lomo",
                "category": "Carnes",
                "price": 2600,
            },
            {
                "date": "2026-04-28",
                "price_list": "salon",
                "product_id": "pollo",
                "product_name": "Pollo",
                "category": "Carnes",
                "price": 1500,
            },
        ]
    )

    comparison = analytics.salon_delivery_comparison(df)

    asado = comparison.loc[comparison["product_name"] == "Asado"].iloc[0]
    lomo = comparison.loc[comparison["product_name"] == "Lomo"].iloc[0]
    pollo = comparison.loc[comparison["product_name"] == "Pollo"].iloc[0]
    assert asado["delivery_minus_salon"] == 100
    assert round(asado["delivery_pct_over_salon"], 2) == 10
    assert lomo["delivery_minus_salon"] == 600
    assert round(lomo["delivery_pct_over_salon"], 2) == 30
    assert pd.isna(pollo["delivery_pct_over_salon"])
    assert analytics.average_delivery_pct_over_salon(comparison) == 20
