from __future__ import annotations

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
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def load_prices(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame(columns=COLUMNS)
    prices = pd.read_csv(csv_path, dtype={"product_id": "string", "price_text": "string"})
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
    neutralize_csv_formulas(combined).to_csv(csv_path, index=False)
    return True
