import unittest

from order_intake_demo.pipeline import process_order


class PipelineTests(unittest.TestCase):
    def test_matches_exact_sku_and_calculates_totals(self):
        result = process_order(
            {
                "customer": "Firma Demo",
                "lines": [
                    {"sku": "PANEL-WHITE-18", "quantity": 3},
                    {"sku": "EDGE-OAK-22", "quantity": 2},
                ],
            }
        )

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["net_total"], 201.0)
        self.assertEqual(result["gross_total"], 247.23)

    def test_sends_unknown_product_to_review_instead_of_guessing(self):
        result = process_order(
            {
                "customer": "Firma Demo",
                "lines": [{"sku": "PANEL-WHIT-18", "quantity": 1}],
            }
        )

        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["review_items"][0]["reason"], "unknown_sku")
        self.assertIsNone(result["net_total"])

    def test_rejects_duplicate_source_id_idempotently(self):
        seen = {"mail-2026-001"}
        result = process_order(
            {
                "source_id": "mail-2026-001",
                "customer": "Firma Demo",
                "lines": [{"sku": "PANEL-WHITE-18", "quantity": 1}],
            },
            seen_source_ids=seen,
        )

        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(result["reason"], "source_id_already_processed")


if __name__ == "__main__":
    unittest.main()
