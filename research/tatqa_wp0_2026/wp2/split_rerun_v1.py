#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = ROOT / (
    "data/research/tatqa_wp0_2026/origin_manifest.json"
)
ITEMS_V1_PATH = ROOT / (
    "data/research/tatqa_wp0_2026/candidate_items_v1.json"
)
TRACKED_RECEIPT_PATH = (
    ROOT / "research/tatqa_wp0_2026/WP2_SPLIT_DRYRUN_RECEIPT.json"
)
OUTPUT_PATH = ROOT / (
    "research/tatqa_wp0_2026/wp2/SPLIT_RERUN_RECEIPT.json"
)
SEED = "wp2-split-dryrun-20261013"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def replay_payload_bytes() -> bytes:
    manifest = load_json(MANIFEST_PATH)
    candidates = load_json(ITEMS_V1_PATH)
    origins = manifest["origins"]
    ranked = sorted(
        origins,
        key=lambda origin: hashlib.sha256(
            f"{SEED}:{origin['origin_id']}".encode("utf-8")
        ).hexdigest(),
    )
    roles = {
        "pilot": [
            origin["origin_id"] for origin in ranked[0:8]
        ],
        "pilot_reserve": [
            origin["origin_id"] for origin in ranked[8:16]
        ],
        "development": [
            origin["origin_id"] for origin in ranked[16:18]
        ],
        "history": [
            origin["origin_id"] for origin in ranked[18:22]
        ],
    }
    usable_rows = {
        origin["origin_id"]: len(origin["usable_rows"])
        for origin in origins
    }
    items_per_origin: dict[str, int] = {}
    for item in candidates["items"]:
        origin_id = item["origin_id"]
        items_per_origin[origin_id] = (
            items_per_origin.get(origin_id, 0) + 1
        )
    role_ids = [
        origin_id
        for role in (
            "pilot",
            "pilot_reserve",
            "development",
            "history",
        )
        for origin_id in roles[role]
    ]
    checks = {
        "roles_disjoint": len(set(role_ids)) == len(role_ids),
        "pilot_origins_with_ge2_rows": (
            f"{sum(1 for origin_id in roles['pilot'] if usable_rows.get(origin_id, 0) >= 2)}/8"
        ),
        "current_max_items_per_origin": (
            max(items_per_origin.values())
            if items_per_origin
            else 0
        ),
        "item_extension_needed": (
            "pilot requires 2 items per origin; the current list emits "
            "1 item per origin -> extend the item builder at freeze "
            "(176 origins have >=2 usable rows)"
        ),
    }
    payload = {
        "schema": "wp2_split_dryrun_v1",
        "status": "DRAFT_NOT_FROZEN",
        "seed": SEED,
        "rule": (
            "sha256(seed:origin_id) ascending; [0:8]=pilot, "
            "[8:16]=pilot_reserve, [16:18]=development, "
            "[18:22]=history"
        ),
        "counts": {
            "origins_total": len(origins),
            "origins_with_ge2_usable_rows": sum(
                1 for count in usable_rows.values() if count >= 2
            ),
            "candidate_items": len(candidates["items"]),
            "distinct_item_origins": len(items_per_origin),
        },
        "roles": roles,
        "checks": checks,
    }
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def main() -> int:
    replay_bytes = replay_payload_bytes()
    tracked_bytes = TRACKED_RECEIPT_PATH.read_bytes()
    byte_identical = replay_bytes == tracked_bytes
    require(
        byte_identical,
        "WP-2 split replay differs from the tracked DRAFT receipt",
    )
    payload = json.loads(replay_bytes.decode("utf-8"))
    output = {
        "schema": "wp2_split_rerun_receipt_v1",
        "status": "PASS_BYTE_IDENTICAL",
        "seed": SEED,
        "comparison": {
            "tracked_receipt_path": str(
                TRACKED_RECEIPT_PATH.relative_to(ROOT)
            ),
            "tracked_receipt_sha256": sha256_file(
                TRACKED_RECEIPT_PATH
            ),
            "replayed_payload_sha256": sha256_bytes(replay_bytes),
            "byte_identical": byte_identical,
            "role_assignments_identical": True,
        },
        "counts": payload["counts"],
        "roles": payload["roles"],
        "checks": payload["checks"],
        "source_hashes": {
            "origin_manifest": sha256_file(MANIFEST_PATH),
            "candidate_items_v1": sha256_file(ITEMS_V1_PATH),
            "original_dryrun_script": sha256_file(
                ROOT / "research/tatqa_wp0_2026/wp2_split_dryrun.py"
            ),
            "replay_script": sha256_file(Path(__file__)),
        },
        "status_detail": (
            "Replay matches the tracked receipt byte-for-byte. The old "
            "receipt was not overwritten and the split remains DRAFT_NOT_FROZEN."
        ),
        "cost": {
            "model_calls": 0,
            "endpoint_calls": 0,
            "judge_calls": 0,
        },
    }
    OUTPUT_PATH.write_bytes(
        (
            json.dumps(
                output,
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        ).encode("utf-8")
    )
    print(
        "SPLIT_RERUN_BYTE_IDENTICAL "
        f"origins={payload['counts']['origins_total']} "
        f"roles={sum(len(value) for value in payload['roles'].values())}"
    )
    print(f"receipt={OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
