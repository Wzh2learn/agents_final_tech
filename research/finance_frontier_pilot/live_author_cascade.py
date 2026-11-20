"""Fit one official-grid Cascade Router point and dispatch its live choices."""

from hashlib import sha256
import json

import numpy as np

from benchmark_actions import deliver, digest_file
from cascade_benchmark import ARMS, REVISION, action_features, fit_estimators, public_features, read_pool, upstream
from run_pilot import paired_prompt
from school_benchmark import campus
from table_scope_replay import public_contract


MODELS = ('oda-fin-rl-8b', campus.QWEN_MODEL, campus.MODEL)
REQUESTS = ('low', *MODELS[1:])
BUDGET_MULTIPLE = 1.5
SEED = 17


def select_author_cascade(row, call, router):
    """Expose a model's public features to the author router only after its reply."""
    question = (row['id'], public_features(row))
    observed = [None] * len(ARMS)
    responses = {}
    calls = []
    for _ in ARMS:
        arm, = router.predict([question], [observed])
        if arm is None:
            break
        if arm in responses:
            raise RuntimeError('Cascade route repeated a model')
        index = ARMS.index(arm)
        name = REQUESTS[index]
        receipt = call(name, 'solve', paired_prompt(row, 'dsl'))
        calls.append(name)
        reply = deliver(receipt)
        projection, submission, decision, cells = public_contract(
            row, reply, stopped=bool(reply) and receipt['finish'] == ['stop'])
        observed[index] = action_features(row, submission, execution_row=projection)
        responses[arm] = ({'submission': submission, 'decision': decision, 'source_cells': cells,
                           'selected_model': MODELS[index],
                           'selected_stage': 'compiled_oda' if name == 'low' else f'compiled_{name}'}, projection)
    if not responses:
        raise RuntimeError('Cascade route stopped before obtaining a reply')
    winner, = router.select_answer([question], [observed])
    if winner not in responses:
        raise RuntimeError('Cascade selected a model whose reply was not requested')
    selected, projection = responses[winner]
    return {**selected, 'calls': calls}, projection


def check_live_profiles(args, benchmark, serving_profile_path, profiles, oda_runs):
    local = json.loads(serving_profile_path.read_bytes())
    opencode_sha256 = digest_file(args.opencode)
    oda = profiles[0]
    if (oda['model'] != local['model'] or oda['checkpoint'] != local['checkpoint']
            or oda['serve_sha256'] != digest_file(serving_profile_path)
            or (oda['seed'], oda['context'], oda['output']['solve'], oda['temperature']) != (SEED, 16384, 4096, .6)
            or any(json.loads((run / 'run.json').read_bytes())['endpoint'] != args.base for run in oda_runs)):
        raise ValueError('Live ODA solve profile differs from the author Cascade fit/calibration profile')
    if any(profile['opencode_sha256'] != opencode_sha256 for profile in profiles):
        raise ValueError('Live OpenCode executable differs from the author Cascade fit/calibration profiles')
    for profile, model, option in zip(profiles[1:], MODELS[1:], ('qwen_api_profile', 'deepseek_api_profile'), strict=True):
        provider_path = getattr(args, option, None) or benchmark / 'managed_profiles' / f'{model}.json'
        if profile['model'] != model or profile['api_profile_sha256'] != digest_file(provider_path):
            raise ValueError(f'Live {model} profile differs from the author Cascade fit/calibration profile')


def load_author_cascade(args, benchmark, serving_profile_path, campus_ledger_path):
    """Bind live identities and fit the compiled, adaptive-start 1.5x policy on TRAIN only."""
    ledger = campus_ledger_path.read_bytes()
    campus_rows = json.loads(ledger)
    if not isinstance(campus_rows, list) or any(row['index'] != index for index, row in enumerate(campus_rows, 1)):
        raise ValueError('Author Cascade requires a campus ledger in provider index order')
    if args.dataset == 'tatqa' and args.metric_dir is None:
        raise ValueError('Author Cascade TAT-QA replay requires the pinned official metric directory')

    oda_fit = benchmark / 'reconciled_fit_v1/oda_fit_v1'
    oda_calibration = benchmark / 'oda_calibration_v1'
    runs = {
        split: [oda_run, *(benchmark / f'campus_{split}_{model}_v1' for model in MODELS[1:])]
        for split, oda_run in (('fit', oda_fit), ('calibration', oda_calibration))
    }
    qmodule, cmodule, cascade, strategy = upstream(args.upstream)
    pools = {split: read_pool(benchmark / 'panel' / split, args.dataset, paths, representation='compiled',
                              metric_dir=args.metric_dir, campus_rows=campus_rows)
             for split, paths in runs.items()}
    fit, calibration = pools['fit'], pools['calibration']
    profiles = fit[-1]
    if profiles != calibration[-1]:
        raise ValueError('Author Cascade fit and calibration serving profiles differ')
    if len({profile['checkpoint'] or profile['api_profile_sha256'] for profile in profiles}) != len(ARMS):
        raise ValueError('Author Cascade requires three distinct model identities')
    if {q[0] for q in fit[0]} & {q[0] for q in calibration[0]}:
        raise ValueError('Author Cascade fit and calibration IDs must be disjoint')
    check_live_profiles(args, benchmark, serving_profile_path, profiles, (oda_fit, oda_calibration))

    keep = np.isfinite(calibration[4]).all(axis=1)
    if np.count_nonzero(keep) < 2:
        raise ValueError('Author Cascade calibration requires at least two all-model known-usage cases')
    cq, ca = [[row for row, ok in zip(group, keep, strict=True) if ok] for group in calibration[:2]]
    cy, ct = calibration[2][keep], calibration[4][keep]
    target = float(BUDGET_MULTIPLE * np.mean(ct[:, 0]))
    caller_state = np.random.get_state()
    try:
        np.random.seed(SEED)
        quality, cost = fit_estimators(qmodule, cmodule, fit[0], fit[1], fit[2], fit[4])
        np.random.seed(SEED)
        router = cascade.CascadeRouter(quality, cost, list(ARMS), target,
                                       strategies=[strategy.ConstantStrategy(1, n_iterations=16)],
                                       force_order=True, cascade=False)
        router.fit(cq, ca, cy, ct)
        prediction_state = np.random.get_state()
    finally:
        np.random.set_state(caller_state)

    def select(row, call):
        nonlocal prediction_state
        if row['dataset'] != args.dataset:
            raise ValueError('Live question dataset differs from the fitted author Cascade')
        caller_state = np.random.get_state()
        np.random.set_state(prediction_state)
        try:
            return select_author_cascade(row, call, router)
        finally:
            prediction_state = np.random.get_state()
            np.random.set_state(caller_state)

    input_digests = {}
    for split, pool in pools.items():
        evidence = {'questions': pool[0], 'charges': pool[3],
                    'runs': [digest_file(path / 'outcomes.jsonl') for path in runs[split]]}
        input_digests[split] = sha256(json.dumps(evidence, sort_keys=True, allow_nan=False).encode('utf-8')).hexdigest()
    metadata = {'author_revision': REVISION, 'dataset': args.dataset, 'representation': 'compiled',
                'policy': f'cascade_routing_{BUDGET_MULTIPLE:g}', 'adaptive_start': True, 'seed': SEED,
                'budget_multiple': BUDGET_MULTIPLE, 'target_mean_tokens': target,
                'lambdas': router.get_lambdas(), 'tie_mix': float(router.gamma),
                'fit_n': len(fit[0]), 'calibration_n': len(cq), 'calibration_excluded_unknown': int(sum(~keep)),
                'profiles': profiles, 'matched_input_sha256': input_digests,
                'campus_ledger_sha256': sha256(ledger).hexdigest()}
    return select, metadata
