"""Run: python -m src.generate_demo [--regenerate-samples]."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from .data_loader import load
from .quality_rules import assess
from .synthetic_data import AS_OF, generate, runs
from .trend_analyzer import analyze

ROOT = Path(__file__).resolve().parents[1]


def build() -> dict:
    products, observations = load(ROOT / "sample_data")
    result = []
    for product in products:
        series = [o for o in observations if o.product_id == product.product_id]
        result.append({**asdict(product), "observations": [
            {"at": o.observed_at.isoformat(), "count": o.review_count} for o in series],
            "windows": {str(days): {"quality": assess(series, AS_OF, days), "trend": analyze(series, AS_OF, days)}
                        for days in (3, 7)}})
    return {"schema_version": 1, "synthetic": True, "as_of": AS_OF.isoformat(),
            "timezone": "Asia/Seoul", "quality_window_days": 7,
            "products": result, "runs": runs()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regenerate-samples", action="store_true")
    args = parser.parse_args()
    try:
        if args.regenerate_samples:
            generate(ROOT / "sample_data")
        data = build()
        target = ROOT / "docs/data/demo.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"Synthetic demo generated: {len(data['products'])} products, {len(data['runs'])} fictional runs")
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"Demo generation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
