"""Evaluate compact programs with one trusted local vLLM request per problem/arm.

The native vLLM path keeps the shared public compiler and official scorer. Its
HTTP receipts are distinct from OpenCode transcripts. A response's API usage
accounts for prompt text and generated choices. Isolated engine counters measure
prefill work and can differ from that API accounting.
"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from statistics import median
from time import perf_counter, sleep
from urllib.request import Request, urlopen
from uuid import uuid4

from benchmark_actions import digest_file, freeze, read_panel
from run_pilot import FINAL_DSL, PUBLIC_FIELDS, local_endpoint
from scoring import SCALE_FACTORS, _metric_type, finqa, public_execution, score
from table_scope_replay import representation


SAMPLE_COUNTS = (1, 4, 8)
COMPACT_SYSTEM = 'Answer the provided task using the supplied evidence.'
OPERAND_PLAN_INSTRUCTION = (
    '\nFirst write Plan: with up to two operand sources in order: Trow,col (table), '
    'Pparagraph (pre-text), Qparagraph (post-text), all zero-based. Use ? if unresolved.'
)
METRIC = re.compile(r'^(vllm:[\w]+)(?:\{([^}]*)\})?\s+(\S+)(?:\s+\S+)?$')
COUNTERS = {
    'vllm:prompt_tokens_total': 'prompt_tokens',
    'vllm:prompt_tokens_cached_total': 'cached_prompt_tokens',
    'vllm:prompt_tokens_by_source_total': 'prompt_tokens_by_source',
    'vllm:generation_tokens_total': 'generated_tokens',
    'vllm:prefix_cache_queries_total': 'prefix_cache_queries',
    'vllm:prefix_cache_hits_total': 'prefix_cache_hits',
    'vllm:request_success_total': 'requests_finished',
    'vllm:num_requests_running': 'running',
    'vllm:num_requests_waiting': 'waiting',
}


def compact_prompt(row, planned=False):
    """Build the same label-free user message for each dataset."""
    task = 'Solve the financial numerical reasoning question using only the supplied report.'
    directions = (
        FINAL_DSL
        + '\nAfter the program add one line Final scale: <none|thousand|million|billion|percent>.'
        ' Scale must describe the number produced by execution. For percent, the number is in percentage points.'
    )
    if planned:
        directions += OPERAND_PLAN_INSTRUCTION
    public = {field: row[field] for field in PUBLIC_FIELDS}
    return f'{task}\n{directions}\n\n{json.dumps(public, ensure_ascii=False)}'


def compact_request(prompt, model, *, n, max_tokens, temperature, seed, logprobs=True, cache_salt=None):
    if type(n) is not int or n not in SAMPLE_COUNTS:
        raise ValueError('n must be 1, 4, or 8')
    if not math.isfinite(temperature) or not 0 <= temperature <= 2 or (n > 1 and temperature == 0):
        raise ValueError('parallel sampling requires a positive finite temperature')
    if type(max_tokens) is not int or max_tokens <= 0 or not isinstance(model, str) or not model:
        raise ValueError('a model and a positive output cap are required')
    payload = {
        'model': model,
        'messages': [{'role': 'system', 'content': COMPACT_SYSTEM}, {'role': 'user', 'content': prompt}],
        'stream': False,
        'n': n, 'max_tokens': max_tokens, 'temperature': temperature, 'seed': seed,
        'logprobs': logprobs, 'chat_template_kwargs': {'enable_thinking': False},
    }
    if cache_salt is not None:
        payload['cache_salt'] = cache_salt
    return payload


def api_usage(response):
    usage = response.get('usage')
    if usage is None:
        return None
    names = ('prompt_tokens', 'completion_tokens', 'total_tokens')
    if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0 for k in names):
        raise ValueError('invalid vLLM response usage')
    if usage['prompt_tokens'] + usage['completion_tokens'] != usage['total_tokens']:
        raise ValueError('vLLM response usage does not reconcile')
    return usage


def metrics_snapshot(text):
    """Read relevant Prometheus counters, summed over an exclusive local engine."""
    totals = Counter()
    for line in text.splitlines():
        found = METRIC.fullmatch(line)
        if not found or (name := COUNTERS.get(found[1])) is None:
            continue
        value = float(found[3])
        if not math.isfinite(value) or value < 0 or not value.is_integer():
            raise ValueError(f'invalid vLLM metric {name}')
        if name == 'prompt_tokens_by_source':
            source = re.search(r'(?:^|,)\s*source="(local_compute|local_cache_hit|external_kv_transfer)"',
                               found[2] or '')
            if source is None:
                continue
            name = f'prompt_{source[1]}_tokens'
        totals[name] += int(value)
    return dict(totals)


def engine_work(before, after, usage):
    deltas = {key: after[key] - before[key] for key in after.keys() & before.keys()
              if key not in ('running', 'waiting')}
    idle = all(snapshot.get(key) == 0 for snapshot in (before, after) for key in ('running', 'waiting'))
    completion_match = usage is not None and deltas.get('generated_tokens') == usage['completion_tokens']
    valid = idle and completion_match and all(delta >= 0 for delta in deltas.values())
    local = deltas.get('prompt_local_compute_tokens') if valid else None
    return {'before': before, 'after': after, 'counter_deltas': deltas,
            'idle_before_after': idle, 'completion_tokens_reconcile': completion_match,
            'locally_computed_prefill_tokens': local,
            'locally_computed_tokens': local + deltas['generated_tokens'] if local is not None else None}


def minimum_logprob(choice):
    logprobs = choice.get('logprobs')
    tokens = logprobs.get('content') if isinstance(logprobs, dict) else None
    if not isinstance(tokens, list) or not tokens:
        return None
    values = [token.get('logprob') if isinstance(token, dict) else None for token in tokens]
    if any(type(value) not in (int, float) or not math.isfinite(value) or value > 0 for value in values):
        return None
    return min(values)


def vote_key(answer, scale):
    """Identify a value and declared unit using the same rule on both corpora."""
    if scale not in SCALE_FACTORS:
        return None
    if answer in ('yes', 'no'):
        return (answer, scale)
    if type(answer) not in (float, int):
        return None
    value = answer * SCALE_FACTORS[scale]
    return (round(value, 4), scale) if math.isfinite(value) else None


def evaluate_choices(row, response, n):
    """Execute each completed sample and select a program without a reference."""
    choices = response.get('choices')
    if (not isinstance(choices, list) or len(choices) != n
            or any(not isinstance(item, dict) or type(item.get('index')) is not int for item in choices)
            or {item['index'] for item in choices} != set(range(n))):
        raise ValueError('vLLM choices must contain each requested index exactly once')
    # The executor also uses public metadata that is absent from model input.
    public = {key: row[key] for key in ('dataset', *finqa.PUBLIC_KEYS)}
    executed = {}
    samples = []
    for choice in sorted(choices, key=lambda item: item['index']):
        index, finish = choice['index'], choice.get('finish_reason')
        message = choice.get('message')
        if not isinstance(message, dict) or message.get('role') != 'assistant':
            raise ValueError('vLLM choice lacks an assistant message')
        sample = {'index': index, 'finish_reason': finish, 'min_token_logprob': minimum_logprob(choice)}
        samples.append(sample)
        reply = message.get('content')
        if (finish != 'stop' or message.get('tool_calls') or message.get('function_call')
                or not isinstance(reply, str) or not reply.strip()):
            sample['status'] = 'not_delivered'
            continue
        projected, program, stage, _cells = representation(public, reply, stopped=True)
        execution = public_execution(projected, program)
        sample.update(stage=stage, submission=program, execution=execution, status='unexecutable')
        if projected is not public:
            sample['table_projection'] = projected['table']
        if execution['status'] == 'executed':
            key = vote_key(execution['terminal_execution_answer'], program['scale'])
            if key is not None:
                executed[index] = key
                sample.update(status='executed', vote_key=list(key))

    # Each requested choice remains in the denominator. Ties are reproducible.
    votes = Counter(executed.values())
    first = next(iter(executed), None)
    plurality = max(executed, key=lambda idx: votes[executed[idx]]) if executed else None
    support = votes[executed[plurality]] if plurality is not None else 0
    majority = plurality if 2 * support > n else None
    selected = majority if majority is not None else first
    return {'samples': samples, 'selected_index': selected, 'plurality_index': plurality,
            'majority_index': majority, 'first_executable_index': first, 'executed_n': len(executed),
            'vote_support': support, 'vote_share': support / n,
            'selected_min_token_logprob': samples[selected]['min_token_logprob'] if selected is not None else None}


def call_compact(row, *, base, model, n, max_tokens, temperature, seed, timeout=120,
                 logprobs=True, cache_salt=None, measure_engine=False, planned=False):
    """Run one native request. Engine measurement requires an exclusive serial server."""
    base = local_endpoint(base)
    request = compact_request(compact_prompt(row, planned=planned), model, n=n, max_tokens=max_tokens,
                              temperature=temperature, seed=seed, logprobs=logprobs, cache_salt=cache_salt)
    metrics_url = base.removesuffix('/v1') + '/metrics'
    before = None
    if measure_engine:
        with urlopen(metrics_url, timeout=timeout) as stream:
            before = metrics_snapshot(stream.read().decode('utf-8'))
        if any(before.get(key) != 0 for key in ('running', 'waiting')):
            raise RuntimeError('exclusive engine measurement requires an idle service')
    post = Request(base + '/chat/completions', data=json.dumps(request).encode('utf-8'),
                   headers={'Content-Type': 'application/json'}, method='POST')
    started = perf_counter()
    with urlopen(post, timeout=timeout) as stream:
        response = json.load(stream)
    model_wall = perf_counter() - started
    if not isinstance(response, dict) or response.get('model') != model:
        raise ValueError('vLLM response model differs from the pinned request')
    usage = api_usage(response)
    decision = evaluate_choices(row, response, n)
    route_wall = perf_counter() - started
    engine = None
    if before is not None:
        # Metric publication may trail the HTTP response. Observer time is excluded.
        for attempt in range(20):
            if attempt:
                sleep(0.1)
            with urlopen(metrics_url, timeout=timeout) as stream:
                after = metrics_snapshot(stream.read().decode('utf-8'))
            engine = engine_work(before, after, usage)
            if engine['locally_computed_tokens'] is not None or usage is None:
                break
    return {'transport': 'vllm_chat_nonstream', 'request': request, 'response': response,
            'model_wall_seconds': model_wall, 'route_wall_seconds': route_wall,
            'usage': usage, 'engine_work': engine, 'decision': decision}


def grade_choices(row, decision, gold, metric_dir):
    """Attach strict scores only after all public selections are fixed."""
    correct = []
    for sample in decision['samples']:
        valid = sample['status'] == 'executed'
        if valid:
            projected = row if 'table_projection' not in sample else {**row, 'table': sample['table_projection']}
            outcome = score(projected, sample['submission'], metric_dir=metric_dir, gold=gold)
            valid = bool(outcome['strict'] and outcome['executable'])
        correct.append(valid)
    selected = decision['selected_index']
    return {'strict_executable': selected is not None and correct[selected],
            'first_sample_strict_executable': correct[0], 'correct_by_index': correct}


def summarize(cases):
    n = len(cases)
    elapsed = sorted(case['route_wall_seconds'] for case in cases)
    usage = [case['usage'] for case in cases if case['usage'] is not None]
    engine = [work for case in cases if (work := case['engine_work']) is not None
              and work['locally_computed_tokens'] is not None]
    return {'questions': n, 'strict_executable': sum(case['score']['strict_executable'] for case in cases),
            'first_sample_strict_executable': sum(case['score']['first_sample_strict_executable'] for case in cases),
            'executable': sum(case['decision']['selected_index'] is not None for case in cases),
            'unanimous': sum(case['decision']['vote_share'] == 1 for case in cases),
            'known_api_usage': len(usage), 'known_engine_work': len(engine),
            'api_tokens': {key: sum(item[key] for item in usage) for key in
                           ('prompt_tokens', 'completion_tokens', 'total_tokens')},
            'engine_compute_tokens': sum(item['locally_computed_tokens'] for item in engine) if engine else None,
            'engine_prefill_tokens': sum(item['locally_computed_prefill_tokens'] for item in engine) if engine else None,
            'total_route_wall_seconds': sum(elapsed), 'p50_route_wall_seconds': median(elapsed),
            'p95_route_wall_seconds': elapsed[math.ceil(0.95 * n) - 1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panel', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--base', required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--serving-profile', required=True, type=Path)
    parser.add_argument('--dataset', choices=('finqa', 'tatqa'))
    parser.add_argument('--metric-dir', type=Path)
    parser.add_argument('--n', nargs='+', default=[1, 4, 8], type=int, choices=SAMPLE_COUNTS)
    parser.add_argument('--max-tokens', default=80, type=int)
    parser.add_argument('--temperature', default=0.6, type=float)
    parser.add_argument('--single-temperature', default=0.0, type=float)
    parser.add_argument('--seed', default=20261127, type=int)
    parser.add_argument('--timeout', default=120, type=float)
    parser.add_argument('--planned', action='store_true')
    parser.add_argument('--without-logprobs', action='store_true')
    parser.add_argument('--measure-exclusive-engine', action='store_true')
    parser.add_argument('--shared-request-cache', action='store_true',
                        help='Allow whole-request prefix reuse between arms and questions')
    parser.add_argument('--workers', type=int, default=1,
                        help='Parallel collection with aggregate engine counters for each n')
    args = parser.parse_args()
    public, gold, identity = read_panel(args.panel, args.dataset)
    if len(args.n) != len(set(args.n)):
        parser.error('duplicate n values')
    if not 1 <= args.workers <= 8:
        parser.error('--workers must be between 1 and 8')
    has_tatqa = any(row['dataset'] == 'tatqa' for row in public)
    if args.metric_dir is None and has_tatqa:
        parser.error('--metric-dir is required to grade TAT-QA')
    # The legacy loaders populate shared Python modules on first use.
    finqa.executor()
    if has_tatqa:
        _metric_type(args.metric_dir)
    args.output.mkdir(parents=True, exist_ok=False)
    run_salt = uuid4().hex
    metadata = vars(args)
    freeze(args.output / 'run.json', {
        **{key: str(value) if isinstance(value, Path) else value for key, value in metadata.items()},
        'compiler_sha256': digest_file(Path(__file__).with_name('table_scope_replay.py')),
        'scorer_sha256': digest_file(Path(__file__).with_name('scoring.py')),
        'runner_sha256': digest_file(Path(__file__)), 'panel_sha256': identity, 'run_salt': run_salt,
        'serving_profile_sha256': digest_file(args.serving_profile),
    })
    def collect(job):
        case_number, row, n = job
        key = row['dataset'], row['id']
        salt = None if args.shared_request_cache else sha256(f'{run_salt}:{case_number}:{n}'.encode()).hexdigest()
        temperature = args.single_temperature if n == 1 else args.temperature
        case = call_compact(row, base=args.base, model=args.model, n=n, max_tokens=args.max_tokens,
                            temperature=temperature, seed=args.seed + case_number * 8, timeout=args.timeout,
                            logprobs=not args.without_logprobs, cache_salt=salt,
                            measure_engine=args.measure_exclusive_engine and args.workers == 1, planned=args.planned)
        case.update(id=row['id'], dataset=row['dataset'], n=n, report=row['report'],
                    score=grade_choices(row, case['decision'], gold[key], args.metric_dir))
        return case

    def snapshot():
        with urlopen(local_endpoint(args.base).removesuffix('/v1') + '/metrics', timeout=args.timeout) as stream:
            return metrics_snapshot(stream.read().decode('utf-8'))

    grouped = {}
    engine_batches = {}
    with (args.output / 'cases.jsonl').open('x', encoding='utf-8') as stream:
        def record(case):
            print(json.dumps(case, ensure_ascii=False, allow_nan=False), file=stream, flush=True)
            # Keep scalar summaries in memory. Complete request and response stay on disk.
            summary_case = {key: case[key] for key in ('usage', 'engine_work', 'route_wall_seconds', 'score')}
            summary_case['decision'] = {key: case['decision'][key] for key in ('selected_index', 'vote_share')}
            grouped.setdefault(f'{case["dataset"]}/n{case["n"]}', []).append(summary_case)

        if args.workers == 1:
            for index, row in enumerate(public):
                offset = index % len(args.n)
                for n in args.n[offset:] + args.n[:offset]:
                    record(collect((index, row, n)))
        else:
            for dataset in sorted({row['dataset'] for row in public}):
                for n in args.n:
                    group = f'{dataset}/n{n}'
                    before = snapshot() if args.measure_exclusive_engine else None
                    if before is not None and any(before.get(key) != 0 for key in ('running', 'waiting')):
                        raise RuntimeError('exclusive engine measurement requires an idle service')
                    started = perf_counter()
                    with ThreadPoolExecutor(max_workers=args.workers) as pool:
                        for case in pool.map(collect, ((i, row, n) for i, row in enumerate(public)
                                                       if row['dataset'] == dataset)):
                            record(case)
                    elapsed = perf_counter() - started
                    usages = [case['usage'] for case in grouped[group]]
                    total = {'completion_tokens': sum(usage['completion_tokens'] for usage in usages)
                             } if all(usage is not None for usage in usages) else None
                    work = None
                    if before is not None:
                        for attempt in range(20):
                            if attempt:
                                sleep(0.1)
                            work = engine_work(before, snapshot(), total)
                            if work['locally_computed_tokens'] is not None or total is None:
                                break
                    engine_batches[group] = {'batch_wall_seconds': elapsed, 'engine_work': work}
    freeze(args.output / 'summary.json', {key: {**summarize(cases), **engine_batches.get(key, {})}
                                        for key, cases in grouped.items()})


if __name__ == '__main__':
    main()
