#!/usr/bin/env python3
"""Post-agent diagnostic metrics against the benchmark reference.

This complements but does not replace the original verifier. The evaluator
and its ground truth must not be mounted into the agent container.
"""
from pathlib import Path
import json
import sys


def score(reference, predicted):
    if not isinstance(reference, list) or not isinstance(predicted, list):
        raise ValueError("expected list inputs")
    expected = {x["invoice_page_number"]: x for x in reference if x.get("reason") != "Clean"}
    clean = {x["invoice_page_number"] for x in reference if x.get("reason") == "Clean"}
    valid = [x for x in predicted if isinstance(x, dict) and isinstance(x.get("invoice_page_number"), int)
             and not isinstance(x["invoice_page_number"], bool)]
    actual = {x["invoice_page_number"]: x for x in valid}
    expected_ids, actual_ids = set(expected), set(actual)
    correct_ids = expected_ids & actual_ids
    true_positive, false_positive, false_negative = len(correct_ids), len(actual_ids - expected_ids), len(expected_ids - actual_ids)
    reason_match = sum(actual[i].get("reason") == expected[i].get("reason") for i in correct_ids)
    return {"expected_positive": len(expected_ids), "reference_clean": len(clean),
            "predicted_rows": len(predicted), "valid_unique_pages": len(actual_ids),
            "invalid_rows": len(predicted) - len(valid), "duplicate_pages": len(valid) - len(actual_ids),
            "true_positive": true_positive, "false_positive": false_positive, "false_negative": false_negative,
            "precision": true_positive / (true_positive + false_positive) if true_positive + false_positive else None,
            "recall": true_positive / (true_positive + false_negative) if true_positive + false_negative else None,
            "reason_match_among_page_true_positives": reason_match,
            "full_field_validation": "not_checked_by_this_diagnostic; see original verifier"}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: score_invoice_output.py ground_truth.json prediction.json")
    ref, pred = (json.loads(Path(x).read_text(encoding="utf8")) for x in sys.argv[1:])
    print(json.dumps(score(ref, pred), indent=2))
