"""Collect matched local actions under a frozen OpenCode serving profile.

BudgetVerify adaptation (https://arxiv.org/html/2609.33052v1#S3): use
the pilot's executable DSL, omitting author-schema metadata such as confidence.
Mid uses the public execution trace, freezes operators and scale, and permits
one operand change or a reformat. High separates the
blind solve and the comparison into two charged requests and uses the pilot
executor and public operand grounding. A single checkpoint supplies all tiers.
CAR adaptation (https://arxiv.org/html/2611.05166v1#A2): collect its five
non-editing probe judgments against the shared DSL draft. This action alone
supplies inputs for CAR calibration, without fitting a gate or performing repair.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import time

from grounding import ground
from run_pilot import (
    PUBLIC_FIELDS, OpenCode, load_lines, local_endpoint, paired_prompt,
    wait_service, write_json,
)
from scoring import finqa, parse_dsl, public_execution, score


ACTIONS = ('low', 'mid', 'high', 'independent', 'car_probe')
FAMILIES = {
    'Omission': 'A requested value, derivation, or part of the question is missing.',
    'Binding': 'A value is tied to the wrong entity, period, concept, unit, or scope.',
    'Evidence': 'A claim uses unsupported, wrong, or conflicting supplied evidence.',
    'Numerical': 'An operation, denominator, sign, magnitude, or aggregate is wrong.',
    'Interpretation': 'A financial definition or stated explanation is unsupported or misapplied.',
}


def digest_file(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def freeze(path, value):
    if path.is_file():
        if json.loads(path.read_text(encoding='utf-8')) != value:
            raise ValueError(f'Frozen request differs at {path}; use a fresh namespace')
    else:
        write_json(path, value)


def deliver(call):
    return call['text'] if not call['exit_code'] and not call['errors'] else ''


def recorded_call(actor, prompt, target, contract_digest):
    target.mkdir(parents=True, exist_ok=True)
    key = {'prompt_sha256': hashlib.sha256(prompt.encode('utf-8')).hexdigest(),
           'run_contract': contract_digest, 'actor': actor.root.name}
    receipt, request, prompt_file = (target / name for name in ('call.json', 'request.json', 'prompt.txt'))
    if receipt.exists() or prompt_file.exists():
        if not request.is_file() or not prompt_file.is_file():
            raise ValueError(f'Unbound cached prompt or receipt at {target}')
        if prompt_file.read_text(encoding='utf-8') != prompt + '\n':
            raise ValueError(f'Cached prompt differs at {target}')
    freeze(request, key)
    return actor.call(prompt, target)


def mid_prompt(row, draft, execution):
    scale_format = (' Include Scale: <none|thousand|million|billion|percent> after the program.'
                    if row['dataset'] == 'tatqa' else '')
    return (
        'Check the existing financial answer for an obvious copying, formatting, or local arithmetic '
        'mistake using the report and the observed program execution below. Preserve the draft by '
        'answering KEEP unless the evidence supports a specific local correction. Do not solve the '
        'question from scratch, change operators, infer missing operands, or change the scale. '
        'If revising, provide a flat function-style program on a line starting Final program:.'
        + scale_format + '\n'
        + json.dumps({**{key: row[key] for key in PUBLIC_FIELDS}, 'draft': draft,
                      'execution': execution}, ensure_ascii=False)
    )


def mid_candidate(row, original, reply):
    if reply.strip() == 'KEEP':
        return original, 'keep_requested'
    candidate = parse_dsl(reply)
    if not candidate['program'] or public_execution(row, candidate)['status'] != 'executed':
        return original, 'keep_unexecutable_revision'
    executor = finqa.executor()
    try:
        before = executor.parse_program(original['program'] or '')
        after = executor.parse_program(candidate['program'])
    except executor.ExecutorContractError:
        return original, 'keep_no_local_edit_to_compare'
    if len(before) != len(after) or candidate['scale'] != original['scale']:
        return original, 'keep_outside_edit_bound'
    paired = list(zip(before, after, strict=True))
    if any(left.op != right.op for left, right in paired):
        return original, 'keep_outside_edit_bound'
    changes = sum((left.arg1 != right.arg1) + (left.arg2 != right.arg2) for left, right in paired)
    if changes > 1 or any(
        a != b and (a.startswith('#') or b.startswith('#'))
        for left, right in paired for a, b in ((left.arg1, right.arg1), (left.arg2, right.arg2))
    ):
        return original, 'keep_outside_edit_bound'
    return candidate, 'revise' if changes else 'reformat'


def compare_prompt(row, initial, candidate, evidence):
    return (
        'Choose between the two programs for the financial question below using only the report, '
        'execution results and operand locations. Prefer KEEP if both programs are equivalent or '
        'the available evidence does not support the new result. Use the requested period, entity, '
        'unit, and arithmetic to choose. Return exactly KEEP or USE_NEW. Do not propose edits.\n'
        + json.dumps({**{key: row[key] for key in PUBLIC_FIELDS}, 'initial': initial,
                      'independent_candidate': candidate, 'public_evidence': evidence}, ensure_ascii=False)
    )


def observable(row, candidate):
    trace = public_execution(row, candidate)
    bindings = ground(row, candidate['program']) if trace['status'] == 'executed' else []
    return {'execution': trace, 'bindings': [
        {'operand_id': item['operand_id'], 'value': item['token'],
         'match_count': len(item['candidates']), 'location': item['selected'],
         'conflicts': item['explicit_conflicts']} for item in bindings
    ]}


def car_prompt(row, draft):
    return (
        'Inspect the shared draft against the supplied report. Give a binary suspicion judgment '
        'and a short evidence-grounded reason for each listed error family. Use supplied evidence. '
        'Leave the draft unchanged and avoid suggesting repairs. Return exactly five lines in '
        'the given order, each formatted FAMILY: yes/no, rationale: REASON.\n'
        + json.dumps({**{key: row[key] for key in PUBLIC_FIELDS}, 'draft': draft,
                      'families': FAMILIES}, ensure_ascii=False)
    )


def parse_car(reply):
    lines = [line.strip() for line in reply.strip().splitlines() if line.strip()]
    if len(lines) != len(FAMILIES):
        return None
    judgments = {}
    for family, line in zip(FAMILIES, lines, strict=True):
        match = re.fullmatch(rf'{family}:\s*(yes|no)\s*,\s*rationale:\s*(\S.*)', line, flags=re.I)
        if match is None:
            return None
        judgments[family] = {'suspect': match[1].casefold() == 'yes', 'rationale': match[2]}
    return judgments


def collect_case(row, gold, actions, call, metric_dir):
    """Select unscored programs and only then attach strict outcome labels."""
    outputs = {}
    if set(actions) - {'independent'}:
        draft = deliver(call('low', 'solve', paired_prompt(row, 'dsl')))
        first = parse_dsl(draft)
        outputs['low'] = {'decision': 'first', 'submission': first, 'calls': ['low']}
        if 'mid' in actions:
            reply = deliver(call('mid', 'verify', mid_prompt(row, draft, public_execution(row, first))))
            candidate, decision = mid_candidate(row, first, reply)
            outputs['mid'] = {'submission': candidate, 'decision': decision, 'calls': ['low', 'mid']}
        if 'high' in actions:
            prompt = ('Derive the answer independently. Locate each operand in the report, then '
                      'work out the operations from the question.\n' + paired_prompt(row, 'dsl'))
            solved = parse_dsl(deliver(call('high_solve', 'solve', prompt)))
            evidence = {'initial': observable(row, first), 'independent': observable(row, solved)}
            judgment = deliver(call('high_compare', 'verify', compare_prompt(row, first, solved, evidence))).strip()
            independent = evidence['independent']
            grounded = all(item['match_count'] and not item['conflicts'] for item in independent['bindings'])
            use_new = judgment == 'USE_NEW' and independent['execution']['status'] == 'executed' and grounded
            outputs['high'] = {'submission': solved if use_new else first,
                               'decision': 'use_new' if use_new else 'keep', 'comparison': judgment,
                               'calls': ['low', 'high_solve', 'high_compare']}
        if 'car_probe' in actions:
            reply = deliver(call('car_probe', 'probe', car_prompt(row, draft)))
            outputs['car_probe'] = {'judgments': parse_car(reply), 'calls': ['low', 'car_probe']}
    if 'independent' in actions:
        if 'low' in outputs:
            outputs['independent'] = {**outputs['low'], 'decision': 'independent'}
        else:
            reply = deliver(call('independent', 'solve', paired_prompt(row, 'dsl')))
            outputs['independent'] = {'submission': parse_dsl(reply), 'decision': 'independent',
                                      'calls': ['independent']}
    for action in outputs.values():
        if 'submission' in action:
            scored = score(row, action['submission'], metric_dir=metric_dir, gold=gold)
            action.update(strict=bool(scored['strict']), executable=bool(scored['executable']))
    return outputs


def action_cost(calls):
    usage = [call['usage'] for call in calls]
    unknown = sum(item is None for item in usage)
    known_tokens = sum(item['total'] for item in usage if item is not None)
    return {'calls': len(calls), 'total_tokens': None if unknown else known_tokens,
            'known_tokens': known_tokens, 'unknown_usage_calls': unknown,
            'summed_call_seconds': sum(call['elapsed_seconds'] for call in calls)}


def read_panel(directory, dataset):
    public_path = directory / 'public.jsonl'
    reference_path = directory / 'references.jsonl'
    public = load_lines(public_path)
    reference = load_lines(reference_path)
    public_keys = {'dataset', 'id', 'report', *PUBLIC_FIELDS}
    if any(set(row) != public_keys or row['dataset'] not in {'finqa', 'tatqa'} for row in public):
        raise ValueError('Unexpected public schema; prompts require a label-free panel')
    if any(set(row) != {'dataset', 'id', 'gold'} for row in reference):
        raise ValueError('Unexpected scoring reference schema')
    ids = [(row['dataset'], row['id']) for row in public]
    gold = {(row['dataset'], row['id']): row['gold'] for row in reference}
    if len(set(ids)) != len(ids) or len(gold) != len(reference) or set(ids) != set(gold):
        raise ValueError('Panel and reference IDs must be unique and correspond one-to-one')
    rows = [row for row in public if dataset is None or row['dataset'] == dataset]
    if not rows:
        raise ValueError('Selected panel is empty')
    identity = {path.name: digest_file(path) for path in (public_path, reference_path)}
    return rows, gold, identity


def collect(args, root):
    rows, gold, panel = read_panel(args.panel, args.dataset)
    if any(row['dataset'] == 'tatqa' for row in rows):
        if args.metric_dir is None:
            raise ValueError('TAT-QA requires the official metric directory')
        from scoring import _metric_type
        _metric_type(args.metric_dir)
    profile = json.loads(args.serving_profile.read_text(encoding='utf-8'))
    if not isinstance(profile, dict) or profile.get('model') != args.model or profile.get('checkpoint') != args.checkpoint:
        raise ValueError('Serving profile must identify the requested model alias and checkpoint')
    outputs = {'solve': args.solve_output, 'verify': args.verify_output, 'probe': args.probe_output}
    profile_digest = digest_file(args.serving_profile)
    freeze(root / 'run.json', {
        'schema': 'finance-benchmark-actions-v1', 'namespace': args.namespace,
        'panel': panel, 'dataset': args.dataset, 'actions': sorted(set(args.actions)),
        'model': args.model, 'checkpoint': args.checkpoint, 'endpoint': args.base,
        'serve_sha256': profile_digest, 'opencode_sha256': digest_file(args.opencode),
        'seed': 17, 'context': args.context, 'output': outputs, 'temperature': args.temperature,
    })
    contract_digest = digest_file(root / 'run.json')
    wait_service(args.base, args.model, 90)
    actors = {name: OpenCode(root / 'actors' / name, args.opencode, args.base, args.model,
                             output, args.context, args.temperature) for name, output in outputs.items()}

    def case(row):
        dataset, ident = row['dataset'], row['id']
        case_id = hashlib.sha256(ident.encode('utf-8')).hexdigest()[:24]
        directory = root / 'calls' / dataset / case_id
        receipts = {}

        def call(name, actor, prompt):
            target = directory / name
            cached = (target / 'call.json').is_file()
            result = recorded_call(actors[actor], prompt, target, contract_digest)
            receipts[name] = {field: result[field] for field in ('usage', 'elapsed_seconds', 'exit_code', 'finish', 'errors')}
            receipts[name].update(cached_this_pass=cached,
                                  path=(target / 'call.json').relative_to(root).as_posix())
            return result

        actions = collect_case(row, gold[dataset, ident], args.actions, call, args.metric_dir)
        for action in actions.values():
            action['cost'] = action_cost([receipts[name] for name in action['calls']])
        return {'dataset': dataset, 'id': ident, 'report': row['report'],
                'actions': actions, 'calls': receipts}

    started = time.monotonic()
    temporary = root / 'outcomes.jsonl.tmp'
    new_calls = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool, temporary.open('w', encoding='utf-8') as stream:
        for index, result in enumerate(pool.map(case, rows), 1):
            new_calls += sum(not call['cached_this_pass'] for call in result['calls'].values())
            stream.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + '\n')
            if index % 10 == 0 or index == len(rows):
                print(f'{args.namespace} {index}/{len(rows)}', flush=True)
    temporary.replace(root / 'outcomes.jsonl')
    write_json(root / 'collection.json', {'rows': len(rows), 'new_calls_this_pass': new_calls,
                                         'collection_wall_seconds_this_pass': time.monotonic() - started})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panel', type=Path, required=True)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--namespace', required=True)
    parser.add_argument('--dataset', choices=('finqa', 'tatqa'))
    parser.add_argument('--actions', nargs='+', choices=ACTIONS, required=True)
    parser.add_argument('--base', type=local_endpoint, required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--checkpoint', required=True, help='Immutable checkpoint revision or digest')
    parser.add_argument('--serving-profile', required=True, type=Path,
                        help='Frozen JSON with model alias, checkpoint, and actual serving configuration')
    parser.add_argument('--metric-dir', type=Path)
    parser.add_argument('--opencode', type=Path, default=Path.home() / '.opencode/bin/opencode')
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--context', type=int, default=16384)
    parser.add_argument('--solve-output', type=int, default=4096)
    parser.add_argument('--verify-output', type=int, default=1024)
    parser.add_argument('--probe-output', type=int, default=256)
    parser.add_argument('--temperature', type=float, default=.6)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*', args.namespace):
        parser.error('namespace must be a single directory name')
    if not re.fullmatch(r'(?:[0-9a-f]{40}|(?:sha256:)?[0-9a-f]{64})', args.checkpoint):
        parser.error('checkpoint must be an immutable revision or SHA-256 digest')
    if args.workers < 1 or not all(0 < n < args.context for n in
                                  (args.solve_output, args.verify_output, args.probe_output)):
        parser.error('workers and output limits must be positive; outputs must fit context')
    args.opencode = args.opencode.resolve()
    import fcntl  # The collector runs beside the local model services on GB10.
    root = args.run_dir.resolve() / args.namespace
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    with (root / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        collect(args, root)


if __name__ == '__main__':
    main()
