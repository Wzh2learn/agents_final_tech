"""Build the pre-generation mechanism freeze and visible-only prompt plan."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
PANEL_PATH = ROOT / "exposure" / "PANEL_FREEZE.json"
BASELINE_PATH = ROOT / "baseline" / "results" / "ZERO_MODEL_BASELINE.json"
SCORER_PATH = ROOT / "scoring_v3" / "scorer.py"
SCORER_TESTS_PATH = ROOT / "scoring_v3" / "test_scoring_v3.py"
SHARED_TOOLS_PATH = (
    REPO
    / "research"
    / "adaptive_mechanism_20261027_v1"
    / "persistent_budget"
    / "shared_tools.py"
)
LEDGER_PATH = (
    REPO
    / "research"
    / "adaptive_mechanism_20261027_v1"
    / "persistent_budget"
    / "ledger.py"
)
RUNNER_PATH = (
    REPO
    / "research"
    / "adaptive_mechanism_20261027_v1"
    / "persistent_budget"
    / "runner.py"
)
PRIOR_PREREG_PATH = (
    REPO
    / "research"
    / "adaptive_mechanism_20261027_v1"
    / "diagnostic_panel"
    / "DIAGNOSTIC_PANEL_PREREGISTRATION.json"
)
NEAREST_PATHS = [
    REPO / "research" / "paper_e_contribution_reassessment_v1" / "NEAREST_WORK_COMPARISON.md",
    REPO / "research" / "paper_e_contribution_reassessment_v1" / "PAPER_E_PUBLIC_CASE_AUDIT.md",
    REPO / "research" / "paper_e_contribution_reassessment_v1" / "REUSE_TASK_REDESIGN.md",
]
PROMPTS_PATH = ROOT / "mechanism" / "PLANNED_PROMPTS.jsonl"
FREEZE_PATH = ROOT / "mechanism" / "MECHANISM_FREEZE.json"
NEAREST_RECEIPT_PATH = ROOT / "mechanism" / "NEAREST_WORK_COMPARISON.json"
NEAREST_MD_PATH = ROOT / "mechanism" / "NEAREST_WORK_COMPARISON.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def visible_context(reference: dict[str, object]) -> str:
    paragraphs = reference["paragraphs"]
    paragraph_lines = [
        f"P{index}: {item['text']}"
        for index, item in enumerate(paragraphs, start=1)
    ]
    return (
        "VISIBLE QUESTION\n"
        f"{reference['question']}\n\n"
        "VISIBLE PARAGRAPHS\n"
        + "\n".join(paragraph_lines)
        + "\n\nVISIBLE TABLE\n"
        + str(reference["table_text"])
    )


FINAL_CONTRACT = """
Return exactly one JSON object with exactly these six keys:
answer, numeric_value, unit, evidence_refs, unknown, clarification.
answer is a non-empty string or a non-empty list of strings.
numeric_value is a finite number or null.
unit is a non-empty string.
evidence_refs is a list of visible identifiers only.
unknown is a boolean.
clarification is a string.
If the required visible evidence is absent or insufficient, set unknown=true,
answer="UNKNOWN", numeric_value=null, unit="UNKNOWN", evidence_refs=[], and
provide a nonempty clarification. Do not emit Markdown or any other text.
""".strip()


TYPED_CONTRACT = """
Return exactly one JSON object with exactly these keys:
answer_type, answer, operands, program, operation, unit, evidence_refs,
unknown, clarification.
answer_type is one of arithmetic, count, multi-span, span, or other.
answer is a non-empty string or a non-empty list of strings.
operands is a list of objects with operand_id, evidence_ref, and value.
program is the deterministic expression to execute; use an empty string when
no numeric expression applies.
operation is one of add, subtract, multiply, divide, percent_change, mean,
compare, count, none.
unit is a non-empty string.
evidence_refs is a list of visible identifiers only.
unknown is a boolean and clarification is a string.
If required visible evidence is absent, use the UNKNOWN envelope from the
shared contract: unknown=true, answer="UNKNOWN", numeric_value=null,
unit="UNKNOWN", evidence_refs=[], and a nonempty clarification.
Do not emit Markdown or any other text.
""".strip()


M_BINDING_CONTRACT = """
Return exactly the typed object above plus exactly one additional key,
bindings. bindings is a list with one object for every operand or evidence
item used. Each binding has evidence_ref, row, period, role, and unit.
Use a visible table row number for row; use the visible header or source
period for period; use the visible column or paragraph role for role; use the
visible table or paragraph unit for unit. Use null only when a field is not
present in the visible source. Bind every field from this prompt before the
shared calculator executes the program. Do not invent hidden row IDs,
periods, roles, units, or reference answers.
""".strip()


def main() -> int:
    panel = json.loads(PANEL_PATH.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    prior = json.loads(PRIOR_PREREG_PATH.read_text(encoding="utf-8"))
    references = panel["references"]
    planned: list[dict[str, object]] = []
    arm_contracts = {
        "D": {
            "instruction": "Answer directly from the visible evidence under the final delivery contract.",
            "output_contract": FINAL_CONTRACT,
            "tools": "same read-only visible context; no hidden references",
        },
        "T": {
            "instruction": "Infer a visible-only typed representation, construct a deterministic program, and let the shared safe calculator execute it before final normalization.",
            "output_contract": TYPED_CONTRACT,
            "tools": "same read-only visible context plus shared normalization and safe calculator",
        },
        "M": {
            "instruction": "Infer the same typed representation, explicitly bind row, period, role, and unit from visible evidence, validate every binding deterministically, and only then let the shared safe calculator execute it.",
            "output_contract": TYPED_CONTRACT + "\n\n" + M_BINDING_CONTRACT,
            "tools": "same read-only visible context, shared normalization and safe calculator, plus deterministic binding validation",
        },
    }
    common = (
        "Use only the visible question, paragraphs, and table in this prompt.\n"
        "Do not use or infer a gold answer, gold answer type, gold program,\n"
        "source requirement, correct row IDs, hidden units, reference answer,\n"
        "UID branch, or any information outside this prompt.\n"
        "Use only visible evidence identifiers of the form P<n>, TABLE:C<n>,\n"
        "TABLE:R<n>, or TABLE:R<n>:C<n>.\n"
    )
    for arm in ("D", "T", "M"):
        for reference in references:
            contract = arm_contracts[arm]
            user_text = (
                common
                + "\nVISIBLE CONTEXT\n"
                + visible_context(reference)
                + "\n\nARM INSTRUCTION\n"
                + str(contract["instruction"])
                + "\n\nOUTPUT CONTRACT\n"
                + str(contract["output_contract"])
            )
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a deployment-facing table question answering actor. "
                        "Follow the user contract exactly."
                    ),
                },
                {"role": "user", "content": user_text},
            ]
            planned.append(
                {
                    "schema": "word_new_family_planned_prompt_v1",
                    "run_id": "word-new-family-20261027-a",
                    "logical_call_id": (
                        f"word-new-family-20261027-a:{arm}:"
                        f"{reference['question_uid']}"
                    ),
                    "arm": arm,
                    "family_id": reference["family_id"],
                    "question_uid": reference["question_uid"],
                    "messages": messages,
                    "prompt_sha256": hashlib.sha256(
                        json.dumps(
                            messages,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    ).hexdigest(),
                    "visible_only": True,
                    "hidden_fields_excluded": [
                        "answer",
                        "answer_type",
                        "program",
                        "source_requirement",
                        "required_evidence",
                        "unit_reference",
                        "family_selection_reason",
                        "baseline_output",
                    ],
                }
            )
    with PROMPTS_PATH.open("w", encoding="utf-8") as handle:
        for row in planned:
            handle.write(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            )

    nearest_rows = [
        {
            "id": "FinRank",
            "source": "PAPER_E_PUBLIC_CASE_AUDIT.md and NEAREST_WORK_COMPARISON.md",
            "overlap": "Provenance-sensitive evidence discrimination and source identity.",
            "boundary": "The present diagnostic does not propose a new financial-QA benchmark.",
        },
        {
            "id": "VeriFin",
            "source": "PAPER_E_PUBLIC_CASE_AUDIT.md and NEAREST_WORK_COMPARISON.md",
            "overlap": "Source-grounded claim verification with period, unit, line-item and formula binding.",
            "boundary": "Arithmetic checking alone is not presented as verification.",
        },
        {
            "id": "Same-Number Citation Swaps",
            "source": "PAPER_E_PUBLIC_CASE_AUDIT.md and REUSE_TASK_REDESIGN.md",
            "overlap": "Separates numeric correctness from cited-role support.",
            "boundary": "The Scoring V3 role control is not claimed as a new metric.",
        },
    ]
    nearest_receipt = {
        "schema": "word_new_family_nearest_work_receipt_v1",
        "reading_scope": "Only the three pre-existing project notes named by the task.",
        "strongest_neighbors": nearest_rows,
        "counterexample": (
            "Ordinary program-aided reasoning and typed schemas are established "
            "capabilities and are a counterexample to any novelty claim for T."
        ),
        "single_mechanism_difference": (
            "M alone adds deterministic row/period/role/unit binding validation "
            "before execution; T already has typed evidence and a program."
        ),
        "source_hashes": {str(path.relative_to(REPO)): sha256(path) for path in NEAREST_PATHS},
        "model_output_seen": False,
    }
    write_json(NEAREST_RECEIPT_PATH, nearest_receipt)
    NEAREST_MD_PATH.write_text(
        "# Nearest Work Receipt\n\n"
        "- FinRank: provenance-sensitive evidence discrimination and source identity.\n"
        "- VeriFin: source-grounded claim verification with period, unit, line-item and formula binding.\n"
        "- Same-Number Citation Swaps: numeric correctness versus cited-role support.\n\n"
        "**Counterexample:** ordinary program-aided reasoning and typed schemas are established and are not novel.\n\n"
        "**Single tested difference:** M alone adds deterministic row/period/role/unit binding validation before execution.\n",
        encoding="utf-8",
    )
    freeze = {
        "schema": "word_new_family_mechanism_freeze_v1",
        "task_id": "word-scoring-new-family-a-20261027",
        "run_id": "word-new-family-20261027-a",
        "status": "FROZEN_PRE_MODEL_OUTPUT",
        "frozen_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "source_identity_label": panel["source_identity_label"],
        "claim_boundary": panel["claim_boundary"],
        "selected_uid_count": len(references),
        "selected_uids": [row["question_uid"] for row in references],
        "selected_family_ids": [row["family_id"] for row in references],
        "baseline": {
            "status": baseline["status"],
            "model_calls": baseline["model_calls"],
            "path": str(BASELINE_PATH.relative_to(REPO)),
            "sha256": sha256(BASELINE_PATH),
        },
        "scoring_v3": {
            "path": str(SCORER_PATH.relative_to(REPO)),
            "sha256": sha256(SCORER_PATH),
            "tests_path": str(SCORER_TESTS_PATH.relative_to(REPO)),
            "tests_sha256": sha256(SCORER_TESTS_PATH),
        },
        "shared_tools": {
            "path": str(SHARED_TOOLS_PATH.relative_to(REPO)),
            "sha256": sha256(SHARED_TOOLS_PATH),
        },
        "persistent_budget": {
            "ledger_path": "/home/testuser/wzh/research_runs/persistent_budget/word_new_family_20261027/ledger.jsonl",
            "ledger_module_path": str(LEDGER_PATH.relative_to(REPO)),
            "ledger_module_sha256": sha256(LEDGER_PATH),
            "runner_module_path": str(RUNNER_PATH.relative_to(REPO)),
            "runner_module_sha256": sha256(RUNNER_PATH),
        },
        "model": {
            "id": prior["model"]["id"],
            "local_path": prior["model"]["local_path"],
            "upstream_revision": prior["model"]["upstream_revision"],
            "file_manifest_sha256": prior["model"]["file_manifest_sha256"],
            "adapter_path": None,
            "training_runs": 0,
        },
        "decoding": prior["decoding"],
        "output_contract": {
            "direct_final_keys": [
                "answer",
                "numeric_value",
                "unit",
                "evidence_refs",
                "unknown",
                "clarification",
            ],
            "typed_keys": [
                "answer_type",
                "answer",
                "operands",
                "program",
                "operation",
                "unit",
                "evidence_refs",
                "unknown",
                "clarification",
            ],
            "binding_key": "bindings",
            "binding_validation": "Every M binding must exist in the visible source and match its visible row, period, role, and unit before execution.",
        },
        "arms": arm_contracts,
        "planned_prompts": {
            "path": str(PROMPTS_PATH.relative_to(REPO)),
            "sha256": sha256(PROMPTS_PATH),
            "count": len(planned),
        },
        "resource_budget": prior["resource_budget"],
        "metrics": [
            "complete_delivery",
            "correct_repair",
            "damage",
            "strict_failure",
            "reasonable_unknown",
            "unnecessary_refusal",
            "pending",
            "numeric_correctness",
            "formula_correctness",
            "visible_citation_support",
            "direct_typed_binding_differences",
            "alternative_explanations",
            "total_cost",
        ],
        "frozen_predictions": [
            "D will be weakest on complete typed delivery and deterministic formula execution.",
            "T will improve typed/formula delivery relative to D when visible evidence is sufficient.",
            "M will differ from T only on binding-specific natural failures; formatting-only or abstention-only changes are not repairs.",
        ],
        "stop_rules": [
            "Stop M after generation if T and M match on complete delivery, V3 status, numeric correctness, formula correctness, and citation support for every UID.",
            "Prepare but do not run an independent confirmation card only when M repairs corresponding natural failures beyond formatting or abstention.",
            "If all arms fail, separate model, reference and interface failures and do not train an adapter.",
            "No confirmation, judge, training, paid API, production call, Memory writeback, public release, or external contact.",
            "Reject attempt 37 or a token projection above 240000 before model loading.",
        ],
        "nearest_work_receipt": {
            "path": str(NEAREST_RECEIPT_PATH.relative_to(REPO)),
            "sha256": sha256(NEAREST_RECEIPT_PATH),
        },
        "model_output_seen": False,
    }
    write_json(FREEZE_PATH, freeze)
    print(
        json.dumps(
            {
                "status": freeze["status"],
                "planned_calls": len(planned),
                "freeze_sha256": sha256(FREEZE_PATH),
                "prompts_sha256": sha256(PROMPTS_PATH),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
