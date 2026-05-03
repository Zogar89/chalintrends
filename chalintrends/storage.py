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
SNAPSHOT_BASE_COLUMNS = ["date", "captured_at"]
JSON_SNAPSHOT_COLUMNS = [*SNAPSHOT_BASE_COLUMNS, "items_json"]
WIDE_ITEM_FIELDS = ["source_category", "category", "product_id", "price_text", "price", "source_url"]
CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
SNAPSHOT_COLUMN_SEPARATOR = " | "


def load_prices(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame(columns=COLUMNS)
    prices = pd.read_csv(csv_path, dtype="string")
    if "items_json" in prices.columns:
        return expand_json_snapshots(prices)
    if is_wide_snapshot_frame(prices):
        return expand_wide_snapshots(prices)
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

    normalized["price"] = pd.to_numeric(normalized["price"], errors="coerce")

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


def snapshot_column(price_list: Any, product_name: Any, field: str) -> str:
    return SNAPSHOT_COLUMN_SEPARATOR.join([str(price_list), str(product_name), field])


def parse_snapshot_column(column: str) -> tuple[str, str, str] | None:
    parts = column.split(SNAPSHOT_COLUMN_SEPARATOR)
    if len(parts) < 3 or parts[-1] not in WIDE_ITEM_FIELDS:
        return None
    return parts[0], SNAPSHOT_COLUMN_SEPARATOR.join(parts[1:-1]), parts[-1]


def is_wide_snapshot_frame(rows: pd.DataFrame) -> bool:
    return all(column in rows.columns for column in SNAPSHOT_BASE_COLUMNS) and any(
        parse_snapshot_column(column) is not None for column in rows.columns
    )


def daily_snapshots_from_prices(rows: pd.DataFrame) -> pd.DataFrame:
    normalized = normalize_price_rows(rows)
    if normalized.empty:
        return pd.DataFrame(columns=SNAPSHOT_BASE_COLUMNS)

    snapshots = []
    for snapshot_date, group in normalized.groupby("date", sort=True, dropna=False):
        captured_at = str(group["captured_at"].dropna().max() if group["captured_at"].notna().any() else "")
        snapshot = {"date": str(snapshot_date), "captured_at": captured_at}
        group = group.sort_values(["price_list", "product_name"], kind="stable")
        for item in group.to_dict("records"):
            for field in WIDE_ITEM_FIELDS:
                snapshot[snapshot_column(item["price_list"], item["product_name"], field)] = _json_safe(item[field])
        snapshots.append(snapshot)

    columns = [*SNAPSHOT_BASE_COLUMNS]
    item_columns = sorted(
        {column for snapshot in snapshots for column in snapshot if column not in SNAPSHOT_BASE_COLUMNS},
        key=lambda column: (*parse_snapshot_column(column)[:2], WIDE_ITEM_FIELDS.index(parse_snapshot_column(column)[2])),
    )
    columns.extend(item_columns)

    return pd.DataFrame(snapshots, columns=columns)


def expand_json_snapshots(snapshots: pd.DataFrame) -> pd.DataFrame:
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


def expand_wide_snapshots(snapshots: pd.DataFrame) -> pd.DataFrame:
    if snapshots.empty:
        return pd.DataFrame(columns=COLUMNS)

    rows = []
    for _, snapshot in snapshots.iterrows():
        items: dict[tuple[str, str], dict[str, Any]] = {}
        for column in snapshots.columns:
            parsed = parse_snapshot_column(column)
            if parsed is None:
                continue
            price_list, product_name, field = parsed
            value = snapshot[column]
            if pd.isna(value):
                continue
            items.setdefault((price_list, product_name), {})[field] = value
        for (price_list, product_name), item in items.items():
            if not any(field in item for field in WIDE_ITEM_FIELDS):
                continue
            row = dict(item)
            row["price_list"] = price_list
            row["product_name"] = product_name
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
