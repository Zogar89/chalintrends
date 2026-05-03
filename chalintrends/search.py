from __future__ import annotations

import unicodedata

import pandas as pd

MAX_SEARCH_QUERY_LENGTH = 128


def normalize_search_text(value: object, *, max_length: int | None = None) -> str:
    text = str(value)
    if max_length is not None:
        text = text[:max_length]
    normalized = unicodedata.normalize("NFKD", text)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return without_accents.casefold()


def product_matches(product_name: object, query: str) -> bool:
    normalized_query = normalize_search_text(query, max_length=MAX_SEARCH_QUERY_LENGTH).strip()
    if not normalized_query:
        return True
    return normalized_query in normalize_search_text(product_name)


def filter_products(df: pd.DataFrame, query: str, *, column: str = "product_name") -> pd.DataFrame:
    normalized_query = normalize_search_text(query, max_length=MAX_SEARCH_QUERY_LENGTH).strip()
    if df.empty or not normalized_query:
        return df

    return df[df[column].map(lambda product_name: normalized_query in normalize_search_text(product_name))]
