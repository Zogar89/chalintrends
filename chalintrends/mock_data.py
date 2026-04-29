from __future__ import annotations

import hashlib
import math
import random

import pandas as pd

from chalintrends.storage import COLUMNS, normalize_price_rows


def _stable_int(value: str) -> int:
    digest = hashlib.blake2b(value.encode("utf-8"), digest_size=8).hexdigest()
    return int(digest, 16)


def _price_text(price: int) -> str:
    return f"{price:,}".replace(",", ".")


def generate_mock_history(prices: pd.DataFrame, days: int = 90, seed: int = 42) -> pd.DataFrame:
    if days < 1:
        raise ValueError("days must be at least 1")
    if prices.empty:
        return prices.copy()

    data = normalize_price_rows(prices)
    data["date"] = pd.to_datetime(data["date"])
    latest_date = data["date"].max()
    latest_rows = data[data["date"] == latest_date].copy()

    rows: list[dict[str, object]] = []
    for _, row in latest_rows.iterrows():
        product_key = f"{row['product_id']}:{row['price_list']}"
        rng = random.Random(seed + _stable_int(product_key))
        phase = rng.uniform(0, math.tau)
        volatility = rng.uniform(0.015, 0.055)
        promo_depth = rng.uniform(0.06, 0.16)
        has_current_promo = _stable_int(product_key + ":promo") % 5 == 0
        base_price = int(row["price"])
        weekly_prices: dict[int, tuple[int, str]] = {
            0: (base_price, str(row["price_text"])),
        }

        for week_block in range(1, ((days - 1) // 7) + 1):
            effective_offset = week_block * 7
            long_term_discount = min(0.34, effective_offset * 0.0014)
            seasonal = math.sin((effective_offset / 9.0) + phase) * volatility
            noise = rng.uniform(-volatility, volatility) * 0.45
            promo_lift = 0.0
            if has_current_promo and effective_offset <= 24:
                promo_lift = promo_depth * (1 - (effective_offset / 25))

            factor = max(0.55, 1 - long_term_discount + seasonal + noise + promo_lift)
            price = max(100, int(round((base_price * factor) / 10) * 10))
            weekly_prices[week_block] = (price, _price_text(price))

        for offset in reversed(range(days)):
            snapshot_date = latest_date - pd.Timedelta(days=offset)
            price, text_price = weekly_prices[offset // 7]

            rows.append(
                {
                    "date": snapshot_date.date().isoformat(),
                    "price_list": row["price_list"],
                    "source_category": row["source_category"],
                    "category": row["category"],
                    "product_id": row["product_id"],
                    "product_name": row["product_name"],
                    "price_text": text_price,
                    "price": price,
                    "source_url": "mock://chalintrends",
                    "captured_at": f"{snapshot_date.date().isoformat()}T09:00:00+00:00",
                }
            )

    return pd.DataFrame(rows, columns=COLUMNS)
