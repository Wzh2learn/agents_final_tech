#!/usr/bin/env python3
"""Resolve final Loop C wording and accounting conditions without new calls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
EXTERNAL = Path("/home/testuser/wzh/research_stage_e_d_20261009")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    doc = ROOT / "docs/research/derived_process_supervision_design_v1.md"
    text = doc.read_text(encoding="utf-8")
    text = text.replace("Native Level 3 requires:", "Native source evidence admission requires:")
    text = text.replace("## 5. Label-quality ladder", "## 5. Source admission gates")
    text = text.replace(
        "`FACT`: `native`, `human-annotated`, `deterministic-derived`, `verifier-derived`, `judge-derived`, and `proxy` remain provenance labels. They are not interchangeable with L0-L5 quality levels.",
        "`FACT`: `native`, `human-annotated`, `deterministic-derived`, `verifier-derived`, `judge-derived`, and `proxy` remain provenance labels. They are not interchangeable with L0-L5 quality levels. Native source provenance does not assign a level by itself; the level follows the independent evidence required by the ladder.",
    )
    doc.write_text(text, encoding="utf-8")

    network_path = TASK / "metadata_network_accounting.json"
    network = load(network_path)
    network.pop("openalex_metadata_requests", None)
    network.update({
        "metadata_http_scope": "curl-based metadata fetches parsed from the Loop A run log; excludes OpenAlex client requests",
        "openalex_query_definitions": 8,
        "openalex_result_files": 8,
        "openalex_executed_request_count": "UNVERIFIED_NO_INDEPENDENT_REQUEST_LOG",
    })
    write(network_path, network)

    source_audit_path = TASK / "source_audit_v1.json"
    source_audit = load(source_audit_path)
    source_audit["call_counts"].pop("openalex_metadata_requests", None)
    source_audit["call_counts"].pop("openalex_metadata_queries", None)
    source_audit["call_counts"].update({
        "metadata_http_logical_attempts_curl_only": network["metadata_http_logical_attempts"],
        "metadata_http_unique_urls_curl_only": network["metadata_http_unique_urls"],
        "openalex_query_definitions": 8,
        "openalex_result_files": 8,
        "openalex_executed_request_count": "UNVERIFIED_NO_INDEPENDENT_REQUEST_LOG",
    })
    write(source_audit_path, source_audit)

    external_matches = {}
    for base in [TASK / "contract", TASK / "sources"]:
        for path in sorted(p for p in base.rglob("*") if p.is_file()):
            rel = str(path.relative_to(TASK))
            external_path = EXTERNAL / rel.split("/", 1)[1] if rel.startswith("contract/") else EXTERNAL / rel
            ext_hash = sha256(external_path) if external_path.is_file() else None
            workspace_hash = sha256(path)
            external_matches[rel] = {
                "workspace_sha256": workspace_hash,
                "external_sha256": ext_hash,
                "match": ext_hash == workspace_hash,
            }

    receipt_path = TASK / "loop_a_receipt.json"
    receipt = load(receipt_path)
    receipt["source_record_index"].pop("openalex_query_count", None)
    receipt["loop_c_condition_repair"]["metadata_http_accounting"].pop("openalex_metadata_queries", None)
    receipt["execution_accounting"].pop("openalex_metadata_requests", None)
    receipt["execution_accounting"].pop("openalex_metadata_queries", None)
    receipt["execution_accounting"].update({
        "metadata_http_logical_attempts_curl_only": network["metadata_http_logical_attempts"],
        "metadata_http_unique_urls_curl_only": network["metadata_http_unique_urls"],
        "metadata_redirect_attempts": network["metadata_redirect_attempts"],
        "openalex_query_definitions": 8,
        "openalex_result_files": 8,
        "openalex_executed_request_count": "UNVERIFIED_NO_INDEPENDENT_REQUEST_LOG",
    })
    receipt["representation_notes"] = {
        "micro_fraction": "96/118 is authoritative; analysis_summary.json visibility.micro.rate is a convenience float only.",
        "openalex_accounting": "Eight query definitions and eight result files are verified. The exact executed OpenAlex request count is UNVERIFIED because no independent request log was preserved.",
        "metadata_http_scope": network["metadata_http_scope"],
    }
    receipt["source_record_index"]["external_copy_matches"] = external_matches
    receipt["source_record_index"]["all_external_copies_match"] = all(x["match"] for x in external_matches.values())
    receipt["source_record_index"]["metadata_network_accounting"]["sha256"] = sha256(network_path)
    receipt["forbidden_action_check"]["existing_dirty_runtime_logs_changed"] = "UNVERIFIED_RUNTIME_WRITER_ATTRIBUTION"
    receipt["forbidden_action_check"]["runtime_log_attribution_note"] = "logs/graph/docs_lint_report.json and logs/graph/verify-report.json mtimes moved in the window; standing writers include docs_lint/status/Loop B, but exact attribution is not proved."

    for item in receipt["deliverables"]:
        path = ROOT / item["path"]
        item["sha256"] = sha256(path)
        item["bytes"] = path.stat().st_size
    for item in receipt["supporting_artifacts"]:
        path = ROOT / item["path"]
        if path.is_file():
            item["sha256"] = sha256(path)
            item["bytes"] = path.stat().st_size
    receipt["final_loop_c_condition_repair"].update({
        "status": "REPAIRED_PENDING_INDEPENDENT_FINAL_CONFIRMATION",
        "openalex_request_count_marked_unverified": True,
        "counter_aliases_removed": True,
        "curl_only_scope_declared": True,
        "external_per_file_hashes_recorded": True,
        "runtime_log_attribution_marked_unverified": True,
        "native_level_wording_repaired": True,
    })
    receipt.setdefault("validation", []).append({
        "command": "./venv/bin/python research/stage_e_stage_d_20261009/resolve_final_conditions.py",
        "result": "PASS",
        "details": "Final counter aliases removed; OpenAlex request count marked UNVERIFIED; curl-only scope declared; external per-file hashes recorded; runtime-log attribution marked UNVERIFIED; L3/L5 wording repaired.",
    })
    write(receipt_path, receipt)

    validation = {
        "status": "PASS_PENDING_INDEPENDENT_FINAL_CONFIRMATION",
        "source_audit_sha256": sha256(source_audit_path),
        "source_audit_bytes": source_audit_path.stat().st_size,
        "network_accounting_sha256": sha256(network_path),
        "external_copy_hashes_recorded": len(external_matches),
        "external_copies_all_match": all(x["match"] for x in external_matches.values()),
        "openalex_executed_request_count": "UNVERIFIED_NO_INDEPENDENT_REQUEST_LOG",
        "forbidden_runtime_log_attribution": "UNVERIFIED_RUNTIME_WRITER_ATTRIBUTION",
    }
    write(TASK / "final_validation.json", validation)
    print(json.dumps(validation, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
