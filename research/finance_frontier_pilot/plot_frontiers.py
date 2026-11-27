"""Render matched accuracy and executable-accuracy frontiers from saved reports."""

import argparse
from collections import Counter
import csv
from hashlib import file_digest, sha256
import json
from math import isclose, isfinite
from pathlib import Path
import re
from statistics import fmean, median, quantiles

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
STRATIFIED_LATENCY_SCHEMA = 'finance-live-policy-timing-stratified-v1'
STRATIFIED_LATENCY_N = 24
LATENCY_REFERENCES = (('compact-fallback', 'compact_paired_online_wall'), ('contract', 'paired_online_wall'))
WALL_DELTA = 'mean_online_wall_seconds_delta'
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
JOINT_COLORS = {'fresh': '#087F73', 'historical': '#686B93', 'local': '#B64D24'}
JOINT_ARCHIVED_TABFM = {'finqa': '0.8', 'tatqa': '0'}
JOINT_ARCHIVED_GBM = {'finqa': '0.8', 'tatqa': '0.65'}
JOINT_TIMED_ARMS = {'contract': 'Earlier contract cascade', 'car': 'CAR', 'budgetverify': 'BudgetVerify / TabFM',
                    'author-cascade': 'Cascade Routing', 'ds-first': 'DeepSeek → Qwen',
                    'qwen-first': 'Qwen → DeepSeek'}
JOINT_PARETO_LABELS = {
    'joint-compact': 'Compact → DeepSeek', 'deepseek-direct': 'DeepSeek direct',
    'car-compiled': 'CAR + compiler', 'budgetverify-gbm-compiled': 'BudgetVerify GBM + compiler',
    'budgetverify-tabfm-compiled': 'BudgetVerify TabFM + compiler', 'author-cascade': 'Cascade Routing',
    'qwen-first': 'Qwen → DeepSeek', 'ds-first': 'DeepSeek → Qwen',
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


def three_axis_frontier(points):
    """Maximize executable correctness, and minimize matched tokens and wall time."""
    vectors = {name: (point['common_strict_executable'], -point['common_request_tokens'],
                      -point['common_mean_wall_seconds']) for name, point in points.items()}
    return {name for name, value in vectors.items()
            if not any(other != value and all(a >= b for a, b in zip(other, value, strict=True))
                       for other in vectors.values())}


def digest(path):
    with path.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


def joint_official(path, measurements, n, rate):
    report = json.loads(path.read_text(encoding='utf-8'))
    metadata = json.loads((measurements / 'run.json').read_text(encoding='utf-8'))
    usage = json.loads((measurements / 'summary.json').read_text(encoding='utf-8'))
    if (metadata['panel_sha256'] != report['panel_sha256']
            or digest(measurements / 'cases.jsonl') != report['local_receipts_sha256']):
        raise ValueError('Official joint figures require matching compact receipt bytes and panel')
    official, prefill = {}, {}
    for dataset, (expected_n, _) in FULL_OFFICIAL_COMPACT.items():
        points, inputs = [], report['original_baselines'][dataset]['benchmark_aggregates']
        baselines = {
            'car': 'CAR', 'car_compiled': 'CAR + compiler',
            f'budgetverify_compiled/tabfm/lambda_{JOINT_ARCHIVED_TABFM[dataset]}': 'TabFM + compiler',
            f'budgetverify_compiled/gbm/lambda_{JOINT_ARCHIVED_GBM[dataset]}': 'GBM + compiler',
            'cascade/compiled/cascade_routing_1.5': 'Cascade Routing + compiler',
            'cascade/compiled/always_deepseek': 'DeepSeek direct',
            'cascade/compiled/nonexecution_deepseek_qwen': 'DeepSeek → Qwen',
            'cascade/compiled/nonexecution_qwen_deepseek': 'Qwen → DeepSeek',
        }

        def point(label, source, row, *, old=False):
            correct = row['strict_and_executable'] if old else row['correct']
            known = row['known_tokens'] if old else row['local_logical_api_tokens_known'] + row['teacher_provider_tokens_known']
            unknown = row['unknown_usage_calls'] if old else row['local_logical_api_usage_unknown_n'] + row['teacher_provider_usage_unknown_n']
            if (row['n'] != expected_n or type(correct) is not int or not 0 <= correct <= expected_n
                    or type(known) is not int or known <= 0 or type(unknown) is not int or unknown < 0):
                raise ValueError(f'{dataset}/{label}: missing or unmatched official accuracy or usage')
            paired = row.get('paired_against_compact', {})
            return {'policy': label, 'collection': source, 'n': expected_n, 'correct': correct,
                    'tokens_known': known, 'unknown_usage_calls': unknown,
                    'teacher_calls': row.get('teacher_calls'), 'recovered': row.get('recovered'),
                    'harmed': row.get('harmed'), 'paired_delta_95_pp': paired.get('paired_cluster_percentile_95_pp')}

        for key, label in baselines.items():
            points.append(point(label, 'historical baselines', inputs[key], old=True))
        for width in dict.fromkeys((1, n)):
            tag = f'{dataset}/n{width}'
            local = report['evaluation'][tag]['compact_only']
            item = usage[tag]
            if item['known_engine_work'] == expected_n:
                physical, source = item['engine_prefill_tokens'], 'isolated per-question engine counters'
            else:
                engine = item.get('engine_work') or {}
                if (not engine.get('idle_before_after') or not engine.get('completion_tokens_reconcile')
                        or engine['counter_deltas']['generated_tokens'] != item['api_tokens']['completion_tokens']):
                    raise ValueError(f'{tag}: missing isolated aggregate engine attribution')
                physical, source = engine['locally_computed_prefill_tokens'], 'isolated batch engine counters'
            if (item['questions'] != expected_n or item['known_api_usage'] != expected_n
                    or item['strict_executable'] != local['correct'] or type(physical) is not int or physical <= 0):
                raise ValueError(f'{tag}: incomplete or unmatched physical prefill measurement')
            points.append(point(f'Compact n={width}', 'current local measurements', local))
            prefill.setdefault(dataset, []).append({'policy': f'n={width}', 'n': expected_n, 'collection': source,
                'logical_prompt_tokens': item['api_tokens']['prompt_tokens'],
                'physical_prefill_tokens': physical,
                'generated_tokens': item['api_tokens']['completion_tokens']})
        selected = report['evaluation'][f'{dataset}/n{n}']['budget_points'][f'{rate:g}']
        points.append(point('Compact → DeepSeek (replay)', 'historical teacher replay', selected))
        if 'fresh_selected_teacher' in selected:
            points.append(point('Compact → DeepSeek', 'fresh selected teacher', selected['fresh_selected_teacher']))
        official[dataset] = points
    return report, official, prefill


def timed_items(path, dataset, ids, arms):
    rows = {}
    with path.with_name('outcomes.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            item = json.loads(line)
            if item['dataset'] != dataset or not item['complete_pair']:
                continue
            key = item['id']
            if key in rows or key not in ids or any(name not in item['policies'] for name in arms):
                raise ValueError(f'{path}: unexpected timed row or missing policy')
            rows[key] = {}
            for name in arms:
                case = item['policies'][name]
                seconds = case['wall_seconds']
                if case['status'] != 'complete' or not isfinite(seconds) or seconds < 0:
                    raise ValueError(f'{path}: invalid completed wall measurement')
                rows[key][name] = (seconds, bool(case['result']['strict'] and case['result']['executable']))
    return rows


def joint_timing(live_files, archived_files, report, n, rate):
    archived = {}
    for path in archived_files:
        old = load_online(path)
        dataset = old['dataset']
        if dataset in archived or 'stratified_latency' not in old:
            raise ValueError('Expected one original stratified timing collection per dataset')
        run_path = path.with_name('run.json')
        run = json.loads(run_path.read_text(encoding='utf-8'))
        if run['panel'] != report['panel_sha256']:
            raise ValueError(f'{path}: timing sample is from another official panel')
        ids = [row['id'] for row in run['case_order']]
        rows = timed_items(path, dataset, set(ids), JOINT_TIMED_ARMS)
        if rows.keys() != set(ids):
            raise ValueError(f'{path}: incomplete original timing membership')
        archived[dataset] = ids, rows, digest(run_path)
    if set(archived) != set(DATASETS):
        raise ValueError('Old matched timing inputs must include both FinQA and TAT-QA')

    fresh, live_labels = {}, {'compact-teacher': 'Compact → DeepSeek', 'deepseek-direct': 'DeepSeek direct'}
    for path in live_files:
        run = json.loads(path.with_name('run.json').read_text(encoding='utf-8'))
        collection = json.loads(path.read_text(encoding='utf-8'))
        if (run['schema'] != 'finance-compact-deepseek-live-v1' or run['panel_sha256'] != report['panel_sha256']
                or run['gate_sha256'] != report['policy_sha256'] or run['n'] != n or run['gate_rate'] != rate):
            raise ValueError(f'{path}: fresh timing runs must use the matching frozen policy and panel')
        for dataset in collection['metrics']:
            ids, _, old_digest = archived[dataset]
            if (run['historical_timing_membership_sha256'][dataset] != old_digest
                    or [row['id'] for row in run['case_order'] if row['dataset'] == dataset] != ids):
                raise ValueError(f'{path}: old and fresh {dataset} timing samples differ')
            rows = timed_items(path, dataset, set(ids), live_labels)
            if any(item['n'] != len(rows) for name, item in collection['metrics'][dataset].items() if name in live_labels):
                raise ValueError(f'{path}: fresh timing counts differ from completed pairs')
            if dataset not in fresh or len(rows) > len(fresh[dataset][0]):
                fresh[dataset] = rows, path.parent.parent.name

    results = {}
    for dataset, (rows, source) in fresh.items():
        if not rows:
            continue
        old_rows = archived[dataset][1]
        points = []
        for labels, lookup, collection in ((live_labels, rows, f'fresh ({source})'),
                                            (JOINT_TIMED_ARMS, old_rows, 'historical same IDs')):
            for key, label in labels.items():
                times, scored = zip(*(lookup[ident][key] for ident in rows), strict=True)
                points.append({'policy': label, 'collection': collection, 'n': len(times), 'correct': sum(scored),
                               'mean_wall_seconds': fmean(times), 'median_wall_seconds': median(times),
                               'p90_wall_seconds': quantiles(times, n=10, method='inclusive')[-1]
                               if len(times) > 1 else times[0]})
        results[dataset] = points
    return results


def save_joint(fig, output, suffix):
    output.parent.mkdir(parents=True, exist_ok=True)
    for extension in ('pdf', 'png'):
        fig.savefig(output.with_name(f'{output.name}_{suffix}.{extension}'), dpi=400, facecolor='white')
    plt.close(fig)


def joint_axes(title, height=3.2):
    matplotlib.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8, 'pdf.fonttype': 42})
    fig, axes = plt.subplots(1, 2, figsize=(7.3, height), layout='constrained')
    fig.suptitle(title, x=.035, ha='left', fontsize=12, fontweight='bold')
    for dataset, axis in zip(DATASETS, axes, strict=True):
        axis.set_title(DATASETS[dataset], loc='left', fontweight='bold')
        axis.spines[['top', 'right']].set_visible(False)
        axis.set_axisbelow(True)
        axis.grid(alpha=.24)
    return fig, axes


def render_joint(official, prefill, timing, output):
    fig, axes = joint_axes('Official accuracy and logical token use', height=4)
    markers = ('D', 'v', '^', 'X', 'P', 's', '<', '>', 'h', 'o', 'x', '*')
    legend = {}
    for dataset, axis in zip(DATASETS, axes, strict=True):
        rows = official[dataset]
        axis.set_title(f'{DATASETS[dataset]}  ·  {rows[0]["n"]:,} questions', loc='left', fontweight='bold')
        exact = {row['policy']: row for row in rows if row['unknown_usage_calls'] == 0}
        frontier = pareto_frontier(exact, 'tokens_known', 'correct')
        coordinates = sorted({(exact[name]['tokens_known'] / exact[name]['n'], exact[name]['correct'] / exact[name]['n'])
                              for name in frontier})
        if coordinates:
            x, y = zip(*coordinates)
            artist, = axis.plot(x, y, color='#253849', linestyle='--', linewidth=1, marker='o',
                                markerfacecolor='none', markersize=9, zorder=2)
            legend['Pareto frontier (complete usage)'] = artist
        for index, row in enumerate(rows):
            marker = markers[index]
            source = row['collection']
            color = JOINT_COLORS['local' if source.startswith('current') else
                                 'fresh' if source.startswith('fresh') else 'historical']
            x, y = row['tokens_known'] / row['n'], row['correct'] / row['n']
            artist, = axis.plot(x, y, marker=marker, color=color, markersize=6.5, linestyle='none', zorder=3)
            if row['unknown_usage_calls']:
                axis.annotate('', xytext=(x, y), xy=(x * 1.065, y), zorder=2,
                              arrowprops={'arrowstyle': '->', 'color': color, 'lw': .8})
            legend[row['policy']] = artist
        axis.set_xlabel('Known logical tokens / question')
        axis.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        axis.margins(x=.16, y=.13)
    axes[0].set_ylabel('Strict & executable rate')
    fig.legend(legend.values(), legend.keys(), loc='lower center', ncol=3, bbox_to_anchor=(.52, .04), frameon=False)
    fig.text(.52, .006, 'Arrows mark lower bounds where token usage is missing.', ha='center', fontsize=7)
    fig.get_layout_engine().set(rect=(0, .23, 1, .77))
    save_joint(fig, output, 'official')

    fig, axes = joint_axes('Local model prefill on the official panels')
    for dataset, axis in zip(DATASETS, axes, strict=True):
        rows = prefill[dataset]
        x = range(len(rows))
        for orientation, field, color, label in ((-1, 'logical_prompt_tokens', '#A3ABB6', 'API prompt'),
                (1, 'physical_prefill_tokens', JOINT_COLORS['fresh'], 'Computed prefill')):
            axis.bar([i + orientation * .16 for i in x], [row[field] / row['n'] for row in rows],
                     width=.28, color=color, label=label, zorder=3)
        for i, row in enumerate(rows):
            share = row['physical_prefill_tokens'] / row['logical_prompt_tokens'] - 1
            axis.annotate(f'{share:+.1%}', (i + .16, row['physical_prefill_tokens'] / row['n']),
                          xytext=(0, 4), textcoords='offset points', ha='center', fontsize=8)
        axis.set_xticks(x, [row['policy'] for row in rows])
        axis.set_ylabel('Tokens / question')
        axis.margins(y=.15)
    items, labels = axes[0].get_legend_handles_labels()
    fig.legend(items, labels, loc='lower center', ncol=2, frameon=False)
    fig.get_layout_engine().set(rect=(0, .075, 1, .925))
    save_joint(fig, output, 'prefill')

    if timing:
        fig, axes = joint_axes('End-to-end timing on shared question IDs', height=3.25)
        observed = [row for rows in timing.values() for row in rows]
        positive = all(row['median_wall_seconds'] > 0 for row in observed)
        lower = min(row['median_wall_seconds'] for row in observed) * .7 if positive else 0
        upper = max(row['p90_wall_seconds'] for row in observed) * 1.3
        for dataset, axis in zip(DATASETS, axes, strict=True):
            rows = timing.get(dataset, [])
            if not rows:
                axis.set_title(f'{DATASETS[dataset]}  ·  no completed timing pairs', loc='left')
                axis.set_axis_off()
                continue
            axis.set_title(f'{DATASETS[dataset]}  ·  {rows[0]["n"]}/{STRATIFIED_LATENCY_N} timing pairs', loc='left')
            for y, row in enumerate(rows):
                color = JOINT_COLORS['historical' if row['collection'].startswith('historical') else 'fresh']
                low, high = row['median_wall_seconds'], row['p90_wall_seconds']
                axis.plot([low, high], [y, y], color=color, lw=1.1)
                axis.scatter(low, y, color=color, s=19, zorder=3)
                axis.scatter(high, y, facecolors='white', edgecolors=color, s=19, zorder=3)
            labels = [f'{row["policy"]}'+(' (archive)' if row['collection'].startswith('historical') else '')
                      for row in rows]
            axis.set_yticks(range(len(rows)), labels)
            if dataset == 'tatqa' and 'finqa' in timing:
                axis.tick_params(axis='y', labelleft=False)
            axis.invert_yaxis()
            if positive:
                axis.set_xscale('log')
            axis.set_xlim(lower, upper or 1)
            axis.set_xlabel('Wall time (s, log scale)' if positive else 'Wall time (s)')
        timing_legend = [Line2D([], [], marker='o', color='#45535F', markerfacecolor=facecolor,
                                linestyle='none', markersize=4, label=label)
                         for label, facecolor in (('Median', '#45535F'), ('p90', 'white'))]
        fig.legend(handles=timing_legend, loc='lower center', ncol=2, frameon=False)
        fig.get_layout_engine().set(rect=(0, .075, 1, .925))
        save_joint(fig, output, 'timing')


def write_joint(official, prefill, timing, output):
    header = ('dataset', 'scope', 'policy', 'collection', 'n', 'correct', 'tokens_known', 'unknown_usage_calls',
              'teacher_calls', 'recovered', 'harmed', 'paired_delta_95_pp', 'logical_prompt_tokens',
              'physical_prefill_tokens', 'generated_tokens', 'mean_wall_seconds', 'median_wall_seconds',
              'p90_wall_seconds')
    with output.with_name(f'{output.name}_joint.tsv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=header, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        for scope, group in (('full official accuracy and cost', official), ('full official local prefill', prefill),
                             ('matched timing sample', timing)):
            for dataset, rows in group.items():
                writer.writerows({'dataset': dataset, 'scope': scope, **row} for row in rows)


def joint_pareto_case(record):
    from benchmark_actions import action_cost

    result, wall, calls = record['result'], record['wall_seconds'], record['calls']
    if (record['status'] != 'complete' or type(result['strict']) is not bool
            or type(result['executable']) is not bool or type(wall) not in (int, float)
            or not isfinite(wall) or wall < 0 or not calls):
        raise ValueError('Invalid completed route in joint timing receipts')
    for call in calls.values():
        usage, seconds = call['usage'], call['elapsed_seconds']
        if (type(seconds) not in (int, float) or not isfinite(seconds) or seconds < 0
                or (usage is not None and (type(usage['total']) is not int or usage['total'] < 0))):
            raise ValueError('Invalid measured model call in joint timing receipts')
    cost = action_cost(list(calls.values()))
    recorded_cost = record['cost'].copy()
    recorded_seconds = recorded_cost.get('summed_call_seconds')
    # Different Python versions can round the sum of the same call durations differently.
    if (type(recorded_seconds) not in (int, float)
            or not isclose(recorded_seconds, cost['summed_call_seconds'], rel_tol=0, abs_tol=1e-12)):
        raise ValueError('Recorded route cost differs from its bound call receipts')
    recorded_cost['summed_call_seconds'] = cost['summed_call_seconds']
    if cost != recorded_cost:
        raise ValueError('Recorded route cost differs from its bound call receipts')
    return result['strict'], result['strict'] and result['executable'], wall, cost


def load_joint_pareto(namespace, *, allow_partial=False):
    """Load the immutable full-panel plan and the accepted fresh timing prefix."""
    from cohorts import UPSTREAM, read_source
    from live_policy_timing import (ISOLATED_ACTOR_STORE, JOINT_POLICIES, JOINT_STEADY_PLAN,
                                    JOINT_WAVE_PLAN, OFFICIAL_COUNTS, joint_history)

    plan_path = namespace / 'joint_plan.json'
    plan = json.loads(plan_path.read_bytes())
    plan_sha = digest(plan_path)
    dataset, order = plan['dataset'], plan['case_order']
    expected, width = OFFICIAL_COUNTS[dataset], plan.get('joint_workers', 1)
    serial = plan['schema'] == 'finance-live-joint-timing-plan-v1' and type(width) is int and width == 1
    waves = plan['schema'] == JOINT_WAVE_PLAN and type(width) is int and 2 <= width <= 4
    steady_block = plan.get('joint_steady_block')
    steady = (plan['schema'] == JOINT_STEADY_PLAN and type(width) is int and width == 4
              and type(steady_block) is int and steady_block == 32
              and plan.get('actor_store_scope') == ISOLATED_ACTOR_STORE)
    official = plan['official_source']
    if (not (serial or waves or steady) or len(order) != expected or len({case['id'] for case in order}) != expected
            or ('joint_steady_block' in plan and not steady)
            or tuple(plan['policies']) != JOINT_POLICIES
            or any(len(case['policy_order']) != len(JOINT_POLICIES) or set(case['policy_order']) != set(JOINT_POLICIES)
                   for case in order)
            or (official['split'], official['sha256'], official['source_questions'])
            != (UPSTREAM[dataset][0], UPSTREAM[dataset][2], expected)
            or any(not isinstance(plan['panel'].get(name), str) or not SHA256.fullmatch(plan['panel'][name])
                   for name in ('public.jsonl', 'references.jsonl'))):
        raise ValueError(f'{namespace}: does not describe the exact eight-policy official panel')
    source_path = Path(official['path'])
    if source_path.is_file():
        source, identity = read_source(dataset, source_path)
        expected_rows = {(row['id'], row['report']) for row, _, _ in source}
        if identity != official or expected_rows != {(case['id'], case['report']) for case in order}:
            raise ValueError(f'{namespace}: timing plan does not match its official source records')
    rows, attempts = joint_history(namespace / 'shards', plan, plan_sha)
    n = len(rows)
    if not n or (n != expected and not allow_partial):
        raise ValueError(f'{namespace}: {n}/{expected} complete pairs; full export requires all official questions')
    points = {name: [joint_pareto_case(row['policies'][name]) for row in rows] for name in JOINT_POLICIES}
    common = [index for index in range(n) if all(arm[index][3]['total_tokens'] is not None for arm in points.values())]
    sizes = Counter(row.get('block_size', 1) for row in rows)
    dataset_scope = 'full_official' if n == expected else 'partial_frozen_prefix'
    block_size = steady_block if steady else width
    schedule = 'rolling' if steady else 'wave' if waves else 'serial'
    policies = {}
    for name, arm in points.items():
        matched = [arm[index] for index in common]
        known = sum(item[3]['known_tokens'] for item in arm)
        unknown_calls = sum(item[3]['unknown_usage_calls'] for item in arm)
        policies[name] = {
            'dataset': dataset, 'scope': dataset_scope, 'policy': name, 'policy_label': JOINT_PARETO_LABELS[name],
            'joint_workers': width, 'official_n': expected, 'timed_n': n, 'common_cost_complete_n': len(common),
            'scheduling': schedule, 'frozen_block_size': block_size, 'actor_store_scope': plan.get('actor_store_scope'),
            'local_selection': plan.get('local_selection', 'native-vote-v1'),
            'timing_attempts': attempts, 'joint_plan_sha256': plan_sha,
            'timed_questions_by_block_size': ';'.join(f'{size}:{sizes[size]}' for size in sorted(sizes)),
            'timed_strict_correct': sum(item[0] for item in arm),
            'timed_strict_executable': sum(item[1] for item in arm),
            'timed_strict_executable_accuracy': sum(item[1] for item in arm) / n,
            'timed_mean_wall_seconds': fmean(item[2] for item in arm),
            'timed_known_request_tokens': known, 'timed_total_request_tokens': None if unknown_calls else known,
            'timed_unknown_usage_questions': sum(item[3]['unknown_usage_calls'] > 0 for item in arm),
            'timed_unknown_usage_calls': unknown_calls,
            'common_strict_correct': sum(item[0] for item in matched),
            'common_strict_executable': sum(item[1] for item in matched),
            'common_strict_executable_accuracy': sum(item[1] for item in matched) / len(matched) if matched else None,
            'common_request_tokens': sum(item[3]['total_tokens'] for item in matched) if matched else None,
            'common_mean_wall_seconds': fmean(item[2] for item in matched) if matched else None,
        }
    frontier = three_axis_frontier(policies) if common else set()
    for name, point in policies.items():
        point['on_three_axis_frontier'] = name in frontier if common else None
    return list(policies.values())


def render_joint_pareto(charts, output, label=None):
    matplotlib.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8, 'pdf.fonttype': 42})
    figure, axes = plt.subplots(len(charts), 2, figsize=(7.6, 2.45 * len(charts) + .85),
                                squeeze=False, layout='constrained')
    markers = ('*', 'o', 'D', 's', '^', 'P', 'v', 'X')
    colors = ('#B64D24', '#0072B2', '#686B93', '#946900', '#AC4F85', '#00815F', '#6D7890', '#564956')
    for rows, (token_axis, wall_axis) in zip(charts, axes, strict=True):
        coverage = rows[0]
        common = coverage['common_cost_complete_n']
        name = DATASETS[coverage['dataset']]
        token_axis.set_title(f'{name} · {coverage["timed_n"]:,}/{coverage["official_n"]:,} timed', loc='left',
                             fontweight='bold')
        load = f'{coverage["scheduling"]} K{coverage["joint_workers"]}/{coverage["frozen_block_size"]}'
        wall_axis.set_title(f'{common:,} with complete usage · {load}', loc='left')
        for axis, field, xlabel, divisor in (
            (token_axis, 'common_request_tokens', 'Measured request tokens / question', common or 1),
            (wall_axis, 'common_mean_wall_seconds', 'End-to-end wall time / question (s)', 1),
        ):
            axis.spines[['top', 'right']].set_visible(False)
            axis.set_axisbelow(True)
            axis.grid(alpha=.24)
            axis.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
            axis.set_xlabel(xlabel)
            if not common:
                axis.text(.5, .5, 'No common complete-usage questions', transform=axis.transAxes, ha='center')
                axis.set_xticks([])
                axis.set_yticks([])
                continue
            for row, marker, color in zip(rows, markers, colors, strict=True):
                x, y = row[field] / divisor, row['common_strict_executable_accuracy']
                if row['on_three_axis_frontier']:
                    axis.scatter(x, y, marker='o', s=93, facecolor='none', edgecolor='#253849', linewidth=.8, zorder=2)
                axis.scatter(x, y, marker=marker, color=color, s=55 if marker == '*' else 33, zorder=3)
            axis.margins(x=.12, y=.14)
            ymin, ymax = axis.get_ylim()
            axis.set_ylim(max(-.04, ymin), min(1.04, ymax))
        token_axis.set_ylabel('Strict & executable accuracy')
    partial = any(rows[0]['scope'] == 'partial_frozen_prefix' for rows in charts)
    title = label or 'Accuracy, measured tokens, and end-to-end wall time'
    figure.suptitle(f'{title} · partial prefix' if partial else title, x=.025, ha='left', fontweight='bold', fontsize=12)
    legend = [Line2D([], [], marker=marker, color=color, markersize=6, linestyle='none', label=row['policy_label'])
              for row, marker, color in zip(charts[0], markers, colors, strict=True)]
    legend.append(Line2D([], [], marker='o', markerfacecolor='none', color='#253849', linestyle='none',
                         markersize=8, label='Three-axis Pareto frontier'))
    figure.legend(handles=legend, loc='lower center', bbox_to_anchor=(.5, .012), ncol=3, frameon=False, fontsize=7)
    figure.get_layout_engine().set(rect=(0, .19 if len(charts) == 1 else .12, 1, .81 if len(charts) == 1 else .88))
    save_joint(figure, output, 'pareto')


def write_joint_pareto(charts, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_name(f'{output.name}_pareto.tsv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(charts[0][0]), delimiter='\t', lineterminator='\n')
        writer.writeheader()
        for rows in charts:
            writer.writerows(rows)


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
    stratified = schema == STRATIFIED_LATENCY_SCHEMA
    has_compact = full_official or stratified or schema == 'finance-live-policy-timing-v3'
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
        raise ValueError(f'{path}: expected a complete matched online evaluation')
    if full_official or stratified:
        expected_n, model = FULL_OFFICIAL_COMPACT[dataset]
        offset = contract.get('case_offset')
        if type(offset) is not int or offset != 0 or contract.get('full_official_panel') is not full_official:
            raise ValueError(f'{path}: online panel scope and offset disagree with the run schema')
        if full_official and n != expected_n:
            raise ValueError(f'{path}: expected the full {expected_n}-question {DATASETS[dataset]} panel')
        validate_full_official_profile(path, compact['profile'], model)
        if stratified:
            validate_stratified_sample(path, contract, cases, n, expected_n)
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
    if stratified:
        report['stratified_latency'] = load_stratified_latency(path, collection, points, n)
    if fresh_comparison:
        if not full_official:
            raise ValueError(f'{path}: fresh comparison requires complete official v4 timing')
        report['fresh_token_strata'] = read_fresh_token_strata(path.with_name('outcomes.jsonl'), cases, dataset, points)
    return report


def validate_stratified_sample(path, contract, cases, n, population_n):
    source = contract['official_source']
    sample = contract['stratified_sampling']
    assignments = sample['stratum_by_id']
    counts = Counter(assignments.values())
    strata = sample['strata']
    if (n != STRATIFIED_LATENCY_N or sample['sample_n'] != n or sample['population_n'] != population_n
            or source['source_questions'] != population_n or set(assignments) != {case['id'] for case in cases}
            or counts.keys() != strata.keys() or sum(cell['population_n'] for cell in strata.values()) != population_n
            or any(not 1 <= counts[name] == cell['sample_n'] <= cell['population_n']
                   for name, cell in strata.items())):
        raise ValueError(f'{path}: stratified sampling counts disagree with the official panel or timed questions')


def load_stratified_latency(path, collection, points, n):
    timings = {}
    for name, point in collection['complete_pair_policies'].items():
        median, p90 = (point[field] for field in ('median_wall_seconds', 'p90_wall_seconds'))
        if not all(type(value) in (int, float) and isfinite(value) for value in (median, p90)) or not 0 <= median <= p90:
            raise ValueError(f'{path}: invalid wall-time percentiles for {name}')
        timings[name] = {'median_wall_seconds': median, 'p90_wall_seconds': p90}
    for reference, field in LATENCY_REFERENCES:
        paired = collection[field]
        comparisons = paired['comparisons']
        if paired['proposed'] != reference or comparisons.keys() != points.keys() - {reference}:
            raise ValueError(f'{path}: paired wall-time coverage disagrees with {reference}')
        for name, scores in comparisons.items():
            result = scores['strict']
            delta = result[WALL_DELTA]
            clusters = result['report_clusters']
            interval = result['interval_95']
            if (result['n'] != n or result['excluded_n'] != 0 or type(clusters) is not int or not 1 <= clusters <= n
                    or not isclose(delta, points[reference]['mean_wall_seconds'] - points[name]['mean_wall_seconds'],
                                   abs_tol=1e-9)
                    or (interval is None) != (clusters < 2)):
                raise ValueError(f'{path}: invalid paired wall-time estimate for {reference}/{name}')
            bounds = (None, None) if interval is None else interval[WALL_DELTA]
            if interval is not None and (len(bounds) != 2 or not all(isfinite(x) for x in bounds)
                                         or bounds[0] > bounds[1]):
                raise ValueError(f'{path}: invalid paired wall-time interval for {reference}/{name}')
            timings[name][reference] = (clusters, delta, *bounds)
    return timings


def write_stratified_latency(reports, path):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        columns = ('report_clusters', 'mean_delta_seconds', 'interval_95_low_seconds', 'interval_95_high_seconds')
        writer.writerow(('dataset', 'scope', 'policy', 'paired_n', 'strict_correct', 'strict_and_executable',
                         'mean_wall_seconds', 'median_wall_seconds', 'p90_wall_seconds',
                         *(f'{reference.replace("-", "_")}_minus_policy_{col}'
                           for reference, _ in LATENCY_REFERENCES for col in columns)))
        for report in reports:
            points = report['strata']['correct']['policies']
            for name, point in sorted(points.items()):
                timing = report['stratified_latency'][name]
                writer.writerow((report['dataset'], 'unweighted_stratified_sample', name, point['n'],
                                 point['correct'], point['strict_and_executable'], point['mean_wall_seconds'],
                                 timing['median_wall_seconds'], timing['p90_wall_seconds'],
                                 *(value for reference, _ in LATENCY_REFERENCES
                                   for value in timing.get(reference, (None, None, None, None)))))


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
    stratified = 'stratified_latency' in report
    if stratified:
        cohort = f'Stratified sample · {cohort}'
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
        if stratified and name in COMPACT_POLICIES:
            continue
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
    source.add_argument('--joint-report', type=Path, help='Shared compact-gate replay report')
    source.add_argument('--joint-pareto', type=Path, nargs='+', metavar='NAMESPACE',
                        help='One or two live eight-policy joint timing namespaces with plan and shards')
    parser.add_argument('--allow-partial', action='store_true', help='Label and export a nonempty frozen timing prefix')
    parser.add_argument('--joint-measurements', type=Path, help='Matched official compact measurements directory')
    parser.add_argument('--joint-live', type=Path, nargs='+', metavar='COLLECTION')
    parser.add_argument('--joint-historical-timing', type=Path, nargs=2, metavar='COLLECTION')
    parser.add_argument('--joint-n', type=int, choices=(1, 4, 8), default=4)
    parser.add_argument('--joint-rate', type=float, default=.2)
    parser.add_argument('--output', type=Path, required=True, help='Output basename without .pdf or .png')
    parser.add_argument('--fresh-comparison', action='store_true',
                        help='Also export a complete v4 token frontier and joined TSV from adjacent outcomes.jsonl')
    parser.add_argument('--label')
    args = parser.parse_args()
    if args.fresh_comparison and not args.online_timing:
        parser.error('--fresh-comparison requires --online-timing')
    if args.allow_partial and not args.joint_pareto:
        parser.error('--allow-partial requires --joint-pareto')
    try:
        if args.joint_pareto:
            charts = [load_joint_pareto(path, allow_partial=args.allow_partial) for path in args.joint_pareto]
            if len({rows[0]['dataset'] for rows in charts}) != len(charts):
                parser.error('Pass distinct FinQA or TAT-QA timing namespaces')
            protocol = ('scheduling', 'joint_workers', 'frozen_block_size', 'actor_store_scope', 'local_selection')
            if len({tuple(rows[0][field] for field in protocol) for rows in charts}) != 1:
                parser.error('Pass timing namespaces measured under one load protocol')
            charts.sort(key=lambda rows: rows[0]['dataset'])
            render_joint_pareto(charts, args.output, args.label)
            write_joint_pareto(charts, args.output)
            return
        if args.joint_report:
            if not args.joint_measurements or bool(args.joint_live) != bool(args.joint_historical_timing):
                parser.error('Joint mode needs matched compact measurements plus both timing inputs if timing is requested')
            report, official, prefill = joint_official(args.joint_report, args.joint_measurements,
                                                        args.joint_n, args.joint_rate)
            timing = (joint_timing(args.joint_live, args.joint_historical_timing, report, args.joint_n, args.joint_rate)
                      if args.joint_live else {})
            render_joint(official, prefill, timing, args.output)
            write_joint(official, prefill, timing, args.output)
            return
        if args.online_timing:
            reports = [load_online(path, fresh_comparison=args.fresh_comparison) for path in args.online_timing]
            full_official = sum(report.get('full_official_panel', False) for report in reports)
            stratified = sum('stratified_latency' in report for report in reports)
            if 0 < full_official < len(reports):
                parser.error('Full official online timing requires both datasets to be complete v4 runs')
            if 0 < stratified < len(reports):
                parser.error('Stratified online timing requires both datasets to use the stratified sample')
            label = ('Stratified sample online wall time' if stratified else
                     'Full official online wall time' if full_official else 'Matched online wall time')
        else:
            stratified = 0
            if len(args.input) not in (1, 2):
                parser.error('Pass one or two frontier reports')
            reports = [json.loads(path.read_text(encoding='utf-8')) for path in args.input]
            label = 'Official benchmark'
        datasets = {report.get('dataset') for report in reports}
        if not datasets <= DATASETS.keys() or len(datasets) != len(reports):
            parser.error('Reports must identify distinct FinQA or TAT-QA datasets')
        label = label if args.label is None else args.label
        render(reports, args.output, label, online=bool(args.online_timing))
        if stratified:
            write_stratified_latency(reports, args.output.with_name(f'{args.output.name}_latency.tsv'))
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
