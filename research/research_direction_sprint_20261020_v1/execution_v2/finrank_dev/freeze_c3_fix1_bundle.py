#!/usr/bin/env python3
"""Freeze C3 FIX1 after correcting the fixture bundle entry path."""

from __future__ import annotations

import json

from finrank_contract import (
    PACKAGE,
    load_object,
    sha256_file,
    write_json,
)


def main() -> int:
    old_bundle = load_object(PACKAGE / "BUNDLE_C3_B0_V4.json")
    run_card = {
        **load_object(PACKAGE / "RUN_CARD_C3_B0_V4.json"),
        "schema": "finrank_c3_run_card_b0_v4_fix1_v1",
        "status": "FROZEN_BEFORE_C3_FIXTURES_FIX1",
        "supersedes_bundle_sha256": sha256_file(
            PACKAGE / "BUNDLE_C3_B0_V4.json"
        ),
        "fix_scope": (
            "Correct the C3 fixture bundle entry path only; scientific task, "
            "reference, visibility, scorer, model and generation policy "
            "unchanged."
        ),
    }
    write_json(PACKAGE / "RUN_CARD_C3_B0_V4_FIX1.json", run_card)
    source_inputs = {
        **old_bundle["source_inputs"],
        "BUNDLE_C3_B0_V4.json": sha256_file(
            PACKAGE / "BUNDLE_C3_B0_V4.json"
        ),
        "B0_V3_POSTHOC_SCORER_V3.json": sha256_file(
            PACKAGE
            / "results"
            / "B0_V3_EQUAL_VISIBILITY"
            / "B0_RESULT_POSTHOC_SCORER_V3.json"
        ),
    }
    artifacts = {}
    for name in (
        "finrank_contract.py",
        "freeze_c3_fix1_bundle.py",
        "qualify_runtime.py",
        "run_fixtures.py",
        "run_b0.py",
        "run_strong_rule.py",
        "rescore_b0_v3_posthoc_v3.py",
        "c3_red_green_unit_fixture.py",
        "c3_red_green_derivation_fixture.py",
        "TASKS_ACTOR_V3.json",
        "REFERENCES_V3.json",
        "TOOL_SCHEMAS_V1.json",
        "RUNTIME_IDENTITY_OVERRIDE_V1.json",
        "RUN_CARD_C3_B0_V4_FIX1.json",
    ):
        artifacts[name] = sha256_file(PACKAGE / name)
    bundle = {
        "schema": "finrank_c3_b0_v4_bundle_v2",
        "status": "FROZEN_BEFORE_C3_FIXTURES_FIX1",
        "source_inputs": source_inputs,
        "artifacts": artifacts,
    }
    write_json(PACKAGE / "BUNDLE_C3_B0_V4_FIX1.json", bundle)
    print(
        json.dumps(
            {
                "status": "FROZEN",
                "bundle_sha256": sha256_file(
                    PACKAGE / "BUNDLE_C3_B0_V4_FIX1.json"
                ),
                "artifacts": len(artifacts),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
