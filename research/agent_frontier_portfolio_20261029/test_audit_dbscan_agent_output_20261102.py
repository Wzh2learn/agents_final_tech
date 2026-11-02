from pathlib import Path

from audit_dbscan_agent_output_20261102 import analyze


HEADER = "F1,delta,min_samples,epsilon,shape_weight\n"
ROW = "0.7,15,3,10,1.8\n"


def run(tmp_path: Path, text):
    reference, output = tmp_path / "reference.csv", tmp_path / "output.csv"
    reference.write_text(HEADER + ROW, encoding="utf-8")
    if text is not None:
        output.write_text(text, encoding="utf-8")
    return analyze(output, reference)


def test_exact_reference_is_accepted(tmp_path):
    assert run(tmp_path, HEADER + ROW)["classification"] == "MATCHES_RELEASED_REFERENCE_WITHIN_TOLERANCES"


def test_extra_key_is_unresolved_and_conflicting_duplicate_is_not_accepted(tmp_path):
    extra = run(tmp_path, HEADER + ROW + "0.71,16,4,12,1.7\n")
    assert extra["classification"] == "UNRESOLVED_ADDITIONAL_OR_DUPLICATE_ROWS"
    assert extra["extra_parameter_rows_unresolved"] == 1
    conflict = run(tmp_path, HEADER + ROW + "0.71,16,3,10,1.8\n")
    assert conflict["classification"] == "CONTRACT_OR_REFERENCE_MISMATCH"
    assert conflict["conflicting_duplicate_parameter_keys"] == 1


def test_missing_malformed_and_out_of_grid_are_distinct(tmp_path):
    assert run(tmp_path, None)["classification"] == "NO_OUTPUT"
    assert run(tmp_path, HEADER + "nan,15,3,10,1.8\n")["classification"] == "INVALID_OUTPUT"
    bad = run(tmp_path, HEADER + "0.7,15,3,11,1.8\n")
    assert bad["invalid_rows"] == 1 and bad["missing_reference_keys"] == 1
