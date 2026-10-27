from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research.adaptive_mechanism_20261027_v1.persistent_budget.ledger import (
    BudgetRejected,
    PersistentLedger,
)
from research.adaptive_mechanism_20261027_v1.persistent_budget.runner import (
    GenerationSpec,
    generate_once,
    rescore,
    resume,
)
from research.adaptive_mechanism_20261027_v1.persistent_budget.shared_tools import (
    normalize_answer,
    safe_calculate,
)


FAULT_ROOT = Path(
    "/home/testuser/wzh/research_runs/persistent_budget/"
    "adaptive_mechanism_20261027/fault_injection"
)


def spec(logical_call_id: str, output_dir: Path, **overrides: object) -> GenerationSpec:
    values: dict[str, object] = {
        "logical_call_id": logical_call_id,
        "arm": "direct",
        "payload": {"fixture": logical_call_id},
        "input_tokens_upper_bound": 1000,
        "max_new_tokens": 100,
        "output_dir": output_dir,
    }
    values.update(overrides)
    return GenerationSpec(**values)  # type: ignore[arg-type]


def ok_loader(_spec: GenerationSpec) -> tuple[str, dict[str, int | None]]:
    return '{"answer":"ok"}', {
        "input_tokens": 900,
        "output_tokens": 80,
        "cached_tokens": None,
        "reasoning_tokens": None,
    }


def ok_scorer(raw: dict[str, object], context: dict[str, object]) -> dict[str, object]:
    return {"status": "PASS", "raw_sha256": raw["event_sha256"], "context": context}


class PersistentBudgetFaultTests(unittest.TestCase):
    def setUp(self) -> None:
        FAULT_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=FAULT_ROOT)
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_scoring_throw_keeps_raw_and_rescore_adds_zero_calls(self) -> None:
        ledger = PersistentLedger(self.root / "ledger.jsonl")

        def throw_scorer(raw: dict[str, object], context: dict[str, object]) -> dict[str, object]:
            raise RuntimeError("injected_scoring_failure")

        with self.assertRaisesRegex(RuntimeError, "injected_scoring_failure"):
            generate_once(
                ledger,
                spec("logical-score-crash", self.root / "out-a"),
                model_loader=ok_loader,
                scorer=throw_scorer,
            )
        before = ledger.snapshot_now()
        self.assertEqual(before.physical_attempts, 1)
        self.assertEqual(len(before.raw_responses), 1)
        receipt = rescore(
            ledger,
            scorer=ok_scorer,
            score_output=self.root / "rescore.json",
        )
        after = ledger.snapshot_now()
        self.assertEqual(receipt["new_generation_records"], 0)
        self.assertEqual(after.physical_attempts, before.physical_attempts)
        self.assertEqual(after.events, before.events)

    def test_crash_after_reservation_before_raw_remains_consumed(self) -> None:
        ledger = PersistentLedger(self.root / "ledger.jsonl")

        def crash_loader(_spec: GenerationSpec) -> tuple[str, dict[str, int | None]]:
            raise RuntimeError("injected_model_crash")

        with self.assertRaisesRegex(RuntimeError, "injected_model_crash"):
            generate_once(
                ledger,
                spec("logical-reservation-crash", self.root / "out-b"),
                model_loader=crash_loader,
                scorer=ok_scorer,
            )
        snapshot = ledger.snapshot_now()
        self.assertEqual(snapshot.physical_attempts, 1)
        self.assertEqual(len(snapshot.raw_responses), 0)
        self.assertEqual(len(snapshot.uncertain_reservations), 1)
        self.assertEqual(snapshot.consumed_tokens, 1100)
        stop = resume(
            ledger,
            "logical-reservation-crash",
            scorer=ok_scorer,
            score_output=self.root / "resume-stop.json",
        )
        self.assertEqual(stop["status"], "UNCERTAIN_RESERVATION_STOP")
        self.assertFalse(stop["model_loaded"])
        self.assertEqual(ledger.snapshot_now().physical_attempts, 1)

    def test_crash_between_calls_preserves_every_earlier_raw(self) -> None:
        ledger = PersistentLedger(self.root / "ledger.jsonl")
        generate_once(
            ledger,
            spec("logical-before-crash", self.root / "out-1"),
            model_loader=ok_loader,
            scorer=ok_scorer,
        )

        def crash_loader(_spec: GenerationSpec) -> tuple[str, dict[str, int | None]]:
            raise RuntimeError("injected_second_call_crash")

        with self.assertRaisesRegex(RuntimeError, "injected_second_call_crash"):
            generate_once(
                ledger,
                spec("logical-at-crash", self.root / "out-2"),
                model_loader=crash_loader,
                scorer=ok_scorer,
            )
        snapshot = ledger.snapshot_now()
        self.assertEqual(snapshot.physical_attempts, 2)
        self.assertEqual(len(snapshot.raw_responses), 1)
        self.assertEqual(snapshot.raw_responses[0]["logical_call_id"], "logical-before-crash")
        self.assertEqual(snapshot.raw_responses[0]["response_text"], '{"answer":"ok"}')

    def test_output_directory_change_cannot_reset_ledger(self) -> None:
        ledger = PersistentLedger(self.root / "ledger.jsonl")
        generate_once(
            ledger,
            spec("logical-dir-a", self.root / "directory-a"),
            model_loader=ok_loader,
            scorer=ok_scorer,
        )
        generate_once(
            ledger,
            spec("logical-dir-b", self.root / "directory-b"),
            model_loader=ok_loader,
            scorer=ok_scorer,
        )
        snapshot = ledger.snapshot_now()
        self.assertEqual(snapshot.physical_attempts, 2)
        self.assertEqual(len(snapshot.raw_responses), 2)
        self.assertEqual(
            {event["output_dir"] for event in snapshot.reservations},
            {str(self.root / "directory-a"), str(self.root / "directory-b")},
        )

    def test_attempt_37_rejected_before_model_loader(self) -> None:
        ledger = PersistentLedger(self.root / "ledger.jsonl")
        loader_calls = 0

        def counting_loader(_spec: GenerationSpec) -> tuple[str, dict[str, int | None]]:
            nonlocal loader_calls
            loader_calls += 1
            return ok_loader(_spec)

        for index in range(36):
            generate_once(
                ledger,
                spec(f"logical-cap-{index}", self.root / f"cap-{index}"),
                model_loader=counting_loader,
                scorer=ok_scorer,
            )
        self.assertEqual(loader_calls, 36)
        with self.assertRaisesRegex(BudgetRejected, "physical_attempt_cap"):
            generate_once(
                ledger,
                spec("logical-cap-37", self.root / "cap-37"),
                model_loader=counting_loader,
                scorer=ok_scorer,
            )
        self.assertEqual(loader_calls, 36)
        self.assertEqual(ledger.snapshot_now().physical_attempts, 36)

    def test_token_cap_successor_rejected_before_model_loader(self) -> None:
        ledger = PersistentLedger(self.root / "ledger.jsonl")
        loader_calls = 0

        def near_cap_loader(
            _spec: GenerationSpec,
        ) -> tuple[str, dict[str, int | None]]:
            nonlocal loader_calls
            loader_calls += 1
            return '{"answer":"ok"}', {
                "input_tokens": 235000,
                "output_tokens": 4500,
                "cached_tokens": None,
                "reasoning_tokens": None,
            }

        generate_once(
            ledger,
            spec(
                "logical-token-1",
                self.root / "token-1",
                input_tokens_upper_bound=235000,
                max_new_tokens=5000,
            ),
            model_loader=near_cap_loader,
            scorer=ok_scorer,
        )
        self.assertEqual(loader_calls, 1)
        with self.assertRaisesRegex(BudgetRejected, "token_cap_projection"):
            generate_once(
                ledger,
                spec(
                    "logical-token-2",
                    self.root / "token-2",
                    input_tokens_upper_bound=4000,
                    max_new_tokens=2000,
                ),
                model_loader=near_cap_loader,
                scorer=ok_scorer,
            )
        self.assertEqual(loader_calls, 1)
        snapshot = ledger.snapshot_now()
        self.assertEqual(snapshot.physical_attempts, 1)
        self.assertEqual(snapshot.consumed_tokens, 239500)

    def test_shared_normalization_and_calculator(self) -> None:
        self.assertEqual(normalize_answer("  Net   Sales. "), "net sales")
        self.assertEqual(safe_calculate("(9660+11191)/2"), 10425.5)
        with self.assertRaises(ValueError):
            safe_calculate("__import__('os').system('id')")


if __name__ == "__main__":
    unittest.main()
