from __future__ import annotations

import unicodedata

UNCATEGORIZED_CATEGORY = "Sin categorizar"

CATEGORY_ORDER = [
    "Vacuno premium",
    "Vacuno medio",
    "Vacuno economico",
    "Pollo",
    "Cerdo",
    "Achuras",
    "Chacinados",
    "Elaborados",
    "Otros",
    UNCATEGORIZED_CATEGORY,
]
CATEGORY_RANK = {category: index for index, category in enumerate(CATEGORY_ORDER)}
TOP_SELLING_PRODUCTS = [
    "Asado",
    "Vacio",
    "Milanesa de Carne",
    "Picada Especial",
    "Pollo x Kg.",
    "Nalga",
    "Supremas",
    "Matambre",
    "Chorizo",
    "Bondiola",
]


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_value.casefold().split())


TOP_SELLING_PRODUCT_KEYS = {_normalize(product) for product in TOP_SELLING_PRODUCTS}


PRODUCT_CATEGORIES = {
    "lomo": "Vacuno premium",
    "lomo sin cordon": "Vacuno premium",
    "bife de chorizo": "Vacuno premium",
    "ojo de bife": "Vacuno premium",
    "entrana": "Vacuno premium",
    "picana": "Vacuno premium",
    "colita cuadril": "Vacuno premium",
    "bife ancho": "Vacuno premium",
    "bife angosto": "Vacuno premium",
    "bife compl. c/ hueso y lomo": "Vacuno premium",
    "asado": "Vacuno medio",
    "vacio": "Vacuno medio",
    "cuadril": "Vacuno medio",
    "nalga": "Vacuno medio",
    "peceto": "Vacuno medio",
    "bola de lomo": "Vacuno medio",
    "matambre": "Vacuno medio",
    "matambre de carne": "Vacuno medio",
    "tapa de asado": "Vacuno medio",
    "tapa de nalga": "Vacuno medio",
    "cuadrada": "Vacuno medio",
    "palomita": "Vacuno medio",
    "r. beef": "Vacuno medio",
    "bife en tira": "Vacuno medio",
    "carnaza comun": "Vacuno economico",
    "paleta": "Vacuno economico",
    "falda en tira": "Vacuno economico",
    "espinazo": "Vacuno economico",
    "osobuco": "Vacuno economico",
    "tortuguita": "Vacuno economico",
    "chiquizuela": "Vacuno economico",
    "pollo x kg.": "Pollo",
    "supremas": "Pollo",
    "pata y muslo": "Pollo",
    "trasero de pollo": "Pollo",
    "matambre de pollo": "Pollo",
    "milanesa de pollo": "Pollo",
    "hamburguesas de pollo": "Pollo",
    "bondiola": "Cerdo",
    "costillitas": "Cerdo",
    "pechito": "Cerdo",
    "pernil de cerdo": "Cerdo",
    "matambre de cerdo": "Cerdo",
    "lechon": "Cerdo",
    "centro": "Achuras",
    "chinchulin": "Achuras",
    "corazon": "Achuras",
    "higado": "Achuras",
    "lengua": "Achuras",
    "molleja": "Achuras",
    "mondongo": "Achuras",
    "rabo": "Achuras",
    "rinon": "Achuras",
    "rueda": "Achuras",
    "seso c/u": "Achuras",
    "tripa gorda": "Achuras",
    "chorizo": "Chacinados",
    "chorizo bb de cerdo": "Chacinados",
    "chorizo bombon": "Chacinados",
    "chorizo colorado": "Chacinados",
    "chorizo de cerdo": "Chacinados",
    "morc. bombon": "Chacinados",
    "morcilla": "Chacinados",
    "morcilla rosca": "Chacinados",
    "salamin": "Chacinados",
    "salch. viena copetin": "Chacinados",
    "salchicha de viena": "Chacinados",
    "salchicha parrillera": "Chacinados",
    "hamburguesas": "Elaborados",
    "milanesa de carne": "Elaborados",
    "picada especial": "Elaborados",
    "patitas / medallones": "Elaborados",
    "cordero": "Otros",
    "huevos x maple": "Otros",
}


def categorize_product(product_name: str, source_category: str) -> str:
    return PRODUCT_CATEGORIES.get(_normalize(product_name), UNCATEGORIZED_CATEGORY)


def category_sort_key(category: str) -> tuple[int, str]:
    return (CATEGORY_RANK.get(category, len(CATEGORY_ORDER)), category)


def sort_category_names(categories) -> list[str]:
    return sorted(categories, key=category_sort_key)


def is_top_seller(product_name: str) -> bool:
    return _normalize(product_name) in TOP_SELLING_PRODUCT_KEYS
