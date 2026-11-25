"""Render matched accuracy and executable-accuracy frontiers from saved reports."""

import argparse
import csv
from hashlib import sha256
import json
from math import isclose, isfinite
from pathlib import Path
import re

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
    'compact-direct': ('Compact 8B direct', 12),
    'compact-fallback': ('Compact 8B → DeepSeek → Qwen', -15),
}
STYLES = {
    'Contract cascade': ('*', '#CC4422', 105),
    'CAR': ('D', '#0072B2', 40),
    'CAR + compiler': ('v', '#296C91', 44),
    'BudgetVerify / TabFM': ('^', '#88549C', 41),
    'BudgetVerify / GBM': ('s', '#B67500', 38),
    COMPILED_BUDGETVERIFY: ('X', '#BD447F', 56),
    'Author Cascade': ('P', '#00815F', 44),
    'Compact 8B direct': ('h', '#D55E00', 48),
    'Compact 8B with fallback': ('p', '#009E73', 48),
    'Fixed / single model': ('o', '#747C87', 25),
}
ONLINE_POLICIES = {'contract', 'car', 'budgetverify', 'author-cascade', 'oda-direct',
                   'qwen-direct', 'deepseek-direct', 'qwen-first', 'ds-first'}
COMPACT_POLICIES = {'compact-direct', 'compact-fallback'}
FULL_OFFICIAL_COMPACT = {
    'finqa': (1147, 'oda-compact-balanced'),
    'tatqa': (718, 'oda-compact-execution-aligned'),
}
ADAPTER_FILES = {'adapter_config.json', 'adapter_model.safetensors'}
SHA256 = re.compile(r'[0-9a-f]{64}')
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
    if name == 'compact-direct':
        return 'Compact 8B direct'
    if name == 'compact-fallback':
        return 'Compact 8B with fallback'
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


def pareto_frontier(points, cost, score):
    return {name for name, point in points.items()
            if not any(other[cost] <= point[cost] and other[score] >= point[score]
                       and (other[cost] < point[cost] or other[score] > point[score])
                       for other in points.values())}


def load_online(path, *, fresh_comparison=False):
    """Read complete paired wall-time points and their adjacent frozen run contract."""
    collection = json.loads(path.read_text(encoding='utf-8'))
    contract = json.loads(path.with_name('run.json').read_text(encoding='utf-8'))
    dataset = contract.get('dataset')
    cases = contract.get('case_order', [])
    n = collection.get('planned_questions')
    policies = collection.get('complete_pair_policies', {})
    schema = contract.get('schema')
    full_official = schema == 'finance-live-policy-timing-v4'
    has_compact = full_official or schema == 'finance-live-policy-timing-v3'
    expected_policies = (ONLINE_POLICIES if schema == 'finance-live-policy-timing-v2' else
                         ONLINE_POLICIES | COMPACT_POLICIES if has_compact else None)
    compact = contract.get('compact_oda')
    if (expected_policies is None or contract.get('stage') != 'eval'
            or (has_compact and
                (not isinstance(compact, dict) or not isinstance(compact.get('profile'), dict)
                 or not compact['profile']))
            or dataset not in DATASETS or type(n) is not int or n < 1
            or collection.get('complete_paired_questions') != n or collection.get('stop_reason') is not None
            or set(policies) != expected_policies or len(cases) != n or len({case['id'] for case in cases}) != n
            or any(len(case['policy_order']) != len(expected_policies)
                   or set(case['policy_order']) != expected_policies for case in cases)):
        raise ValueError(f'{path}: expected a complete matched v2, v3 or v4 evaluation')
    if full_official:
        expected_n, model = FULL_OFFICIAL_COMPACT[dataset]
        offset = contract.get('case_offset')
        if contract.get('full_official_panel') is not True or type(offset) is not int or offset != 0 or n != expected_n:
            raise ValueError(f'{path}: expected the full {expected_n}-question {DATASETS[dataset]} panel at offset zero')
        validate_full_official_profile(path, compact['profile'], model)
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
        expected = pareto_frontier(points, 'mean_wall_seconds', score)
        if not isinstance(recorded, list) or len(recorded) != len(expected) or set(recorded) != expected:
            raise ValueError(f'{path}: {field} disagrees with measured wall-time points')
        strata[score] = {'n': n, field: recorded,
                         'policies': {name: {**point, 'accuracy': point[score] / n} for name, point in points.items()}}
    budgetverify = contract.get('baseline_policies', {}).get('budgetverify', {})
    if budgetverify.get('method') not in ('GBM', 'TabFM-1.0.0-PyTorch'):
        raise ValueError(f'{path}: unknown BudgetVerify model')
    report = {'dataset': dataset, 'policy_metadata': {'budgetverify': budgetverify}, 'strata': strata}
    if full_official:
        report['full_official_panel'] = True
    if fresh_comparison:
        if not full_official:
            raise ValueError(f'{path}: fresh comparison requires complete official v4 timing')
        report['fresh_token_strata'] = read_fresh_token_strata(path.with_name('outcomes.jsonl'), cases, dataset, points)
    return report


def read_fresh_token_strata(path, cases, dataset, wall_points):
    """Use one shared known-usage cohort for every policy and both scores."""
    outcomes = {name: [] for name in wall_points}
    with path.open(encoding='utf-8') as stream:
        for case, line in zip(cases, stream, strict=True):
            row = json.loads(line)
            measured = row['policies']
            if (row['dataset'] != dataset or row['id'] != case['id'] or row['policy_order'] != case['policy_order']
                    or row['complete_pair'] is not True or measured.keys() != outcomes.keys()):
                raise ValueError(f'{path}: outcome differs from planned pair {case["id"]}')
            for name, record in measured.items():
                result, seconds, cost = record['result'], record['wall_seconds'], record['cost']
                correct, executable = result['strict'], result['executable']
                tokens, unknown = cost['total_tokens'], cost['unknown_usage_calls']
                if (record['status'] != 'complete' or type(correct) is not bool or type(executable) is not bool
                        or type(seconds) not in (int, float) or not isfinite(seconds) or seconds < 0
                        or type(unknown) is not int or unknown < 0
                        or (tokens is None) != (unknown > 0)
                        or (tokens is not None and (type(tokens) is not int or tokens < 0))):
                    raise ValueError(f'{path}: invalid measurement for {case["id"]}/{name}')
                outcomes[name].append((correct, correct and executable, seconds, tokens))

    cohort = [i for i in range(len(cases)) if all(rows[i][3] is not None for rows in outcomes.values())]
    if not cohort:
        raise ValueError(f'{path}: no pairs with complete token usage across all policies')
    n = len(cohort)
    points = {}
    for name, rows in outcomes.items():
        wall = wall_points[name]
        if (sum(row[0] for row in rows) != wall['correct']
                or sum(row[1] for row in rows) != wall['strict_and_executable']
                or not isclose(sum(row[2] for row in rows), len(cases) * wall['mean_wall_seconds'])):
            raise ValueError(f'{path}: outcomes disagree with timing summary for {name}')
        points[name] = {'n': n, 'correct': sum(rows[i][0] for i in cohort),
                        'strict_and_executable': sum(rows[i][1] for i in cohort),
                        'total_tokens': sum(rows[i][3] for i in cohort)}
    return {score: {'n': n, 'token_frontier': sorted(pareto_frontier(points, 'total_tokens', score)),
                    'policies': {name: {**point, 'accuracy': point[score] / n} for name, point in points.items()}}
            for score in ONLINE_METRICS}


def write_fresh_comparison(reports, path):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        writer.writerow(('dataset', 'policy', 'paired_n', 'strict_correct', 'strict_and_executable',
                         'mean_wall_seconds', 'common_usage_n', 'common_usage_strict_correct',
                         'common_usage_strict_and_executable', 'common_usage_total_tokens',
                         'mean_tokens_per_common_usage_question', 'on_strict_wall_frontier',
                         'on_executable_wall_frontier', 'on_strict_token_frontier',
                         'on_executable_token_frontier'))
        for report in reports:
            paired, executable = (report['strata'][score] for score in ONLINE_METRICS)
            tokens, executable_tokens = (report['fresh_token_strata'][score] for score in ONLINE_METRICS)
            for name, point in sorted(paired['policies'].items()):
                token_point = tokens['policies'][name]
                writer.writerow((report['dataset'], name, point['n'], point['correct'],
                                 point['strict_and_executable'], point['mean_wall_seconds'], token_point['n'],
                                 token_point['correct'], token_point['strict_and_executable'],
                                 token_point['total_tokens'], token_point['total_tokens'] / token_point['n'],
                                 name in paired['strict_wall_frontier'],
                                 name in executable['strict_and_executable_wall_frontier'],
                                 name in tokens['token_frontier'], name in executable_tokens['token_frontier']))


def validate_full_official_profile(path, profile, model):
    files = profile.get('adapter_files')
    evaluated_profile = profile.get('evaluated_serving_profile_sha256')
    if (profile.get('model') != model or not isinstance(files, dict) or set(files) != ADAPTER_FILES
            or any(not isinstance(value, str) or not SHA256.fullmatch(value) for value in files.values())
            or not isinstance(evaluated_profile, str) or not SHA256.fullmatch(evaluated_profile)):
        raise ValueError(f'{path}: expected the verified compact profile for {model}')
    checkpoint = sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
    if profile.get('checkpoint') != checkpoint:
        raise ValueError(f'{path}: compact checkpoint differs from its adapter file digests')


def plot_axis(axis, report, *, tokens=False, online_score=None, executable=False):
    if online_score is not None and tokens:
        scope, cost_field, frontier_field = online_score, 'total_tokens', 'token_frontier'
        x_label = 'Mean measured model tokens / question'
        cohort = 'complete usage across all policies'
    elif online_score is not None:
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
    group = report['fresh_token_strata' if online_score is not None and tokens else 'strata'][scope]
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
    title = f'{DATASETS[report["dataset"]]}  ·  n={n:,}\n{cohort}'
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


def render(reports, output, label, *, online=False, executable=False, online_tokens=False):
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
                present.update(plot_axis(axis, report, online_score=score, tokens=online_tokens))
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
    parser.add_argument('--fresh-comparison', action='store_true',
                        help='Also export a complete v4 token frontier and joined TSV from adjacent outcomes.jsonl')
    parser.add_argument('--label')
    args = parser.parse_args()
    if args.fresh_comparison and not args.online_timing:
        parser.error('--fresh-comparison requires --online-timing')
    try:
        if args.online_timing:
            reports = [load_online(path, fresh_comparison=args.fresh_comparison) for path in args.online_timing]
            full_official = sum(report.get('full_official_panel', False) for report in reports)
            if 0 < full_official < len(reports):
                parser.error('Full official online timing requires both datasets to be complete v4 runs')
            label = 'Full official online wall time' if full_official else 'Matched online wall time'
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
        if args.fresh_comparison:
            token_output = args.output.with_name(f'{args.output.name}_tokens')
            render(reports, token_output, 'Full official online token use', online=True, online_tokens=True)
            write_fresh_comparison(reports, args.output.with_name(f'{args.output.name}_comparison.tsv'))
        if args.input:
            executable_reports = [report for report in reports
                                  if all(report['strata'].get(scope, {}).get('n', 0) > 0
                                         for scope, _, _ in EXECUTABLE_FRONTIERS.values())]
            if executable_reports:
                output = args.output.with_name(f'{args.output.name}_executable')
                render(executable_reports, output, f'{label} (strict and executable)', executable=True)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
