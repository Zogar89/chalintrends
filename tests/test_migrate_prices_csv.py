from datetime import date, datetime, timezone

import pandas as pd

from chalintrends.storage import COLUMNS, append_daily_snapshot, load_prices
from scripts.migrate_prices_csv import migrate_prices_csv

SNAPSHOT_BASE_COLUMNS = ["date", "captured_at"]


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

    assert raw.columns.tolist() == [
        *SNAPSHOT_BASE_COLUMNS,
        "delivery | Asado | source_category",
        "delivery | Asado | category",
        "delivery | Asado | product_id",
        "delivery | Asado | price_text",
        "delivery | Asado | price",
        "delivery | Asado | source_url",
        "salon | Asado | source_category",
        "salon | Asado | category",
        "salon | Asado | product_id",
        "salon | Asado | price_text",
        "salon | Asado | price",
        "salon | Asado | source_url",
    ]
    assert raw["date"].tolist() == ["2026-04-28", "2026-04-29"]
    assert raw.loc[0, "salon | Asado | price"] == 15999
    assert raw.loc[0, "delivery | Asado | price"] == 17499
    assert raw.loc[1, "salon | Asado | price"] == 16499
    assert len(loaded) == len(legacy)
    loaded_records = loaded[COLUMNS].sort_values(["date", "price_list", "product_name"]).reset_index(drop=True)
    legacy_records = legacy.sort_values(["date", "price_list", "product_name"]).reset_index(drop=True)
    assert loaded_records.to_dict("records") == legacy_records.to_dict("records")
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


def test_migrate_prices_csv_does_not_overwrite_existing_default_backup(tmp_path):
    csv_path = tmp_path / "prices.csv"
    existing_backup_path = tmp_path / "prices.long-backup.csv"
    existing_backup_text = "keep,this\nbackup,safe\n"
    existing_backup_path.write_text(existing_backup_text)
    pd.DataFrame(
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
            }
        ],
        columns=COLUMNS,
    ).to_csv(csv_path, index=False)

    migrate_prices_csv(csv_path)

    assert existing_backup_path.read_text() == existing_backup_text
    assert (tmp_path / "prices.long-backup-1.csv").exists()
