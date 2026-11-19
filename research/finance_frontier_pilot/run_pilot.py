"""Run the fixed strong-base pilot on GB10 with OpenCode and pinned local endpoints."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.parse import urlparse
from urllib.request import urlopen

from grounding import ground, parse_verifier, verifier_prompt
from scoring import parse_dsl, parse_free, score


PUBLIC_FIELDS = ('question', 'table', 'pre_text', 'post_text')
FINAL_FREE = (
    'Reason in your preferred format and compute the numerical answer. End with one '
    'line in this format: Final answer: <number> [percent, thousand, million or billion '
    'if reported with that scale]. Give the actual requested unit. Do not emit a program.'
)
FINAL_DSL = (
    'Give a complete executable numeric program. End with a plain line Final program: '
    'followed by comma-separated op(arg1, arg2) steps. Allowed operators are add, '
    'subtract, multiply, divide, exp, greater, table_sum, table_average, table_max, '
    'table_min. Use #0 for the output of the first step, #1 for the second and so on. '
    'Use a literal from the report, a constant such as const_100, or a prior-step '
    'reference as an argument. For table operators use the exact row label and none. '
    'Do not nest calls. Format example: subtract(10, 4), divide(#0, const_100). '
    'For a literal-only result use add(value, const_0). End with no Markdown fence.'
)


def load_lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]


def write_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def paired_prompt(row, arm):
    task = 'Solve the financial numerical reasoning question using only the supplied report.'
    if arm == 'free':
        instructions = FINAL_FREE
        if row['dataset'] == 'finqa':
            instructions += ' For comparison questions the final answer may be yes or no.'
    else:
        instructions = FINAL_DSL
        if row['dataset'] == 'tatqa':
            instructions += (' After the program add one line Scale: <none|thousand|million|'
                             'billion|percent>. Scale must describe the number produced by execution. '
                             'For percent, the number is in percentage points.')
    public = {field: row[field] for field in PUBLIC_FIELDS}
    return f'{task}\n{instructions}\n\n{json.dumps(public, ensure_ascii=False)}'


def local_endpoint(address):
    url = urlparse(address)
    if (url.scheme, url.hostname, url.path) != ('http', '127.0.0.1', '/v1'):
        raise ValueError('use a local GB10 model service at http://127.0.0.1:<port>/v1')
    if url.query or url.fragment or url.username or url.password or not url.port:
        raise ValueError('invalid local endpoint')
    return address


def service_ready(base, model):
    try:
        with urlopen(f'{base}/models', timeout=3) as response:
            return any(item['id'] == model for item in json.load(response)['data'])
    except OSError:
        return False


def wait_service(base, model, timeout):
    until = time.monotonic() + timeout
    while not service_ready(base, model):
        if time.monotonic() >= until:
            raise TimeoutError(f'no healthy {model} at {base}')
        time.sleep(4)


def usage_from(events):
    totals = dict(input=0, output=0, total=0, reasoning=0, cache_read=0, cache_write=0, steps=0)
    for event in events:
        part = event.get('part', {})
        tokens = part.get('tokens')
        if event.get('type') == 'step_finish' and isinstance(tokens, dict):
            totals['steps'] += 1
            for field in ('input', 'output', 'reasoning'):
                totals[field] += tokens.get(field) or 0
            totals['total'] += tokens.get('total') or (tokens.get('input') or 0) + (tokens.get('output') or 0)
            cache = tokens.get('cache') or {}
            totals['cache_read'] += cache.get('read') or 0
            totals['cache_write'] += cache.get('write') or 0
    return totals if totals['steps'] else None


class OpenCode:
    def __init__(self, root, executable, base, model, output, context, temperature):
        self.root = root
        self.executable = executable
        self.model = f'pilot/{model}'
        self.root.mkdir(parents=True, exist_ok=True)
        (root / 'workspace').mkdir(exist_ok=True)
        config = {
            'autoupdate': False, 'share': 'disabled', 'model': self.model,
            'enabled_providers': ['pilot'], 'provider': {'pilot': {
                'name': 'GB10', 'npm': '@ai-sdk/openai-compatible',
                'options': {'baseURL': base, 'timeout': 480000, 'maxRetries': 0, 'includeUsage': True},
                'models': {model: {'name': model, 'tool_call': False,
                                    'limit': {'context': context, 'output': output}}}}},
            'agent': {'numeric': {'description': 'Financial numerical reasoning', 'mode': 'primary',
                                  'prompt': 'Answer the provided task using the supplied evidence.',
                                  'temperature': temperature, 'seed': 17,
                                  'permission': {'*': 'deny'}}},
            'tools': {'*': False}, 'permission': {'*': 'deny'},
        }
        frozen = root / 'opencode.json'
        if frozen.exists():
            saved = json.loads(frozen.read_text(encoding='utf-8'))
            saved.pop('$schema', None)  # OpenCode adds the schema URL on first use.
            if saved != config:
                raise ValueError(f'OpenCode configuration already frozen for {root.name}')
        else:
            write_json(frozen, config)
        self.env = {
            'PATH': os.environ['PATH'], 'LANG': 'C.UTF-8', 'HOME': str(root),
            'XDG_DATA_HOME': str(root / 'data'), 'XDG_STATE_HOME': str(root / 'state'),
            'XDG_CACHE_HOME': str(root / 'cache'), 'XDG_CONFIG_HOME': str(root / 'config'),
            'OPENCODE_CONFIG': str(frozen), 'OPENCODE_DISABLE_MODELS_FETCH': '1',
            'OPENCODE_DISABLE_AUTOUPDATE': '1', 'OPENCODE_DISABLE_LSP': '1',
            'OPENCODE_DISABLE_PROJECT_CONFIG': '1', 'OPENCODE_DISABLE_AUTO_COMPACT': '1',
        }

    def call(self, prompt, destination):
        destination.mkdir(parents=True, exist_ok=True)
        result_path = destination / 'call.json'
        if result_path.is_file():
            return json.loads(result_path.read_text(encoding='utf-8'))
        (destination / 'prompt.txt').write_text(prompt + '\n', encoding='utf-8')
        started = time.monotonic()
        command = [str(self.executable), 'run', '--pure', '--format', 'json', '--thinking',
                   '--agent', 'numeric', '--title', 'financial pilot', '-m', self.model, '--', prompt]
        try:
            run = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, cwd=self.root / 'workspace',
                                 env=self.env, timeout=500)
            raw, stderr, code = run.stdout, run.stderr, run.returncode
        except subprocess.TimeoutExpired as error:
            raw, stderr, code = error.stdout or b'', error.stderr or b'', 124
        (destination / 'raw.jsonl').write_bytes(raw)
        (destination / 'stderr.txt').write_bytes(stderr)
        events = []
        for line in raw.decode('utf-8', errors='replace').splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        result = {
            'text': '\n'.join(e.get('part', {}).get('text', '') for e in events if e.get('type') == 'text'),
            'finish': [event.get('part', {}).get('reason') for event in events if event.get('type') == 'step_finish'],
            'errors': [event.get('error') for event in events if event.get('type') == 'error'],
            'elapsed_seconds': round(time.monotonic() - started, 3),
            'exit_code': code, 'usage': usage_from(events),
        }
        write_json(result_path, result)
        return result


def rank_auc(values, keys):
    points = sorted(zip(values, keys))
    positives = sum(keys)
    negatives = len(keys) - positives
    if not positives or not negatives:
        return None
    start = rank_sum = 0
    while start < len(points):
        end = start + 1
        while end < len(points) and points[end][0] == points[start][0]:
            end += 1
        mean_rank = (start + 1 + end) / 2
        rank_sum += sum(label for _, label in points[start:end]) * mean_rank
        start = end
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def finish_batch(items, arm, function, workers):
    started = time.monotonic()
    with ThreadPoolExecutor(workers) as executor:
        tasks = [executor.submit(function, item) for item in items]
        for count, future in enumerate(as_completed(tasks), 1):
            future.result()
            if count % 10 == 0 or count == len(items):
                print(f'{arm} {count}/{len(items)} {time.monotonic()-started:.0f}s', flush=True)


def grounding_diagnostic(row, parsed, executable, actor, path):
    if not executable:
        return {'bindings': [], 'risk_score': None, 'status': 'not_executable'}
    bindings = ground(row, parsed['program'])
    if not bindings:
        return {'bindings': [], 'risk_score': None, 'status': 'no_literal_bindings'}
    eligible = any(b['selected'] and not b['explicit_conflicts'] for b in bindings)
    reply = actor.call(verifier_prompt(row, bindings), path / 'reverse')['text'] if eligible else None
    return {'bindings': bindings, 'verifier_called': eligible, **parse_verifier(reply, bindings)}


def normalized_disagreement(dataset, free, dsl):
    left, right = free.get('normalized_answer'), dsl.get('normalized_answer')
    if left is None or right is None:
        return None
    if isinstance(left, (float, int)) and isinstance(right, (float, int)):
        precision = 5 if dataset == 'finqa' else 4
        return int(round(left, precision) != round(right, precision))
    return int(left != right)


def summarize(rows):
    summary = {'datasets': {}}
    for scope in ('finqa', 'tatqa', 'pooled'):
        group = [r for r in rows if scope == 'pooled' or r['dataset'] == scope]
        if not group:
            continue
        n = len(group)
        arms = ('free', 'dsl')
        counts = {arm: {name: sum(bool(r[arm][name]) for r in group) for name in ('strict', 'norm', 'rule')}
                  for arm in arms}
        diagnostic = {}
        signals = [name for name in ('reverse_risk', 'representation_disagreement', 'legacy_risk', 'legacy_value')
                   if any(r.get(name) is not None for r in group)]
        for signal in signals:
            covered = [r for r in group if r.get(signal) is not None]
            teachers = [r for r in covered if not r['dsl']['strict'] and r.get('teacher') is not None]
            wrong = [not r['dsl']['strict'] for r in covered]
            rescued = [bool(r['teacher']['strict']) for r in teachers]
            common = [r for r in covered if all(r.get(other) is not None for other in signals)]
            common_teachers = [r for r in common if not r['dsl']['strict'] and r.get('teacher') is not None]
            diagnostic[signal] = {
                'detection_auc': rank_auc([r[signal] for r in covered], wrong),
                'detection_n': len(covered), 'detection_wrong_n': sum(wrong),
                'recoverability_auc': rank_auc([r[signal] for r in teachers], rescued),
                'recoverability_n': len(teachers), 'recoverable_n': sum(rescued),
                'common_detection_auc': rank_auc([r[signal] for r in common], [not r['dsl']['strict'] for r in common]),
                'common_detection_n': len(common),
                'common_recoverability_auc': rank_auc([r[signal] for r in common_teachers],
                                                       [bool(r['teacher']['strict']) for r in common_teachers]),
                'common_recoverability_n': len(common_teachers),
            }
        transitions = {}
        for left, right in (('dsl.strict', 'dsl.norm'), ('dsl.rule', 'dsl.norm'), ('dsl.norm', 'free.norm')):
            a, m = left.split('.')
            b, k = right.split('.')
            transitions[f'{left}->{right}'] = {
                'recoveries': sum(not r[a][m] and r[b][k] for r in group),
                'losses': sum(r[a][m] and not r[b][k] for r in group),
            }
        summary['datasets'][scope] = {
            'n': n, 'counts': counts, 'executable_dsl': sum(r['dsl']['executable'] for r in group),
            'teacher_wrong_n': sum(r.get('teacher') is not None for r in group),
            'teacher_rescued': sum(bool(r.get('teacher') and r['teacher']['strict']) for r in group),
            'delta_contract_pp_raw': 100 * (counts['dsl']['norm']-counts['dsl']['strict'])/n,
            'delta_contract_pp_after_public_rule': 100 * (counts['dsl']['norm']-counts['dsl']['rule'])/n,
            'delta_format_tax_pp': 100 * (counts['free']['norm']-counts['dsl']['norm'])/n,
            'delta_semantic_operational_pp': 100 * (n-counts['free']['norm'])/n,
            'transitions': transitions, 'diagnostic': diagnostic,
        }
    return summary


def aggregate_cost(root):
    sums = {}
    for path in root.glob('calls/*/*/*/call.json'):
        arm = path.parent.name
        receipt = json.loads(path.read_text(encoding='utf-8'))
        total = sums.setdefault(arm, {'calls': 0, 'unknown_usage': 0, 'exit_nonzero': 0,
                                      'input': 0, 'output': 0, 'total': 0, 'reasoning': 0,
                                      'cache_read': 0, 'cache_write': 0,
                                      'summed_call_seconds': 0})
        total['calls'] += 1
        total['exit_nonzero'] += receipt['exit_code'] != 0
        total['summed_call_seconds'] += receipt['elapsed_seconds']
        usage = receipt['usage']
        if usage is None:
            total['unknown_usage'] += 1
        else:
            for field in ('input', 'output', 'reasoning', 'cache_read', 'cache_write'):
                total[field] += usage[field]
            total['total'] += usage.get('total', usage['input'] + usage['output'])
    return sums


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--metric-dir', required=True, type=Path)
    parser.add_argument('--opencode', type=Path, default=Path.home()/'.opencode/bin/opencode')
    parser.add_argument('--rule-dir', type=Path)
    parser.add_argument('--base', type=local_endpoint, default='http://127.0.0.1:18157/v1')
    parser.add_argument('--model', default='oda-fin-rl-8b')
    parser.add_argument('--teacher-base', type=local_endpoint, default='http://127.0.0.1:8006/v1')
    parser.add_argument('--teacher-model', default='qwen38-27b-fp8')
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--smoke', action='store_true', help='synthetic inputs only')
    parser.add_argument('--phase', choices=('oda', 'teacher'), required=True)
    args = parser.parse_args()
    run(args)


def run(args):
    started = time.monotonic()
    root = args.root.resolve()
    main_actor = OpenCode(root / 'actors/oda', args.opencode, args.base, args.model, 4096, 16384, .6)
    reverse_actor = OpenCode(root / 'actors/reverse', args.opencode, args.base, args.model, 1024, 16384, .1)
    teacher = OpenCode(root / 'actors/teacher', args.opencode, args.teacher_base, args.teacher_model, 4096, 16384, .2)
    if args.phase == 'oda':
        wait_service(args.base, args.model, 300)
    if args.smoke:
        row = {'dataset': 'finqa', 'question': 'What was the change in revenue from 2022 to 2023?',
               'table': [['$ in millions', '2022', '2023'], ['revenue', '17', '29']],
               'pre_text': [], 'post_text': []}
        if args.phase == 'teacher':
            wait_service(args.teacher_base, args.teacher_model, 90)
            report = teacher.call(paired_prompt(row, 'dsl'), root / 'smoke/teacher')
            print('teacher', report, flush=True)
            if not parse_dsl(report['text']).get('program') or not report['usage']:
                raise ValueError('OpenCode teacher smoke failed')
            return
        for arm in ('free', 'dsl'):
            report = main_actor.call(paired_prompt(row, arm), root / 'smoke' / arm)
            print(arm, report, flush=True)
            parser = parse_free if arm == 'free' else parse_dsl
            if not report['text'] or not report['usage']:
                raise ValueError(f'OpenCode {arm} smoke failed')
            parsed = parser(report['text'])
            if not parsed.get('program') and parsed.get('answer') is None:
                raise ValueError(f'OpenCode {arm} output could not be read')
        path = root / 'smoke'
        report = json.loads((path / 'dsl/call.json').read_text(encoding='utf-8'))
        parsed = parse_dsl(report['text'])
        print('reverse', grounding_diagnostic(row, parsed, bool(parsed.get('program')), reverse_actor, path), flush=True)
        return

    public = load_lines(root / 'panel/public.jsonl')
    references = {(row['dataset'], row['id']): row['gold'] for row in load_lines(root / 'panel/references.jsonl')}
    if len(public) != 400 or len(references) != 400:
        raise ValueError('expected two frozen panels of 200 tasks')
    indexed = list(enumerate(public))

    def destination(idx, row):
        return root / 'calls' / row['dataset'] / f'{idx:03d}'

    def action(task):
        idx, row, arm = task
        report = main_actor.call(paired_prompt(row, arm), destination(idx, row) / arm)
        if not report['text']:
            print(f'no answer: {row["dataset"]}:{idx}:{arm} exit={report["exit_code"]}', flush=True)

    if args.phase == 'oda':
        actions = [(idx, row, arm) for idx, row in indexed for arm in ('free', 'dsl')]
        finish_batch(actions, 'paired generation', action, args.workers)
        write_json(root / 'generation_cost.json', {'wall_seconds': time.monotonic()-started,
                                                   'cost': aggregate_cost(root)})

    def read_score(idx, row, arm):
        path = destination(idx, row) / arm / 'call.json'
        receipt = json.loads(path.read_text(encoding='utf-8'))
        parsed = (parse_free if arm == 'free' else parse_dsl)(receipt['text'])
        return parsed, score(row, parsed, metric_dir=args.metric_dir, rule_dir=args.rule_dir,
                             gold=references[row['dataset'], row['id']])

    prepared = []
    for idx, row in indexed:
        _, free = read_score(idx, row, 'free')
        parsed, dsl = read_score(idx, row, 'dsl')
        prepared.append((idx, row, parsed, free, dsl))
    generation_results = [{'dataset': row['dataset'], 'id': row['id'], 'free': free, 'dsl': dsl,
                           'reverse_risk': None, 'representation_disagreement': normalized_disagreement(row['dataset'], free, dsl)}
                          for _, row, _, free, dsl in prepared]
    write_json(root / 'generation_scores.json', summarize(generation_results))
    print(json.dumps(summarize(generation_results)), flush=True)

    def reverse(item):
        idx, row, parsed, _, dsl = item
        path = destination(idx, row)
        write_json(path / 'grounding.json', grounding_diagnostic(row, parsed, dsl['executable'], reverse_actor, path))

    def independent_teacher(item):
        idx, row, _, _, _ = item
        teacher.call(paired_prompt(row, 'dsl'), destination(idx, row) / 'teacher')

    if args.phase == 'oda':
        finish_batch(prepared, 'reverse', reverse, args.workers)
        write_json(root / 'oda_cost.json', {'wall_seconds': time.monotonic()-started,
                                           'cost': aggregate_cost(root)})
        return
    wait_service(args.teacher_base, args.teacher_model, 240)
    finish_batch([item for item in prepared if not item[4]['strict']], 'teacher', independent_teacher, 1)
    legacy_path = root / 'legacy_heads.json'
    legacy = json.loads(legacy_path.read_text(encoding='utf-8')) if legacy_path.is_file() else None
    indexed_legacy = {(r['dataset'], r['id']): r for r in legacy['rows']} if legacy else {}
    for (idx, row, _, _, _), result in zip(prepared, generation_results):
        path = destination(idx, row)
        result['grounding'] = json.loads((path / 'grounding.json').read_text(encoding='utf-8'))
        result['reverse_risk'] = result['grounding'].get('risk_score')
        prior = indexed_legacy.get((row['dataset'], row['id']), {})
        result.update(legacy_risk=prior.get('risk'), legacy_value=prior.get('value'))
        if not result['dsl']['strict']:
            _, result['teacher'] = read_score(idx, row, 'teacher')
    write_json(root / 'outcomes.json', generation_results)
    summary = summarize(generation_results)
    summary.update(wall_seconds=time.monotonic()-started, cost=aggregate_cost(root))
    if legacy:
        summary['legacy_head_compute'] = legacy['metrics']
    write_json(root / 'summary.json', summary)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
