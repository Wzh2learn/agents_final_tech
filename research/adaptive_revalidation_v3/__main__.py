"""CLI entry points for budget replay and replay-bound receipt verification."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from .receipt import build_receipt, verify_receipt, write_receipt
from .runner import experiment_as_dict, run_budget_sweep


def _root() -> Path:
    return Path(__file__).resolve().parent


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="adaptive_revalidation_v3")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="run deterministic isolated-process policy replay for budgets 0-9",
    )
    run_parser.add_argument("--output", type=Path, default=None)

    receipt_parser = subparsers.add_parser("receipt", help="write a hash-bound receipt")
    receipt_parser.add_argument("--output", type=Path, default=_root() / "result_receipt.json")
    receipt_parser.add_argument("--test-command", required=True)
    receipt_parser.add_argument("--test-exit-code", type=int, required=True)
    receipt_parser.add_argument("--test-passed", type=int, required=True)
    receipt_parser.add_argument("--test-failed", type=int, required=True)
    receipt_parser.add_argument("--test-skipped", type=int, default=0)

    verify_parser = subparsers.add_parser(
        "verify-receipt",
        help="recompute replay and verify source/result/summary integrity",
    )
    verify_parser.add_argument("--input", type=Path, required=True)

    args = parser.parse_args(argv)
    root = _root()
    if args.command == "run":
        result = experiment_as_dict(run_budget_sweep())
        text = json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
        if args.output is None:
            print(text, end="")
        else:
            with args.output.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
        return 0
    if args.command == "receipt":
        payload = build_receipt(
            root,
            test_command=args.test_command,
            test_exit_code=args.test_exit_code,
            test_passed=args.test_passed,
            test_failed=args.test_failed,
            test_skipped=args.test_skipped,
        )
        write_receipt(args.output, payload)
        print(args.output.resolve())
        return 0
    verification = verify_receipt(args.input, root)
    print(json.dumps(verification, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
