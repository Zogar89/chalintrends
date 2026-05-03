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
    window_start = latest_date - pd.Timedelta(days=window_days - 1)
    comparison_cutoff = latest_date - pd.Timedelta(days=window_days)
    recent = data[data["date"] >= window_start]

    latest = data[data["date"] == latest_date].copy()
    comparison = (
        data[data["date"] <= comparison_cutoff]
        .sort_values("date")
        .groupby("product_id")
        .tail(1)[["product_id", "date", "price"]]
        .rename(columns={"date": "comparison_date", "price": "comparison_price"})
    )
    medians = (
        recent.groupby("product_id")["price"]
        .median()
        .reset_index()
        .rename(columns={"price": "recent_median"})
    )

    result = latest.merge(comparison, on="product_id", how="left").merge(medians, on="product_id", how="left")
    result["previous_price"] = result["comparison_price"]
    result["change"] = result["price"] - result["comparison_price"]
    result["change_pct"] = (result["change"] / result["comparison_price"]) * 100
    result["dropped_since_comparison"] = result["change"] < 0
    result["dropped_today"] = result["dropped_since_comparison"]
    result["below_recent_median"] = result["price"] < result["recent_median"]
    result["opportunity"] = result["dropped_since_comparison"] | result["below_recent_median"]
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


def salon_delivery_comparison(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    data = _prepare(df)
    latest_date = data["date"].max()
    latest = data[data["date"] == latest_date]
    comparison = latest.pivot_table(
        index="product_name",
        columns="price_list",
        values="price",
        aggfunc="last",
    )
    comparison = comparison.dropna(how="all")
    for column in ["salon", "delivery"]:
        if column not in comparison.columns:
            comparison[column] = pd.NA

    comparison["delivery_minus_salon"] = comparison["delivery"] - comparison["salon"]
    comparison["delivery_pct_over_salon"] = (
        comparison["delivery_minus_salon"] / comparison["salon"].where(comparison["salon"] != 0) * 100
    )
    comparison = comparison.sort_values("delivery_minus_salon", ascending=False, na_position="last")
    return comparison.reset_index()


def average_delivery_pct_over_salon(comparison: pd.DataFrame) -> float | None:
    if comparison.empty or "delivery_pct_over_salon" not in comparison.columns:
        return None

    values = pd.to_numeric(comparison["delivery_pct_over_salon"], errors="coerce").dropna()
    if values.empty:
        return None
    return float(values.mean())
