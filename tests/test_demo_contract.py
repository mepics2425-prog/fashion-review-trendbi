import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from unittest.mock import patch
from src.data_loader import load
from src.generate_demo import build
from src.synthetic_data import generate
from src.generate_demo import main


class DemoContractTests(unittest.TestCase):
    def test_reproducible_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            generate(path)
            before = {p.name: p.read_bytes() for p in path.iterdir()}
            generate(path)
            self.assertEqual(before, {p.name: p.read_bytes() for p in path.iterdir()})
            products, observations = load(path)
            self.assertEqual(len(products), 24)
            self.assertEqual(len(observations), 180)
            self.assertEqual(sum(o.review_count is not None for o in observations), 179)

    def test_export_json_matches_current_code(self):
        path = Path(__file__).resolve().parents[1] / "docs/data/demo.json"
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), build())

    def test_overview_contract(self):
        data = build()
        self.assertTrue(data["synthetic"])
        groups = {grade: sum(p["windows"]["7"]["quality"]["grade"] == grade for p in data["products"])
                  for grade in ("반복 관측", "비교 가능", "추가 관측 필요")}
        self.assertEqual(list(groups.values()), [12, 4, 8])
        eligible = [p["windows"]["7"]["trend"] for p in data["products"]
                    if p["windows"]["7"]["quality"]["grade"] != "추가 관측 필요"
                    and p["windows"]["7"]["trend"]["status"] == "comparable"]
        self.assertEqual(sum(p["delta"] for p in eligible), 687)

    def test_monitoring_denominator_and_failures(self):
        runs = build()["runs"]
        self.assertEqual(len(runs), 14)
        self.assertEqual(sum(r["attempted"] for r in runs), 280)
        self.assertEqual(sum(r["succeeded"] for r in runs), 256)
        for run in runs:
            self.assertEqual(sum(run["failure_reasons"].values()), run["attempted"] - run["succeeded"])

    def test_cli_rejects_truncated_csv_without_overwriting_previous_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generate(root / "sample_data")
            (root / "sample_data/synthetic_observations.csv").write_text(
                "product_id,observed_at,review_count\nDEMO-001,2026-10-26T09:00:00+09:00\n", encoding="utf-8")
            output = root / "docs/data/demo.json"
            output.parent.mkdir(parents=True)
            output.write_text("previous valid export", encoding="utf-8")
            errors = StringIO()
            with patch("src.generate_demo.ROOT", root), patch("sys.argv", ["generate_demo"]), redirect_stderr(errors):
                self.assertEqual(main(), 1)
            self.assertIn("incorrect field count", errors.getvalue())
            self.assertNotIn("Traceback", errors.getvalue())
            self.assertEqual(output.read_text(encoding="utf-8"), "previous valid export")
