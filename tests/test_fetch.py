import pytest

from chalintrends.fetch import (
    MAX_PRICE_ROWS,
    MAX_PRODUCTS_PER_GROUP,
    MAX_RESPONSE_BYTES,
    PricePayloadError,
    PricePayloadWarning,
    fetch_price_payload,
    parse_price_payload,
)


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
            "source_category": "Carnes",
            "category": "Vacuno medio",
            "product_id": "asado-id",
            "product_name": "Asado",
            "price_text": "15.999",
            "price": 15999,
            "source_url": "https://precios.chalincarnespremium.com.ar",
        },
        {
            "price_list": "delivery",
            "source_category": "Carnes",
            "category": "Vacuno medio",
            "product_id": "asado-id",
            "product_name": "Asado",
            "price_text": "17.499",
            "price": 17499,
            "source_url": "https://precios.chalincarnespremium.com.ar",
        },
    ]


def test_fetch_price_payload_rejects_invalid_json(monkeypatch):
    class FakeResponse:
        headers = {}
        content = b"not json"

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size):
            yield self.content

    monkeypatch.setattr("chalintrends.fetch.requests.get", lambda *args, **kwargs: FakeResponse())

    with pytest.raises(PricePayloadError, match="valid JSON"):
        fetch_price_payload()


def test_fetch_price_payload_rejects_oversized_response(monkeypatch):
    class FakeResponse:
        headers = {"Content-Length": str(MAX_RESPONSE_BYTES + 1)}
        content = b"{}"

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size):
            raise AssertionError("oversized responses should be rejected before reading the body")

    monkeypatch.setattr("chalintrends.fetch.requests.get", lambda *args, **kwargs: FakeResponse())

    with pytest.raises(PricePayloadError, match="too large"):
        fetch_price_payload()


def test_parse_price_payload_rejects_missing_data_object():
    with pytest.raises(PricePayloadError, match="data"):
        parse_price_payload({"status": "success"})


def test_parse_price_payload_rejects_unrecognized_lists():
    payload = {
        "data": {
            "listas": [
                {
                    "descripcion": "Mayorista",
                    "grupos": [],
                }
            ]
        }
    }

    with pytest.raises(PricePayloadError, match="Salon or Delivery"):
        parse_price_payload(payload)


def test_parse_price_payload_rejects_too_many_price_rows():
    remaining = MAX_PRICE_ROWS + 1
    groups = []
    product_id = 0
    while remaining:
        product_count = min(MAX_PRODUCTS_PER_GROUP, remaining)
        products = []
        for _ in range(product_count):
            product_id += 1
            products.append(
                {
                    "id_producto": f"product-{product_id}",
                    "descripcion": f"Producto {product_id}",
                    "precio": "1.000",
                    "precio_numerico": 1000,
                }
            )
        groups.append({"descripcion": "Carnes", "productos": products})
        remaining -= product_count

    payload = {"data": {"listas": [{"descripcion": "Salón", "grupos": groups}]}}

    with pytest.raises(PricePayloadError, match="too many product price rows"):
        parse_price_payload(payload)


def test_parse_price_payload_skips_product_with_missing_fields():
    payload = {
        "data": {
            "listas": [
                {
                    "descripcion": "Salón",
                    "grupos": [
                        {
                            "descripcion": "Carnes",
                            "productos": [
                                {
                                    "descripcion": "Asado",
                                    "precio": "15.999",
                                    "precio_numerico": 15999,
                                },
                                {
                                    "id_producto": "vacio-id",
                                    "descripcion": "Vacío",
                                    "precio": "19.999",
                                    "precio_numerico": 19999,
                                },
                            ],
                        }
                    ],
                }
            ]
        }
    }

    with pytest.warns(PricePayloadWarning, match="id_producto"):
        rows = parse_price_payload(payload)

    assert [row["product_name"] for row in rows] == ["Vacío"]


def test_parse_price_payload_skips_product_with_invalid_numeric_price():
    payload = {
        "data": {
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
                                    "precio": "consultar",
                                    "precio_numerico": "nope",
                                },
                                {
                                    "id_producto": "vacio-id",
                                    "descripcion": "Vacío",
                                    "precio": "19.999",
                                    "precio_numerico": 19999,
                                },
                            ],
                        }
                    ],
                }
            ]
        }
    }

    with pytest.warns(PricePayloadWarning, match="precio_numerico"):
        rows = parse_price_payload(payload)

    assert [row["product_name"] for row in rows] == ["Vacío"]
