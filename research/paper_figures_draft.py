#!/usr/bin/env python3
"""Paper figure drafts (zero-endpoint; all data traceable to repo artifacts; no fabricated values).

Outputs (docs/experiments/figures_paper/):
  fig_visibility_spectrum.png  C1 six-type visibility spectrum
                               <- logs/graph/eval/checkpoint_discrimination_tables_v2.json
  fig_checkpoint_trees.png     evaluation checkpoint tree structure (2 trees, expert weights)
                               <- config/eval_checkpoint_trees.json
  fig_pareto.png               cost-discriminability Pareto: generated only when the T4
                               artifact (logs/graph/eval/t4_pso_fair_comparison.json) exists;
                               otherwise skipped with explicit note (never mocked).

Usage: PYTHONPATH=src python research/paper_figures_draft.py
Deterministic: fixed style, no RNG, no network.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "experiments" / "figures_paper"

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
})

PATENT_GROUPS = {  # patent crosswalk (same artifact, key patent_crosswalk)
    "alias-type": ["alias_variant", "mixed_lang"],
    "column-name-type": ["ocr_similar", "prefix_noise"],
    "type-type": ["unit_suffix", "date_variant"],
}
GROUP_COLOR = {"alias-type": "#4C8CB4", "column-name-type": "#C4553D", "type-type": "#5E9C63"}


def fig_visibility_spectrum() -> str:
    src = REPO / "logs" / "graph" / "eval" / "checkpoint_discrimination_tables_v2.json"
    d = json.loads(src.read_text(encoding="utf-8"))
    by_type = d["by_type"]
    rows = sorted(by_type.items(), key=lambda kv: kv[1]["visibility_rate"])
    names = [k for k, _ in rows]
    rates = [v["visibility_rate"] for _, v in rows]
    ns = [v["n_injections"] for _, v in rows]
    absorbed = [v["n_absorbed"] for _, v in rows]
    group_of = {}
    for g, members in PATENT_GROUPS.items():
        for m in members:
            group_of[m] = g
    colors = [GROUP_COLOR[group_of[n]] for n in names]

    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    bars = ax.bar(range(len(names)), rates, color=colors, edgecolor="black", linewidth=0.4)
    for i, (r, n, a) in enumerate(zip(rates, ns, absorbed)):
        ax.text(i, r + 0.02, f"{r:.2f}\nn={n}", ha="center", va="bottom", fontsize=7.5)
        if a:
            ax.text(i, 0.02, f"absorbed={a}", ha="center", va="bottom", fontsize=6.5, color="white")
    ax.axhline(0.2, color="grey", lw=0.6, ls="--")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels([n.replace("_", "\n") for n in names], fontsize=7.5)
    ax.set_ylim(0, 1.22)
    ax.set_ylabel("Injection-level visibility rate")
    ax.set_title("Defect visibility spectrum by injection type (95 tables / 118 injections;\n"
                 "drop threshold 2.0; checkpoint_discrimination_tables_v2.json)", fontsize=8.5)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=GROUP_COLOR[g]) for g in PATENT_GROUPS]
    ax.legend(handles, list(PATENT_GROUPS), loc="upper left", fontsize=7, frameon=False)
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "fig_visibility_spectrum.png"
    fig.savefig(p)
    plt.close(fig)
    return str(p)


def _layout(node, depth, counter, xs, ys, labels):
    kids = node.get("children", [])
    if not kids:
        x = counter[0]
        counter[0] += 1
    else:
        cx = []
        for c in kids:
            _layout(c, depth + 1, counter, xs, ys, labels)
            cx.append(xs[c["id"]])
        x = sum(cx) / len(cx)
    xs[node["id"]] = x
    ys[node["id"]] = -depth
    labels[node["id"]] = node


def fig_checkpoint_trees() -> str:
    src = REPO / "config" / "eval_checkpoint_trees.json"
    d = json.loads(src.read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    for tree in d["trees"]:
        xs, ys, labels = {}, {}, {}
        _layout(tree, 0, [0 if not xs else max(xs.values()) + 2], xs, ys, labels)
        # recompute with proper offset between the two trees
        pass
    # single-pass layout across both trees with a gap
    xs, ys, labels = {}, {}, {}
    counter = [0]
    for tree in d["trees"]:
        _layout(tree, 0, counter, xs, ys, labels)
        counter[0] += 2
    def draw(node):
        x, y = xs[node["id"]], ys[node["id"]]
        leaf = not node.get("children")
        w = node.get("weight", "")
        lbl = node["id"].split(".")[-1]
        t = ax.text(x, y, f"{lbl}\nw={w}", ha="center", va="center", fontsize=6.8,
                    bbox=dict(boxstyle="round,pad=0.25",
                              fc="#DCE9F2" if not leaf else "#F7E9C9", ec="black", lw=0.5))
        for c in node.get("children", []):
            cx, cy = xs[c["id"]], ys[c["id"]]
            ax.plot([x, cx], [y - 0.28, cy + 0.28], color="0.35", lw=0.7, zorder=0)
            draw(c)
    for tree in d["trees"]:
        draw(tree)
        en = {"parse": "Parsing tree (doc / table / field / reconcile)",
              "qa": "QA tree (retrieval / faithfulness / numeric / citation / refusal)"}
        ax.text(xs[tree["id"]], ys[tree["id"]] + 0.55, en.get(tree["id"], tree["label"]),
                ha="center", fontsize=8, fontweight="bold")
    ax.set_xlim(min(xs.values()) - 1, max(xs.values()) + 1)
    ax.set_ylim(min(ys.values()) - 0.9, 1.1)
    ax.axis("off")
    ax.set_title("Evaluation checkpoint trees (2 roots / 12 scored leaves; sibling-normalized "
                 "weighted aggregation; hinge gates on doc/ok, exact_numeric, number_grounding; "
                 "config/eval_checkpoint_trees.json)", fontsize=8)
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "fig_checkpoint_trees.png"
    fig.savefig(p)
    plt.close(fig)
    return str(p)


def fig_pareto() -> str:
    src = REPO / "logs" / "graph" / "eval" / "t4_pso_fair_comparison.json"
    if not src.exists():
        return ("SKIPPED fig_pareto.png: T4 artifact absent (%s). "
                "Pareto data pending W2 window (equal/expert/random/greedy/PSO + budget gradient); "
                "no mock data by pre-registration discipline." % src.name)
    d = json.loads(src.read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    for series in d.get("pareto", []):
        ax.plot(series["cost"], series["discriminability"], marker="o", ms=3, label=series["protocol"])
    ax.set_xlabel("Evaluation cost (scored checkpoints / calls)")
    ax.set_ylabel("Discriminability (mean separation)")
    ax.legend(fontsize=7, frameon=False)
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "fig_pareto.png"
    fig.savefig(p)
    plt.close(fig)
    return str(p)


def main() -> int:
    print("fig1:", fig_visibility_spectrum())
    print("fig2:", fig_checkpoint_trees())
    print("fig3:", fig_pareto())
    return 0


if __name__ == "__main__":
    sys.exit(main())
