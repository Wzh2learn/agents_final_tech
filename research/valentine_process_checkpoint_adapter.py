"""Extract a gold-free Valentine process/checkpoint view from D-C staging.

This adapter is an evidence builder, not a labeler or evaluator. It reads only
source/target headers, the process trajectory, and the audit-trail tool-call
state. It never opens ground_truth.json and never emits the embedded
ground_truth/final_evaluation fields from <pair>_full.json. Correctness remains
NOT_RUN until an independent Q3 review is completed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.phase1a_data_contract import lineage_uid
from research.valentine_q3_review_package import (
    APPROVED_PAIRS,
    DATA_PREFIX,
    PackageBuildError,
    _load_sha256_manifest,
    _sha256_file,
    _sample_id,
    _sha256_bytes,
    _stable_json,
)

CONTRACT_VERSION = "valentine-process-checkpoint-adapter-v1"
DATASET_ID = "valentine_nyc"
READ_FILES = ("source_table.csv", "target_table.csv", "_full.json", "_trajectory.json")
PRESENCE_ONLY_FILES = ("ground_truth.json", "_result.json")
EXPECTED_INVALID_ACTION_REFERENCES = {
    ("City_Government__DSNY_Districts_With_Disposal_Vendor_Assignments", 12, "record_match", "call_c4f11200e31c4c269217b8dc"): "mgp_curb_pri_boro",
    ("City_Government__DSNY_Districts_With_Disposal_Vendor_Assignments", 13, "revoke_match", "call_59ac6c3556084cfea42c037f"): "mgp_curb_pri_boro",
    ("City_Government__DSNY_Districts_With_Disposal_Vendor_Assignments", 31, "batch_record_match", "call_5e32f59bddca46e18a95c413"): "mgp_curb_pri_boro",
}
ANALYSIS_VARIANTS = ("quarantine-primary", "pair-invalid-sensitivity")
ACTION_EVENTS = {
    "record_match": "record_candidate",
    "batch_record_match": "record_candidate",
    "revoke_match": "revoke_candidate",
    "finalize_all_matches": "finalize",
}
FORBIDDEN_OUTPUT_KEYS = frozenset({"ground_truth", "final_evaluation", "gold", "matches", "ambiguous_scenarios", "false_positive_scenarios"})
FORBIDDEN_OUTPUT_MARKERS = ("ground_truth", "final_evaluation", "ambiguous_scenarios", "false_positive_scenarios")


class AdapterError(PackageBuildError):
    """Fail-closed rejection with a machine-readable code."""


def _pair_file_name(pair: str, suffix: str) -> str:
    return f"{pair}_{suffix}.json"


def _expected_pair_files(pair: str) -> set[str]:
    return {
        "source_table.csv",
        "target_table.csv",
        "ground_truth.json",
        _pair_file_name(pair, "full"),
        _pair_file_name(pair, "result"),
        _pair_file_name(pair, "trajectory"),
    }


def _assert_manifest_scope(rows: dict[str, str]) -> None:
    expected = {
        f"{DATA_PREFIX}{pair}/{name}"
        for pair in APPROVED_PAIRS
        for name in _expected_pair_files(pair)
    }
    actual = {path for path in rows if path.startswith(DATA_PREFIX)}
    if actual != expected:
        raise AdapterError(
            "input_manifest_scope_mismatch",
            missing=sorted(expected - actual),
            extra=sorted(actual - expected),
        )


def _validate_input_tree(staging_root: Path) -> list[Path]:
    data_root = staging_root / "valentine" / "experiments" / "data"
    if not data_root.is_dir() or data_root.is_symlink():
        raise AdapterError("missing_valentine_data_root", path=str(data_root))
    entries = list(data_root.iterdir())
    bad_root = sorted(item.name for item in entries if not item.is_dir() or item.is_symlink())
    if bad_root:
        raise AdapterError("unexpected_data_root_entry", entries=bad_root)
    actual_pairs = {item.name for item in entries}
    expected_pairs = set(APPROVED_PAIRS)
    if actual_pairs != expected_pairs:
        raise AdapterError(
            "pair_directory_allowlist_mismatch",
            missing=sorted(expected_pairs - actual_pairs),
            extra=sorted(actual_pairs - expected_pairs),
        )
    for pair in APPROVED_PAIRS:
        pair_dir = data_root / pair
        items = list(pair_dir.iterdir())
        bad = sorted(item.name for item in items if not item.is_file() or item.is_symlink())
        if bad:
            raise AdapterError("unexpected_pair_entry_type", pair=pair, entries=bad)
        names = {item.name for item in items}
        expected = _expected_pair_files(pair)
        if names != expected:
            raise AdapterError(
                "pair_file_allowlist_mismatch",
                pair=pair,
                missing=sorted(expected - names),
                extra=sorted(names - expected),
            )
    return [data_root / pair for pair in APPROVED_PAIRS]


def _validate_output_dir(out_dir: Path, staging_root: Path) -> None:
    if not out_dir.is_absolute():
        raise AdapterError("output_path_not_absolute", path=str(out_dir))
    if out_dir.is_symlink():
        raise AdapterError("output_path_is_symlink", path=str(out_dir))
    resolved = out_dir.resolve(strict=False)
    temp_root = Path(tempfile.gettempdir()).resolve()
    if resolved == temp_root or not resolved.is_relative_to(temp_root):
        raise AdapterError("output_path_outside_temp", path=str(resolved), temp_root=str(temp_root))
    for label, anchor in (("staging", staging_root.resolve()), ("repo", REPO.resolve())):
        if resolved == anchor or resolved.is_relative_to(anchor) or anchor.is_relative_to(resolved):
            raise AdapterError("output_path_conflicts_with_input", kind=label, path=str(resolved))
    if out_dir.exists():
        if not out_dir.is_dir() or out_dir.is_symlink():
            raise AdapterError("output_path_not_directory", path=str(out_dir))
        entries = list(out_dir.iterdir())
        if entries:
            raise AdapterError(
                "output_dir_not_empty",
                entries=sorted(item.name for item in entries),
                has_nested_directory=any(item.is_dir() for item in entries),
            )
        return
    if not out_dir.parent.is_dir() or out_dir.parent.is_symlink():
        raise AdapterError("output_parent_invalid", path=str(out_dir.parent))
    out_dir.mkdir()


def _assert_read_hash(path: Path, rows: dict[str, str], staging_root: Path) -> None:
    relpath = path.relative_to(staging_root).as_posix()
    expected = rows.get(relpath)
    actual = _sha256_file(path)
    if expected is None or expected != actual:
        raise AdapterError("sha256_manifest_mismatch", path=relpath, expected=expected, actual=actual)


def _read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header = next(csv.reader(handle), None)
    if not header or any(not isinstance(value, str) or not value for value in header):
        raise AdapterError("invalid_csv_header", path=str(path))
    if len(set(header)) != len(header):
        raise AdapterError("duplicate_source_header", path=str(path))
    return header


def _named_values(value: object, key: str) -> list[object]:
    found: list[object] = []
    if isinstance(value, dict):
        for name, child in value.items():
            if name == key:
                found.append(child)
            found.extend(_named_values(child, key))
    elif isinstance(value, list):
        for child in value:
            found.extend(_named_values(child, key))
    return found


def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for child in value:
            out.extend(_strings(child))
        return out
    return []


def _safe_call_view(
    call: object,
    source_headers: set[str],
    target_headers: set[str],
    *,
    pair: str,
    turn: int,
    event_index: int,
) -> dict[str, object]:
    if not isinstance(call, dict) or set(call) != {"id", "name", "args"}:
        raise AdapterError("invalid_tool_call_shape")
    args = call["args"]
    if not isinstance(args, dict):
        raise AdapterError("invalid_tool_call_args")
    source = sorted(set(_strings(_named_values(args, "source_column")) + _strings(_named_values(args, "source_columns"))))
    target = sorted(set(_strings(_named_values(args, "target_column")) + _strings(_named_values(args, "target_columns"))))
    invalid_source = sorted(value for value in source if value not in source_headers)
    valid_source = sorted(value for value in source if value in source_headers)
    unknown_target = [value for value in target if value not in target_headers]
    name = str(call["name"])
    call_id = str(call["id"])
    for value in invalid_source:
        key = (pair, turn, name, call_id)
        expected = EXPECTED_INVALID_ACTION_REFERENCES.get(key)
        if expected != value:
            raise AdapterError(
                "unexpected_invalid_action_reference",
                pair=pair,
                turn=turn,
                event_index=event_index,
                tool_name=name,
                call_id=call_id,
                expected=expected,
                actual=value,
            )
    if len(invalid_source) > 1:
        raise AdapterError("multiple_invalid_action_references_in_call", values=len(invalid_source))
    confidence = args.get("confidence")
    if confidence is not None and (not isinstance(confidence, (int, float)) or not math.isfinite(confidence)):
        raise AdapterError("invalid_tool_call_confidence")
    return {
        "tool_name": name,
        "call_id": call_id,
        "event_kind": ACTION_EVENTS.get(name, "process_tool"),
        "source_columns": valid_source,
        "invalid_source_references": invalid_source,
        "target_columns": target,
        "unknown_target_count": len(unknown_target),
        "confidence": confidence,
        "reasoning_present": bool(_named_values(args, "reasoning") or _named_values(args, "reason")),
        "transformation_present": bool(_named_values(args, "transformation_code") or _named_values(args, "transformation_type")),
    }

def _safe_state_view(state: object) -> dict[str, object]:
    if not isinstance(state, dict):
        raise AdapterError("invalid_audit_state")
    allowed = {"content", "reasoning_content", "tool_calls"}
    if set(state) != allowed:
        raise AdapterError("invalid_audit_state_keys", keys=sorted(state))
    calls = state.get("tool_calls")
    if not isinstance(calls, list) or any(not isinstance(call, dict) for call in calls):
        raise AdapterError("invalid_audit_tool_calls")
    return {"tool_call_count": len(calls)}


def _assert_no_forbidden_output(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_OUTPUT_KEYS:
                raise AdapterError("forbidden_output_key", key=str(key))
            _assert_no_forbidden_output(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_forbidden_output(child)
    elif isinstance(value, str):
        lower = value.lower()
        if any(marker in lower for marker in FORBIDDEN_OUTPUT_MARKERS):
            raise AdapterError("forbidden_output_marker")


def build(
    staging_root: Path,
    dataset_revision: str,
    out_dir: Path,
    analysis_variant: str = "quarantine-primary",
) -> dict[str, object]:
    if not isinstance(dataset_revision, str) or not dataset_revision.strip():
        raise AdapterError("missing_dataset_revision")
    if analysis_variant not in ANALYSIS_VARIANTS:
        raise AdapterError("invalid_analysis_variant", value=analysis_variant)
    manifest_path = staging_root / "sha256_manifest.txt"
    rows = _load_sha256_manifest(manifest_path)
    _assert_manifest_scope(rows)
    pair_dirs = _validate_input_tree(staging_root)
    _validate_output_dir(out_dir, staging_root)

    events: list[dict[str, object]] = []
    quarantine_events: list[dict[str, object]] = []
    pair_summaries: list[dict[str, object]] = []
    input_files_read: list[str] = []
    invalid_pairs: set[str] = set()
    for pair_dir in pair_dirs:
        pair = pair_dir.name
        for name in ("source_table.csv", "target_table.csv", _pair_file_name(pair, "full"), _pair_file_name(pair, "trajectory")):
            _assert_read_hash(pair_dir / name, rows, staging_root)
        source_headers = _read_header(pair_dir / "source_table.csv")
        target_headers = _read_header(pair_dir / "target_table.csv")
        if len(set(source_headers)) != len(source_headers):
            raise AdapterError("duplicate_source_header", pair=pair)
        source_set, target_set = set(source_headers), set(target_headers)
        full = json.loads((pair_dir / _pair_file_name(pair, "full")).read_text(encoding="utf-8"))
        trajectory = json.loads((pair_dir / _pair_file_name(pair, "trajectory")).read_text(encoding="utf-8"))
        input_files_read.extend([
            f"{DATA_PREFIX}{pair}/source_table.csv",
            f"{DATA_PREFIX}{pair}/target_table.csv",
            f"{DATA_PREFIX}{pair}/{_pair_file_name(pair, 'full')}",
            f"{DATA_PREFIX}{pair}/{_pair_file_name(pair, 'trajectory')}",
        ])
        audit = full.get("audit_trail")
        if not isinstance(audit, list) or not audit:
            raise AdapterError("missing_audit_trail", pair=pair)
        turns = [row.get("turn") for row in audit]
        if any(type(turn) is not int for turn in turns) or any(a >= b for a, b in zip(turns, turns[1:])):
            raise AdapterError("invalid_audit_turn_sequence", pair=pair)
        if len(set(turns)) != len(turns):
            raise AdapterError("duplicate_audit_turn", pair=pair)
        trajectory_log = ((trajectory.get("metadata") or {}).get("trajectory_log"))
        if not isinstance(trajectory_log, list):
            raise AdapterError("missing_trajectory_log", pair=pair)

        pair_source_seen: set[str] = set()
        pair_target_seen: set[str] = set()
        pair_events: list[dict[str, object]] = []
        pair_quarantine: list[dict[str, object]] = []
        for row in audit:
            if not isinstance(row, dict):
                raise AdapterError("invalid_audit_row", pair=pair)
            raw_state = row.get("agent_a_raw")
            final_state = row.get("final")
            _safe_state_view(raw_state)
            _safe_state_view(final_state)
            raw_calls = raw_state["tool_calls"]
            final_calls = final_state["tool_calls"]
            for call_index, call in enumerate(final_calls):
                view = _safe_call_view(
                    call,
                    source_set,
                    target_set,
                    pair=pair,
                    turn=int(row["turn"]),
                    event_index=call_index,
                )
                invalid_refs = list(view["invalid_source_references"])
                for invalid_ref in invalid_refs:
                    quarantine_id = _sha256_bytes(_stable_json({
                        "pair": pair,
                        "turn": row["turn"],
                        "call_index": call_index,
                        "tool_name": view["tool_name"],
                        "call_id": view["call_id"],
                        "invalid_source_reference": invalid_ref,
                    }).encode("utf-8"))
                    pair_quarantine.append({
                        "quarantine_id": quarantine_id,
                        "dataset_id": DATASET_ID,
                        "dataset_revision": dataset_revision,
                        "pair_id": pair,
                        "lineage_uid": lineage_uid(DATASET_ID, dataset_revision, pair),
                        "turn": row["turn"],
                        "event_index": call_index,
                        "tool_name": view["tool_name"],
                        "call_id": view["call_id"],
                        "invalid_source_reference": invalid_ref,
                        "reason": "approved_reference_level_quarantine",
                        "paper_result": False,
                    })
                    invalid_pairs.add(pair)
                source_columns = list(view["source_columns"])
                target_columns = list(view["target_columns"])
                pair_source_seen.update(source_columns)
                pair_target_seen.update(target_columns)
                event_id = _sha256_bytes(_stable_json({
                    "pair": pair,
                    "turn": row["turn"],
                    "call_index": call_index,
                    "tool_name": view["tool_name"],
                    "source_columns": source_columns,
                    "target_columns": target_columns,
                }).encode("utf-8"))
                for source_column in source_columns:
                    col_index = source_headers.index(source_column)
                    pair_events.append({
                        "event_id": event_id,
                        "dataset_id": DATASET_ID,
                        "dataset_revision": dataset_revision,
                        "pair_id": pair,
                        "lineage_uid": lineage_uid(DATASET_ID, dataset_revision, pair),
                        "sample_id": _sample_id(DATASET_ID, dataset_revision, pair, col_index),
                        "col": col_index,
                        "source_header": source_column,
                        "target_headers": target_columns,
                        "turn": row["turn"],
                        "event_index": call_index,
                        "tool_name": view["tool_name"],
                        "event_kind": view["event_kind"],
                        "confidence": view["confidence"],
                        "reasoning_present": view["reasoning_present"],
                        "transformation_present": view["transformation_present"],
                        "raw_final_equal": raw_calls == final_calls,
                        "correctness_status": "NOT_RUN",
                        "paper_result": False,
                    })

        pair_has_invalid_reference = bool(pair_quarantine)
        include_pair_events = not (
            analysis_variant == "pair-invalid-sensitivity" and pair_has_invalid_reference
        )
        if include_pair_events:
            events.extend(pair_events)
        quarantine_events.extend(pair_quarantine)
        pair_summaries.append({
            "pair_id": pair,
            "analysis_included": include_pair_events,
            "exclusion_reason": "invalid_action_reference_pair_sensitivity" if not include_pair_events else None,
            "source_header_count": len(source_headers),
            "target_header_count": len(target_headers),
            "analysis_source_header_count": len(source_headers) if include_pair_events else 0,
            "audit_turns": len(audit),
            "trajectory_log_turns": len(trajectory_log),
            "final_source_coverage": len(pair_source_seen),
            "final_target_coverage": len(pair_target_seen),
            "invalid_action_reference_count": len(pair_quarantine),
        })

    if len(quarantine_events) != 3:
        raise AdapterError("invalid_action_reference_count_mismatch", expected=3, actual=len(quarantine_events))
    expected_invalid_pairs = {
        pair for pair, _turn, _tool, _call_id in EXPECTED_INVALID_ACTION_REFERENCES
    }
    if invalid_pairs != expected_invalid_pairs:
        raise AdapterError(
            "invalid_action_reference_pairs_mismatch",
            expected=sorted(expected_invalid_pairs),
            actual=sorted(invalid_pairs),
        )
    if analysis_variant == "pair-invalid-sensitivity" and len(invalid_pairs) != 1:
        raise AdapterError("pair_invalid_sensitivity_scope_mismatch", pairs=sorted(invalid_pairs))

    events.sort(key=lambda row: (str(row["pair_id"]), int(row["turn"]), int(row["event_index"]), str(row["source_header"])))
    quarantine_events.sort(key=lambda row: (str(row["pair_id"]), int(row["turn"]), int(row["event_index"]), str(row["invalid_source_reference"])))
    event_path = out_dir / "checkpoint_events.jsonl"
    event_path.write_text("".join(_stable_json(row) + "\n" for row in events), encoding="utf-8", newline="\n")
    quarantine_path = out_dir / "quarantine_events.jsonl"
    quarantine_path.write_text("".join(_stable_json(row) + "\n" for row in quarantine_events), encoding="utf-8", newline="\n")
    included_pairs = [row for row in pair_summaries if row["analysis_included"]]
    summary = {
        "contract_version": CONTRACT_VERSION,
        "analysis_variant": analysis_variant,
        "dataset_id": DATASET_ID,
        "dataset_revision": dataset_revision,
        "pair_count": len(pair_dirs),
        "analysis_pair_count": len(included_pairs),
        "source_header_count": sum(row["source_header_count"] for row in pair_summaries),
        "analysis_source_header_count": sum(row["analysis_source_header_count"] for row in pair_summaries),
        "target_header_count": sum(row["target_header_count"] for row in pair_summaries),
        "event_count": len(events),
        "invalid_action_reference_count": len(quarantine_events),
        "invalid_action_reference_pairs": sorted(invalid_pairs),
        "pairs": pair_summaries,
        "correctness_status": "NOT_RUN",
        "ground_truth_read": False,
        "embedded_gold_exposed": False,
        "paper_result": False,
        "source_gold_used_for_correctness": False,
    }
    _assert_no_forbidden_output(summary)
    summary_path = out_dir / "checkpoint_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    manifest = {
        "contract_version": CONTRACT_VERSION,
        "analysis_variant": analysis_variant,
        "input_files_read": sorted(input_files_read),
        "presence_only_file_count": len(APPROVED_PAIRS) * len(PRESENCE_ONLY_FILES),
        "presence_only_file_names_emitted": False,
        "forbidden_files_read": [],
        "ground_truth_read": False,
        "embedded_gold_exposed": False,
        "files": {
            "checkpoint_events.jsonl": {"bytes": event_path.stat().st_size, "sha256": _sha256_bytes(event_path.read_bytes())},
            "quarantine_events.jsonl": {"bytes": quarantine_path.stat().st_size, "sha256": _sha256_bytes(quarantine_path.read_bytes())},
            "checkpoint_summary.json": {"bytes": summary_path.stat().st_size, "sha256": _sha256_bytes(summary_path.read_bytes())},
        },
    }
    _assert_no_forbidden_output(events)
    _assert_no_forbidden_output(quarantine_events)
    _assert_no_forbidden_output(manifest)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return summary

def main() -> int:
    parser = argparse.ArgumentParser(description="Build a gold-free Valentine process/checkpoint view")
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--dataset-revision", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--analysis-variant", choices=ANALYSIS_VARIANTS, default="quarantine-primary")
    args = parser.parse_args()
    summary = build(args.staging_root, args.dataset_revision, args.out_dir, args.analysis_variant)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
