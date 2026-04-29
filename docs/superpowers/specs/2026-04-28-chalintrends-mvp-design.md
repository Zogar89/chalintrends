# ChalinTrends MVP Design

## Summary

ChalinTrends is a personal Streamlit app for tracking daily prices from Chalin Carnes Premium. It stores both Salon and Delivery prices every day, highlights useful buying opportunities, and keeps a backlog of richer analysis features for later.

## Source Data

The public website loads prices from:

`https://api.chalincarnespremium.com.ar/precios/lista`

The endpoint returns JSON with two price lists:

- `Salon`
- `Reparto`, treated in the app as Delivery

The MVP uses direct server-side HTTP requests from Python. It does not need browser automation for daily extraction.

## Storage

The database is a single CSV file:

`data/prices.csv`

Each daily run appends one row per product per price list.

Columns:

- `date`
- `price_list`
- `category`
- `product_id`
- `product_name`
- `price_text`
- `price`
- `source_url`
- `captured_at`

The CSV is intentionally simple so it can be versioned in GitHub and read directly by pandas.

## Daily Refresh

GitHub Actions runs once per day. The workflow:

1. Installs Python dependencies.
2. Runs the scraper.
3. Appends today's Salon and Delivery prices if they are not already present.
4. Commits `data/prices.csv` only when it changed.

The scraper is polite: one API request, a descriptive User-Agent, timeout, and clear failure messages.

## Streamlit App

The MVP app is mobile-friendly and optimized for personal use.

Home layout:

1. Header with app name.
2. Price list selector: Salon or Delivery.
3. Search bar for cuts/products.
4. Offer summary.
5. Ranking of best opportunities.
6. Ranking of products that dropped since the previous recorded day.
7. Category trend chart.
8. Multi-product comparison chart.

Product detail:

- Current price by selected list.
- Historical line chart.
- Salon vs Delivery comparison when both exist.
- Recent changes.

## Offer Logic

The app calculates two signals:

- `dropped_today`: current price is lower than the previous recorded price for the same product/list.
- `below_recent_median`: current price is below the recent median for the same product/list.

The default recent window is 30 days. If fewer than 30 days exist, the app uses available data and treats confidence as lower.

For the first day of data, the app shows current prices without pretending there are trends.

## MVP Scope

Included:

- Direct API scraper.
- CSV append storage.
- Tests for parsing, storage idempotency, and trend calculations.
- Streamlit dashboard.
- GitHub Actions daily refresh.
- Salon and Delivery tracking.

Not included:

- Telegram or WhatsApp alerts.
- User login.
- External database.
- Browser-based scraping.
- Machine learning predictions.

## Backlog Features

Evaluate after the MVP has some historical data:

- Ranking of daily price drops.
- Ranking of daily price increases.
- Price by category over time.
- Trend by category.
- Compare several cuts in one chart.
- Difference between Salon and Delivery by product.
- Product opportunity score from 0 to 100.
- Product traffic-light status: cheap, normal, expensive.
- Product volatility ranking.
- Historical minimum and maximum distance.
- New/disappeared product detection.
- Suspicious price jump detection.
- Custom favorites.
- Custom basket tracking.
- Parrilla basket: Asado, Vacio, Chorizo, Morcilla, Achuras.
- Milanga basket.
- Cost per gathering.
- Target price thresholds.
- Mobile quick-buy mode.
- Telegram alerts.
- WhatsApp alerts.
- Weekly report export.
- Simple trend projection.
- CSV backup.
- Scraper health panel.

## Open Decisions

None for MVP. The initial implementation should choose simple defaults and keep configuration in code or app controls.
