"""Deterministic fixtures: invented products, counts, failure modes and runs."""
import csv
from datetime import datetime, timedelta
from pathlib import Path
from .models import CATEGORIES, KST

AS_OF = datetime(2026, 10, 26, 18, tzinfo=KST)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def generate(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    products, observations = [], []
    names = ("코튼 레이어 티", "스트레이트 데님", "라이트 필드 재킷", "플리츠 드레스")
    brands = ("DEMO ATELIER", "DEMO FORM", "DEMO ORBIT", "DEMO STILL")
    for i in range(24):
        product_id = f"DEMO-{i + 1:03}"
        products.append(dict(product_id=product_id, brand=brands[i % 4],
                             name=f"{names[i % 4]} {i // 4 + 1:02}", category=CATEGORIES[i % 4]))
        # Include recent, sparse, stale, zero, missing, and decreasing series.
        offsets = list(range(13)) if i % 6 in (0, 1, 2) else ([9, 12] if i % 6 == 3 else ([0, 1, 2] if i % 6 == 4 else [12]))
        for j in offsets:
            count = (i + 3) * 17 + j * (i % 7 + 2)
            if i == 0:
                count = 0
            if i == 2 and j >= 8:
                count -= 80
            if i == 1 and j == 12:
                count = ""
            observations.append(dict(product_id=product_id,
                observed_at=(AS_OF - timedelta(days=6, hours=3) + timedelta(hours=j * 12)).isoformat(), review_count=count))
    # A byte-equivalent duplicate exercises idempotent snapshot normalization.
    observations.append(observations[0].copy())
    write_csv(directory / "synthetic_products.csv", ["product_id", "brand", "name", "category"], products)
    write_csv(directory / "synthetic_observations.csv", ["product_id", "observed_at", "review_count"], observations)


def runs() -> list[dict]:
    result = []
    for day in range(7):
        for hour in (9, 13):
            failed = (day + hour) % 4
            reasons = {"timeout": 0, "identity_mismatch": 0, "ambiguous_count": 0}
            for i in range(failed):
                reasons[list(reasons)[i]] += 1
            result.append({"run_id": f"DEMO-RUN-{day:02}-{hour}",
                "started_at": (AS_OF.replace(hour=hour) - timedelta(days=day)).isoformat(),
                "job": "검색어 순환" if hour == 9 else "균형 재관측", "attempted": 20,
                "succeeded": 20 - failed, "failure_reasons": reasons})
    return sorted(result, key=lambda r: r["started_at"], reverse=True)
