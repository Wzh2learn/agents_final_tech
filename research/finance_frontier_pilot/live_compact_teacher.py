"""Time fresh Compact-to-DeepSeek and DeepSeek-only routes on shared official panels."""

import argparse
from contextlib import closing
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
from statistics import fmean, median
import sys
from time import monotonic
from uuid import uuid4

from benchmark_actions import action_cost, deliver, digest_file, freeze, grade_case, read_panel
from compact_consensus import SAMPLE_COUNTS, call_compact, compact_prompt
from compact_frontier import SCHEMA, SELECTED_SCHEMA, TEACHER, local_cases, risk, route_case
from live_policy_timing import OFFICIAL_COUNTS, paired_online_wall, stratified_cases, validate_official_panel
from run_pilot import local_endpoint
from scoring import _metric_type, parse_dsl, public_execution
import school_benchmark as school
from table_scope_replay import representation


POLICIES = ('compact-teacher', 'deepseek-direct')
PRIVATE = (Path.home() / 'wzh/research_evidence').resolve()


def checked_json(path, expected):
    if digest_file(path) != expected:
        raise ValueError(f'Pinned artifact digest mismatch: {path.name}')
    return json.loads(path.read_text(encoding='utf-8'))


def gate_profile(policy, serving, serving_digest, n, rate):
    if policy['schema'] != SCHEMA or not isfinite(rate) or not 0 < rate < 1:
        raise ValueError('Expected a frozen pooled TRAIN policy and a finite fractional rate')
    profile = policy['profile']
    if (profile['serving_profile_sha256'] != serving_digest or profile['model'] != serving['model']
            or type(profile['max_tokens']) is not int or not 0 < profile['max_tokens'] <= 80
            or not isfinite(profile['temperature']) or not 0 < profile['temperature'] <= 2
            or profile['without_logprobs'] or profile['shared_request_cache']):
        raise ValueError('Live serving or sampling differs from the frozen TRAIN gate')
    cutoff = policy['arms'][f'n{n}']['pooled_cutoffs'][f'{rate:g}']['risk_cutoff']
    if cutoff is not None and (
        not isinstance(cutoff, list) or len(cutoff) != 3 or cutoff[0] not in (0, 1)
        or not 0 <= cutoff[1] <= 1 or not isfinite(cutoff[2]) or cutoff[2] > 0
    ):
        raise ValueError('Invalid frozen risk cutoff')
    return profile


def official_cases(args, public, gold, panel):
    cases, manifests = [], {}
    for dataset in args.datasets:
        rows = [row for row in public if row['dataset'] == dataset]
        validate_official_panel(args.benchmark, dataset, rows, gold)
        if not args.full_panel:
            archive = args.benchmark / f'matched_live_policy_{dataset}_stratified_v1/run.json'
            saved = json.loads(archive.read_text(encoding='utf-8'))
            sampled, strata = stratified_cases(rows, gold, dataset)
            expected_order = [row['id'] for row, _ in sampled]
            if (saved['schema'] != 'finance-live-policy-timing-stratified-v1' or saved['dataset'] != dataset
                    or saved['panel'] != panel or [row['id'] for row in saved['case_order']] != expected_order
                    or saved['stratified_sampling'] != strata):
                raise ValueError(f'{dataset} historical timing membership differs from the deterministic sample')
            manifests[dataset] = digest_file(archive)
            rows = [row for row, _ in sampled]
        cases.extend((row, POLICIES if index % 2 == 0 else POLICIES[::-1]) for index, row in enumerate(rows))
    return cases, manifests


def local_call(args, profile, row, seed, salt):
    case = call_compact(
        row, base=args.base, model=profile['model'], n=args.n, max_tokens=profile['max_tokens'],
        temperature=profile['temperature'] if args.n > 1 else profile.get('single_temperature', 0.0), seed=seed,
        timeout=args.timeout, cache_salt=salt, planned=profile['planned'],
    )
    return {**case, 'id': row['id'], 'n': args.n}


def local_selection(row, case):
    decision = case['decision']
    index = decision['selected_index']
    if index is None:
        return {'submission': parse_dsl(''), 'decision': 'no_local_program'}, row
    sample = decision['samples'][index]
    projection = {**row, 'table': sample['table_projection']} if 'table_projection' in sample else row
    return {'submission': sample['submission'], 'decision': sample['stage']}, projection


def teacher_selection(row, receipt):
    reply = deliver(receipt) if receipt['finish'] == ['stop'] else ''
    projection, submission, stage, _ = representation(
        row, reply, stopped=bool(reply),
    )
    execution = public_execution(projection, submission)
    return {'submission': submission, 'decision': stage}, projection, execution['status'] == 'executed'


def timed_arm(args, policy, profile, row, arm, root, index, run_salt, teacher_call, has_capacity, seed_index=None):
    started = monotonic()
    local, remote, local_risk = None, None, None
    calls = []
    teacher_path = None
    if arm == 'compact-teacher':
        salt = sha256(f'{run_salt}:{index}'.encode()).hexdigest()
        local = local_call(args, profile, row, args.seed + (index if seed_index is None else seed_index) * 8, salt)
        local_risk = risk(local)
        dispatch = route_case(local, policy, args.rate)
        selected, projection = local_selection(row, local)
        calls.append({'usage': school.measured_usage(local['response']['usage']) if local['usage'] else None,
                      'elapsed_seconds': local['model_wall_seconds']})
    else:
        dispatch = True
        selected, projection = {'submission': parse_dsl(''), 'decision': 'no_teacher_program'}, row
    result = {'risk': local_risk, 'compact': local, 'teacher_requested': dispatch}
    if dispatch:
        if not has_capacity():
            return {**result, 'status': 'incomplete_budget', 'wall_seconds': monotonic() - started,
                    'cost': action_cost(calls)}, None, None
        identity = sha256(f'{row["dataset"]}:{row["id"]}'.encode()).hexdigest()[:24]
        target = root / 'calls' / identity / arm
        remote = teacher_call(target, compact_prompt(row, planned=profile['planned']))
        calls.append(remote)
        teacher_path = (target / 'provider_receipt.json').relative_to(root).as_posix()
        candidate, teacher_projection, executable = teacher_selection(row, remote)
        if executable or arm == 'deepseek-direct':
            selected, projection = candidate, teacher_projection
            selected['model'] = TEACHER
    if 'model' not in selected:
        selected['model'] = profile['model']
    public_execution(projection, selected['submission'])
    wall = monotonic() - started
    return {**result, 'status': 'complete', 'wall_seconds': wall, 'cost': action_cost(calls),
            'local_api_tokens': local['usage']['total_tokens'] if local and local['usage'] else None,
            'teacher_api_tokens': remote['usage']['total'] if remote and remote['usage'] else None,
            'teacher_call': teacher_path, 'teacher_posts': remote['provider_posts'] if remote else 0}, selected, projection


def collect(args, root, policy, profile, cases, gold, budget, key, teacher_profile, gateway, digest, run_salt,
            seed_indices=None):
    def teacher_call(target, prompt):
        return school.fresh_managed_call(target, args.opencode, digest, prompt, key=key, budget=budget,
                                         profile=teacher_profile, gateway=gateway)

    opening_index = len(budget.rows)
    records = {dataset: {policy: [] for policy in POLICIES} for dataset in args.datasets}
    reports = {dataset: {} for dataset in args.datasets}
    stopped = False
    with (root / 'outcomes.jsonl').open('x', encoding='utf-8') as stream:
        for index, (row, order) in enumerate(cases):
            dataset, ident = row['dataset'], row['id']
            matched = {}
            for arm in order:
                item, selected, projection = timed_arm(
                    args, policy, profile, row, arm, root, index, run_salt, teacher_call,
                    lambda: school.has_gateway_capacity(budget),
                    seed_index=seed_indices[dataset, ident] if seed_indices is not None else None,
                )
                if selected is not None:
                    item['result'] = grade_case(row, gold[dataset, ident], {'final': selected},
                                                {'final': projection}, args.metric_dir)['final']
                matched[arm] = item
                if item['status'] != 'complete':
                    stopped = True
                    break
            log = {'dataset': dataset, 'id': ident, 'report': row['report'], 'order': order,
                   'complete_pair': not stopped, 'policies': matched}
            print(json.dumps(log, ensure_ascii=False, allow_nan=False), file=stream, flush=True)
            if stopped:
                break
            reports[dataset][ident] = row['report']
            for arm, item in matched.items():
                records[dataset][arm].append({name: item[name] for name in (
                    'result', 'wall_seconds', 'cost', 'teacher_requested', 'teacher_posts',
                    'local_api_tokens', 'teacher_api_tokens',
                )})
    metrics = {}
    for dataset, arms in records.items():
        metrics[dataset] = {}
        for arm, rows in arms.items():
            wall = [row['wall_seconds'] for row in rows]
            metrics[dataset][arm] = {
                'n': len(rows), 'strict_executable': sum(row['result']['strict'] and row['result']['executable']
                                                         for row in rows),
                'mean_wall_seconds': fmean(wall) if wall else None,
                'median_wall_seconds': median(wall) if wall else None,
                'known_tokens': sum(row['cost']['known_tokens'] for row in rows),
                'unknown_usage_calls': sum(row['cost']['unknown_usage_calls'] for row in rows),
                'known_local_api_tokens': sum(row['local_api_tokens'] or 0 for row in rows),
                'known_teacher_api_tokens': sum(row['teacher_api_tokens'] or 0 for row in rows),
                'teacher_requests': sum(row['teacher_requested'] for row in rows),
                'teacher_posts': sum(row['teacher_posts'] for row in rows),
            }
        if reports[dataset]:
            metrics[dataset]['paired_wall'] = paired_online_wall(arms, reports[dataset], proposed=POLICIES[0])
    posts, tokens = school.charged(budget.rows[opening_index:])
    freeze(root / 'collection.json', {'planned_pairs': len(cases), 'completed_pairs': sum(map(len, reports.values())),
                                      'stop_reason': 'gateway_budget' if stopped else None,
                                      'campus_posts': posts, 'campus_debit_including_unknown': tokens,
                                      'metrics': metrics})


def selected_rows(args, public, panel, policy, compiler_sha):
    """Join every official row to its finished local output before selecting teachers."""
    local_root = args.selected_local
    groups, profile = local_cases(local_root, public, panel)
    local_run = local_root / 'run.json'
    if (profile != policy['profile'] or json.loads(local_run.read_bytes())['compiler_sha256'] != compiler_sha
            or args.n not in groups):
        raise ValueError('Local outputs differ from the frozen serving, gate, or compiler')
    cutoff = policy['arms'][f'n{args.n}']['pooled_cutoffs'][f'{args.rate:g}']['risk_cutoff']
    threshold = None if cutoff is None else tuple(cutoff)
    rows = [row for row in public if threshold is not None
            and groups[args.n][row['dataset'], row['id']]['risk'] <= threshold]
    return rows, {'local_receipts_sha256': digest_file(local_root / 'cases.jsonl'),
                  'local_run_sha256': digest_file(local_run)}


def collect_selected(args, root, rows, gold, lock, budget, key, teacher_profile, gateway, run_digest):
    """Attach fresh teacher execution to a previously recorded compact decision."""
    opening_index = len(budget.rows)
    items = []
    with (root / 'selected_attempts.jsonl').open('x', encoding='utf-8') as stream:
        for row in rows:
            if not school.has_gateway_capacity(budget):
                break
            dataset, ident = row['dataset'], row['id']
            target = root / 'calls' / sha256(f'{dataset}:{ident}'.encode()).hexdigest()[:24]
            prompt = compact_prompt(row, planned=lock['planned'])
            receipt = school.fresh_managed_call(target, args.opencode, run_digest, prompt,
                                                key=key, budget=budget, profile=teacher_profile, gateway=gateway)
            answer, projection, executable = teacher_selection(row, receipt)
            graded = grade_case(row, gold[dataset, ident], {'teacher': answer},
                                {'teacher': projection}, args.metric_dir)['teacher']
            if executable != graded['executable']:
                raise ValueError('The response execution and official scorer disagree about program validity')
            item = {'dataset': dataset, 'id': ident, 'selected': 'deepseek', 'queried': ['deepseek'],
                    'strict': graded['strict'], 'executable': executable, **action_cost([receipt]),
                    'online_route_seconds': None,
                    'teacher_receipt': (target / 'provider_receipt.json').relative_to(root).as_posix()}
            print(json.dumps(item, ensure_ascii=False, allow_nan=False), file=stream, flush=True)
            items.append(item)
    complete = len(items) == len(rows)
    posts, tokens = school.charged(budget.rows[opening_index:])
    freeze(root / 'collection.json', {'planned': len(rows), 'completed': len(items), 'complete': complete,
                                      'stop_reason': None if complete else 'gateway_budget',
                                      'campus_posts': posts, 'campus_debit_including_unknown': tokens})
    if complete:
        freeze(root / 'selected_teacher.json', {'schema': SELECTED_SCHEMA, **lock, 'items': items})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('panel', 'benchmark', 'output', 'gate', 'serving-profile', 'api-profile', 'metric-dir'):
        parser.add_argument(f'--{name}', type=Path, required=True)
    for name in ('gate-sha256', 'serving-profile-sha256', 'api-profile-sha256'):
        parser.add_argument(f'--{name}', required=True)
    parser.add_argument('--base', type=local_endpoint, default='http://127.0.0.1:18157/v1')
    parser.add_argument('--opencode', type=Path, default=Path.home() / '.opencode/bin/opencode')
    parser.add_argument('--n', type=int, choices=SAMPLE_COUNTS, required=True)
    parser.add_argument('--rate', type=float, required=True)
    parser.add_argument('--seed', type=int, default=20261127)
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--datasets', nargs='+', choices=tuple(OFFICIAL_COUNTS), default=list(OFFICIAL_COUNTS))
    parser.add_argument('--full-panel', action='store_true')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--live', action='store_true', help='Measure fresh compact and teacher paths (default)')
    mode.add_argument('--selected-local', type=Path, help='Collect teachers only for selected cached official rows')
    parser.add_argument('--dry-run', action='store_true', help='Validate frozen inputs and show the sample size without calls')
    parser.add_argument('--max-posts', type=int, required=True)
    parser.add_argument('--token-cap', type=int, required=True)
    parser.add_argument('--prior-charged-tokens', type=int, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    if (sys.platform != 'linux' or not root.is_relative_to(PRIVATE) or root.exists()
            or not args.benchmark.resolve().is_relative_to(PRIVATE)
            or not args.panel.resolve().is_relative_to(PRIVATE)):
        parser.error('use a fresh output and the private GB10 benchmark inputs')
    if (not 0 < args.max_posts or args.token_cap < school.campus.REQUEST_TOKEN_CEILING
            or not school.RECORDED_PRIOR_CHARGE <= args.prior_charged_tokens < school.PROJECT_CAP
            or len(set(args.datasets)) != len(args.datasets) or not isfinite(args.timeout) or args.timeout <= 0):
        parser.error('require valid caps, charge history, timeout and unique datasets')
    policy = checked_json(args.gate, args.gate_sha256)
    serving = checked_json(args.serving_profile, args.serving_profile_sha256)
    profile = gate_profile(policy, serving, args.serving_profile_sha256, args.n, args.rate)
    teacher_profile, gateway = school.read_profile(args.api_profile, args.api_profile_sha256)
    if gateway['model_id'] != TEACHER:
        parser.error('the admitted teacher for this policy is DeepSeek V4 Flash')
    public, gold, panel = read_panel(args.panel, None)
    compiler_sha = digest_file(Path(__file__).with_name('table_scope_replay.py'))
    scorer_sha = digest_file(Path(__file__).with_name('scoring.py'))
    if profile.get('compiler_sha256', compiler_sha) != compiler_sha or profile.get('scorer_sha256', scorer_sha) != scorer_sha:
        parser.error('the current compiler or scorer differs from the frozen policy')
    if args.selected_local is None:
        cases, manifests = official_cases(args, public, gold, panel)
        seed_indices = {(row['dataset'], row['id']): index for index, row in enumerate(public)}
    else:
        args.selected_local = args.selected_local.resolve()
        if not args.selected_local.is_relative_to(PRIVATE) or set(args.datasets) != set(OFFICIAL_COUNTS):
            parser.error('selected-only collection requires the full official local cache for both datasets')
        for dataset in args.datasets:
            validate_official_panel(args.benchmark, dataset, [row for row in public if row['dataset'] == dataset], gold)
        routed, local_sources = selected_rows(args, public, panel, policy, compiler_sha)
        lock = {'model': TEACHER, 'panel_sha256': panel, 'policy_sha256': args.gate_sha256,
                'compiler_sha256': compiler_sha, 'scorer_sha256': scorer_sha,
                'teacher_profile_sha256': args.api_profile_sha256,
                'n': args.n, 'rate': args.rate, 'planned': profile['planned'], **local_sources}
        if len(routed) > args.max_posts:
            parser.error(f'the frozen selection contains {len(routed)} rows, exceeding the request cap')
    if 'tatqa' in args.datasets:
        _metric_type(args.metric_dir)
    if args.dry_run:
        if args.selected_local is None:
            print(json.dumps({'pairs': len(cases), 'datasets': args.datasets,
                              'gate_sha256': args.gate_sha256, 'sample_manifests_sha256': manifests}))
        else:
            print(json.dumps({'selected': {dataset: sum(row['dataset'] == dataset for row in routed)
                                           for dataset in args.datasets}, **lock}))
        return
    key = os.environ.get('BUPT_API_KEY')
    if not key:
        parser.error('BUPT_API_KEY is required in the authorized process environment')
    args.opencode = args.opencode.resolve(strict=True)
    run_salt = uuid4().hex
    with closing(school.campus.BatchBudget(PRIVATE / '.finance_frontier_campus_budget')) as budget:
        freeze(budget.root / 'opening.json', {'project_cap': school.PROJECT_CAP,
                                              'historical_charged_tokens': args.prior_charged_tokens})
        opening_posts, opening_tokens = school.charged(budget.rows)
        budget.posts = opening_posts + args.max_posts
        budget.tokens = min(school.PROJECT_CAP - args.prior_charged_tokens, opening_tokens + args.token_cap)
        if not school.has_gateway_capacity(budget):
            parser.error('shared ledger has no headroom for the first request')
        root.mkdir(parents=True, mode=0o700, exist_ok=False)
        run = root / 'run.json'
        if args.selected_local is not None:
            freeze(run, {'schema': 'finance-compact-selected-teacher-run-v1', **lock,
                         'routes': [(row['dataset'], row['id']) for row in routed],
                         'opencode_sha256': digest_file(args.opencode),
                         'runner_sha256': digest_file(Path(__file__)), 'opening_posts': opening_posts,
                         'opening_tokens': opening_tokens, 'max_new_posts': args.max_posts, 'token_cap': args.token_cap,
                         'measurement': 'Fresh teacher and cached compact calls; no end-to-end route wall time.'})
            collect_selected(args, root, routed, gold, lock, budget, key, teacher_profile, gateway, digest_file(run))
            return
        freeze(run, {
            'schema': 'finance-compact-deepseek-live-v1', 'panel_sha256': panel,
            'historical_timing_membership_sha256': manifests,
            'case_order': [{'dataset': row['dataset'], 'id': row['id'], 'order': order,
                            'local_seed': args.seed + seed_indices[row['dataset'], row['id']] * 8} for row, order in cases],
            'gate_sha256': args.gate_sha256, 'serving_profile_sha256': args.serving_profile_sha256,
            'teacher_profile_sha256': args.api_profile_sha256, 'teacher_model': TEACHER,
            'compiler_sha256': compiler_sha, 'scorer_sha256': scorer_sha,
            'opencode_sha256': digest_file(args.opencode), 'runner_sha256': digest_file(Path(__file__)),
            'gate_rate': args.rate, 'n': args.n, 'seed': args.seed, 'run_salt': run_salt,
            'base': args.base, 'opening_posts': opening_posts, 'opening_tokens': opening_tokens,
            'max_new_posts': args.max_posts, 'token_cap': args.token_cap,
            'measurement': 'Fresh alternating serial requests through native execution; scoring follows timing.',
        })
        collect(args, root, policy, profile, cases, gold, budget, key, teacher_profile, gateway,
                digest_file(run), run_salt, seed_indices=seed_indices)


if __name__ == '__main__':
    main()
