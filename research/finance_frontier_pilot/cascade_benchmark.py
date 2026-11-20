"""Apply the pinned Cascade Routing policy to matched independent solves."""

import argparse
from collections import Counter
from hashlib import sha256
from importlib import import_module
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import numpy as np

from benchmark_actions import digest_file, observable
from run_pilot import load_lines, write_json
from scoring import _canonical


REVISION = '9da6cf7da39c42148eae0178635e9211e5b67742'
ARMS = ('oda-8b', 'qwen-27b', 'deepseek')
NO_DETECTED_OVERLAP = 'no_pilot_or_reserved_context_detected'


def upstream(source):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(source), *args], text=True).strip()

    if git('rev-parse', 'HEAD') != REVISION or git('status', '--porcelain', '--', 'src/selection'):
        raise ValueError('Cascade Routing source must match the pinned clean checkout')
    # Load the routing submodules without importing the author's unrelated API clients.
    package = ModuleType('_pinned_selection')
    package.__path__ = [str((source / 'src/selection').resolve())]
    sys.modules[package.__name__] = package
    return tuple(import_module(f'{package.__name__}.{module}') for module in
                 ('quality_computer', 'cost_computer', 'cascade_router', 'lambda_strategy'))


def public_features(example):
    question = example['question'].casefold()
    return (len(question), sum(char.isdigit() for char in question),
            float('%' in question or 'percent' in question),
            len(example['table']), sum(len(line) for line in example['table']),
            sum(len(paragraph) for field in ('pre_text', 'post_text') for paragraph in example[field]))


def action_features(example, submission, *, execution_row=None):
    result = observable(example, submission, execution_row=execution_row)
    execution = result['execution']
    valid = execution['status'] == 'executed'
    bindings = result['bindings']
    value = _canonical(example['dataset'], execution.get('terminal_execution_answer'),
                       submission['scale']) if valid else None
    return ((1, int(valid), len(execution.get('steps', ())), len(bindings),
             sum(not binding['match_count'] for binding in bindings),
             sum(bool(binding['conflicts']) for binding in bindings),
             sum(binding['match_count'] > 1 for binding in bindings)), value)


def features(question, answers):
    values = [answer[1] for answer in answers if answer is not None and answer[1] is not None]
    return [*question[1], int(len(set(values)) > 1),
            *(number for answer in answers for number in (answer[0] if answer is not None else (0,) * 7))]


def fit_estimators(qmodule, cmodule, questions, answers, labels, tokens):
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    visible = [[answer if available else None for answer, available in zip(row, mask, strict=True)]
               for row in answers for mask in product((False, True), repeat=len(ARMS))]
    repeated = [question for question in questions for _ in range(2 ** len(ARMS))]
    matrix = np.asarray([features(q, a) for q, a in zip(repeated, visible, strict=True)])
    expanded = np.repeat(labels, 2 ** len(ARMS), axis=0)
    quality_models, cost_models = [], []
    public = [q[1] for q in questions]
    for idx in range(len(ARMS)):
        target = expanded[:, idx]
        classifier = None
        if len(set(target)) > 1:
            classifier = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500))
            classifier.fit(matrix, target)
        quality_models.append((classifier, float(target[0])))
        known = np.isfinite(tokens[:, idx])
        if not np.any(known):
            raise ValueError(f'no observed fit token charges for {ARMS[idx]}')
        cost_models.append(make_pipeline(StandardScaler(), Ridge(alpha=10)).fit(
            np.asarray(public)[known], tokens[known, idx]))

    class Quality(qmodule.BaseQualityComputer):
        def __init__(self):
            super().__init__(n_samples=128)
            self.cache = {}

        @property
        def is_independent(self):
            return False

        def predict(self, questions, model_answers):
            result = []
            for question, answers in zip(questions, model_answers, strict=True):
                key = question[0], tuple(answers)
                if key not in self.cache:
                    matrix = [features(question, answers)]
                    self.cache[key] = np.asarray([
                        default if model is None else model.predict_proba(matrix)[0, 1]
                        for model, default in quality_models])
                result.append(self.cache[key])
            return np.asarray(result), self.predict_covariances(questions, model_answers)

    class Cost(cmodule.BaseCostComputer):
        def __init__(self):
            super().__init__()
            self.cache = {}

        def predict(self, questions, model_answers=None):
            for question in questions:
                key = question[0]
                if key not in self.cache:
                    self.cache[key] = [max(1, model.predict([question[1]])[0]) for model in cost_models]
            return np.asarray([self.cache[question[0]] for question in questions])

    quality = Quality()
    quality.fit_covariances(questions, answers)
    return quality, Cost()


def replay_independent(path, run_digest, example, gold, outcome, managed_model, campus_rows, metric_dir,
                       representation):
    """Check the collected native result and select its raw or publicly compiled submission."""
    from benchmark_actions import action_cost, deliver
    from diagnose import read_replay_call
    from run_pilot import paired_prompt
    from scoring import parse_dsl, score

    native = outcome['actions']['independent']
    allowed = (['independent'],) if managed_model else (['independent'], ['low'])
    if native['calls'] not in allowed:
        raise ValueError(f'{path}: expected one native solve receipt for {example["id"]}')
    name = native['calls'][0]
    metadata = outcome['calls'][name]
    prompt = paired_prompt(example, 'dsl')
    if managed_model:
        from school_benchmark import replay_case

        slug = sha256(example['id'].encode('utf-8')).hexdigest()[:24]
        relative = Path('calls') / example['dataset'] / slug / name
        if metadata['path'] != (relative / 'provider_receipt.json').as_posix():
            raise ValueError(f'{path}: campus receipt location differs for {example["id"]}')
        receipt = replay_case(path / relative, run_digest, campus_rows, prompt, model_id=managed_model)
        fields = ('usage', 'elapsed_seconds', 'exit_code', 'finish', 'errors', 'provider_posts')
        if any(receipt[key] != metadata[key] for key in fields):
            raise ValueError(f'{path}: campus receipt metadata differs for {example["id"]}')
    else:
        receipt = read_replay_call(path, example, name, 'solve', prompt, run_digest, metadata)

    reply = deliver(receipt)
    raw = parse_dsl(reply)
    raw_score = score(example, raw, gold=gold, metric_dir=metric_dir)
    if (raw != native['submission'] or raw_score['strict'] != native['strict']
            or bool(raw_score['executable']) != native['executable']
            or action_cost([receipt]) != native['cost']):
        raise ValueError(f'{path}: recorded native result or solve cost differs for {example["id"]}')
    if representation == 'raw':
        return native, example

    from table_scope_replay import public_contract

    projected, submission, _, _ = public_contract(
        example, reply, stopped=bool(reply) and receipt['finish'] == ['stop'],
        preserve_literal_ratio=representation == 'literal_ratio_guarded')
    compiled = score(projected, submission, gold=gold, metric_dir=metric_dir)
    return {**native, 'submission': submission, 'strict': compiled['strict'],
            'executable': bool(compiled['executable'])}, projected


def read_pool(panel, dataset, paths, *, representation='raw', metric_dir=None, campus_rows=None):
    if representation not in ('raw', 'compiled', 'literal_ratio_guarded'):
        raise ValueError(f'Unknown representation: {representation}')
    if representation != 'raw' and campus_rows is None:
        raise ValueError('Compiled representation requires a frozen campus ledger')
    audit = campus_rows is not None
    if audit:
        from benchmark_actions import read_panel
        from school_benchmark import campus

        rows, gold, expected = read_panel(panel, dataset)
        public = {row['id']: row for row in rows}
        managed_models = (None, campus.QWEN_MODEL, campus.MODEL)
        if len(paths) != len(managed_models):
            raise ValueError('Expected ODA, campus Qwen and campus DeepSeek runs in that order')
    else:
        public = {row['id']: row for row in load_lines(panel / 'public.jsonl') if row['dataset'] == dataset}
        if not public:
            raise ValueError(f'empty {dataset} panel at {panel}')
        files = ('public.jsonl', 'references.jsonl')
        expected = {name: digest_file(panel / name) for name in files}
    received = []
    profiles = []
    for index, path in enumerate(paths):
        contract_path = path / 'run.json'
        contract = json.loads(contract_path.read_text(encoding='utf-8'))
        if contract['panel'] != expected or contract['dataset'] not in {None, dataset}:
            raise ValueError(f'collector did not use this panel: {path}')
        rows = [row for row in load_lines(path / 'outcomes.jsonl') if row['dataset'] == dataset]
        indexed = {row['id']: row for row in rows}
        if set(indexed) != set(public) or len(indexed) != len(rows):
            raise ValueError(f'independent solves do not cover the full selected panel: {path}')
        checkpoint = contract.get('checkpoint')
        managed_api = contract.get('api_profile_sha256')
        if bool(checkpoint) == bool(managed_api):
            raise ValueError(f'need one checkpoint or managed API identity: {path}')
        if audit:
            model = managed_models[index]
            if (contract['schema'] != 'finance-benchmark-actions-v1' or 'independent' not in contract['actions']
                    or bool(managed_api) != bool(model)
                    or (model and (contract['model'] != model or contract['endpoint'] != campus.BASE_URL))
                    or (model is None and contract['model'] != 'oda-fin-rl-8b')):
                raise ValueError(f'{path}: run identity differs from its {ARMS[index]} role')
            if any(outcome['report'] != public[ident]['report'] for ident, outcome in indexed.items()):
                raise ValueError(f'{path}: native solve report differs from the frozen panel')
        if managed_api and not any(row['calls']['independent']['provider_posts']
                                   and not row['calls']['independent']['exit_code']
                                   and not row['calls']['independent']['errors'] for row in rows):
            raise ValueError(f'managed arm delivered no provider responses: {path}')
        if audit:
            run_digest = digest_file(contract_path)
            received.append({
                ident: replay_independent(path, run_digest, example, gold[dataset, ident], indexed[ident],
                                          model, campus_rows, metric_dir, representation)
                for ident, example in public.items()
            })
        else:
            received.append({ident: (outcome['actions']['independent'], public[ident])
                             for ident, outcome in indexed.items()})
        profile = {key: contract[key] for key in ('model', 'serve_sha256', 'opencode_sha256',
                                                  'seed', 'context', 'output', 'temperature')}
        profile.update(checkpoint=checkpoint, api_profile_sha256=managed_api)
        if 'weights_precision' in contract:
            profile['weights_precision'] = contract['weights_precision']
        profiles.append(profile)
    questions = [(ident, public_features(example)) for ident, example in public.items()]
    answers = [[action_features(example, action['submission'], execution_row=projected)
                for action, projected in (arm[ident] for arm in received)]
               for ident, example in public.items()]
    quality = np.asarray([[arm[ident][0]['strict'] for arm in received] for ident in public], dtype=int)
    charges = [[arm[ident][0]['cost'] for arm in received] for ident in public]
    tokens = np.asarray([[item['total_tokens'] for item in row] for row in charges], dtype=float)
    return questions, answers, quality, charges, tokens, profiles


def read_oda_fallbacks(panel, dataset, run, metric_dir):
    """Replay the compiled 8B draft and the locally chosen free answer at recorded cost."""
    from benchmark_actions import action_cost, collect_case, read_panel
    from diagnose import read_replay_call

    rows, gold, identity = read_panel(panel, dataset)
    run_path = run / 'run.json'
    profile = json.loads(run_path.read_text(encoding='utf-8'))
    if (profile['panel'] != identity or profile['model'] != 'oda-fin-rl-8b'
            or 'compiled_fallback' not in profile['actions']):
        raise ValueError(f'{run}: expected matched ODA compiled-fallback receipts')
    run_digest = digest_file(run_path)
    records = [item for item in load_lines(run / 'outcomes.jsonl') if item['dataset'] == dataset]
    by_id = {item['id']: item for item in records}
    if len(by_id) != len(records) or by_id.keys() != {row['id'] for row in rows}:
        raise ValueError(f'{run}: compiled fallback outcomes differ from the panel')

    fallbacks = {}
    for row in rows:
        item = by_id[row['id']]
        calls = {}

        def call(name, actor, prompt):
            calls[name] = read_replay_call(run, row, name, actor, prompt, run_digest, item['calls'][name])
            return calls[name]

        actions = collect_case(row, gold[dataset, row['id']], ['compiled_fallback'], call, metric_dir)
        for name in ('contract_compile', 'compiled_fallback'):
            result = actions[name]
            cost = action_cost([calls[key] for key in result['calls']])
            if item['actions'][name] != {**result, 'cost': cost}:
                raise ValueError(f'{run}: {name} output or charge differs for {row["id"]}')
        fallbacks[row['id']] = item['actions']['compiled_fallback']
    return fallbacks


def contract_cascade(pool, local):
    """Retain an executable draft or numeric free answer, then try the compiled managed arms."""
    questions, answers, quality, charges, _, _ = pool
    decisions = []
    for index, (ident, _) in enumerate(questions):
        draft = local[ident]
        route = ['oda-8b']
        stage = 'compiled_oda' if draft['executable'] else 'free_oda'
        selected = ARMS[0]
        correct = draft['strict']
        executable = draft['executable']
        costs = [draft['cost']]
        if len(draft['calls']) == 2:
            route.append('oda-8b-free')
        if not executable and type(draft['submission']['answer']) not in (int, float):
            for arm in (1, 2):
                selected = ARMS[arm]
                route.append(selected)
                costs.append(charges[index][arm])
                stage = f'compiled_{selected}'
                correct = quality[index, arm]
                executable = bool(answers[index][arm][0][1])
                if executable:
                    break
        decisions.append({'id': ident, 'strict': int(correct), 'selected': selected, 'queried': route,
                          'selected_stage': stage, 'executable': executable,
                          'known_tokens': sum(cost['known_tokens'] for cost in costs),
                          'unknown_usage_calls': sum(cost['unknown_usage_calls'] for cost in costs),
                          'summed_call_seconds': sum(cost['summed_call_seconds'] for cost in costs)})
    return decisions


def realized(router, pool, initial=None):
    questions, answers, quality, charge, _, _ = pool
    seen = [[None] * len(ARMS) for _ in questions]
    if initial is not None:
        for state, actual in zip(seen, answers, strict=True):
            state[initial] = actual[initial]
    if router is not None:
        pending = list(range(len(questions)))
        for _ in ARMS:
            if not pending:
                break
            actions = router.predict([questions[i] for i in pending], [seen[i] for i in pending])
            continuing = []
            for idx, action in zip(pending, actions, strict=True):
                if action is not None:
                    model = ARMS.index(action)
                    if seen[idx][model] is not None:
                        raise RuntimeError('route repeated a model')
                    seen[idx][model] = answers[idx][model]
                    continuing.append(idx)
            pending = continuing
        if any(all(answer is None for answer in state) for state in seen):
            raise RuntimeError('route stopped before obtaining an answer')
        selected = [ARMS.index(arm) for arm in router.select_answer(questions, seen)]
    else:
        selected = [initial] * len(questions)
    decisions = []
    for idx, (question, state, best) in enumerate(zip(questions, seen, selected, strict=True)):
        called = [model for model, answer in enumerate(state) if answer is not None]
        spent = [charge[idx][model] for model in called]
        decisions.append({'id': question[0], 'strict': int(quality[idx, best]),
                          'executable': bool(answers[idx][best][0][1]),
                          'selected': ARMS[best], 'queried': [ARMS[model] for model in called],
                          'known_tokens': sum(item['known_tokens'] for item in spent),
                          'unknown_usage_calls': sum(item['unknown_usage_calls'] for item in spent),
                          'summed_call_seconds': sum(item['summed_call_seconds'] for item in spent)})
    return decisions


class NonexecutionCascade:
    """Advance along a fixed order until a program executes or models run out."""

    def __init__(self, order):
        self.order = tuple(order)

    def executable_answer(self, state):
        return next((index for index in self.order
                     if state[index] is not None and state[index][0][1]), None)

    def predict(self, _questions, seen):
        return [None if self.executable_answer(state) is not None
                else next((ARMS[index] for index in self.order if state[index] is None), None)
                for state in seen]

    def select_answer(self, _questions, seen):
        selected = []
        for state in seen:
            index = self.executable_answer(state)
            selected.append(ARMS[self.order[-1] if index is None else index])
        return selected


def summarize(decisions):
    usage = sum(row['unknown_usage_calls'] for row in decisions)
    known = sum(row['known_tokens'] for row in decisions)
    serial = np.asarray([row['summed_call_seconds'] for row in decisions])
    result = {'n': len(decisions), 'strict': sum(row['strict'] for row in decisions),
              'selected': dict(Counter(row['selected'] for row in decisions)),
              'queries': dict(Counter(arm for row in decisions for arm in row['queried'])),
              'tokens': known if not usage else None, 'known_tokens': known, 'unknown_usage_calls': usage,
              'mean_serial_call_seconds': float(serial.mean()),
              'median_serial_call_seconds': float(np.median(serial)),
              'p90_serial_call_seconds': float(np.percentile(serial, 90))}
    if all('executable' in row for row in decisions):
        result['executable'] = sum(row['executable'] for row in decisions)
        result['strict_and_executable'] = sum(row['strict'] and row['executable'] for row in decisions)
    if all('selected_stage' in row for row in decisions):
        result['selected_stage'] = dict(Counter(row['selected_stage'] for row in decisions))
    return result


def literal_ratio_sensitivity(evaluation, guarded, policies, exposure):
    """Regrade fixed selections under a terminal-value change with identical calls."""
    questions, answers, _, charges, _, profiles = evaluation
    other_questions, other_answers, other_strict, other_charges, _, other_profiles = guarded
    if questions != other_questions or charges != other_charges or profiles != other_profiles:
        raise ValueError('Literal-ratio sensitivity requires unchanged questions, calls and profiles')
    indices = {ident: i for i, (ident, _) in enumerate(questions)}
    for before, after in zip(answers, other_answers, strict=True):
        if any(left[0][1] != right[0][1] for left, right in zip(before, after, strict=True)):
            raise ValueError('Literal-ratio sensitivity must preserve executability')

    effects = {}
    for name, policy in policies.items():
        paired = []
        for item in policy['items']:
            ident = item['id']
            index = indices[ident]
            arm = ARMS.index(item['selected'])
            free = arm == 0 and 'oda-8b-free' in item['queried']
            before = item['strict']
            after = before if free else int(other_strict[index, arm])
            changed = not free and answers[index][arm][1] != other_answers[index][arm][1]
            if before != after and not changed:
                raise ValueError('A sensitivity score changed without a terminal-value change')
            paired.append((ident, before, after, changed))
        groups = {'all': paired}
        independent = [item for item in paired if exposure[item[0]] == NO_DETECTED_OVERLAP]
        if independent:
            groups['no_detected_overlap'] = independent
        effects[name] = {
            group: {'n': len(rows), 'baseline_correct': sum(before for _, before, _, _ in rows),
                    'guarded_correct': sum(after for _, _, after, _ in rows),
                    'gains': sum(after > before for _, before, after, _ in rows),
                    'harms': sum(after < before for _, before, after, _ in rows),
                    'changed_values': sum(changed for _, _, _, changed in rows)}
            for group, rows in groups.items()
        }
    return {'rule': 'Keep the final ×100 when a compiled FinQA percent program is two steps and divides two bare literals.',
            'policies': effects}


def compare(args):
    representation = getattr(args, 'representation', 'raw')
    metric_dir = getattr(args, 'metric_dir', None)
    ledger_path = getattr(args, 'campus_ledger', None)
    campus_rows = None
    if ledger_path is not None:
        ledger = ledger_path.read_bytes()
        campus_rows = json.loads(ledger)
        if not isinstance(campus_rows, list) or any(row['index'] != index
                                                   for index, row in enumerate(campus_rows, 1)):
            raise ValueError('expected the frozen campus ledger in provider index order')
        if args.dataset == 'tatqa' and metric_dir is None:
            raise ValueError('TAT-QA receipt replay requires the official metric directory')
    elif representation == 'compiled':
        raise ValueError('Compiled representation requires a frozen campus ledger')

    qlib, clib, cascade, strategy = upstream(args.upstream)
    def load(part, runs, selected_representation=representation):
        return read_pool(args.panels / part, args.dataset, runs, representation=selected_representation,
                         metric_dir=metric_dir, campus_rows=campus_rows)

    fit = load('fit', args.fit)
    calibration = load('calibration', args.calibration)
    if fit[-1] != calibration[-1]:
        raise ValueError('model serving contracts differ between splits')
    if len({item['checkpoint'] or item['api_profile_sha256'] for item in fit[-1]}) != len(ARMS):
        raise ValueError('distinct model identities required for the three roles')
    fit_ids = {q[0] for q in fit[0]}
    cal_ids = {q[0] for q in calibration[0]}
    if fit_ids & cal_ids:
        raise ValueError('fit, calibration and evaluation IDs must be disjoint')
    if campus_rows is not None:
        np.random.seed(17)
    quality, cost = fit_estimators(qlib, clib, fit[0], fit[1], fit[2], fit[4])
    keep = np.isfinite(calibration[4]).all(axis=1)
    if np.count_nonzero(keep) < 2:
        raise ValueError('calibration requires at least two all-model known-usage tasks')
    cq, ca = [[row for row, ok in zip(group, keep, strict=True) if ok] for group in calibration[:2]]
    cy, ct = calibration[2][keep], calibration[4][keep]
    fitted_routes = []
    for budget in args.budgets:
        target = float(budget * np.mean(ct[:, 0]))
        for fixed_start in (False, True):
            np.random.seed(17)
            router = cascade.CascadeRouter(quality, cost, list(ARMS), target,
                                           strategies=[strategy.ConstantStrategy(1, n_iterations=16)],
                                           force_order=True, cascade=fixed_start)
            router.fit(cq, ca, cy, ct)
            key = ('ordered_cascade' if fixed_start else 'cascade_routing') + f'_{budget:g}'
            fitted_routes.append((key, target, fixed_start, router, np.random.get_state()))

    evaluation = load('eval', args.eval)
    if fit[-1] != evaluation[-1]:
        raise ValueError('model serving contracts differ between splits')
    if (fit_ids | cal_ids) & {q[0] for q in evaluation[0]}:
        raise ValueError('fit, calibration and evaluation IDs must be disjoint')
    exposure_path = args.panels / 'eval/exposure.json'
    exposure = {row['id']: row['exposure'] for row in json.loads(exposure_path.read_text(encoding='utf-8'))
                if row['dataset'] == args.dataset}

    def record(decisions):
        strata = {group: summarize([row for row in decisions if exposure[row['id']] == group])
                  for group in sorted({exposure[row['id']] for row in decisions})}
        return {'all': summarize(decisions), 'exposure': strata, 'items': decisions}

    policies = {f'always_{arm}': record(realized(None, evaluation, idx)) for idx, arm in enumerate(ARMS)}
    if campus_rows is not None:
        for name, order in (('nonexecution_8b_qwen_deepseek', (0, 1, 2)),
                            ('nonexecution_deepseek_qwen', (2, 1))):
            policies[name] = record(realized(NonexecutionCascade(order), evaluation))
    if representation == 'compiled':
        local_fallbacks = read_oda_fallbacks(args.panels / 'eval', args.dataset, args.eval[0], metric_dir)
        policies['contract_8b_free_qwen_deepseek'] = record(contract_cascade(evaluation, local_fallbacks))
    fixed_sensitivity = None
    if representation == 'compiled' and args.dataset == 'finqa':
        guarded = load('eval', args.eval, 'literal_ratio_guarded')
        fixed_sensitivity = literal_ratio_sensitivity(evaluation, guarded, policies, exposure)
    for key, target, fixed_start, router, prediction_state in fitted_routes:
        np.random.set_state(prediction_state)
        result = record(realized(router, evaluation, 0 if fixed_start else None))
        result.update(target_mean_tokens=target, lambdas=router.get_lambdas(), tie_mix=float(router.gamma))
        policies[key] = result
    report = {'dataset': args.dataset, 'author_revision': REVISION, 'profiles': fit[-1],
              'fit_n': len(fit[0]), 'calibration_n': len(cq), 'calibration_excluded_unknown': int(sum(~keep)),
              'policy': 'Author CascadeRouter and ConstantStrategy with public execution features. '
                        'Ordered cascade begins with 8B and visits subsequent models consecutively.',
              'latency': 'Per-question sum of selected call receipts. Online routing latency is unmeasured.',
              'policies': policies}
    if fixed_sensitivity is not None:
        report['literal_ratio_sensitivity'] = fixed_sensitivity
    if campus_rows is not None:
        report['representation'] = representation
        report['campus_ledger_sha256'] = sha256(ledger).hexdigest()
        report['matched_input_sha256'] = {
            part: sha256(json.dumps({'questions': pool[0], 'charges': pool[3],
                                     'runs': [digest_file(run / 'outcomes.jsonl') for run in runs]},
                                    sort_keys=True, allow_nan=False).encode('utf-8')).hexdigest()
            for part, runs, pool in (('fit', args.fit, fit), ('calibration', args.calibration, calibration),
                                     ('eval', args.eval, evaluation))
        }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--panels', type=Path, required=True)
    parser.add_argument('--dataset', choices=('finqa', 'tatqa'), required=True)
    parser.add_argument('--representation', choices=('raw', 'compiled'), default='raw')
    parser.add_argument('--metric-dir', type=Path, help='Official TAT-QA metric checkout for receipt replay')
    parser.add_argument('--campus-ledger', type=Path, help='Immutable gateway ledger snapshot for matched receipt replay')
    for partition in ('fit', 'calibration', 'eval'):
        parser.add_argument(f'--{partition}', type=Path, nargs=len(ARMS), required=True,
                            metavar=('ODA_8B', 'QWEN_27B', 'DEEPSEEK'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--budgets', type=float, nargs='+', default=(1.25, 1.5, 2, 3))
    args = parser.parse_args()
    if args.output.exists() or any(not np.isfinite(budget) or budget <= 1 for budget in args.budgets):
        parser.error('require a fresh report path and finite budget multipliers above 1')
    if args.representation == 'compiled' and args.campus_ledger is None:
        parser.error('--representation compiled requires --campus-ledger')
    if args.campus_ledger is not None and args.dataset == 'tatqa' and args.metric_dir is None:
        parser.error('TAT-QA receipt replay requires --metric-dir')
    write_json(args.output, compare(args))


if __name__ == '__main__':
    main()
