import unittest
from datetime import timedelta
from src.models import Observation
from src.synthetic_data import AS_OF
from src.trend_analyzer import analyze


class TrendTests(unittest.TestCase):
    def series(self, counts):
        return [Observation("DEMO-001", AS_OF - timedelta(days=len(counts)-i-1), count) for i, count in enumerate(counts)]

    def test_elapsed_time_rate(self):
        result = analyze(self.series([0, 4, 10]), AS_OF)
        self.assertEqual(result["delta"], 10)
        self.assertEqual(result["reviews_per_day"], 5)

    def test_missing_not_zero(self):
        self.assertIsNone(analyze(self.series([None, 0]), AS_OF)["delta"])
        self.assertEqual(analyze(self.series([0, 0]), AS_OF)["delta"], 0)

    def test_negative_retained_rate_excluded(self):
        result = analyze(self.series([100, 90]), AS_OF)
        self.assertEqual(result["delta"], -10)
        self.assertIsNone(result["reviews_per_day"])

    def test_intermediate_decrease(self):
        self.assertEqual(analyze(self.series([100, 90, 120]), AS_OF)["status"], "decrease_detected")

    def test_duplicate_and_window(self):
        values = self.series([1, 2])
        self.assertEqual(analyze(values + values, AS_OF)["delta"], 1)
        self.assertIsNone(analyze(values, AS_OF + timedelta(days=10))["delta"])

    def test_empty(self):
        self.assertEqual(analyze([], AS_OF)["status"], "insufficient")
