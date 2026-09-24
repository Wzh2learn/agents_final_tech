"""Offline, development-only baselines for the Phase 1a learnability probe.

The runner is deliberately narrower than a paper experiment.  It consumes only a
hash-bound ``proposal_train`` view after an independent-acceptance receipt exists,
never reads gate-validation/sealed/future bodies, and emits aggregate statistics.
Its strongest positive outcome is ``LEARNABILITY_SIGNAL``; it cannot authorize
training or produce ``DATA_GO``.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
import hashlib
import json
import math
from pathlib import Path
import random
import re
from typing import Any, Callable

try:
    from research.phase1a_data_contract import (
        CONTRACT_VERSION as DATA_CONTRACT_VERSION,
        FEATURE_FIELDS,
        FEATURE_LEDGER_VERSION,
        LABEL_FIELDS,
        MANIFEST_ROW_FIELDS,
        offline_guard,
    )
except ModuleNotFoundError:  # Direct ``python research/...py`` execution.
    from phase1a_data_contract import (  # type: ignore
        CONTRACT_VERSION as DATA_CONTRACT_VERSION,
        FEATURE_FIELDS,
        FEATURE_LEDGER_VERSION,
        LABEL_FIELDS,
        MANIFEST_ROW_FIELDS,
        offline_guard,
    )


REPO = Path(__file__).resolve().parents[1]
PROBE_VERSION = "phase1a-learnability-probe-v2"
ACCEPTANCE_VERSION = "phase1a-independent-acceptance-v2"
PRECHECK_READY = "READY_FOR_INDEPENDENT_ACCEPTANCE"
ACCEPTED = "ACCEPTED_FOR_PHASE1A_LEARNABILITY"

ACTIONS = ("skip", "hold", "map_to")
BASELINES = (
    "always_skip",
    "deterministic_matcher",
    "lexical_fuzzy",
    "confidence_only",
    "simple_classifier",
)
CASE_FIELDS = {
    "sample_id",
    "uid",
    "observed_header",
    "canonical_fields",
    "candidate_target",
    "confidence",
    "gold_action",
    "gold_target",
    "quality_grade",
    "family",
}
CONFIG_FIELDS = {
    "contract_version",
    "lexical_threshold",
    "confidence_policy",
    "classifier",
    "bootstrap",
    "decision_policy",
}
POLICY_FIELDS = {
    "min_dev_uids",
    "min_dev_uids_by_action",
    "min_dev_uids_by_family",
    "min_action_macro_f1",
    "max_harmful_map_rate",
    "min_correct_map_coverage",
    "min_classifier_macro_f1_gain",
}
MANUAL_REVIEW_FIELDS = {
    "licence_authority",
    "label_independence",
    "analysis_and_parser_provenance",
}
SHA256_RE = re.compile(r"[0-9a-f]{64}")
PRECHECK_GATES = {
    "artifact_integrity",
    "layer_isolation",
    "independent_correctness",
    "licence_permission",
    "confidence_provenance",
    "analysis_plan",
    "parser_contract",
}
MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_CASES = 100_000
MAX_TEXT = 4_096
MAX_CANONICAL_FIELDS = 512
MAX_CLASSIFIER_WORK = 5_000_000
MAX_BOOTSTRAP_WORK = 5_000_000


def _stable_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _strict_json(raw: bytes, source: str) -> Any:
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError(f"{source} exceeds the {MAX_JSON_BYTES}-byte limit")

    def invalid(value: str) -> None:
        raise ValueError(f"invalid JSON constant in {source}: {value}")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key in {source}: {key}")
            result[key] = value
        return result

    try:
        return json.loads(
            raw.decode("utf-8"),
            parse_constant=invalid,
            object_pairs_hook=unique,
        )
    except UnicodeDecodeError as exc:
        raise ValueError(f"{source} must be UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {source}") from exc


def _read_json_object(path: Path, source: str) -> tuple[dict[str, object], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read {source}") from exc
    value = _strict_json(raw, source)
    if not isinstance(value, dict):
        raise ValueError(f"{source} must be a JSON object")
    return value, raw


def _iso8601(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _finite_number(value: object, *, minimum: float, maximum: float) -> bool:
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and minimum <= float(value) <= maximum
    )


def _expect_exact_keys(value: dict[str, object], expected: set[str], source: str) -> None:
    unknown = sorted(set(value) - expected)
    missing = sorted(expected - set(value))
    if unknown:
        raise ValueError(f"unknown {source} fields: {unknown}")
    if missing:
        raise ValueError(f"missing {source} fields: {missing}")


def _resolve_inside(root: Path, relative: object) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("learnability view must use a safe package-relative path")
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("learnability view must use a safe package-relative path")
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("learnability view must use a safe package-relative path")
    return resolved


def _validate_config(config: dict[str, object]) -> dict[str, object]:
    _expect_exact_keys(config, CONFIG_FIELDS, "config")
    if config.get("contract_version") != PROBE_VERSION:
        raise ValueError("unsupported learnability config contract_version")
    if not _finite_number(config.get("lexical_threshold"), minimum=0.0, maximum=1.0):
        raise ValueError("lexical_threshold must be finite and within [0, 1]")

    confidence_policy = config.get("confidence_policy")
    required_confidence = {
        "high": "map_to",
        "medium": "hold",
        "low": "skip",
        "missing": "unmeasurable",
    }
    if confidence_policy != required_confidence:
        raise ValueError("confidence_policy must use the frozen high/medium/low/missing mapping")

    classifier = config.get("classifier")
    if not isinstance(classifier, dict):
        raise ValueError("classifier config must be an object")
    _expect_exact_keys(classifier, {"epochs", "learning_rate", "l2"}, "classifier")
    epochs = classifier.get("epochs")
    if type(epochs) is not int or not 1 <= epochs <= 10_000:
        raise ValueError("classifier epochs must be an integer within [1, 10000]")
    if not _finite_number(classifier.get("learning_rate"), minimum=1e-8, maximum=0.5):
        raise ValueError("classifier learning_rate must be within (0, 0.5]")
    if not _finite_number(classifier.get("l2"), minimum=0.0, maximum=1.0):
        raise ValueError("classifier l2 must be within [0, 1]")

    bootstrap = config.get("bootstrap")
    if not isinstance(bootstrap, dict):
        raise ValueError("bootstrap config must be an object")
    _expect_exact_keys(bootstrap, {"samples", "seed"}, "bootstrap")
    if type(bootstrap.get("samples")) is not int or not 100 <= bootstrap["samples"] <= 10_000:
        raise ValueError("bootstrap samples must be an integer within [100, 10000]")
    if type(bootstrap.get("seed")) is not int:
        raise ValueError("bootstrap seed must be an integer")

    policy = config.get("decision_policy")
    if not isinstance(policy, dict):
        raise ValueError("decision_policy must be an object")
    _expect_exact_keys(policy, POLICY_FIELDS, "decision_policy")
    if type(policy.get("min_dev_uids")) is not int or policy["min_dev_uids"] < 2:
        raise ValueError("min_dev_uids must be at least two independent lineage UIDs")
    action_minimums = policy.get("min_dev_uids_by_action")
    if not isinstance(action_minimums, dict) or set(action_minimums) != set(ACTIONS):
        raise ValueError("min_dev_uids_by_action must define skip, hold, and map_to")
    if any(type(value) is not int or value < 2 for value in action_minimums.values()):
        raise ValueError("each action UID minimum must be at least two")
    family_minimums = policy.get("min_dev_uids_by_family")
    if (
        not isinstance(family_minimums, dict)
        or not family_minimums
        or any(
            not isinstance(family, str)
            or not family
            or type(value) is not int
            or value < 2
            for family, value in family_minimums.items()
        )
    ):
        raise ValueError("each registered family UID minimum must be at least two")
    for field in POLICY_FIELDS - {
        "min_dev_uids",
        "min_dev_uids_by_action",
        "min_dev_uids_by_family",
    }:
        if not _finite_number(policy.get(field), minimum=0.0, maximum=1.0):
            raise ValueError(f"{field} must be finite and within [0, 1]")
    return config


def _validate_precheck(
    precheck: dict[str, object],
    manifest_sha256: str,
) -> None:
    if precheck.get("status") != PRECHECK_READY:
        raise ValueError("Phase 1a package precheck is not ready for independent acceptance")
    meta = precheck.get("meta")
    if not isinstance(meta, dict) or meta.get("endpoint_calls") != 0 or meta.get("socket_attempts") != 0:
        raise ValueError("precheck must attest zero endpoint and socket calls")
    if meta.get("contract_version") != DATA_CONTRACT_VERSION:
        raise ValueError("precheck contract_version is incompatible")
    hashes = precheck.get("hashes")
    if not isinstance(hashes, dict) or hashes.get("manifest_sha256") != manifest_sha256:
        raise ValueError("precheck manifest SHA-256 does not match the package")
    gates = precheck.get("gates")
    if not isinstance(gates, dict) or set(gates) != PRECHECK_GATES:
        raise ValueError("precheck gate set is incomplete or unknown")
    if any(not isinstance(gate, dict) or gate.get("status") != "PASS" for gate in gates.values()):
        raise ValueError("precheck contains a failed gate")


def _validate_acceptance(
    receipt: dict[str, object],
    *,
    manifest_sha256: str,
    precheck_sha256: str,
    config_sha256: str,
) -> dict[str, object]:
    expected = {
        "contract_version",
        "status",
        "scope",
        "approved_by",
        "approved_at",
        "package_manifest_sha256",
        "precheck_report_sha256",
        "preregistered_config_sha256",
        "learnability_view",
        "manual_reviews",
    }
    _expect_exact_keys(receipt, expected, "acceptance receipt")
    if receipt.get("contract_version") != ACCEPTANCE_VERSION:
        raise ValueError("unsupported independent-acceptance receipt version")
    if receipt.get("status") != ACCEPTED:
        raise ValueError("independent-acceptance receipt is not accepted for Phase 1a")
    if receipt.get("scope") != "proposal_train_only":
        raise ValueError("independent acceptance must be limited to proposal_train_only")
    if not isinstance(receipt.get("approved_by"), str) or not receipt["approved_by"]:
        raise ValueError("independent acceptance requires approved_by")
    if not _iso8601(receipt.get("approved_at")):
        raise ValueError("independent acceptance requires a timezone-bearing approved_at")
    if receipt.get("package_manifest_sha256") != manifest_sha256:
        raise ValueError("acceptance receipt manifest SHA-256 mismatch")
    if receipt.get("precheck_report_sha256") != precheck_sha256:
        raise ValueError("acceptance receipt precheck SHA-256 mismatch")
    if receipt.get("preregistered_config_sha256") != config_sha256:
        raise ValueError("acceptance receipt preregistered-config SHA-256 mismatch")

    reviews = receipt.get("manual_reviews")
    if not isinstance(reviews, dict):
        raise ValueError("manual_reviews must be an object")
    _expect_exact_keys(reviews, MANUAL_REVIEW_FIELDS, "manual review")
    reviewer_ids: list[str] = []
    for name in sorted(MANUAL_REVIEW_FIELDS):
        review = reviews.get(name)
        if not isinstance(review, dict) or set(review) != {"status", "reviewer_id"}:
            raise ValueError(f"manual review {name} has an invalid shape")
        reviewer_id = review.get("reviewer_id")
        if review.get("status") != "PASS" or not isinstance(reviewer_id, str) or not reviewer_id:
            raise ValueError(f"manual review {name} is not a recorded PASS")
        reviewer_ids.append(reviewer_id)
    if len(set(reviewer_ids)) != len(reviewer_ids):
        raise ValueError("manual review categories require distinct reviewers")

    view = receipt.get("learnability_view")
    if not isinstance(view, dict):
        raise ValueError("learnability_view binding must be an object")
    _expect_exact_keys(view, {"path", "bytes", "sha256"}, "learnability view binding")
    if type(view.get("bytes")) is not int or not 0 < view["bytes"] <= MAX_JSON_BYTES:
        raise ValueError("learnability view byte count is invalid")
    if not isinstance(view.get("sha256"), str) or not SHA256_RE.fullmatch(view["sha256"]):
        raise ValueError("learnability view SHA-256 is invalid")
    return view


def _proposal_refs(manifest: dict[str, object]) -> tuple[dict[str, str], dict[str, str]]:
    layers = manifest.get("layers")
    proposal = layers.get("proposal_train") if isinstance(layers, dict) else None
    if not isinstance(proposal, dict):
        raise ValueError("manifest lacks proposal_train layers")

    result: list[dict[str, str]] = []
    for partition in ("train", "dev"):
        rows = proposal.get(partition)
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"proposal_train.{partition} must be non-empty")
        refs: dict[str, str] = {}
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or set(row) != MANIFEST_ROW_FIELDS:
                raise ValueError(f"invalid proposal_train.{partition} row {index}")
            sample_id, uid = row.get("sample_id"), row.get("uid")
            if not isinstance(sample_id, str) or not sample_id or not isinstance(uid, str) or not uid:
                raise ValueError(f"invalid proposal_train.{partition} identity {index}")
            if sample_id in refs:
                raise ValueError(f"duplicate proposal_train.{partition} sample_id")
            refs[sample_id] = uid
        result.append(refs)
    train, dev = result
    if set(train) & set(dev) or set(train.values()) & set(dev.values()):
        raise ValueError("proposal_train train/dev must be sample- and UID-disjoint")
    return train, dev


def _bounded_text(value: object, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value) or len(value) > MAX_TEXT:
        raise ValueError(f"invalid {field}")
    return value


def _validate_case(value: object, line: int) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"learnability case line {line} must be an object")
    _expect_exact_keys(value, CASE_FIELDS, "case")
    sample_id = _bounded_text(value.get("sample_id"), "sample_id")
    uid = _bounded_text(value.get("uid"), "uid")
    observed = _bounded_text(value.get("observed_header"), "observed_header", allow_empty=True)
    family = _bounded_text(value.get("family"), "family")
    canonical = value.get("canonical_fields")
    if (
        not isinstance(canonical, list)
        or not 1 <= len(canonical) <= MAX_CANONICAL_FIELDS
        or any(not isinstance(field, str) or not field or len(field) > MAX_TEXT for field in canonical)
        or len(set(canonical)) != len(canonical)
    ):
        raise ValueError(f"invalid canonical_fields on line {line}")
    candidate = value.get("candidate_target")
    if candidate is not None and candidate not in canonical:
        raise ValueError(f"candidate_target is outside canonical_fields on line {line}")
    confidence = value.get("confidence")
    if confidence not in {None, "low", "medium", "high"}:
        raise ValueError(f"invalid confidence on line {line}")
    gold_action, gold_target = value.get("gold_action"), value.get("gold_target")
    if value.get("quality_grade") != "Q3":
        raise ValueError(f"learnability view requires Q3 labels on line {line}")
    if gold_action not in ACTIONS:
        raise ValueError(f"invalid gold_action on line {line}")
    if gold_action == "map_to":
        if gold_target not in canonical:
            raise ValueError(f"map_to gold_target is outside canonical_fields on line {line}")
    elif gold_target is not None:
        raise ValueError(f"non-map gold_target must be null on line {line}")
    return {
        "sample_id": sample_id,
        "uid": uid,
        "observed_header": observed,
        "canonical_fields": list(canonical),
        "candidate_target": candidate,
        "confidence": confidence,
        "gold_action": gold_action,
        "gold_target": gold_target,
        "quality_grade": "Q3",
        "family": family,
    }


def _read_cases(path: Path) -> tuple[list[dict[str, object]], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError("cannot read learnability view") from exc
    if not raw or len(raw) > MAX_JSON_BYTES:
        raise ValueError("learnability view is empty or exceeds its size limit")
    rows: list[dict[str, object]] = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        rows.append(_validate_case(_strict_json(line, f"learnability view line {line_number}"), line_number))
        if len(rows) > MAX_CASES:
            raise ValueError(f"learnability view exceeds {MAX_CASES} cases")
    if not rows:
        raise ValueError("learnability view has no cases")
    sample_ids = [str(row["sample_id"]) for row in rows]
    if len(set(sample_ids)) != len(sample_ids):
        raise ValueError("learnability view contains duplicate sample_id values")
    return rows, raw


def _bind_partitions(
    rows: list[dict[str, object]],
    train_refs: dict[str, str],
    dev_refs: dict[str, str],
    labels: dict[str, tuple[str, str, str | None, str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    expected = set(train_refs) | set(dev_refs)
    actual = {str(row["sample_id"]) for row in rows}
    if actual != expected:
        raise ValueError("learnability view must exactly match the proposal_train sample set")
    train: list[dict[str, object]] = []
    dev: list[dict[str, object]] = []
    for row in rows:
        sample_id, uid = str(row["sample_id"]), str(row["uid"])
        refs, target = (train_refs, train) if sample_id in train_refs else (dev_refs, dev)
        if refs[sample_id] != uid:
            raise ValueError("learnability view UID does not match proposal_train manifest")
        expected_label = labels.get(sample_id)
        actual_label = (
            uid,
            str(row["gold_action"]),
            row.get("gold_target"),
            str(row["quality_grade"]),
        )
        if expected_label != actual_label:
            raise ValueError("learnability view label does not match the accepted Q3 label ledger")
        target.append(row)
    return train, dev


def _load_label_ledger(
    package_root: Path,
    manifest: dict[str, object],
) -> dict[str, tuple[str, str, str | None, str]]:
    bindings = manifest.get("bindings")
    artifacts = manifest.get("artifacts")
    if not isinstance(bindings, dict) or not isinstance(artifacts, list):
        raise ValueError("manifest lacks the canonical label-ledger binding")
    label_id = bindings.get("label_ledger")
    matches = [
        item for item in artifacts
        if isinstance(item, dict) and item.get("id") == label_id
        and item.get("role") == "label_ledger"
    ]
    if len(matches) != 1:
        raise ValueError("manifest label-ledger binding is missing or ambiguous")
    artifact = matches[0]
    path = _resolve_inside(package_root, artifact.get("path"))
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError("cannot read canonical label ledger") from exc
    if len(raw) != artifact.get("bytes") or _sha256_bytes(raw) != artifact.get("sha256"):
        raise ValueError("canonical label ledger no longer matches the accepted manifest")
    labels: dict[str, tuple[str, str, str | None, str]] = {}
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        row = _strict_json(line, f"label ledger line {line_number}")
        if not isinstance(row, dict) or set(row) != LABEL_FIELDS:
            raise ValueError(f"invalid canonical label ledger row {line_number}")
        sample_id = row.get("sample_id")
        uid = row.get("uid")
        action = row.get("gold_action")
        target = row.get("gold_target")
        quality = row.get("quality_grade")
        if (
            not isinstance(sample_id, str) or not sample_id or sample_id in labels
            or not isinstance(uid, str) or not uid
            or action not in ACTIONS or quality != "Q3"
            or (action == "map_to" and (not isinstance(target, str) or not target))
            or (action != "map_to" and target is not None)
        ):
            raise ValueError(f"invalid canonical label identity on line {line_number}")
        labels[sample_id] = (uid, str(action), target if isinstance(target, str) else None, "Q3")
    return labels


def _load_feature_ledger(
    package_root: Path,
    manifest: dict[str, object],
) -> dict[str, dict[str, object]]:
    bindings = manifest.get("bindings")
    artifacts = manifest.get("artifacts")
    if not isinstance(bindings, dict) or not isinstance(artifacts, list):
        raise ValueError("manifest lacks the canonical feature-ledger binding")
    feature_id = bindings.get("learnability_feature_ledger")
    matches = [
        item for item in artifacts
        if isinstance(item, dict) and item.get("id") == feature_id
        and item.get("role") == "learnability_feature_ledger"
    ]
    if len(matches) != 1:
        raise ValueError("manifest feature-ledger binding is missing or ambiguous")
    artifact = matches[0]
    path = _resolve_inside(package_root, artifact.get("path"))
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError("cannot read canonical feature ledger") from exc
    if len(raw) != artifact.get("bytes") or _sha256_bytes(raw) != artifact.get("sha256"):
        raise ValueError("canonical feature ledger no longer matches the accepted manifest")
    value = _strict_json(raw, "canonical feature ledger")
    expected = {
        "contract_version",
        "source_tables_sha256",
        "schema_sha256",
        "confidence_manifest_sha256",
        "rows",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError("canonical feature ledger has an invalid shape")
    if value.get("contract_version") != FEATURE_LEDGER_VERSION:
        raise ValueError("canonical feature ledger has an unsupported version")
    rows = value.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("canonical feature ledger has no rows")
    result: dict[str, dict[str, object]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != FEATURE_FIELDS:
            raise ValueError(f"invalid canonical feature ledger row {index}")
        sample_id = row.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id or sample_id in result:
            raise ValueError(f"invalid canonical feature identity on row {index}")
        result[sample_id] = row
    return result


# D11 (user ruling 2026-09-24, convention (i)): the approved UID floors live in the
# package's analysis_plan under role-layer-scoped keys, while the floors that actually
# drive the PILOT_ONLY decision live in the preregistered config under bare family
# names. The analysis_plan side therefore uses "proposal_train.dev/<family>".
DEV_ROLE_PREFIX = "proposal_train.dev/"


def _load_analysis_plan(
    package_root: Path,
    manifest: dict[str, object],
) -> dict[str, object]:
    """Load the hash-bound analysis_plan artifact for the D11 consistency check.

    Mirrors ``_load_feature_ledger``: the artifact must be uniquely bound in the
    manifest and must still match the accepted byte count and SHA-256, so a plan
    edited after acceptance cannot be substituted.
    """
    bindings = manifest.get("bindings")
    artifacts = manifest.get("artifacts")
    if not isinstance(bindings, dict) or not isinstance(artifacts, list):
        raise ValueError("manifest lacks the canonical analysis-plan binding")
    plan_id = bindings.get("analysis_plan")
    matches = [
        item for item in artifacts
        if isinstance(item, dict) and item.get("id") == plan_id
        and item.get("role") == "analysis_plan"
    ]
    if len(matches) != 1:
        raise ValueError("manifest analysis-plan binding is missing or ambiguous")
    artifact = matches[0]
    path = _resolve_inside(package_root, artifact.get("path"))
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError("cannot read canonical analysis plan") from exc
    if len(raw) != artifact.get("bytes") or _sha256_bytes(raw) != artifact.get("sha256"):
        raise ValueError("canonical analysis plan no longer matches the accepted manifest")
    value = _strict_json(raw, "canonical analysis plan")
    if not isinstance(value, dict):
        raise ValueError("canonical analysis plan must be an object")
    return value


def _check_uid_floor_consistency(
    analysis_plan: dict[str, object],
    policy: dict[str, object],
) -> None:
    """D11: fail closed unless the approved floors and the enforced floors agree.

    Before this check the two copies were unrelated: the data contract only
    shape-checked ``analysis_plan.minimum_uid_by_action`` /
    ``minimum_uid_by_role_family``, while ``decision_policy.min_dev_uids_by_action``
    / ``min_dev_uids_by_family`` were what actually produced ``PILOT_ONLY``. A human
    could approve 50/50/50 and hash-bind it, set the config to 2/2/2, and the probe
    would still return a positive decision -- the approved power floor was silently
    bypassed at the very step meant to enforce it.

    action dimension: both sides key on exactly {map_to, skip, hold}, so the dicts
    must be equal.

    family dimension (convention (i)): analysis_plan keys are dev-scoped
    ``proposal_train.dev/<family>``; config keys are bare ``<family>``. Stripping the
    prefix must yield exactly the config dict -- same keys and same values.
    """
    plan_action = analysis_plan.get("minimum_uid_by_action")
    cfg_action = policy.get("min_dev_uids_by_action")
    if not isinstance(plan_action, dict) or plan_action != cfg_action:
        raise ValueError(
            "minimum_uid_by_action disagrees with the preregistered config's "
            "min_dev_uids_by_action; the approved UID floor would not be enforced"
        )

    plan_family = analysis_plan.get("minimum_uid_by_role_family")
    cfg_family = policy.get("min_dev_uids_by_family")
    if not isinstance(plan_family, dict) or not isinstance(cfg_family, dict):
        raise ValueError("UID floor family minimums must both be objects")
    mapped: dict[str, object] = {}
    for key, value in plan_family.items():
        if not isinstance(key, str) or not key.startswith(DEV_ROLE_PREFIX):
            raise ValueError(
                "minimum_uid_by_role_family key "
                f"{key!r} must be dev-scoped as {DEV_ROLE_PREFIX}<family>"
            )
        family = key[len(DEV_ROLE_PREFIX):]
        if not family or "/" in family:
            raise ValueError(
                f"minimum_uid_by_role_family key {key!r} has an invalid family name"
            )
        if family in mapped:
            raise ValueError(
                f"duplicate dev family in minimum_uid_by_role_family: {family}"
            )
        mapped[family] = value
    if mapped != cfg_family:
        raise ValueError(
            "minimum_uid_by_role_family (dev-scoped) disagrees with the preregistered "
            "config's min_dev_uids_by_family; the approved UID floor would not be enforced"
        )


def _normalize(value: object) -> str:
    return "".join(character.lower() for character in str(value) if character.isalnum())


def _tokens(value: object) -> set[str]:
    return set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", str(value).lower()))


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


Prediction = tuple[str, str | None] | None


def _always_skip(row: dict[str, object]) -> Prediction:
    del row
    return "skip", None


def _deterministic_matcher(row: dict[str, object]) -> Prediction:
    observed = _normalize(row["observed_header"])
    matches = [field for field in row["canonical_fields"] if _normalize(field) == observed]
    if len(matches) == 1 and observed:
        return "map_to", str(matches[0])
    return "skip", None


def _best_lexical(row: dict[str, object]) -> tuple[str, float]:
    observed = _normalize(row["observed_header"])
    ranked: list[tuple[float, str]] = []
    for field in row["canonical_fields"]:
        normalized = _normalize(field)
        score = SequenceMatcher(None, observed, normalized, autojunk=False).ratio()
        ranked.append((score, str(field)))
    score, field = max(ranked, key=lambda item: (item[0], item[1]))
    return field, score


def _lexical_fuzzy(row: dict[str, object], threshold: float) -> Prediction:
    field, score = _best_lexical(row)
    return ("map_to", field) if score >= threshold else ("skip", None)


def _confidence_only(row: dict[str, object]) -> Prediction:
    confidence = row["confidence"]
    if confidence is None:
        return None
    if confidence == "high":
        candidate = row["candidate_target"]
        return ("map_to", str(candidate)) if candidate is not None else ("hold", None)
    if confidence == "medium":
        return "hold", None
    return "skip", None


def _features(row: dict[str, object]) -> list[float]:
    observed = str(row["observed_header"])
    candidate = row["candidate_target"]
    candidate_text = str(candidate) if candidate is not None else ""
    normalized_observed = _normalize(observed)
    normalized_candidate = _normalize(candidate_text)
    sequence = (
        SequenceMatcher(None, normalized_observed, normalized_candidate, autojunk=False).ratio()
        if candidate is not None
        else 0.0
    )
    confidence = row["confidence"]
    exact_canonical = any(
        normalized_observed and normalized_observed == _normalize(field)
        for field in row["canonical_fields"]
    )
    return [
        1.0 if candidate is not None else 0.0,
        1.0 if normalized_observed and normalized_observed == normalized_candidate else 0.0,
        sequence,
        _jaccard(set(normalized_observed), set(normalized_candidate)),
        _jaccard(_tokens(observed), _tokens(candidate_text)),
        1.0 if exact_canonical else 0.0,
        1.0 if confidence == "high" else 0.0,
        1.0 if confidence == "medium" else 0.0,
        1.0 if confidence == "low" else 0.0,
        1.0 if confidence is None else 0.0,
        min(len(row["canonical_fields"]) / 20.0, 1.0),
        min(len(observed) / 100.0, 1.0),
    ]


class _SoftmaxClassifier:
    """Small deterministic CPU classifier for learnability triage, not a student model."""

    def __init__(self, *, epochs: int, learning_rate: float, l2: float) -> None:
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.l2 = l2
        self.weights: list[list[float]] = []

    def fit(self, rows: list[dict[str, object]]) -> None:
        if not rows:
            raise ValueError("simple classifier requires non-empty proposal_train.train")
        features = [[1.0] + _features(row) for row in rows]
        labels = [ACTIONS.index(str(row["gold_action"])) for row in rows]
        width = len(features[0])
        self.weights = [[0.0] * width for _ in ACTIONS]
        for _ in range(self.epochs):
            gradients = [[0.0] * width for _ in ACTIONS]
            for vector, label in zip(features, labels, strict=True):
                probabilities = self._probabilities(vector)
                for class_index in range(len(ACTIONS)):
                    error = probabilities[class_index] - (1.0 if class_index == label else 0.0)
                    for feature_index, feature in enumerate(vector):
                        gradients[class_index][feature_index] += error * feature
            scale = 1.0 / len(features)
            for class_index in range(len(ACTIONS)):
                for feature_index in range(width):
                    regularization = (
                        self.l2 * self.weights[class_index][feature_index]
                        if feature_index > 0
                        else 0.0
                    )
                    self.weights[class_index][feature_index] -= self.learning_rate * (
                        gradients[class_index][feature_index] * scale + regularization
                    )
                    if not math.isfinite(self.weights[class_index][feature_index]):
                        raise ValueError("simple classifier produced a non-finite weight")

    def _probabilities(self, vector: list[float]) -> list[float]:
        logits = [
            sum(weight * feature for weight, feature in zip(class_weights, vector, strict=True))
            for class_weights in self.weights
        ]
        pivot = max(logits)
        exponentials = [math.exp(logit - pivot) for logit in logits]
        total = sum(exponentials)
        return [value / total for value in exponentials]

    def predict(self, row: dict[str, object]) -> Prediction:
        probabilities = self._probabilities([1.0] + _features(row))
        index = max(range(len(ACTIONS)), key=lambda item: (probabilities[item], -item))
        action = ACTIONS[index]
        if action == "map_to":
            candidate = row["candidate_target"]
            return ("map_to", str(candidate)) if candidate is not None else ("hold", None)
        return action, None


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _round(value: float | None) -> float | None:
    return round(value, 8) if value is not None else None


def _core_metrics(
    rows: list[dict[str, object]],
    predictions: list[Prediction],
) -> dict[str, object]:
    pairs = [(row, prediction) for row, prediction in zip(rows, predictions, strict=True)
             if prediction is not None]
    excluded = len(rows) - len(pairs)
    evaluated = len(pairs)
    f1_by_action: dict[str, float] = {}
    for action in ACTIONS:
        true_positive = sum(
            1 for row, prediction in pairs
            if row["gold_action"] == action and prediction[0] == action
        )
        false_positive = sum(
            1 for row, prediction in pairs
            if row["gold_action"] != action and prediction[0] == action
        )
        false_negative = sum(
            1 for row, prediction in pairs
            if row["gold_action"] == action and prediction[0] != action
        )
        denominator = 2 * true_positive + false_positive + false_negative
        f1_by_action[action] = 2 * true_positive / denominator if denominator else 0.0

    gold_map = sum(1 for row, _ in pairs if row["gold_action"] == "map_to")
    correct_map = sum(
        1 for row, prediction in pairs
        if row["gold_action"] == "map_to"
        and prediction == ("map_to", row["gold_target"])
    )
    gold_hold = sum(1 for row, _ in pairs if row["gold_action"] == "hold")
    correct_hold = sum(
        1 for row, prediction in pairs
        if row["gold_action"] == "hold" and prediction[0] == "hold"
    )
    predicted_map = sum(1 for _, prediction in pairs if prediction[0] == "map_to")
    harmful = sum(
        1 for row, prediction in pairs
        if prediction[0] == "map_to"
        and (row["gold_action"] != "map_to" or prediction[1] != row["gold_target"])
    )
    uids = {str(row["uid"]) for row, _ in pairs}
    return {
        "action_macro_f1": _round(sum(f1_by_action.values()) / len(ACTIONS)),
        "action_f1": {action: _round(f1_by_action[action]) for action in ACTIONS},
        "correct_map_to_recall": _round(_ratio(correct_map, gold_map)),
        "hold_recall": _round(_ratio(correct_hold, gold_hold)),
        "harmful_map_rate": _round(_ratio(harmful, evaluated)),
        "map_to_risk": _round(_ratio(harmful, predicted_map)),
        "correct_map_coverage": _round(_ratio(correct_map, evaluated)),
        "evaluated_samples": evaluated,
        "evaluated_uids": len(uids),
        "excluded_unmeasurable": excluded,
    }


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _cluster_intervals(
    rows: list[dict[str, object]],
    predictions: list[Prediction],
    *,
    samples: int,
    seed: int,
) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[tuple[dict[str, object], Prediction]]] = defaultdict(list)
    for row, prediction in zip(rows, predictions, strict=True):
        grouped[str(row["uid"])].append((row, prediction))
    uids = sorted(grouped)
    metrics = ("action_macro_f1", "harmful_map_rate", "correct_map_coverage")
    draws: dict[str, list[float]] = {metric: [] for metric in metrics}
    if uids:
        rng = random.Random(seed)
        for _ in range(samples):
            selected = [uids[rng.randrange(len(uids))] for _ in uids]
            sampled_pairs = [pair for uid in selected for pair in grouped[uid]]
            sampled_rows = [pair[0] for pair in sampled_pairs]
            sampled_predictions = [pair[1] for pair in sampled_pairs]
            result = _core_metrics(sampled_rows, sampled_predictions)
            for metric in metrics:
                value = result[metric]
                if isinstance(value, float):
                    draws[metric].append(value)
    return {
        metric: {
            "lower": _round(_percentile(draws[metric], 0.025)),
            "upper": _round(_percentile(draws[metric], 0.975)),
            "method": "uid_cluster_bootstrap",
            "samples": samples,
        }
        for metric in metrics
    }


def _worst_family(
    rows: list[dict[str, object]],
    predictions: list[Prediction],
) -> dict[str, object] | None:
    grouped: dict[str, list[tuple[dict[str, object], Prediction]]] = defaultdict(list)
    for row, prediction in zip(rows, predictions, strict=True):
        grouped[str(row["family"])].append((row, prediction))
    candidates: list[tuple[float, float, str, dict[str, object]]] = []
    for family, pairs in grouped.items():
        metrics = _core_metrics([pair[0] for pair in pairs], [pair[1] for pair in pairs])
        macro = float(metrics["action_macro_f1"] or 0.0)
        harm = float(metrics["harmful_map_rate"] or 0.0)
        candidates.append((macro, -harm, family, metrics))
    if not candidates:
        return None
    _, _, family, metrics = min(candidates, key=lambda item: (item[0], item[1], item[2]))
    return {
        "family": family,
        "evaluated_samples": metrics["evaluated_samples"],
        "action_macro_f1": metrics["action_macro_f1"],
        "harmful_map_rate": metrics["harmful_map_rate"],
        "correct_map_coverage": metrics["correct_map_coverage"],
    }


def _score(
    rows: list[dict[str, object]],
    predictor: Callable[[dict[str, object]], Prediction],
    *,
    bootstrap_samples: int,
    bootstrap_seed: int,
    confidence_subset: bool = False,
) -> dict[str, object]:
    predictions = [predictor(row) for row in rows]
    metrics = _core_metrics(rows, predictions)
    metrics["uid_cluster_intervals"] = _cluster_intervals(
        rows,
        predictions,
        samples=bootstrap_samples,
        seed=bootstrap_seed,
    )
    metrics["worst_family"] = _worst_family(rows, predictions)
    metrics["scope"] = "confidence_measurable_subset" if confidence_subset else "full_partition"
    metrics["comparable_to_full_dev"] = not confidence_subset or metrics["excluded_unmeasurable"] == 0
    return metrics


def _meets_policy(metrics: dict[str, object], policy: dict[str, object]) -> bool:
    values = (
        metrics.get("action_macro_f1"),
        metrics.get("harmful_map_rate"),
        metrics.get("correct_map_coverage"),
    )
    if any(type(value) not in (int, float) for value in values):
        return False
    return (
        float(values[0]) >= float(policy["min_action_macro_f1"])
        and float(values[1]) <= float(policy["max_harmful_map_rate"])
        and float(values[2]) >= float(policy["min_correct_map_coverage"])
    )


def _uid_support(rows: list[dict[str, object]]) -> dict[str, object]:
    by_action: dict[str, set[str]] = {action: set() for action in ACTIONS}
    by_family: dict[str, set[str]] = defaultdict(set)
    all_uids: set[str] = set()
    for row in rows:
        uid = str(row["uid"])
        all_uids.add(uid)
        by_action[str(row["gold_action"])].add(uid)
        by_family[str(row["family"])].add(uid)
    return {
        "total": len(all_uids),
        "by_action": {
            action: len(by_action[action])
            for action in ACTIONS
        },
        "by_family": {
            family: len(uids)
            for family, uids in sorted(by_family.items())
        },
    }


def decide_probe(
    dev_uid_support: dict[str, object],
    metrics: dict[str, dict[str, object]],
    policy: dict[str, object],
) -> dict[str, object]:
    """Return a bounded development decision; never a data or training release."""

    action_counts = dev_uid_support.get("by_action")
    family_counts = dev_uid_support.get("by_family")
    if not isinstance(action_counts, dict) or not isinstance(family_counts, dict):
        raise ValueError("dev UID support must contain action and family counts")
    action_minimums = policy["min_dev_uids_by_action"]
    family_minimums = policy["min_dev_uids_by_family"]
    assert isinstance(action_minimums, dict) and isinstance(family_minimums, dict)
    shortfalls: list[dict[str, object]] = []
    total = dev_uid_support.get("total")
    if type(total) is not int or total < int(policy["min_dev_uids"]):
        shortfalls.append({
            "dimension": "all",
            "name": "all",
            "observed_uids": total if type(total) is int else 0,
            "required_uids": int(policy["min_dev_uids"]),
        })
    for action in ACTIONS:
        observed = action_counts.get(action)
        required = int(action_minimums[action])
        if type(observed) is not int or observed < required:
            shortfalls.append({
                "dimension": "action",
                "name": action,
                "observed_uids": observed if type(observed) is int else 0,
                "required_uids": required,
            })
    registered_families = set(family_minimums)
    observed_families = set(family_counts)
    for family in sorted(registered_families | observed_families):
        observed = family_counts.get(family)
        required = family_minimums.get(family)
        if type(observed) is not int or type(required) is not int or observed < required:
            shortfalls.append({
                "dimension": "family",
                "name": family,
                "observed_uids": observed if type(observed) is int else 0,
                "required_uids": required if type(required) is int else None,
            })
    if shortfalls:
        return {
            "status": "PILOT_ONLY",
            "reason": "insufficient_or_unregistered_dev_uid_support",
            "uid_support_shortfalls": shortfalls,
            "training_authorized": False,
        }
    nonlearned_names = ("deterministic_matcher", "lexical_fuzzy", "confidence_only")
    comparable = [
        name for name in nonlearned_names
        if name in metrics and metrics[name].get("comparable_to_full_dev", True) is not False
    ]
    sufficient = [name for name in comparable if _meets_policy(metrics[name], policy)]
    classifier = metrics.get("simple_classifier", {})
    best_nonlearned = max(
        (float(metrics[name].get("action_macro_f1") or 0.0) for name in comparable),
        default=0.0,
    )
    classifier_macro = float(classifier.get("action_macro_f1") or 0.0)
    if (
        _meets_policy(classifier, policy)
        and classifier_macro - best_nonlearned
        >= float(policy["min_classifier_macro_f1_gain"])
    ):
        return {
            "status": "LEARNABILITY_SIGNAL",
            "reason": "cheap_classifier_exceeds_nonlearned_baselines_on_development_view",
            "macro_f1_gain": _round(classifier_macro - best_nonlearned),
            "training_authorized": False,
        }
    if sufficient:
        return {
            "status": "SIMPLE_SUFFICIENT",
            "reason": "nonlearned_baseline_meets_policy_without_preregistered_residual_gain",
            "baseline": max(
                sufficient,
                key=lambda name: (float(metrics[name]["action_macro_f1"]), name),
            ),
            "training_authorized": False,
        }
    return {
        "status": "NO_CLEAR_SIGNAL",
        "reason": "no_baseline_satisfies_the_preregistered_development_policy",
        "training_authorized": False,
    }


def _baseline_results(
    train: list[dict[str, object]],
    dev: list[dict[str, object]],
    config: dict[str, object],
) -> dict[str, dict[str, object]]:
    threshold = float(config["lexical_threshold"])
    classifier_config = config["classifier"]
    bootstrap = config["bootstrap"]
    assert isinstance(classifier_config, dict) and isinstance(bootstrap, dict)
    classifier = _SoftmaxClassifier(
        epochs=int(classifier_config["epochs"]),
        learning_rate=float(classifier_config["learning_rate"]),
        l2=float(classifier_config["l2"]),
    )
    classifier.fit(train)
    predictors: dict[str, Callable[[dict[str, object]], Prediction]] = {
        "always_skip": _always_skip,
        "deterministic_matcher": _deterministic_matcher,
        "lexical_fuzzy": lambda row: _lexical_fuzzy(row, threshold),
        "confidence_only": _confidence_only,
        "simple_classifier": classifier.predict,
    }
    result: dict[str, dict[str, object]] = {}
    for baseline_index, name in enumerate(BASELINES):
        predictor = predictors[name]
        confidence_subset = name == "confidence_only"
        result[name] = {
            "train": _score(
                train,
                predictor,
                bootstrap_samples=int(bootstrap["samples"]),
                bootstrap_seed=int(bootstrap["seed"]) + baseline_index * 2,
                confidence_subset=confidence_subset,
            ),
            "dev": _score(
                dev,
                predictor,
                bootstrap_samples=int(bootstrap["samples"]),
                bootstrap_seed=int(bootstrap["seed"]) + baseline_index * 2 + 1,
                confidence_subset=confidence_subset,
            ),
        }
    return result


def _run_probe(
    *,
    package_root: Path,
    precheck_report: Path,
    acceptance_receipt: Path,
    config_path: Path,
) -> dict[str, object]:
    manifest_path = package_root / "phase1a_manifest.json"
    manifest, manifest_raw = _read_json_object(manifest_path, "package manifest")
    manifest_sha = _sha256_bytes(manifest_raw)
    precheck, precheck_raw = _read_json_object(precheck_report, "precheck report")
    _validate_precheck(precheck, manifest_sha)
    config, config_raw = _read_json_object(config_path, "preregistered config")
    _validate_config(config)
    receipt, receipt_raw = _read_json_object(acceptance_receipt, "acceptance receipt")
    view_binding = _validate_acceptance(
        receipt,
        manifest_sha256=manifest_sha,
        precheck_sha256=_sha256_bytes(precheck_raw),
        config_sha256=_sha256_bytes(config_raw),
    )

    view_path = _resolve_inside(package_root, view_binding["path"])
    if view_path.suffix != ".jsonl" or not view_path.is_file():
        raise ValueError("learnability view must be an existing JSONL file")
    rows, view_raw = _read_cases(view_path)
    if len(view_raw) != view_binding["bytes"]:
        raise ValueError("learnability view byte count mismatch")
    if _sha256_bytes(view_raw) != view_binding["sha256"]:
        raise ValueError("learnability view SHA-256 mismatch")

    train_refs, dev_refs = _proposal_refs(manifest)
    labels = _load_label_ledger(package_root, manifest)
    features = _load_feature_ledger(package_root, manifest)
    train, dev = _bind_partitions(rows, train_refs, dev_refs, labels)
    if set(features) != set(train_refs) | set(dev_refs):
        raise ValueError("canonical feature ledger must exactly cover proposal_train")
    for row in train + dev:
        sample_id = str(row["sample_id"])
        actual = {field: row[field] for field in FEATURE_FIELDS}
        if actual != features[sample_id]:
            raise ValueError(
                "learnability view features do not match the hash-bound feature ledger"
            )
    classifier = config["classifier"]
    bootstrap = config["bootstrap"]
    assert isinstance(classifier, dict) and isinstance(bootstrap, dict)
    if len(train) * int(classifier["epochs"]) > MAX_CLASSIFIER_WORK:
        raise ValueError("classifier work budget exceeded")
    if (len(train) + len(dev)) * int(bootstrap["samples"]) > MAX_BOOTSTRAP_WORK:
        raise ValueError("bootstrap work budget exceeded")
    baselines = _baseline_results(train, dev, config)
    dev_metrics = {name: result["dev"] for name, result in baselines.items()}
    policy = config["decision_policy"]
    assert isinstance(policy, dict)
    # D11: the approved floors (package analysis_plan) and the enforced floors
    # (preregistered config) must agree before any decision is derived from them.
    _check_uid_floor_consistency(_load_analysis_plan(package_root, manifest), policy)
    dev_uid_support = _uid_support(dev)
    decision = decide_probe(dev_uid_support, dev_metrics, policy)
    return {
        "decision": decision["status"],
        "decision_detail": decision,
        "meta": {
            "contract_version": PROBE_VERSION,
            "evidence_level": "DEVELOPMENT_ONLY",
            "endpoint_calls": 0,
            "socket_attempts": 0,
            "training_authorized": False,
            "paper_result": False,
        },
        "counts": {
            "train_samples": len(train),
            "train_uids": len({str(row["uid"]) for row in train}),
            "dev_samples": len(dev),
            "dev_uids": len({str(row["uid"]) for row in dev}),
            "dev_uid_support": dev_uid_support,
            "manual_review_categories": len(MANUAL_REVIEW_FIELDS),
        },
        "hashes": {
            "implementation_sha256": _sha256_bytes(Path(__file__).read_bytes()),
            "package_manifest_sha256": manifest_sha,
            "precheck_report_sha256": _sha256_bytes(precheck_raw),
            "acceptance_receipt_sha256": _sha256_bytes(receipt_raw),
            "learnability_view_sha256": _sha256_bytes(view_raw),
            "preregistered_config_sha256": _sha256_bytes(config_raw),
        },
        "metric_definitions": {
            "harmful_map_rate": "incorrect map_to predictions divided by evaluated samples",
            "map_to_risk": "incorrect map_to predictions divided by predicted map_to actions",
            "correct_map_coverage": "correct map_to predictions divided by evaluated samples",
            "confidence_missing": "excluded as unmeasurable; never filled with zero",
        },
        "baselines": baselines,
        "release_boundary": (
            "Development-only triage. SIMPLE_SUFFICIENT stops escalation; "
            "LEARNABILITY_SIGNAL only supports requesting a separately authorized window. "
            "No outcome is DATA_GO, training permission, sealed-test evidence, or a paper result."
        ),
    }


def run_probe(
    *,
    package_root: Path | str,
    precheck_report: Path | str,
    acceptance_receipt: Path | str,
    config_path: Path | str,
) -> dict[str, object]:
    root = Path(package_root).resolve()
    if not root.is_dir():
        raise ValueError("package_root must be an existing directory")
    with offline_guard() as attempts:
        report = _run_probe(
            package_root=root,
            precheck_report=Path(precheck_report).resolve(),
            acceptance_receipt=Path(acceptance_receipt).resolve(),
            config_path=Path(config_path).resolve(),
        )
        report["meta"]["socket_attempts"] = attempts[0]
        if attempts[0]:
            raise RuntimeError("network attempted during Phase 1a learnability probe")
    return report


def _valid_output_path(output: Path, package_root: Path) -> bool:
    resolved = output.resolve()
    return not resolved.is_relative_to(package_root) and not resolved.is_relative_to(REPO)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run aggregate-only Phase 1a simple baselines after independent data acceptance",
    )
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--precheck-report", type=Path, required=True)
    parser.add_argument("--acceptance-receipt", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    output = args.output.resolve()
    root = args.package_root.resolve()
    if output.exists():
        parser.error("output already exists; use a new path")
    if not _valid_output_path(output, root):
        parser.error("output must be outside the private package and repository")
    report = run_probe(
        package_root=root,
        precheck_report=args.precheck_report,
        acceptance_receipt=args.acceptance_receipt,
        config_path=args.config,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(_stable_json(report) + "\n")
    summary = {
        "decision": report["decision"],
        "counts": report["counts"],
        "endpoint_calls": 0,
        "socket_attempts": report["meta"]["socket_attempts"],
        "report_sha256": _sha256_bytes(output.read_bytes()),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
