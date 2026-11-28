"""Replay matched-cost confidence-only routing from accepted native joint timing."""

from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import NamedTuple

import benchmark_actions
import compact_consensus
import compact_frontier
import live_compact_teacher
import live_policy_timing
import school_benchmark
import scoring
import table_scope_replay
from benchmark_actions import action_cost, digest_file, grade_case, read_panel
from compact_consensus import api_usage, compact_prompt, compact_request, evaluate_choices
from compact_frontier import compare, risk, route_case
from live_compact_teacher import confidence_priority, gate_profile, local_selection, teacher_selection
from live_policy_timing import JOINT_N, JOINT_POLICIES, JOINT_RATE, JOINT_SEED, OFFICIAL_COUNTS, joint_history


TEACHER = school_benchmark.campus.MODEL
DRIVERS = (benchmark_actions, compact_consensus, compact_frontier, live_compact_teacher,
           live_policy_timing, school_benchmark, scoring, table_scope_replay)


class Teacher(NamedTuple):
    correct: bool
    executable: bool
    tokens: int | None
    posts: int


class Case(NamedTuple):
    risk: tuple
    local_correct: bool
    local_tokens: int | None
    routed: bool
    teacher: Teacher


def read(path: Path):
    return json.loads(path.read_bytes())


def require(condition, message: str) -> None:
    if not condition:
        raise ValueError(message)


def ordered_hash(values) -> str:
    return sha256(json.dumps(values, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def accepted_prefix(namespace, dataset, panel, official, gate_hash, serving_hash, profile_hash, metric, pins, partial):
    plan_path = namespace / 'joint_plan.json'
    plan = read(plan_path)
    binding = digest_file(plan_path)
    expected = OFFICIAL_COUNTS[dataset]
    require(plan['dataset'] == dataset and plan['panel'] == panel and plan['official_source'] == official
            and len(plan['case_order']) == expected and tuple(plan['policies']) == JOINT_POLICIES
            and plan['schema'] == live_policy_timing.JOINT_STEADY_PLAN
            and plan['local_selection'] == 'confidence-rerank-v1'
            and plan['gate_n'] == JOINT_N and plan['gate_rate'] == JOINT_RATE and plan['local_seed'] == JOINT_SEED
            and plan['gate_sha256'] == gate_hash and plan['serving_sha256'] == serving_hash
            and plan['managed_profile_sha256'][TEACHER] == profile_hash
            and plan['official_metric_sha256'] == metric
            and all(plan['driver_sha256'].get(name) == value for name, value in pins.items()),
            f'{namespace}: incompatible official panel, native driver, serving, metric or gate')
    accepted, attempts = joint_history(namespace / 'shards', plan, binding)
    count = len(accepted)
    require(count and (partial or count == expected),
            f'{namespace}: {count}/{expected} accepted pairs; full replay requires {expected}')
    progress = read(namespace / 'progress.json')
    require(progress['joint_plan_sha256'] == binding and progress['complete_paired_questions'] == count
            and progress['planned_questions'] == expected and progress['next_offset'] == count,
            f'{namespace}: unpublished or changing accepted prefix')
    if count == expected:
        full = read(namespace / 'collection.json')
        require(full['joint_plan_sha256'] == binding and full['complete_paired_questions'] == expected,
                f'{namespace}: missing complete collection receipt')

    # The shared validator returns rows, not their attempt directories. Trace
    # accepted records back to the exact source without taking an aborted row.
    remaining = {row['id']: row for row in accepted}
    require(len(remaining) == count, f'{namespace}: duplicate accepted question')
    locations, sources = {}, {}
    for shard in sorted((namespace / 'shards').iterdir()):
        outcomes = shard / 'outcomes.jsonl'
        if not outcomes.is_file():
            continue
        located = False
        with outcomes.open(encoding='utf-8') as stream:
            for line in stream:
                if not line.endswith('\n'):
                    break
                row = json.loads(line)
                ident = row['id']
                if remaining.get(ident) == row:
                    locations[ident] = shard
                    del remaining[ident]
                    located = True
        if located:
            contract = read(shard / 'run.json')
            require(contract['executed_timing_driver_sha256'] == pins['live_policy_timing.py'],
                    f'{shard}: recorded executed timing driver differs')
            sources[shard.name] = {name: digest_file(shard / name) for name in ('run.json', 'outcomes.jsonl')}
    require(not remaining, f'{namespace}: accepted record lost its source shard')
    return plan, accepted, locations, {
        'plan_sha256': binding, 'progress_sha256': digest_file(namespace / 'progress.json'),
        'accepted_attempts': attempts, 'shards': sources,
    }


def call_path(shard: Path, ident: str, arm: str, entry, filename: str) -> Path:
    directory = sha256(ident.encode()).hexdigest()[:24]
    relative = Path('calls', directory, arm, filename)
    expected = (shard / relative).resolve()
    require(Path(entry['path']) == relative and expected.is_relative_to(shard.resolve()),
            f'{ident}: {arm} receipt does not bind to this question and shard')
    return expected


def load_teacher(shard, row, gold, arm, entry, prompt, run_hash, metric_dir, ledger, seen):
    path = call_path(shard, row['id'], arm, entry, f'{TEACHER}/provider_receipt.json')
    saved = read(path)
    original = path.with_name('call.json')
    value = saved['metered_result']
    provider = value['provider']
    request = {'actor': 'solve', 'run_contract': run_hash, 'prompt_sha256': sha256(prompt.encode()).hexdigest()}
    require(saved['run_contract'] == run_hash and saved['opencode_call_sha256'] == digest_file(original)
            and read(path.with_name('request.json')) == request
            and path.with_name('prompt.txt').read_bytes() == (prompt + '\n').encode(),
            f'{row["id"]}: {arm} teacher prompt or OpenCode binding differs')
    unmetered = read(original)
    require(value['opencode_usage'] == unmetered['usage']
            and all(value[k] == unmetered[k] for k in ('text', 'finish', 'exit_code', 'elapsed_seconds'))
            and all(value[k] == entry[k] for k in ('usage', 'finish', 'exit_code', 'elapsed_seconds', 'provider_posts')),
            f'{row["id"]}: {arm} native call fields differ from its timing receipt')

    if provider is None:
        expected_tokens, posts = 0, 0
    else:
        index = provider['index']
        require(type(index) is int and 1 <= index <= len(ledger) and index not in seen
                and provider == ledger[index - 1] and provider['model'] == TEACHER,
                f'{row["id"]}: {arm} missing, reused or mismatched provider ledger row')
        seen.add(index)
        posts = school_benchmark.charged([provider])[0]
        if provider['state'] == 'complete':
            meter = api_usage({'usage': provider['usage']})
            require(meter is not None and value['usage'] == school_benchmark.measured_usage(meter),
                    f'{row["id"]}: {arm} provider usage does not reconcile')
            expected_tokens = meter['total_tokens']
        else:
            expected_tokens = 0 if provider['state'] == 'not_sent' else None
    usage = value['usage']
    require((usage['total'] if usage is not None else None) == expected_tokens
            and value['provider_posts'] == posts,
            f'{row["id"]}: {arm} lost or imputed provider usage')
    action, projection, executable = teacher_selection(row, value)
    grade = grade_case(row, gold, {'teacher': action}, {'teacher': projection}, metric_dir)['teacher']
    require(grade['executable'] == executable, f'{row["id"]}: {arm} teacher execution changed')
    return Teacher(grade['strict'] and executable, executable, expected_tokens, posts), grade, digest_file(path)


def verify_route(arm, grade, ident):
    require(arm['cost'] == action_cost(list(arm['calls'].values()))
            and all(arm['result'][key] == grade[key] for key in ('strict', 'executable', 'submission', 'decision')),
            f'{ident}: recorded fresh route differs from reconstructed score or usage')


def read_case(historical, row, gold, shard, run_hash, gate, profile, seed, metric_dir, ledger, seen):
    ident = row['id']
    joint = historical['policies']['joint-compact']
    direct = historical['policies']['deepseek-direct']
    native_call = joint['calls']['compact']
    path = call_path(shard, ident, 'joint-compact', native_call, 'compact_call.json')
    native = read(path)
    prompt = compact_prompt(row, planned=profile['planned'])
    expected = compact_request(prompt, profile['model'], n=JOINT_N, max_tokens=profile['max_tokens'],
                               temperature=profile['temperature'], seed=seed,
                               cache_salt=sha256(f'{run_hash}:{ident}'.encode()).hexdigest())
    usage = api_usage(native['response'])
    require(native['id'] == ident and native['n'] == JOINT_N and native['transport'] == 'vllm_chat_nonstream'
            and native['request'] == expected and native['usage'] == usage
            and native_call['usage'] == (school_benchmark.measured_usage(usage) if usage is not None else None)
            and native_call['elapsed_seconds'] == native['model_wall_seconds']
            and native['decision'] == evaluate_choices(row, native['response'], JOINT_N),
            f'{ident}: local choices, generation request or meter changed')
    action, projection = local_selection(row, native, rerank=True)
    grade = grade_case(row, gold, {'local': action}, {'local': projection}, metric_dir)['local']
    local_correct = grade['strict'] and grade['executable']
    routed = route_case(native, gate, JOINT_RATE)
    require(set(joint['calls']) == ({'compact', TEACHER} if routed else {'compact'})
            and set(direct['calls']) == {TEACHER}, f'{ident}: frozen gate and fresh dispatch differ')

    teacher, remote_grade, direct_hash = load_teacher(
        shard, row, gold, 'deepseek-direct', direct['calls'][TEACHER], prompt, run_hash, metric_dir, ledger, seen)
    verify_route(direct, remote_grade, ident)
    routed_hash = None
    if routed:
        teacher, remote_grade, routed_hash = load_teacher(
            shard, row, gold, 'joint-compact', joint['calls'][TEACHER], prompt, run_hash, metric_dir, ledger, seen)
        if teacher.executable:
            grade = remote_grade
    verify_route(joint, grade, ident)
    local_tokens = usage['total_tokens'] if usage is not None else None
    case = Case(risk(native), local_correct, local_tokens, routed, teacher)
    return case, [digest_file(path), direct_hash, routed_hash]


def cap_prefix(order, budget: int, cases):
    used = 0
    for i, key in enumerate(order):
        next_cost = cases[key].teacher.tokens
        if used + next_cost > budget:
            return order[:i], used, next_cost
        used += next_cost
    return order, used, None


def replay(order, cases, local):
    chosen = set(order)
    return {key: (item.teacher.correct if key in chosen and item.teacher.executable else local[key])
            for key, item in cases.items()}


def scope_stats(order, cases, local_tokens, local_unknown):
    prices = [cases[key].teacher.tokens for key in order]
    unknown = sum(item is None for item in prices)
    known = sum(item for item in prices if item is not None)
    return {'teacher_routes': len(order), 'teacher_provider_posts': sum(cases[k].teacher.posts for k in order),
            'known_teacher_tokens': known, 'unknown_teacher_usage_routes': unknown,
            'total_known_tokens': local_tokens + known,
            'total_tokens': None if unknown or local_unknown else local_tokens + known,
            'selected_ids_sha256': ordered_hash(order)}


def summarize(cases, reports, public_order, draws: int):
    agree = sorted((key for key in cases if cases[key].routed),
                   key=lambda key: (cases[key].risk, public_order[key]))
    prio = lambda key: confidence_priority(key, {'risk': cases[key].risk})
    rank_only = sorted(cases, key=prio)[:len(agree)]
    local = {key: item.local_correct for key, item in cases.items()}
    local_known = sum(item.local_tokens for item in cases.values() if item.local_tokens is not None)
    local_unknown = sum(item.local_tokens is None for item in cases.values())
    orders = {'consensus': agree, 'risk': rank_only}

    def grouped(chosen, outputs):
        stats = {'arms': {}, 'paired_consensus_minus_risk': compare(outputs['consensus'], outputs['risk'], reports, draws)}
        for name, keys in chosen.items():
            stats['arms'][name] = {
                **scope_stats(keys, cases, local_known, local_unknown),
                'strict_executable_correct': sum(outputs[name].values()),
            }
        return stats

    equal = grouped(orders, {name: replay(order, cases, local) for name, order in orders.items()})
    result = {'n': len(cases), 'local': {'strict_executable_correct': sum(local.values()),
              'known_tokens': local_known, 'unknown_usage_questions': local_unknown},
              'equal_k': equal}
    if local_unknown or any(x['unknown_teacher_usage_routes'] for x in equal['arms'].values()):
        result['same_token_cap'] = {'status': 'unavailable_missing_usage'}
        return result

    target = min(x['known_teacher_tokens'] for x in equal['arms'].values())
    prefixes = {name: cap_prefix(order, target, cases) for name, order in orders.items()}
    applied = {name: prefix[0] for name, prefix in prefixes.items()}
    common = grouped(applied, {name: replay(order, cases, local) for name, order in applied.items()})
    common.update(status='complete', common_teacher_token_cap=target,
                  common_total_token_cap=target + local_known)
    for name, (_, used, next_cost) in prefixes.items():
        arm = common['arms'][name]
        require(arm['known_teacher_tokens'] == used, 'Token cap prefix accounting differs')
        arm.update(unused_cap=target - used, next_recorded_teacher_tokens=next_cost)
    result['same_token_cap'] = common
    return result


def run(args):
    benchmark = args.benchmark.resolve()
    panel_dir = benchmark / 'panel/eval'
    public, gold, panel = read_panel(panel_dir, None)
    public_order = {(row['dataset'], row['id']): i for i, row in enumerate(public)}
    gate, serving = read(args.gate), read(args.serving_profile)
    serving_hash, gate_hash = digest_file(args.serving_profile), digest_file(args.gate)
    profile = gate_profile(gate, serving, serving_hash, JOINT_N, JOINT_RATE)
    driver = {Path(module.__file__).name: digest_file(Path(module.__file__)) for module in DRIVERS}
    require(profile['compiler_sha256'] == driver['table_scope_replay.py']
            and profile['scorer_sha256'] == driver['scoring.py'], 'Frozen gateway compiler/scorer mismatch')
    provider_path = benchmark / 'managed_profiles' / f'{TEACHER}.json'
    provider_hash = digest_file(provider_path)
    _, managed = school_benchmark.read_profile(provider_path, provider_hash)
    require(managed['model_id'] == TEACHER, 'Teacher profile mismatch')
    ledger_path = args.ledger or benchmark.parent / '.finance_frontier_campus_budget/gateway_ledger.json'
    ledger = read(ledger_path)
    require(isinstance(ledger, list), 'Expected the authoritative campus ledger rows')
    metric = {path.name: digest_file(path) for path in sorted(args.metric_dir.glob('tatqa_*.py'))}
    require(metric, 'Expected the native TAT-QA metric dependencies')

    report = {
        'schema': 'finance-joint-native-risk-matched-cost-v1',
        'scope': 'full_official',
        'comparison': 'Counterfactual routing over a shared pool of observed same-prompt teacher replies. '
                      'Use the actually routed managed reply where present and the fresh direct reply elsewhere. '
                      'Each selected route has its recorded logical local/teacher token use.',
        'cost_contract': 'Within each dataset use the smaller teacher token total from the equal-call arms. '
                         'Keep only leading prefixes and use identical local draws. Budget equality is a common '
                         'cap; undispatchable remainder is reported. This is retrospective usage, not price or latency.',
        'priority': {'consensus': 'Frozen executable, disagreement, minimum token confidence; ties use public row order.',
                     'risk': 'Frozen executable and minimum token confidence with hashed question-ID ties.'},
        'model_calls': 0, 'risk_wall_time_seconds': None, 'panel_sha256': panel,
        'gate_sha256': gate_hash, 'serving_profile_sha256': serving_hash,
        'managed_profile_sha256': provider_hash, 'official_metric_sha256': metric,
        'driver_sha256': driver, 'datasets': {},
    }
    seen, workers = set(), None
    for name in OFFICIAL_COUNTS:
        namespace = getattr(args, name)
        pool = [row for row in public if row['dataset'] == name]
        official = live_policy_timing.validate_official_panel(benchmark, name, pool, gold)
        plan, accepted, locations, provenance = accepted_prefix(
            namespace, name, panel, official, gate_hash, serving_hash, provider_hash, metric, driver, args.allow_partial)
        require(workers is None or plan['joint_workers'] == workers, 'Datasets use different actor concurrency')
        workers = plan['joint_workers']
        rows = {row['id']: row for row in pool}
        require({item['id']: item['report'] for item in plan['case_order']}
                == {key: row['report'] for key, row in rows.items()}, f'{name}: wrong question membership')
        cases, raw_hashes = {}, []
        incumbent = Counter()
        for historical in accepted:
            ident = historical['id']
            item = (name, ident)
            shard = locations[ident]
            run_hash = provenance['shards'][shard.name]['run.json']
            case, receipts = read_case(historical, rows[ident], gold[item], shard, run_hash, gate, profile,
                                       JOINT_SEED + 8 * public_order[item], args.metric_dir, ledger, seen)
            cases[item] = case
            raw_hashes.append([item, *receipts])
            actual = historical['policies']['joint-compact']
            incumbent.update(correct=actual['result']['strict'] and actual['result']['executable'],
                             known_tokens=actual['cost']['known_tokens'],
                             unknown_usage_calls=actual['cost']['unknown_usage_calls'],
                             teacher_posts=actual['calls'].get(TEACHER, {}).get('provider_posts', 0))
        by_report = {key: rows[key[1]]['report'] for key in cases}
        summary = summarize(cases, by_report, public_order, args.bootstrap_draws)
        reconstruction = summary['equal_k']['arms']['consensus']
        require(incumbent['correct'] == reconstruction['strict_executable_correct']
                and incumbent['known_tokens'] == reconstruction['total_known_tokens']
                and incumbent['teacher_posts'] == reconstruction['teacher_provider_posts']
                and incumbent['unknown_usage_calls'] == summary['local']['unknown_usage_questions']
                + reconstruction['unknown_teacher_usage_routes'],
                f'{name}: equal-K consensus must reproduce the actual fresh score and meter')
        summary['reproduced_fresh_consensus'] = dict(incumbent)
        if len(cases) < OFFICIAL_COUNTS[name]:
            report['scope'] = 'accepted_prefix_diagnostic'
        report['datasets'][name] = {**summary, 'official_n': OFFICIAL_COUNTS[name],
                                    'joint_workers': workers, 'verified_receipt_bundle_sha256': ordered_hash(raw_hashes),
                                    'provenance': provenance}
    return report


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    for flag in ('benchmark', 'finqa', 'tatqa', 'gate', 'serving-profile', 'metric-dir'):
        parser.add_argument(f'--{flag}', type=Path, required=True)
    parser.add_argument('--ledger', type=Path)
    parser.add_argument('--output', type=Path, help='Write one new JSON result. Defaults to stdout.')
    parser.add_argument('--allow-partial', action='store_true', help='Diagnostic replay of published accepted prefixes.')
    parser.add_argument('--bootstrap-draws', type=int, default=2000)
    args = parser.parse_args()
    if args.bootstrap_draws < 1:
        parser.error('--bootstrap-draws must be positive')
    report = run(args)
    result = json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2)
    if args.output is None:
        print(result)
    else:
        with args.output.open('x', encoding='utf-8') as output:
            output.write(result + '\n')


if __name__ == '__main__':
    main()
