import unittest
from pathlib import Path
import tempfile
from src.data_loader import read_csv
from src.data_validator import normalize_products, normalize_observations


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(product_id=" DEMO-001 ", brand=" DEMO   FORM ", name=" 테스트 티 ", category="상의")
        self.products = normalize_products([self.row])

    def obs(self, count="0", at="2026-10-26T09:00:00+09:00"):
        return dict(product_id="DEMO-001", observed_at=at, review_count=count)

    def test_product_normalization_and_idempotence(self):
        self.assertEqual(normalize_products([self.row, self.row]), self.products)
        self.assertEqual(self.products[0].brand, "DEMO FORM")

    def test_conflicting_product_rejected(self):
        with self.assertRaises(ValueError):
            normalize_products([self.row, {**self.row, "name": "different"}])

    def test_zero_missing_and_duplicate(self):
        values = normalize_observations([self.obs(), self.obs(), self.obs("", "2026-10-26T10:00:00+09:00")], self.products)
        self.assertEqual([o.review_count for o in values], [0, None])

    def test_timezone_equivalent_duplicates(self):
        self.assertEqual(len(normalize_observations([self.obs(), self.obs(at="2026-10-26T00:00:00Z")], self.products)), 1)

    def test_conflict_rejected(self):
        with self.assertRaises(ValueError):
            normalize_observations([self.obs(), self.obs("1")], self.products)

    def test_invalid_counts(self):
        for value in ("-1", "1.2", "NaN", "true"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_observations([self.obs(value)], self.products)

    def test_naive_and_unknown_rejected(self):
        for row in (self.obs(at="2026-10-26T09:00:00"), {**self.obs(), "product_id": "DEMO-999"}):
            with self.assertRaises(ValueError):
                normalize_observations([row], self.products)

    def test_absent_cell_is_not_an_explicit_missing_count(self):
        with self.assertRaisesRegex(ValueError, "text field"):
            normalize_observations([self.obs(None)], self.products)


class CsvBoundaryTests(unittest.TestCase):
    def parse(self, text, fields=("product_id", "review_count")):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.csv"
            path.write_text(text, encoding="utf-8")
            return read_csv(path, fields)

    def test_explicit_blank_and_bom_are_supported(self):
        self.assertEqual(self.parse("\ufeffproduct_id,review_count\nDEMO-001,\n")[0]["review_count"], "")

    def test_required_column_absent(self):
        with self.assertRaisesRegex(ValueError, "missing columns"):
            self.parse("product_id\nDEMO-001\n")

    def test_truncated_or_extra_cell(self):
        for row in ("DEMO-001", "DEMO-001,1,unexpected"):
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, "field count"):
                self.parse(f"product_id,review_count\n{row}\n")

    def test_duplicate_header(self):
        with self.assertRaisesRegex(ValueError, "duplicate CSV headers"):
            self.parse("product_id,review_count,review_count\nDEMO-001,1,2\n")

    def test_unclosed_quote(self):
        with self.assertRaisesRegex(ValueError, "malformed CSV"):
            self.parse('product_id,review_count\nDEMO-001,"1\n')

    def test_unclosed_header_quote(self):
        with self.assertRaisesRegex(ValueError, "malformed CSV header"):
            self.parse('product_id,"review_count\nDEMO-001,1\n')
