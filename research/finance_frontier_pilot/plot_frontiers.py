"""Render matched accuracy and executable-accuracy frontiers from saved reports."""

import argparse
import json
from math import isclose, isfinite
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator, PercentFormatter


DATASETS = {'finqa': 'FinQA', 'tatqa': 'TAT-QA'}
CONTRACT = 'cascade/compiled/contract_8b_free_qwen_deepseek'
COMPILED_BUDGETVERIFY = 'BudgetVerify + compiler'
FIXED_ANCHORS = {
    'cascade/compiled/always_deepseek': ('DeepSeek direct', -13),
    'cascade/compiled/nonexecution_deepseek_qwen': ('DeepSeek → Qwen', 11),
    'cascade/compiled/nonexecution_qwen_deepseek': ('Qwen → DeepSeek', 11),
    'cascade/compiled/nonexecution_8b_qwen_deepseek': ('8B → Qwen → DeepSeek', -17),
    'oda-direct': ('8B direct', 12),
    'qwen-direct': ('Qwen direct', -14),
    'deepseek-direct': ('DeepSeek direct', -13),
    'qwen-first': ('Qwen → DeepSeek', -16),
    'ds-first': ('DeepSeek → Qwen', 11),
}
STYLES = {
    'Contract cascade': ('*', '#CC4422', 105),
    'CAR': ('D', '#0072B2', 40),
    'CAR + compiler': ('v', '#296C91', 44),
    'BudgetVerify / TabFM': ('^', '#88549C', 41),
    'BudgetVerify / GBM': ('s', '#B67500', 38),
    COMPILED_BUDGETVERIFY: ('X', '#BD447F', 56),
    'Author Cascade': ('P', '#00815F', 44),
    'Fixed / single model': ('o', '#747C87', 25),
}
ONLINE_POLICIES = {'contract', 'car', 'budgetverify', 'author-cascade', 'oda-direct',
                   'qwen-direct', 'deepseek-direct', 'qwen-first', 'ds-first'}
ONLINE_METRICS = {
    'correct': ('strict_wall_frontier', 'Strict accuracy'),
    'strict_and_executable': ('strict_and_executable_wall_frontier', 'Strict & executable rate'),
}
EXECUTABLE_FRONTIERS = {
    True: ('common_complete_usage_and_execution', 'executable_correct_token_frontier',
           'complete usage and execution'),
    False: ('common_complete_execution', 'executable_correct_serial_call_time_frontier',
            'complete execution'),
}


def family(name, metadata):
    if name in (CONTRACT, 'contract'):
        return 'Contract cascade'
    if name == 'car':
        return 'CAR'
    if name == 'car_compiled':
        return 'CAR + compiler'
    if name == 'budgetverify':
        return 'BudgetVerify / GBM' if metadata.get('method') == 'GBM' else 'BudgetVerify / TabFM'
    if name.startswith('budgetverify/') and '/lambda_' in name:
        return 'BudgetVerify / TabFM' if '/tabfm/' in name else 'BudgetVerify / GBM'
    if name.startswith(('budgetverify_compiled/gbm/', 'budgetverify_compiled/tabfm/')):
        return COMPILED_BUDGETVERIFY
    if name == 'author-cascade' or metadata.get('family') == 'Cascade Routing adaptation':
        return 'Author Cascade'
    return 'Fixed / single model'


def load_online(path):
    """Read the nine full-pair wall-time points and the adjacent frozen run contract."""
    collection = json.loads(path.read_text(encoding='utf-8'))
    contract = json.loads(path.with_name('run.json').read_text(encoding='utf-8'))
    dataset = contract.get('dataset')
    cases = contract.get('case_order', [])
    n = collection.get('planned_questions')
    policies = collection.get('complete_pair_policies', {})
    if (contract.get('schema') != 'finance-live-policy-timing-v2' or contract.get('stage') != 'eval'
            or dataset not in DATASETS or type(n) is not int or n < 1
            or collection.get('complete_paired_questions') != n or collection.get('stop_reason') is not None
            or set(policies) != ONLINE_POLICIES or len(cases) != n or len({case['id'] for case in cases}) != n
            or any(len(case['policy_order']) != len(ONLINE_POLICIES)
                   or set(case['policy_order']) != ONLINE_POLICIES for case in cases)):
        raise ValueError(f'{path}: expected a complete matched evaluation with nine policies')
    points = {}
    for name, point in policies.items():
        correct = point.get('correct')
        executable_correct = point.get('strict_and_executable')
        wall = point.get('mean_wall_seconds')
        total_wall = point.get('summed_wall_seconds')
        if (point.get('n') != n or type(correct) is not int or not 0 <= correct <= n
                or type(executable_correct) is not int or not 0 <= executable_correct <= correct
                or type(wall) not in (int, float) or not isfinite(wall) or wall < 0
                or type(total_wall) not in (int, float) or not isclose(total_wall, n * wall)):
            raise ValueError(f'{path}: invalid complete wall-time point for {name}')
        points[name] = {'n': n, 'correct': correct, 'strict_and_executable': executable_correct, 'mean_wall_seconds': wall}
    strata = {}
    for score, (field, _) in ONLINE_METRICS.items():
        recorded = collection.get(field)
        expected = {name for name, point in points.items()
                    if not any(other['mean_wall_seconds'] <= point['mean_wall_seconds']
                               and other[score] >= point[score]
                               and (other['mean_wall_seconds'] < point['mean_wall_seconds']
                                    or other[score] > point[score]) for other in points.values())}
        if not isinstance(recorded, list) or len(recorded) != len(expected) or set(recorded) != expected:
            raise ValueError(f'{path}: {field} disagrees with measured wall-time points')
        strata[score] = {'n': n, field: recorded,
                         'policies': {name: {**point, 'accuracy': point[score] / n} for name, point in points.items()}}
    budgetverify = contract.get('baseline_policies', {}).get('budgetverify', {})
    if budgetverify.get('method') not in ('GBM', 'TabFM-1.0.0-PyTorch'):
        raise ValueError(f'{path}: unknown BudgetVerify model')
    return {'dataset': dataset, 'policy_metadata': {'budgetverify': budgetverify}, 'strata': strata}


def plot_axis(axis, report, *, tokens=False, online_score=None, executable=False):
    if online_score is not None:
        scope, cost_field, frontier_field = online_score, 'mean_wall_seconds', ONLINE_METRICS[online_score][0]
        x_label = 'Mean measured online wall time / question (s)'
        cohort = 'complete paired'
    elif tokens:
        scope, cost_field, frontier_field = 'common_complete_usage', 'total_tokens', 'token_frontier'
        x_label = 'Mean recorded model tokens / question'
        cohort = 'complete usage'
    else:
        scope, cost_field, frontier_field = 'all', 'mean_serial_call_seconds', 'serial_call_time_frontier'
        x_label = 'Mean recorded serial call time / question (s)'
        cohort = 'all matched'
    if executable:
        scope, frontier_field, cohort = EXECUTABLE_FRONTIERS[tokens]
    group = report['strata'][scope]
    n = group['n']
    points = {}
    missing = 0
    for name, point in group['policies'].items():
        cost = point.get(cost_field)
        if cost is None:
            missing += 1
            continue
        score = point['strict_and_executable'] if executable else point['accuracy']
        if (n < 1 or point['n'] != n or not isfinite(cost) or cost < 0
                or (executable and type(score) is not int) or not 0 <= score <= (n if executable else 1)):
            raise ValueError(f'{report["dataset"]}/{scope}: invalid matched point for {name}')
        accuracy = score / n if executable else score
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
    title = f'{DATASETS[report["dataset"]]}  ·  {cohort}, n={n:,}'
    if missing:
        title += f'\nUnavailable policy costs: {missing}'
    axis.set_title(title, loc='left', fontsize=9.2, fontweight='bold', pad=8)
    axis.set_xlabel(x_label)
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
    bottom, top = axis.get_ylim()
    for name, (label, offset) in FIXED_ANCHORS.items():
        if name in frontier:
            coordinate = points[name]
            place_left = coordinate[0] > left + .60 * (right - left)
            if online_score is not None and offset < 0 and coordinate[1] < bottom + .15 * (top - bottom):
                offset = 10
            if online_score is not None and offset > 0 and coordinate[1] > top - .15 * (top - bottom):
                offset = -12
            axis.annotate(label, coordinate, xytext=(-7 if place_left else 7, offset),
                          textcoords='offset points', ha='right' if place_left else 'left',
                          va='center', fontsize=7, color='#344555', zorder=11)
    return present


def render(reports, output, label, *, online=False, executable=False):
    matplotlib.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8.5,
                                'axes.edgecolor': '#6A7581', 'axes.labelcolor': '#182632',
                                'xtick.color': '#45535F', 'ytick.color': '#45535F', 'pdf.fonttype': 42})
    rows = len(ONLINE_METRICS) if online else len(reports)
    figure, axes = plt.subplots(rows, 2, squeeze=False, sharey='none' if online else 'row',
                               sharex='col' if online else 'none',
                               figsize=(7.3, 2.35 * rows + 1.07))
    present = set()
    if online:
        for (score, (_, y_label)), row in zip(ONLINE_METRICS.items(), axes, strict=True):
            for report, axis in zip(reports, row, strict=True):
                present.update(plot_axis(axis, report, online_score=score))
                axis.set_ylabel(y_label)
                if score == 'correct':
                    axis.set_xlabel('')
    else:
        for report, (token_axis, time_axis) in zip(reports, axes, strict=True):
            present.update(plot_axis(token_axis, report, tokens=True, executable=executable))
            present.update(plot_axis(time_axis, report, executable=executable))
            token_axis.set_ylabel('Strict & executable rate' if executable else 'Strict accuracy')
    figure.suptitle(label, x=.08, ha='left', y=.97, fontsize=12, fontweight='bold')
    native_online = {'CAR', 'BudgetVerify / TabFM', 'BudgetVerify / GBM'} if online else set()
    legend = [Line2D([], [], marker=marker, color=color, markersize=7 if marker == '*' else 5,
                     linestyle='none', label=f'{kind} (native)' if kind in native_online else kind)
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
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--input', type=Path, nargs='+')
    source.add_argument('--online-timing', type=Path, nargs=2, metavar='COLLECTION',
                        help='FinQA and TAT-QA live collection.json files with adjacent run.json')
    parser.add_argument('--output', type=Path, required=True, help='Output basename without .pdf or .png')
    parser.add_argument('--label')
    args = parser.parse_args()
    try:
        if args.online_timing:
            reports = [load_online(path) for path in args.online_timing]
            label = 'Matched online wall time'
        else:
            if len(args.input) not in (1, 2):
                parser.error('Pass one or two frontier reports')
            reports = [json.loads(path.read_text(encoding='utf-8')) for path in args.input]
            label = 'Official benchmark'
        datasets = {report.get('dataset') for report in reports}
        if not datasets <= DATASETS.keys() or len(datasets) != len(reports):
            parser.error('Reports must identify distinct FinQA or TAT-QA datasets')
        label = label if args.label is None else args.label
        render(reports, args.output, label, online=bool(args.online_timing))
        if args.input:
            executable_reports = [report for report in reports
                                  if all(report['strata'].get(scope, {}).get('n', 0) > 0
                                         for scope, _, _ in EXECUTABLE_FRONTIERS.values())]
            if executable_reports:
                output = args.output.with_name(f'{args.output.name}_executable')
                render(executable_reports, output, f'{label} (strict and executable)', executable=True)
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
