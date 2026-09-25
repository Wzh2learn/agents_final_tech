"""Score the frozen FinQA step-level checkpoint corpus under pre-registration v1.

Zero model, zero connect, deterministic. This module implements
docs/experiments/2026-09-25_step_checkpoint_scorer_preregistration.md clause-for-clause and
records that file's sha256 in its own output, so a result can never be silently detached from
the spec that produced it. Rule changes require a new pre-registration version, not an edit
here: every semantic choice below cites its clause (R2/R3/R4/R5).

Honesty constraints that are enforced in code, not in prose:
* an unparseable argument, an unknown op family, a zero divisor, a tied comparison or a
  malformed `res` yields the explicit state UNEVALUABLE -- never silently true or false (R2/R3);
* metrics are defined only on the `clean_faithful` subset, and the excluded portion is reported
  as its own bucket with its own count, so no denominator can quietly shrink (R5);
* `interpretation_fidelity` is a first-class output. A low value is a finding about our
  reconstructed op semantics, not a reason to change the convention and rerun (R4/R8);
* both localization metrics are always emitted together (R5.4).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import sys
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.finqa_step_checkpoint_adapter import (  # noqa: E402
    AdapterError,
    apply_fault,
    op_family,
)
from research.phase1a_data_contract import _digest_object  # noqa: E402

SCORE_CONTRACT_VERSION = "finqa-step-checkpoint-score-v2"
PREREG_VERSION = "v2"
READING_DIRECT = "mantissa_direct"
READING_SCALED = "mantissa_scaled"
READINGS = (READING_DIRECT, READING_SCALED)
REL_TOL = Decimal("1e-9")  # R4: written once, never tuned after a run
NUM_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)$")
PCT_RE = re.compile(r"^([+-]?(?:\d+\.?\d*|\.\d+))%$")
CONST_RE = re.compile(r"^const_(m?)(\d+)$")
REF_RE = re.compile(r"^#(\d+)$")
COMMUTATIVE = frozenset({"add", "multiply", "sum", "average", "max", "min"})
BOOL_RES = frozenset({"yes", "no"})
HEX40 = set("0123456789abcdef")


class ScorerError(ValueError):
    """Fail-closed rejection with a machine-readable code."""

    def __init__(self, code: str, **detail: object) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def install_network_guard() -> None:
    def _blocked(*_a: object, **_k: object) -> object:
        raise ScorerError("zero_connect_violation")

    socket.socket.connect = _blocked  # type: ignore[method-assign]
    socket.create_connection = _blocked  # type: ignore[assignment]


def _decimal(text: str) -> Decimal | None:
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    return value if value.is_finite() else None


def res_form(res: str) -> str:
    """R6 stratification dimension: num / pct / bool / other."""
    if NUM_RE.match(res):
        return "num"
    if PCT_RE.match(res):
        return "pct"
    if res in BOOL_RES:
        return "bool"
    return "other"


def res_as_arg(res: str) -> Decimal | None:
    """R4: a percent `res` is consumed downstream as mantissa / 100; bools and malformed are None."""
    if NUM_RE.match(res):
        return _decimal(res)
    match = PCT_RE.match(res)
    if match:
        mantissa = _decimal(match.group(1))
        return None if mantissa is None else mantissa / Decimal(100)
    return None


def resolve_arg(token: str, steps: list[dict], cache: dict[int, Decimal | None]) -> Decimal | None:
    """R2 grammar, exhaustive over the measured vocabulary. None means UNEVALUABLE."""
    if NUM_RE.match(token):
        return _decimal(token)
    match = PCT_RE.match(token)
    if match:
        mantissa = _decimal(match.group(1))
        return None if mantissa is None else mantissa / Decimal(100)
    const = CONST_RE.match(token)
    if const:
        value = Decimal(const.group(2))
        return -value if const.group(1) else value
    ref = REF_RE.match(token)
    if ref:
        index = int(ref.group(1))
        if not 0 <= index < len(steps):
            return None
        if index not in cache:
            cache[index] = res_as_arg(str(steps[index].get("res", "")))
        return cache[index]
    # "none" and free text such as "net sales": never guessed, never zero (R2).
    return None


def compute(family: str, a1: Decimal, a2: Decimal) -> Decimal | str | None:
    """R3 semantics. None means UNEVALUABLE; a str result is a compare_larger boolean."""
    if family == "add" or family == "sum":
        return a1 + a2
    if family == "minus":
        return a1 - a2
    if family == "multiply":
        return a1 * a2
    if family == "divide":
        if a2 == 0:
            return None
        with localcontext() as ctx:
            ctx.prec = 50
            return a1 / a2
    if family == "average":
        with localcontext() as ctx:
            ctx.prec = 50
            return (a1 + a2) / Decimal(2)
    if family == "max":
        return max(a1, a2)
    if family == "min":
        return min(a1, a2)
    if family == "exp":
        try:
            value = a1 ** a2
        except (InvalidOperation, OverflowError, ValueError):
            return None
        return value if value.is_finite() else None
    if family == "compare_larger":
        if a1 == a2:
            return None  # R3: ties are not adjudicated
        return "yes" if a1 > a2 else "no"
    return None  # unknown family: UNEVALUABLE, never guessed


OP_PARTS_RE = re.compile(r"^(?P<family>[A-Za-z_]+?)(?P<variant>\d*)-(?P<position>\d+)$")


def op_variant(op: str) -> str:
    """R6 stratification dimension: the variant digit, which R3 deliberately does not semanticize."""
    match = OP_PARTS_RE.match(op)
    return match.group("variant") if match else ""


def _close(a: Decimal, b: Decimal) -> bool:
    if a == b:
        return True
    scale = max(abs(a), abs(b))
    if scale == 0:
        return False
    return abs(a - b) <= REL_TOL * scale


def step_verdict(steps: list[dict], index: int, reading: str) -> tuple[str, str]:
    """One step -> ("match" | "mismatch" | "unevaluable", detail). R2/R3/R4 plus V2-1.

    `reading` selects the percent convention and, by construction, affects only pct-form
    results: num-form comparison is reading-independent, so the two readings cannot diverge
    anywhere except the stratum where v1 measured the divergence.
    """
    if reading not in READINGS:
        raise ScorerError("unknown_percent_reading", reading=reading)
    step = steps[index]
    op = str(step.get("op", ""))
    family = op_family(op)
    res = str(step.get("res", ""))
    cache: dict[int, Decimal | None] = {}
    a1 = resolve_arg(str(step.get("arg1", "")), steps, cache)
    a2 = resolve_arg(str(step.get("arg2", "")), steps, cache)
    if a1 is None or a2 is None:
        return "unevaluable", "arg_unresolvable"
    value = compute(family, a1, a2)
    if value is None:
        return "unevaluable", "undefined_" + family
    if isinstance(value, str):
        if res not in BOOL_RES:
            return "unevaluable", "res_form_" + res_form(res)
        return ("match", "") if value == res else ("mismatch", "bool")
    form = res_form(res)
    if form in ("bool", "other"):
        return "unevaluable", "res_form_" + form
    if form == "pct":
        match = PCT_RE.match(res)
        expected = _decimal(match.group(1)) if match else None
        if expected is not None and reading == READING_SCALED:
            assert not isinstance(value, str)
            value = value * Decimal(100)
    else:
        expected = _decimal(res)
    if expected is None:
        return "unevaluable", "res_unparsable"
    return ("match", "") if _close(value, expected) else ("mismatch", "numeric")


def run_steps(steps: list[dict], reading: str) -> dict:
    verdicts = [step_verdict(steps, i, reading) for i in range(len(steps))]
    return {
        "verdicts": verdicts,
        "flagged": [i for i, (state, _) in enumerate(verdicts) if state == "mismatch"],
        "unevaluable": [i for i, (state, _) in enumerate(verdicts) if state == "unevaluable"],
    }


def score_record(record: dict, reading: str) -> dict:
    """R5: classify one corpus record; the mutant always comes from the adapter's apply_fault."""
    clean = record["steps_clean"]
    fault = record["fault"]
    mutant = apply_fault(clean, fault)
    clean_run = run_steps(clean, reading)
    mutant_run = run_steps(mutant, reading)
    injected = int(fault["step_index"])
    faithful = not clean_run["flagged"] and not clean_run["unevaluable"]
    detected = bool(mutant_run["flagged"])
    return {
        "sample_id": record["sample_id"],
        "partition": record["partition"],
        "n_steps": len(clean),
        "clean_faithful": faithful,
        "clean_flagged": bool(clean_run["flagged"]),
        "steps_unevaluable": len(clean_run["unevaluable"]),
        "steps_mismatch": len(clean_run["flagged"]),
        "detected": detected,
        "exact_localization": mutant_run["flagged"] == [injected],
        "inclusive_localization": injected in mutant_run["flagged"],
        # V2-1(2): the injected step is the earliest altered one, so downstream mismatches
        # are consequences of #N propagation rather than independent detections.
        "root_cause_localization": bool(mutant_run["flagged"])
        and min(mutant_run["flagged"]) == injected,
        "reading": reading,
        "fault_family": fault["family"],
        "injected_op_family": op_family(str(clean[injected].get("op", ""))),
        "injected_variant": op_variant(str(clean[injected].get("op", ""))),
        "step_op_families": [op_family(str(s.get("op", ""))) for s in clean],
        "step_variants": [op_variant(str(s.get("op", ""))) for s in clean],
        "step_res_forms": [res_form(str(s.get("res", ""))) for s in clean],
        "step_verdict_states": [state for state, _ in clean_run["verdicts"]],
    }


def _bump(table: dict, dimension: str, key: str, fields: dict[str, int]) -> None:
    slot = table.setdefault(dimension, {}).setdefault(str(key), {})
    for name, delta in fields.items():
        slot[name] = slot.get(name, 0) + delta


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 8) if denominator else None


def aggregate(scored: list[dict]) -> dict:
    totals = {
        "records": len(scored),
        "clean_faithful": 0,
        "clean_unfaithful": 0,
        "clean_false_flag": 0,
        "detected": 0,
        "exact_localization": 0,
        "inclusive_localization": 0,
        "root_cause_localization": 0,
        "steps_total": 0,
        "steps_match": 0,
        "steps_mismatch": 0,
        "steps_unevaluable": 0,
    }
    step_strata: dict[str, dict] = {}
    example_strata: dict[str, dict] = {}
    for row in scored:
        faithful = row["clean_faithful"]
        totals["clean_faithful"] += int(faithful)
        totals["clean_unfaithful"] += int(not faithful)
        totals["clean_false_flag"] += int(bool(faithful and row["clean_flagged"]))
        if faithful:
            totals["detected"] += int(row["detected"])
            totals["exact_localization"] += int(row["exact_localization"])
            totals["inclusive_localization"] += int(row["inclusive_localization"])
            totals["root_cause_localization"] += int(row["root_cause_localization"])
        for i in range(row["n_steps"]):
            state = row["step_verdict_states"][i]
            totals["steps_total"] += 1
            totals["steps_" + state] += 1
            fields = {"steps": 1, state: 1}
            _bump(step_strata, "op_family", row["step_op_families"][i], fields)
            _bump(step_strata, "variant", row["step_variants"][i] or "none", fields)
            _bump(step_strata, "res_form", row["step_res_forms"][i], fields)
        example_fields = {
            "clean_faithful": int(faithful),
            "clean_unfaithful": int(not faithful),
        }
        if faithful:
            example_fields.update({
                "detected": int(row["detected"]),
                "exact_localization": int(row["exact_localization"]),
                "inclusive_localization": int(row["inclusive_localization"]),
                "root_cause_localization": int(row["root_cause_localization"]),
            })
        _bump(example_strata, "fault_family", row["fault_family"], example_fields)
        _bump(example_strata, "partition", row["partition"], example_fields)
        _bump(example_strata, "n_steps", row["n_steps"], example_fields)
        _bump(example_strata, "injected_op_family", row["injected_op_family"], example_fields)
        _bump(example_strata, "injected_variant", row["injected_variant"] or "none", example_fields)
    faithful_n = totals["clean_faithful"]
    detected_n = totals["detected"]
    metrics = {
        "interpretation_fidelity": _ratio(faithful_n, faithful_n + totals["clean_unfaithful"]),
        "fault_detection_rate": _ratio(detected_n, faithful_n),
        "exact_localization_rate": _ratio(totals["exact_localization"], detected_n),
        "inclusive_localization_rate": _ratio(totals["inclusive_localization"], detected_n),
        "root_cause_localization_rate": _ratio(totals["root_cause_localization"], detected_n),
        "clean_false_flag_rate": _ratio(totals["clean_false_flag"], faithful_n),
    }
    return {
        "totals": totals,
        "metrics": metrics,
        "metric_denominators": {
            "interpretation_fidelity": faithful_n + totals["clean_unfaithful"],
            "fault_detection_rate": faithful_n,
            "exact_localization_rate": detected_n,
            "inclusive_localization_rate": detected_n,
            "root_cause_localization_rate": detected_n,
            "clean_false_flag_rate": faithful_n,
        },
        "step_strata": {d: {k: step_strata[d][k] for k in sorted(step_strata[d])}
                        for d in sorted(step_strata)},
        "example_strata": {d: {k: example_strata[d][k] for k in sorted(example_strata[d])}
                           for d in sorted(example_strata)},
    }


def verify_bindings(corpus_raw: bytes, corpus_sha: str, summary: dict, layers: dict) -> set[str]:
    """R1: corpus hash, summary agreement, layer digest recomputation, and row containment."""
    actual = hashlib.sha256(corpus_raw).hexdigest()
    if actual != corpus_sha:
        raise ScorerError("corpus_sha256_mismatch", expected=corpus_sha, actual=actual)
    counts = summary.get("counts") or {}
    if counts.get("corpus_sha256") != actual:
        raise ScorerError("summary_corpus_sha_mismatch")
    digest = _digest_object(layers.get("layers"))
    declared = (summary.get("inputs") or {}).get("layers_manifest_sha256")
    if declared != digest:
        raise ScorerError("layers_manifest_sha256_mismatch", declared=str(declared), recomputed=digest)
    assigned: set[str] = set()
    flat = layers["layers"]
    for rows in (flat["proposal_train"]["train"], flat["proposal_train"]["dev"],
                 flat["gate_validation"], flat["sealed_test"], flat["future_replay"]):
        for row in rows:
            assigned.add(str(row["sample_id"]))
    return assigned


def score_corpus(
    corpus_raw: bytes, assigned: set[str], expected_records: int, reading: str
) -> list[dict]:
    scored: list[dict] = []
    for line_number, line in enumerate(corpus_raw.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        if str(record.get("sample_id")) not in assigned:
            raise ScorerError("corpus_row_not_in_layers", line=line_number)
        for key in ("steps_clean", "fault", "partition"):
            if key not in record:
                raise ScorerError("invalid_corpus_record", line=line_number, missing=key)
        scored.append(score_record(record, reading))
    if len(scored) != expected_records:
        raise ScorerError("corpus_record_count_mismatch", got=len(scored), expected=expected_records)
    return scored


def _assert_reproduces_v1(block: dict, v1: dict) -> None:
    """V2-4: under mantissa_direct, v2 must reproduce every v1 number or fail closed.

    Without this guard a "spec version bump" could silently redefine v1's semantics, and the
    two published results would no longer be comparable.
    """
    sections = (("counts", "totals"), ("metrics", "metrics"),
                ("metric_denominators", "metric_denominators"))
    for v1_key, v2_key in sections:
        expected = v1.get(v1_key) or {}
        actual = block.get(v2_key) or {}
        for key in sorted(expected):
            if actual.get(key) != expected[key]:
                raise ScorerError("v1_reproduction_mismatch", section=v1_key, key=key,
                                  v1=expected[key], v2=actual.get(key))
    if (v1.get("step_strata") or {}) != (block.get("step_strata") or {}):
        raise ScorerError("v1_reproduction_mismatch", section="step_strata")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", required=True, type=Path)
    ap.add_argument("--corpus-sha256", required=True)
    ap.add_argument("--summary", required=True, type=Path, help="adapter corpus summary artifact")
    ap.add_argument("--layers", required=True, type=Path, help="phase1a_split_assign artifact")
    ap.add_argument("--prereg", required=True, type=Path, help="frozen pre-registration file")
    ap.add_argument("--v1-results-doc", required=True, type=Path,
                    help="v1 results markdown; hashed into the artifact per V2-4")
    ap.add_argument("--v1-score", required=True, type=Path,
                    help="v1 score artifact; mantissa_direct must reproduce it")
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    commit = args.commit.strip()
    if len(commit) != 40 or not set(commit) <= HEX40:
        raise ScorerError("invalid_scorer_commit", commit=commit)
    install_network_guard()
    corpus_raw = args.corpus.read_bytes()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    layers = json.loads(args.layers.read_text(encoding="utf-8"))
    assigned = verify_bindings(corpus_raw, args.corpus_sha256.strip(), summary, layers)
    expected = int((summary.get("counts") or {}).get("corpus_records", -1))
    v1_score = json.loads(args.v1_score.read_text(encoding="utf-8"))

    def _run() -> dict:
        return {
            reading: aggregate(score_corpus(corpus_raw, assigned, expected, reading))
            for reading in READINGS
        }

    first = _run()
    second = _run()
    if json.dumps(first, sort_keys=True) != json.dumps(second, sort_keys=True):
        raise ScorerError("nondeterministic_scoring")
    _assert_reproduces_v1(first[READING_DIRECT], v1_score)
    prereg_raw = args.prereg.read_bytes()
    artifact = {
        "contract_version": SCORE_CONTRACT_VERSION,
        "prereg": {
            "path": args.prereg.name,
            "sha256": hashlib.sha256(prereg_raw).hexdigest(),
            "version": PREREG_VERSION,
            "relative_tolerance": str(REL_TOL),
        },
        "readings": list(READINGS),
        "v1_anchors": {
            "results_doc_sha256": hashlib.sha256(args.v1_results_doc.read_bytes()).hexdigest(),
            "score_artifact_sha256": hashlib.sha256(args.v1_score.read_bytes()).hexdigest(),
            "reproduced_under": READING_DIRECT,
            "reproduction_checked_sections": [
                "counts", "metrics", "metric_denominators", "step_strata"],
        },
        "bindings": {
            "corpus_sha256": hashlib.sha256(corpus_raw).hexdigest(),
            "corpus_bytes": len(corpus_raw),
            "summary_sha256": hashlib.sha256(args.summary.read_bytes()).hexdigest(),
            "layers_sha256": hashlib.sha256(args.layers.read_bytes()).hexdigest(),
            "layers_manifest_sha256": (summary.get("inputs") or {}).get("layers_manifest_sha256"),
            "layers_m_universe": (summary.get("inputs") or {}).get("layers_m_universe"),
        },
        "by_reading": {
            reading: {
                "counts": first[reading]["totals"],
                "metrics": first[reading]["metrics"],
                "metric_denominators": first[reading]["metric_denominators"],
                "step_strata": first[reading]["step_strata"],
                "example_strata": first[reading]["example_strata"],
            }
            for reading in READINGS
        },
        "commit": commit,
        "observed_ports": [],
    }
    args.out.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    for reading in READINGS:
        block = artifact["by_reading"][reading]
        totals = block["counts"]
        print(
            "[" + reading + "] wrote " + str(args.out)
            + " records=" + str(totals["records"])
            + " clean_faithful=" + str(totals["clean_faithful"])
            + " clean_unfaithful=" + str(totals["clean_unfaithful"])
            + " detected=" + str(totals["detected"])
        )
        print("[" + reading + "] metrics=" + json.dumps(block["metrics"], sort_keys=True))
        print("[" + reading + "] steps=" + json.dumps(
            {k: v for k, v in totals.items() if k.startswith("steps_")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ScorerError, AdapterError) as exc:
        print(
            "SCORER_FAIL " + exc.code + " " + json.dumps(exc.detail, sort_keys=True, default=str),
            file=sys.stderr,
        )
        raise SystemExit(2) from None
