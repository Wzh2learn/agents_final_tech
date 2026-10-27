from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research.adaptive_mechanism_20261027_v1.persistent_budget import (
    test_persistent_budget as base_tests,
)
from research.adaptive_mechanism_20261027_v1.persistent_budget.ledger import (
    PersistentLedger,
)
from research.adaptive_mechanism_20261027_v1.persistent_budget.runner import (
    generate_once,
    resume,
)


FAULT_ROOT = Path(__file__).resolve().parent / ".fault_tmp"
base_tests.FAULT_ROOT = FAULT_ROOT


class WordNewFamilyAdditionalFaults(unittest.TestCase):
    def setUp(self) -> None:
        FAULT_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=FAULT_ROOT)
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_timeout_reservation_remains_consumed_and_resume_stops(self) -> None:
        ledger = PersistentLedger(self.root / "ledger.jsonl")
        loader_calls = 0

        def timeout_loader(spec: object) -> tuple[str, dict[str, int | None]]:
            nonlocal loader_calls
            loader_calls += 1
            raise TimeoutError("injected_timeout")

        with self.assertRaisesRegex(TimeoutError, "injected_timeout"):
            generate_once(
                ledger,
                base_tests.spec("word-timeout", self.root / "timeout-out"),
                model_loader=timeout_loader,
                scorer=base_tests.ok_scorer,
            )
        snapshot = ledger.snapshot_now()
        self.assertEqual(snapshot.physical_attempts, 1)
        self.assertEqual(len(snapshot.uncertain_reservations), 1)
        self.assertEqual(snapshot.consumed_tokens, 1100)
        stop = resume(
            ledger,
            "word-timeout",
            scorer=base_tests.ok_scorer,
            score_output=self.root / "timeout-stop.json",
        )
        self.assertEqual(stop["status"], "UNCERTAIN_RESERVATION_STOP")
        self.assertFalse(stop["model_loaded"])
        self.assertEqual(loader_calls, 1)

    def test_restart_preserves_ledger_and_prevents_duplicate_logical_call(self) -> None:
        ledger_path = self.root / "ledger.jsonl"
        first = PersistentLedger(ledger_path)
        generate_once(
            first,
            base_tests.spec("word-restart", self.root / "before-restart"),
            model_loader=base_tests.ok_loader,
            scorer=base_tests.ok_scorer,
        )
        before = first.snapshot_now()
        second = PersistentLedger(ledger_path)
        after = second.snapshot_now()
        self.assertEqual(after.events, before.events)
        self.assertEqual(after.physical_attempts, 1)
        with self.assertRaisesRegex(Exception, "physical_attempt_cap|already_has_raw"):
            generate_once(
                second,
                base_tests.spec("word-restart", self.root / "after-restart"),
                model_loader=base_tests.ok_loader,
                scorer=base_tests.ok_scorer,
            )
        self.assertEqual(second.snapshot_now().physical_attempts, 1)

    def test_reservation_matches_exact_input_plus_max_new(self) -> None:
        ledger = PersistentLedger(self.root / "ledger.jsonl")
        spec = base_tests.spec(
            "word-token-bound",
            self.root / "token-bound",
            input_tokens_upper_bound=6000,
            max_new_tokens=512,
        )
        generate_once(
            ledger,
            spec,
            model_loader=base_tests.ok_loader,
            scorer=base_tests.ok_scorer,
        )
        reservation = ledger.snapshot_now().reservations[0]
        self.assertEqual(reservation["reserved_input_tokens"], 6000)
        self.assertEqual(reservation["reserved_output_tokens"], 512)
        self.assertEqual(
            reservation["reserved_input_tokens"]
            + reservation["reserved_output_tokens"],
            6512,
        )

    def test_rescore_never_invokes_a_model_loader(self) -> None:
        ledger = PersistentLedger(self.root / "ledger.jsonl")
        generate_once(
            ledger,
            base_tests.spec("word-rescore", self.root / "rescore-out"),
            model_loader=base_tests.ok_loader,
            scorer=base_tests.ok_scorer,
        )
        before = ledger.snapshot_now()
        receipt = base_tests.rescore(
            ledger,
            scorer=base_tests.ok_scorer,
            score_output=self.root / "rescore.json",
        )
        after = ledger.snapshot_now()
        self.assertEqual(receipt["model_loaded"], False)
        self.assertEqual(receipt["new_generation_records"], 0)
        self.assertEqual(after.events, before.events)


if __name__ == "__main__":
    unittest.main()
