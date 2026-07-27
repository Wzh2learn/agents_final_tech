#!/usr/bin/env python3
"""Run retrieval strategy ablation experiments on TAT-DQA validation."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "app_config.json"
EVAL_SCRIPT = PROJECT_ROOT / "scripts" / "run_tat_dqa_m2_upper_bound.py"
MANIFEST = PROJECT_ROOT / "docs" / "datasets" / "tat-dqa-joint-v1-manifest.json"
QA_JSON = Path.home() / "wzh" / "datasets" / "tat-dqa" / "raw" / "tatdqa_dataset_dev.json"
DOCS_ARCHIVE = Path.home() / "wzh" / "datasets" / "tat-dqa" / "raw" / "tatdqa_docs_dev.zip"
OUTPUT_DIR = Path.home() / "wzh" / "datasets" / "tat-dqa" / "derived" / "ablation"
PYTHON = Path.home() / "miniconda3" / "envs" / "wzh_retrieval" / "bin" / "python"
COLLECTION = "tat-dqa-joint-v1-validation"
TIMEOUT_SEC = 600

BASE_ENV = {
    **os.environ,
    "LOCAL_EMBEDDING_MODEL_PATH": str(Path.home() / "wzh" / "models" / "hf" / "qwen3-embedding-0.6b"),
    "LOCAL_EMBEDDING_DEVICE": "cuda",
    "PGDATABASE_URL": "postgresql://postgres:postgres@localhost:15432/vector_db",
    "PYTHONPATH": str(PROJECT_ROOT / "src"),
}


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def run_experiment(
    name: str,
    config_overrides: dict | None,
    extra_args: list[str],
    extra_env: dict | None = None,
) -> dict | None:
    """Run one experiment, return metrics or None on failure."""
    original_config = load_config()
    output_file = OUTPUT_DIR / f"{name}.json"
    env = {**BASE_ENV, **(extra_env or {})}

    try:
        if config_overrides:
            modified = copy.deepcopy(original_config)
            for key_path, value in config_overrides.items():
                parts = key_path.split(".")
                target = modified
                for part in parts[:-1]:
                    target = target[part]
                target[parts[-1]] = value
            save_config(modified)
            print(f"[{name}] Config overrides: {config_overrides}")
        else:
            print(f"[{name}] Default config")

        cmd = [
            str(PYTHON), str(EVAL_SCRIPT),
            "--manifest", str(MANIFEST),
            "--qa-json", str(QA_JSON),
            "--docs-archive", str(DOCS_ARCHIVE),
            "--split", "validation",
            "--collection", COLLECTION,
            "--evaluate", "--with-answers",
            "--output", str(output_file),
        ] + extra_args

        print(f"[{name}] Extra args: {extra_args or 'none'}")
        started = time.time()
        result = subprocess.run(
            cmd, env=env, capture_output=True, text=True,
            timeout=TIMEOUT_SEC, cwd=str(PROJECT_ROOT),
        )
        elapsed = time.time() - started

        if result.returncode != 0:
            print(f"[{name}] FAILED (exit {result.returncode}, {elapsed:.1f}s)")
            stderr_tail = result.stderr[-500:] if result.stderr else ""
            print(f"  stderr tail: {stderr_tail}")
            return {"error": f"exit {result.returncode}", "stderr_tail": stderr_tail}

        print(f"[{name}] Completed in {elapsed:.1f}s")
        output = json.loads(output_file.read_text(encoding="utf-8"))
        return output.get("evaluation", {}).get("metrics")

    except subprocess.TimeoutExpired:
        print(f"[{name}] TIMEOUT (>{TIMEOUT_SEC}s)")
        return {"error": "TIMEOUT"}
    except Exception as exc:
        print(f"[{name}] ERROR: {exc}")
        return {"error": str(exc)}
    finally:
        save_config(original_config)
        print(f"[{name}] Config restored")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict | None] = {}

    experiments = [
        # (name, config_overrides, extra_cli_args, extra_env)
        ("A_vector_only",
         {"rag.vector_weight": 1.0, "rag.bm25_weight": 0.0},
         [], None),
        ("B_bm25_only",
         {"rag.vector_weight": 0.0, "rag.bm25_weight": 1.0},
         [], None),
        ("C_hybrid_default",
         None, [], None),
        ("D_hybrid_no_rerank",
         None, [], None),
        ("E_hybrid_rerank",
         {"rerank.enabled": True, "rag.force_rerank": True,
          "rerank.llm_model": "Qwen3-14B-Q4_K_M.gguf",
          "rerank.api_key_env": "RERANK_API_KEY",
          "rerank.base_url_env": "RERANK_BASE_URL"},
         ["--use-rerank"],
         {"RERANK_API_KEY": "not-needed", "RERANK_BASE_URL": "http://127.0.0.1:8004/v1"}),
        ("F_top_k_3",
         None, ["--top-k", "3"], None),
        ("F_top_k_10",
         None, ["--top-k", "10"], None),
    ]

    consecutive_failures = 0
    for name, overrides, extra_args, extra_env in experiments:
        print(f"\n{'='*60}")
        print(f"EXPERIMENT: {name}")
        print(f"{'='*60}")
        metrics = run_experiment(name, overrides, extra_args, extra_env)
        results[name] = metrics

        if metrics and "error" in metrics:
            consecutive_failures += 1
            if consecutive_failures >= 3:
                print("\nSTOP: 3 consecutive failures")
                break
        else:
            consecutive_failures = 0

    summary_path = OUTPUT_DIR / "ablation_summary.json"
    summary_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nSummary: {summary_path}")

    # Print results table
    print(f"\n{'Experiment':<20} {'DocR@5':>7} {'EviR@5':>7} {'MRR':>8} {'EM':>7} {'Cite':>7} {'Lat(s)':>7}")
    print("-" * 75)
    for name, metrics in results.items():
        if metrics and "error" not in metrics:
            print(f"{name:<20} "
                  f"{metrics.get('document_recall_at_5', 0):>7.3f} "
                  f"{metrics.get('evidence_recall_at_5', 0):>7.3f} "
                  f"{metrics.get('evidence_mrr', 0):>8.4f} "
                  f"{metrics.get('answer_exact_match', 0):>7.3f} "
                  f"{metrics.get('answer_evidence_hit_rate', 0):>7.3f} "
                  f"{metrics.get('latency_mean_sec', 0):>7.3f}")
        else:
            err = metrics.get("error", "unknown") if metrics else "no result"
            print(f"{name:<20} ERROR: {err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
