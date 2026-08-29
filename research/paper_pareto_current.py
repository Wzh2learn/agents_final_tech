#!/usr/bin/env python3
"""Pareto current version (cost-discriminability, uses W1 T1 arm A existing artifact; not the final version).

Data source: logs/graph/eval/t1_eval_baseline_comparison.json (arm_a four protocols, derived per_mutant).
Cost definition (design draft T1 3.1): E1.1 = 2 root-score units; E1.2-E1.4 = 12 leaves.
Final version awaits T4 (question-set budget gradient + random30/greedy points); this output is marked current_v0.
Zero endpoint, no RNG.
"""
from __future__ import annotations
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
T1 = REPO / "logs" / "graph" / "eval" / "t1_eval_baseline_comparison.json"
OUTFIG = REPO / "docs" / "experiments" / "figures_paper" / "fig_pareto_current.png"
OUTJSON = REPO / "logs" / "graph" / "eval" / "pareto_current_v0.json"


def main() -> int:
    d = json.loads(T1.read_text(encoding="utf-8"))
    protos = d["arm_a"]["protocols"]
    pts = []
    for name, pr in protos.items():
        pm = pr["per_mutant"]
        cost = 2 if "end_to_end" in name else 12
        pooled = round(sum(m["sep_blended"] for m in pm) / len(pm), 6)
        rootsep = round(sum(m["sep_tree_root"] for m in pm) / len(pm), 6)
        det = sum(1 for m in pm if m["primary_detect"])
        worst = min((m["sep_tree_root"] for m in pm), key=lambda v: v)
        worst_id = [m["id"] for m in pm if m["sep_tree_root"] == worst][0]
        # localization is protocol-aware: end-to-end has no leaf attribution by design (report W1 3.2)
        loc = 0.0 if "end_to_end" in name else round(sum(1 for m in pm if m["primary_detect"] and m["localizable"]) / max(1, det), 3)
        pts.append({"protocol": name, "cost_scored_units": cost,
                    "pooled_separation": pooled, "tree_root_separation": rootsep,
                    "detected": det, "n_mutants": len(pm),
                    "worst_mutant": {"id": worst_id, "sep": worst}, "localization": loc})
    fig, ax = plt.subplots(figsize=(5.6, 3.5))
    for pt in pts:
        ax.plot(pt["cost_scored_units"], pt["pooled_separation"], "o", ms=8)
        ax.annotate("%s\n%d/9 det, loc %.1f, worst %.2f" % (
            pt["protocol"], pt["detected"], pt["localization"], pt["worst_mutant"]["sep"]),
            (pt["cost_scored_units"], pt["pooled_separation"]),
            textcoords="offset points", xytext=(10, 4), fontsize=7)
    ax.set_xlabel("Evaluation cost (scored checkpoint units)")
    ax.set_ylabel("Discriminability (mean pooled separation, arm A)")
    ax.set_title("Cost-discriminability Pareto, current version (W1 T1 arm A);\n"
                 "final version pending T4 budget gradient", fontsize=8.5)
    ax.grid(alpha=0.2)
    OUTFIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTFIG, bbox_inches="tight", dpi=150)
    plt.close(fig)
    OUTJSON.write_text(json.dumps({
        "version": "current_v0",
        "source": "logs/graph/eval/t1_eval_baseline_comparison.json",
        "source_sha256": d["payload_sha256"],
        "cost_definition": "E1.1=2 root units; E1.2-E1.4=12 leaves (design T1 3.1)",
        "note": "current version only; replaced by T4 Pareto (budget gradient + 5-group)",
        "points": pts,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("fig:", OUTFIG)
    print("json:", OUTJSON)
    for pt in pts:
        print(pt["protocol"], pt["cost_scored_units"], pt["pooled_separation"], pt["detected"], pt["localization"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
