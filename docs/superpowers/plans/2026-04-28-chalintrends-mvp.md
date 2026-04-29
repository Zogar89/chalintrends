# ChalinTrends MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first usable ChalinTrends MVP with daily price capture, CSV storage, trend calculations, and a Streamlit mobile-friendly dashboard.

**Architecture:** A small Python package under `chalintrends/` owns fetching, parsing, storage, and analytics. Streamlit reads the CSV and renders dashboard views. GitHub Actions runs the scraper once per day and commits CSV changes.

**Tech Stack:** Python, requests, pandas, Streamlit, pytest, GitHub Actions, CSV.

---

## File Structure

- `pyproject.toml`: project metadata and dependencies.
- `README.md`: setup, local run, and deployment notes.
- `.github/workflows/daily-prices.yml`: scheduled scraper workflow.
- `chalintrends/__init__.py`: package marker.
- `chalintrends/fetch.py`: API request and JSON parsing.
- `chalintrends/storage.py`: CSV append/load behavior.
- `chalintrends/analytics.py`: trend and offer calculations.
- `scripts/update_prices.py`: daily scraper entrypoint.
- `streamlit_app.py`: Streamlit UI.
- `data/prices.csv`: created by scraper when data exists.
- `tests/test_fetch.py`: parser tests.
- `tests/test_storage.py`: storage tests.
- `tests/test_analytics.py`: trend tests.

## Task 1: Project Skeleton And Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `chalintrends/__init__.py`

- [ ] **Step 1: Create project metadata**

Write `pyproject.toml` with runtime and test dependencies:

```toml
[project]
name = "chalintrends"
version = "0.1.0"
description = "Personal Streamlit tracker for Chalin Carnes Premium prices."
requires-python = ">=3.11"
dependencies = [
  "pandas>=2.2",
  "requests>=2.32",
  "streamlit>=1.35",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create package marker**

Write `chalintrends/__init__.py`:

```python
"""ChalinTrends package."""
```

- [ ] **Step 3: Create README**

Write `README.md` with:

```markdown
# ChalinTrends

Personal Streamlit app for tracking Salon and Delivery prices from Chalin Carnes Premium.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

## Update prices

```powershell
python scripts/update_prices.py
```

## Run app

```powershell
streamlit run streamlit_app.py
```
```

- [ ] **Step 4: Commit**

Run:

```powershell
git add pyproject.toml README.md chalintrends/__init__.py .gitignore
git commit -m "chore: scaffold ChalinTrends project"
```

## Task 2: Fetch And Parse API Data

**Files:**
- Create: `tests/test_fetch.py`
- Create: `chalintrends/fetch.py`

- [ ] **Step 1: Write failing parser test**

Create `tests/test_fetch.py`:

```python
from chalintrends.fetch import parse_price_payload


def test_parse_price_payload_returns_rows_for_salon_and_delivery():
    payload = {
        "status": "success",
        "data": {
            "url": "https://precios.chalincarnespremium.com.ar",
            "listas": [
                {
                    "descripcion": "Salón",
                    "grupos": [
                        {
                            "descripcion": "Carnes",
                            "productos": [
                                {
                                    "id_producto": "asado-id",
                                    "descripcion": "Asado",
                                    "precio": "15.999",
                                    "precio_numerico": 15999,
                                }
                            ],
                        }
                    ],
                },
                {
                    "descripcion": "Reparto",
                    "grupos": [
                        {
                            "descripcion": "Carnes",
                            "productos": [
                                {
                                    "id_producto": "asado-id",
                                    "descripcion": "Asado",
                                    "precio": "17.499",
                                    "precio_numerico": 17499,
                                }
                            ],
                        }
                    ],
                },
            ],
        },
    }

    rows = parse_price_payload(payload)

    assert rows == [
        {
            "price_list": "salon",
            "category": "Carnes",
            "product_id": "asado-id",
            "product_name": "Asado",
            "price_text": "15.999",
            "price": 15999,
            "source_url": "https://precios.chalincarnespremium.com.ar",
        },
        {
            "price_list": "delivery",
            "category": "Carnes",
            "product_id": "asado-id",
            "product_name": "Asado",
            "price_text": "17.499",
            "price": 17499,
            "source_url": "https://precios.chalincarnespremium.com.ar",
        },
    ]
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
pytest tests/test_fetch.py -v
```

Expected: FAIL because `chalintrends.fetch` does not exist.

- [ ] **Step 3: Implement fetch module**

Create `chalintrends/fetch.py`:

```python
from __future__ import annotations

from typing import Any

import requests

API_URL = "https://api.chalincarnespremium.com.ar/precios/lista"
USER_AGENT = "ChalinTrends/0.1 personal price tracker"


PRICE_LIST_NAMES = {
    "Salón": "salon",
    "Salon": "salon",
    "Reparto": "delivery",
}


def fetch_price_payload(timeout: int = 20) -> dict[str, Any]:
    response = requests.get(
        API_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/plain"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def parse_price_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data") or {}
    source_url = data.get("url") or API_URL
    rows: list[dict[str, Any]] = []

    for price_list in data.get("listas", []):
        list_name = PRICE_LIST_NAMES.get(price_list.get("descripcion"))
        if list_name is None:
            continue

        for group in price_list.get("grupos", []):
            category = group.get("descripcion", "")
            for product in group.get("productos", []):
                rows.append(
                    {
                        "price_list": list_name,
                        "category": category,
                        "product_id": product["id_producto"],
                        "product_name": product["descripcion"],
                        "price_text": product["precio"],
                        "price": int(product["precio_numerico"]),
                        "source_url": source_url,
                    }
                )

    return rows
```

- [ ] **Step 4: Run test and verify it passes**

Run:

```powershell
pytest tests/test_fetch.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add tests/test_fetch.py chalintrends/fetch.py
git commit -m "feat: parse Chalin price API"
```

## Task 3: CSV Storage

**Files:**
- Create: `tests/test_storage.py`
- Create: `chalintrends/storage.py`

- [ ] **Step 1: Write failing storage test**

Create `tests/test_storage.py`:

```python
from datetime import date, datetime, timezone

import pandas as pd

from chalintrends.storage import append_daily_snapshot


def test_append_daily_snapshot_is_idempotent_for_same_date(tmp_path):
    csv_path = tmp_path / "prices.csv"
    rows = [
        {
            "price_list": "salon",
            "category": "Carnes",
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
    assert df.loc[0, "price"] == 15999
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
pytest tests/test_storage.py -v
```

Expected: FAIL because `chalintrends.storage` does not exist.

- [ ] **Step 3: Implement storage module**

Create `chalintrends/storage.py`:

```python
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

COLUMNS = [
    "date",
    "price_list",
    "category",
    "product_id",
    "product_name",
    "price_text",
    "price",
    "source_url",
    "captured_at",
]


def load_prices(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(csv_path, dtype={"product_id": "string"})


def append_daily_snapshot(
    csv_path: Path,
    rows: list[dict[str, Any]],
    snapshot_date: date,
    captured_at: datetime,
) -> bool:
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    existing = load_prices(csv_path)
    date_text = snapshot_date.isoformat()
    if not existing.empty and (existing["date"] == date_text).any():
        return False

    daily = pd.DataFrame(rows)
    daily.insert(0, "date", date_text)
    daily["captured_at"] = captured_at.isoformat()
    daily = daily[COLUMNS]

    combined = pd.concat([existing, daily], ignore_index=True)
    combined.to_csv(csv_path, index=False)
    return True
```

- [ ] **Step 4: Run test and verify it passes**

Run:

```powershell
pytest tests/test_storage.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add tests/test_storage.py chalintrends/storage.py
git commit -m "feat: store daily price snapshots"
```

## Task 4: Analytics

**Files:**
- Create: `tests/test_analytics.py`
- Create: `chalintrends/analytics.py`

- [ ] **Step 1: Write failing analytics test**

Create `tests/test_analytics.py`:

```python
import pandas as pd

from chalintrends.analytics import latest_offers


def test_latest_offers_detects_drops_and_below_recent_median():
    df = pd.DataFrame(
        [
            {"date": "2026-04-26", "price_list": "salon", "product_id": "asado", "product_name": "Asado", "category": "Carnes", "price": 18000},
            {"date": "2026-04-27", "price_list": "salon", "product_id": "asado", "product_name": "Asado", "category": "Carnes", "price": 17000},
            {"date": "2026-04-28", "price_list": "salon", "product_id": "asado", "product_name": "Asado", "category": "Carnes", "price": 15000},
            {"date": "2026-04-26", "price_list": "salon", "product_id": "lomo", "product_name": "Lomo", "category": "Carnes", "price": 24000},
            {"date": "2026-04-27", "price_list": "salon", "product_id": "lomo", "product_name": "Lomo", "category": "Carnes", "price": 24500},
            {"date": "2026-04-28", "price_list": "salon", "product_id": "lomo", "product_name": "Lomo", "category": "Carnes", "price": 25000},
        ]
    )

    offers = latest_offers(df, price_list="salon", window_days=30)

    asado = offers.loc[offers["product_id"] == "asado"].iloc[0]
    lomo = offers.loc[offers["product_id"] == "lomo"].iloc[0]
    assert bool(asado["dropped_today"]) is True
    assert bool(asado["below_recent_median"]) is True
    assert round(asado["change_pct"], 2) == -11.76
    assert bool(lomo["dropped_today"]) is False
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```powershell
pytest tests/test_analytics.py -v
```

Expected: FAIL because `chalintrends.analytics` does not exist.

- [ ] **Step 3: Implement analytics module**

Create `chalintrends/analytics.py`:

```python
from __future__ import annotations

import pandas as pd


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared["date"] = pd.to_datetime(prepared["date"])
    prepared["price"] = pd.to_numeric(prepared["price"])
    return prepared.sort_values(["price_list", "product_id", "date"])


def latest_offers(df: pd.DataFrame, price_list: str, window_days: int = 30) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    data = _prepare(df)
    data = data[data["price_list"] == price_list]
    if data.empty:
        return pd.DataFrame()

    latest_date = data["date"].max()
    window_start = latest_date - pd.Timedelta(days=window_days)
    recent = data[data["date"] >= window_start]

    latest = data[data["date"] == latest_date].copy()
    previous = (
        data[data["date"] < latest_date]
        .sort_values("date")
        .groupby("product_id")
        .tail(1)[["product_id", "price"]]
        .rename(columns={"price": "previous_price"})
    )
    medians = (
        recent.groupby("product_id")["price"]
        .median()
        .reset_index()
        .rename(columns={"price": "recent_median"})
    )

    result = latest.merge(previous, on="product_id", how="left").merge(medians, on="product_id", how="left")
    result["change"] = result["price"] - result["previous_price"]
    result["change_pct"] = (result["change"] / result["previous_price"]) * 100
    result["dropped_today"] = result["change"] < 0
    result["below_recent_median"] = result["price"] < result["recent_median"]
    result["opportunity"] = result["dropped_today"] | result["below_recent_median"]
    return result.sort_values(["opportunity", "change_pct"], ascending=[False, True])


def category_daily_prices(df: pd.DataFrame, price_list: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    data = _prepare(df)
    data = data[data["price_list"] == price_list]
    return (
        data.groupby(["date", "category"], as_index=False)["price"]
        .median()
        .rename(columns={"price": "median_price"})
    )
```

- [ ] **Step 4: Run test and verify it passes**

Run:

```powershell
pytest tests/test_analytics.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add tests/test_analytics.py chalintrends/analytics.py
git commit -m "feat: calculate price opportunities"
```

## Task 5: Daily Update Script

**Files:**
- Create: `scripts/update_prices.py`

- [ ] **Step 1: Create update script**

Create `scripts/update_prices.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from chalintrends.fetch import fetch_price_payload, parse_price_payload
from chalintrends.storage import append_daily_snapshot

DATA_PATH = Path("data/prices.csv")


def main() -> None:
    now = datetime.now(timezone.utc)
    payload = fetch_price_payload()
    rows = parse_price_payload(payload)
    changed = append_daily_snapshot(DATA_PATH, rows, snapshot_date=now.date(), captured_at=now)
    if changed:
        print(f"Stored {len(rows)} price rows for {now.date().isoformat()}.")
    else:
        print(f"Prices for {now.date().isoformat()} already exist. No changes made.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run update script**

Run:

```powershell
python scripts/update_prices.py
```

Expected: creates `data/prices.csv` and prints stored row count.

- [ ] **Step 3: Commit**

Run:

```powershell
git add scripts/update_prices.py data/prices.csv
git commit -m "feat: add daily price updater"
```

## Task 6: Streamlit Dashboard

**Files:**
- Create: `streamlit_app.py`

- [ ] **Step 1: Create Streamlit app**

Create `streamlit_app.py`:

```python
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from chalintrends.analytics import category_daily_prices, latest_offers
from chalintrends.storage import load_prices

DATA_PATH = Path("data/prices.csv")
PRICE_LIST_LABELS = {"salon": "Salon", "delivery": "Delivery"}


st.set_page_config(page_title="ChalinTrends", page_icon="🥩", layout="centered")

st.title("ChalinTrends")
st.caption("Precios diarios de Chalin Carnes Premium")

prices = load_prices(DATA_PATH)
if prices.empty:
    st.info("Todavia no hay datos. Ejecuta `python scripts/update_prices.py` para cargar el primer snapshot.")
    st.stop()

price_list = st.segmented_control(
    "Lista",
    options=["salon", "delivery"],
    format_func=lambda value: PRICE_LIST_LABELS[value],
    default="salon",
)

query = st.text_input("Buscar corte o producto", placeholder="Asado, vacio, lomo...")
offers = latest_offers(prices, price_list=price_list)

if query:
    mask = offers["product_name"].str.contains(query, case=False, na=False)
    offers = offers[mask]

latest_date = pd.to_datetime(prices["date"]).max().date()
st.metric("Ultima actualizacion", latest_date.isoformat())

opportunities = offers[offers["opportunity"]] if not offers.empty else offers
st.subheader("Ofertas primero")
if opportunities.empty:
    st.write("No hay oportunidades detectadas para esta vista.")
else:
    display_cols = ["product_name", "category", "price", "previous_price", "change_pct", "recent_median"]
    st.dataframe(opportunities[display_cols].head(20), hide_index=True, use_container_width=True)

st.subheader("Bajaron desde el registro anterior")
drops = offers[offers["dropped_today"]] if not offers.empty else offers
if drops.empty:
    st.write("No hay bajas registradas.")
else:
    st.dataframe(drops[["product_name", "category", "price", "previous_price", "change_pct"]].head(20), hide_index=True, use_container_width=True)

st.subheader("Tendencia por categoria")
category_prices = category_daily_prices(prices, price_list=price_list)
if category_prices.empty:
    st.write("No hay datos de categorias.")
else:
    chart_df = category_prices.pivot(index="date", columns="category", values="median_price")
    st.line_chart(chart_df)

st.subheader("Comparar cortes")
product_options = sorted(prices["product_name"].dropna().unique())
selected_products = st.multiselect("Productos", product_options, default=product_options[:3])
if selected_products:
    product_history = prices[
        (prices["price_list"] == price_list) & (prices["product_name"].isin(selected_products))
    ].copy()
    product_history["date"] = pd.to_datetime(product_history["date"])
    chart_df = product_history.pivot_table(index="date", columns="product_name", values="price", aggfunc="last")
    st.line_chart(chart_df)

st.subheader("Salon vs Delivery")
latest_prices = prices[prices["date"] == prices["date"].max()]
comparison = latest_prices.pivot_table(index="product_name", columns="price_list", values="price", aggfunc="last")
comparison = comparison.dropna(how="all")
if {"salon", "delivery"}.issubset(comparison.columns):
    comparison["delivery_minus_salon"] = comparison["delivery"] - comparison["salon"]
st.dataframe(comparison.reset_index(), hide_index=True, use_container_width=True)
```

- [ ] **Step 2: Run Streamlit locally**

Run:

```powershell
streamlit run streamlit_app.py
```

Expected: app opens and displays current prices.

- [ ] **Step 3: Commit**

Run:

```powershell
git add streamlit_app.py
git commit -m "feat: add Streamlit dashboard"
```

## Task 7: GitHub Actions Daily Refresh

**Files:**
- Create: `.github/workflows/daily-prices.yml`

- [ ] **Step 1: Create workflow**

Create `.github/workflows/daily-prices.yml`:

```yaml
name: Daily prices

on:
  schedule:
    - cron: "15 10 * * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  update-prices:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: python -m pip install -e .
      - name: Update prices
        run: python scripts/update_prices.py
      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/prices.csv
          git diff --cached --quiet || git commit -m "data: update daily Chalin prices"
          git push
```

- [ ] **Step 2: Commit**

Run:

```powershell
git add .github/workflows/daily-prices.yml
git commit -m "ci: update prices daily"
```

## Task 8: Final Verification

**Files:**
- No new files.

- [ ] **Step 1: Run all tests**

Run:

```powershell
pytest -v
```

Expected: all tests pass.

- [ ] **Step 2: Run scraper idempotency check**

Run:

```powershell
python scripts/update_prices.py
python scripts/update_prices.py
```

Expected: first run stores rows if today is missing; second run says today's prices already exist.

- [ ] **Step 3: Run Streamlit smoke test**

Run:

```powershell
streamlit run streamlit_app.py
```

Expected: dashboard loads with Salon/Delivery selector, search, offers, category chart, product comparison, and Salon vs Delivery table.

## Self-Review

Spec coverage:

- Direct API scraper: Task 2 and Task 5.
- CSV storage: Task 3.
- Tests: Tasks 2, 3, 4, and 8.
- Streamlit mobile-friendly dashboard: Task 6.
- GitHub Actions daily refresh: Task 7.
- Salon and Delivery tracking: Tasks 2, 3, 5, and 6.
- Backlog features: captured in the design spec.

Placeholder scan:

- No TBD/TODO placeholders remain.

Type consistency:

- `price_list`, `product_id`, `product_name`, `price`, and `date` are consistent across fetch, storage, analytics, and UI.
