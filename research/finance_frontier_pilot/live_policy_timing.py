"""Measure three fixed policies with fresh, interleaved calls on a bounded TRAIN panel."""

import argparse
from hashlib import sha256
from itertools import permutations
import json
import os
from pathlib import Path
from random import Random
import re
from statistics import median, quantiles
import sys
from time import monotonic

from benchmark_actions import action_cost, deliver, digest_file, freeze, grade_case, read_panel, recorded_call, select_case
from run_pilot import OpenCode, local_endpoint, paired_prompt, wait_service, write_json
from scoring import _metric_type, public_execution
import school_benchmark as school
from table_scope_replay import public_contract


POLICIES = ('oda-local', 'contract', 'ds-first')
MANAGED = (school.campus.QWEN_MODEL, school.campus.MODEL)
ODA = 'oda-fin-rl-8b'
ODA_CHECKPOINT = '948c22ea48f9bf93e5747f4211657fcad9cb0295'
ORDER_SEED = 20261120


class TimingBudgetExhausted(Exception):
    """A measured policy could not dispatch its next managed request."""


def select_policy(row, policy, call):
    """Select only from the public report and newly requested model replies."""
    if policy not in POLICIES:
        raise ValueError(f'unknown timed policy {policy}')
    calls = []
    if policy != 'ds-first':
        outputs, projections = select_case(row, ['compiled_fallback'], call)
        draft = outputs['compiled_fallback']
        projected = projections.get('compiled_fallback', row)
        calls.extend(draft['calls'])
        trace = public_execution(projected, draft['submission'])
        executable = trace is not None and trace['status'] == 'executed'
        if policy == 'oda-local' or executable or type(draft['submission']['answer']) in (int, float):
            stage = 'compiled_oda' if executable else 'free_oda'
            return {**draft, 'selected_stage': stage, 'selected_model': ODA}, projected

    order = MANAGED if policy == 'contract' else tuple(reversed(MANAGED))
    for model in order:
        receipt = call(model, 'solve', paired_prompt(row, 'dsl'))
        calls.append(model)
        reply = deliver(receipt)
        projected, candidate, decision, cells = public_contract(row, reply, stopped=bool(reply) and receipt['finish'] == ['stop'])
        if public_execution(projected, candidate)['status'] == 'executed':
            break
    return {'submission': candidate, 'decision': decision, 'source_cells': cells, 'calls': calls,
            'selected_stage': f'compiled_{model}', 'selected_model': model}, projected


def frozen_cases(rows, count):
    if not 1 <= count <= len(rows):
        raise ValueError('timing size must be within the selected official TRAIN split')
    key = lambda row: sha256(f'{ORDER_SEED}|{row["dataset"]}|{row["id"]}'.encode()).hexdigest()
    orders = list(permutations(POLICIES))
    Random(ORDER_SEED).shuffle(orders)
    return [(row, orders[i % len(orders)]) for i, row in enumerate(sorted(rows, key=key)[:count])]


def summed_cost(costs):
    known = sum(item['known_tokens'] for item in costs)
    unknown = sum(item['unknown_usage_calls'] for item in costs)
    return {'calls': sum(item['calls'] for item in costs), 'known_tokens': known,
            'unknown_usage_calls': unknown, 'total_tokens': None if unknown else known,
            'summed_call_seconds': sum(item['summed_call_seconds'] for item in costs)}


def collect_cases(args, root, cases, gold, actor, profiles, budget, key, run_digest):
    completed = 0
    started = monotonic()
    start_index = len(budget.rows)
    stopped = False
    pair_records = {name: [] for name in POLICIES}
    all_costs = []
    with (root / 'outcomes.jsonl').open('x', encoding='utf-8') as stream:
        for row, order in cases:
            ident = sha256(row['id'].encode()).hexdigest()[:24]
            measured = {}
            for policy in order:
                receipts = {}

                def call(name, role, prompt):
                    target = root / 'calls' / ident / policy / name
                    if role != 'solve' or target.exists() or name in receipts:
                        raise ValueError('live timing expects independent fresh solve calls')
                    if name in profiles:
                        if not school.has_gateway_capacity(budget):
                            raise TimingBudgetExhausted
                        profile, gateway = profiles[name]
                        result = school.fresh_managed_call(target, args.opencode, run_digest, prompt,
                                                           key=key, budget=budget, profile=profile, gateway=gateway)
                        receipt_path = target / 'provider_receipt.json'
                    else:
                        result = recorded_call(actor, prompt, target, run_digest)
                        receipt_path = target / 'call.json'
                    fields = ('usage', 'elapsed_seconds', 'exit_code', 'finish', 'errors', 'provider_posts')
                    receipts[name] = {**{item: result[item] for item in fields if item in result},
                                      'path': receipt_path.relative_to(root).as_posix()}
                    return result

                begin = monotonic()
                try:
                    selected, projection = select_policy(row, policy, call)
                    if selected['calls'] != list(receipts):
                        raise ValueError('selected call order and metered calls disagree')
                except TimingBudgetExhausted:
                    cost = action_cost(list(receipts.values()))
                    measured[policy] = {'status': 'incomplete_budget', 'wall_seconds': monotonic() - begin,
                                        'calls': receipts, 'cost': cost}
                    stopped = True
                    break
                cost = action_cost(list(receipts.values()))
                wall = monotonic() - begin
                scored = grade_case(row, gold[row['dataset'], row['id']], {'selected': selected},
                                    {'selected': projection}, args.metric_dir)['selected']
                measured[policy] = {'status': 'complete', 'wall_seconds': wall, 'result': scored,
                                    'calls': receipts, 'cost': cost}
            report = {item: row[item] for item in ('dataset', 'id', 'report')}
            report.update(policy_order=order, policies=measured, complete_pair=not stopped)
            stream.write(json.dumps(report, ensure_ascii=False, allow_nan=False) + '\n')
            stream.flush()
            all_costs.extend(record['cost'] for record in measured.values())
            if stopped:
                break
            for name, record in measured.items():
                pair_records[name].append(record)
            completed += 1

    policies = {}
    for name, records in pair_records.items():
        durations = [record['wall_seconds'] for record in records]
        p90 = quantiles(durations, n=10, method='inclusive')[-1] if len(durations) > 1 else next(iter(durations), None)
        policies[name] = {'n': len(records), 'correct': sum(record['result']['strict'] for record in records),
                          'median_wall_seconds': median(durations) if durations else None, 'p90_wall_seconds': p90,
                          'cost': summed_cost([record['cost'] for record in records])}
    posts, tokens = school.charged(budget.rows[start_index:])
    write_json(root / 'collection.json', {
        'complete_paired_questions': completed, 'planned_questions': len(cases),
        'stop_reason': 'gateway_budget' if stopped else None,
        'campus_posts': posts, 'campus_debit_including_unknown': tokens,
        'complete_pair_policies': policies, 'all_attempt_cost': summed_cost(all_costs),
        'collection_wall_seconds': monotonic() - started,
    })


def run(args, benchmark, ledger_root):
    benchmark_panel = benchmark / 'panel' / args.stage
    if args.dataset == 'tatqa':
        _metric_type(args.metric_dir)
    public, gold, panel_digest = read_panel(benchmark_panel, args.dataset)
    cases = frozen_cases(public, args.cases)
    serve_path = args.serving_profile or benchmark / 'oda_serving_profile.json'
    serve = json.loads(serve_path.read_text(encoding='utf-8'))
    if serve['model'] != ODA or serve['checkpoint'] != ODA_CHECKPOINT:
        raise ValueError('ODA requires the pinned local serving profile and checkpoint')
    providers = {}
    provider_digest = {}
    for model, custom in zip(MANAGED, (args.qwen_api_profile, args.deepseek_api_profile), strict=True):
        profile_path = custom or benchmark / 'managed_profiles' / f'{model}.json'
        provider_digest[model] = digest_file(profile_path)
        providers[model] = school.read_profile(profile_path, provider_digest[model])
        if providers[model][1]['model_id'] != model:
            raise ValueError(f'managed serving profile differs from {model}')
    key = os.environ.get('BUPT_API_KEY')
    if not key:
        raise ValueError('BUPT_API_KEY must be available in the authorized process environment')

    budget = school.campus.BatchBudget(ledger_root)
    try:
        freeze(ledger_root / 'opening.json', {'project_cap': school.PROJECT_CAP,
                                             'historical_charged_tokens': args.prior_charged_tokens})
        opening_posts, opening_tokens = school.charged(budget.rows)
        budget.posts = opening_posts + args.max_posts
        budget.tokens = min(school.PROJECT_CAP - args.prior_charged_tokens, opening_tokens + args.token_cap)
        if not school.has_gateway_capacity(budget):
            raise ValueError('no shared gateway capacity for timing')
        root = benchmark / args.namespace
        root.mkdir(exist_ok=False, mode=0o700)
        contract = root / 'run.json'
        freeze(contract, {
            'schema': 'finance-live-policy-timing-v1', 'namespace': args.namespace, 'stage': args.stage,
            'dataset': args.dataset, 'panel': panel_digest,
            'case_order': [{'id': row['id'], 'policy_order': order} for row, order in cases],
            'order_seed': ORDER_SEED, 'opencode_sha256': digest_file(args.opencode), 'seed': 17,
            'oda': {'endpoint': args.base, 'model': ODA, 'checkpoint': serve['checkpoint'],
                    'serve_sha256': digest_file(serve_path), 'context': 16384, 'output': 4096, 'temperature': .6},
            'managed': {name: {'profile_sha256': provider_digest[name], **profile}
                        for name, (profile, _) in providers.items()},
            'gateway_batch': {'posts_before': opening_posts, 'tokens_before': opening_tokens,
                              'post_limit': budget.posts, 'token_limit': budget.tokens},
            'measurement': 'Fresh serial request construction, model/relay and public execution with policy '
                           'cost accounting. Official grading follows timing. Receipt reuse disabled.',
        })
        actor = OpenCode(root / 'actors' / 'solve', args.opencode, args.base, ODA, 4096, 16384, .6)
        actor.initialize_session_store()
        wait_service(args.base, ODA, 90)
        collect_cases(args, root, cases, gold, actor, providers, budget, key, digest_file(contract))
    finally:
        budget.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, required=True)
    parser.add_argument('--namespace', required=True)
    parser.add_argument('--stage', choices=('fit', 'calibration'), required=True)
    parser.add_argument('--dataset', choices=('finqa', 'tatqa'), required=True)
    parser.add_argument('--cases', type=int, required=True)
    parser.add_argument('--max-posts', type=int, required=True)
    parser.add_argument('--token-cap', type=int, required=True)
    parser.add_argument('--prior-charged-tokens', type=int, default=school.RECORDED_PRIOR_CHARGE)
    parser.add_argument('--base', type=local_endpoint, default='http://127.0.0.1:18157/v1')
    parser.add_argument('--serving-profile', type=Path)
    parser.add_argument('--qwen-api-profile', type=Path)
    parser.add_argument('--deepseek-api-profile', type=Path)
    parser.add_argument('--metric-dir', type=Path)
    parser.add_argument('--opencode', type=Path, default=Path.home() / '.opencode/bin/opencode')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*', args.namespace):
        parser.error('namespace must be one fresh directory name')
    if (args.max_posts < 1 or args.token_cap < school.campus.REQUEST_TOKEN_CEILING
            or not school.RECORDED_PRIOR_CHARGE <= args.prior_charged_tokens < school.PROJECT_CAP
            or (args.dataset == 'tatqa' and args.metric_dir is None)):
        parser.error('require explicit positive gateway caps and the official TAT-QA metric directory when used')
    private = (Path.home() / 'wzh/research_evidence').resolve()
    benchmark = args.benchmark.resolve()
    if (sys.platform != 'linux' or not benchmark.is_relative_to(private)
            or not re.fullmatch(r'finance_frontier_benchmark_\d{8}_v\d+', benchmark.name)):
        parser.error('timing requires a GB10 finance benchmark workspace')
    args.opencode = args.opencode.resolve()
    run(args, benchmark, private / '.finance_frontier_campus_budget')


if __name__ == '__main__':
    main()
