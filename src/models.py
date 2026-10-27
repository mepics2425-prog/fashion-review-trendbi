"""Typed boundary objects. All timestamps must carry a UTC offset."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
CATEGORIES = ("상의", "하의", "아우터", "원피스")


def timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timezone offset required")
    return result.astimezone(KST)


@dataclass(frozen=True)
class Product:
    product_id: str
    brand: str
    name: str
    category: str


@dataclass(frozen=True)
class Observation:
    product_id: str
    observed_at: datetime
    review_count: int | None
