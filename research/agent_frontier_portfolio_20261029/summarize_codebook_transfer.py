#!/usr/bin/env python3
"""Summarize saved codebook agent outputs without presenting a proxy as gold."""
import argparse
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


def normalized(value):
    return " ".join(str(value or "").casefold().split())


def inspect_visible_inputs(data_dir):
    """Count simple label opportunities in public inputs without using predictions."""
    labels = {}
    for path in sorted(data_dir.glob("codebook_*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                label = normalized(row["standard_label"])
                if label:
                    labels.setdefault(row["product_id"], set()).add(label)
    counts = Counter()
    with (data_dir / "test_center_logs.csv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            counts["input_records"] += 1
            text = normalized(row["raw_reason_text"])
            options = labels.get(row["product_id"], set())
            if text in options:
                counts["exact_whole_label_in_raw_text"] += 1
            if any(label in text for label in options):
                counts["full_label_substring_in_raw_text"] += 1
    return {key: counts[key] for key in ("input_records", "exact_whole_label_in_raw_text", "full_label_substring_in_raw_text")}


def inspect_output(data_dir, output):
    """Aggregate public contract properties; exact label identity is not semantic truth."""
    with (data_dir / "test_center_logs.csv").open(encoding="utf-8", newline="") as handle:
        inputs = {row["record_id"]: row for row in csv.DictReader(handle)}
    codebooks = {}
    labels = {}
    for path in sorted(data_dir.glob("codebook_*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                product, code = row["product_id"], row["code"]
                codebooks[(product, code)] = row
                labels.setdefault((product, normalized(row["standard_label"])), set()).add(code)
    result = {"input_records": len(inputs), "has_output": output.is_file()}
    if not output.is_file():
        return result, {}
    result["output_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    try:
        obj = json.loads(output.read_text(encoding="utf-8"))
        records = obj.get("records", []) if isinstance(obj, dict) else []
        if not isinstance(records, list):
            raise ValueError("records is not a list")
    except (json.JSONDecodeError, ValueError, UnicodeError) as exc:
        result["parse_error"] = type(exc).__name__
        return result, {}
    counts = Counter()
    ids = set()
    assignments = {}
    for record in records:
        if not isinstance(record, dict):
            counts["malformed_records"] += 1
            continue
        rid = str(record.get("record_id", ""))
        if rid in ids:
            counts["duplicate_record_ids"] += 1
        ids.add(rid)
        source = inputs.get(rid)
        if source is None:
            counts["unknown_record_ids"] += 1
            continue
        product = source["product_id"]
        segments = record.get("normalized", [])
        if not isinstance(segments, list):
            counts["malformed_segment_lists"] += 1
            continue
        for seg in segments:
            if not isinstance(seg, dict):
                counts["malformed_segments"] += 1
                continue
            counts["segments"] += 1
            code = str(seg.get("pred_code", ""))
            segid = str(seg.get("segment_id", ""))
            key = (rid, segid)
            if key in assignments:
                counts["duplicate_segment_ids"] += 1
            assignments[key] = (code, str(seg.get("span_text", "")))
            if code == "UNKNOWN":
                counts["unknown_segments"] += 1
            else:
                entry = codebooks.get((product, code))
                if entry is None:
                    counts["invalid_codes"] += 1
                else:
                    counts["known_valid_codes"] += 1
                    scope = {s.strip() for s in entry["station_scope"].split(";") if s.strip()}
                    if scope and source["station"] not in scope:
                        counts["known_station_mismatch"] += 1
            exact = labels.get((product, normalized(seg.get("span_text"))), set())
            if exact:
                counts["exact_label_segments"] += 1
                if code in exact:
                    counts["exact_label_selected"] += 1
                if len(exact) > 1:
                    counts["exact_label_ambiguous"] += 1
    result.update({"output_records": len(records), "unique_output_ids": len(ids),
                   "input_ids_covered": len(ids & inputs.keys()), "counts": dict(counts)})
    return result, assignments


def summarize_case(case, data_dir):
    receipt = json.loads((case / "receipt.json").read_text(encoding="utf-8"))
    intervention = json.loads((case / "intervention.json").read_text(encoding="utf-8"))
    verifier = (case / "verifier.txt").read_text(encoding="utf-8", errors="replace")
    stats, assignments = inspect_output(data_dir, case / "work/output/solution.json")
    match = re.search(r"(\d+) failed, (\d+) passed", verifier)
    if match:
        failed, passed = int(match[1]), int(match[2])
    else:
        passed_only = re.search(r"(\d+) passed", verifier)
        failed_only = re.search(r"(\d+) failed", verifier)
        passed = int(passed_only[1]) if passed_only else None
        failed = int(failed_only[1]) if failed_only else None
    stats.update({"case": str(case), "condition": intervention["condition"],
                  "agent_exit": receipt["agent_exit"], "verifier_exit": receipt["verifier_exit"],
                  "tests_passed": passed, "tests_failed": failed,
                  "failed_tests": re.findall(r"^FAILED .*?::(test_\w+)", verifier, re.MULTILINE),
                  "post_requests": sum(item.startswith("POST ") for item in receipt["model_http_requests"]),
                  "denied_or_limit": receipt["model_http_requests"].count("DENIED_OR_LIMIT"),
                  "reported_step_tokens_including_cache": sum((item or {}).get("total", 0) or 0 for item in receipt["step_finish_tokens"]),
                  "step_finish_count": len(receipt["step_finish_tokens"]),
                  "elapsed_seconds_including_verifier": receipt["elapsed_seconds"],
                  "raw_sha256": receipt["raw_sha256"], "input_hashes": intervention["files"]})
    return stats, assignments


def compare_assignments(left, right):
    shared = left.keys() & right.keys()
    same_span = {k for k in shared if left[k][1] == right[k][1]}
    return {"shared_record_segment_ids": len(shared),
            "same_exact_span_with_shared_ids": len(same_span),
            "different_assigned_codes_on_same_exact_span": sum(left[k][0] != right[k][0] for k in same_span)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cases", type=Path)
    parser.add_argument("data", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    out, mappings = {}, {}
    for case in sorted(args.cases.iterdir()):
        if not (case / "receipt.json").is_file() or not (case / "intervention.json").is_file():
            continue
        result, assignments = summarize_case(case, args.data)
        condition = result["condition"]
        if condition in out:
            raise ValueError("More than one completed case for condition: " + condition)
        out[condition], mappings[condition] = result, assignments
    pair = {}
    if "no_memory" in mappings and "transferred_memory" in mappings:
        pair = compare_assignments(mappings["no_memory"], mappings["transferred_memory"])
    result = {"status": "DEVELOPMENT_ONLY_NOT_SEMANTIC_GOLD", "visible_input_diagnostics": inspect_visible_inputs(args.data),
              "cases": out, "pair": pair}
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
