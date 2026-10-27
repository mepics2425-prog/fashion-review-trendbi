"""Review counts are cumulative signals, not sales or review text sentiment."""
from datetime import datetime, timedelta
from .models import Observation


def analyze(observations: list[Observation], as_of: datetime, days: int = 7) -> dict:
    if as_of.tzinfo is None or days < 1:
        raise ValueError("Aware as_of and positive days required")
    window = {o.observed_at: o for o in observations
              if as_of - timedelta(days=days) <= o.observed_at <= as_of and o.review_count is not None}
    values = sorted(window.values(), key=lambda o: o.observed_at)
    latest = values[-1].review_count if values else None
    if len(values) < 2:
        return {"latest_count": latest, "delta": None, "reviews_per_day": None, "status": "insufficient"}
    hours = (values[-1].observed_at - values[0].observed_at).total_seconds() / 3600
    delta = values[-1].review_count - values[0].review_count
    has_decrease = any(b.review_count < a.review_count for a, b in zip(values, values[1:]))
    # Retain the signed endpoint change, exclude any declining series from growth ranking.
    return {"latest_count": latest, "delta": delta,
            "reviews_per_day": round(delta / (hours / 24), 2) if hours and not has_decrease else None,
            "status": "decrease_detected" if has_decrease else "comparable"}
