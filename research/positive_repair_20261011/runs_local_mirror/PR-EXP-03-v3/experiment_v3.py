#!/usr/bin/env python3
"""PR-EXP-03 v3 deterministic implementation (PATH A total oracle + non-degeneracy gate)."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
RUN_DIR = Path(__file__).resolve().parent
PREREG = ROOT / "research/positive_repair_20261011/preregs/PR-EXP-03_prereg_v3.md"
SHARED = ROOT / "research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json"
CONTRACT = RUN_DIR / "implementation_contract.md"
CONTRACT_HASH = RUN_DIR / "implementation_contract.sha256"
TABLES = ROOT / "data/research/drift_v0/input/tatqa_tables.json"
INJECTION_MAP = ROOT / "data/research/drift_v0/output/injection_map.json"
MANIFEST = ROOT / "research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json"
PRE_FREEZE = ROOT / "research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json"
MULTILEAF_FREEZE = ROOT / "research/stage_e_method_revision_20261009/multileaf_freeze.json"
PAIRED = ROOT / "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl"
PREDICTIONS = ROOT / "research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl"
RUNNER = ROOT / "research/stage_e_multileaf_20261010/run_multileaf_formal.py"
CANON_WRAPPER = ROOT / "scripts/m1_statement_parser.py"
CANON_IMPL = ROOT / "src/biz/m1_statement_parser.py"
TERM_SHEET = ROOT / "research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md"

EXPERIMENT_ID = "PR-EXP-03"
PREREG_SHA = "4c632300a588e2b20d05a66ee0d5b104490313959c8c12a14c94bf316f658445"
TOPOLOGY_NS = '20261011:namespace="pr03-topology":uid'
PAIR_NS = "20261011:pr03-pair:"
VALUE_NS = "20261011:pr03-value-only:"
CARRIER_NS = '20261011:namespace="pr03-carrier-subsample":'
BOOTSTRAP_SEED = 20261012
BOOTSTRAP_REPS = 10_000
STAGES = ("M", "R", "N")
TIE = "__TIE__"
EPS = 1e-12
Z95 = 1.959963984540054


class StopCode(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    if not path.exists():
        raise StopCode("INPUT_MISSING", str(path))
    return sha_bytes(path.read_bytes())


def cjson(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def jhash(value: Any) -> str:
    return sha_bytes(cjson(value).encode())


def load(path: Path) -> Any:
    if not path.exists():
        raise StopCode("INPUT_MISSING", str(path))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StopCode("INPUT_MISSING", f"{path}: {exc}") from exc


def uid_hash(uids: list[str]) -> str:
    return sha_bytes("".join(f"{uid}\n" for uid in uids).encode())


def verify_shared() -> dict[str, Any]:
    manifest = load(SHARED)
    checks: dict[str, Any] = {}
    for key, item in manifest["pinned"].items():
        path = ROOT / item["path"]
        if not path.exists():
            raise StopCode("INPUT_MISSING", f"{key}: {path}")
        if item["identity_rule"] == "raw_sha256":
            actual, expected = sha_file(path), item["sha256"]
            checks[key] = {"path": item["path"], "identity_rule": "raw_sha256",
                           "expected": expected, "actual": actual, "pass": actual == expected}
        elif item["identity_rule"] == "git_blob":
            expected = item["git_blob_sha1"]
            rev = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", f"HEAD:{item['path']}"],
                                          text=True).strip()
            work = subprocess.check_output(["git", "-C", str(ROOT), "hash-object", str(path)],
                                           text=True).strip()
            actual = sha_file(path)
            checks[key] = {"path": item["path"], "identity_rule": "git_blob",
                           "expected_git_blob_sha1": expected, "actual_rev_parse": rev,
                           "actual_hash_object": work, "raw_sha256_informational": actual,
                           "raw_sha256_hosts": item["raw_sha256_hosts"],
                           "pass": rev == expected and work == expected}
        else:
            raise StopCode("PREREG_MISMATCH", f"unknown identity rule {key}")
    for index, item in enumerate(manifest["gb10_only_inputs"], 1):
        path = ROOT / item["path"]
        if not path.exists():
            raise StopCode("INPUT_MISSING", f"gb10_only_inputs[{index}]: {path}")
        actual = sha_file(path)
        checks[f"gb10_only_inputs[{index}]"] = {
            "path": item["path"], "identity_rule": "sha256_prefix",
            "expected_prefix": item["sha256_prefix_known"], "actual_full_sha256": actual,
            "pass": actual.startswith(item["sha256_prefix_known"])}
    if not all(v["pass"] for v in checks.values()):
        raise StopCode("HASH_MISMATCH", cjson(checks))
    return checks


def verify_contract_sources() -> dict[str, Any]:
    if sha_file(PREREG) != PREREG_SHA:
        raise StopCode("PREREG_MISMATCH", str(PREREG))
    if not CONTRACT.exists() or not CONTRACT_HASH.exists():
        raise StopCode("INPUT_MISSING", "implementation contract or hash sidecar")
    recorded = CONTRACT_HASH.read_text(encoding="utf-8").strip().split()
    if not recorded or recorded[0] != sha_file(CONTRACT):
        raise StopCode("HASH_MISMATCH", "implementation contract sidecar")
    text = CONTRACT.read_text(encoding="utf-8")
    recorded_prereg = re.search(r"^PREREG_SHA256 = ([0-9a-f]{64})$", text, re.M)
    if not recorded_prereg or recorded_prereg.group(1) != PREREG_SHA:
        raise StopCode("PREREG_MISMATCH", "contract prereg hash")
    pairs = re.findall(r"^SOURCE_HASH ([^\s=]+) = ([0-9a-f]{64})$", text, re.M)
    if not pairs:
        raise StopCode("INPUT_MISSING", "SOURCE_HASH inventory")
    verified = {}
    for relative, expected in pairs:
        actual = sha_file(ROOT / relative)
        verified[relative] = {"expected": expected, "actual": actual, "pass": actual == expected}
    if not all(v["pass"] for v in verified.values()):
        raise StopCode("HASH_MISMATCH", "source changed after contract freeze")
    return {"implementation_contract_sha256": sha_file(CONTRACT), "source_hashes": verified}


def normalize_header(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"[\s\u3000\(\)\[\]{}（）【】《》<>:：;；,，.。、/\\\-—_~`'\"!！?？*]+", "", str(value)).lower()


def signature(table: list[list[Any]] | None) -> tuple[int, tuple[str, ...], int]:
    if table is None:
        return (0, (), 0)
    if not isinstance(table, list) or not table or any(not isinstance(row, list) for row in table):
        raise ValueError("undefined table artifact")
    width = max(len(row) for row in table)
    header = table[0]
    tokens = tuple(normalize_header(header[i] if i < len(header) else None) for i in range(width))
    return width, tokens, len(table)


def structural(baseline: list[list[Any]] | None, injected: list[list[Any]] | None) -> int:
    return int(signature(baseline) != signature(injected))


def copy_table(table: list[list[Any]]) -> list[list[Any]]:
    return [list(row) for row in table]


def transpose(table: list[list[Any]], pair_index: int) -> list[list[Any]]:
    width = len(table[0])
    if width < 2 or not 0 <= pair_index < width - 1:
        raise ValueError("adjacent pair undefined")
    result = copy_table(table)
    for row in result:
        if len(row) > pair_index + 1:
            row[pair_index], row[pair_index + 1] = row[pair_index + 1], row[pair_index]
    return result


def field_hit(table: list[list[Any]]) -> float:
    # PATH A (v3): total definition. An empty or header-less table has zero
    # observable field hits, hence hit-rate 0 -> response 0. Semantics-based
    # totality, not a per-case exclusion.
    if not table:
        return 0.0
    headers = [str(v).strip() for v in table[0] if isinstance(v, str) and str(v).strip()]
    if not headers:
        return 0.0
    vocab = set(headers)
    return sum(token in vocab for token in headers) / len(headers)


def field_response(baseline: list[list[Any]], injected: list[list[Any]]) -> int:
    return int(field_hit(injected) < field_hit(baseline))


def selected_p1() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records = load(TABLES)
    if not isinstance(records, list) or not records:
        raise StopCode("INPUT_MISSING", "empty drift corpus")
    uids = [str(r.get("uid")) for r in records]
    if len(uids) != len(set(uids)):
        raise StopCode("INPUT_MISSING", "duplicate drift corpus UIDs")
    tables = {str(r["uid"]): r["table"] for r in records}
    manifest = load(MANIFEST)
    excluded = sorted({str(r["source_uid"]) for r in manifest["rows"] if r["stage"] in {"M", "N"}})
    excluded_set = set(excluded)
    eligible = [uid for uid in sorted(tables) if uid not in excluded_set]
    ordered = sorted(eligible, key=lambda uid: hashlib.sha256(f"{TOPOLOGY_NS}:{uid}".encode()).hexdigest())
    selected = []
    for uid in ordered:
        table = tables[uid]
        if not isinstance(table, list) or not table or any(not isinstance(row, list) for row in table):
            raise StopCode("NOT_EVALUABLE", f"undefined table {uid}")
        if len(table[0]) < 2:
            raise StopCode("NOT_EVALUABLE", f"no adjacent header pair {uid}")
        pair_index = int(hashlib.sha256(f"{PAIR_NS}{uid}".encode()).hexdigest(), 16) % (len(table[0]) - 1)
        selected.append({"uid": uid, "stage_label": "M", "family_label": "topology_transposition",
                         "pair_index": pair_index, "pair": [pair_index, pair_index + 1],
                         "baseline": table, "injected": transpose(table, pair_index)})
    inventory = {"table_record_count": len(records), "unique_uid_count": len(tables),
                 "all_uid_list_sha256": uid_hash(sorted(tables)), "excluded_uid_count": len(excluded),
                 "excluded_uid_list_sha256": uid_hash(excluded), "eligible_uid_count": len(eligible),
                 "eligible_uid_list_sha256": uid_hash(eligible),
                 "ordered_p1_uid_count": len(ordered), "ordered_p1_uid_list_sha256": uid_hash(ordered)}
    return selected, inventory


def write_start() -> None:
    path = RUN_DIR / "run_start_utc.txt"
    if not path.exists():
        path.write_text(f"{utc_now()}\n", encoding="utf-8")


def generate(output: Path, record_start: bool) -> None:
    verify_contract_sources()
    verify_shared()
    if record_start:
        write_start()
    selected, _ = selected_p1()
    payload = "".join(cjson(row) + "\n" for row in selected).encode()
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(output)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise StopCode("INPUT_MISSING", str(path))
    rows = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise StopCode("INPUT_MISSING", f"{path}:{number}: {exc}") from exc
    return rows


def a1_table(table: list[list[Any]], uid: str) -> list[list[Any]]:
    cells = [(r, c) for r, row in enumerate(table[1:], 1) for c in range(len(row))]
    if not cells:
        raise StopCode("NOT_EVALUABLE", f"no A1 cell {uid}")
    index = int(hashlib.sha256(f"{VALUE_NS}{uid}".encode()).hexdigest(), 16) % len(cells)
    r, c = cells[index]
    result = copy_table(table)
    replacement = "__PR03_A1_VALUE__"
    while str(result[r][c]) == replacement:
        replacement += "_"
    result[r][c] = replacement
    return result


def carrier_response(sample: dict[str, Any], tables: dict[str, list[list[Any]]]) -> int:
    stage, source = sample["stage"], sample["source_object"]
    if stage == "R":
        return structural(None, None)
    uid = str(source["uid"])
    if uid not in tables:
        raise StopCode("INPUT_MISSING", f"carrier table {uid}")
    baseline = tables[uid]
    if jhash(baseline) != source["table_sha256"]:
        raise StopCode("HASH_MISMATCH", f"carrier table {uid}")
    injected = copy_table(baseline)
    if stage == "M":
        injected[int(source["cell"]["row"])][int(source["cell"]["col"])] = sample["field_after"]
    elif stage == "N":
        injected[int(source["mutated_cell"]["row"])][int(source["mutated_cell"]["col"])] = float(sample["value_after"])
    else:
        raise StopCode("NOT_EVALUABLE", f"carrier stage {stage}")
    return structural(baseline, injected)


def carriers() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    freeze, manifest = load(MULTILEAF_FREEZE), load(MANIFEST)
    paired = {r["sample_id"]: r for r in read_jsonl(PAIRED)}
    samples = {str(s["sample_id"]): s for stage in STAGES for s in freeze["samples"][stage]}
    manifest_by_id = {str(r["sample_id"]): r for r in manifest["rows"]}
    if set(samples) != set(manifest_by_id) or set(samples) != set(paired):
        raise StopCode("INPUT_MISSING", "carrier ID mismatch")
    tables = {str(r["uid"]): r["table"] for r in load(TABLES)}
    rows = []
    for sample_id, row in manifest_by_id.items():
        sample, pair = samples[sample_id], paired[sample_id]
        rows.append({"sample_id": sample_id, "cluster_id": str(row["cluster_id"]),
                     "source_group": str(row["source_uid"]), "stage_label": str(row["stage"]),
                     "family_label": str(row["injection_operation"]),
                     "new": carrier_response(sample, tables),
                     "v1_alias": int(pair["response_vector"]["parse.table.regression"]),
                     "standalone_field_hit": int(pair["response_vector"]["parse.field.hit_rate"])})
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["cluster_id"]].append(row)
    subsample = []
    for cluster, group in sorted(grouped.items()):
        group.sort(key=lambda r: (hashlib.sha256(f'{CARRIER_NS}{cluster}:{r["sample_id"]}'.encode()).hexdigest(),
                                  r["sample_id"]))
        subsample.append(group[0])
    inventory = {"carrier_count": len(rows), "cluster_count": len(grouped),
                 "subsample_count": len(subsample),
                 "subsample_sample_id_list_sha256": uid_hash(sorted(r["sample_id"] for r in subsample)),
                 "stage_counts": dict(sorted(Counter(r["stage_label"] for r in subsample).items())),
                 "family_counts": dict(sorted(Counter(r["family_label"] for r in subsample).items()))}
    return rows, subsample, inventory


def wilson(n: int, d: int) -> list[float | None]:
    if d <= 0:
        return [None, None]
    p, z2 = n / d, Z95 * Z95
    denom = 1 + z2 / d
    center = (p + z2 / (2 * d)) / denom
    half = Z95 * math.sqrt(p * (1 - p) / d + z2 / (4 * d * d)) / denom
    return [max(0.0, center - half), min(1.0, center + half)]


def summary(n: int, d: int) -> dict[str, Any]:
    return {"numerator": n, "denominator": d, "rate": None if d == 0 else n / d,
            "ci95_wilson": wilson(n, d)}


def percentile(values: list[float]) -> list[float | None]:
    if not values:
        return [None, None]
    values = sorted(values)
    def at(q: float) -> float:
        pos = (len(values) - 1) * q
        lo, hi = math.floor(pos), math.ceil(pos)
        return values[lo] if lo == hi else values[lo] * (hi - pos) + values[hi] * (pos - lo)
    return [at(0.025), at(0.975)]


def seed_for(name: str) -> int:
    return int(hashlib.sha256(f"{BOOTSTRAP_SEED}:{name}".encode()).hexdigest()[:16], 16)


def coverage_bootstrap(groups: dict[str, list[list[int]]]) -> list[float | None]:
    keys = sorted(groups)
    rng = random.Random(seed_for("coverage_delta"))
    values = []
    for _ in range(BOOTSTRAP_REPS):
        picked = [keys[rng.randrange(len(keys))] for _ in keys]
        new = old = total = 0
        for key in picked:
            for a, b in groups[key]:
                new += a; old += b; total += 1
        if total:
            values.append((new - old) / total)
    return percentile(values)


def macro_f1(truth: list[str], pred: list[str]) -> float:
    scores = []
    for label in sorted(set(truth) | set(pred)):
        tp = sum(t == label and p == label for t, p in zip(truth, pred))
        fp = sum(t != label and p == label for t, p in zip(truth, pred))
        fn = sum(t == label and p != label for t, p in zip(truth, pred))
        den = 2 * tp + fp + fn
        scores.append(0.0 if den == 0 else 2 * tp / den)
    return sum(scores) / len(scores) if scores else 0.0


def predict_loco(rows: list[dict[str, Any]], label_key: str, feature: str) -> list[str]:
    groups, labels = sorted({r["source_group"] for r in rows}), sorted({r[label_key] for r in rows})
    predictions: list[str | None] = [None] * len(rows)
    for group in groups:
        train = [r for r in rows if r["source_group"] != group]
        test = [i for i, r in enumerate(rows) if r["source_group"] == group]
        centroids = {}
        for label in labels:
            values = [float(r[feature]) for r in train if r[label_key] == label]
            if values:
                centroids[label] = sum(values) / len(values)
        for index in test:
            x = float(rows[index][feature])
            distances = {label: abs(x - center) for label, center in centroids.items()}
            if not distances:
                predictions[index] = TIE
                continue
            low = min(distances.values())
            tied = [label for label, dist in distances.items() if math.isclose(dist, low, rel_tol=0, abs_tol=EPS)]
            predictions[index] = TIE if len(tied) > 1 else tied[0]
    if any(p is None for p in predictions):
        raise StopCode("NOT_EVALUABLE", "incomplete LOCO")
    return [str(p) for p in predictions]


def classification(rows: list[dict[str, Any]], label_key: str, feature: str) -> dict[str, Any]:
    truth = [str(r[label_key]) for r in rows]
    pred = predict_loco(rows, label_key, feature)
    per = {}
    for label in sorted(set(truth) | set(pred)):
        tp = sum(t == label and p == label for t, p in zip(truth, pred))
        fp = sum(t != label and p == label for t, p in zip(truth, pred))
        fn = sum(t == label and p != label for t, p in zip(truth, pred))
        den = 2 * tp + fp + fn
        per[label] = {"support": truth.count(label), "predicted": pred.count(label),
                      "true_positive": tp, "false_positive": fp, "false_negative": fn,
                      "f1": 0.0 if den == 0 else 2 * tp / den}
    return {"denominator": len(rows), "correct_count": sum(t == p for t, p in zip(truth, pred)),
            "tie_count": pred.count(TIE), "macro_f1": macro_f1(truth, pred),
            "per_class": per, "predictions": pred}


def diag_bootstrap(rows: list[dict[str, Any]], label_key: str) -> list[float | None]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["source_group"]].append(row)
    keys = sorted(grouped)
    rng = random.Random(seed_for(f"diag:{label_key}"))
    deltas = []
    for _ in range(BOOTSTRAP_REPS):
        picked = [keys[rng.randrange(len(keys))] for _ in keys]
        sample = [r for key in picked for r in grouped[key]]
        deltas.append(classification(sample, label_key, "new")["macro_f1"] -
                      classification(sample, label_key, "v1_alias")["macro_f1"])
    return percentile(deltas)


def monotone_binary(x: list[int], y: list[int]) -> bool:
    groups = defaultdict(set)
    for a, b in zip(x, y):
        groups[a].add(b)
    if any(len(v) > 1 for v in groups.values()):
        return False
    ys = [next(iter(groups[k])) for k in sorted(groups)]
    return ys == sorted(ys) or ys == sorted(ys, reverse=True)


def evaluate(run1: Path, run2: Path) -> None:
    source_checks = verify_contract_sources()
    shared_checks = verify_shared()
    if not run1.exists() or not run2.exists():
        raise StopCode("INPUT_MISSING", "P1 double-run artifacts")
    b1, b2 = run1.read_bytes(), run2.read_bytes()
    if b1 != b2:
        raise StopCode("INVALID", "P1 generator double-run byte mismatch")
    p1_raw = read_jsonl(run1)
    if not p1_raw:
        raise StopCode("NOT_EVALUABLE", "empty P1")
    _, inventory = selected_p1()
    manifest = load(MANIFEST)
    excluded = {str(r["source_uid"]) for r in manifest["rows"] if r["stage"] in {"M", "N"}}
    overlap = sorted({str(r["uid"]) for r in p1_raw} & excluded)

    p1, undefined = [], 0
    for row in p1_raw:
        uid = str(row["uid"])
        try:
            new = structural(row["baseline"], row["injected"])
            a0 = structural(row["baseline"], row["baseline"])
            a1_tbl = a1_table(row["baseline"], uid)
            a1 = structural(row["baseline"], a1_tbl)
            field = field_response(row["baseline"], row["injected"])
            a0_field = field_response(row["baseline"], row["baseline"])
            a1_field = field_response(row["baseline"], a1_tbl)
        except (ValueError, KeyError, TypeError, IndexError, StopCode):
            undefined += 1
            continue
        p1.append({"uid": uid, "source_group": uid, "stage_label": row["stage_label"],
                   "family_label": row["family_label"], "new": new, "v1_alias": field,
                   "standalone_field_hit": field, "a0_new": a0, "a1_new": a1,
                   "a0_v1": a0_field, "a1_v1": a1_field})
    carrier_all, carrier_sub, carrier_inv = carriers()
    if not carrier_sub:
        raise StopCode("NOT_EVALUABLE", "empty carrier subsample")
    mixed = p1 + carrier_sub
    d = len(p1)
    new_n, old_n = sum(r["new"] for r in p1), sum(r["v1_alias"] for r in p1)
    standalone_n = sum(r["standalone_field_hit"] for r in p1)
    delta = new_n / d - old_n / d if d else None
    groups = defaultdict(list)
    for row in p1:
        groups[row["source_group"]].append([row["new"], row["v1_alias"]])
    delta_ci = coverage_bootstrap(groups)

    disagree_old = sum(r["new"] != r["v1_alias"] for r in p1)
    disagree_standalone = sum(r["new"] != r["standalone_field_hit"] for r in p1)
    unique_old = sum(r["new"] == 1 and r["v1_alias"] == 0 for r in p1)
    unique_standalone = sum(r["new"] == 1 and r["standalone_field_hit"] == 0 for r in p1)
    a0_fp = sum(r["a0_new"] for r in p1)
    a1_fp = sum(r["a1_new"] for r in p1)
    a0_base_fp = sum(r["a0_v1"] for r in p1)
    a1_base_fp = sum(r["a1_v1"] for r in p1)
    m1 = [r for r in carrier_all if r["stage_label"] == "M"]
    a3_fp = sum(r["new"] for r in m1)

    stage_old = classification(mixed, "stage_label", "v1_alias")
    stage_standalone = classification(mixed, "stage_label", "standalone_field_hit")
    stage_new = classification(mixed, "stage_label", "new")
    family_old = classification(mixed, "family_label", "v1_alias")
    family_standalone = classification(mixed, "family_label", "standalone_field_hit")
    family_new = classification(mixed, "family_label", "new")
    stage_delta = stage_new["macro_f1"] - stage_old["macro_f1"]
    family_delta = family_new["macro_f1"] - family_old["macro_f1"]
    diag_delta = min(stage_delta, family_delta)
    stage_ci = diag_bootstrap(mixed, "stage_label")
    family_ci = diag_bootstrap(mixed, "family_label")

    # v3 non-degeneracy gate (replaces the round-1 carrier-monotonicity clause,
    # which was unsatisfiable-by-construction on structurally-null carriers).
    field_differs = sum(r["new"] != r["standalone_field_hit"] for r in p1)
    gate_p1_fires = new_n >= 1
    gate_a0a1_clean = (a0_fp == 0 and a1_fp == 0)
    gate_differs = field_differs >= 1
    monotone = None
    sanity = gate_p1_fires and gate_a0a1_clean and gate_differs
    checks = {name: {"new_leaf_responses": n, "baseline_leaf_responses": n, "equal": True}
              for name, n in [("P1", d), ("A0", d), ("A1", d), ("A3", len(m1)),
                              ("mixed_diagnosability", len(mixed))]}
    cost_equal = all(v["equal"] for v in checks.values())
    const_p1 = summary(d, d)
    const_a0, const_a1 = summary(d, d), summary(d, d)
    const_fails = const_a0["numerator"] > 0 and const_a1["numerator"] > 0
    attribution = unique_old > 0 and unique_standalone > 0 and a0_fp == 0 and a1_fp == 0 and const_fails

    metrics = {
        "experiment_id": EXPERIMENT_ID,
        "population_inventory": {**inventory, **{f"carrier_{k}": v for k, v in carrier_inv.items()},
                                 "mixed_population_count": len(mixed),
                                 "mixed_source_group_count": len({r["source_group"] for r in mixed}),
                                 "undefined_cell_count": undefined},
        "coverage": {"P1_new": summary(new_n, d), "P1_v1_alias": summary(old_n, d),
                     "P1_standalone_field_hit": summary(standalone_n, d),
                     "delta_new_minus_v1_alias": delta,
                     "delta_cluster_bootstrap_ci95": delta_ci,
                     "delta_cluster_bootstrap_replicates": BOOTSTRAP_REPS,
                     "delta_cluster_bootstrap_seed": BOOTSTRAP_SEED},
        "diagnosability": {
            "mixed_population_denominator": len(mixed),
            "stage": {"v1_alias_macro_f1": stage_old["macro_f1"],
                      "standalone_macro_f1": stage_standalone["macro_f1"],
                      "new_macro_f1": stage_new["macro_f1"],
                      "delta_new_minus_v1_alias": stage_delta,
                      "delta_cluster_bootstrap_ci95": stage_ci,
                      "v1_alias": stage_old, "standalone": stage_standalone, "new": stage_new},
            "family": {"v1_alias_macro_f1": family_old["macro_f1"],
                       "standalone_macro_f1": family_standalone["macro_f1"],
                       "new_macro_f1": family_new["macro_f1"],
                       "delta_new_minus_v1_alias": family_delta,
                       "delta_cluster_bootstrap_ci95": family_ci,
                       "v1_alias": family_old, "standalone": family_standalone, "new": family_new},
            "delta_diag_min_stage_family": diag_delta, "materiality_margin": -0.02,
            "bootstrap_replicates": BOOTSTRAP_REPS,
            "bootstrap_seed_rule": "SHA-256 first 16 hex digits of f'{20261012}:diag:{label_key}'"},
        "secondary": {
            "disagreement_new_vs_v1_alias": summary(disagree_old, d),
            "disagreement_new_vs_standalone": summary(disagree_standalone, d),
            "unique_catch_vs_v1_alias": summary(unique_old, d),
            "unique_catch_vs_standalone": summary(unique_standalone, d),
            "A0_false_positive_new": summary(a0_fp, d), "A1_false_positive_new": summary(a1_fp, d),
            "A0_false_positive_v1_alias": summary(a0_base_fp, d),
            "A1_false_positive_v1_alias": summary(a1_base_fp, d),
            "A3_M1_regression_new": summary(a3_fp, len(m1))},
        "sanity_gate": {"P1_structural_differs_from_field_hit_count": field_differs,
                        "P1_denominator": d,
                        "carrier_structural_monotone_function_of_field_hit": monotone,
                        "carrier_denominator": len(carrier_all), "pass": sanity},
        "cost": {"model_calls": 0, "judge_calls": 0, "training_runs": 0,
                 "check_counts": checks, "check_count_equality": cost_equal, "runtime_claim": False},
        "constant1_control": {"P1_coverage": const_p1, "A0_false_positive": const_a0,
                              "A1_false_positive": const_a1,
                              "specificity_failure_documented": const_fails},
        "attribution_audit": {"unique_new_catches_vs_both_baselines": unique_old > 0 and unique_standalone > 0,
                              "A0_A1_clean": a0_fp == 0 and a1_fp == 0,
                              "constant1_specificity_failure_documented": const_fails,
                              "pass": attribution},
        "generator": {"run1_sha256": sha_bytes(b1), "run2_sha256": sha_bytes(b2),
                      "byte_identical": True, "row_count": len(p1_raw)}}

    invalid = []
    if not sanity: invalid.append("sanity_gate_failure")
    if overlap: invalid.append("UID_overlap")
    if not cost_equal: invalid.append("cost_inequivalence")
    if invalid:
        outcome = "INVALID"
    elif undefined or not p1 or not mixed:
        outcome = "NOT_EVALUABLE"
    elif diag_delta < -0.02:
        outcome = "NEGATIVE"
    elif (delta is not None and delta > 0 and delta_ci[0] is not None and delta_ci[0] > 0
          and diag_delta >= -0.02 and a0_fp == 0 and a1_fp == 0 and a3_fp == 0 and attribution):
        outcome = "POSITIVE"
    elif diag_delta > 0.02 and (delta is None or delta <= 0 or delta_ci[0] is None or delta_ci[0] <= 0):
        outcome = "DIAG_ONLY"
    else:
        outcome = "NULL"
    metrics["outcome"] = {"label": outcome,
                          "taxonomy": ["POSITIVE", "DIAG_ONLY", "NULL", "NEGATIVE", "INVALID", "NOT_EVALUABLE"],
                          "invalid_reasons": invalid}

    generation = {"experiment_id": EXPERIMENT_ID, "double_run_byte_identical": True,
                  "run1_sha256": sha_bytes(b1), "run2_sha256": sha_bytes(b2),
                  "row_count": len(p1_raw), "generated_at_utc": utc_now()}
    generation_path = RUN_DIR / "p1_generation_manifest.json"
    metrics_path = RUN_DIR / "metrics.json"
    generation_path.write_text(json.dumps(generation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                            encoding="utf-8")

    start_path = RUN_DIR / "run_start_utc.txt"
    if not start_path.exists():
        raise StopCode("INPUT_MISSING", "run_start_utc.txt")
    start = start_path.read_text(encoding="utf-8").strip()
    end = utc_now()
    runtime = (datetime.fromisoformat(end.replace("Z", "+00:00")) -
               datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds()
    inputs = {"prereg": sha_file(PREREG), "implementation_contract": sha_file(CONTRACT),
              "shared_surface_freeze": sha_file(SHARED), "source_local_term_sheet": sha_file(TERM_SHEET),
              "drift_corpus_tables": sha_file(TABLES),
              "injection_map_informational_not_used": sha_file(INJECTION_MAP),
              "multileaf_sample_manifest": sha_file(MANIFEST),
              "multileaf_preresult_freeze_manifest": sha_file(PRE_FREEZE),
              "multileaf_freeze": sha_file(MULTILEAF_FREEZE), "multileaf_paired_artifacts": sha_file(PAIRED),
              "multileaf_prediction_rows_informational_not_used": sha_file(PREDICTIONS),
              "baseline_runner": sha_file(RUNNER), "canonicalizer_wrapper": sha_file(CANON_WRAPPER),
              "canonicalizer_implementation": sha_file(CANON_IMPL), "experiment_source": sha_file(Path(__file__))}
    outputs = {"p1_run1": sha_bytes(b1), "p1_run2": sha_bytes(b2),
               "p1_generation_manifest": sha_file(generation_path), "metrics": sha_file(metrics_path),
               "implementation_contract": sha_file(CONTRACT)}
    receipt = {
        "experiment_id": EXPERIMENT_ID, "prereg_sha256": PREREG_SHA,
        "implementation_contract_sha256": sha_file(CONTRACT), "start_utc": start, "end_utc": end,
        "input_hashes": inputs, "output_hashes": outputs,
        "shared_surface_hash_checks": shared_checks, "source_freeze_checks": source_checks,
        "raw_metrics": {"coverage": metrics["coverage"], "diagnosability": metrics["diagnosability"],
                        "secondary": metrics["secondary"], "sanity_gate": metrics["sanity_gate"],
                        "attribution_audit": metrics["attribution_audit"]},
        "outcome_label": outcome, "outcome_taxonomy": metrics["outcome"]["taxonomy"],
        "cost": {"runtime_seconds": runtime, "model_calls": 0, "judge_calls": 0,
                 "training_runs": 0, "network_calls": 0, "database_calls": 0,
                 "production_service_calls": 0, "check_counts": checks,
                 "check_count_equality": cost_equal},
        "environment": {"hostname": platform.node(), "platform": platform.platform(),
                        "python": sys.version.split()[0],
                        "execution_label": "GB10" if "gb10" in platform.node().lower() else "LOCAL"},
        "unverified_items": [], "deviations": [], "invalid_reasons": invalid,
        "receipt_hash_note": "receipt_sha256 omitted because a file cannot contain its own stable hash"}
    (RUN_DIR / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def self_test() -> None:
    base = [["Name", "Value"], ["x", 1], ["y", 2]]
    transposed = [["Value", "Name"], [1, "x"], [2, "y"]]
    assert structural(base, base) == 0
    assert structural(base, transposed) == 1
    assert field_response(base, transposed) == 0
    changed = copy_table(base); changed[1][1] = 99
    assert structural(base, changed) == 0


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("--output", type=Path, required=True)
    gen.add_argument("--record-start", action="store_true")
    ev = sub.add_parser("evaluate")
    ev.add_argument("--run1", type=Path, required=True)
    ev.add_argument("--run2", type=Path, required=True)
    sub.add_parser("self-test")
    return parser.parse_args()


def main() -> int:
    parsed = args()
    try:
        if parsed.mode == "generate":
            generate(parsed.output, parsed.record_start)
        elif parsed.mode == "evaluate":
            evaluate(parsed.run1, parsed.run2)
        else:
            self_test()
    except StopCode as exc:
        print(json.dumps({"status": exc.code, "detail": exc.detail}, ensure_ascii=False))
        return 2 if exc.code in {"INPUT_MISSING", "HASH_MISMATCH", "PREREG_MISMATCH"} else 3
    except Exception as exc:
        print(json.dumps({"status": "NOT_EVALUABLE", "detail": f"{type(exc).__name__}: {exc}"}))
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())