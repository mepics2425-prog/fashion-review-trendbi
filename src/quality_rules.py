"""Operational comparability rubric, NOT statistical confidence."""
from datetime import datetime, timedelta
from .models import KST, Observation


def assess(observations: list[Observation], as_of: datetime, days: int = 7) -> dict:
    if as_of.tzinfo is None or days < 1:
        raise ValueError("Aware as_of and positive days required")
    # A missing extraction is an attempt, not a valid review observation.
    window = {o.observed_at: o for o in observations
              if as_of - timedelta(days=days) <= o.observed_at <= as_of and o.review_count is not None}
    values = sorted(window.values(), key=lambda o: o.observed_at)
    dates = len({o.observed_at.astimezone(KST).date() for o in values})
    span = (values[-1].observed_at - values[0].observed_at).total_seconds() / 3600 if values else 0
    age = (as_of - values[-1].observed_at).total_seconds() / 3600 if values else None
    grade = "추가 관측 필요"
    if age is not None and age <= 72:
        if dates >= 3 and span >= 48:
            grade = "반복 관측"
        elif dates >= 2 and span >= 24:
            grade = "비교 가능"
    return {"grade": grade, "snapshots": len(values), "distinct_dates": dates,
            "span_hours": round(span, 2), "age_hours": round(age, 2) if age is not None else None,
            "first_at": values[0].observed_at.isoformat() if values else None,
            "last_at": values[-1].observed_at.isoformat() if values else None}
