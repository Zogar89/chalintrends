from chalintrends.categories import TOP_SELLING_PRODUCTS, categorize_product, is_top_seller, sort_category_names


def test_categorize_product_maps_known_products_to_curated_categories():
    assert categorize_product("Lomo", "Carnes") == "Vacuno premium"
    assert categorize_product("Asado", "Carnes") == "Vacuno medio"
    assert categorize_product("Carnaza Comun", "Carnes") == "Vacuno economico"
    assert categorize_product("Hamburguesas de Pollo", "Carnes") == "Pollo"
    assert categorize_product("Lechon", "Varios") == "Cerdo"
    assert categorize_product("Morcilla Rosca", "Embutidos") == "Chacinados"
    assert categorize_product("Patitas / Medallones", "Varios") == "Elaborados"


def test_categorize_product_marks_unknown_products_as_uncategorized():
    assert categorize_product("Producto Misterioso", "Carnes") == "Sin categorizar"


def test_sort_category_names_uses_business_importance_before_alphabetical_order():
    categories = [
        "Otros",
        "Achuras",
        "Vacuno medio",
        "Pollo",
        "Vacuno premium",
        "Chacinados",
        "Categoria nueva",
        "Vacuno economico",
        "Sin categorizar",
    ]

    assert sort_category_names(categories) == [
        "Vacuno premium",
        "Vacuno medio",
        "Vacuno economico",
        "Pollo",
        "Achuras",
        "Chacinados",
        "Otros",
        "Sin categorizar",
        "Categoria nueva",
    ]


def test_is_top_seller_identifies_curated_best_sellers():
    assert len(TOP_SELLING_PRODUCTS) == 10
    assert is_top_seller("Asado")
    assert is_top_seller("vacio")
    assert is_top_seller("POLLO X KG.")
    assert is_top_seller("Supremas")
    assert is_top_seller("bondiola")
    assert not is_top_seller("Lomo")
