#!/usr/bin/env python3
"""Exploratory per-column sensitivity analysis for the frozen E3 result.

This analysis reuses the existing rho=1.0 expansion artifacts and makes no
endpoint calls.  It is explicitly secondary: the preregistered table-level E3
estimate and Version-B verdict remain unchanged.
"""

import importlib.util
import json
import math
import os
import random
from pathlib import Path


REPO = Path(os.environ.get("JINRONG_REPO",
                           str(Path(__file__).resolve().parents[1]))).resolve()
EVAL = REPO / "logs" / "graph" / "eval"
SEED = 20260829
N_BOOT = 10_000


def load_module(name: str, path: Path):
    """Load a repository module without changing sys.path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def percentile_ci(values: list[float]) -> list[float]:
    """Return a deterministic percentile 95% interval."""
    ordered = sorted(values)
    return [ordered[int(0.025 * len(ordered))],
            ordered[int(0.975 * len(ordered))]]


def bootstrap_columns(diffs: list[int]) -> list[float]:
    """Naive paired-column bootstrap; ignores within-table dependence."""
    rng = random.Random(SEED)
    n = len(diffs)
    draws = [sum(rng.choices(diffs, k=n)) / n for _ in range(N_BOOT)]
    return percentile_ci(draws)


def bootstrap_table_clusters(rows: list[dict]) -> list[float]:
    """Resample tables and retain all collision columns within each table."""
    by_table: dict[str, list[int]] = {}
    for row in rows:
        by_table.setdefault(row["uid"], []).append(row["diff"])
    tables = sorted(by_table)
    rng = random.Random(SEED)
    draws = []
    for _ in range(N_BOOT):
        sampled = rng.choices(tables, k=len(tables))
        diffs = [value for uid in sampled for value in by_table[uid]]
        draws.append(sum(diffs) / len(diffs))
    return percentile_ci(draws)


def mcnemar_exact_two_sided(improved: int, harmed: int) -> float:
    """Exact two-sided McNemar p-value for discordant paired columns."""
    discordant = improved + harmed
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, i)
               for i in range(min(improved, harmed) + 1)) / (2 ** discordant)
    return min(1.0, 2 * tail)


def correctness_rows(vg, corpus: dict, meas: list[str],
                     gated_rules: dict, ungated_rules: dict) -> list[dict]:
    """Calculate paired correctness for every collision column."""
    rows = []
    for uid in meas:
        record = corpus[uid]
        collisions = [entry for entry in record["entries"]
                      if entry.get("type") == "collision"]
        if not collisions:
            continue
        per_arm = {}
        for arm, rules in (("gated", gated_rules), ("ungated", ungated_rules)):
            mapping, _ = vg.mp.map_headers(
                record["inj_header"], vg.schema_table_for(record, rules))
            per_arm[arm] = {source: standard for standard, source in mapping.items()}
        for entry in collisions:
            injected = record["inj_header"][entry["col"]]
            gated_ok = int(per_arm["gated"].get(injected) == entry["original"])
            ungated_ok = int(per_arm["ungated"].get(injected) == entry["original"])
            rows.append({
                "uid": uid,
                "col": entry["col"],
                "injected": injected,
                "original": entry["original"],
                "gated_correct": gated_ok,
                "ungated_correct": ungated_ok,
                "diff": gated_ok - ungated_ok,
            })
    return rows


def main() -> int:
    vg = load_module("vgmc_exp1", REPO / "research" / "vgmc_exp1.py")
    overlay = json.loads((EVAL / "vgmc_collision_overlay_v2_rho10.json")
                         .read_text(encoding="utf-8"))
    corpus = vg.load_corpus(overlay)
    _, meas = vg.split_uids(list(corpus))
    gated = json.loads((EVAL / "vgmc_collision_EXP_g10_checkpoint.json")
                       .read_text(encoding="utf-8"))["arm_gated"]["rules"]
    ungated = json.loads((EVAL / "vgmc_collision_EXP_u10_checkpoint.json")
                         .read_text(encoding="utf-8"))["arm_ungated"]["rules"]
    frozen = json.loads((EVAL / "vgmc_expansion_curve.json")
                        .read_text(encoding="utf-8"))["E3"]

    rows = correctness_rows(vg, corpus, meas, gated, ungated)
    diffs = [row["diff"] for row in rows]
    gated_correct = sum(row["gated_correct"] for row in rows)
    ungated_correct = sum(row["ungated_correct"] for row in rows)
    improved = sum(row["gated_correct"] == 1 and row["ungated_correct"] == 0
                   for row in rows)
    harmed = sum(row["gated_correct"] == 0 and row["ungated_correct"] == 1
                 for row in rows)
    n_columns = len(rows)

    out = {
        "meta": {
            "name": "vgmc-column-sensitivity",
            "analysis_type": "exploratory_column_level_sensitivity",
            "seed": SEED,
            "n_boot": N_BOOT,
            "endpoint_calls": 0,
            "frozen_e3_unchanged": True,
        },
        "frozen_table_level_E3": frozen,
        "column_level": {
            "n_tables": len({row["uid"] for row in rows}),
            "n_columns": n_columns,
            "gated_correct": gated_correct,
            "ungated_correct": ungated_correct,
            "gated_acc": gated_correct / n_columns,
            "ungated_acc": ungated_correct / n_columns,
            "paired_delta_acc": sum(diffs) / n_columns,
            "improved": improved,
            "harmed": harmed,
            "ties": n_columns - improved - harmed,
            "mcnemar_exact_p_two_sided": mcnemar_exact_two_sided(improved, harmed),
            "naive_column_bootstrap_ci95": bootstrap_columns(diffs),
            "table_cluster_bootstrap_ci95": bootstrap_table_clusters(rows),
        },
        "interpretation": (
            "Exploratory only: report the pooled per-column effect and dependence-aware "
            "cluster interval; do not replace the frozen table-level E3 or switch Version B."
        ),
        "rows": rows,
    }
    output = EVAL / "vgmc_column_sensitivity.json"
    output.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"output": str(output), **out["column_level"]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
