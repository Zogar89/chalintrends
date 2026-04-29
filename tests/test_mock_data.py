import pandas as pd

from chalintrends.mock_data import generate_mock_history


def test_generate_mock_history_preserves_latest_prices_and_shape():
    latest = pd.DataFrame(
        [
            {
                "date": "2026-04-28",
                "price_list": "salon",
                "source_category": "Carnes",
                "category": "Vacuno medio",
                "product_id": "asado",
                "product_name": "Asado",
                "price_text": "15.999",
                "price": 15999,
                "source_url": "source",
                "captured_at": "2026-04-28T12:00:00+00:00",
            },
            {
                "date": "2026-04-28",
                "price_list": "delivery",
                "source_category": "Carnes",
                "category": "Vacuno medio",
                "product_id": "asado",
                "product_name": "Asado",
                "price_text": "17.499",
                "price": 17499,
                "source_url": "source",
                "captured_at": "2026-04-28T12:00:00+00:00",
            },
        ]
    )

    history = generate_mock_history(latest, days=10, seed=7)

    assert len(history) == 20
    assert history["date"].nunique() == 10

    last_day = history[history["date"] == "2026-04-28"].sort_values("price_list")
    assert last_day["price"].tolist() == [17499, 15999]
    assert last_day["price_text"].tolist() == ["17.499", "15.999"]


def test_generate_mock_history_defaults_to_three_months():
    latest = pd.DataFrame(
        [
            {
                "date": "2026-04-28",
                "price_list": "salon",
                "source_category": "Carnes",
                "category": "Vacuno medio",
                "product_id": "asado",
                "product_name": "Asado",
                "price_text": "15.999",
                "price": 15999,
                "source_url": "source",
                "captured_at": "2026-04-28T12:00:00+00:00",
            }
        ]
    )

    history = generate_mock_history(latest, seed=7)

    assert history["date"].nunique() == 90


def test_generate_mock_history_keeps_prices_stable_within_weekly_blocks():
    latest = pd.DataFrame(
        [
            {
                "date": "2026-04-28",
                "price_list": "salon",
                "source_category": "Carnes",
                "category": "Vacuno medio",
                "product_id": "asado",
                "product_name": "Asado",
                "price_text": "15.999",
                "price": 15999,
                "source_url": "source",
                "captured_at": "2026-04-28T12:00:00+00:00",
            }
        ]
    )

    history = generate_mock_history(latest, days=21, seed=7)
    history["date"] = pd.to_datetime(history["date"])
    latest_date = history["date"].max()
    history["week_block"] = ((latest_date - history["date"]).dt.days // 7)

    prices_by_week = history.groupby("week_block")["price"].nunique()

    assert prices_by_week.tolist() == [1, 1, 1]


def test_generate_mock_history_preserves_source_category():
    latest = pd.DataFrame(
        [
            {
                "date": "2026-04-28",
                "price_list": "salon",
                "source_category": "Carnes",
                "category": "Vacuno premium",
                "product_id": "lomo",
                "product_name": "Lomo",
                "price_text": "24.999",
                "price": 24999,
                "source_url": "source",
                "captured_at": "2026-04-28T12:00:00+00:00",
            }
        ]
    )

    history = generate_mock_history(latest, days=2, seed=7)

    assert history["source_category"].unique().tolist() == ["Carnes"]
    assert history["category"].unique().tolist() == ["Vacuno premium"]


def test_generate_mock_history_accepts_legacy_rows_without_source_category():
    latest = pd.DataFrame(
        [
            {
                "date": "2026-04-28",
                "price_list": "salon",
                "category": "Carnes",
                "product_id": "lomo",
                "product_name": "Lomo",
                "price_text": "24.999",
                "price": 24999,
                "source_url": "source",
                "captured_at": "2026-04-28T12:00:00+00:00",
            }
        ]
    )

    history = generate_mock_history(latest, days=2, seed=7)

    assert history["source_category"].unique().tolist() == ["Carnes"]
    assert history["category"].unique().tolist() == ["Vacuno premium"]
