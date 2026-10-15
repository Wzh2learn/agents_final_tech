#!/usr/bin/env python3
"""Paper E Layer-1 v4 runner (contract v2)."""
import argparse
import hashlib
import json
import re
import string
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DEFAULT_CONTRACT = HERE / "LAYER1_V4_COMPACT_CONTRACT_v3.json"
DEFAULT_MANIFEST = HERE / "V4_GOVERNING_MANIFEST_v3.json"
DEFAULT_FIXTURES = HERE / "fixtures" / "SYNTHETIC_FIXTURES_v3.json"

E = "LEGAL_VARIATION"
H = "HARMFUL_ERROR"
U = "INSUFFICIENT_EVIDENCE"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical_norm(value):
    if not isinstance(value, str):
        return "NON_STRING"
    text = unicodedata.normalize("NFKC", value).casefold()
    text = "".join(
        " " if (unicodedata.category(ch).startswith("P") or ch in string.punctuation) else ch
        for ch in text
    )
    return re.sub(r"\s+", " ", text).strip()


def levenshtein(left, right):
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for i, ch_left in enumerate(left, 1):
        current = [i] + [0] * len(right)
        for j, ch_right in enumerate(right, 1):
            current[j] = min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (ch_left != ch_right),
            )
        previous = current
    return previous[-1]


def serialize_values(values):
    return json.dumps(values, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def injection_id(entry):
    if isinstance(entry.get("injection_id"), str) and entry["injection_id"]:
        return entry["injection_id"]
    fields = ("uid", "col", "original", "injected", "type", "variant", "seed_component")
    parts = [json.dumps(entry.get(field), ensure_ascii=False, separators=(",", ":")) for field in fields]
    return "\x1f".join(parts)


def is_dev(entry):
    digest = hashlib.sha256(injection_id(entry).encode("utf-8")).digest()
    return int.from_bytes(digest, "big") % 10 < 5


def index_tables(records, label):
    indexed = {}
    for record in records:
        uid = record.get("uid")
        table = record.get("table")
        if not isinstance(uid, str) or not isinstance(table, list):
            raise ValueError("%s: malformed table record" % label)
        if uid in indexed:
            raise ValueError("%s: duplicate uid %s" % (label, uid))
        indexed[uid] = table
    return indexed


def extract_column_values(table, col):
    if not table or not isinstance(table[0], list):
        raise ValueError("missing header row")
    values = []
    for row in table[1:]:
        if not isinstance(row, list) or col >= len(row):
            raise ValueError("malformed row or col out of range")
        values.append(row[col])
    return values


def base_row(identifier, entry, split_name):
    return {
        "injection_id": identifier,
        "uid": entry.get("uid"),
        "col": entry.get("col"),
        "type": entry.get("type"),
        "original": entry.get("original"),
        "injected": entry.get("injected"),
        "split": split_name,
        "label": U,
        "reason": None,
        "binding": None,
        "nearest_distances": None,
    }


def u_row(identifier, entry, split_name, reason, extra=None):
    row = base_row(identifier, entry, split_name)
    row["reason"] = reason
    if extra:
        row.update(extra)
    return row


def label_from_rows(entry, source_rows, injected_rows, split_name):
    identifier = injection_id(entry)
    uid = entry.get("uid")
    if not isinstance(uid, str):
        return u_row(identifier, entry, split_name, "uid_not_string")
    if entry.get("row") != 0:
        return u_row(identifier, entry, split_name, "header_row_not_zero")
    if not source_rows or not injected_rows:
        return u_row(identifier, entry, split_name, "table_header_missing")
    if not isinstance(source_rows[0], list) or not source_rows[0]:
        return u_row(identifier, entry, split_name, "source_header_not_list")
    if not isinstance(injected_rows[0], list) or not injected_rows[0]:
        return u_row(identifier, entry, split_name, "injected_header_not_list")
    source_headers = source_rows[0]
    if not all(isinstance(header, str) for header in source_headers):
        return u_row(identifier, entry, split_name, "source_header_non_string")
    col = entry.get("col")
    if isinstance(col, bool) or not isinstance(col, int):
        return u_row(identifier, entry, split_name, "column_index_not_integer")
    if col < 0 or col >= len(source_headers):
        return u_row(identifier, entry, split_name, "column_index_out_of_range")
    if entry.get("original") != source_headers[col]:
        return u_row(identifier, entry, split_name, "original_header_provenance_mismatch")
    if col >= len(injected_rows[0]) or injected_rows[0][col] != entry.get("injected"):
        return u_row(identifier, entry, split_name, "injected_header_provenance_mismatch")
    if len(source_rows) != len(injected_rows):
        return u_row(identifier, entry, split_name, "row_count_mismatch")
    try:
        clean_values = extract_column_values(source_rows, col)
        injected_values = extract_column_values(injected_rows, col)
        clean_bytes = serialize_values(clean_values)
        injected_bytes = serialize_values(injected_values)
    except (TypeError, ValueError, OverflowError):
        return u_row(identifier, entry, split_name, "value_serialization_failure")
    value_evidence = {
        "value_invariant": clean_bytes == injected_bytes,
        "clean_column_sha256": sha256_bytes(clean_bytes),
        "injected_column_sha256": sha256_bytes(injected_bytes),
        "clean_value_count": len(clean_values),
        "injected_value_count": len(injected_values),
    }
    if clean_bytes != injected_bytes:
        return u_row(identifier, entry, split_name, "value_invariance_failed_bytewise", value_evidence)

    canonical = [canonical_norm(header) for header in source_headers]
    original_norm = canonical_norm(entry.get("original"))
    injected_norm = canonical_norm(entry.get("injected"))
    if original_norm == "NON_STRING" or injected_norm == "NON_STRING":
        return u_row(identifier, entry, split_name, "header_non_string", value_evidence)
    if injected_norm == "":
        return u_row(identifier, entry, split_name, "injected_header_empty_after_norm", value_evidence)
    if canonical[col] == "":
        return u_row(identifier, entry, split_name, "source_header_empty_after_norm_column_local", value_evidence)
    nonempty_other = {canonical[pos] for pos in range(len(canonical)) if pos != col and canonical[pos] != ""}
    if canonical[col] in nonempty_other:
        return u_row(identifier, entry, split_name, "source_header_canonical_collision_column_local", value_evidence)

    empty_positions = {pos for pos, value in enumerate(canonical) if value == ""}
    candidates = [pos for pos in range(len(canonical)) if pos not in empty_positions]
    row = base_row(identifier, entry, split_name)
    row.update(value_evidence)
    if injected_norm == original_norm:
        row.update({
            "label": E,
            "reason": "unique_nearest_neighbour_target",
            "binding": col,
            "nearest_distances": {str(col): 0},
        })
        return row
    distances = {str(pos): levenshtein(injected_norm, canonical[pos]) for pos in candidates}
    minimum = min(distances.values())
    nearest = [pos for pos in candidates if distances[str(pos)] == minimum]
    row["nearest_distances"] = distances
    if len(nearest) != 1:
        row.update({"label": U, "reason": "nearest_neighbour_tie"})
        return row
    binding = nearest[0]
    if binding == col:
        row.update({"label": E, "reason": "unique_nearest_neighbour_target", "binding": binding})
    else:
        row.update({"label": H, "reason": "unique_nearest_neighbour_other_column", "binding": binding})
    return row


def verify_governing(contract_path, manifest_path):
    manifest = load_json(manifest_path)
    contract_hash = sha256_file(contract_path)
    if manifest.get("governing_contract_sha256") != contract_hash:
        raise SystemExit("HASH_MISMATCH: contract hash does not match governing manifest")
    contract = load_json(contract_path)
    if contract.get("status") != "FROZEN_BEFORE_LABELS":
        raise SystemExit("RULE_AMBIGUOUS: contract is not frozen")
    runner_spec = manifest.get("runner")
    if not isinstance(runner_spec, dict) or runner_spec.get("sha256") != sha256_file(Path(__file__)):
        raise SystemExit("HASH_MISMATCH: runner hash does not match governing manifest")
    return contract, manifest, contract_hash


def check_inputs(contract, skip=()):
    for name, spec in contract["inputs"].items():
        if name in skip:
            continue
        path = REPO / spec["path"]
        if not path.exists():
            raise SystemExit("INPUT_MISSING: %s" % path)
        actual = sha256_file(path)
        if actual != spec["sha256"]:
            raise SystemExit("HASH_MISMATCH: %s expected %s got %s" % (name, spec["sha256"], actual))


def preflight_lock_path():
    return HERE / "PREFLIGHT_LOCK_v1.json"


def verify_preflight_lock(contract_hash, manifest_path, fixtures_path=DEFAULT_FIXTURES):
    lock_path = preflight_lock_path()
    if not lock_path.exists():
        raise SystemExit("INPUT_MISSING: preflight lock")
    lock = load_json(lock_path)
    receipt_hash = sha256_file(HERE / "PREFLIGHT_RECEIPT_v1.json")
    if lock.get("preflight_receipt_sha256") != receipt_hash:
        raise SystemExit("POST_FREEZE_CHANGE: preflight receipt changed after lock")
    if lock.get("manifest_sha256") != sha256_file(manifest_path):
        raise SystemExit("POST_FREEZE_CHANGE: manifest changed after lock")
    verify_preflight_receipt(contract_hash, manifest_path, fixtures_path)


def verify_preflight_receipt(contract_hash, manifest_path, fixtures_path=DEFAULT_FIXTURES):
    receipt_path = HERE / "PREFLIGHT_RECEIPT_v1.json"
    if not receipt_path.exists():
        raise SystemExit("INPUT_MISSING: preflight receipt")
    receipt = load_json(receipt_path)
    if receipt.get("status") != "PASS":
        raise SystemExit("POST_FREEZE_CHANGE: preflight did not pass")
    if receipt.get("contract_sha256") != contract_hash:
        raise SystemExit("POST_FREEZE_CHANGE: contract changed after preflight")
    if receipt.get("fixtures_sha256") != sha256_file(fixtures_path):
        raise SystemExit("POST_FREEZE_CHANGE: fixtures changed after preflight")
    if receipt.get("manifest_sha256") != sha256_file(manifest_path):
        raise SystemExit("POST_FREEZE_CHANGE: manifest changed after preflight")


def run_preflight(contract_path, manifest_path, fixtures_path, allow_overwrite=False):
    contract, manifest, contract_hash = verify_governing(contract_path, manifest_path)
    fixtures = load_json(fixtures_path)
    if sha256_file(fixtures_path) != manifest.get("fixtures_sha256"):
        raise SystemExit("HASH_MISMATCH: fixtures do not match manifest")
    results = []
    failures = []
    for fixture in fixtures["fixtures"]:
        entry = {
            "uid": fixture["id"],
            "row": 0,
            "col": fixture["col"],
            "original": fixture["original"],
            "injected": fixture["injected"],
            "type": "synthetic_fixture",
            "variant": fixture["id"],
            "seed_component": 0,
        }
        injected_table = [list(row) for row in fixture["table"]]
        injected_table[0][fixture["col"]] = fixture["injected"]
        row = label_from_rows(entry, fixture["table"], injected_table, "fixture")
        actual = (row["label"], row["reason"])
        expected = (fixture["expected_label"], fixture["expected_reason"])
        passed = actual == expected
        results.append({"id": fixture["id"], "expected": list(expected), "actual": list(actual), "passed": passed})
        if not passed:
            failures.append(fixture["id"])
    if preflight_lock_path().exists() and not allow_overwrite:
        raise SystemExit("POST_FREEZE_CHANGE: preflight lock exists; re-running preflight requires --allow-preflight-overwrite and a fresh audit")
    receipt = {
        "schema": "paper_e_layer1_v4_preflight_receipt",
        "status": "PASS" if not failures else "FAIL",
        "contract_sha256": contract_hash,
        "manifest_sha256": sha256_file(manifest_path),
        "fixtures_sha256": sha256_file(fixtures_path),
        "fixture_count": len(results),
        "failures": failures,
        "results": results,
        "calls": {"model": 0, "judge": 0, "network": 0, "training": 0},
    }
    (HERE / "PREFLIGHT_RECEIPT_v1.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "failures": failures, "fixture_count": len(results)}))
    return 0 if not failures else 1


def run_heldout(contract_path, manifest_path, fixtures_path):
    contract, manifest, contract_hash = verify_governing(contract_path, manifest_path)
    check_inputs(contract, skip=("checker_target",))
    verify_preflight_lock(contract_hash, manifest_path, fixtures_path)
    injection_map = load_json(REPO / contract["inputs"]["injection_map"]["path"])
    source_tables = index_tables(load_json(REPO / contract["inputs"]["source_tables"]["path"]), "source")
    injected_tables = index_tables(load_json(REPO / contract["inputs"]["injected_tables"]["path"]), "injected")
    records = injection_map.get("mapping", injection_map) if isinstance(injection_map, dict) else injection_map
    heldout = [entry for entry in records if not is_dev(entry)]
    if len(heldout) != contract["sample"]["size"]:
        raise SystemExit("RULE_AMBIGUOUS: heldout size %d != %d" % (len(heldout), contract["sample"]["size"]))
    rows = []
    for entry in heldout:
        uid = entry.get("uid")
        if uid not in source_tables or uid not in injected_tables:
            rows.append(u_row(injection_id(entry), entry, "heldout", "table_lookup_missing"))
            continue
        rows.append(label_from_rows(entry, source_tables[uid], injected_tables[uid], "heldout"))
    labels_json = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    labels_sha = sha256_bytes(labels_json)
    frozen = HERE / "V4_HELDOUT_LABELS_FROZEN_v1.json"
    frozen.write_bytes(labels_json)
    checker_spec = contract["inputs"]["checker_target"]
    checker_path = REPO / checker_spec["path"]
    if sha256_file(checker_path) != checker_spec["sha256"]:
        raise SystemExit("HASH_MISMATCH: checker_target")
    checker = load_json(checker_path)
    checker_lookup = {}
    for item in checker.get("injections", []):
        key = (item.get("uid"), item.get("col"), item.get("original"), item.get("injected"), item.get("type"))
        checker_lookup[key] = "visible" if item.get("visible_frozen") else "blind"
    for row in rows:
        key = (row.get("uid"), row.get("col"), row.get("original"), row.get("injected"), row.get("type"))
        if key not in checker_lookup:
            raise SystemExit("UNDECIDED_CASE: checker join missing for %s" % (key,))
        row["checker_verdict"] = checker_lookup[key]
    label_counts = {E: 0, H: 0, U: 0}
    for row in rows:
        label_counts[row["label"]] += 1
    contingency = {verdict: {label: 0 for label in (E, H, U)} for verdict in ("visible", "blind")}
    for row in rows:
        contingency[row["checker_verdict"]][row["label"]] += 1
    n_heldout = len(rows)
    u_rate = label_counts[U] / n_heldout
    blind_total = sum(contingency["blind"].values())
    visible_total = sum(contingency["visible"].values())
    co_miss = contingency["blind"][H] / blind_total if blind_total else None
    co_alarm = contingency["visible"][E] / visible_total if visible_total else None
    verdict = "GOLD_ESTABLISHED_ON_HELDOUT" if u_rate <= 0.30 else "GOLD_NOT_ESTABLISHED"
    results = {
        "schema": "paper_e_layer1_v4_results",
        "experiment_id": contract["experiment_id"],
        "contract_sha256": contract_hash,
        "heldout_n": n_heldout,
        "label_counts": label_counts,
        "u_rate_heldout": u_rate,
        "contingency": contingency,
        "co_miss_rate": co_miss,
        "co_alarm_rate": co_alarm,
        "verdict": verdict,
        "labels_frozen_sha256": labels_sha,
        "case_rows": rows,
        "calls": {"model": 0, "judge": 0, "network": 0, "training": 0},
        "boundary": "Descriptive held-out feasibility result only. Not a population rate, OCR result, or harmful-blind-spot claim.",
    }
    (HERE / "V4_RESULTS_v1.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "schema": "paper_e_layer1_v4_receipt",
        "status": verdict,
        "contract_sha256": contract_hash,
        "manifest_sha256": sha256_file(manifest_path),
        "inputs": contract["inputs"],
        "heldout_n": n_heldout,
        "labels_frozen_sha256": labels_sha,
        "calls": {"model": 0, "judge": 0, "network": 0, "training": 0},
        "stop_conditions": contract["stop_conditions"],
    }
    (HERE / "V4_RECEIPT_v1.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = "# Paper E Layer-1 v4 Summary\n\n"
    summary += "- verdict: `%s`\n" % verdict
    summary += "- heldout_n: %d\n" % n_heldout
    summary += "- label_counts: E=%d H=%d U=%d\n" % (label_counts[E], label_counts[H], label_counts[U])
    summary += "- u_rate_heldout: %.6f\n" % u_rate
    summary += "- contingency visible: E=%d H=%d U=%d\n" % (contingency["visible"][E], contingency["visible"][H], contingency["visible"][U])
    summary += "- contingency blind: E=%d H=%d U=%d\n" % (contingency["blind"][E], contingency["blind"][H], contingency["blind"][U])
    summary += "- co_miss_rate: %s\n" % co_miss
    summary += "- co_alarm_rate: %s\n" % co_alarm
    summary += "- calls: 0 model / 0 judge / 0 network / 0 training\n"
    summary += "- boundary: descriptive held-out feasibility only; no population, OCR, or harmful-blind-spot claim.\n"
    (HERE / "V4_SUMMARY_v1.md").write_text(summary, encoding="utf-8")
    print(json.dumps({"verdict": verdict, "u_rate_heldout": u_rate, "label_counts": label_counts}))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("preflight", "heldout"), required=True)
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT))
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--fixtures", default=str(DEFAULT_FIXTURES))
    parser.add_argument("--allow-preflight-overwrite", action="store_true")
    args = parser.parse_args()
    if args.mode == "preflight":
        return run_preflight(Path(args.contract), Path(args.manifest), Path(args.fixtures), args.allow_preflight_overwrite)
    return run_heldout(Path(args.contract), Path(args.manifest), Path(args.fixtures))


if __name__ == "__main__":
    sys.exit(main())
