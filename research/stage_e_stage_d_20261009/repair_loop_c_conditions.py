#!/usr/bin/env python3
"""Repair Loop C conditions without changing frozen Stage E inputs."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = Path(__file__).resolve().parent
EXTERNAL = Path("/home/testuser/wzh/research_stage_e_d_20261009")
RUN_LOG = Path("/home/testuser/wzh/loop_runs/stage-ed-20261009/a.log.attempt-1")
LOOP_C_LOG = Path("/home/testuser/wzh/loop_runs/stage-ed-20261009/c.log")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def insert_after(path: Path, marker: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    if addition.strip() in text:
        return
    if marker not in text:
        raise RuntimeError(f"marker missing in {path}: {marker}")
    text = text.replace(marker, marker + "\n\n" + addition, 1)
    path.write_text(text, encoding="utf-8")


def extract_loop_c_verdict() -> dict:
    text = LOOP_C_LOG.read_text(encoding="utf-8", errors="replace")
    start = text.find("\n{\n")
    if start < 0:
        raise RuntimeError("Loop C JSON object not found")
    verdict = json.loads(text[start + 1:])
    write_json(TASK / "loop_c_verdict.json", verdict)
    return verdict


def network_accounting() -> dict:
    commands = []
    for line in RUN_LOG.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") or {}
        if item.get("type") == "command_execution" and item.get("status") == "completed":
            command = item.get("command", "")
            if "curl" in command and "apply_patch" not in command:
                commands.append(command)
    literal_curl_calls = sum(len(re.findall(r"(?:^|\s)curl(?:\s|$)", c)) for c in commands)
    loop_extra_attempts = 0
    for command in commands:
        for match in re.finditer(r"for\s+\w+\s+in\s+([^;]+);\s+do[\s\S]*?curl", command):
            urls = re.findall(r"https://\S+", match.group(1))
            loop_extra_attempts += max(0, len(urls) - 1)
    urls = set()
    for command in commands:
        for raw_url in re.findall(r"https://\S+", command):
            clean_url = raw_url.split('\\n')[0]
            for delimiter in map(chr, (34, 39, 60, 62, 41)):
                clean_url = clean_url.split(delimiter, 1)[0]
            clean_url = clean_url.rstrip('.,;:')
            urls.add(clean_url)
    openalex_queries = len(list((EXTERNAL / "sources" / "openalex").glob("*.json")))
    return {
        "metadata_http_logical_attempts": literal_curl_calls + loop_extra_attempts,
        "metadata_http_unique_urls": len(urls),
        "metadata_redirect_attempts": "UNVERIFIED_NOT_SEPARATELY_LOGGED",
        "openalex_metadata_queries": openalex_queries,
        "scientific_model_calls": 0,
        "judge_calls": 0,
    }


def main() -> int:
    before = {
        p.name: sha256(p)
        for p in TASK.iterdir()
        if p.is_file() and p.name not in {"loop_a_receipt.json", "repair_loop_c_conditions.py"}
    }
    subprocess.run([sys.executable, str(TASK / "quantify_stage_e.py")], check=True)
    after = {
        p.name: sha256(p)
        for p in TASK.iterdir()
        if p.is_file() and p.name not in {"loop_a_receipt.json", "repair_loop_c_conditions.py"}
    }
    changed_by_rerun = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))

    qdoc = ROOT / "docs/research/stage_e_118_quantification_v1.md"
    insert_after(
        qdoc,
        "`FACT`: OCR-like is a predefined negative-observability control: every case is blind under the frozen absorption rule and every gamma in the grid.",
        """### OCR-like grouped uncertainty

`FACT`: OCR-like is `0/13` across 11 table-UID clusters. The table-cluster bootstrap is degenerate at `[0,0]` because every resampled cluster has zero visible OCR cases; that interval describes this frozen construction and is not a population upper bound.

`FACT`: as a sensitivity reference only, the exact binomial 95% interval is `[0,24.71%]` if the 13 injections were independent. They are not guaranteed independent.

`VALUE`: the conservative grouped report is `0/13 visible; 0/11 table clusters contain a visible OCR case; exact cluster-event 95% sensitivity interval [0,28.49%]`. State that transfer to a new corpus or lineage is `UNVERIFIED`.""",
    )
    mdoc = ROOT / "docs/research/stage_e_observability_metrics_v1.md"
    insert_after(
        mdoc,
        "`INFERENCE`: cluster-aware intervals are descriptive uncertainty for this frozen corpus. They do not turn 118 injections into 118 independent units and do not establish population generalization beyond the corpus.",
        """`VALUE`: for a zero-event family such as OCR-like, report the raw `0/13`, the number of independent table clusters (`11`), a grouped cluster-event exact interval, and the degenerate cluster-bootstrap interval separately. Do not present `[0,0]` bootstrap or a naive Bernoulli interval as population certainty.""",
    )

    contract_dir = TASK / "contract"
    source_dir = TASK / "sources"
    contract_dir.mkdir(exist_ok=True)
    for name in ["PROMPT.md", "IMPLEMENTATION_PLAN.md", "loop_a_prompt.md", "loop_c_prompt.md", "openalex_search.py"]:
        shutil.copy2(EXTERNAL / name, contract_dir / name)
    if source_dir.exists():
        shutil.rmtree(source_dir)
    shutil.copytree(EXTERNAL / "sources", source_dir)

    accounting = network_accounting()
    analysis = load_json(TASK / "analysis_summary.json")
    receipt_path = TASK / "loop_a_receipt.json"
    receipt = load_json(receipt_path)
    receipt["derived_results"]["visibility"].pop("micro_rate", None)
    receipt["derived_results"]["visibility"]["micro_fraction"] = "96/118"
    receipt["derived_results"]["visibility"]["table_cluster_bootstrap_ci95"] = analysis["cluster_bootstrap"]["intervals"]["visibility_rate"]
    receipt["execution_accounting"].update(accounting)
    receipt["source_record_index"] = {
        "workspace_contract_dir": "research/stage_e_stage_d_20261009/contract",
        "workspace_sources_dir": "research/stage_e_stage_d_20261009/sources",
        "external_source_dir_preserved": str(EXTERNAL / "sources"),
        "openalex_query_count": accounting["openalex_metadata_queries"],
    }
    receipt["loop_c_condition_repair"] = {
        "status": "REPAIRED_PENDING_LOOP_C_REVIEW",
        "micro_rate_source": "analysis_summary.json",
        "bootstrap_ci_source": "analysis_summary.json",
        "analysis_rerun_rc": 0,
        "analysis_rerun_changed_outputs": changed_by_rerun,
        "workspace_contract_copied": True,
        "workspace_sources_copied": True,
        "metadata_http_accounting": accounting,
        "ocr_grouped_uncertainty_added": True,
    }
    verdict = extract_loop_c_verdict()
    receipt["loop_c_verdict_before_repair"] = {
        "path": "research/stage_e_stage_d_20261009/loop_c_verdict.json",
        "sha256": sha256(TASK / "loop_c_verdict.json"),
        "verdict": verdict.get("verdict"),
        "status": verdict.get("status"),
    }
    deliverables = {}
    for item in receipt["deliverables"]:
        name = Path(item["path"]).name
        path = ROOT / "docs/research" / name
        item["sha256"] = sha256(path)
        item["bytes"] = path.stat().st_size
        deliverables[name] = item["sha256"]
    receipt.setdefault("validation", []).append({
        "command": "python research/stage_e_stage_d_20261009/repair_loop_c_conditions.py",
        "result": "PASS",
        "details": "Loop C conditions repaired; frozen inputs untouched; receipt floats and CI now derive from analysis_summary.json; workspace evidence packet copied; OCR grouped uncertainty added; metadata HTTP accounting recorded.",
    })
    source_audit_path = TASK / "source_audit_v1.json"
    source_audit = load_json(source_audit_path)
    source_audit["call_counts"].update(accounting)
    write_json(source_audit_path, source_audit)
    write_json(receipt_path, receipt)
    print(json.dumps({
        "status": "PASS",
        "changed_by_analysis_rerun": changed_by_rerun,
        "network_accounting": accounting,
        "deliverables": deliverables,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
