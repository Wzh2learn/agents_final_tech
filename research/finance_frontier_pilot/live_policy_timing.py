"""Measure fresh, interleaved policy wall time with official grading outside the timer."""

import argparse
import ast
from contextlib import ExitStack
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
from types import SimpleNamespace

from benchmark_actions import action_cost, deliver, digest_file, freeze, grade_case, read_panel, recorded_call, select_case
from frontier_report import BOOTSTRAP_DRAWS, frontier
from paired_tradeoff import contrast
from run_pilot import OpenCode, local_endpoint, paired_prompt, wait_service, write_json
from scoring import _metric_type, public_execution
import school_benchmark as school
from table_scope_replay import public_contract


POLICIES = ('oda-local', 'contract', 'ds-first')
MANAGED = (school.campus.QWEN_MODEL, school.campus.MODEL)
MANAGED_ORDERS = {'qwen-first': MANAGED, 'ds-first': MANAGED[::-1]}
ODA = 'oda-fin-rl-8b'
ODA_CHECKPOINT = '948c22ea48f9bf93e5747f4211657fcad9cb0295'
ORDER_SEED = 20261120
DIRECT_MODELS = dict(zip(('oda-direct', 'qwen-direct', 'deepseek-direct'), (ODA, *MANAGED), strict=True))
MATCHED_POLICIES = ('contract', 'car', 'budgetverify', 'author-cascade', *DIRECT_MODELS, *MANAGED_ORDERS)
COMPACT_POLICIES = ('compact-direct', 'compact-fallback')
OFFICIAL_COUNTS = {'finqa': 1147, 'tatqa': 718}
STRATIFIED_COUNT = 24
STRATIFIED_SEED = 20261126


class TimingBudgetExhausted(Exception):
    """A measured policy could not dispatch its next managed request."""


def validate_full_panel_request(args):
    """A v4 declaration denotes the complete matched, unsharded official panel."""
    if (args.dataset not in OFFICIAL_COUNTS or args.stage != 'eval' or not args.compare_baselines
            or not getattr(args, 'compact_container', None) or args.offset != 0
            or args.cases != OFFICIAL_COUNTS[args.dataset]):
        raise ValueError('full-panel timing requires eval, matched baselines, a compact container, '
                         'zero offset and the complete official question count')


def validate_stratified_panel_request(args):
    if (args.dataset not in OFFICIAL_COUNTS or args.stage != 'eval' or not args.compare_baselines
            or not getattr(args, 'compact_container', None) or args.offset != 0
            or args.cases != STRATIFIED_COUNT):
        raise ValueError('stratified-panel timing requires eval, matched baselines, a compact container, '
                         'zero offset and 24 questions')


def validate_official_panel(benchmark, dataset, public, gold):
    """Bind selected prompts and gold to the pinned, complete official source."""
    from cohorts import read_source

    manifest = json.loads((benchmark / 'panel' / 'manifest.json').read_text(encoding='utf-8'))
    expected_source = manifest['datasets'][dataset]['eval']
    official, source = read_source(dataset, Path(expected_source['path']))
    expected = {row['id']: (row, {k: v for k, v in reference.items() if k != 'question'})
                for row, reference, _ in official}
    if (source != expected_source or len(expected) != OFFICIAL_COUNTS[dataset]
            or len(public) != OFFICIAL_COUNTS[dataset]
            or len({row['id'] for row in public}) != len(public)
            or {row['id'] for row in public} != set(expected)
            or any(row['dataset'] != dataset or row != expected[row['id']][0]
                   or gold.get((dataset, row['id'])) != expected[row['id']][1] for row in public)):
        raise ValueError('full-panel inputs differ from the pinned official source or references')
    return source


def select_policy(row, policy, call):
    """Select only from the public report and newly requested model replies."""
    if policy in DIRECT_MODELS:
        model = DIRECT_MODELS[policy]
        name = 'low' if model == ODA else model
        receipt = call(name, 'solve', paired_prompt(row, 'dsl'))
        reply = deliver(receipt)
        projected, submission, decision, cells = public_contract(
            row, reply, stopped=bool(reply) and receipt['finish'] == ['stop'])
        return {'submission': submission, 'decision': decision, 'source_cells': cells, 'calls': [name],
                'selected_model': model, 'selected_stage': f'compiled_{model}'}, projected
    if policy not in POLICIES and policy not in MANAGED_ORDERS:
        raise ValueError(f'unknown timed policy {policy}')
    calls = []
    if policy not in MANAGED_ORDERS:
        outputs, projections = select_case(row, ['compiled_fallback'], call)
        draft = outputs['compiled_fallback']
        projected = projections.get('compiled_fallback', row)
        calls.extend(draft['calls'])
        trace = public_execution(projected, draft['submission'])
        executable = trace is not None and trace['status'] == 'executed'
        if policy == 'oda-local' or executable or type(draft['submission']['answer']) in (int, float):
            stage = 'compiled_oda' if executable else 'free_oda'
            return {**draft, 'selected_stage': stage, 'selected_model': ODA}, projected

    order = MANAGED_ORDERS.get(policy, MANAGED)
    for model in order:
        receipt = call(model, 'solve', paired_prompt(row, 'dsl'))
        calls.append(model)
        reply = deliver(receipt)
        projected, candidate, decision, cells = public_contract(row, reply, stopped=bool(reply) and receipt['finish'] == ['stop'])
        if public_execution(projected, candidate)['status'] == 'executed':
            break
    return {'submission': candidate, 'decision': decision, 'source_cells': cells, 'calls': calls,
            'selected_stage': f'compiled_{model}', 'selected_model': model}, projected


def select_compact_policy(row, policy, call, model):
    """Use the compiled compact output, escalating only when it cannot execute."""
    if policy not in COMPACT_POLICIES:
        raise ValueError(f'unknown compact timed policy {policy}')
    role = policy.replace('-', '_')
    outputs, projections = select_case(
        row, ['contract_compile'], lambda name, unused_role, prompt: call('compact', role, prompt))
    selected = {**outputs['contract_compile'], 'calls': ['compact'],
                'selected_model': model, 'selected_stage': 'compiled_compact'}
    projected = projections.get('contract_compile', row)
    if policy == 'compact-direct' or public_execution(projected, selected['submission'])['status'] == 'executed':
        return selected, projected
    fallback, projected = select_policy(row, 'ds-first', call)
    return {**fallback, 'calls': ['compact', *fallback['calls']]}, projected


def frozen_cases(rows, count, policies=POLICIES, offset=0):
    if not 0 <= offset < len(rows) or not 1 <= count <= len(rows) - offset:
        raise ValueError('timing offset and size must be within the selected panel')
    key = lambda row: sha256(f'{ORDER_SEED}|{row["dataset"]}|{row["id"]}'.encode()).hexdigest()
    rng = Random(ORDER_SEED)
    if len(policies) == 3:
        orders = list(permutations(policies))
        rng.shuffle(orders)
    else:
        order = list(policies)
        rng.shuffle(order)
        n = len(order)
        positions = [0]
        for i in range(1, n):
            positions.append((i + 1) // 2 if i % 2 else n - i // 2)
        orders = [tuple(order[(position + shift) % n] for position in positions) for shift in range(n)]
        if n % 2:
            orders.extend([tuple(reversed(sequence)) for sequence in orders])
    sample = sorted(rows, key=key)[offset:offset + count]
    return [(row, orders[(offset + i) % len(orders)]) for i, row in enumerate(sample)]


def reference_depth(dataset, reference):
    """Coarse reference-operation count for sampling, independent of model outputs."""
    if dataset == 'finqa':
        steps = (reference.get('program') or '').count('(')
    else:
        derivation = reference.get('derivation')
        if not isinstance(derivation, str) or not derivation.strip():
            return 'unknown'
        # Treat formatting symbols as annotations on numbers. Parse syntax only.
        normalized = derivation.translate(str.maketrans('−–×÷％', '--*/%'))
        normalized = re.sub(r'(?<=\d),(?=\d{3}(?:\D|$))', '', normalized).replace('%', '').strip()
        try:
            nodes = list(ast.walk(ast.parse(normalized, mode='eval')))
        except SyntaxError:
            return 'unknown'
        if any(not isinstance(node, (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
                                     ast.operator, ast.unaryop)) or
               isinstance(node, ast.Constant) and type(node.value) not in (int, float)
               for node in nodes):
            return 'unknown'
        steps = sum(isinstance(node, ast.BinOp) for node in nodes)
    return 'single' if steps == 1 else 'multi' if steps > 1 else 'unknown'


def stratified_cases(public, gold, dataset, policies=(*MATCHED_POLICIES, *COMPACT_POLICIES)):
    """Freeze 24 official questions before any timed inference on these cases."""
    if len(public) < STRATIFIED_COUNT:
        raise ValueError('stratified timing requires at least 24 eligible questions')
    by_depth = {}
    for row in public:
        depth = reference_depth(dataset, gold[dataset, row['id']])
        by_depth.setdefault(depth, []).append(row)

    strata = {}
    for depth, rows in sorted(by_depth.items()):
        ordered = sorted(rows, key=lambda row: (len(paired_prompt(row, 'dsl')), row['id']))
        middle = (len(ordered) + 1) // 2
        strata[f'{depth}-short'] = ordered[:middle]
        if middle < len(ordered):
            strata[f'{depth}-long'] = ordered[middle:]

    # Guarantee one observation in each nonempty stratum, then fill the largest
    # proportional allocation deficits while respecting finite stratum sizes.
    counts = dict.fromkeys(strata, 1)
    for _ in range(STRATIFIED_COUNT - len(strata)):
        eligible = (name for name, rows in strata.items() if counts[name] < len(rows))
        name = max(eligible, key=lambda name: (
            STRATIFIED_COUNT * len(strata[name]) - counts[name] * len(public), name))
        counts[name] += 1

    selected, stratum_by_id = [], {}
    for name, rows in strata.items():
        ranked = sorted(rows, key=lambda row: (
            sha256(f'{STRATIFIED_SEED}|{dataset}|{row["id"]}'.encode()).digest(), row['id']))
        for row in ranked[:counts[name]]:
            selected.append(row)
            stratum_by_id[row['id']] = name
    cases = frozen_cases(selected, STRATIFIED_COUNT, policies)
    sampling = {
        'seed': STRATIFIED_SEED,
        'method': 'Within each reference-depth group, rank by input length and split into halves. '
                  'Allocate near-proportionally with at least one per nonempty stratum, '
                  'then select by fixed SHA-256 rank.',
        'length_metric': 'Character length of the public DSL prompt, with question ID as length tie-break.',
        'depth_metric': ('FinQA official program operation count.' if dataset == 'finqa' else
                         'TAT-QA reference derivation binary operation count after normalizing numeric notation. '
                         'Unparsed expressions and expressions without binary operations have unknown depth.'),
        'population_n': len(public),
        'sample_n': len(cases),
        'strata': {name: {'population_n': len(rows), 'sample_n': counts[name]} for name, rows in strata.items()},
        'stratum_by_id': stratum_by_id,
    }
    return cases, sampling


def summed_cost(costs):
    known = sum(item['known_tokens'] for item in costs)
    unknown = sum(item['unknown_usage_calls'] for item in costs)
    return {'calls': sum(item['calls'] for item in costs), 'known_tokens': known,
            'unknown_usage_calls': unknown, 'total_tokens': None if unknown else known,
            'summed_call_seconds': sum(item['summed_call_seconds'] for item in costs)}


def paired_online_wall(pair_records, reports, proposed='contract'):
    """Compare measured response-path wall time on the same complete questions."""
    if proposed not in pair_records:
        return {}
    ids = list(reports)
    outcomes = {
        name: {ident: SimpleNamespace(strict=entry['result']['strict'], executable=entry['result']['executable'],
                                     wall_seconds=entry['wall_seconds'])
               for ident, entry in zip(ids, records, strict=True)} for name, records in pair_records.items()
    }

    def wall_delta(proposed, baseline):
        return proposed.wall_seconds - baseline.wall_seconds

    return {name: {metric: contrast(outcomes[proposed], baseline, ids, reports, 'mean_online_wall_seconds_delta',
                                    wall_delta, BOOTSTRAP_DRAWS, 0, require_execution)
                   for metric, require_execution in (('strict', False), ('strict_and_executable', True))}
            for name, baseline in outcomes.items() if name != proposed}


def collect_cases(args, root, cases, gold, actors, profiles, budget, key, run_digest, selectors=None):
    completed = 0
    started = monotonic()
    start_index = len(budget.rows)
    stopped = False
    paired_policies = tuple(selectors) if selectors is not None else POLICIES
    pair_records = {name: [] for name in paired_policies}
    reports = {}
    all_costs = []
    with (root / 'outcomes.jsonl').open('x', encoding='utf-8') as stream:
        for row, order in cases:
            ident = sha256(row['id'].encode()).hexdigest()[:24]
            measured = {}
            for policy in order:
                receipts = {}

                def call(name, role, prompt):
                    target = root / 'calls' / ident / policy / name
                    if role not in actors or (name in profiles and role != 'solve') or target.exists() or name in receipts:
                        raise ValueError('live timing expects independent fresh calls to a configured role')
                    if name in profiles:
                        if not school.has_gateway_capacity(budget):
                            raise TimingBudgetExhausted
                        profile, gateway = profiles[name]
                        result = school.fresh_managed_call(target, args.opencode, run_digest, prompt,
                                                           key=key, budget=budget, profile=profile, gateway=gateway)
                        receipt_path = target / 'provider_receipt.json'
                    else:
                        result = recorded_call(actors[role], prompt, target, run_digest)
                        receipt_path = target / 'call.json'
                    fields = ('usage', 'elapsed_seconds', 'exit_code', 'finish', 'errors', 'provider_posts')
                    receipts[name] = {**{item: result[item] for item in fields if item in result},
                                      'path': receipt_path.relative_to(root).as_posix()}
                    if (getattr(args, 'compare_baselines', False) and name not in profiles
                            and (result['exit_code'] or result['errors'])):
                        model = actors[role].model.removeprefix('pilot/') if name == 'compact' else ODA
                        wait_service(args.base, model, 10)
                    return result

                begin = monotonic()
                try:
                    selected, projection = (select_policy(row, policy, call) if selectors is None
                                            else selectors[policy](row, call))
                    if selected['calls'] != list(receipts):
                        raise ValueError('selected call order and metered calls disagree')
                    public_execution(projection, selected['submission'])
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
            reports[row['id']] = row['report']
            for name, record in measured.items():
                pair_records[name].append(record)
            completed += 1

    policies = {}
    for name, records in pair_records.items():
        durations = [record['wall_seconds'] for record in records]
        p90 = quantiles(durations, n=10, method='inclusive')[-1] if len(durations) > 1 else next(iter(durations), None)
        policies[name] = {'n': len(records), 'correct': sum(record['result']['strict'] for record in records),
                          'strict_and_executable': sum(record['result']['strict'] and record['result']['executable']
                                                       for record in records),
                          'summed_wall_seconds': sum(durations),
                          'mean_wall_seconds': sum(durations) / len(durations) if durations else None,
                          'median_wall_seconds': median(durations) if durations else None, 'p90_wall_seconds': p90,
                          'cost': summed_cost([record['cost'] for record in records])}
    posts, tokens = school.charged(budget.rows[start_index:])
    summary = {
        'complete_paired_questions': completed, 'planned_questions': len(cases),
        'stop_reason': 'gateway_budget' if stopped else None,
        'campus_posts': posts, 'campus_debit_including_unknown': tokens,
        'complete_pair_policies': policies, 'all_attempt_cost': summed_cost(all_costs),
        'strict_wall_frontier': frontier(policies, 'mean_wall_seconds'),
        'strict_and_executable_wall_frontier': frontier(policies, 'mean_wall_seconds', 'strict_and_executable'),
        'paired_online_wall': {
            'proposed': 'contract',
            'scope': 'Fresh measured wall, using complete paired questions even when token usage is missing.',
            'interval_method': 'Report-cluster bootstrap with simultaneous 95% coverage of each contrast’s two axes. '
                               'Intervals are per comparison and describe the timed block.',
            'comparisons': paired_online_wall(pair_records, reports),
        },
        'collection_wall_seconds': monotonic() - started,
    }
    if 'compact-fallback' in pair_records:
        summary['compact_paired_online_wall'] = {
            'proposed': 'compact-fallback',
            'scope': 'Fresh measured wall, using complete paired questions even when token usage is missing.',
            'interval_method': summary['paired_online_wall']['interval_method'],
            'comparisons': paired_online_wall(pair_records, reports, 'compact-fallback'),
        }
    write_json(root / 'collection.json', summary)


def run(args, benchmark, ledger_root):
    benchmark_panel = benchmark / 'panel' / args.stage
    full_panel = getattr(args, 'full_panel', False)
    stratified_panel = getattr(args, 'stratified_panel', False)
    if full_panel and stratified_panel:
        raise ValueError('full-panel and stratified-panel timing are mutually exclusive')
    official_panel = full_panel or stratified_panel
    if official_panel:
        if full_panel:
            validate_full_panel_request(args)
        else:
            validate_stratified_panel_request(args)
        public, gold, panel_digest = read_panel(benchmark_panel, args.dataset)
        official_source = validate_official_panel(benchmark, args.dataset, public, gold)
        if stratified_panel:
            cases, sampling = stratified_cases(public, gold, args.dataset)
    if args.dataset == 'tatqa':
        _metric_type(args.metric_dir)
    serve_path = args.serving_profile or benchmark / 'oda_serving_profile.json'
    serve = json.loads(serve_path.read_text(encoding='utf-8'))
    if serve['model'] != ODA or serve['checkpoint'] != ODA_CHECKPOINT:
        raise ValueError('ODA requires the pinned local serving profile and checkpoint')
    compact_profile = None
    if getattr(args, 'compact_container', None):
        from compact_eval import BASE as COMPACT_BASE, timed_compact_profile

        if official_panel:
            compact_profile = timed_compact_profile(benchmark, args.compact_container, args.dataset, expanded=True)
        else:
            compact_profile = timed_compact_profile(benchmark, args.compact_container, args.dataset)
        if (args.base != COMPACT_BASE or compact_profile.get('base_checkpoint') != ODA_CHECKPOINT
                or not compact_profile.get('model') or not compact_profile.get('checkpoint')):
            raise ValueError('Compact timing requires a verified ODA adapter profile')
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
    with ExitStack() as resources:
        resources.callback(budget.close)
        freeze(ledger_root / 'opening.json', {'project_cap': school.PROJECT_CAP,
                                             'historical_charged_tokens': args.prior_charged_tokens})
        opening_posts, opening_tokens = school.charged(budget.rows)
        budget.posts = opening_posts + args.max_posts
        budget.tokens = min(school.PROJECT_CAP - args.prior_charged_tokens, opening_tokens + args.token_cap)
        if not school.has_gateway_capacity(budget):
            raise ValueError('no shared gateway capacity for timing')
        selectors, baseline_metadata = None, {}
        roles = ('solve',)
        if args.compare_baselines:
            from live_author_cascade import load_isolated_author_cascade
            from live_local_baselines import load_local_baselines

            local, local_metadata = load_local_baselines(args, benchmark, serve_path)
            author, author_metadata = resources.enter_context(load_isolated_author_cascade(
                args, benchmark, serve_path, ledger_root / 'gateway_ledger.json'))
            selector_by_name = {**local, 'author-cascade': author}
            for name in ('contract', *DIRECT_MODELS, *MANAGED_ORDERS):
                selector_by_name[name] = lambda row, call, policy=name: select_policy(row, policy, call)
            policy_names = MATCHED_POLICIES
            if compact_profile is not None:
                for name in COMPACT_POLICIES:
                    selector_by_name[name] = lambda row, call, policy=name: select_compact_policy(
                        row, policy, call, compact_profile['model'])
                policy_names = (*MATCHED_POLICIES, *COMPACT_POLICIES)
            selectors = {name: selector_by_name[name] for name in policy_names}
            baseline_metadata = {**local_metadata, 'author-cascade': author_metadata,
                                 'direct_reference': 'One compiled response from the indicated model.',
                                 'managed_nonexecution_orders': MANAGED_ORDERS}
            roles = ('solve', 'verify', 'probe', 'repair')
        if not official_panel:
            public, gold, panel_digest = read_panel(benchmark_panel, args.dataset)
        if not stratified_panel:
            cases = frozen_cases(public, args.cases, tuple(selectors) if selectors else POLICIES, args.offset)
        root = benchmark / args.namespace
        root.mkdir(exist_ok=False, mode=0o700)
        contract = root / 'run.json'
        contract_data = {
            'schema': ('finance-live-policy-timing-stratified-v1' if stratified_panel else
                       'finance-live-policy-timing-v4' if full_panel else
                       'finance-live-policy-timing-v3' if compact_profile is not None else
                       'finance-live-policy-timing-v2' if selectors else 'finance-live-policy-timing-v1'),
            'namespace': args.namespace, 'stage': args.stage, 'case_offset': args.offset,
            'dataset': args.dataset, 'panel': panel_digest,
            'case_order': [{'id': row['id'], 'policy_order': order} for row, order in cases],
            'order_seed': ORDER_SEED, 'opencode_sha256': digest_file(args.opencode), 'seed': 17,
            'oda': {'endpoint': args.base, 'model': ODA, 'checkpoint': serve['checkpoint'],
                    'serve_sha256': digest_file(serve_path), 'context': 16384, 'output': 4096, 'temperature': .6},
            'local_role_outputs': {role: 4096 for role in roles}, 'baseline_policies': baseline_metadata,
            'managed': {name: {'profile_sha256': provider_digest[name], **profile}
                        for name, (profile, _) in providers.items()},
            'gateway_batch': {'posts_before': opening_posts, 'tokens_before': opening_tokens,
                              'post_limit': budget.posts, 'token_limit': budget.tokens},
            'measurement': 'Fresh serial request construction, model/relay and public execution with policy '
                           'cost accounting. Official grading follows timing. Receipt reuse disabled.',
        }
        if full_panel:
            contract_data.update(full_official_panel=True, official_source=official_source,
                                 full_panel_completion='Check collection.json for completed paired questions.')
        if stratified_panel:
            contract_data.update(full_official_panel=False, official_source=official_source,
                                 stratified_sampling=sampling)
        if compact_profile is not None:
            contract_data['compact_oda'] = {'endpoint': args.base, 'profile': compact_profile,
                                            'context': 16384, 'output': 4096, 'temperature': .6,
                                            'chat_template_kwargs': {'enable_thinking': False},
                                            'fallback': 'Nonexecution only; DeepSeek then Qwen.'}
        freeze(contract, contract_data)
        actors = {role: OpenCode(root / 'actors' / role, args.opencode, args.base, ODA, 4096, 16384, .6) for role in roles}
        if compact_profile is not None:
            for role in ('compact_direct', 'compact_fallback'):
                actors[role] = OpenCode(root / 'actors' / role, args.opencode, args.base,
                                        compact_profile['model'], 4096, 16384, .6, disable_thinking=True)
        for actor in actors.values():
            actor.initialize_session_store()
        wait_service(args.base, ODA, 90)
        if compact_profile is not None:
            wait_service(args.base, compact_profile['model'], 90)
        collect_cases(args, root, cases, gold, actors, providers, budget, key, digest_file(contract), selectors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, required=True)
    parser.add_argument('--namespace', required=True)
    parser.add_argument('--stage', choices=('fit', 'calibration', 'eval'), required=True)
    parser.add_argument('--dataset', choices=('finqa', 'tatqa'), required=True)
    parser.add_argument('--cases', type=int, required=True)
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--max-posts', type=int, required=True)
    parser.add_argument('--token-cap', type=int, required=True)
    parser.add_argument('--prior-charged-tokens', type=int, default=school.RECORDED_PRIOR_CHARGE)
    parser.add_argument('--base', type=local_endpoint, default='http://127.0.0.1:18157/v1')
    parser.add_argument('--serving-profile', type=Path)
    parser.add_argument('--qwen-api-profile', type=Path)
    parser.add_argument('--deepseek-api-profile', type=Path)
    parser.add_argument('--metric-dir', type=Path)
    parser.add_argument('--compare-baselines', action='store_true')
    panel_group = parser.add_mutually_exclusive_group()
    panel_group.add_argument('--full-panel', action='store_true',
                             help='Measure the complete official eval panel with the expanded compact profile')
    panel_group.add_argument('--stratified-panel', action='store_true',
                             help='Measure 24 stratified official eval questions with the expanded compact profile')
    parser.add_argument('--compact-container', help='Verified running Docker container ID for optional compact policies')
    parser.add_argument('--upstream', type=Path)
    parser.add_argument('--author-deps', dest='author_dependency_path', type=Path)
    parser.add_argument('--tabfm-checkpoint', type=Path)
    parser.add_argument('--opencode', type=Path, default=Path.home() / '.opencode/bin/opencode')
    args = parser.parse_args()
    if args.full_panel or args.stratified_panel:
        try:
            if args.full_panel:
                validate_full_panel_request(args)
            else:
                validate_stratified_panel_request(args)
        except ValueError as exc:
            parser.error(str(exc))
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*', args.namespace):
        parser.error('namespace must be one fresh directory name')
    if (args.max_posts < 1 or args.token_cap < school.campus.REQUEST_TOKEN_CEILING
            or not school.RECORDED_PRIOR_CHARGE <= args.prior_charged_tokens < school.PROJECT_CAP
            or (args.dataset == 'tatqa' and args.metric_dir is None)):
        parser.error('require explicit positive gateway caps and the official TAT-QA metric directory when used')
    if args.compare_baselines != (args.stage == 'eval'):
        parser.error('the matched baseline batch requires the official eval panel and frozen training policies')
    if args.compact_container and (args.stage != 'eval' or not args.compare_baselines
                                   or not re.fullmatch(r'[0-9a-f]{12,64}', args.compact_container)):
        parser.error('compact policies require --stage eval --compare-baselines and a Docker container ID')
    if args.compare_baselines and (args.upstream is None or not args.upstream.is_dir()):
        parser.error('the matched baseline batch requires the pinned author Cascade checkout')
    if args.compare_baselines and (args.author_dependency_path is None or not args.author_dependency_path.is_dir()):
        parser.error('the matched baseline batch requires isolated author Cascade dependencies')
    private = (Path.home() / 'wzh/research_evidence').resolve()
    benchmark = args.benchmark.resolve()
    if (sys.platform != 'linux' or not benchmark.is_relative_to(private)
            or not re.fullmatch(r'finance_frontier_benchmark_\d{8}_v\d+', benchmark.name)):
        parser.error('timing requires a GB10 finance benchmark workspace')
    args.opencode = args.opencode.resolve()
    run(args, benchmark, private / '.finance_frontier_campus_budget')


if __name__ == '__main__':
    main()
