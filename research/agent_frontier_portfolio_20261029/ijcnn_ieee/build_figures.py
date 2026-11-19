"""Render the three IJCNN figures from published aggregate experiment results."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Patch, Rectangle
from matplotlib.ticker import MaxNLocator


HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "results"
INK = "#1E2936"
SUBTLE = "#4D5D6B"
LINE = "#BBC6CF"
BLUE = "#005F96"
ORANGE = "#A34816"
GREEN = "#006F56"
GRAY = "#656565"
PALE_BLUE = "#EAF3F8"
PALE_GREEN = "#EAF4EF"
PALE_ORANGE = "#FAEEE7"
LIGHT = "#F2F5F7"
WIDTH = 7.12

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8,
    "axes.titlesize": 8.6, "axes.titleweight": "bold", "axes.edgecolor": LINE,
    "axes.linewidth": 0.65, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": SUBTLE, "ytick.color": SUBTLE, "xtick.labelsize": 7,
    "ytick.labelsize": 7, "pdf.fonttype": 42, "mathtext.fontset": "dejavusans",
})


def export(fig, folder, name):
    for extension in ("pdf", "png"):
        fig.savefig(folder / f"{name}.{extension}", dpi=600, facecolor="white")
    plt.close(fig)


def box(ax, x, y, width, height, content, color=LIGHT, size=7.8, bold=False):
    ax.add_patch(Rectangle((x, y), width, height, facecolor=color, edgecolor=LINE, linewidth=0.55))
    ax.text(x + width / 2, y + height / 2, content, ha="center", va="center", fontsize=size,
            fontweight="bold" if bold else "normal", linespacing=1.3)


def arrow(ax, start, end, *, color=SUBTLE, head=True):
    style = "-|>" if head else "-"
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=7, color=color,
                                 linewidth=0.65, shrinkA=0, shrinkB=0))


def methodology(folder):
    fig, ax = plt.subplots(figsize=(WIDTH, 3.10))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")

    for x, letter, title, accent in (
        (0.025, "A", "Paired local correction", BLUE),
        (0.353, "B", "Shared-teacher utility", GREEN),
        (0.681, "C", "Scale adaptation", ORANGE),
    ):
        ax.text(x, 0.940, letter, color=accent, weight="bold", fontsize=10, va="center")
        ax.text(x + 0.030, 0.940, title, weight="bold", fontsize=9.1, va="center")
        ax.hlines(0.892, x, x + 0.293, color=accent, linewidth=1.25)

    box(ax, 0.025, 0.667, 0.139, 0.151, "Before recovery\nFailed state", PALE_BLUE)
    box(ax, 0.179, 0.667, 0.139, 0.151, "After recovery\nRestored state", PALE_BLUE)
    for x in (0.0945, 0.2485):
        arrow(ax, (x, 0.667), (x, 0.588))
    box(ax, 0.025, 0.436, 0.293, 0.152, "Same execution-verified\nwrong-program counterexamples")
    arrow(ax, (0.1715, 0.436), (0.1715, 0.353), color=BLUE)
    box(ax, 0.025, 0.209, 0.293, 0.144, "Local corrector\nPreserve or revise", PALE_BLUE, bold=True)
    arrow(ax, (0.321, 0.280), (0.349, 0.280), color=BLUE)

    box(ax, 0.353, 0.727, 0.293, 0.117, r"One teacher trajectory from $p^0$", PALE_GREEN)
    arrow(ax, (0.4995, 0.727), (0.4995, 0.684), head=False)
    ax.hlines(0.684, 0.401, 0.598, color=SUBTLE, linewidth=0.65)
    for x, content in ((0.353, "View 1"), (0.452, "View 2"), (0.551, "View $v$")):
        center = x + 0.0475
        arrow(ax, (center, 0.684), (center, 0.642))
        box(ax, x, 0.515, 0.095, 0.127, content)
        arrow(ax, (center, 0.515), (center, 0.468), head=False)
    ax.hlines(0.468, 0.401, 0.598, color=SUBTLE, linewidth=0.65)
    ax.text(0.4995, 0.415, "Label each state with the same teacher", ha="center", fontsize=7.25)
    arrow(ax, (0.4995, 0.390), (0.4995, 0.353), color=GREEN)
    box(ax, 0.353, 0.209, 0.293, 0.144, "Rank by expected gain\nUp to $K$ acquisitions with guard $G$", PALE_GREEN, size=7.45, bold=True)

    box(ax, 0.681, 0.727, 0.293, 0.117, r"Hold the executed program $p$ fixed", PALE_ORANGE)
    arrow(ax, (0.8275, 0.727), (0.8275, 0.682), color=ORANGE)
    ax.text(0.8275, 0.649, "Score scale variants on TRAIN", ha="center", fontsize=7.6)
    arrow(ax, (0.8275, 0.629), (0.8275, 0.607), head=False)
    ax.hlines(0.607, 0.751, 0.904, color=SUBTLE, linewidth=0.65)
    for x, content in ((0.681, "Passing scale\nKEEP"), (0.835, "Failing scale\nREPLACE")):
        center = x + 0.0695
        arrow(ax, (center, 0.607), (center, 0.564))
        box(ax, x, 0.443, 0.139, 0.121, content)
        arrow(ax, (center, 0.443), (center, 0.353), color=ORANGE)
    box(ax, 0.681, 0.209, 0.293, 0.144, "TAT-QA scale-only adapter\nFinQA skips this module", PALE_ORANGE, bold=True)

    ax.add_patch(Rectangle((0.025, 0.036), 0.949, 0.110, facecolor=LIGHT, edgecolor=LINE, linewidth=0.55))
    ax.text(0.045, 0.091, "Expected gain", va="center", fontweight="bold", fontsize=8.3)
    ax.text(0.244, 0.091, r"$\Delta_\kappa(s,u) = q_\kappa(s)a_{\kappa,u}(s) - [1-q_\kappa(s)]b_{\kappa,u}(s)$",
            va="center", fontsize=9.1)
    ax.text(0.949, 0.091, r"$\kappa$ is the task's scoring contract", va="center", ha="right", color=SUBTLE, fontsize=7.4)
    export(fig, folder, "method")


# Raw-teacher counts from the matched Table 1 pools. Teacher costs for full
# execution come from the terminal rows of results/FINQA_BUDGET_CURVES.csv.
PANELS = (
    ("DEV64", "Development (64)", 64, 8, 18, 40),
    ("FORWARD57", "Prospective (57)", 57, 7, 16, 32),
    ("CONFIRM64", "Confirmation (64)", 64, 8, 18, 41),
)
POLICY = {
    "value": ("Value", BLUE, "-"),
    "risk": ("Risk", ORANGE, (0, (5, 2))),
    "single": ("Single state", GREEN, (0, (4, 2, 1, 2))),
    "random": ("Uniform random mean", GRAY, (0, (1.3, 2.1))),
}


def budget_data():
    data = {key: {policy: [] for policy in ("value", "risk", "single")} for key, *_ in PANELS}
    with (RESULTS / "FINQA_BUDGET_CURVES.csv").open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            if row["panel"] in data and row["policy"] in data[row["panel"]]:
                data[row["panel"]][row["policy"]].append(
                    (int(row["K"]), int(row["teacher_tokens"]), int(row["success"])))
    for key, _, n, _, _, _ in PANELS:
        curves = data[key]
        for policy, series in curves.items():
            series.sort()
            if [point[0] for point in series] != list(range(n + 1)):
                raise ValueError(f"Missing frozen points: {key}, {policy}")
        value = curves["value"]
        if any(series[0] != value[0] or series[-1] != value[-1] for series in curves.values()):
            raise ValueError(f"Frozen outcome pool does not match: {key}")
        baseline = value[0][2]
        gain = value[-1][2] - baseline
        total = value[-1][1]
        curves["random"] = [(k, total * k / n, baseline + gain * k / n) for k in range(n + 1)]
    if data["CONFIRM64"]["value"][8] != (8, 85971, 41) or data["CONFIRM64"]["value"][-1][1] != 538488:
        raise ValueError("Confirmation cost anchors do not match the frozen manuscript")
    return data


def axis_style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=2.5, width=0.55, pad=2.4)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=LINE, alpha=0.48, linewidth=0.55)


def budget(folder):
    data = budget_data()
    fig, axes = plt.subplots(2, 3, figsize=(WIDTH, 3.30))
    fig.subplots_adjust(left=0.085, right=0.987, top=0.830, bottom=0.128, hspace=0.57, wspace=0.24)
    for column, (key, title, n, low, primary, raw) in enumerate(PANELS):
        curves = data[key]
        total = curves["value"][-1][1] / 1000
        low_end = min(min(row[2] for row in c) for c in curves.values())
        high_end = max(max(row[2] for row in c) for c in curves.values())
        for dim, ax in enumerate(axes[:, column]):
            axis_style(ax)
            ax.set_ylim(min(low_end, raw) - 0.55, max(high_end, raw) + 0.85)
            ax.yaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
            if dim == 0:
                ax.set_title(f"({chr(97 + column)}) {title}", loc="left", pad=7)
                ax.set_xticks([0, low, primary, 32, 48, n])
                ax.set_xlim(-1.5, n + 3)
            else:
                ax.set_xlim(-12, 562)
                ax.set_xticks((0, 125, 250, 375, 500))
            for name in ("random", "single", "risk", "value"):
                _, color, line = POLICY[name]
                xs = [row[dim] / (1 if dim == 0 else 1000) for row in curves[name]]
                ax.plot(xs, [row[2] for row in curves[name]], color=color, linestyle=line,
                        linewidth=1.35 if name == "value" else 1.15, zorder=3 if name == "value" else 2)
            ax.plot(n if dim == 0 else total, raw, "D", color=INK, markerfacecolor="white",
                    markeredgewidth=1.0, markersize=4.6, zorder=6, clip_on=False)
            for k in (low, primary):
                _, value_tokens, successes = curves["value"][k]
                ax.plot(k if dim == 0 else value_tokens / 1000, successes, "o",
                        color=BLUE, markerfacecolor="white" if k == low else BLUE,
                        markeredgewidth=1, markersize=4.1, zorder=7)
        if key == "CONFIRM64":
            ax = axes[1, column]
            ax.plot((85.971, 538.488), (41, 41), color=GRAY, linestyle=(0, (2, 2)),
                    linewidth=0.65, zorder=1)
            for x, label, target_x, align, color in (
                (85.971, "41/64 at 85,971", 45, "left", BLUE),
                (538.488, "41/64 at 538,488", 540, "right", INK),
            ):
                ax.annotate(label, (x, 41), xytext=(target_x, 39.55), color=color, fontsize=6.75, ha=align,
                            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.45},
                            arrowprops={"arrowstyle": "-", "color": color, "linewidth": 0.65})
            ax.text(352, 40.42, "84% fewer teacher tokens", color=BLUE, ha="center", va="center", fontsize=6.5)
    fig.text(0.025, 0.489, "Native successes", va="center", rotation="vertical", fontsize=8.2)
    fig.text(0.533, 0.484, "Teacher task budget $K$", ha="center", fontsize=8.2)
    fig.text(0.533, 0.031, "Teacher tokens (thousands)", ha="center", fontsize=8.2)
    handles = [Line2D([], [], label=label, color=color, linestyle=line, linewidth=1.5)
               for label, color, line in POLICY.values()]
    handles.append(Line2D([], [], label="Full raw teacher", color=INK, linestyle="none", marker="D",
                          markerfacecolor="white", markersize=4.6))
    fig.legend(handles=handles, loc="upper center", ncol=5, frameon=False, fontsize=7.6, handlelength=2.4,
               columnspacing=1.47, bbox_to_anchor=(0.523, 0.997))
    export(fig, folder, "finqa_budget")


# The manuscript and results/IJCNN_EXPERIMENT_TABLES.md report all outcomes
# at a fixed baseline within panel. An additional C3 panel can be supplied
# from verified aggregates without importing examples or reference labels.
CHANGES = (
    ("A", "FinQA local correction", 64, 33, (
        ("SFT", 33, 0, 0), ("Pre only", 29, 3, 7),
        ("Post only", 34, 1, 0), ("Paired", 37, 4, 0),
    )),
    ("B", "TAT-QA disclosure", 32, 7, (
        ("Original ($T_0$)", 17, 14, 4), ("Current ($T_1$)", 15, 9, 1),
    )),
    ("C", "TAT-QA scale doses", 64, 13, (
        ("Ord. 128", 22, 19, 10), ("Pair 128", 29, 16, 0),
        ("Ord. 160", 23, 20, 10), ("Pair 160", 28, 21, 6),
    )),
)


def recovery_harm(folder, extension_path):
    panels = list(CHANGES)
    if extension_path is not None:
        extension = json.loads(extension_path.read_text(encoding="utf-8"))
        panels.append(("D", extension["title"], extension["n"], extension["baseline"],
                       [tuple(row) for row in extension["rows"]]))
    if extension_path is None:
        fig, axes = plt.subplots(1, 3, figsize=(WIDTH, 2.43))
        fig.subplots_adjust(left=0.133, right=0.980, top=0.690, bottom=0.240, wspace=0.62)
    else:
        fig, axes = plt.subplots(2, 2, figsize=(WIDTH, 3.80))
        fig.subplots_adjust(left=0.140, right=0.980, top=0.800, bottom=0.162, wspace=0.48, hspace=0.92)
    for ax, (letter, title, n, baseline, rows) in zip(axes.flat, panels):
        if any(success != baseline + recovered - harmed or not 0 <= recovered <= n - baseline
               or not 0 <= harmed <= baseline for _, success, recovered, harmed in rows):
            raise ValueError(f"Unbalanced recovery/harm totals for panel {letter}")
        labels, totals, recovered, harmed = zip(*rows)
        positions = list(range(len(rows)))
        ax.set_title(f"({letter.lower()}) {title}", loc="left", pad=22, fontsize=7.5)
        ax.text(0.0, 1.073, f"{baseline}/{n} correct at baseline", transform=ax.transAxes,
                fontsize=7.1, color=SUBTLE)
        ax.barh(positions, recovered, height=0.50, color=BLUE)
        ax.barh(positions, [-count for count in harmed], height=0.50, color="white", edgecolor=ORANGE,
                hatch="////", linewidth=0.65)
        span = max(max(recovered), max(harmed), 5)
        bounds = (max(max(harmed), span * 0.36), max(max(recovered), span * 0.72))
        ax.set_xlim(-bounds[0] - span * 0.22, bounds[1] + span * 0.22)
        ax.set_ylim(len(rows) - 0.52 if len(rows) > 2 else 2.5, -0.55)
        ax.axvline(0, color=SUBTLE, linewidth=0.65)
        ax.set_yticks(positions, [f"{label}  ({total})" for label, total in zip(labels, totals)])
        ax.tick_params(axis="y", length=0, pad=2, labelsize=7)
        ax.set_xticks([])
        ax.spines[:].set_visible(False)
        for i, rescues, losses in zip(positions, recovered, harmed):
            ax.text(rescues + span * 0.05, i, str(rescues), fontsize=7, va="center", color=BLUE)
            ax.text(-losses - span * 0.05, i, str(losses), fontsize=7, va="center", ha="right", color=ORANGE)
    fig.legend(handles=[Patch(facecolor="white", edgecolor=ORANGE, hatch="////", label="Previously correct, now wrong"),
                        Patch(facecolor=BLUE, label="Previously wrong, now correct")],
               loc="lower center", ncol=2, fontsize=7.6, frameon=False, bbox_to_anchor=(0.505, 0.078))
    fig.text(0.505, 0.033, "Parentheses show total correct. Bar scales differ by panel.",
             ha="center", color=SUBTLE, fontsize=7.1)
    export(fig, folder, "recovery_harm")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE / "figures")
    parser.add_argument("--c3-extension", type=Path,
                        help="Optional public aggregate JSON: title, n, baseline, rows [label, success, R, H].")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    methodology(args.out)
    budget(args.out)
    recovery_harm(args.out, args.c3_extension)


if __name__ == "__main__":
    main()
