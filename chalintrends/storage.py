from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from chalintrends.categories import categorize_product

COLUMNS = [
    "date",
    "price_list",
    "source_category",
    "category",
    "product_id",
    "product_name",
    "price_text",
    "price",
    "source_url",
    "captured_at",
]
ITEM_COLUMNS = [column for column in COLUMNS if column not in {"date", "captured_at"}]
SNAPSHOT_COLUMNS = ["date", "captured_at", "items_json"]
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def load_prices(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame(columns=COLUMNS)
    prices = pd.read_csv(
        csv_path,
        dtype={"product_id": "string", "price_text": "string", "items_json": "string"},
    )
    if "items_json" in prices.columns:
        return expand_daily_snapshots(prices)
    return normalize_price_rows(prices)


def normalize_price_rows(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame(columns=COLUMNS)

    normalized = rows.copy()
    if "source_category" not in normalized.columns:
        normalized["source_category"] = normalized["category"]
        normalized["category"] = normalized.apply(
            lambda row: categorize_product(str(row["product_name"]), str(row["source_category"])),
            axis=1,
        )

    for column in COLUMNS:
        if column not in normalized.columns:
            normalized[column] = pd.NA

    return normalized[COLUMNS]


def neutralize_csv_formula(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(CSV_FORMULA_PREFIXES):
        return "'" + value
    return value


def neutralize_csv_formulas(rows: pd.DataFrame) -> pd.DataFrame:
    neutralized = rows.copy()
    for column in neutralized.select_dtypes(include=["object", "string"]).columns:
        neutralized[column] = neutralized[column].map(neutralize_csv_formula)
    return neutralized


def _json_safe(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def daily_snapshots_from_prices(rows: pd.DataFrame) -> pd.DataFrame:
    normalized = normalize_price_rows(rows)
    if normalized.empty:
        return pd.DataFrame(columns=SNAPSHOT_COLUMNS)

    snapshots = []
    for snapshot_date, group in normalized.groupby("date", sort=True, dropna=False):
        captured_at = str(group["captured_at"].dropna().max() if group["captured_at"].notna().any() else "")
        items = []
        for item in group[ITEM_COLUMNS].to_dict("records"):
            items.append({column: _json_safe(item[column]) for column in ITEM_COLUMNS})
        snapshots.append(
            {
                "date": str(snapshot_date),
                "captured_at": captured_at,
                "items_json": json.dumps(items, ensure_ascii=False, separators=(",", ":")),
            }
        )

    return pd.DataFrame(snapshots, columns=SNAPSHOT_COLUMNS)


def expand_daily_snapshots(snapshots: pd.DataFrame) -> pd.DataFrame:
    if snapshots.empty:
        return pd.DataFrame(columns=COLUMNS)

    rows = []
    for _, snapshot in snapshots.iterrows():
        items = json.loads(str(snapshot["items_json"]))
        if not isinstance(items, list):
            raise ValueError("items_json must contain a list of price items.")
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("items_json price items must be objects.")
            row = dict(item)
            row["date"] = snapshot["date"]
            row["captured_at"] = snapshot["captured_at"]
            rows.append(row)

    return normalize_price_rows(pd.DataFrame(rows))


def write_daily_snapshots(csv_path: Path, rows: pd.DataFrame) -> None:
    daily_snapshots_from_prices(rows).to_csv(csv_path, index=False)


def append_daily_snapshot(
    csv_path: Path,
    rows: list[dict[str, Any]],
    snapshot_date: date,
    captured_at: datetime,
) -> bool:
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    existing = load_prices(csv_path)
    date_text = snapshot_date.isoformat()

    daily = pd.DataFrame(rows)
    daily.insert(0, "date", date_text)
    daily["captured_at"] = captured_at.isoformat()
    daily = normalize_price_rows(daily)

    if existing.empty:
        previous_days = existing
    else:
        previous_days = existing[existing["date"] != date_text]

    combined = pd.concat([previous_days, daily], ignore_index=True)
    write_daily_snapshots(csv_path, neutralize_csv_formulas(combined))
    return True
