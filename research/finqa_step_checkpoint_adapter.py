"""Build the pre-registered FinQA step-level fault-injection corpus (zero model, zero connect).

This is a corpus builder, not an evaluator. It turns the audited FinQA `qa.steps`
decomposition (measured: 10 960 steps, every step exactly `(op, arg1, arg2, res)`) into a
deterministic step-level checkpoint benchmark bound to an authoritative layer assignment
produced by `research/phase1a_split_assign.py`.

Why the corpus is frozen before any scorer exists: choosing a detector after seeing
detection numbers is how a benchmark gets tuned into a result. So this module fixes the
fault families, their admissibility conditions and the selection rule now, and reports
`measurement_status = CORPUS_ONLY_SCORER_NOT_PREREGISTERED`. It publishes no detection or
localization rate, because no scorer has been pre-registered yet.

Fault families (both total over the measured step schema, both format-explicit):

  res_scale -- multiply the numeric `res` by 11/10 in exact decimal arithmetic, preserving
      sign, a trailing '%' suffix and decimal places (+1 place); inadmissible when `res` is
      non-numeric or numerically zero (0 * 1.1 = 0 is not a fault).
  arg_swap -- exchange `arg1` and `arg2`; admissible only for non-commutative op families
      and only when the two args differ. Swapping args of add/multiply/sum/average/max/min
      yields a semantically identical step, which would be an undetectable "fault" and would
      silently corrupt any detection metric.

Exactly one fault per multi-step example. Single-step examples have no intermediate step, so
they are counted and reported but never injected; the step-level denominator is multi-step
only. Examples admitting neither family are reported as `no_admissible_fault`, never forced.

Governance and provenance are enforced, not promised: the layer artifact's
`layers_manifest_sha256` is recomputed with the contract digest and compared; every input
file must appear in the staging sha256 manifest with a matching digest; the summary artifact
carries no wall-clock field, so a re-run is byte-identical; a connect attempt raises.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import sys
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.phase1a_data_contract import _digest_object  # noqa: E402
from research.phase1a_split_assign import (  # noqa: E402  reuse, never reimplement
    FINQA_SOURCES,
    SplitError,
    bucket,
    load_sha256_manifest,
    read_verified,
    stable_sample_id,
)

CONTRACT_VERSION = "finqa-step-checkpoint-corpus-v1"
SPLIT_CONTRACT_VERSION = "phase1a-split-assignment-v1"
MEASUREMENT_STATUS = "CORPUS_ONLY_SCORER_NOT_PREREGISTERED"
INDEX_SALT = "finqa-step-ckpt-v1:step-index"
FAMILY_SALT = "finqa-step-ckpt-v1:fault-family"
SCALE = Decimal("1.1")
COMMUTATIVE_FAMILIES = frozenset({"add", "multiply", "sum", "average", "max", "min"})
NUM_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)$")
PCT_RE = re.compile(r"^([+-]?(?:\d+\.?\d*|\.\d+))%$")
OP_RE = re.compile(r"^(?P<family>[A-Za-z_]+?)(?P<variant>\d*)-(?P<position>\d+)$")
HEX40 = set("0123456789abcdef")
STEP_FIELDS = ("op", "arg1", "arg2", "res")


class AdapterError(ValueError):
    """Fail-closed rejection with a machine-readable code."""

    def __init__(self, code: str, **detail: object) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def install_network_guard() -> None:
    """Any connect attempt raises; the observed port set stays empty."""

    def _blocked(*_a: object, **_k: object) -> object:
        raise AdapterError("zero_connect_violation")

    socket.socket.connect = _blocked  # type: ignore[method-assign]
    socket.create_connection = _blocked  # type: ignore[assignment]


def op_family(op: str) -> str:
    """`divide1-2` -> `divide`; tolerates the plain form by stripping trailing digits."""
    match = OP_RE.match(op)
    base = match.group("family") + match.group("variant") if match else op.split("-")[0]
    return re.sub(r"\d+$", "", base) or "unknown"


def parse_numeric(value: str) -> tuple[Decimal, str, int] | None:
    """Return (magnitude, suffix, decimal_places) for a numeric or percent literal."""
    text = value.strip()
    suffix = ""
    pct = PCT_RE.match(text)
    if pct:
        text, suffix = pct.group(1), "%"
    elif not NUM_RE.match(text):
        return None
    sign = -1 if text[:1] == "-" else 1
    body = text.lstrip("+-")
    places = len(body.split(".")[1]) if "." in body else 0
    try:
        magnitude = Decimal(body) * sign
    except Exception:  # pragma: no cover - regex already constrains the shape
        return None
    return magnitude, suffix, places


def scale_res(res: str) -> str | None:
    """Exact x1.1 with preserved sign, '%' suffix and decimal places (+1 place)."""
    parsed = parse_numeric(res)
    if parsed is None:
        return None
    magnitude, suffix, places = parsed
    if magnitude == 0:
        return None
    scaled = (magnitude * SCALE).quantize(
        Decimal(1).scaleb(-(places + 1)), rounding=ROUND_HALF_EVEN
    )
    return f"{scaled}{suffix}"


def admissible_families(step: dict[str, object]) -> tuple[bool, bool]:
    """(res_scale admissible, arg_swap admissible) for one step."""
    res = step.get("res")
    res_ok = isinstance(res, str) and scale_res(res) is not None
    family = op_family(str(step.get("op", "")))
    arg1, arg2 = step.get("arg1"), step.get("arg2")
    swap_ok = (
        family not in COMMUTATIVE_FAMILIES
        and isinstance(arg1, str)
        and isinstance(arg2, str)
        and arg1 != arg2
    )
    return res_ok, swap_ok


def apply_fault(steps: list[dict[str, object]], fault: dict[str, object]) -> list[dict[str, object]]:
    """Public, deterministic mutant derivation; scorers must reuse this, not reimplement it."""
    index = int(str(fault["step_index"]))
    if not 0 <= index < len(steps):
        raise AdapterError("fault_step_index_out_of_range", index=index)
    out = [dict(s) for s in steps]
    family = str(fault["family"])
    if family == "res_scale":
        out[index]["res"] = fault["after"]
    elif family == "arg_swap":
        before = fault["before"]
        if not isinstance(before, list) or len(before) != 2:
            raise AdapterError("invalid_arg_swap_before")
        out[index]["arg1"], out[index]["arg2"] = before[1], before[0]
    else:
        raise AdapterError("unknown_fault_family", family=family)
    return out


def plan_fault(seed: int, sample_id: str, steps: list[dict[str, object]]) -> dict[str, object] | None:
    """Pre-registered selection: one fault per multi-step example.

    The starting index comes from a salted bucket and the family preference from an
    independent salted parity bit. Admissibility is a property of a single step, so the scan
    walks the remaining indices in deterministic wrap-around order and takes the first step
    that admits a family. Without that scan an example would be dropped merely because the
    bucketed step happened to be commutative with a non-numeric result, which would make the
    corpus silently smaller than its own spec ("one fault per multi-step example").
    Returns None only when no step of the example admits either family.
    """
    total = len(steps)
    start = bucket(INDEX_SALT + ":" + str(seed), sample_id, total)
    prefer_swap = bucket(FAMILY_SALT + ":" + str(seed), sample_id, 2) == 1
    for offset in range(total):
        index = (start + offset) % total
        step = steps[index]
        res_ok, swap_ok = admissible_families(step)
        if not res_ok and not swap_ok:
            continue
        if prefer_swap and swap_ok:
            order = ("arg_swap", "res_scale")
        elif res_ok:
            order = ("res_scale", "arg_swap")
        else:
            order = ("arg_swap",)
        for family in order:
            if family == "res_scale" and res_ok:
                before = str(step["res"])
                return {
                    "family": "res_scale",
                    "step_index": index,
                    "field": "res",
                    "op_family": op_family(str(step.get("op", ""))),
                    "before": before,
                    "after": scale_res(before),
                }
            if family == "arg_swap" and swap_ok:
                return {
                    "family": "arg_swap",
                    "step_index": index,
                    "field": "arg1+arg2",
                    "op_family": op_family(str(step.get("op", ""))),
                    "before": [str(step["arg1"]), str(step["arg2"])],
                    "after": [str(step["arg2"]), str(step["arg1"])],
                }
    return None


def role_layer_of(partition: str) -> str:
    return "proposal_train" if partition.startswith("proposal_train.") else partition


def load_layers(path: Path) -> dict[str, object]:
    """Load a split artifact and prove its layers were not hand-edited."""
    artifact = json.loads(path.read_text(encoding="utf-8"))
    if artifact.get("contract_version") != SPLIT_CONTRACT_VERSION:
        raise AdapterError(
            "invalid_layers_contract_version", got=str(artifact.get("contract_version"))
        )
    if artifact.get("namespace") != "finqa":
        raise AdapterError("layers_namespace_not_finqa", got=str(artifact.get("namespace")))
    layers = artifact.get("layers")
    if not isinstance(layers, dict):
        raise AdapterError("invalid_layers_object")
    declared = artifact.get("layers_manifest_sha256")
    recomputed = _digest_object(layers)
    if declared != recomputed:
        raise AdapterError(
            "layers_manifest_sha256_mismatch", declared=str(declared), recomputed=recomputed
        )
    return artifact


def iter_layer_rows(layers: dict[str, object]):
    flat = (
        ("proposal_train.train", layers["proposal_train"]["train"]),
        ("proposal_train.dev", layers["proposal_train"]["dev"]),
        ("gate_validation", layers["gate_validation"]),
        ("sealed_test", layers["sealed_test"]),
        ("future_replay", layers["future_replay"]),
    )
    for partition, rows in flat:
        for row in rows:
            yield partition, row


def load_examples(
    root: Path,
    manifest: dict[str, str],
    dataset_id: str,
    dataset_revision: str,
    hashes: dict[str, str],
) -> dict[str, dict[str, object]]:
    """sample_id -> example; validates the uniform step schema on every step of every example."""
    out: dict[str, dict[str, object]] = {}
    for rel, split in FINQA_SOURCES:
        entries = json.loads(read_verified(root, rel, manifest))
        hashes[rel] = manifest[rel]
        if not isinstance(entries, list):
            raise AdapterError("invalid_source_json", path=rel)
        for entry in entries:
            if not isinstance(entry, dict):
                raise AdapterError("invalid_example_object", path=rel)
            example_id = entry.get("id")
            if not isinstance(example_id, str) or not example_id.strip():
                raise AdapterError("missing_example_id", path=rel)
            qa = entry.get("qa")
            steps = qa.get("steps") if isinstance(qa, dict) else None
            if not isinstance(steps, list) or not steps:
                raise AdapterError("missing_steps", example_id=example_id)
            for index, step in enumerate(steps):
                if not isinstance(step, dict) or set(step) != set(STEP_FIELDS):
                    raise AdapterError("invalid_step_schema", example_id=example_id, index=index)
                if any(not isinstance(step.get(key), str) for key in STEP_FIELDS):
                    raise AdapterError("non_string_step_field", example_id=example_id, index=index)
            sample_id = stable_sample_id(dataset_id, dataset_revision, example_id)
            if sample_id in out:
                raise AdapterError("duplicate_sample_id", example_id=example_id)
            out[sample_id] = {
                "example_id": example_id,
                "source_split": split,
                "steps": steps,
            }
    if not out:
        raise AdapterError("empty_example_index")
    return out


def _verify_mutant(steps: list[dict], fault: dict, index: int) -> None:
    mutant = apply_fault(steps, fault)
    if mutant == steps:
        raise AdapterError("fault_is_a_noop", step_index=index)
    changed = [i for i, (a, b) in enumerate(zip(steps, mutant)) if a != b]
    if changed != [index]:
        raise AdapterError("fault_changed_unexpected_steps", changed=changed, expected=index)
    field = str(fault["field"])
    keys = {k for k in STEP_FIELDS if steps[index].get(k) != mutant[index].get(k)}
    expected_keys = {"res"} if field == "res" else {"arg1", "arg2"}
    if keys != expected_keys:
        raise AdapterError("fault_field_mismatch", changed=sorted(keys), expected=sorted(expected_keys))


def build(*, root: Path, manifest_path: Path, layers_path: Path, seed: int) -> tuple[dict, str]:
    manifest = load_sha256_manifest(manifest_path)
    layers_artifact = load_layers(layers_path)
    dataset_id = str(layers_artifact["dataset_id"])
    dataset_revision = str(layers_artifact["dataset_revision"])
    hashes: dict[str, str] = {}
    examples = load_examples(root, manifest, dataset_id, dataset_revision, hashes)
    layers_bytes = layers_path.read_bytes()
    records: list[dict] = []
    seen: set[str] = set()
    by_partition: dict[str, dict[str, int]] = {}
    by_step_count: dict[str, int] = {}
    by_op_family: dict[str, int] = {}
    by_fault_family: dict[str, int] = {}
    layer_rows = single_step = inadmissible = steps_in_injected = 0
    for partition, row in iter_layer_rows(layers_artifact["layers"]):  # type: ignore[arg-type]
        layer_rows += 1
        sample_id = str(row["sample_id"])
        example = examples.get(sample_id)
        if example is None:
            raise AdapterError("layer_sample_not_in_source", partition=partition)
        stats = by_partition.setdefault(
            partition, {"injected": 0, "single_step_excluded": 0, "no_admissible_fault": 0}
        )
        steps = example["steps"]
        assert isinstance(steps, list)
        if len(steps) < 2:
            single_step += 1
            stats["single_step_excluded"] += 1
            continue
        fault = plan_fault(seed, sample_id, steps)
        if fault is None:
            inadmissible += 1
            stats["no_admissible_fault"] += 1
            continue
        _verify_mutant(steps, fault, int(str(fault["step_index"])))
        if sample_id in seen:
            raise AdapterError("duplicate_corpus_sample", partition=partition)
        seen.add(sample_id)
        families = [op_family(str(s["op"])) for s in steps]
        for name in families:
            by_op_family[name] = by_op_family.get(name, 0) + 1
        by_step_count[str(len(steps))] = by_step_count.get(str(len(steps)), 0) + 1
        fault_family = str(fault["family"])
        by_fault_family[fault_family] = by_fault_family.get(fault_family, 0) + 1
        steps_in_injected += len(steps)
        stats["injected"] += 1
        records.append({
            "sample_id": sample_id,
            "uid": row["uid"],
            "lineage_root_id": row["lineage_root_id"],
            "independence_cluster": row["independence_cluster"],
            "partition": partition,
            "role_layer": role_layer_of(partition),
            "example_id": example["example_id"],
            "source_split": example["source_split"],
            "n_steps": len(steps),
            "op_families": families,
            "steps_clean": [{k: s[k] for k in STEP_FIELDS} for s in steps],
            "fault": fault,
        })
    records.sort(key=lambda r: str(r["sample_id"]))
    corpus = "".join(
        json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records
    )
    summary = {
        "contract_version": CONTRACT_VERSION,
        "namespace": "finqa",
        "dataset_id": dataset_id,
        "dataset_revision": dataset_revision,
        "measurement_status": MEASUREMENT_STATUS,
        "seed": seed,
        "fault_spec": {
            "families": ["res_scale", "arg_swap"],
            "index_salt": INDEX_SALT,
            "family_salt": FAMILY_SALT,
            "res_scale_factor": "1.1",
            "commutative_families_excluded_from_arg_swap": sorted(COMMUTATIVE_FAMILIES),
            "faults_per_example": 1,
            "index_selection": "salted_bucket_then_deterministic_wraparound_scan",
            "admissibility_scope": "per_candidate_step",
            "step_level_denominator": "multi_step_only",
            "single_step_examples": "counted_never_injected",
            "scorer": "NOT_PREREGISTERED",
        },
        "inputs": {
            "source_sha256": dict(sorted(hashes.items())),
            "layers_artifact_sha256": hashlib.sha256(layers_bytes).hexdigest(),
            "layers_manifest_sha256": layers_artifact["layers_manifest_sha256"],
            "layers_m_universe": layers_artifact["m_universe"],
            "layers_status": layers_artifact["status"],
            "layers_reasons": layers_artifact["reasons"],
        },
        "counts": {
            "layer_rows": layer_rows,
            "injected": len(records),
            "single_step_excluded": single_step,
            "no_admissible_fault": inadmissible,
            "steps_in_injected_examples": steps_in_injected,
            "corpus_records": len(records),
            "corpus_sha256": hashlib.sha256(corpus.encode("utf-8")).hexdigest(),
        },
        "stratifications": {
            "by_partition": {k: by_partition[k] for k in sorted(by_partition)},
            "by_step_count": {k: by_step_count[k] for k in sorted(by_step_count)},
            "by_op_family": {k: by_op_family[k] for k in sorted(by_op_family)},
            "by_fault_family": {k: by_fault_family[k] for k in sorted(by_fault_family)},
        },
        "observed_ports": [],
    }
    return summary, corpus


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--staging-root", required=True, type=Path)
    ap.add_argument("--sha256-manifest", required=True, type=Path)
    ap.add_argument("--layers", required=True, type=Path, help="phase1a_split_assign artifact")
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out", required=True, type=Path, help="summary artifact (small, quotable)")
    ap.add_argument("--out-corpus", required=True, type=Path, help="JSONL corpus (stays out of Git)")
    args = ap.parse_args()
    commit = args.commit.strip()
    if len(commit) != 40 or not set(commit) <= HEX40:
        raise AdapterError("invalid_adapter_commit", commit=commit)
    install_network_guard()
    kwargs = {
        "root": args.staging_root,
        "manifest_path": args.sha256_manifest,
        "layers_path": args.layers,
        "seed": args.seed,
    }
    first_summary, first_corpus = build(**kwargs)
    second_summary, second_corpus = build(**kwargs)
    if json.dumps(first_summary, sort_keys=True) != json.dumps(second_summary, sort_keys=True):
        raise AdapterError("nondeterministic_summary")
    if first_corpus != second_corpus:
        raise AdapterError("nondeterministic_corpus")
    first_summary["commit"] = commit
    args.out_corpus.write_text(first_corpus, encoding="utf-8", newline="\n")
    args.out.write_text(
        json.dumps(first_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    counts = first_summary["counts"]
    print(
        "wrote " + str(args.out) + " status=" + str(first_summary["measurement_status"])
        + " injected=" + str(counts["injected"])
        + " single_step_excluded=" + str(counts["single_step_excluded"])
        + " no_admissible_fault=" + str(counts["no_admissible_fault"])
    )
    print("corpus_sha256=" + str(counts["corpus_sha256"]) + " records=" + str(counts["corpus_records"]))
    print("layers_manifest_sha256=" + str(first_summary["inputs"]["layers_manifest_sha256"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AdapterError, SplitError) as exc:
        print(
            "ADAPTER_FAIL " + exc.code + " " + json.dumps(exc.detail, sort_keys=True, default=str),
            file=sys.stderr,
        )
        raise SystemExit(2) from None
