from __future__ import annotations

import unicodedata

import pandas as pd


def normalize_search_text(value: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return without_accents.casefold()


def product_matches(product_name: object, query: str) -> bool:
    normalized_query = normalize_search_text(query).strip()
    if not normalized_query:
        return True
    return normalized_query in normalize_search_text(product_name)


def filter_products(df: pd.DataFrame, query: str, *, column: str = "product_name") -> pd.DataFrame:
    normalized_query = normalize_search_text(query).strip()
    if df.empty or not normalized_query:
        return df

    return df[df[column].map(lambda product_name: normalized_query in normalize_search_text(product_name))]
