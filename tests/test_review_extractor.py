import unittest
from src.review_extractor import extract_review_count

# Fictional numeric ID for an offline fixture; never requested over a network.
URL = "https://www.musinsa.com/app/goods/999999999"


def product(count=0, url=URL):
    return {"@type": "Product", "url": url, "aggregateRating": {"reviewCount": count}}


class ExtractorTests(unittest.TestCase):
    def test_graph_zero(self):
        self.assertEqual(extract_review_count(URL, URL, [{"@graph": [product()]}]), 0)

    def test_unique_count(self):
        self.assertEqual(extract_review_count(URL, URL, [product("42"), product(42)]), 42)

    def test_ambiguity(self):
        self.assertIsNone(extract_review_count(URL, URL, [product(42), product(43)]))

    def test_wrong_product(self):
        self.assertIsNone(extract_review_count(URL, URL, [product(2, URL + "1")]))
        with self.assertRaises(ValueError):
            extract_review_count(URL, URL + "1", [product()])

    def test_untrusted_and_malformed(self):
        with self.assertRaises(ValueError):
            extract_review_count("https://evil.example/goods/1", URL, [])
        for value in (True, -1, "1,000", 1.2):
            self.assertIsNone(extract_review_count(URL, URL, [product(value)]))

    def test_not_product_or_missing(self):
        self.assertIsNone(extract_review_count(URL, URL, [{"@type": "Organization", "reviewCount": 2}]))
        self.assertIsNone(extract_review_count(URL, URL, [product(None)]))

    def test_malformed_identity_and_type(self):
        self.assertIsNone(extract_review_count(URL, URL, [{**product(), "url": None}]))
        self.assertIsNone(extract_review_count(URL, URL, [{**product(), "@type": None}]))
        self.assertIsNone(extract_review_count(URL, URL, [{**product(), "aggregateRating": []}]))
        with self.assertRaises(ValueError):
            extract_review_count(URL.replace("www.", "user@www."), URL, [])
