import pandas as pd

from chalintrends.search import MAX_SEARCH_QUERY_LENGTH, filter_products, product_matches


def test_product_matches_ignores_case_and_accents():
    assert product_matches("Vacío Especial", "vacio")
    assert product_matches("MATAMBRÉ DE CERDO", "matambre")


def test_filter_products_ignores_case_and_accents():
    products = pd.DataFrame(
        [
            {"product_name": "Vacío Especial"},
            {"product_name": "Asado"},
            {"product_name": "MATAMBRÉ DE CERDO"},
        ]
    )

    filtered = filter_products(products, "matambre")

    assert filtered["product_name"].tolist() == ["MATAMBRÉ DE CERDO"]


def test_search_caps_query_length_before_filtering():
    capped_name = "a" * MAX_SEARCH_QUERY_LENGTH
    oversized_query = capped_name + ("b" * 10_000)
    products = pd.DataFrame([{"product_name": capped_name}])

    assert product_matches(capped_name, oversized_query)
    assert filter_products(products, oversized_query)["product_name"].tolist() == [capped_name]
