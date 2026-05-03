from __future__ import annotations

import json
from typing import Any
import warnings

import requests

from chalintrends.categories import categorize_product

API_URL = "https://api.chalincarnespremium.com.ar/precios/lista"
USER_AGENT = "ChalinTrends/0.1 personal price tracker"
MAX_RESPONSE_BYTES = 1_000_000
MAX_PRICE_LISTS = 20
MAX_GROUPS_PER_LIST = 100
MAX_PRODUCTS_PER_GROUP = 500
MAX_PRICE_ROWS = 2_000
MAX_TEXT_LENGTH = 500

PRICE_LIST_NAMES = {
    "Salón": "salon",
    "Salon": "salon",
    "Reparto": "delivery",
}


class PricePayloadError(RuntimeError):
    """Raised when the Chalin API response cannot be safely stored."""


class PricePayloadWarning(UserWarning):
    """Warns about skipped records in an otherwise usable Chalin API response."""


def _read_bounded_response(response: requests.Response) -> bytes:
    content_length = response.headers.get("Content-Length")
    if content_length is not None:
        try:
            response_size = int(content_length)
        except ValueError as exc:
            raise PricePayloadError("Chalin API returned an invalid Content-Length header.") from exc
        if response_size > MAX_RESPONSE_BYTES:
            raise PricePayloadError("Chalin API response is too large.")

    chunks = []
    response_size = 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        response_size += len(chunk)
        if response_size > MAX_RESPONSE_BYTES:
            raise PricePayloadError("Chalin API response is too large.")
        chunks.append(chunk)
    return b"".join(chunks)


def fetch_price_payload(timeout: int = 20) -> dict[str, Any]:
    response = requests.get(
        API_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,text/plain"},
        timeout=timeout,
        stream=True,
    )
    response.raise_for_status()
    response_content = _read_bounded_response(response)
    try:
        payload = json.loads(response_content)
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


def _require_bounded_list(value: Any, path: str, limit: int) -> list[Any]:
    items = _require_list(value, path)
    if len(items) > limit:
        raise PricePayloadError(f"Chalin API field {path} has too many items.")
    return items


def _bounded_text(value: Any, path: str) -> str:
    text = str(value)
    if len(text) > MAX_TEXT_LENGTH:
        raise PricePayloadError(f"Chalin API field {path} is too long.")
    return text


def _require_product_field(product: dict[str, Any], field: str, path: str) -> Any:
    value = product.get(field)
    if value in (None, ""):
        raise PricePayloadError(f"Chalin API product at {path} is missing {field}.")
    return value


def parse_price_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = _require_mapping(payload.get("data"), "data")
    source_url = _bounded_text(data.get("url") or API_URL, "data.url")
    price_lists = _require_bounded_list(data.get("listas"), "data.listas", MAX_PRICE_LISTS)
    rows: list[dict[str, Any]] = []
    supported_lists = 0

    for list_index, raw_price_list in enumerate(price_lists):
        price_list = _require_mapping(raw_price_list, f"data.listas[{list_index}]")
        list_name = PRICE_LIST_NAMES.get(price_list.get("descripcion"))
        if list_name is None:
            continue
        supported_lists += 1

        try:
            groups = _require_bounded_list(
                price_list.get("grupos"),
                f"data.listas[{list_index}].grupos",
                MAX_GROUPS_PER_LIST,
            )
        except PricePayloadError as exc:
            warnings.warn(str(exc), PricePayloadWarning, stacklevel=2)
            continue

        for group_index, raw_group in enumerate(groups):
            try:
                group = _require_mapping(raw_group, f"data.listas[{list_index}].grupos[{group_index}]")
            except PricePayloadError as exc:
                warnings.warn(str(exc), PricePayloadWarning, stacklevel=2)
                continue

            source_category = _bounded_text(
                group.get("descripcion") or "",
                f"data.listas[{list_index}].grupos[{group_index}].descripcion",
            )
            try:
                products = _require_bounded_list(
                    group.get("productos"),
                    f"data.listas[{list_index}].grupos[{group_index}].productos",
                    MAX_PRODUCTS_PER_GROUP,
                )
            except PricePayloadError as exc:
                warnings.warn(str(exc), PricePayloadWarning, stacklevel=2)
                continue

            for product_index, raw_product in enumerate(products):
                product_path = f"data.listas[{list_index}].grupos[{group_index}].productos[{product_index}]"
                try:
                    product = _require_mapping(raw_product, product_path)
                    product_name = _bounded_text(
                        _require_product_field(product, "descripcion", product_path),
                        f"{product_path}.descripcion",
                    )
                    product_id = _bounded_text(
                        _require_product_field(product, "id_producto", product_path),
                        f"{product_path}.id_producto",
                    )
                    price_text = _bounded_text(
                        _require_product_field(product, "precio", product_path),
                        f"{product_path}.precio",
                    )
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

                if len(rows) >= MAX_PRICE_ROWS:
                    raise PricePayloadError("Chalin API response contains too many product price rows.")

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
