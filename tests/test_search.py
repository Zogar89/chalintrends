import pandas as pd

from chalintrends.search import filter_products, product_matches


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
