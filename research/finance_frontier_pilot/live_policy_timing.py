"""Measure fresh, interleaved policy wall time with official grading outside the timer."""

import argparse
import ast
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import ExitStack, nullcontext
from copy import copy
from hashlib import sha256
from itertools import permutations
import json
import os
from pathlib import Path
from random import Random
import re
from statistics import median, quantiles
import subprocess
import sys
from threading import Lock
from time import monotonic
from types import SimpleNamespace

from benchmark_actions import action_cost, deliver, digest_file, freeze, grade_case, read_panel, recorded_call, select_case
from frontier_report import BOOTSTRAP_DRAWS, frontier
from paired_tradeoff import contrast
from run_pilot import OpenCode, local_endpoint, paired_prompt, wait_service, write_json
from scoring import _metric_type, finqa_ratio_rule, public_execution
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
JOINT_N, JOINT_RATE, JOINT_SEED = 4, .2, 20261127
JOINT_POLICIES = ('joint-compact', 'deepseek-direct', 'car-compiled', 'budgetverify-gbm-compiled',
                  'budgetverify-tabfm-compiled', 'author-cascade', *MANAGED_ORDERS)
JOINT_LAMBDAS = {'finqa': (.8, .8), 'tatqa': (.65, 0.)}
JOINT_WAVE_PLAN = 'finance-live-joint-timing-wave-plan-v1'
JOINT_WAVE_SHARD = 'finance-live-joint-timing-wave-shard-v1'
JOINT_STEADY_PLAN = 'finance-live-joint-timing-steady-plan-v1'
JOINT_STEADY_SHARD = 'finance-live-joint-timing-steady-shard-v1'
JOINT_STEADY_FULL = 'finance-live-joint-timing-steady-full-v1'
JOINT_STEADY_WORKERS = (4, 6, 8)
ISOLATED_ACTOR_STORE = 'per-role-per-block-slot-xdg-v1'
LEGACY_SERIAL_DRIVERS = {
    '427de38a89e70075940a4e1dc79f6cb27fd03e177d121ae78d1bcd4bc6c200b4',
    '8a9cbec1f2d5e1ee368b783dec372d2cf863414d71a3d9f10f7f636ef636a55a',
}


class TimingBudgetExhausted(Exception):
    """A measured policy could not dispatch its next managed request."""


class TimingLocalStorageLocked(Exception):
    """OpenCode exited on a local SQLite lock without emitting a model event."""


class TimingLocalActorCrash(Exception):
    """The local actor was killed by a signal without emitting a model event."""


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


def compiled_baseline(native, role):
    def select(row, call):
        receipts = {}

        def capture(name, actor, prompt):
            receipt = call(name, actor, prompt)
            receipts[name] = receipt
            return receipt

        selected, projection = native(row, capture)
        if role == 'car' and selected['decision'] == 'edited':
            candidate = selected['submission']
            revised = finqa_ratio_rule(row, candidate, public_execution(row, candidate))
            if revised is not None and public_execution(row, revised)['status'] == 'executed':
                selected = {**selected, 'submission': revised}
        else:
            winner = {'use_new': 'high_solve', 'revise': 'mid', 'reformat': 'mid'}.get(selected['decision'], 'low')
            receipt = receipts[winner]
            reply = deliver(receipt)
            projection, candidate, stage, cells = public_contract(
                row, reply, stopped=bool(reply) and receipt['finish'] == ['stop'])
            selected = {**selected, 'submission': candidate, 'compiler_stage': stage, 'source_cells': cells}
        return selected, projection

    return select


def serialized_predictor(selector):
    """Protect shared predictor/IPC state but release the lock during model calls."""
    lock = Lock()

    def select(row, call):
        def inference(*args):
            lock.release()
            try:
                return call(*args)
            finally:
                lock.acquire()

        with lock:
            return selector(row, inference)

    return select


def joint_selectors(args, benchmark, serve_path, providers, resources, ledger_root):
    from live_author_cascade import load_isolated_author_cascade
    from live_local_baselines import load_local_baselines

    gbm_args = copy(args)
    gbm_args.tabfm_checkpoint = None
    gbm, gbm_info = load_local_baselines(gbm_args, benchmark, serve_path)
    tabfm, tabfm_info = load_local_baselines(args, benchmark, serve_path)
    actual = tuple(info['budgetverify']['policy']['lambda'] for info in (gbm_info, tabfm_info))
    if actual != JOINT_LAMBDAS[args.dataset]:
        raise ValueError(f'BudgetVerify TRAIN-selected points changed: {actual}')
    author, author_meta = resources.enter_context(load_isolated_author_cascade(
        args, benchmark, serve_path, ledger_root / 'gateway_ledger.json'))
    selectors = {
        'joint-compact': None,
        'deepseek-direct': None,
        'car-compiled': compiled_baseline(gbm['car'], 'car'),
        'budgetverify-gbm-compiled': compiled_baseline(gbm['budgetverify'], 'budgetverify'),
        'budgetverify-tabfm-compiled': compiled_baseline(tabfm['budgetverify'], 'budgetverify'),
        'author-cascade': author,
    }
    selectors.update((name, lambda row, call, policy=name: select_policy(row, policy, call)) for name in MANAGED_ORDERS)
    if getattr(args, 'joint_workers', 1) > 1:
        for name in ('budgetverify-gbm-compiled', 'budgetverify-tabfm-compiled', 'author-cascade'):
            selectors[name] = serialized_predictor(selectors[name])
    if tuple(selectors) != JOINT_POLICIES:
        raise ValueError('Unexpected joint timing roster')
    return selectors, {'car-compiled': gbm_info['car'], 'budgetverify-gbm-compiled': gbm_info['budgetverify'],
                       'budgetverify-tabfm-compiled': tabfm_info['budgetverify'], 'author-cascade': author_meta,
                       'managed_nonexecution_orders': MANAGED_ORDERS,
                       'managed_profiles': {name: profile for name, (profile, _) in providers.items()}}


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


def joint_wave_cases(rows, block_size):
    """Use the original public question order and rotate policies by whole block."""
    ordered = frozen_cases(rows, len(rows), JOINT_POLICIES)
    return [(row, ordered[index // block_size][1]) for index, (row, _) in enumerate(ordered)]


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


def select_joint(row, arm, call, receipts, directory, run_digest, joint):
    from compact_consensus import compact_prompt
    from compact_frontier import route_case
    from live_compact_teacher import local_call, local_selection, teacher_selection

    policy, profile, config, seed_by_id = joint
    if arm == 'joint-compact':
        salt = sha256(f'{run_digest}:{row["id"]}'.encode()).hexdigest()
        path = directory / 'compact_call.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        started = monotonic()
        try:
            local = local_call(config, profile, row, seed_by_id[row['id']], salt)
        except (OSError, ValueError) as error:
            write_json(directory / 'compact_failure.json', {'status': 'uncertified_native_request',
                       'error_type': type(error).__name__, 'http_status': getattr(error, 'code', None),
                       'elapsed_seconds': monotonic() - started, 'usage': None})
            raise
        write_json(path, local)
        usage = school.measured_usage(local['usage']) if local['usage'] is not None else None
        receipts['compact'] = {'usage': usage, 'elapsed_seconds': local['model_wall_seconds'],
                               'path': Path('calls', directory.parent.name, directory.name, path.name).as_posix()}
        selected, projection = local_selection(row, local, rerank=getattr(config, 'rerank', False))
        selected.update(selected_model=profile['model'], selected_stage='joint_compact')
        if not route_case(local, policy, config.rate):
            return {**selected, 'calls': list(receipts)}, projection
    else:
        selected, projection = None, row
    teacher = school.campus.MODEL
    receipt = call(teacher, 'solve', compact_prompt(row, planned=profile['planned']))
    candidate, teacher_projection, executable = teacher_selection(row, receipt)
    if selected is None or executable:
        selected, projection = {**candidate, 'selected_model': teacher, 'selected_stage': 'joint_teacher'}, teacher_projection
    return {**selected, 'calls': list(receipts)}, projection


def local_startup_failure(target, result):
    exit_code = result['exit_code']
    if (type(exit_code) is not int or not (exit_code == 1 or exit_code < 0)
            or result['finish'] or result['usage'] is not None):
        return None
    raw = target / 'raw.jsonl'
    if not raw.is_file() or raw.stat().st_size != 0:
        return None
    if exit_code < 0:
        return TimingLocalActorCrash
    stderr = target / 'stderr.txt'
    if stderr.is_file() and 'database is locked' in stderr.read_text(encoding='utf-8', errors='replace').casefold():
        return TimingLocalStorageLocked
    return None


def measure_route(args, root, row, policy, actors, profiles, budget, key, run_digest, selectors, joint,
                  *, admitted=None, campus_lock=None):
    ident = sha256(row['id'].encode()).hexdigest()[:24]
    directory = root / 'calls' / ident / policy
    receipts = {}

    def call(name, role, prompt):
        target = directory / name
        if role not in actors or (name in profiles and role != 'solve') or target.exists() or name in receipts:
            raise ValueError('live timing expects independent fresh calls to a configured role')
        if name in profiles:
            with campus_lock if campus_lock is not None else nullcontext():
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
        if campus_lock is not None and name not in profiles:
            startup_failure = local_startup_failure(target, result)
            if startup_failure is not None:
                raise startup_failure
        if (getattr(args, 'compare_baselines', False) and name not in profiles
                and (result['exit_code'] or result['errors'])):
            model = actors[role].model.removeprefix('pilot/') if name == 'compact' else ODA
            wait_service(args.base, model, 10)
        return result

    begin = monotonic() if admitted is None else admitted
    status, failure, selected, projection = 'complete', None, None, None
    try:
        if joint is not None and policy in ('joint-compact', 'deepseek-direct'):
            selected, projection = select_joint(row, policy, call, receipts, directory, run_digest, joint)
        else:
            selected, projection = (select_policy(row, policy, call) if selectors is None
                                    else selectors[policy](row, call))
        if selected['calls'] != list(receipts):
            raise ValueError('selected call order and metered calls disagree')
        public_execution(projection, selected['submission'])
    except TimingBudgetExhausted:
        status = 'incomplete_budget'
    except Exception as error:
        if campus_lock is None:
            raise
        status, failure = 'incomplete_error', type(error).__name__
    cost = action_cost(list(receipts.values()))
    measured = {'status': status, 'wall_seconds': monotonic() - begin, 'calls': receipts, 'cost': cost}
    if failure is not None:
        measured['failure_type'] = failure
    if campus_lock is not None:
        measured['local_call_cost'] = action_cost([receipt for name, receipt in receipts.items() if name not in profiles])
        measured['campus_call_cost'] = action_cost([receipt for name, receipt in receipts.items() if name in profiles])
    return measured, selected, projection


def grade_timed_route(args, row, gold, measure):
    record, selected, projection = measure
    if record['status'] == 'complete':
        record['result'] = grade_case(row, gold[row['dataset'], row['id']], {'selected': selected},
                                      {'selected': projection}, args.metric_dir)['selected']
    return record


def steady_arm(pool, block, policy, measure, workers, campus_lock):
    """Refill only the actor slot whose prior route has returned."""
    admission = Lock()
    pending, results = {}, {}
    failed = False
    rows = iter(enumerate(block))

    def execute(row, slot, admitted):
        nonlocal failed
        try:
            item = measure(row, policy, admitted=admitted, campus_lock=campus_lock, actor_slot=slot)
        except Exception as error:
            cost = action_cost([])
            item = ({'status': 'incomplete_error', 'failure_type': type(error).__name__, 'calls': {}, 'cost': cost,
                     'local_call_cost': cost, 'campus_call_cost': cost, 'wall_seconds': monotonic() - admitted},
                    None, None)
        if item[0]['status'] != 'complete':
            with admission:
                failed = True
        item[0]['actor_slot'] = slot
        return item

    def submit(slot):
        with admission:
            next_row = None if failed else next(rows, None)
            if next_row is not None:
                index, (row, _) = next_row
                pending[pool.submit(execute, row, slot, monotonic())] = index, slot

    for slot in range(min(workers, len(block))):
        submit(slot)
    while pending:
        done, _ = wait(pending, return_when=FIRST_COMPLETED)
        for future in sorted(done, key=pending.__getitem__):
            index, slot = pending.pop(future)
            results[index] = future.result()
            submit(slot)
    return results


def wave_reports(args, cases, gold, measure, workers, offset, *, steady_block=None):
    """Yield complete blocks in frozen order and preserve the entire failed block."""
    campus_lock = Lock()
    block_width = steady_block or workers
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for start in range(0, len(cases), block_width):
            block = cases[start:start + block_width]
            order = block[0][1]
            if any(arm_order != order for _, arm_order in block):
                raise ValueError('Every route in a timing wave must use the same frozen arm order')
            records = [{} for _ in block]
            batches, stop = {}, None
            for policy in order:
                batch_start = monotonic()
                if steady_block is not None:
                    measured = steady_arm(pool, block, policy, measure, workers, campus_lock)
                else:
                    futures = [pool.submit(measure, row, policy, admitted=monotonic(), campus_lock=campus_lock,
                                           actor_slot=slot)
                               for slot, (row, _) in enumerate(block)]
                    measured = {i: future.result() for i, future in enumerate(futures)}
                batch_wall = monotonic() - batch_start
                for index, item in sorted(measured.items()):
                    row = block[index][0]
                    try:
                        records[index][policy] = grade_timed_route(args, row, gold, item)
                    except Exception as error:
                        records[index][policy] = {**item[0], 'status': 'incomplete_error',
                                                  'failure_type': type(error).__name__}
                items = [record[policy] for record in records if policy in record]
                statuses = {item['status'] for item in items}
                batches[policy] = {'wall_seconds': batch_wall, 'attempted_routes': len(items),
                                   'complete_routes': sum(item['status'] == 'complete' for item in items),
                                   'local_call_cost': summed_cost([item['local_call_cost'] for item in items]),
                                   'campus_call_cost': summed_cost([item['campus_call_cost'] for item in items])}
                if statuses != {'complete'}:
                    stop = 'route_error' if 'incomplete_error' in statuses else 'gateway_budget'
                    break
            index = (offset + start) // block_width
            for slot, ((row, _), record) in enumerate(zip(block, records, strict=True)):
                report = {k: row[k] for k in ('dataset', 'id', 'report')}
                report.update(policy_order=order, policies=record, complete_pair=stop is None, block_index=index,
                              block_size=len(block), block_slot=slot)
                if slot == 0:
                    report['arm_batches'] = batches
                yield report, stop
            if stop is not None:
                return


def serial_reports(args, cases, gold, measure):
    for row, order in cases:
        records = {}
        stop = None
        for policy in order:
            record = grade_timed_route(args, row, gold, measure(row, policy))
            records[policy] = record
            if record['status'] == 'incomplete_budget':
                stop = 'gateway_budget'
                break
        report = {k: row[k] for k in ('dataset', 'id', 'report')}
        yield {**report, 'policy_order': order, 'policies': records, 'complete_pair': stop is None}, stop
        if stop is not None:
            return


def collect_cases(args, root, cases, gold, actors, profiles, budget, key, run_digest, selectors=None, joint=None,
                  *, joint_offset=0, actor_slots=None):
    completed = 0
    started = monotonic()
    start_index = len(budget.rows)
    stop = None
    paired_policies = tuple(selectors) if selectors is not None else POLICIES
    pair_records = {name: [] for name in paired_policies}
    reports = {}
    all_costs, accepted_rows = [], []
    workers = getattr(args, 'joint_workers', 1)
    steady_block = getattr(args, 'joint_steady_block', None)
    if actor_slots is not None and (workers <= 1 or len(actor_slots) != workers):
        raise ValueError('Isolated actor stores must match the wave width')
    if steady_block is not None and (steady_block != 32 or workers not in JOINT_STEADY_WORKERS or actor_slots is None):
        raise ValueError('Steady timing requires 32-question blocks and four, six, or eight isolated actor slots')
    if steady_block is None and not 1 <= workers <= 4:
        raise ValueError('Non-steady timing supports at most four workers')

    def measure(row, policy, *, actor_slot=0, **kwargs):
        selected_actors = actors if actor_slots is None else actor_slots[actor_slot]
        return measure_route(args, root, row, policy, selected_actors, profiles, budget, key, run_digest, selectors, joint,
                             **kwargs)

    produced = (wave_reports(args, cases, gold, measure, workers, joint_offset, steady_block=steady_block) if workers > 1
                else serial_reports(args, cases, gold, measure))
    with (root / 'outcomes.jsonl').open('x', encoding='utf-8') as stream:
        for report, stop in produced:
            measured = report['policies']
            stream.write(json.dumps(report, ensure_ascii=False, allow_nan=False) + '\n')
            stream.flush()
            all_costs.extend(record['cost'] for record in measured.values())
            if not report['complete_pair']:
                continue
            reports[report['id']] = report['report']
            if workers > 1:
                accepted_rows.append(report)
            for name, record in measured.items():
                pair_records[name].append(record)
            completed += 1

    policies = summarize_timed_policies(pair_records)
    posts, tokens = school.charged(budget.rows[start_index:])
    proposed = 'joint-compact' if joint is not None else 'contract'
    summary = {
        'complete_paired_questions': completed, 'planned_questions': len(cases),
        'stop_reason': stop,
        'campus_posts': posts, 'campus_debit_including_unknown': tokens,
        'complete_pair_policies': policies, 'all_attempt_cost': summed_cost(all_costs),
        'strict_wall_frontier': frontier(policies, 'mean_wall_seconds'),
        'strict_and_executable_wall_frontier': frontier(policies, 'mean_wall_seconds', 'strict_and_executable'),
        'paired_online_wall': {
            'proposed': proposed,
            'scope': 'Fresh measured wall, using complete paired questions even when token usage is missing.',
            'interval_method': 'Report-cluster bootstrap with simultaneous 95% coverage of each contrast’s two axes. '
                               'Intervals are per comparison and describe the timed block.',
            'comparisons': paired_online_wall(pair_records, reports, proposed),
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
    if workers > 1:
        summary.update(joint_workers=workers, block_size_strata=wave_strata(accepted_rows, paired_policies))
    if steady_block is not None:
        summary['joint_steady_block'] = steady_block
    write_json(root / 'collection.json', summary)
    if stop == 'route_error':
        raise RuntimeError('A timing wave failed; inspect its recorded route attempts')


def summarize_timed_policies(pair_records):
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
    return policies


def wave_strata(rows, policies):
    strata = {}
    for size in sorted({row['block_size'] for row in rows}):
        cohort = [row for row in rows if row['block_size'] == size]
        batches = [row['arm_batches'] for row in cohort if row['block_slot'] == 0]
        times = {name: [batch[name]['wall_seconds'] for batch in batches] for name in policies}
        records = {name: [row['policies'][name] for row in cohort] for name in policies}
        strata[str(size)] = {
            'questions': len(cohort), 'blocks': len(batches), 'complete_pair_policies': summarize_timed_policies(records),
            'arms': {name: {'summed_batch_wall_seconds': sum(times[name]),
                            'median_batch_wall_seconds': median(times[name]),
                            'local_call_cost': summed_cost([batch[name]['local_call_cost'] for batch in batches]),
                            'campus_call_cost': summed_cost([batch[name]['campus_call_cost'] for batch in batches])}
                     for name in policies},
        }
    return strata


def check_joint_serving(args, baseline, compact):
    """Require the exact live container and the same admitted base model settings."""
    template = '\n'.join('{{json .' + field + '}}' for field in ('Image', 'Config.Cmd', 'Mounts', 'State.Running'))
    image, argv, mounts, running = map(json.loads, subprocess.check_output(
        ['docker', 'inspect', '--format', template, args.compact_container], text=True).splitlines())
    mounts = sorted(({key: item[key] for key in ('Source', 'Destination', 'RW')} for item in mounts),
                    key=lambda item: item['Destination'])
    if not running or (image, argv, mounts) != (compact['image'], compact['argv'], compact['mounts']):
        raise ValueError('Joint timing requires the frozen compact LoRA serving profile on the live container')
    keys = ('--dtype', '--max-model-len', '--max-num-seqs', '--max-num-batched-tokens',
            '--served-model-name', '--reasoning-parser', '--port')
    old = baseline['argv']
    if (baseline['image'] != image or old[:3] != argv[:3]
            or any(old[old.index(key) + 1] != argv[argv.index(key) + 1] for key in keys)
            or any((flag in old) != (flag in argv) for flag in ('--enable-prefix-caching', '--enforce-eager'))):
        raise ValueError('Joint and original baseline base-engine settings differ')
    model_path = argv[2]
    model_mount = lambda entries: [(item['Source'], item['RW']) for item in entries if item['Destination'] == model_path]
    if not model_mount(mounts) or model_mount(mounts) != model_mount(baseline['mounts']):
        raise ValueError('Both timing arms must share the pinned ODA base-model mount')


def joint_block_width(plan):
    workers = plan.get('joint_workers', 1)
    steady = plan.get('joint_steady_block')
    if steady is not None or plan.get('schema') == JOINT_STEADY_PLAN:
        if (plan.get('schema') != JOINT_STEADY_PLAN or type(steady) is not int or steady != 32
                or type(workers) is not int or workers not in JOINT_STEADY_WORKERS
                or plan.get('actor_store_scope') != ISOLATED_ACTOR_STORE
                or plan.get('local_selection') != 'confidence-rerank-v1'):
            raise ValueError('A steady plan requires 32-question blocks, four, six, or eight isolated actor slots, and frozen selection')
    elif type(workers) is not int or not 1 <= workers <= 4:
        raise ValueError('A non-steady plan supports at most four workers')
    return steady or workers


def joint_history(shards, plan, plan_hash):
    """Return the exact completed prefix; keep failed/partial attempts on disk."""
    accepted, attempts = [], sorted(shards.iterdir())
    target = plan['case_order']
    workers = plan.get('joint_workers', 1)
    width = joint_block_width(plan)
    steady = plan.get('joint_steady_block')
    schema = (JOINT_STEADY_SHARD if steady is not None else
              JOINT_WAVE_SHARD if workers > 1 else 'finance-live-joint-timing-shard-v1')
    if steady is not None:
        for start in range(0, len(target), width):
            order = target[start]['policy_order']
            if (len(order) != len(JOINT_POLICIES) or set(order) != set(JOINT_POLICIES)
                    or any(item['policy_order'] != order for item in target[start:start + width])):
                raise ValueError('A steady plan must run the same full arm order throughout each block')
    for number, path in enumerate(attempts):
        if not path.is_dir() or path.name != f'{number:05d}':
            raise ValueError('Unexpected attempt directory in the immutable joint timing namespace')
        contract_path, outcomes_path = path / 'run.json', path / 'outcomes.jsonl'
        if not contract_path.exists() and not outcomes_path.exists():
            continue
        contract = json.loads(contract_path.read_text(encoding='utf-8'))
        start, order = len(accepted), contract['case_order']
        if (contract['schema'] != schema or contract['joint_plan_sha256'] != plan_hash
                or contract['case_offset'] != start or not order or order != target[start:start + len(order)]):
            raise ValueError('Joint shard must be a contiguous attempt on the next frozen question IDs')
        if workers > 1 and (contract.get('joint_workers') != workers or start % width
                            or contract.get('joint_steady_block') != steady
                            or (steady is not None and contract.get('local_selection') != plan['local_selection'])
                            or contract.get('actor_store_scope') != plan.get('actor_store_scope')
                            or (len(order) % width and start + len(order) != len(target))):
            raise ValueError('A wave shard must use the frozen actor stores, width and complete blocks')
        if not outcomes_path.is_file():
            continue
        failed_block = None
        buffer = []
        with outcomes_path.open(encoding='utf-8') as stream:
            for index, line in enumerate(stream):
                if not line.endswith('\n'):
                    break  # A process killed while writing has not published this row.
                row = json.loads(line)
                if (index >= len(order) or row['dataset'] != plan['dataset']
                        or row['id'] != order[index]['id'] or row['report'] != order[index]['report']
                        or row['policy_order'] != order[index]['policy_order']
                        or type(row['complete_pair']) is not bool):
                    raise ValueError('Joint shard recorded an unexpected or duplicate timing row')
                block, slot = divmod(start + index, width)
                size = min(width, len(target) - block * width)
                if workers > 1 and ((row['block_index'], row['block_slot'], row['block_size']) != (block, slot, size)
                                    or (slot == 0) != ('arm_batches' in row)):
                    raise ValueError('A wave timing row has invalid block metadata')
                if failed_block is not None and (failed_block != block or row['complete_pair']):
                    raise ValueError('No completed routes or later blocks can follow a failed block')
                if not row['complete_pair']:
                    if buffer:
                        raise ValueError('A wave must mark all rows of a failed block incomplete')
                    failed_block = block
                    continue
                if (set(row['policies']) != set(JOINT_POLICIES)
                        or any(item['status'] != 'complete' for item in row['policies'].values())):
                    raise ValueError('A completed joint pair must contain every completed fresh route')
                if steady is not None and any(type(item.get('actor_slot')) is not int
                                              or not 0 <= item['actor_slot'] < workers
                                              for item in row['policies'].values()):
                    raise ValueError('A completed steady route must identify its admitted actor slot')
                for item in row['policies'].values():
                    paths = [(path / receipt['path']).resolve() for receipt in item['calls'].values()]
                    if not paths or any(not receipt.is_relative_to(path.resolve()) or not receipt.is_file()
                                        for receipt in paths):
                        raise ValueError('A completed joint pair must retain all of its own new receipts')
                if workers > 1 and slot == 0 and set(row['arm_batches']) != set(JOINT_POLICIES):
                    raise ValueError('A completed wave requires timing evidence for every arm')
                if steady is not None and slot == 0 and any(
                        item['attempted_routes'] != size or item['complete_routes'] != size
                        for item in row['arm_batches'].values()):
                    raise ValueError('A completed steady block must measure every planned route in each arm')
                buffer.append(row)
                if len(buffer) == size:
                    accepted.extend(buffer)
                    buffer.clear()
    return accepted, len(attempts)


def joint_shard(args, benchmark, resources, plan, cases):
    import fcntl

    root = benchmark / args.namespace
    root.mkdir(mode=0o700, exist_ok=True)
    guard = resources.enter_context((root / '.joint-timing.lock').open('a'))
    fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
    plan_path, shards = root / 'joint_plan.json', root / 'shards'
    if not plan_path.exists() and any(item != '.joint-timing.lock' for item in os.listdir(root)):
        raise ValueError('Joint timing requires a dedicated namespace')
    plan = json.loads(json.dumps(plan, ensure_ascii=False, allow_nan=False))
    workers = plan.get('joint_workers', 1)
    width = joint_block_width(plan)
    if workers == 1 and plan_path.is_file():
        previous = json.loads(plan_path.read_text(encoding='utf-8'))
        old_driver = previous.get('driver_sha256', {}).get('live_policy_timing.py')
        if previous.get('schema') == 'finance-live-joint-timing-plan-v1' and old_driver in LEGACY_SERIAL_DRIVERS:
            # Preserve exact legacy plan bytes while recording the executing driver in each new shard.
            plan['driver_sha256']['live_policy_timing.py'] = old_driver
    freeze(plan_path, plan)
    plan_hash = digest_file(plan_path)
    shards.mkdir(mode=0o700, exist_ok=True)
    accepted, next_attempt = joint_history(shards, plan, plan_hash)
    start = len(accepted)
    if args.offset is not None and args.offset != start:
        raise ValueError(f'Next joint timing offset is {start}, not {args.offset}')
    if start == len(cases):
        publish_joint_progress(root, plan, plan_hash)
        return None, [], start, plan_hash
    end = min(start + args.cases, len(cases))
    if width > 1 and end < len(cases):
        end -= end % width
        if end <= start:
            raise ValueError('Joint wave shard size must fit the next complete block')
    shard = shards / f'{next_attempt:05d}'
    shard.mkdir(mode=0o700, exist_ok=False)
    return shard, cases[start:end], start, plan_hash


def publish_joint_progress(root, plan, plan_hash):
    rows, attempts = joint_history(root / 'shards', plan, plan_hash)
    total = len(plan['case_order'])
    progress = {'planned_questions': total, 'complete_paired_questions': len(rows), 'attempts': attempts,
                'next_offset': len(rows), 'joint_plan_sha256': plan_hash}
    write_json(root / 'progress.json', progress)
    if len(rows) == total:
        records = {name: [row['policies'][name] for row in rows] for name in JOINT_POLICIES}
        reports = {row['id']: row['report'] for row in rows}
        policies = summarize_timed_policies(records)
        collection = {**progress, 'schema': 'finance-live-joint-timing-full-v1',
               'dataset': plan['dataset'], 'panel': plan['panel'], 'measurement': plan['measurement'],
               'complete_pair_policies': policies, 'strict_wall_frontier': frontier(policies, 'mean_wall_seconds'),
               'strict_and_executable_wall_frontier': frontier(policies, 'mean_wall_seconds', 'strict_and_executable'),
               'paired_online_wall': paired_online_wall(records, reports, 'joint-compact')}
        if plan.get('joint_workers', 1) > 1:
            collection.update(schema='finance-live-joint-timing-wave-full-v1', joint_workers=plan['joint_workers'],
                              block_size_strata=wave_strata(rows, JOINT_POLICIES))
        if 'joint_steady_block' in plan:
            collection.update(schema=JOINT_STEADY_FULL, joint_steady_block=plan['joint_steady_block'],
                              local_selection=plan['local_selection'])
        freeze(root / 'collection.json', collection)


def initialized_actors(root, args, roles):
    actors = {role: OpenCode(root / role, args.opencode, args.base, ODA, 4096, 16384, .6) for role in roles}
    for actor in actors.values():
        actor.initialize_session_store()
    return actors


def run(args, benchmark, ledger_root):
    benchmark_panel = benchmark / 'panel' / args.stage
    full_panel = getattr(args, 'full_panel', False)
    stratified_panel = getattr(args, 'stratified_panel', False)
    joint_path = getattr(args, 'joint_gate', None)
    if full_panel and stratified_panel:
        raise ValueError('full-panel and stratified-panel timing are mutually exclusive')
    official_panel = full_panel or stratified_panel or joint_path is not None
    joint = None
    if joint_path is not None:
        all_public, gold, panel_digest = read_panel(benchmark_panel, None)
        public = [row for row in all_public if row['dataset'] == args.dataset]
        official_source = validate_official_panel(benchmark, args.dataset, public, gold)
        seed_by_id = {row['id']: JOINT_SEED + index * 8 for index, row in enumerate(all_public)
                      if row['dataset'] == args.dataset}
    elif official_panel:
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
    if joint_path is not None:
        from live_compact_teacher import gate_profile

        policy = json.loads(joint_path.read_text(encoding='utf-8'))
        compact_serve = json.loads(args.joint_serving_profile.read_text(encoding='utf-8'))
        check_joint_serving(args, serve, compact_serve)
        gate = gate_profile(policy, compact_serve, digest_file(args.joint_serving_profile), JOINT_N, JOINT_RATE)
        driver = Path(__file__).resolve().parent
        files = ('live_policy_timing.py', 'live_compact_teacher.py', 'compact_consensus.py', 'compact_frontier.py',
                 'benchmark_actions.py', 'table_scope_replay.py', 'scoring.py', 'school_benchmark.py',
                 'live_local_baselines.py', 'live_author_cascade.py', 'budget_policy.py', 'car_adapter.py')
        driver_hashes = {name: digest_file(driver / name) for name in files}
        if gate['compiler_sha256'] != driver_hashes['table_scope_replay.py'] or gate['scorer_sha256'] != driver_hashes['scoring.py']:
            raise ValueError('Joint timing compiler and scorer must match the frozen gate')
        config = SimpleNamespace(base=args.base, n=JOINT_N, rate=JOINT_RATE, timeout=120,
                                 rerank=bool(getattr(args, 'joint_steady_block', None)))
        joint = policy, gate, config, seed_by_id
    elif getattr(args, 'compact_container', None):
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
        if joint is not None:
            selectors, baseline_metadata = joint_selectors(args, benchmark, serve_path, providers, resources, ledger_root)
            roles = ('solve', 'verify', 'probe', 'repair')
        elif args.compare_baselines:
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
        if joint is not None:
            # The shared provider ledger grows between attempts; the fitted input digests remain fixed.
            author_ledger_observed = baseline_metadata['author-cascade'].pop('campus_ledger_sha256')
            workers = getattr(args, 'joint_workers', 1)
            isolated = getattr(args, 'joint_isolated_actor_slots', False)
            steady = getattr(args, 'joint_steady_block', None)
            cases = (joint_wave_cases(public, steady or workers) if workers > 1
                     else frozen_cases(public, len(public), JOINT_POLICIES))
            plan = {
                'schema': 'finance-live-joint-timing-plan-v1', 'dataset': args.dataset, 'panel': panel_digest,
                'official_source': official_source, 'case_order': [{'id': row['id'], 'policy_order': list(order),
                              'report': row['report']} for row, order in cases],
                'policies': list(JOINT_POLICIES), 'ordering_seed': ORDER_SEED, 'local_seed': JOINT_SEED,
                'gate_n': JOINT_N, 'gate_rate': JOINT_RATE, 'gate_sha256': digest_file(joint_path),
                'baseline_serving_sha256': digest_file(serve_path),
                'serving_sha256': digest_file(args.joint_serving_profile),
                'opencode_sha256': digest_file(args.opencode), 'driver_sha256': driver_hashes,
                'managed_profile_sha256': provider_digest, 'baseline_policies': baseline_metadata,
                'endpoint': args.base, 'local_role_outputs': {role: 4096 for role in roles},
                'official_metric_sha256': ({path.name: digest_file(path) for path in sorted(args.metric_dir.glob('tatqa_*.py'))}
                                           if args.metric_dir is not None else None),
                'measurement': 'Real fresh serial route wall time from dispatch through public compile/execution. '
                               'Balanced policy order on the same pinned profiles. Grading follows timing.',
                'author_rng_scope': 'The author worker starts at its fixed post-fit random state in every shard.',
            }
            if workers > 1:
                plan.update(schema=JOINT_WAVE_PLAN, joint_workers=workers,
                            measurement='Fresh wall from per-route admission through terminal public execution, '
                                        'including the shared gateway queue. Same-arm requests run concurrently '
                                        'within each frozen question block. Grading follows timing.',
                            block_order='Balanced policy orders rotate by block index. A failed block is retried '
                                        'at its original size and question IDs. The final remainder is reported separately.',
                            author_rng_scope='The author worker starts at its fixed post-fit random state in each '
                                             'shard. Exchanges are serialized in the order reached by admitted routes.')
            actor_profile = {'actor_store_scope': ISOLATED_ACTOR_STORE} if isolated else {}
            plan.update(actor_profile)
            steady_profile = ({'joint_steady_block': steady, 'local_selection': 'confidence-rerank-v1'}
                              if steady is not None else {})
            if steady is not None:
                slots = {4: 'Four', 6: 'Six', 8: 'Eight'}[workers]
                plan.update(schema=JOINT_STEADY_PLAN, **steady_profile,
                            measurement='Fresh wall from each route admission through terminal public execution, '
                                        f'including gateway wait. {slots} isolated slots are refilled within a 32-question '
                                        'same-arm block. No overlap between arms. Grading follows timing.',
                            block_order='Balanced policy orders rotate by frozen block index. Only complete blocks '
                                        'advance the prefix; the true final remainder is reported separately.')
            shard, todo, start, plan_hash = joint_shard(args, benchmark, resources, plan, cases)
            if shard is None:
                return
            contract = shard / 'run.json'
            shard_schema = (JOINT_STEADY_SHARD if steady is not None else
                            JOINT_WAVE_SHARD if workers > 1 else 'finance-live-joint-timing-shard-v1')
            freeze(contract, {'schema': shard_schema,
                              'joint_plan_sha256': plan_hash,
                              'case_offset': start, 'case_order': plan['case_order'][start:start + len(todo)],
                              'joint_workers': workers, 'executed_timing_driver_sha256': driver_hashes['live_policy_timing.py'],
                              'author_observed_campus_ledger_sha256': author_ledger_observed,
                              **actor_profile, **steady_profile,
                              'gateway_batch': {'posts_before': opening_posts, 'tokens_before': opening_tokens,
                                                'post_limit': budget.posts, 'token_limit': budget.tokens}})
            if isolated:
                actor_slots = tuple(initialized_actors(shard / 'actors' / f'slot-{slot}', args, roles)
                                    for slot in range(workers))
                actors = actor_slots[0]
            else:
                actor_slots = None
                actors = initialized_actors(shard / 'actors', args, roles)
            try:
                wait_service(args.base, ODA, 90)
                wait_service(args.base, joint[1]['model'], 90)
                collect_cases(args, shard, todo, gold, actors, providers, budget, key,
                              digest_file(contract), selectors, joint, joint_offset=start, actor_slots=actor_slots)
            finally:
                publish_joint_progress(benchmark / args.namespace, plan, plan_hash)
            return
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
    parser.add_argument('--offset', type=int, help='Legacy slice offset or exact expected joint resume offset')
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
    panel_group.add_argument('--joint-gate', type=Path,
                             help='Measure a bounded shard of the frozen full official joint/strong-baseline comparison')
    parser.add_argument('--joint-serving-profile', type=Path,
                        help='Recorded base and joint LoRA configuration of the admitted live container')
    parser.add_argument('--joint-workers', type=int, choices=(1, 2, 3, *JOINT_STEADY_WORKERS), default=1,
                        help='Joint-only same-arm concurrency (default 1, serial; above 4 requires steady timing)')
    parser.add_argument('--joint-isolated-actor-slots', action='store_true',
                        help='Preinitialize one OpenCode store per local role and concurrent block slot')
    parser.add_argument('--joint-steady-block', type=int, choices=(32,),
                        help='Refill four, six, or eight isolated slots within each frozen 32-question same-arm block')
    parser.add_argument('--compact-container', help='Verified running Docker container ID for optional compact policies')
    parser.add_argument('--upstream', type=Path)
    parser.add_argument('--author-deps', dest='author_dependency_path', type=Path)
    parser.add_argument('--tabfm-checkpoint', type=Path)
    parser.add_argument('--opencode', type=Path, default=Path.home() / '.opencode/bin/opencode')
    args = parser.parse_args()
    if args.joint_workers > 1 and not args.joint_gate:
        parser.error('--joint-workers above one requires --joint-gate')
    if args.joint_isolated_actor_slots and (not args.joint_gate or args.joint_workers <= 1):
        parser.error('--joint-isolated-actor-slots requires --joint-gate and --joint-workers above one')
    if args.joint_steady_block is not None and (not args.joint_gate or args.joint_workers not in JOINT_STEADY_WORKERS
                                                or not args.joint_isolated_actor_slots):
        parser.error('--joint-steady-block requires --joint-gate, --joint-workers 4, 6, or 8 and --joint-isolated-actor-slots')
    if args.joint_workers > 4 and args.joint_steady_block is None:
        parser.error('--joint-workers above 4 requires --joint-steady-block 32 and isolated actor slots')
    if args.joint_gate:
        if (args.stage != 'eval' or not args.compare_baselines or not args.compact_container
                or not args.joint_serving_profile or not args.tabfm_checkpoint or args.cases < 1
                or (args.offset is not None and args.offset < 0)):
            parser.error('Joint timing requires official eval, a compact container/profile, a TabFM checkpoint and a positive shard size')
    elif args.joint_serving_profile:
        parser.error('--joint-serving-profile requires --joint-gate')
    elif args.offset is None:
        args.offset = 0
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
