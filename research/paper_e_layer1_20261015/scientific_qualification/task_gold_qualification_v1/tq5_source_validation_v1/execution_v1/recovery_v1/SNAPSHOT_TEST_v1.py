#!/usr/bin/env python3
"""Focused tests for TQ-5 snapshot enforcement and invalid decision rendering."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import chain_analyze
import tq5_snapshot_entry as entry


class SnapshotTests(unittest.TestCase):
    def test_snapshot_hashes_match(self) -> None:
        manifest = entry.verify_snapshot()
        self.assertGreaterEqual(len(manifest["files"]), 7)

    def test_snapshot_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = entry.load_manifest()
            for item in manifest["files"]:
                target = root / item["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(entry.HERE / item["path"], target)
            shutil.copy2(entry.MANIFEST_PATH, root / entry.MANIFEST_PATH.name)
            with (root / "chain_runner.py").open("a", encoding="utf-8") as handle:
                handle.write("\n# deliberate test tamper\n")
            with self.assertRaises(RuntimeError):
                entry.verify_snapshot(root)

    def test_formal_run_requires_linux_root(self) -> None:
        manifest = entry.load_manifest()
        child = ["--config", str(entry.HERE / entry.CONFIG_NAME), "--root", "D:\\wrong", "--run"]
        with self.assertRaises(ValueError):
            entry.validate_invocation("run", child, manifest)

    def test_parse_failure_displays_invalid(self) -> None:
        row = {"decision": None, "ledger_state": "done", "parse_error": "json_parse_error"}
        self.assertEqual(chain_analyze.display_decision(row), "invalid")
        done = {"decision": None, "ledger_state": "done", "parse_error": None}
        self.assertEqual(chain_analyze.display_decision(done), "invalid")
        accepted = {"decision": "accept", "ledger_state": "done", "parse_error": None}
        self.assertEqual(chain_analyze.display_decision(accepted), "accept")


if __name__ == "__main__":
    unittest.main()
