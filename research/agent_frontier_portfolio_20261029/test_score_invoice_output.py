import unittest

try:
    from .score_invoice_output import score
except ImportError:
    from score_invoice_output import score


class InvoiceScoringTest(unittest.TestCase):
    def test_missed_false_positive_and_duplicate(self):
        reference = [{"invoice_page_number": 1, "reason": "Clean"},
                     {"invoice_page_number": 2, "reason": "Invalid PO"},
                     {"invoice_page_number": 3, "reason": "Unknown Vendor"}]
        predicted = [{"invoice_page_number": 1, "reason": "Invalid PO"},
                     {"invoice_page_number": 2, "reason": "Invalid PO"},
                     {"invoice_page_number": 2, "reason": "Invalid PO"}, {}]
        r = score(reference, predicted)
        self.assertEqual((r["true_positive"], r["false_positive"], r["false_negative"]), (1, 1, 1))
        self.assertEqual((r["duplicate_pages"], r["invalid_rows"]), (1, 1))
        self.assertEqual(r["reason_match_among_page_true_positives"], 1)

    def test_empty_output(self):
        r = score([{"invoice_page_number": 1, "reason": "Invalid PO"}], [])
        self.assertIsNone(r["precision"])
        self.assertEqual(r["recall"], 0)


if __name__ == "__main__":
    unittest.main()
