"""CAR adaptation for the shared OpenCode draft and official DSL scoring.

Run collect fit, fit, collect calibration, freeze, then collect eval. Fit trials
assign one of five bounded checks independently of the draft and probe. Fit
labels use binary native miss and seven failure proxies, not the authors' rubric
or induced 25 leaves. Question-only TF-IDF neighbors and shrunken single-check
recovery estimates route checks. Local edits use structured DSL field bounds
instead of the paper's text spans. Calibration replays the fixed repair plan on
every draft. The final gate uses the resulting recovery/damage rates.

Source: https://arxiv.org/html/2611.05166v1#S4 and Appendices A–E.
"""

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re
import time

from benchmark_actions import (
    FAMILIES, OpenCode, action_cost, car_prompt, deliver, digest_file, freeze, load_lines,
    local_endpoint, parse_car, read_panel, recorded_call, wait_service, write_json,
)
from diagnose import read_replay_call
from grounding import YEAR, UNIT, ground
from run_pilot import paired_prompt
from scoring import SCALE_FACTORS, _metric_type, _reply_text, finqa, parse_dsl, public_execution, score


CHECKS = {
    'Omission': 'Check whether a requested calculation step is missing. Append the missing step only when supported.',
    'Binding': 'Match the operand to the requested entity, reporting period, unit, and accounting concept.',
    'Evidence': 'Verify that the operand is supported by the supplied report and matches the question.',
    'Numerical': 'Check the selected operands, operation, signs, denominator, and output scale.',
    'Interpretation': 'Check which comparison, aggregation, or financial relation the question requests.',
}
LEAVES = ('missing_program', 'missing_step', 'binding_conflict', 'unlocated_operand',
          'scale_factor', 'operation_or_arithmetic', 'requested_relation')
ALPHAS = (.0001, .001, .01, .1, 1., 10., 100.)
FEATURES = ('question_words', 'question_years', 'question_units', 'source_words', 'table_cells',
            'program_words', 'program_years', 'program_units', 'missing_probe', *FAMILIES)
PROFILE_KEYS = ('model', 'checkpoint', 'serve_sha256', 'opencode_sha256', 'seed',
                'context', 'output', 'temperature')
WORD = re.compile(r'\b\w+\b')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def row_key(row):
    return row['dataset'], row['id']


def strict_join(rows, entries):
    indexed = {row_key(entry): entry for entry in entries}
    if len(indexed) != len(entries) or set(indexed) != {row_key(row) for row in rows}:
        raise ValueError('CAR collection and public panel must have exactly the same questions')
    return [(row, indexed[row_key(row)]) for row in rows]


def program_steps(draft):
    executor = finqa.executor()
    try:
        return executor.parse_program(draft.get('program') or '')
    except executor.ExecutorContractError:
        return ()


def features(row, draft, judgments):
    question = row['question']
    program = draft.get('program') or ''
    narrative = ' '.join([*row['pre_text'], *row['post_text']])
    return [len(WORD.findall(question)), len(YEAR.findall(question)), len(UNIT.findall(question)),
            len(WORD.findall(narrative)), sum(map(len, row['table'])), len(WORD.findall(program)),
            len(YEAR.findall(program)), len(UNIT.findall(program)), int(judgments is None),
            *(int(judgments[family]['suspect']) if judgments else 0 for family in FAMILIES)]


def fit_leaf(row, draft, gold, scored):
    """Use answer labels only to form the offline failure index."""
    steps = program_steps(draft)
    if not steps:
        return 'missing_program'
    reference_steps = program_steps({'program': gold.get('program')})
    if reference_steps and len(steps) < len(reference_steps):
        return 'missing_step'
    bindings = ground(row, draft['program'])
    if any(binding['explicit_conflicts'] for binding in bindings):
        return 'binding_conflict'
    if any(not binding['candidates'] for binding in bindings):
        return 'unlocated_operand'
    if scored['gold_assisted_factor'] is not None:
        return 'scale_factor'
    if reference_steps and (reference_steps[-1].op == 'greater') != (steps[-1].op == 'greater'):
        return 'requested_relation'
    return 'operation_or_arithmetic'


def evidence_pointer(row, draft, check):
    """Index the shared context and mark a calculation using public evidence only."""
    blocks = {f'table[{i}]': cells for i, cells in enumerate(row['table'])}
    blocks.update({f'{name}[{i}]': text for name in ('pre_text', 'post_text')
                   for i, text in enumerate(row[name])})
    query = set(WORD.findall(row['question'].casefold()))
    ranked = sorted(blocks, key=lambda key: -len(query.intersection(WORD.findall(str(blocks[key]).casefold()))))
    steps = program_steps(draft)
    target_step = len(steps) - 1
    bindings = ground(row, draft['program']) if steps and check != 'Omission' else []
    if check in ('Binding', 'Evidence'):
        candidates = [binding for binding in bindings if binding['explicit_conflicts'] or not binding['candidates']]
        if candidates:
            target_step = int(candidates[0]['operand_id'].split(':')[0])
    nearby = []
    for binding in bindings:
        if not binding['operand_id'].startswith(f'{target_step}:'):
            continue
        for source in binding['candidates']:
            nearby.append(f"table[{source['row']}]" if 'row' in source
                          else f"{source['section']}[{source['paragraph']}]")
    return blocks, {'step': target_step, 'source_ids': list(dict.fromkeys(nearby[:3] + ranked[:3]))}


def repair_prompt(row, draft, check, hypotheses, blocks, pointer):
    if check == 'Omission':
        contract = ('Return zero or one append edit with keys type, program, evidence_id. The program field '
                    'contains exactly one flat DSL operation over supplied values or prior step references.')
    else:
        contract = ('Return replacements with keys type, field, value, evidence_id. Edit only op, arg1, or arg2 '
                    'of the pointed-to step. The value is a single DSL field, never a complete program.')
        if row['dataset'] == 'tatqa' and check == 'Numerical':
            contract += ' For a scale correction, field may be scale and value one of none, thousand, million, billion, percent.'
    return (
        'Inspect the named relation using only the question, draft and supplied evidence. Begin at the pointer. '
        'The listed failure possibilities are hypotheses. Preserve all content outside the edit scope. '
        'Each edit must cite a supplied evidence ID. Return a single JSON object with the key edits and an '
        'array of edits, or an empty array if a correction is unsupported. ' + contract + '\n'
        + json.dumps({'question': row['question'], 'draft': draft, 'evidence': blocks, 'pointer': pointer,
                      'check': CHECKS[check], 'possible_failures': hypotheses}, ensure_ascii=False)
    )


def accept_patch(row, draft, reply, check, blocks, pointer):
    try:
        payload = json.loads(_reply_text(reply))
    except ValueError:
        return draft, 'invalid_json'
    if not isinstance(payload, dict) or set(payload) != {'edits'} or not isinstance(payload['edits'], list):
        return draft, 'invalid_edits'
    edits = payload['edits']
    if not edits:
        return draft, 'kept'
    steps = list(program_steps(draft))
    scale = draft['scale']
    executor = finqa.executor()
    if len(edits) > min(2, max(1, (3 * len(steps) + (row['dataset'] == 'tatqa')) // 5)):
        return draft, 'outside_edit_bound'
    touched = set()
    for edit in edits:
        if not isinstance(edit, dict) or not isinstance(edit.get('evidence_id'), str) or edit['evidence_id'] not in blocks:
            return draft, 'unsupported_evidence_id'
        if check == 'Omission':
            if set(edit) != {'type', 'program', 'evidence_id'} or edit['type'] != 'append' or len(edits) != 1:
                return draft, 'outside_append_bound'
            program = edit['program']
            if not isinstance(program, str) or len(program) > 320:
                return draft, 'outside_append_bound'
            added = program_steps({'program': program})
            if len(added) != 1:
                return draft, 'outside_append_bound'
            steps.append(replace(added[0], index=len(steps)))
        else:
            if set(edit) != {'type', 'field', 'value', 'evidence_id'} or edit['type'] != 'replace':
                return draft, 'outside_edit_bound'
            field, value = edit['field'], edit['value']
            if not isinstance(field, str) or field in touched or not isinstance(value, str) or len(value) > 160:
                return draft, 'outside_edit_bound'
            touched.add(field)
            if field == 'scale' and row['dataset'] == 'tatqa' and check == 'Numerical':
                scale = '' if value == 'none' else value
                if scale not in SCALE_FACTORS:
                    return draft, 'invalid_scale'
            elif field in ('op', 'arg1', 'arg2') and steps and not re.search(r'[()\r\n]|,\s', value):
                step = pointer['step']
                steps[step] = replace(steps[step], **{field: value})
            else:
                return draft, 'outside_edit_bound'
    candidate = {**draft, 'program': executor.render_program(steps), 'scale': scale}
    if candidate == draft:
        return draft, 'kept'
    if public_execution(row, candidate)['status'] != 'executed':
        return draft, 'unexecutable_edit'
    return candidate, 'edited'


class RepairPlanner:
    def __init__(self, policy):
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.policy = policy
        neighbors = policy['neighbors']
        self.vectorizer = TfidfVectorizer(token_pattern=r'\b\w+\b')
        self.matrix = self.vectorizer.fit_transform([item['question'] for item in neighbors]) if neighbors else None

    def predict(self, row, draft, judgments):
        x = features(row, draft, judgments)
        ridge = self.policy['ridge']
        miss = ridge['intercept'] + sum(w * (v - m) / s for w, v, m, s in zip(
            ridge['weights'], x, ridge['means'], ridge['scales'], strict=True))
        return min(1., max(0., miss))

    def check(self, question, miss):
        neighbors = self.policy['neighbors']
        counts = Counter()
        if self.matrix is not None:
            similarities = (self.matrix @ self.vectorizer.transform([question[:700]]).T).toarray().ravel()
            nearest = sorted(range(len(neighbors)), key=lambda i: (-similarities[i], i))[:50]
            counts.update(neighbors[i]['leaf'] for i in nearest if similarities[i] > 0)
        scores = self.policy['check_rates']
        n = sum(counts.values())
        hypotheses = sorted(counts, key=lambda leaf: (-counts[leaf], leaf))[:5]

        def expected_recovery(check):
            action = scores[check]
            weighted = sum(counts[leaf] * action['leaves'][leaf] for leaf in counts)
            return (weighted + 4 * action['recover']) / (n + 4)

        check = max(CHECKS, key=expected_recovery)
        gain = miss * expected_recovery(check) - (1 - miss) * scores[check]['damage']
        return check, gain, hypotheses


def fit_policy(rows, results, checked_profile):
    import numpy as np
    from sklearn.linear_model import Ridge
    from sklearn.model_selection import GroupKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    samples = strict_join(rows, results)
    x = np.asarray([features(row, result['draft'], result['judgments']) for row, result in samples])
    y = np.asarray([int(not result['draft_correct']) for _, result in samples])
    groups = [row['report'] for row, _ in samples]
    if len(set(groups)) < 2:
        raise ValueError('ridge selection requires at least two fit reports')
    partitions = list(GroupKFold(n_splits=min(5, len(set(groups)))).split(x, y, groups))

    def fit(indices, alpha):
        return make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(x[indices], y[indices])

    def cross_validation(alpha):
        return float(np.mean([np.mean(abs(fit(train, alpha).predict(x[val]).clip(0, 1) - y[val]))
                              for train, val in partitions]))

    errors = [cross_validation(alpha) for alpha in ALPHAS]
    alpha = ALPHAS[errors.index(min(errors))]
    estimator = fit(np.arange(len(y)), alpha)
    scale, ridge = estimator.named_steps['standardscaler'], estimator.named_steps['ridge']
    totals, leaves = Counter(), Counter()
    for _, result in samples:
        check, leaf = result['check'], result['fit_leaf']
        before, after = result['draft_correct'], result['strict']
        totals[check, before, after] += 1
        if not before:
            leaves[check, leaf, after] += 1

    def rate(events, attempts, prior=0., shrinkage=0):
        return (events + prior * shrinkage) / (attempts + shrinkage) if attempts + shrinkage else 0.

    recovered = sum(totals[name, False, True] for name in CHECKS)
    damaged = sum(totals[name, True, False] for name in CHECKS)
    fit_recovery, fit_damage = rate(recovered, sum(y)), rate(damaged, len(y) - sum(y))
    check_rates = {}
    for name in CHECKS:
        r = totals[name, False, True]
        h = totals[name, True, False]
        miss = r + totals[name, False, False]
        hits = h + totals[name, True, True]
        recover = float(rate(r, miss, fit_recovery, 4))
        check_rates[name] = {'recover': recover, 'damage': float(rate(h, hits, fit_damage, 4)),
                             'recovered': r, 'damaged': h, 'prior_misses': miss, 'prior_hits': hits,
                             'leaves': {leaf: rate(leaves[name, leaf, True],
                                                   leaves[name, leaf, True] + leaves[name, leaf, False], recover, 4)
                                        for leaf in LEAVES}}
    return {'schema': 'finance-car-v1', 'stage': 'fit', 'dataset': rows[0]['dataset'], 'profile': checked_profile,
            'fit_reports': sorted(set(groups)), 'fit_ids': sorted(row['id'] for row in rows),
            'ridge': {'alpha': alpha, 'features': list(FEATURES), 'means': scale.mean_.tolist(),
                      'scales': scale.scale_.tolist(), 'weights': ridge.coef_.tolist(),
                      'intercept': float(ridge.intercept_), 'group_cv_mae': dict(zip(map(str, ALPHAS), errors))},
            'neighbors': [{'question': row['question'][:700], 'leaf': result['fit_leaf']}
                          for row, result in samples if not result['draft_correct']],
            'check_rates': check_rates}


def freeze_gate(policy, results):
    before_wrong = sum(not result['draft_correct'] for result in results)
    before_right = len(results) - before_wrong
    recovered = sum(not result['draft_correct'] and result['strict'] for result in results)
    damaged = sum(result['draft_correct'] and not result['strict'] for result in results)
    f = recovered / before_wrong if before_wrong else None
    d = damaged / before_right if before_right else None
    threshold = d / (f + d) if f is not None and d is not None and f + d else None
    return {**policy, 'stage': 'frozen', 'gate': {'threshold': threshold, 'recover': f, 'damage': d,
            'recovered': recovered, 'damaged': damaged, 'prior_misses': before_wrong,
            'prior_hits': before_right, 'trials': len(results)}}


def source_rows(args, stage):
    rows, gold, panel = read_panel(args.panel_root / stage, args.dataset)
    source = args.drafts / 'run.json'
    contract = read(source)
    if contract['panel'] != panel or contract['dataset'] not in (None, args.dataset):
        raise ValueError('Draft collection disagrees with the selected panel')
    outcomes = [r for r in load_lines(args.drafts / 'outcomes.jsonl') if r['dataset'] == args.dataset]
    entries = strict_join(rows, outcomes)
    run_digest = digest_file(source)
    coverage = {'decoder': 'explicit_five_family_final_answer_v1', 'questions': len(entries),
                'saved_valid': 0, 'recovered_by_replay': 0, 'missing': 0}
    for row, entry in entries:
        choices = entry['actions']
        if (choices['low']['calls'] != ['low'] or choices['car_probe']['calls'] != ['low', 'car_probe']
                or not {'low', 'car_probe'} <= entry['calls'].keys()):
            raise ValueError('CAR requires a shared low draft and its charged five-family probe')
        probe = choices['car_probe']
        if probe['judgments'] is not None:
            coverage['saved_valid'] += 1
            continue
        calls = entry['calls']
        low = read_replay_call(args.drafts, row, 'low', 'solve', paired_prompt(row, 'dsl'), run_digest, calls['low'])
        draft = deliver(low)
        if parse_dsl(draft) != choices['low']['submission']:
            raise ValueError(f'{row["id"]}: retained CAR draft differs from its solve receipt')
        receipt = read_replay_call(args.drafts, row, 'car_probe', 'probe', car_prompt(row, draft),
                                   run_digest, calls['car_probe'])
        judgments = parse_car(deliver(receipt), unwrap_answer=True)
        if judgments is None:
            coverage['missing'] += 1
        else:
            probe['judgments'] = judgments
            coverage['recovered_by_replay'] += 1
    return entries, gold, {k: contract[k] for k in PROFILE_KEYS}, panel, coverage


def evaluate_row(row, entry, gold, args, call, planner):
    low = entry['actions']['low']
    draft, judgments = low['submission'], entry['actions']['car_probe']['judgments']
    miss = gain = None
    hypotheses = []
    if args.stage == 'fit':
        assignment = hashlib.sha256(f'car-check-v1|{row["dataset"]}|{row["report"]}'.encode()).digest()
        check = tuple(CHECKS)[int.from_bytes(assignment[:4], 'big') % len(CHECKS)]
        gate = True
    else:
        miss = planner.predict(row, draft, judgments)
        check, gain, hypotheses = planner.check(row['question'], miss)
        threshold = planner.policy.get('gate', {}).get('threshold')
        gate = args.stage == 'calibration' or (threshold is not None and miss >= threshold and gain > 0)
    receipts = [entry['calls'][name] for name in ('low', 'car_probe')]
    candidate, status, receipt_path = draft, 'gate_closed', None
    if gate:
        blocks, pointer = evidence_pointer(row, draft, check)
        prompt = repair_prompt(row, draft, check, hypotheses, blocks, pointer)
        receipt, receipt_path = call(row, prompt)
        receipts.append(receipt)
        candidate, status = (accept_patch(row, draft, deliver(receipt), check, blocks, pointer)
                             if deliver(receipt) else (draft, 'repair_undelivered'))
    final = score(row, candidate, metric_dir=args.metric_dir, gold=gold)
    result = {'dataset': row['dataset'], 'id': row['id'], 'report': row['report'], 'strict': bool(final['strict']),
              'draft_correct': low['strict'], 'executable': final['executable'], 'submission': candidate,
              'repaired': status == 'edited', 'check': check, 'miss': miss, 'expected_gain': gain, 'attempted_repair': gate,
              'result': status, 'repair_receipt': receipt_path, 'cost': action_cost(receipts)}
    if args.stage == 'fit':
        initial = score(row, draft, metric_dir=args.metric_dir, gold=gold)
        result.update(draft=draft, judgments=judgments, fit_leaf=fit_leaf(row, draft, gold, initial) if not low['strict'] else None)
    return result


def collect(args):
    entries, gold, profile, panel, coverage = source_rows(args, args.stage)
    finqa.executor()  # The shared loader publishes its module before definitions finish.
    if args.dataset == 'tatqa':
        if args.metric_dir is None:
            raise ValueError('provide the pinned official TAT-QA metric directory')
        _metric_type(args.metric_dir)
    draft_config = read(args.drafts / 'run.json')
    if profile['opencode_sha256'] != digest_file(args.opencode) or args.base != draft_config['endpoint']:
        raise ValueError('use the same OpenCode executable and serving endpoint as the retained drafts')
    if profile['serve_sha256'] != digest_file(args.serving_profile):
        raise ValueError('repair must use the same frozen serving profile as the retained drafts')
    policy = read(args.policy) if args.policy else None
    if args.stage != 'fit':
        expected = 'fit' if args.stage == 'calibration' else 'frozen'
        if (not policy or policy.get('stage') != expected or policy['dataset'] != args.dataset
                or policy['profile'] != profile or policy['repair_output'] != args.repair_output):
            raise ValueError(f'{args.stage} requires the matched {expected} policy')
        protected_ids = set(policy['fit_ids']) | set(policy.get('calibration_ids', []))
        protected_reports = set(policy['fit_reports']) | set(policy.get('calibration_reports', []))
        if any(row['id'] in protected_ids or row['report'] in protected_reports for row, _ in entries):
            raise ValueError('CAR panel overlaps a fitting or calibration source')
    elif policy is not None:
        raise ValueError('fit collection uses randomized checks independently of any policy')
    planner = RepairPlanner(policy) if policy else None
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    import fcntl
    with (root / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        contract = root / 'run.json'
        freeze(contract, {'schema': 'finance-car-collection-v1', 'panel': panel, 'stage': args.stage,
                          'dataset': args.dataset, 'profile': profile, 'repair_output': args.repair_output,
                          'policy': digest_file(args.policy) if policy else None,
                          'draft_collection': digest_file(args.drafts / 'outcomes.jsonl'),
                          'probe_decoding': coverage})
        actor = OpenCode(root / 'repair', args.opencode, args.base, profile['model'], args.repair_output,
                         profile['context'], profile['temperature'])
        wait_service(args.base, profile['model'], 90)
        contract_digest = digest_file(contract)

        def call(row, prompt):
            case_id = hashlib.sha256(row['id'].encode()).hexdigest()[:24]
            target = root / 'calls' / case_id
            return recorded_call(actor, prompt, target, contract_digest), f'calls/{case_id}/call.json'

        def case(item):
            row, entry = item
            return evaluate_row(row, entry, gold[row_key(row)], args, call, planner)

        begin = time.monotonic()
        if args.workers > 1:
            actor.initialize_session_store()
        tmp = root / 'outcomes.jsonl.tmp'
        with ThreadPoolExecutor(max_workers=args.workers) as pool, tmp.open('w', encoding='utf-8') as out:
            attempts = correct = recovered = damaged = known_tokens = unknown_usage = 0
            charged_seconds = 0.
            for i, result in enumerate(pool.map(case, entries), 1):
                attempts += result['attempted_repair']
                correct += result['strict']
                recovered += result['strict'] and not result['draft_correct']
                damaged += result['draft_correct'] and not result['strict']
                known_tokens += result['cost']['known_tokens']
                unknown_usage += result['cost']['unknown_usage_calls']
                charged_seconds += result['cost']['summed_call_seconds']
                out.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + '\n')
                if i % 10 == 0 or i == len(entries):
                    print(f'CAR {args.stage} {i}/{len(entries)}', flush=True)
        tmp.replace(root / 'outcomes.jsonl')
        write_json(root / 'collection.json', {'questions': len(entries), 'correct': correct, 'probe_calls': len(entries),
                                              'probe_decoding': coverage,
                                              'repair_calls': attempts, 'recovered': recovered, 'damaged': damaged,
                                              'known_tokens': known_tokens, 'charged_call_seconds': charged_seconds,
                                              'total_tokens': known_tokens if not unknown_usage else None,
                                              'unknown_usage_calls': unknown_usage,
                                              'collection_wall_seconds': time.monotonic() - begin})


def fit_or_freeze(args):
    stage = 'fit' if args.action == 'fit' else 'calibration'
    rows, _, panel = read_panel(args.panel_root / stage, args.dataset)
    contract = read(args.collection / 'run.json')
    if contract['stage'] != stage or contract['panel'] != panel or contract['dataset'] != args.dataset:
        raise ValueError(f'{args.action} requires the matching {stage} collection')
    outcomes = load_lines(args.collection / 'outcomes.jsonl')
    strict_join(rows, outcomes)
    if args.action == 'fit':
        fitted = fit_policy(rows, outcomes, contract['profile'])
        fitted['repair_output'] = contract['repair_output']
    else:
        policy = read(args.policy)
        if digest_file(args.policy) != contract['policy'] or policy['stage'] != 'fit':
            raise ValueError('freeze requires the fit policy used for calibration trials')
        if not all(row['attempted_repair'] for row in outcomes):
            raise ValueError('every calibration question must carry a repair attempt before freezing')
        fitted = freeze_gate(policy, outcomes)
        fitted.update(calibration_reports=sorted({row['report'] for row in rows}),
                      calibration_ids=sorted(row['id'] for row in rows))
    fitted[f'{stage}_outcomes_sha256'] = digest_file(args.collection / 'outcomes.jsonl')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    freeze(args.output, fitted)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    for action in ('collect', 'fit', 'freeze'):
        command = commands.add_parser(action)
        command.add_argument('--panel-root', type=Path, required=True)
        command.add_argument('--dataset', choices=('finqa', 'tatqa'), required=True)
        command.add_argument('--output', type=Path, required=True)
        if action == 'collect':
            command.add_argument('stage', choices=('fit', 'calibration', 'eval'))
            command.add_argument('--drafts', type=Path, required=True)
            command.add_argument('--base', type=local_endpoint, required=True)
            command.add_argument('--serving-profile', type=Path, required=True)
            command.add_argument('--opencode', type=Path, default=Path.home() / '.opencode/bin/opencode')
            command.add_argument('--metric-dir', type=Path)
            command.add_argument('--workers', type=int, default=1)
            command.add_argument('--repair-output', type=int, default=384)
            command.add_argument('--policy', type=Path)
        else:
            command.add_argument('--collection', type=Path, required=True)
            if action == 'freeze':
                command.add_argument('--policy', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'collect':
        if args.workers < 1 or args.repair_output < 1:
            parser.error('positive worker and token limits are required')
        collect(args)
    else:
        fit_or_freeze(args)


if __name__ == '__main__':
    main()
