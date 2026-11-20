"""Render the matched strict-accuracy frontiers from saved report JSON."""

import argparse
import json
from math import isfinite
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator, PercentFormatter


DATASETS = {'finqa': 'FinQA', 'tatqa': 'TAT-QA'}
CONTRACT = 'cascade/compiled/contract_8b_free_qwen_deepseek'
FIXED_ANCHORS = {
    'cascade/compiled/always_deepseek': ('DeepSeek direct', -13),
    'cascade/compiled/nonexecution_deepseek_qwen': ('DeepSeek → Qwen', 11),
    'cascade/compiled/nonexecution_8b_qwen_deepseek': ('8B → Qwen → DeepSeek', -17),
}
STYLES = {
    'Contract cascade': ('*', '#CC4422', 105),
    'CAR': ('D', '#0072B2', 40),
    'BudgetVerify / TabFM': ('^', '#88549C', 41),
    'BudgetVerify / GBM': ('s', '#B67500', 38),
    'Author Cascade': ('P', '#00815F', 44),
    'Fixed / single model': ('o', '#747C87', 25),
}


def family(name, metadata):
    if name == CONTRACT:
        return 'Contract cascade'
    if name == 'car':
        return 'CAR'
    if name.startswith('budgetverify/') and '/lambda_' in name:
        return 'BudgetVerify / TabFM' if '/tabfm/' in name else 'BudgetVerify / GBM'
    if metadata.get('family') == 'Cascade Routing adaptation':
        return 'Author Cascade'
    return 'Fixed / single model'


def plot_axis(axis, report, *, tokens):
    scope = 'common_complete_usage' if tokens else 'all'
    cost_field = 'total_tokens' if tokens else 'mean_serial_call_seconds'
    frontier_field = 'token_frontier' if tokens else 'serial_call_time_frontier'
    group = report['strata'][scope]
    n = group['n']
    points = {}
    missing = 0
    for name, point in group['policies'].items():
        cost = point.get(cost_field)
        if cost is None:
            missing += 1
            continue
        accuracy = point['accuracy']
        if n < 1 or point['n'] != n or not isfinite(cost) or cost < 0 or not 0 <= accuracy <= 1:
            raise ValueError(f'{report["dataset"]}/{scope}: invalid matched point for {name}')
        points[name] = (cost / n if tokens else cost, accuracy)
    if not points:
        raise ValueError(f'{report["dataset"]}/{scope}: no usable policy points')
    frontier = set(group[frontier_field]) & points.keys()
    marked = sorted({points[name] for name in frontier})
    if not marked:
        raise ValueError(f'{report["dataset"]}/{scope}: no usable recorded frontier')

    metadata = report.get('policy_metadata', {})
    kinds = {name: family(name, metadata.get(name, {})) for name in points}
    present = set(kinds.values())
    for depth, (kind, (marker, color, size)) in enumerate(reversed(STYLES.items()), start=3):
        coordinates = [points[name] for name in points if kinds[name] == kind]
        if coordinates:
            axis.scatter(*zip(*coordinates), marker=marker, color=color, s=size,
                         edgecolors='white', linewidths=.35, alpha=.78 if depth == 3 else .95, zorder=depth)
    x, y = zip(*marked)
    axis.plot(x, y, color='#253849', linestyle='--', linewidth=1.05, zorder=2)
    axis.scatter(x, y, s=130, facecolors='none', edgecolors='#253849', linewidths=.9, zorder=10)
    cohort = f'complete usage, n={n:,}' if tokens else f'all matched, n={n:,}'
    title = f'{DATASETS[report["dataset"]]}  ·  {cohort}'
    if missing:
        title += f'\nUnavailable policy costs: {missing}'
    axis.set_title(title, loc='left', fontsize=9.2, fontweight='bold', pad=8)
    axis.set_xlabel('Mean recorded model tokens / question' if tokens else 'Mean recorded serial call time / question (s)')
    axis.xaxis.set_major_locator(MaxNLocator(nbins=5))
    if tokens and max(cost for cost, _ in points.values()) >= 1000:
        axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value / 1000:g}k' if value else '0'))
    axis.yaxis.set_major_locator(MaxNLocator(nbins=5))
    axis.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    axis.set_axisbelow(True)
    axis.grid(axis='y', color='#D9E0E6', linewidth=.55)
    axis.spines[['top', 'right']].set_visible(False)
    axis.margins(x=.08, y=.11)
    left, right = axis.get_xlim()
    for name, (label, offset) in FIXED_ANCHORS.items():
        if name in frontier:
            coordinate = points[name]
            place_left = coordinate[0] > left + .60 * (right - left)
            axis.annotate(label, coordinate, xytext=(-7 if place_left else 7, offset),
                          textcoords='offset points', ha='right' if place_left else 'left',
                          va='center', fontsize=7, color='#344555', zorder=11)
    return present


def render(reports, output, label):
    matplotlib.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8.5,
                                'axes.edgecolor': '#6A7581', 'axes.labelcolor': '#182632',
                                'xtick.color': '#45535F', 'ytick.color': '#45535F', 'pdf.fonttype': 42})
    figure, axes = plt.subplots(len(reports), 2, squeeze=False, sharey='row',
                               figsize=(7.3, 2.35 * len(reports) + 1.07))
    present = set()
    for report, (token_axis, time_axis) in zip(reports, axes, strict=True):
        present.update(plot_axis(token_axis, report, tokens=True))
        present.update(plot_axis(time_axis, report, tokens=False))
        token_axis.set_ylabel('Strict accuracy')
    figure.suptitle(label, x=.08, ha='left', y=.97, fontsize=12, fontweight='bold')
    legend = [Line2D([], [], marker=marker, color=color, markersize=7 if marker == '*' else 5,
                     linestyle='none', label=kind)
              for kind, (marker, color, _) in STYLES.items() if kind in present]
    legend.append(Line2D([], [], color='#253849', linestyle='--', marker='o', markerfacecolor='none',
                         markersize=6, linewidth=1, label='Point-estimate frontier'))
    figure.legend(handles=legend, loc='lower center', bbox_to_anchor=(.5, .012),
                  ncols=4, frameon=False, handletextpad=.45, columnspacing=1.35)
    figure.tight_layout(rect=(.015, .61 / figure.get_figheight(), .998, 1 - .33 / figure.get_figheight()))
    output.parent.mkdir(parents=True, exist_ok=True)
    for extension in ('pdf', 'png'):
        figure.savefig(output.parent / f'{output.name}.{extension}', dpi=400, facecolor='white')
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True, help='Output basename without .pdf or .png')
    parser.add_argument('--label', default='Official benchmark')
    args = parser.parse_args()
    if len(args.input) not in (1, 2):
        parser.error('Pass one or two frontier reports')
    reports = [json.loads(path.read_text(encoding='utf-8')) for path in args.input]
    datasets = {report.get('dataset') for report in reports}
    if not datasets <= DATASETS.keys() or len(datasets) != len(reports):
        parser.error('Reports must identify distinct FinQA or TAT-QA datasets')
    try:
        render(reports, args.output, args.label)
    except ValueError as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
