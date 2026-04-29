from datetime import date, datetime, timezone

import pandas as pd

from chalintrends.storage import COLUMNS, append_daily_snapshot, load_prices


def test_append_daily_snapshot_is_idempotent_for_same_date(tmp_path):
    csv_path = tmp_path / "prices.csv"
    rows = [
        {
            "price_list": "salon",
            "source_category": "Carnes",
            "category": "Vacuno medio",
            "product_id": "asado-id",
            "product_name": "Asado",
            "price_text": "15.999",
            "price": 15999,
            "source_url": "https://precios.chalincarnespremium.com.ar",
        }
    ]

    append_daily_snapshot(
        csv_path,
        rows,
        snapshot_date=date(2026, 4, 28),
        captured_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )
    append_daily_snapshot(
        csv_path,
        rows,
        snapshot_date=date(2026, 4, 28),
        captured_at=datetime(2026, 4, 28, 12, 5, tzinfo=timezone.utc),
    )

    df = pd.read_csv(csv_path)
    assert len(df) == 1
    assert df.loc[0, "date"] == "2026-04-28"
    assert df.loc[0, "price_list"] == "salon"
    assert df.loc[0, "source_category"] == "Carnes"
    assert df.loc[0, "category"] == "Vacuno medio"
    assert df.loc[0, "price"] == 15999


def test_load_prices_migrates_legacy_category_to_source_category(tmp_path):
    csv_path = tmp_path / "prices.csv"
    pd.DataFrame(
        [
            {
                "date": "2026-04-28",
                "price_list": "salon",
                "category": "Carnes",
                "product_id": "lomo-id",
                "product_name": "Lomo",
                "price_text": "24.999",
                "price": 24999,
                "source_url": "source",
                "captured_at": "2026-04-28T12:00:00+00:00",
            }
        ]
    ).to_csv(csv_path, index=False)

    loaded = load_prices(csv_path)

    assert loaded.columns.tolist() == COLUMNS
    assert loaded.loc[0, "source_category"] == "Carnes"
    assert loaded.loc[0, "category"] == "Vacuno premium"
