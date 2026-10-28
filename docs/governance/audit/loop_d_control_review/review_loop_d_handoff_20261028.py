"""Read fixed Git blobs and local Word metadata; never edit scientific evidence.

Run from the repository with Python >=3.11. The only write is --output.
No checkout, model import, endpoint, environment-file content, or cleanup.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo

RESEARCH = "c644cb4f57f24c943b469cda5a6fea3b8a105db8"
RENAME_COMMIT = "2b51ae607"
STAGE = "research/word_scoring_new_family_20261027_v1/"
WORD = STAGE + "paper_e_word/"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], stderr=subprocess.PIPE)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(rev: str, path: str) -> bytes:
    return git("cat-file", "blob", f"{rev}:{path}")


def classify_bytes(local: bytes, versioned: bytes) -> str:
    if local == versioned:
        return "EXACT_BYTES"
    try:
        local.decode("utf-8")
        versioned.decode("utf-8")
    except UnicodeDecodeError:
        return "CONTENT_DIFFERENT"
    if local.replace(b"\r\n", b"\n") == versioned.replace(b"\r\n", b"\n"):
        return "CRLF_ONLY"
    return "CONTENT_DIFFERENT"


def self_test() -> None:
    assert classify_bytes(b"a\n", b"a\n") == "EXACT_BYTES"
    assert classify_bytes(b"a\r\n", b"a\n") == "CRLF_ONLY"
    assert classify_bytes(b"a\r\n", b"b\n") == "CONTENT_DIFFERENT"
    assert classify_bytes(b"\xff\r\n", b"\xff\n") == "CONTENT_DIFFERENT"
    assert digest(b"evidence") != digest(b"changed evidence")
    typed_keys = {"answer_type", "answer", "operands", "program", "operation",
                  "unit", "evidence_refs", "unknown", "clarification"}
    assert set(dict.fromkeys(typed_keys)) == typed_keys
    assert set(dict.fromkeys(typed_keys | {"numeric_value"})) != typed_keys


def probe_contract(parser: str, freeze: dict) -> dict:
    """Exercise the actual frozen function's first guard, before any other calls."""
    tree = ast.parse(parser)
    assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "TYPED_KEYS" for t in node.targets))
    typed_keys = set(ast.literal_eval(assignment.value))
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "normalize_typed")
    namespace = {"TYPED_KEYS": typed_keys}
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
                              function], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), "<frozen-normalize-typed-guard>", "exec"), namespace)
    payload = dict(answer_type="other", answer="UNKNOWN", operands=[], program="", operation="none",
                   unit="UNKNOWN", evidence_refs=[], unknown=True, clarification="Insufficient visible evidence",
                   numeric_value=None)
    normalized, observed = namespace["normalize_typed"](payload, "T", {}, None)
    assert normalized is None and observed["reason"] == "typed_key_contract_mismatch"
    return {
        "typed_unknown_instructs_numeric_value": "numeric_value=null" in freeze["arms"]["T"]["output_contract"],
        "parser_has_exact_key_guard": 'if set(payload) != expected_keys:' in parser,
        "instructed_unknown_keys_pass_typed_exact_guard": set(payload) == typed_keys,
        "extra_key": "numeric_value", "actual_frozen_function_probe": observed,
        "probe_scope": "Frozen key-guard counterexample, not actual model error attribution",
        "reference_unit_ambiguities_need_separate_review": True,
    }


def build_report(main_ref: str) -> dict:
    root = Path(git("rev-parse", "--show-toplevel").decode().strip())
    main = git("rev-parse", main_ref).decode().strip()
    research = git("rev-parse", RESEARCH).decode().strip()
    tree = git("ls-tree", "-r", "--name-only", research).decode().splitlines()
    branch_paths = set(tree)
    left, right = map(int, git("rev-list", "--left-right", "--count",
                               f"{main}...{research}").decode().split())

    renames = []
    mapping = {}
    changes = git("diff-tree", "-r", "--no-commit-id", "--name-status", "-M",
                  RENAME_COMMIT).decode().splitlines()
    for line in changes:
        fields = line.split("\t")
        if fields[0].startswith("R") and fields[1].startswith(STAGE + "generation/receipts/"):
            old, new = fields[1:3]
            before = blob(RENAME_COMMIT + "^", old)
            renamed = blob(RENAME_COMMIT, new)
            final = blob(research, new)
            mapping[old] = new
            renames.append({"old": old, "new": new, "sha256_before": digest(before),
                            "sha256_at_rename": digest(renamed), "sha256_at_research": digest(final),
                            "unchanged_across_rename_and_final": before == renamed == final})
    assert len(mapping.values()) == len(set(mapping.values())), "rename collision"

    manifest_path = STAGE + "validation/ARTIFACT_HASHES.json"
    manifest_bytes = blob(research, manifest_path)
    manifest = json.loads(manifest_bytes)
    validations = []
    for old_path, expected in sorted(manifest["artifacts"].items()):
        resolved = old_path if old_path in branch_paths else mapping.get(old_path)
        actual = digest(blob(research, resolved)) if resolved in branch_paths else None
        row = {"historical_path": old_path, "resolved_path": resolved,
               "expected_sha256": expected, "actual_sha256": actual,
               "status": "MATCH" if actual == expected else
               "MISSING" if actual is None else "HASH_MISMATCH"}
        if row["status"] == "HASH_MISMATCH":
            row["expected_matches_A_delivery_62c637ba"] = digest(blob("62c637ba", old_path)) == expected
            row["expected_matches_pre_merge_2b51ae607"] = digest(blob(RENAME_COMMIT, resolved)) == expected
            row["expected_matches_merge_a441c5ca"] = digest(blob("a441c5ca", resolved)) == expected
            row["interpretation"] = "Historical snapshot differs after merge; preserve both and issue a derived current index"
        validations.append(row)

    local_files = []
    for path in sorted((root / WORD).rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        local = path.read_bytes()
        row = {"path": relative, "bytes": len(local), "local_sha256": digest(local)}
        if relative in branch_paths:
            versioned = blob(research, relative)
            row.update({"classification": classify_bytes(local, versioned),
                        "branch_blob_id": git("rev-parse", f"{research}:{relative}").decode().strip(),
                        "branch_raw_sha256": digest(versioned)})
        else:
            row["classification"] = "LOCAL_ONLY_PRESERVE"
        local_files.append(row)

    conversion_path = WORD + "CONVERSION_MANIFEST.json"
    conversion_bytes = blob(research, conversion_path)
    conversion = json.loads(conversion_bytes)
    render_path = WORD + "D_WORD_RENDER_RECEIPT.md"
    render_bytes = blob(research, render_path)
    bound_hashes = set(re.findall(r"\b[0-9a-f]{64}\b", render_bytes.decode("utf-8")))
    chain = []
    paths = [conversion["canonical_source"], WORD + "paper_e_word.md",
             WORD + "paper_e_word_fixed.md", WORD + "paper_e.docx",
             WORD + "rendered_final/paper_e.pdf"]
    for path in paths:
        raw = blob(research, path)
        actual = digest(raw)
        if path == conversion["canonical_source"]:
            expected = conversion["canonical_source_sha256"]
            receipt = conversion_path
        elif path == WORD + "paper_e_word.md":
            expected = conversion["files"]["paper_e_word.md"]["sha256"]
            receipt = conversion_path
        else:
            expected = actual if actual in bound_hashes else None
            receipt = render_path
        chain.append({"path": path, "git_blob_id": git("rev-parse", f"{research}:{path}").decode().strip(),
                      "raw_sha256": actual, "bound_by": receipt,
                      "hash_present_and_matching": expected == actual})

    rows = [json.loads(line) for line in blob(research, STAGE + "generation/results/RAW_RESPONSES.jsonl").splitlines() if line]
    receipt = json.loads(blob(research, STAGE + "generation/GENERATION_RECEIPT.json"))
    summary = json.loads(blob(research, STAGE + "scoring_v3/results/DIAGNOSTIC_SUMMARY.json"))
    freeze = json.loads(blob(research, STAGE + "mechanism/MECHANISM_FREEZE.json"))
    parser_path = STAGE + "scoring_v3/diagnostic_rescore.py"
    parser = blob(research, parser_path).decode()
    contract_probe = probe_contract(parser, freeze)
    arm_counts = {}
    for arm in ("D", "T", "M"):
        arm_rows = [r for r in rows if r["arm"] == arm]
        arm_counts[arm] = {"raw_rows": len(arm_rows),
                          "outputs_at_512": sum(r["usage"]["output_tokens"] == 512 for r in arm_rows),
                          "strict_whole_json": sum(_is_whole_json(r["response_text"]) for r in arm_rows),
                          "extracted_interface": summary["arm_summary"][arm]["interface_status_counts"]}
    persisted = {key: sum(r["usage"][key] for r in rows) for key in ("input_tokens", "output_tokens")}
    ignored = subprocess.run(["git", "check-ignore", "-v", ".env"], capture_output=True, text=True)
    tracked_env = git("ls-files", "--", ".env").decode().strip()
    return {
        "schema": "loop_d_handoff_metadata_review_v1",
        "review_date": datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat(),
        "scope": "OFFLINE_BLOB_AND_LOCAL_METADATA_NOT_FULL_SCIENTIFIC_OR_REMOTE_AUDIT",
        "git_snapshot": {"main_at_review": main, "research_commit": research,
                         "merge_base": git("merge-base", main, research).decode().strip(),
                         "main_only_commits": left, "research_only_commits": right,
                         "counts_are_point_in_time_not_required_future_state": True},
        "local_word": {"total_files": len(local_files),
                       "counts": dict(Counter(r["classification"] for r in local_files)),
                       "action": "PRESERVE_ALL_NO_DELETE_OR_MOVE", "files": local_files},
        "receipt_rename": {"commit": git("rev-parse", RENAME_COMMIT).decode().strip(),
                           "count": len(renames), "items": renames},
        "historical_manifest": {"path": manifest_path, "raw_sha256": digest(manifest_bytes),
                                "declared_entries": manifest["artifact_count"],
                                "checked_entries": len(validations),
                                "counts": dict(Counter(r["status"] for r in validations)),
                                "historical_manifest_modified": False,
                                "derived_path_resolution_only": True, "items": validations},
        "paper_chain": {"conversion_manifest_sha256": digest(conversion_bytes),
                        "render_receipt_sha256": digest(render_bytes), "items": chain,
                        "interpretation": "Multiple receipts bind identity, not submission quality"},
        "raw_and_budget": {"raw_rows": len(rows), "arms": arm_counts,
                           "persisted_usage": persisted,
                           "persisted_total_tokens": sum(persisted.values()),
                           "conservative_receipt_total": receipt["consumed_tokens"],
                           "difference_retained_as_uncertain": receipt["consumed_tokens"] - sum(persisted.values()),
                           "generation_receipt_sha256": digest(blob(research, STAGE + "generation/GENERATION_RECEIPT.json")),
                           "no_new_generation_or_authorization": True},
        "contract_probe": {
            "freeze_sha256": digest(blob(research, STAGE + "mechanism/MECHANISM_FREEZE.json")),
            "parser_sha256": digest(parser.encode()),
            **contract_probe,
        },
        "environment_file": {"tracked_at_root": bool(tracked_env),
                             "ignored_at_root": ignored.returncode == 0,
                             "ignore_rule": ignored.stdout.strip(),
                             "content_read": False, "history_read": False,
                             "leak_established": False},
        "not_done": ["GB10 live state or conversation-cleanup recheck", "merge or checkout research branch",
                     "delete, move, archive local files or worktrees", "Paper E editing or final submission audit",
                     "model generation, training, A/C dispatch", "submission, publication, payment or contact"]
    }


def _is_whole_json(text: str) -> bool:
    try:
        return isinstance(json.loads(text), dict)
    except (ValueError, TypeError):
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-ref", default="main")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("7 metadata/contract positive and negative controls passed")
        return
    report = build_report(args.main_ref)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"git": report["git_snapshot"], "local_word": report["local_word"]["counts"],
                      "renames": report["receipt_rename"]["count"],
                      "manifest": report["historical_manifest"]["counts"],
                      "paper_chain_bound": all(x["hash_present_and_matching"] for x in report["paper_chain"]["items"]),
                      "raw": report["raw_and_budget"], "contract_probe": report["contract_probe"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
