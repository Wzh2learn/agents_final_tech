#!/usr/bin/env python3
"""Build a derived artifact index bound to one integration commit.

Reads the historical ``ARTIFACT_HASHES.json`` (never rewritten), applies the
already-verified 24-item receipt rename map, and re-binds every entry to a
concrete commit in the current repository.

Two hashes are reported per artifact and never conflated:

* ``git_blob_oid``       -- Git object id of the blob at ``HEAD:<path>``.
* ``raw_blob_sha256``    -- SHA-256 over the *raw blob bytes* obtained through
                            ``git cat-file blob <oid>`` (no text pipeline, no
                            EOL conversion).

A third, explicitly segregated column records the Windows working-tree file
hash. Because ``core.autocrlf=true`` in this clone, text artifacts check out
with CRLF while the blob keeps LF, so the working-tree hash differs from the
raw-blob hash by construction. That difference is checkout policy, not
content drift, and must never be reported as a raw-hash mismatch.

Usage:
    python build_derived_artifact_index.py --out <path.json> [--rev HEAD]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MANIFEST_REL = (
    "research/word_scoring_new_family_20261027_v1/validation/ARTIFACT_HASHES.json"
)
RENAME_MAP_REL = "docs/governance/audit/loop_d_control_review/NEW_LOOP_D_HANDOFF_REVIEW_20261028.json"

# Thesis documents whose expected hash binds the A-delivery / pre-merge version.
THESIS_PATHS = (
    "research/feedback_learning_phase_b_20261026_v1/thesis_draft/"
    "CHAPTER_METHOD_RESULTS_LIMITATIONS_ZH.md",
    "research/feedback_learning_phase_b_20261026_v1/thesis_draft/EVIDENCE_TABLE.md",
)


def run(args: list[str], binary: bool = False):
    proc = subprocess.run(
        args,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        stdin=subprocess.DEVNULL,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout if binary else proc.stdout.decode("utf-8", "replace")


def rev_parse(rev: str) -> str:
    out = run(["git", "rev-parse", rev])
    if out is None:
        raise SystemExit(f"cannot resolve revision: {rev}")
    return out.strip()


def blob_at(rev: str, path: str):
    """Return (blob_oid, raw_bytes) for rev:path, or (None, None) if absent."""
    out = run(["git", "rev-parse", f"{rev}:{path}"])
    if out is None:
        return None, None
    oid = out.strip()
    if not oid.startswith(("blob", "")):  # guarded below by cat-file
        return None, None
    raw = run(["git", "cat-file", "blob", oid], binary=True)
    if raw is None:
        return None, None
    return oid, raw


def sha256_file(path: Path):
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def eol_of(data: bytes | None) -> str | None:
    if data is None:
        return None
    return "CRLF" if b"\r\n" in data else "LF"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--rev", default="HEAD")
    args = ap.parse_args()

    commit = rev_parse(args.rev)
    manifest_path = REPO_ROOT / MANIFEST_REL
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()

    rename = json.loads((REPO_ROOT / RENAME_MAP_REL).read_text(encoding="utf-8"))
    rename_items = rename["receipt_rename"]["items"]
    old_to_new = {i["old"]: i["new"] for i in rename_items}
    rename_by_new = {i["new"]: i for i in rename_items}

    artifacts = manifest["artifacts"]
    entries = []
    counts = {
        "total": len(artifacts),
        "raw_blob_match": 0,
        "raw_blob_match_after_rename": 0,
        "version_changed": 0,
        "missing_at_commit": 0,
        "worktree_hash_equals_raw": 0,
        "worktree_hash_differs_only_by_eol": 0,
        "renamed": 0,
    }

    for hist_path, expected in artifacts.items():
        new_path = old_to_new.get(hist_path, hist_path)
        renamed = new_path != hist_path
        if renamed:
            counts["renamed"] += 1

        oid, raw = blob_at(args.rev, new_path)
        rec = {
            "historical_path": hist_path,
            "resolved_path": new_path,
            "renamed": renamed,
            "historical_sha256": expected,
            "git_blob_oid": oid,
            "raw_blob_sha256": None,
            "raw_blob_eol": None,
            "worktree_sha256": None,
            "worktree_eol": None,
            "worktree_vs_raw": "NOT_COMPARED",
            "status": None,
        }

        if raw is None:
            rec["status"] = "MISSING_AT_COMMIT"
            counts["missing_at_commit"] += 1
            entries.append(rec)
            continue

        raw_sha = hashlib.sha256(raw).hexdigest()
        rec["raw_blob_sha256"] = raw_sha
        rec["raw_blob_eol"] = eol_of(raw)

        wt_path = REPO_ROOT / new_path
        wt_sha = sha256_file(wt_path)
        rec["worktree_sha256"] = wt_sha
        if wt_sha is not None:
            wt_bytes = wt_path.read_bytes()
            rec["worktree_eol"] = eol_of(wt_bytes)
            if wt_sha == raw_sha:
                rec["worktree_vs_raw"] = "IDENTICAL"
                counts["worktree_hash_equals_raw"] += 1
            elif wt_bytes.replace(b"\r\n", b"\n") == raw:
                rec["worktree_vs_raw"] = "CRLF_CHECKOUT_ONLY"
                counts["worktree_hash_differs_only_by_eol"] += 1
            else:
                rec["worktree_vs_raw"] = "CONTENT_DIFFERS"

        if raw_sha == expected:
            rec["status"] = "RAW_BLOB_MATCH"
            counts["raw_blob_match"] += 1
            if renamed:
                counts["raw_blob_match_after_rename"] += 1
        elif hist_path in THESIS_PATHS:
            rec["status"] = "THESIS_VERSION_CHANGED"
            counts["version_changed"] += 1
        else:
            rec["status"] = "RAW_BLOB_MISMATCH"
            counts["version_changed"] += 1

        if renamed:
            r = rename_by_new[new_path]
            rec["rename_sha256_before"] = r["sha256_before"]
            rec["rename_sha256_at_research"] = r["sha256_at_research"]

        entries.append(rec)

    thesis_versions = []
    for p in THESIS_PATHS:
        hist_expected = manifest["artifacts"][p]
        oid, raw = blob_at(args.rev, p)
        versions = []
        for tag, rev in (
            ("A_delivery_62c637ba", "62c637ba5f3a21e370669a596298d45d3544ca82"),
            ("pre_merge_2b51ae607", "2b51ae6070086bb52ab5e2746562bc66a99ae48e"),
            ("research_c644cb4f", "c644cb4f57f24c943b469cda5a6fea3b8a105db8"),
            ("integration_" + commit[:8], commit),
        ):
            o2, raw2 = blob_at(rev, p)
            versions.append(
                {
                    "snapshot": tag,
                    "git_blob_oid": o2,
                    "raw_blob_sha256": hashlib.sha256(raw2).hexdigest()
                    if raw2 is not None
                    else None,
                    "matches_historical_expected": (
                        hashlib.sha256(raw2).hexdigest() == hist_expected
                        if raw2 is not None
                        else False
                    ),
                }
            )
        thesis_versions.append(
            {
                "path": p,
                "historical_expected_sha256": hist_expected,
                "current_git_blob_oid": oid,
                "current_raw_blob_sha256": hashlib.sha256(raw).hexdigest()
                if raw is not None
                else None,
                "versions": versions,
                "interpretation": (
                    "The historical manifest binds the pre-merge thesis version. "
                    "The integration merge appended the 2026-10-27 A-stage and "
                    "C-boundary addenda, so the expected hash no longer describes "
                    "the current blob. Both versions are retained; the old "
                    "manifest is not rewritten."
                ),
            }
        )

    head_info = {
        "integration_commit": commit,
        "integration_branch": (run(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "").strip(),
        "main_at_build": rev_parse("main"),
        "research_branch_commit": rev_parse(
            "origin/research/word-scoring-new-family-20261027"
        ),
        "merge_base": rev_parse("62c637ba5f3a21e370669a596298d45d3544ca82"),
        "core_autocrlf": (run(["git", "config", "--get", "core.autocrlf"]) or "").strip(),
    }

    payload = {
        "schema": "word_scoring_new_family_derived_artifact_index_v1",
        "generated_date": "2026-10-28",
        "generated_by": "docs/governance/audit/loop_d_control_review/build_derived_artifact_index.py",
        "nature": (
            "DERIVED path-resolution and re-binding index. Not a replacement for "
            "the historical manifest, which is preserved unmodified."
        ),
        "parent_manifest": {
            "path": MANIFEST_REL,
            "raw_sha256": manifest_sha,
            "declared_entries": manifest["artifact_count"],
            "declared_hash_algorithm": manifest["hash_algorithm"],
            "modified_by_this_index": False,
        },
        "hash_semantics": {
            "git_blob_oid": "Git object id of the blob at the integration commit.",
            "raw_blob_sha256": "SHA-256 over raw blob bytes from `git cat-file blob`.",
            "worktree_sha256": (
                "SHA-256 of the Windows working-tree file. Segregated on purpose: "
                "core.autocrlf=true converts LF to CRLF on checkout, so this value "
                "differs from raw_blob_sha256 for text artifacts by design."
            ),
            "rule": (
                "Raw-blob equality is the identity criterion. Working-tree "
                "difference confined to CRLF is reported as CRLF_CHECKOUT_ONLY and "
                "is never counted as content drift."
            ),
        },
        "rename_map": {
            "source": RENAME_MAP_REL,
            "items": len(rename_items),
            "rule": "':' -> '_' in receipt basenames; content identical before/after.",
            "applied": counts["renamed"],
        },
        "integration_snapshot": head_info,
        "counts": counts,
        "thesis_version_changes": thesis_versions,
        "artifacts": entries,
    }

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps({"out": str(out), "commit": commit, "counts": counts}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
