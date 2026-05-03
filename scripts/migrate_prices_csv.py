from __future__ import annotations

from pathlib import Path
import shutil

import pandas as pd

from chalintrends.storage import SNAPSHOT_COLUMNS, load_prices, write_daily_snapshots

DATA_PATH = Path("data/prices.csv")


def is_snapshot_csv(csv_path: Path) -> bool:
    if not csv_path.exists():
        return False
    columns = pd.read_csv(csv_path, nrows=0).columns.tolist()
    return columns == SNAPSHOT_COLUMNS


def migrate_prices_csv(csv_path: Path = DATA_PATH, *, backup_path: Path | None = None) -> bool:
    if is_snapshot_csv(csv_path):
        return False

    if backup_path is None:
        backup_path = csv_path.with_name(f"{csv_path.stem}.long-backup{csv_path.suffix}")

    prices = load_prices(csv_path)
    shutil.copy2(csv_path, backup_path)
    write_daily_snapshots(csv_path, prices)
    return True


def main() -> None:
    migrated = migrate_prices_csv()
    if migrated:
        print(f"Migrated {DATA_PATH} to daily snapshot format.")
    else:
        print(f"{DATA_PATH} is already in daily snapshot format.")


if __name__ == "__main__":
    main()
