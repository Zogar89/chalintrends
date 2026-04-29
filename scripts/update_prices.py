from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

import requests

from chalintrends.fetch import PricePayloadError, fetch_price_payload, parse_price_payload
from chalintrends.storage import append_daily_snapshot

DATA_PATH = Path("data/prices.csv")


def main() -> None:
    now = datetime.now(timezone.utc)
    try:
        payload = fetch_price_payload()
        rows = parse_price_payload(payload)
    except (PricePayloadError, requests.RequestException) as exc:
        print(f"Price update failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    changed = append_daily_snapshot(DATA_PATH, rows, snapshot_date=now.date(), captured_at=now)
    if changed:
        print(f"Stored {len(rows)} price rows for {now.date().isoformat()}.")
    else:
        print(f"Prices for {now.date().isoformat()} already exist. No changes made.")


if __name__ == "__main__":
    main()
