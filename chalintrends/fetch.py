from __future__ import annotations

from typing import Any
import warnings

import requests

from chalintrends.categories import categorize_product

API_URL = "https://api.chalincarnespremium.com.ar/precios/lista"
USER_AGENT = "ChalinTrends/0.1 personal price tracker"

PRICE_LIST_NAMES = {
    "Salón": "salon",
    "Salon": "salon",
    "Reparto": "delivery",
}


class PricePayloadError(RuntimeError):
    """Raised when the Chalin API response cannot be safely stored."""


class PricePayloadWarning(UserWarning):
    """Warns about skipped records in an otherwise usable Chalin API response."""


def fetch_price_payload(timeout: int = 20) -> dict[str, Any]:
    response = requests.get(
        API_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/plain"},
        timeout=timeout,
    )
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as exc:
        raise PricePayloadError("Chalin API did not return valid JSON.") from exc

    if not isinstance(payload, dict):
        raise PricePayloadError("Chalin API JSON root must be an object.")
    return payload


def _require_mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PricePayloadError(f"Chalin API field {path} must be an object.")
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise PricePayloadError(f"Chalin API field {path} must be a list.")
    return value


def _require_product_field(product: dict[str, Any], field: str, path: str) -> Any:
    value = product.get(field)
    if value in (None, ""):
        raise PricePayloadError(f"Chalin API product at {path} is missing {field}.")
    return value


def parse_price_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = _require_mapping(payload.get("data"), "data")
    source_url = str(data.get("url") or API_URL)
    price_lists = _require_list(data.get("listas"), "data.listas")
    rows: list[dict[str, Any]] = []
    supported_lists = 0

    for list_index, raw_price_list in enumerate(price_lists):
        price_list = _require_mapping(raw_price_list, f"data.listas[{list_index}]")
        list_name = PRICE_LIST_NAMES.get(price_list.get("descripcion"))
        if list_name is None:
            continue
        supported_lists += 1

        try:
            groups = _require_list(price_list.get("grupos"), f"data.listas[{list_index}].grupos")
        except PricePayloadError as exc:
            warnings.warn(str(exc), PricePayloadWarning, stacklevel=2)
            continue

        for group_index, raw_group in enumerate(groups):
            try:
                group = _require_mapping(raw_group, f"data.listas[{list_index}].grupos[{group_index}]")
            except PricePayloadError as exc:
                warnings.warn(str(exc), PricePayloadWarning, stacklevel=2)
                continue

            source_category = str(group.get("descripcion") or "")
            try:
                products = _require_list(
                    group.get("productos"),
                    f"data.listas[{list_index}].grupos[{group_index}].productos",
                )
            except PricePayloadError as exc:
                warnings.warn(str(exc), PricePayloadWarning, stacklevel=2)
                continue

            for product_index, raw_product in enumerate(products):
                product_path = f"data.listas[{list_index}].grupos[{group_index}].productos[{product_index}]"
                try:
                    product = _require_mapping(raw_product, product_path)
                    product_name = str(_require_product_field(product, "descripcion", product_path))
                    product_id = str(_require_product_field(product, "id_producto", product_path))
                    price_text = str(_require_product_field(product, "precio", product_path))
                    numeric_price = _require_product_field(product, "precio_numerico", product_path)
                    price = int(numeric_price)
                except (TypeError, ValueError) as exc:
                    warnings.warn(
                        f"Chalin API product at {product_path} has invalid precio_numerico.",
                        PricePayloadWarning,
                        stacklevel=2,
                    )
                    continue
                except PricePayloadError as exc:
                    warnings.warn(str(exc), PricePayloadWarning, stacklevel=2)
                    continue

                rows.append(
                    {
                        "price_list": list_name,
                        "source_category": source_category,
                        "category": categorize_product(product_name, source_category),
                        "product_id": product_id,
                        "product_name": product_name,
                        "price_text": price_text,
                        "price": price,
                        "source_url": source_url,
                    }
                )

    if supported_lists == 0:
        raise PricePayloadError("Chalin API response contains no Salon or Delivery price lists.")
    if not rows:
        raise PricePayloadError("Chalin API response contains no product price rows.")

    return rows
