"""Separate generate, resume and rescore entry points over one global ledger."""

from __future__ import annotations

import argparse
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .ledger import BudgetRejected, BudgetSnapshot, PersistentLedger


DEFAULT_LEDGER = Path(
    "/home/testuser/wzh/research_runs/persistent_budget/"
    "adaptive_mechanism_20261027/ledger.jsonl"
)
ModelLoader = Callable[[dict[str, Any]], tuple[str, dict[str, int | None]]]
Scorer = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class GenerationSpec:
    logical_call_id: str
    arm: str
    payload: dict[str, Any]
    input_tokens_upper_bound: int
    max_new_tokens: int
    output_dir: Path


def import_object(path: str) -> Any:
    module_name, attribute = path.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, attribute)


def default_local_model_loader(
    spec: GenerationSpec,
) -> tuple[str, dict[str, int | None]]:
    raise RuntimeError(
        "No implicit model loader is invoked by tests; provide an explicit "
        "reviewed local loader only after all budget guards pass."
    )


def generate_once(
    ledger: PersistentLedger,
    spec: GenerationSpec,
    *,
    model_loader: ModelLoader,
    scorer: Scorer,
    score_output: Path | None = None,
) -> dict[str, Any]:
    reservation = ledger.reserve(
        logical_call_id=spec.logical_call_id,
        arm=spec.arm,
        output_dir=spec.output_dir,
        input_tokens_upper_bound=spec.input_tokens_upper_bound,
        max_new_tokens=spec.max_new_tokens,
    )
    response_text, usage = model_loader(spec)
    raw_event = ledger.append_raw(
        physical_attempt_id=reservation["physical_attempt_id"],
        logical_call_id=spec.logical_call_id,
        response_text=response_text,
        usage=usage,
    )
    score = scorer(raw_event, {"arm": spec.arm, "payload": spec.payload})
    receipt = {
        "schema": "adaptive_mechanism_generate_receipt_v1",
        "logical_call_id": spec.logical_call_id,
        "physical_attempt_id": reservation["physical_attempt_id"],
        "reservation_event_sha256": reservation["event_sha256"],
        "raw_event_sha256": raw_event["event_sha256"],
        "score": score,
        "scored_only_after_raw_fsync": True,
        "output_dir": str(spec.output_dir),
    }
    if score_output is not None:
        score_output.parent.mkdir(parents=True, exist_ok=True)
        score_output.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return receipt


def _find_logical(
    snapshot: BudgetSnapshot,
    logical_call_id: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    reservations = [
        event
        for event in snapshot.reservations
        if event["logical_call_id"] == logical_call_id
    ]
    raws = [
        event
        for event in snapshot.raw_responses
        if event["logical_call_id"] == logical_call_id
    ]
    return (reservations[-1] if reservations else None, raws[-1] if raws else None)


def resume(
    ledger: PersistentLedger,
    logical_call_id: str,
    *,
    scorer: Scorer,
    score_output: Path | None = None,
) -> dict[str, Any]:
    snapshot = ledger.snapshot_now()
    reservation, raw = _find_logical(snapshot, logical_call_id)
    if reservation is None:
        raise BudgetRejected("logical_call_not_reserved")
    if raw is None:
        return {
            "schema": "adaptive_mechanism_resume_stop_v1",
            "status": "UNCERTAIN_RESERVATION_STOP",
            "logical_call_id": logical_call_id,
            "physical_attempt_id": reservation["physical_attempt_id"],
            "consumed": True,
            "model_loaded": False,
            "new_generation_records": 0,
        }
    score = scorer(raw, {"logical_call_id": logical_call_id})
    receipt = {
        "schema": "adaptive_mechanism_resume_receipt_v1",
        "status": "SCORED_EXISTING_RAW",
        "logical_call_id": logical_call_id,
        "physical_attempt_id": raw["physical_attempt_id"],
        "score": score,
        "model_loaded": False,
        "new_generation_records": 0,
    }
    if score_output is not None:
        score_output.parent.mkdir(parents=True, exist_ok=True)
        score_output.write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return receipt


def rescore(
    ledger: PersistentLedger,
    *,
    scorer: Scorer,
    score_output: Path,
) -> dict[str, Any]:
    before = ledger.snapshot_now()
    rows: list[dict[str, Any]] = []
    for raw in before.raw_responses:
        rows.append(
            {
                "physical_attempt_id": raw["physical_attempt_id"],
                "logical_call_id": raw["logical_call_id"],
                "raw_event_sha256": raw["event_sha256"],
                "score": scorer(raw, {"mode": "rescore"}),
            }
        )
    after = ledger.snapshot_now()
    if after.physical_attempts != before.physical_attempts or after.events != before.events:
        raise RuntimeError("rescore_mutated_generation_ledger")
    receipt = {
        "schema": "adaptive_mechanism_rescore_receipt_v1",
        "status": "COMPLETE",
        "model_loaded": False,
        "new_generation_records": 0,
        "physical_attempts_before": before.physical_attempts,
        "physical_attempts_after": after.physical_attempts,
        "raw_rows_scored": len(rows),
        "rows": rows,
    }
    score_output.parent.mkdir(parents=True, exist_ok=True)
    score_output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("generate", "resume", "rescore"), required=True)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--logical-call-id")
    parser.add_argument("--arm")
    parser.add_argument("--payload-json", default="{}")
    parser.add_argument("--input-tokens-upper-bound", type=int)
    parser.add_argument("--max-new-tokens", type=int)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--model-loader")
    parser.add_argument("--scorer", required=True)
    parser.add_argument("--score-output", type=Path, required=True)
    args = parser.parse_args()

    ledger = PersistentLedger(args.ledger)
    scorer = import_object(args.scorer)
    if args.mode == "rescore":
        rescore(ledger, scorer=scorer, score_output=args.score_output)
        print(
            json.dumps(
                {"mode": "rescore", "model_loaded": False, "new_generation_records": 0},
                sort_keys=True,
            )
        )
        return 0
    if not args.logical_call_id:
        parser.error("--logical-call-id is required")
    if args.mode == "resume":
        resume(
            ledger,
            args.logical_call_id,
            scorer=scorer,
            score_output=args.score_output,
        )
        print(
            json.dumps(
                {"mode": "resume", "model_loaded": False, "new_generation_records": 0},
                sort_keys=True,
            )
        )
        return 0
    if not args.model_loader or not args.arm or args.output_dir is None:
        parser.error("generate requires --model-loader, --arm and --output-dir")
    if args.input_tokens_upper_bound is None or args.max_new_tokens is None:
        parser.error("generate requires token bounds")
    spec = GenerationSpec(
        logical_call_id=args.logical_call_id,
        arm=args.arm,
        payload=json.loads(args.payload_json),
        input_tokens_upper_bound=args.input_tokens_upper_bound,
        max_new_tokens=args.max_new_tokens,
        output_dir=args.output_dir,
    )
    generate_once(
        ledger,
        spec,
        model_loader=import_object(args.model_loader),
        scorer=scorer,
        score_output=args.score_output,
    )
    print(
        json.dumps(
            {"mode": "generate", "logical_call_id": spec.logical_call_id},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
