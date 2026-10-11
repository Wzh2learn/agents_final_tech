#!/usr/bin/env python3
"""Build versioned multi-leaf figure candidates from frozen result artifacts."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research/stage_e_multileaf_20261010/results"
OUT = ROOT / "docs/research/figures_multileaf"
PREDICTIONS = RESULTS / "multileaf_prediction_rows.jsonl"
RESULT = RESULTS / "multileaf_formal_results.json"
TREES = ROOT / "config/eval_checkpoint_trees.json"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 160,
    "savefig.bbox": "tight",
})


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def leaf_order(tree: dict) -> list[str]:
    leaves = []

    def visit(node: dict) -> None:
        children = node.get("children") or []
        if children:
            for child in children:
                visit(child)
        else:
            leaves.append(str(node["id"]))

    for root in tree.get("trees", []):
        visit(root)
    return leaves


def effective_weights(tree: dict) -> dict[str, float]:
    weights = {}

    def visit(node: dict, prefix: float) -> None:
        children = node.get("children") or []
        if not children:
            weights[str(node["id"])] = prefix
            return
        total = sum(float(child.get("weight", 1)) for child in children)
        for child in children:
            visit(child, prefix * float(child.get("weight", 1)) / total)

    roots = tree.get("trees", [])
    root_total = sum(float(root.get("weight", 1)) for root in roots)
    for root in roots:
        visit(root, float(root.get("weight", 1)) / root_total)
    return weights


def build() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in PREDICTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    tree = json.loads(TREES.read_text(encoding="utf-8"))
    leaves = leaf_order(tree)
    stages = ("M", "R", "N")
    signatures = np.asarray([
        [result["response_signatures"][stage][0][0][leaves.index(leaf)] for leaf in leaves]
        for stage in stages
    ])

    fig, ax = plt.subplots(figsize=(10.5, 3.2))
    image = ax.imshow(signatures, cmap=matplotlib.colors.ListedColormap(["#F7F7F7", "#C4553D"]), vmin=0, vmax=1, aspect="auto")
    ax.set_yticks(range(len(stages)))
    ax.set_yticklabels([f"{stage} (n=72)" for stage in stages])
    ax.set_xticks(range(len(leaves)))
    ax.set_xticklabels([leaf.replace(".", ".\n") for leaf in leaves], rotation=45, ha="right", fontsize=7)
    ax.set_title("Controlled M/R/N response signatures (contract-derived codebook)", fontsize=11)
    ax.set_xlabel("Frozen checkpoint leaf order")
    ax.set_ylabel("Stage")
    for row in range(signatures.shape[0]):
        for col in range(signatures.shape[1]):
            ax.text(col, row, str(int(signatures[row, col])), ha="center", va="center", fontsize=7, color="white" if signatures[row, col] else "black")
    fig.colorbar(image, ax=ax, ticks=[0, 1], label="response bit")
    signature_png = OUT / "fig_multileaf_response_signatures.png"
    signature_svg = OUT / "fig_multileaf_response_signatures.svg"
    fig.savefig(signature_png)
    fig.savefig(signature_svg)
    plt.close(fig)

    weight_vector = np.asarray([effective_weights(tree)[leaf] for leaf in leaves], dtype=float)
    x_bits = np.asarray([[row["response_vector"][leaf] for leaf in leaves] for row in rows], dtype=float)
    flat = 10.0 * x_bits.mean(axis=1)
    hierarchical = 10.0 * (x_bits * weight_vector).sum(axis=1)
    slope, intercept = np.polyfit(flat, hierarchical, 1)
    counts = Counter(zip(np.round(flat, 6), np.round(hierarchical, 6)))
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    for (x_value, y_value), count in sorted(counts.items()):
        ax.scatter([x_value], [y_value], s=28 + 6 * count, color="#4C8CB4", edgecolor="black", linewidth=0.4)
        ax.annotate(f"n={count}", (x_value, y_value), xytext=(5, 5), textcoords="offset points", fontsize=7)
    grid = np.linspace(float(min(flat)), float(max(flat)), 100)
    ax.plot(grid, slope * grid + intercept, color="#C4553D", linewidth=1.1, label=f"linear fit: h={slope:.3f}f+{intercept:.3f}")
    ax.set_xlabel("Flat score (10 × mean response)")
    ax.set_ylabel("Hierarchical score (10 × weighted response)")
    ax.set_title("Multi-leaf scores are non-affine (secondary analysis)", fontsize=11)
    ax.legend(frameon=False, fontsize=8)
    ax.grid(True, alpha=0.2)
    relation_png = OUT / "fig_multileaf_flat_hierarchy_relation.png"
    relation_svg = OUT / "fig_multileaf_flat_hierarchy_relation.svg"
    fig.savefig(relation_png)
    fig.savefig(relation_svg)
    plt.close(fig)

    manifest = {
        "namespace": "MULTILEAF_FIGURE_CANDIDATES",
        "status": "EXPLORATORY_VISUALIZATION_NOT_INSERTED_IN_PAPER",
        "sources": {
            str(PREDICTIONS): sha256_file(PREDICTIONS),
            str(RESULT): sha256_file(RESULT),
            str(TREES): sha256_file(TREES),
        },
        "outputs": {
            path.name: {"sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in sorted(OUT.iterdir())
            if path.is_file() and path.name != "manifest.json"
        },
        "caption_boundaries": {
            "signatures": "three controlled stage classes; direct/derived codebook, not natural trace",
            "flat_hierarchy": "secondary score relation; no hierarchy superiority or matched-FPR claim",
        },
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, sort_keys=True))
