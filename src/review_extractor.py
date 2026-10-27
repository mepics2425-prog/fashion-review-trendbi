"""Offline JSON-LD contract demo; no browser/network or company code.

This deliberately supports a narrow Product shape. A production adapter must
validate redirects and canonical identity before calling it.
"""
import re
from urllib.parse import urlsplit


def product_id(url: str) -> str:
    if not isinstance(url, str):
        raise ValueError("Product URL must be a string")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ("www.musinsa.com", "musinsa.com") or parsed.port not in (None, 443) or parsed.username or parsed.password:
        raise ValueError("Untrusted product URL")
    match = re.fullmatch(r"/(?:app/)?goods/(\d+)/?", parsed.path)
    if not match:
        raise ValueError("Invalid product path")
    return match.group(1)


def extract_review_count(request_url: str, response_url: str, documents: list[dict]) -> int | None:
    """Return a unique verified count or None; zero is valid.

    Identity proof requires a matching Product URL; sku alone is insufficient.
    Any conflicting Product candidate fails closed. Missing counts stay missing.
    """
    requested = product_id(request_url)
    if product_id(response_url) != requested:
        raise ValueError("Response product mismatch")
    candidates: set[int] = set()

    def walk(node):
        if isinstance(node, list):
            for item in node:
                yield from walk(item)
        elif isinstance(node, dict):
            yield node
            for key, value in node.items():
                if key == "@graph":
                    yield from walk(value)

    for node in walk(documents):
        types = node.get("@type", [])
        if not isinstance(types, (str, list)):
            continue
        if "Product" not in ([types] if isinstance(types, str) else types):
            continue
        try:
            if product_id(node.get("url", "")) != requested:
                return None
        except ValueError:
            return None
        rating = node.get("aggregateRating", {})
        if not isinstance(rating, dict):
            return None
        count = rating.get("reviewCount")
        if count is None:
            continue
        if isinstance(count, bool) or not re.fullmatch(r"\d+", str(count)):
            return None
        candidates.add(int(count))
    return next(iter(candidates)) if len(candidates) == 1 else None
