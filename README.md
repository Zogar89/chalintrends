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

## Migrate price storage

`data/prices.csv` is stored as one human-readable row per day. Product data is spread
across columns named like `salon | Asado | price` and `delivery | Asado | price_text`.
To migrate an older row-per-product CSV, or the intermediate `items_json` snapshot format:

```powershell
python scripts/migrate_prices_csv.py
```

## Run app

```powershell
streamlit run streamlit_app.py
```

## Streamlit Community Cloud

- App file: `streamlit_app.py`
- Python dependencies: `requirements.txt`
- Python version: `3.11`
- Data file included in the repo: `data/prices.csv`

After publishing the repository to GitHub, create a new Streamlit Community Cloud app and point it to `streamlit_app.py`.

For the production checklist, GitHub Actions setup, and security notes, see [docs/DEPLOYMENT_SECURITY.md](docs/DEPLOYMENT_SECURITY.md).
