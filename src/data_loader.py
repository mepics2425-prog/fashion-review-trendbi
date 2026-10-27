"""Explicit UTF-8 CSV loading; never read environment files or remote data."""
import csv
from pathlib import Path
from .data_validator import normalize_observations, normalize_products
from .models import Observation, Product


def read_csv(path: Path, required_fields: tuple[str, ...] = ()) -> list[dict[str, str]]:
    """Reject truncated/ambiguous rows; an explicit empty cell remains valid."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        try:
            headers = reader.fieldnames
        except csv.Error as error:
            raise ValueError(f"{path.name}: malformed CSV header") from error
        if not headers or len(set(headers)) != len(headers):
            raise ValueError(f"{path.name}: missing or duplicate CSV headers")
        missing = set(required_fields) - set(headers)
        if missing:
            raise ValueError(f"{path.name}: missing columns: {', '.join(sorted(missing))}")
        rows = []
        try:
            for row in reader:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(f"{path.name}: row {reader.line_num} has an incorrect field count")
                rows.append(row)
        except csv.Error as error:
            raise ValueError(f"{path.name}: malformed CSV at line {reader.line_num}") from error
        return rows


def load(directory: Path) -> tuple[list[Product], list[Observation]]:
    products = normalize_products(read_csv(directory / "synthetic_products.csv",
                                          ("product_id", "brand", "name", "category")))
    observations = read_csv(directory / "synthetic_observations.csv",
                            ("product_id", "observed_at", "review_count"))
    return products, normalize_observations(observations, products)
