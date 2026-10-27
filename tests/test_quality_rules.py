import unittest
from datetime import timedelta
from src.models import Observation, timestamp
from src.quality_rules import assess

NOW = timestamp("2026-10-26T18:00:00+09:00")


class QualityTests(unittest.TestCase):
    def series(self, hours):
        return [Observation("DEMO-001", NOW - timedelta(hours=h), 0) for h in hours]

    def test_repeat_boundaries(self):
        self.assertEqual(assess(self.series([120, 96, 72]), NOW)["grade"], "반복 관측")

    def test_comparable_boundary(self):
        self.assertEqual(assess(self.series([24, 0]), NOW)["grade"], "비교 가능")

    def test_stale_boundary(self):
        self.assertEqual(assess(self.series([120.01, 96.01, 72.01]), NOW)["grade"], "추가 관측 필요")

    def test_multiple_dates_insufficient_span(self):
        self.assertEqual(assess(self.series([13, 0]), NOW)["grade"], "추가 관측 필요")

    def test_kst_dates(self):
        values = [Observation("DEMO-001", timestamp(t), 1) for t in
                  ("2026-10-25T14:59:00Z", "2026-10-25T15:01:00Z")]
        self.assertEqual(assess(values, NOW)["distinct_dates"], 2)

    def test_window_future_and_missing(self):
        values = self.series([200, -1]) + [Observation("DEMO-001", NOW, None)]
        self.assertEqual(assess(values, NOW)["snapshots"], 0)
        self.assertIsNone(assess(values, NOW)["age_hours"])

    def test_duplicate_does_not_inflate(self):
        values = self.series([24, 0])
        self.assertEqual(assess(values + values, NOW)["snapshots"], 2)

    def test_48_hour_span_and_just_below(self):
        self.assertEqual(assess(self.series([48, 24, 0]), NOW)["grade"], "반복 관측")
        self.assertEqual(assess(self.series([47.99, 24, 0]), NOW)["grade"], "비교 가능")

    def test_inclusive_window_start(self):
        self.assertEqual(assess(self.series([168, 168.01, 0]), NOW)["snapshots"], 2)

    def test_missing_latest_does_not_refresh_recency(self):
        values = self.series([120, 96, 73]) + [Observation("DEMO-001", NOW, None)]
        self.assertEqual(assess(values, NOW)["grade"], "추가 관측 필요")
        self.assertEqual(assess(values, NOW)["age_hours"], 73)
