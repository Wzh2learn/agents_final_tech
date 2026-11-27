"""Freeze a pooled TRAIN gate and replay compact-to-DeepSeek on matched receipts."""

import argparse
from collections import Counter
import json
from math import floor, fsum, isfinite
from pathlib import Path
from statistics import median
from typing import NamedTuple

from benchmark_actions import digest_file, freeze, read_panel
from benchmark_panels import TRAIN, identity_keys
from diagnose import paired_effect
from run_pilot import rank_auc


SCHEMA = 'finance-compact-teacher-gate-v1'
SELECTED_SCHEMA = 'finance-compact-selected-teacher-v1'
TEACHER = 'deepseek-v4-flash'
DATASETS = tuple(TRAIN)
PROFILE = ('model', 'serving_profile_sha256', 'max_tokens', 'temperature', 'single_temperature',
           'planned', 'without_logprobs', 'shared_request_cache', 'compiler_sha256', 'scorer_sha256')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def risk(case):
    """Lower sorts first: no executable choice, less agreement, less confidence."""
    decision = case['decision']
    n, executed, support = case['n'], decision['executed_n'], decision['vote_support']
    index, confidence = decision['selected_index'], decision['selected_min_token_logprob']
    if (not 0 <= support <= executed <= n or (index is None) != (executed == 0)
            or (index is not None and (type(index) is not int or not 0 <= index < n))
            or decision['vote_share'] != support / n or bool(support) != bool(executed)
            or (confidence is not None and (not isfinite(confidence) or confidence > 0))):
        raise ValueError(f'Invalid compact output for {case["id"]}')
    return int(executed > 0), support / n, float(confidence if confidence is not None else 0)


def route_case(case, policy, rate):
    """Decide from the current local output and a TRAIN-locked gate."""
    if policy['schema'] != SCHEMA:
        raise ValueError('Unexpected compact gate schema')
    cutoff = policy['arms'][f'n{case["n"]}']['pooled_cutoffs'][f'{rate:g}']['risk_cutoff']
    return cutoff is not None and risk(case) <= tuple(cutoff)


def local_cases(directory, public, identity):
    metadata = read(directory / 'run.json')
    if metadata['panel_sha256'] != identity:
        raise ValueError('Compact receipts do not identify these panel bytes')
    ids = {(row['dataset'], row['id']): row['report'] for row in public}
    groups = {n: {} for n in metadata['n']}
    with (directory / 'cases.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            key = row['dataset'], row['id']
            n = row['n']
            if (key not in ids or row['report'] != ids[key] or n not in groups or key in groups[n]
                    or row['transport'] != 'vllm_chat_nonstream' or row['request']['n'] != n
                    or row['request']['model'] != metadata['model']):
                raise ValueError('Expected exactly one matched native vLLM case per arm')
            label = row['score']['strict_executable']
            risk_key = risk(row)
            usage = row['usage']
            work = row['engine_work']
            wall = row['route_wall_seconds']
            known = usage['total_tokens'] if usage is not None else None
            if (type(label) is not bool or (label and not risk_key[0])
                    or not isfinite(wall) or wall < 0
                    or (known is not None and (type(known) is not int or known < 0))):
                raise ValueError(f'Invalid compact label, cost or latency for {key}')
            groups[n][key] = {'risk': risk_key, 'correct': label,
                              'first_correct': row['score']['first_sample_strict_executable'],
                              'local_api_tokens': known, 'local_engine_tokens': (
                                  work['locally_computed_tokens'] if work is not None else None),
                              'local_wall': wall}
    if not groups or any(rows.keys() != ids.keys() for rows in groups.values()):
        raise ValueError('Compact arm is incomplete')
    return groups, {field: metadata[field] for field in PROFILE}


def train_panel(summary, public, identity):
    provenance = read(summary)
    for dataset in DATASETS:
        source = provenance['provenance'][dataset]
        if source['split'] != 'train' or source['sha256'] != TRAIN[dataset][2]:
            raise ValueError('Gate fitting requires pinned official TRAIN sources')
    if ({row['dataset'] for row in public} != set(DATASETS)
            or provenance['partitions']['calibration']['rows'] != len(public)
            or any(provenance['outputs'][f'calibration/{name}']['sha256'] != digest
                   for name, digest in identity.items())):
        raise ValueError('Panel is not the frozen TRAIN calibration partition')


class ArchivedAnswer(NamedTuple):
    strict: bool
    executable: bool | None
    known_tokens: int
    unknown_usage_calls: int
    serial_seconds: float


def archived_answer(row):
    known, unknown, wall = (row[key] for key in ('known_tokens', 'unknown_usage_calls', 'summed_call_seconds'))
    strict, executed = row['strict'], row.get('executable')
    if (type(strict) not in (int, bool) or strict not in (0, 1)
            or (executed is not None and type(executed) is not bool)
            or type(known) is not int or known < 0 or type(unknown) is not int
            or not 0 <= unknown <= len(row['queried']) or not isfinite(wall) or wall < 0):
        raise ValueError('Invalid archived outcome, usage or timing')
    return ArchivedAnswer(bool(strict), executed, known, unknown, wall)


def teacher_item(row):
    if row['selected'] != 'deepseek' or row['queried'] != ['deepseek']:
        raise ValueError('Teacher items must come from one standalone DeepSeek call')
    item = archived_answer(row)
    if item.executable is None:
        raise ValueError('Shared compiler execution must be known before accepting a teacher answer')
    return item


def normalized_teacher(path, expected, identity):
    """Optional preexisting TRAIN replay, in the same per-case receipt schema."""
    archive = read(path)
    if (archive['model'] != TEACHER or archive['representation'] != 'shared_teacher_compiled'
            or archive['panel_sha256'] != identity):
        raise ValueError('Unmatched calibration teacher archive')
    raw = archive['items']
    rows = {(row['dataset'], row['id']): teacher_item(row) for row in raw}
    if len(rows) != len(raw) or rows.keys() != expected:
        raise ValueError('Calibration teacher archive must match the complete TRAIN panel')
    return rows


def frozen_cutoff(rows, rate, teacher, *, disagreement_only=False):
    """Include tied candidates together and learn the cutoff using TRAIN only."""
    buckets = Counter(row['risk'] for row in rows.values())
    gains = Counter()
    if teacher is not None:
        for key, row in rows.items():
            item = teacher[key]
            final = bool(item.strict) if item.executable else row['correct']
            gains[row['risk']] += int(final) - int(row['correct'])
    cap = floor(rate * len(rows))
    cutoff, actual, utility = None, 0, 0
    count, gain = 0, 0
    for key, size in sorted(buckets.items()):
        if disagreement_only and key[1] == 1:
            break
        count += size
        if count > cap:
            break
        gain += gains[key]
        if teacher is None or gain > utility:
            cutoff, actual, utility = key, count, gain
    return {'risk_cutoff': list(cutoff) if cutoff is not None else None,
            'train_cap': cap, 'train_selected': actual,
            'train_net_gain': utility if teacher is not None else None}


def total_or_unknown(values):
    return sum(value for value in values if value is not None), sum(value is None for value in values)


def summary(rows, cutoff=None, teacher=None):
    routed, final, walls = set(), {}, []
    local_api, unknown_local = total_or_unknown([row['local_api_tokens'] for row in rows.values()])
    local_engine, unknown_engine = total_or_unknown([row['local_engine_tokens'] for row in rows.values()])
    for key, row in rows.items():
        if cutoff is not None and row['risk'] <= tuple(cutoff):
            routed.add(key)
        item = teacher[key] if teacher is not None and key in routed else None
        final[key] = bool(item.strict) if item is not None and item.executable else row['correct']
        walls.append(row['local_wall'] + (item.serial_seconds if item is not None else 0))
    items = [teacher[key] for key in sorted(routed)] if teacher is not None else []
    known_remote = sum(item.known_tokens for item in items)
    unknown_remote = sum(item.unknown_usage_calls for item in items)
    extra_unknown = len(routed) if teacher is None else unknown_remote
    scored = teacher is not None or not routed
    return {
        'n': len(rows), 'local_correct': sum(row['correct'] for row in rows.values()),
        'first_sample_correct': sum(row['first_correct'] for row in rows.values()),
        'local_executable': sum(row['risk'][0] for row in rows.values()),
        'local_error_detection_auc': rank_auc([tuple(-v for v in row['risk']) for row in rows.values()],
                                              [not row['correct'] for row in rows.values()]),
        'teacher_calls': len(routed), 'teacher_executable': sum(item.executable for item in items) if scored else None,
        'nonunanimous_not_routed': sum(row['risk'][1] < 1 and key not in routed for key, row in rows.items()),
        'unanimous_wrong_not_routed': sum(row['risk'][1] == 1 and not row['correct'] and key not in routed
                                         for key, row in rows.items()),
        'correct': sum(final.values()) if scored else None,
        'recovered': sum(value and not rows[key]['correct'] for key, value in final.items()) if scored else None,
        'harmed': sum(not value and rows[key]['correct'] for key, value in final.items()) if scored else None,
        'local_logical_api_tokens_known': local_api, 'local_logical_api_usage_unknown_n': unknown_local,
        'local_engine_tokens_known': local_engine if unknown_engine < len(rows) else None,
        'local_engine_work_unknown_n': unknown_engine,
        'teacher_provider_tokens_known': known_remote, 'teacher_provider_usage_unknown_n': extra_unknown,
        'combined_api_tokens': None if unknown_local or extra_unknown else local_api + known_remote,
        'recorded_local_wall_seconds_sum': fsum(row['local_wall'] for row in rows.values()),
        'recorded_teacher_call_seconds_sum': fsum(item.serial_seconds for item in items) if scored else None,
        'stitched_serial_seconds_sum': fsum(walls) if scored else None,
        'stitched_serial_seconds_p50': median(walls) if scored else None,
    }, final, routed


def calibration_report(args, rows, identity):
    train_panel(args.train_summary, rows, identity)
    groups, profile = local_cases(args.local, rows, identity)
    keys = {(row['dataset'], row['id']) for row in rows}
    teacher = normalized_teacher(args.teacher, keys, identity) if args.teacher else None
    if not args.rates or any(not isfinite(rate) or not 0 < rate < 1 for rate in args.rates):
        raise ValueError('Expected budget fractions strictly between 0 and 1')
    if len(args.rates) != len(set(args.rates)):
        raise ValueError('Duplicate budget fractions')
    policy = {}
    for n, states in sorted(groups.items()):
        arms = {}
        for rate in sorted(args.rates):
            cutoff = frozen_cutoff(states, rate, teacher, disagreement_only=n > 1)
            arms[f'{rate:g}'] = {**cutoff, 'train': summary(states, cutoff['risk_cutoff'], teacher)[0]}
        no_teacher = {dataset: summary({key: row for key, row in states.items() if key[0] == dataset})[0]
                      for dataset in DATASETS}
        policy[f'n{n}'] = {'compact_only_train': no_teacher, 'pooled_cutoffs': arms}
    return {'schema': SCHEMA, 'train_panel_sha256': identity,
            'train_summary_sha256': digest_file(args.train_summary), 'profile': profile,
            'train_local_receipts_sha256': digest_file(args.local / 'cases.jsonl'),
            'train_teacher_sha256': digest_file(args.teacher) if args.teacher else None,
            'risk_order': 'Ascending (has-executable-result, execution vote share, selected minimum token logprob); '
                          'missing logprob is neutral and exact cutoff ties route together. '
                          'Multisample unanimity accepts locally, regardless of the call cap.',
            'calibration': ('Maximize paired net gains within each TRAIN call cap; ties favor fewer calls.'
                            if teacher is not None else 'Use pooled, label-free TRAIN call-rate quantiles.'),
            'arms': policy}


def original_archives(paths, public, identity):
    teacher, originals, baseline_rows, profiles = {}, {}, {}, []
    for dataset, cascade_path, report_path in paths:
        if dataset not in DATASETS or dataset in originals:
            raise ValueError('Specify one unique compiled Cascade and frontier report for each dataset')
        compiled, frontier = read(cascade_path), read(report_path)
        source_hash = digest_file(cascade_path)
        items = {row['id'] for row in public if row['dataset'] == dataset}
        if (compiled['dataset'] != dataset or compiled['representation'] != 'compiled'
                or frontier['dataset'] != dataset or frontier['panel'] != identity
                or frontier['input_sha256']['cascade_compiled'] != source_hash or frontier['n'] != len(items)):
            raise ValueError(f'Unmatched historical benchmark panel or Cascade input for {dataset}')
        profile = [item for item in compiled['profiles'] if item['model'] == TEACHER]
        if len(profile) != 1 or not profile[0]['api_profile_sha256'] or not profile[0]['opencode_sha256']:
            raise ValueError('Expected the original campus DeepSeek/OpenCode run profile')
        profiles.append(profile[0])
        raw = compiled['policies']['always_deepseek']['items']
        rows = {row['id']: teacher_item(row) for row in raw}
        if rows.keys() != items or len(rows) != len(raw):
            raise ValueError(f'{dataset}: teacher receipts do not cover panel exactly once')
        teacher.update({(dataset, key): item for key, item in rows.items()})
        baseline_rows[dataset] = {}
        for name in ('always_deepseek', 'nonexecution_deepseek_qwen', 'nonexecution_qwen_deepseek',
                     'cascade_routing_1.5'):
            raw_baseline = compiled['policies'][name]['items']
            index = {(dataset, row['id']): archived_answer(row) for row in raw_baseline}
            if {ident for _, ident in index} != items or len(index) != len(raw_baseline):
                raise ValueError(f'{dataset}/{name}: baseline rows do not cover the panel exactly once')
            baseline_rows[dataset][name] = index
        originals[dataset] = {'cascade_compiled_sha256': source_hash,
                              'frontier_report_sha256': digest_file(report_path),
                              'teacher_direct_historical_wall': compiled.get('managed_direct_wall', {}).get('deepseek'),
                              'benchmark_aggregates': frontier['strata']['all']['policies'],
                              'benchmark_common_known_usage': frontier['strata']['common_complete_usage']['policies']}
    if originals.keys() != {row['dataset'] for row in public} or any(p != profiles[0] for p in profiles[1:]):
        raise ValueError('Both datasets must use the same archived DeepSeek/OpenCode profile')
    return teacher, originals, baseline_rows, profiles[0]


def compare(final, baseline, reports, draws):
    if final.keys() != baseline.keys():
        raise ValueError('Paired correctness requires the same item IDs')
    examples = [(reports[key], {'cascade': {'strict': int(final[key])},
                                'reference': {'strict': int(baseline[key])}}) for key in sorted(final)]
    return paired_effect(examples, (('cascade', 'strict'), ('reference', 'strict')), draws)


def selected_teacher(path, groups, policy, identity, policy_digest, local_digest, compiler_digest):
    archive = read(path)
    if (archive['schema'] != SELECTED_SCHEMA or archive['model'] != TEACHER
            or archive['panel_sha256'] != identity or archive['policy_sha256'] != policy_digest
            or archive['local_receipts_sha256'] != local_digest
            or archive['compiler_sha256'] != compiler_digest or not archive['teacher_profile_sha256']):
        raise ValueError('Unmatched fresh selected-teacher collection')
    n, rate = archive['n'], f'{archive["rate"]:g}'
    cutoff = policy['arms'][f'n{n}']['pooled_cutoffs'][rate]['risk_cutoff']
    expected = {key for key, row in groups[n].items() if cutoff is not None and row['risk'] <= tuple(cutoff)}
    items = archive['items']
    normalized = {(row['dataset'], row['id']): teacher_item(row) for row in items}
    if len(normalized) != len(items) or normalized.keys() != expected:
        raise ValueError('Fresh teacher collection must cover exactly the cases selected by the frozen gate')
    wall = {(row['dataset'], row['id']): row.get('online_route_seconds') for row in items}
    if any(seconds is not None and (not isfinite(seconds) or seconds < 0) for seconds in wall.values()):
        raise ValueError('Invalid measured selected-route wall time')
    return normalized, wall, n, rate, archive['teacher_profile_sha256']


def replay_report(args, rows, identity):
    policy = read(args.policy)
    calibration, _, cal_identity = read_panel(args.calibration_panel, None)
    groups, profile = local_cases(args.local, rows, identity)
    if (policy['schema'] != SCHEMA or policy['train_panel_sha256'] != cal_identity
            or policy['profile'] != profile or not {f'n{n}' for n in groups} <= policy['arms'].keys()):
        raise ValueError('Official replay requires an unchanged compact profile and frozen TRAIN policy')
    train_panel(args.train_summary, calibration, cal_identity)
    if digest_file(args.train_summary) != policy['train_summary_sha256']:
        raise ValueError('TRAIN provenance summary differs from the frozen policy')
    train_sources = {key for row in calibration for key in identity_keys(row)}
    if any(train_sources.intersection(identity_keys(row)) for row in rows):
        raise ValueError('TRAIN calibration and evaluation source groups overlap')
    teacher, originals, baseline_rows, teacher_profile = original_archives(args.archive, rows, identity)
    policy_digest = digest_file(args.policy)
    local_digest = digest_file(args.local / 'cases.jsonl')
    fresh = None
    if args.selected_teacher is not None:
        fresh = selected_teacher(args.selected_teacher, groups, policy, identity, policy_digest, local_digest,
                                 read(args.local / 'run.json')['compiler_sha256'])
    reports = {(row['dataset'], row['id']): row['report'] for row in rows}
    results, routes = {}, {}
    for dataset in sorted(originals):
        for n, states in sorted(groups.items()):
            subset = {key: row for key, row in states.items() if key[0] == dataset}
            local = {key: row['correct'] for key, row in subset.items()}
            tag = f'{dataset}/n{n}'
            results[tag] = {'compact_only': summary(subset)[0], 'budget_points': {}}
            for rate, gate in policy['arms'][f'n{n}']['pooled_cutoffs'].items():
                stats, final, routed = summary(subset, gate['risk_cutoff'], teacher)
                routes[f'{tag}/{rate}'] = sorted(ident for _, ident in routed)
                recovery = [key for key in sorted(subset) if not local[key]]
                stats['conditional_teacher_recovery_auc'] = rank_auc(
                    [tuple(-v for v in subset[key]['risk']) for key in recovery],
                    [bool(teacher[key].strict and teacher[key].executable) for key in recovery])
                stats['paired_against_compact'] = compare(final, local, reports, args.bootstrap_draws)
                # Scorers' unknown execution flags affect joint-success comparisons only.
                stats['paired_against_archived_compiled'] = {
                    name: compare(final, {k: item.strict and item.executable for k, item in items.items()},
                                  reports, args.bootstrap_draws)
                    for name, items in baseline_rows[dataset].items()
                    if all(item.executable is not None for item in items.values())}
                if fresh is not None and (n, rate) == (fresh[2], fresh[3]):
                    fresh_stats, final_fresh, _ = summary(subset, gate['risk_cutoff'], fresh[0])
                    fresh_stats['paired_against_compact'] = compare(final_fresh, local, reports, args.bootstrap_draws)
                    route_wall = fresh[1]
                    if all(route_wall[key] is not None for key in routed):
                        measured = [route_wall[key] if key in routed else row['local_wall'] for key, row in subset.items()]
                        fresh_stats['measured_end_to_end_wall_seconds_sum'] = fsum(measured)
                        fresh_stats['measured_end_to_end_wall_seconds_p50'] = median(measured)
                    stats['fresh_selected_teacher'] = fresh_stats
                results[tag]['budget_points'][rate] = stats
    if args.routes is not None:
        freeze(args.routes, routes)
    return {'panel_sha256': identity, 'policy_sha256': policy_digest, 'local_receipts_sha256': local_digest,
            'calibration_panel_sha256': cal_identity, 'teacher_profile': teacher_profile,
            'fresh_selected_teacher_profile_sha256': fresh[4] if fresh is not None else None,
            'teacher_rule': 'One compiled DeepSeek answer per selected case. Retain local answer if it cannot execute.',
            'historical_teacher_scope': 'Archived DeepSeek prompts and compiler differ from the current shared contract. '
                                        'These rows are historical replay references.',
            'timing_scope': 'Compact wall is directly measured. Teacher call time comes from matched historical '
                            'requests. Their per-case sum is a serial replay estimate. Fresh route wall is reported '
                            'separately when a matching selected-teacher receipt records it.',
            'budget_scope': 'Fractions are TRAIN caps. Fixed cutoffs can yield a different realized rate per dataset.',
            'evaluation': results, 'original_baselines': originals}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest='action', required=True)
    for mode in ('calibrate', 'replay'):
        command = subcommands.add_parser(mode)
        for flag in ('panel', 'local', 'output', 'train-summary'):
            command.add_argument(f'--{flag}', type=Path, required=True)
        if mode == 'calibrate':
            command.add_argument('--rates', type=float, nargs='+', default=(.1, .15, .2, .25))
            command.add_argument('--teacher', type=Path)
        else:
            command.add_argument('--policy', type=Path, required=True)
            command.add_argument('--calibration-panel', type=Path, required=True)
            command.add_argument('--archive', type=Path, nargs=3, action='append', required=True,
                                 metavar=('DATASET', 'CASCADE_COMPILED', 'FRONTIER_REPORT'))
            command.add_argument('--routes', type=Path)
            command.add_argument('--selected-teacher', type=Path)
            command.add_argument('--bootstrap-draws', type=int, default=2000)
    args = parser.parse_args()
    rows, _, identity = read_panel(args.panel, None)
    if args.action == 'calibrate':
        report = calibration_report(args, rows, identity)
    else:
        if args.bootstrap_draws < 1:
            parser.error('--bootstrap-draws must be positive')
        args.archive = [(str(dataset), cascade, report) for dataset, cascade, report in args.archive]
        report = replay_report(args, rows, identity)
    freeze(args.output, report)


if __name__ == '__main__':
    main()
