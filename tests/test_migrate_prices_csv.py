from datetime import date, datetime, timezone

import pandas as pd

from chalintrends.storage import COLUMNS, SNAPSHOT_COLUMNS, append_daily_snapshot, load_prices
from scripts.migrate_prices_csv import migrate_prices_csv


def test_migrate_prices_csv_converts_legacy_rows_to_daily_snapshots(tmp_path):
    csv_path = tmp_path / "prices.csv"
    backup_path = tmp_path / "prices.long-backup.csv"
    legacy = pd.DataFrame(
        [
            {
                "date": "2026-04-28",
                "price_list": "salon",
                "source_category": "Carnes",
                "category": "Vacuno medio",
                "product_id": "asado-id",
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
                "product_id": "asado-id",
                "product_name": "Asado",
                "price_text": "17.499",
                "price": 17499,
                "source_url": "source",
                "captured_at": "2026-04-28T12:00:00+00:00",
            },
            {
                "date": "2026-04-29",
                "price_list": "salon",
                "source_category": "Carnes",
                "category": "Vacuno medio",
                "product_id": "asado-id",
                "product_name": "Asado",
                "price_text": "16.499",
                "price": 16499,
                "source_url": "source",
                "captured_at": "2026-04-29T12:00:00+00:00",
            },
        ],
        columns=COLUMNS,
    )
    legacy.to_csv(csv_path, index=False)

    migrate_prices_csv(csv_path, backup_path=backup_path)

    raw = pd.read_csv(csv_path)
    loaded = load_prices(csv_path)
    backup = pd.read_csv(backup_path, dtype={"product_id": "string", "price_text": "string"})

    assert raw.columns.tolist() == SNAPSHOT_COLUMNS
    assert raw["date"].tolist() == ["2026-04-28", "2026-04-29"]
    assert len(loaded) == len(legacy)
    assert loaded[COLUMNS].to_dict("records") == legacy.to_dict("records")
    assert backup.to_dict("records") == legacy.to_dict("records")


def test_migrate_prices_csv_is_idempotent_for_snapshot_format(tmp_path):
    csv_path = tmp_path / "prices.csv"
    append_daily_snapshot(
        csv_path,
        [
            {
                "price_list": "salon",
                "source_category": "Carnes",
                "category": "Vacuno medio",
                "product_id": "asado-id",
                "product_name": "Asado",
                "price_text": "15.999",
                "price": 15999,
                "source_url": "source",
            }
        ],
        snapshot_date=date(2026, 4, 28),
        captured_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )
    before = csv_path.read_text()

    migrate_prices_csv(csv_path)

    assert csv_path.read_text() == before
