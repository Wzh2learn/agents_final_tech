"""Measure field value extraction accuracy against ground truth."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import m1_statement_parser as m1p

SAMPLES_DIR = os.path.expanduser("~/wzh/m1_samples")
GROUND_TRUTH = os.path.join(os.path.dirname(__file__), "..", "tests", "ground_truth_values.json")



def _desensitized_match(expected: str, actual: str) -> bool:
    """Check if actual matches expected, accounting for **** desensitization.
    
    Desensitized values like '2000****8295' should match '200030028295'
    because the visible prefix/suffix align.
    """
    expected = str(expected)
    actual = str(actual)
    if expected == actual:
        return True
    if expected in actual or actual in expected:
        return True
    # Handle desensitization: split on **** and check prefix/suffix
    if "****" in actual:
        parts = actual.split("****")
        prefix, suffix = parts[0], parts[-1] if len(parts) > 1 else ""
        if prefix and not expected.startswith(prefix):
            return False
        if suffix and not expected.endswith(suffix):
            return False
        return True
    if "****" in expected:
        parts = expected.split("****")
        prefix, suffix = parts[0], parts[-1] if len(parts) > 1 else ""
        if prefix and not actual.startswith(prefix):
            return False
        if suffix and not actual.endswith(suffix):
            return False
        return True
    return False


def evaluate_sample(sample_id: str, result: dict, expected: dict) -> dict:
    """Compare parsed result against ground truth. Returns accuracy stats."""
    checks = []
    
    # Check header_meta
    actual_meta = result.get("header_meta", {})
    for key, expected_val in expected.get("header_meta", {}).items():
        actual_val = str(actual_meta.get(key, ""))
        # Fuzzy match: check if expected is substring of actual (handles desensitization)
        match = _desensitized_match(expected_val, actual_val)
        checks.append({"field": f"meta.{key}", "expected": expected_val, "actual": actual_val, "match": match})
    
    # Check table values
    actual_tables = result.get("tables", [])
    for table_name, table_checks in expected.get("tables", {}).items():
        # Find matching table
        matching_table = None
        for t in actual_tables:
            if t.get("matched_schema") == table_name or table_name in t.get("table", ""):
                matching_table = t
                break
        
        if matching_table is None:
            checks.append({"field": f"table.{table_name}", "expected": "exists", "actual": "NOT FOUND", "match": False})
            continue
        
        records = matching_table.get("_records", matching_table.get("records", []))
        
        for check_key, check_val in table_checks.items():
            if check_key == "row_count":
                actual_count = len(records)
                match = actual_count == check_val
                checks.append({"field": f"{table_name}.row_count", "expected": check_val, "actual": actual_count, "match": match})
            elif check_key == "row_count_gte":
                actual_count = len(records)
                match = actual_count >= check_val
                checks.append({"field": f"{table_name}.row_count>={check_val}", "expected": f">={check_val}", "actual": actual_count, "match": match})
            elif check_key.startswith("has_"):
                code = check_key[4:]
                found = any(_desensitized_match(code, str(v)) for r in records for v in r.values())
                checks.append({"field": f"{table_name}.has_{code}", "expected": True, "actual": found, "match": found == check_val})
            elif "_" in check_key:
                # Format: row_identifier_field_value (e.g. "600157_市值")
                parts = check_key.split("_", 1)
                row_id, field_name = parts[0], parts[1]
                # Find the row
                target_row = None
                for r in records:
                    if row_id in str(r.values()):
                        target_row = r
                        break
                if target_row:
                    actual_val = str(target_row.get(field_name, ""))
                    expected_str = str(check_val)
                    match = _desensitized_match(expected_str, actual_val)
                    checks.append({"field": f"{table_name}.{row_id}.{field_name}", "expected": expected_str, "actual": actual_val, "match": match})
                else:
                    checks.append({"field": f"{table_name}.{row_id}", "expected": "row exists", "actual": "NOT FOUND", "match": False})
            else:
                # Direct field check in first record
                if records:
                    actual_val = str(records[0].get(check_key, ""))
                    expected_str = str(check_val)
                    match = _desensitized_match(expected_str, actual_val)
                    checks.append({"field": f"{table_name}.{check_key}", "expected": expected_str, "actual": actual_val, "match": match})
    
    return checks


def main():
    with open(GROUND_TRUTH) as f:
        gt = json.load(f)
    
    schema = m1p.Schema.load(m1p.DEFAULT_SCHEMA)
    
    total_checks = 0
    total_pass = 0
    results = {}
    
    for sample_id, expected in gt.items():
        path = os.path.join(SAMPLES_DIR, sample_id)
        if not os.path.exists(path):
            print(f"SKIP {sample_id}: file not found")
            continue
        
        t0 = time.perf_counter()
        result = m1p.process_sample(path, schema, llm_fallback=False)
        parse_ms = int((time.perf_counter() - t0) * 1000)
        
        checks = evaluate_sample(sample_id, result, expected)
        passed = sum(1 for c in checks if c["match"])
        total = len(checks)
        total_checks += total
        total_pass += passed
        
        results[sample_id] = {
            "parse_ms": parse_ms,
            "checks": total,
            "passed": passed,
            "accuracy": round(passed / total * 100, 1) if total else 0,
            "failures": [c for c in checks if not c["match"]],
        }
        
        status = "✓" if passed == total else "✗"
        print(f"  {status} {sample_id}: {passed}/{total} ({results[sample_id]['accuracy']}%) [{parse_ms}ms]")
        for fail in results[sample_id]["failures"]:
            print(f"      FAIL: {fail['field']} expected={fail['expected']} actual={fail['actual']}")
    
    overall = round(total_pass / total_checks * 100, 1) if total_checks else 0
    print(f"\n=== OVERALL: {total_pass}/{total_checks} = {overall}% ===")
    
    # Save report
    report = {"overall_accuracy": overall, "total_checks": total_checks, "passed": total_pass, "per_sample": results}
    with open("docs/experiments/2026-08-01_field_accuracy.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Report saved to docs/experiments/2026-08-01_field_accuracy.json")


if __name__ == "__main__":
    main()
