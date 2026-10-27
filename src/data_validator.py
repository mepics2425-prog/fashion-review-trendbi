"""Normalize fields and reject conflicting records instead of guessing."""
import re
from .models import CATEGORIES, Observation, Product, timestamp


def clean(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected a text field; a CSV cell must be present")
    return " ".join(value.split())


def normalize_products(rows: list[dict]) -> list[Product]:
    products: dict[str, Product] = {}
    for row in rows:
        product = Product(*(clean(row[k]) for k in ("product_id", "brand", "name", "category")))
        if not re.fullmatch(r"DEMO-\d{3}", product.product_id):
            raise ValueError("Only fictional DEMO product identifiers are allowed")
        if not product.brand or not product.name or product.category not in CATEGORIES:
            raise ValueError(f"Invalid product: {product.product_id}")
        if product.product_id in products and products[product.product_id] != product:
            raise ValueError(f"Conflicting product: {product.product_id}")
        products[product.product_id] = product
    return sorted(products.values(), key=lambda p: p.product_id)


def normalize_observations(rows: list[dict], products: list[Product]) -> list[Observation]:
    known = {p.product_id for p in products}
    unique: dict[tuple, Observation] = {}
    for row in rows:
        product_id = clean(row["product_id"])
        raw = clean(row["review_count"])
        if product_id not in known:
            raise ValueError(f"Unknown product: {product_id}")
        if raw and not re.fullmatch(r"\d+", raw):
            raise ValueError("review_count must be a nonnegative integer or blank")
        observation = Observation(product_id, timestamp(row["observed_at"]), int(raw) if raw else None)
        key = (product_id, observation.observed_at)
        if key in unique and unique[key] != observation:
            raise ValueError(f"Conflicting snapshot: {key}")
        unique[key] = observation
    return sorted(unique.values(), key=lambda o: (o.product_id, o.observed_at))
