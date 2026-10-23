"""Evaluate STALE answers from text and source evidence, not model self-labels."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for",
    "from", "has", "have", "in", "is", "it", "its", "of", "on", "or", "the",
    "their", "them", "there", "this", "to", "was", "were", "with", "you",
    "your", "i", "my", "me", "we", "our",
}
UNCERTAINTY = (
    "not sure", "cannot establish", "can't establish", "insufficient",
    "unknown", "unable to determine", "not enough", "unclear", "may be",
    "might be", "possibly", "perhaps", "could be",
)
QUALIFIERS = (
    "may", "might", "could", "possibly", "likely", "suggests", "not necessarily",
    "appears", "seems", "but the evidence", "qualified",
)
CONTRAST_MARKERS = (
    "no longer", "rather than", "instead", "used to", "previously", "old",
    "anymore", "not the same", "has changed", "has returned", "returned",
    "completed a drop-off", "cleared",
)


def normalize(text: Any) -> str:
    """Normalize text for stable phrase and token comparisons."""
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()


def tokens(text: Any) -> set[str]:
    """Return informative lowercase word tokens."""
    return {
        word
        for word in re.findall(r"[a-z0-9]+", normalize(text))
        if word not in STOPWORDS and len(word) > 2
    }


def match_group(group: list[str], text: str) -> bool:
    """Return whether any concept alternative appears in normalized text."""
    normalized = normalize(text)
    return any(normalize(concept) in normalized for concept in group)


def matched_groups(groups: list[list[str]], text: str) -> list[int]:
    """Return indexes of matched required concept groups."""
    return [index for index, group in enumerate(groups) if match_group(group, text)]


def clause_contains_negation(clause: str) -> bool:
    """Detect a replacement/contrast context in one sentence-like clause."""
    normalized = normalize(clause)
    return any(term in normalized for term in CONTRAST_MARKERS)


def affirms_old_state(answer: str, old_concepts: list[str]) -> bool:
    """Detect an unqualified current affirmation of an old-state concept."""
    clauses = re.split(r"[.!?;]\s*", answer or "")
    for clause in clauses:
        normalized = normalize(clause)
        if not any(normalize(concept) in normalized for concept in old_concepts):
            continue
        if clause_contains_negation(clause):
            continue
        if re.search(r"\b(yes|still|currently|continues|remains|keeps)\b", normalized):
            return True
        if not re.search(r"\b(no|rather|instead|old|previous|used)\b", normalized):
            return True
    return False


def answer_relation(answer: str, reference: dict[str, Any]) -> str:
    """Classify answer meaning without using model-provided labels."""
    normalized = normalize(answer)
    matched = matched_groups(reference["required_concept_groups"], answer)
    affirm_old = affirms_old_state(answer, reference["old_state_concepts"])
    uncertain = any(term in normalized for term in UNCERTAINTY)
    if uncertain and not matched:
        return "UNKNOWN_CURRENT"
    if matched and affirm_old:
        return "CONTRADICTORY"
    if matched and not affirm_old:
        return "OLD_STATE_INVALID"
    if affirm_old:
        return "OLD_STATE_VALID"
    return "UNSPECIFIED"


def evidence_text(dataset_item: dict[str, Any], selected_indices: list[int]) -> str:
    """Render only the selected source sessions for grounding checks."""
    sessions = dataset_item.get("haystack_session", [])
    chunks = []
    for index in selected_indices:
        if 0 <= index < len(sessions):
            for message in sessions[index]:
                chunks.append(f"{message.get('role', '')}: {message.get('content', '')}")
    return "\n".join(chunks)


def grounding_metrics(answer: str, evidence: str, reference: dict[str, Any]) -> dict[str, Any]:
    """Measure answer-token and required-concept grounding in allowed evidence."""
    answer_tokens = tokens(answer)
    evidence_tokens = tokens(evidence)
    grounded = answer_tokens & evidence_tokens
    ratio = len(grounded) / len(answer_tokens) if answer_tokens else 0.0
    concept_grounded = [
        index
        for index, group in enumerate(reference["required_concept_groups"])
        if match_group(group, evidence)
    ]
    return {
        "answer_token_count": len(answer_tokens),
        "grounded_token_count": len(grounded),
        "grounded_token_ratio": round(ratio, 4),
        "required_groups_grounded": concept_grounded,
    }


def evaluate_answer(
    answer: str,
    dataset_item: dict[str, Any],
    reference: dict[str, Any],
    selected_indices: list[int],
) -> dict[str, Any]:
    """Score one answer from text and evidence only."""
    relation = answer_relation(answer, reference)
    matched = matched_groups(reference["required_concept_groups"], answer)
    grounding = grounding_metrics(
        answer, evidence_text(dataset_item, selected_indices), reference
    )
    qualified = any(term in normalize(answer) for term in QUALIFIERS)
    expected = reference["expected_relation"]
    matched_group_grounded = any(
        group in grounding["required_groups_grounded"] for group in matched
    )
    if expected == "OLD_STATE_INVALID":
        semantic_success = (
            relation == "OLD_STATE_INVALID"
            and len(matched) >= int(reference["min_required_groups"])
            and matched_group_grounded
        )
    elif expected == "QUALIFIED_INVALIDATION":
        semantic_success = (
            relation in {"OLD_STATE_INVALID", "UNKNOWN_CURRENT"}
            and len(matched) >= int(reference["min_required_groups"])
            and qualified
            and matched_group_grounded
        )
    else:
        semantic_success = relation == expected
    return {
        "relation": relation,
        "matched_required_groups": matched,
        "grounding": grounding,
        "qualified_uncertainty": qualified,
        "semantic_success": bool(semantic_success),
        "failure_reason": (
            None
            if semantic_success
            else "relation_or_specificity_or_grounding_mismatch"
        ),
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dataset_by_uid(path: Path) -> dict[str, dict[str, Any]]:
    return {item["uid"]: item for item in load_json(path)}


def result_rows(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    return list(payload.get("rows", []))


def score_rows(
    rows: list[dict[str, Any]],
    data: dict[str, dict[str, Any]],
    references: dict[str, Any],
    arm_key: str,
) -> list[dict[str, Any]]:
    """Score a normalized list of answer rows."""
    scored = []
    for row in rows:
        uid = row["uid"]
        answer = row["answer"]
        reference = references[uid]
        scored.append({
            "arm": arm_key,
            "uid": uid,
            "type": reference["type"],
            "answer": answer,
            "selected_indices": row.get("selected_indices", []),
            **evaluate_answer(
                answer,
                data[uid],
                reference,
                row.get("selected_indices", []),
            ),
        })
    return scored


def collect_v3_rows(revision_v3: Path) -> list[dict[str, Any]]:
    """Extract answer-only rows from the frozen v3 model results."""
    rows: list[dict[str, Any]] = []
    main = result_rows(
        revision_v3 / "stale_model_run_20261023_v1" / "STALE_MODEL_RESULTS_V1.json"
    )
    for row in main:
        if row.get("dimension") != "dim1" or row.get("arm") != "oracle_relevant_top2":
            continue
        rows.append({
            "arm": "v3_dev_one_shot",
            "uid": row["uid"],
            "answer": row["call"].get("parsed", {}).get("answer"),
            "selected_indices": row.get("hidden_reference", {}).get("selected_indices", []),
        })
    dev_two = result_rows(
        revision_v3 / "stale_model_two_stage_20261023_v1" / "STALE_MODEL_TWO_STAGE_RESULTS_V1.json"
    )
    for row in dev_two:
        rows.append({
            "arm": "v3_dev_two_stage",
            "uid": row["uid"],
            "answer": (row.get("stage2", {}).get("parsed") or {}).get("answer"),
            "selected_indices": row.get("hidden_reference", {}).get("selected_indices", []),
        })
    confirmation = result_rows(
        revision_v3
        / "stale_model_new_uid_confirmation_20261023_v1"
        / "STALE_MODEL_NEW_UID_CONFIRMATION_RESULTS_V1.json"
    )
    for row in confirmation:
        rows.append({
            "arm": "v3_new_uid_one_shot",
            "uid": row["uid"],
            "answer": (row.get("one_shot", {}).get("parsed") or {}).get("answer"),
            "selected_indices": row.get("hidden_reference", {}).get("selected_indices", []),
        })
        rows.append({
            "arm": "v3_new_uid_two_stage",
            "uid": row["uid"],
            "answer": (row.get("stage2", {}).get("parsed") or {}).get("answer"),
            "selected_indices": row.get("hidden_reference", {}).get("selected_indices", []),
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--revision-v3", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = dataset_by_uid(args.data)
    reference_doc = load_json(args.reference)
    references = reference_doc["items"]
    rows = collect_v3_rows(args.revision_v3)
    scored = []
    for arm in sorted({row["arm"] for row in rows}):
        scored.extend(score_rows(
            [row for row in rows if row["arm"] == arm],
            data,
            references,
            arm,
        ))
    by_arm = {}
    for arm in sorted({row["arm"] for row in scored}):
        group = [row for row in scored if row["arm"] == arm]
        by_arm[arm] = {
            "count": len(group),
            "semantic_success": sum(row["semantic_success"] for row in group),
            "semantic_rate": round(
                sum(row["semantic_success"] for row in group) / len(group), 4
            ),
            "relation_counts": dict(Counter(row["relation"] for row in group)),
            "specificity_failure": sum(
                not row["matched_required_groups"] for row in group
            ),
            "grounding_failure": sum(
                row["grounding"]["grounded_token_ratio"] < 0.25 for row in group
            ),
        }
    controls = []
    for control in reference_doc["derived_controls"]:
        control_ref = {
            "required_concept_groups": [],
            "min_required_groups": 0,
            "old_state_concepts": ["blue sedan", "smartwatch", "light rail", "current location"],
            "expected_relation": control["expected_relation"],
        }
        control_item = {"haystack_session": [[{"role": "user", "content": control["evidence"]}]]}
        controls.append({
            "id": control["id"],
            "accepted": [
                evaluate_answer(answer, control_item, control_ref, [0])["relation"]
                for answer in control["accepted_answers"]
            ],
            "rejected": [
                evaluate_answer(answer, control_item, control_ref, [0])["relation"]
                for answer in control["rejected_answers"]
            ],
        })
    output = {
        "schema": "stale_semantic_reanalysis_v2",
        "date": "2026-10-23",
        "evidence_identity": "POST_HOC_TEXT_AND_EVIDENCE_SCORING_NOT_OFFICIAL_STALE_JUDGE",
        "independence_contract": {
            "ignored_fields": [
                "model state_resolution",
                "model premise_resistance",
                "model action_adaptation",
                "answer prefix",
                "generated state card",
            ],
            "read_fields": ["answer text", "selected source sessions", "semantic reference"],
        },
        "reference_identity": reference_doc["evidence_identity"],
        "summary_by_arm": by_arm,
        "rows": scored,
        "derived_control_sanity": controls,
        "nonclaims": [
            "The semantic reference is AI-assisted development material, not human gold.",
            "This reanalysis does not overwrite frozen proxy counts.",
            "Evidence grounding is a deterministic text check, not a full entailment proof.",
        ],
    }
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"summary_by_arm": by_arm, "controls": controls}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
