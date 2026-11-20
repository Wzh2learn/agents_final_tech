"""Load fixed CAR and BudgetVerify policies for fresh, matched OpenCode timing."""

import numpy as np

from benchmark_actions import car_prompt, deliver, digest_file, parse_car, select_case
import budget_policy
import car_adapter as car
from run_pilot import paired_prompt
from scoring import parse_dsl


MODEL = 'oda-fin-rl-8b'
CHECKPOINT = '948c22ea48f9bf93e5747f4211657fcad9cb0295'
OUTPUT = 4096
LOW_COST_MULTIPLE = 2


def select_car(row, call, planner):
    draft_reply = deliver(call('low', 'solve', paired_prompt(row, 'dsl')))
    draft = parse_dsl(draft_reply)
    probe = call('car_probe', 'probe', car_prompt(row, draft_reply))
    judgments = parse_car(deliver(probe), unwrap_answer=True)
    check, miss, gain, hypotheses, gate = car.plan_repair(row, draft, judgments, 'eval', planner)
    calls = ['low', 'car_probe']
    submission, decision = draft, 'gate_closed'
    if gate:
        blocks, pointer = car.evidence_pointer(row, draft, check)
        repair = deliver(call('car_repair', 'repair', car.repair_prompt(row, draft, check, hypotheses, blocks, pointer)))
        calls.append('car_repair')
        submission, decision = (car.accept_patch(row, draft, repair, check, blocks, pointer)
                                if repair else (draft, 'repair_undelivered'))
    return {'submission': submission, 'calls': calls, 'decision': decision, 'selected_stage': 'car',
            'selected_model': MODEL, 'check': check, 'miss': miss, 'expected_gain': gain}, row


def select_budgetverify(row, call, predict, feature_names):
    prompt = paired_prompt(row, 'dsl')
    low = call('low', 'solve', prompt)
    vector = budget_policy.features(row, parse_dsl(deliver(low)))
    if list(vector) != feature_names:
        raise ValueError('Live BudgetVerify feature ordering differs from calibration')
    choice = int(predict(np.asarray([list(vector.values())], dtype=float))[0])
    if not 0 <= choice < len(budget_policy.TIERS):
        raise ValueError('BudgetVerify predicted an unknown tier')
    tier = budget_policy.TIERS[choice]

    def dispatch(name, role, request):
        if name == 'low':
            if (role, request) != ('solve', prompt):
                raise ValueError('BudgetVerify changed the shared Low request')
            return low
        return call(name, role, request)

    actions, projections = select_case(row, [tier], dispatch, decode_verifier_answer=True)
    return {**actions[tier], 'selected_stage': f'budgetverify_{tier}', 'selected_model': MODEL}, projections.get(tier, row)


def budgetverify_point(policies, calibration):
    feasible = [(predict, point) for predict, point in policies
                if point['calibration_frontier'] and point['calibration']['normalized_token_cost'] is not None
                and point['calibration']['normalized_token_cost'] <= LOW_COST_MULTIPLE]
    if feasible:
        return max(feasible, key=lambda item: (item[1]['calibration']['accuracy'],
                                               -item[1]['calibration']['total_tokens'], -item[1]['lambda']))
    indices = np.flatnonzero(np.isfinite(calibration['tokens']).all(axis=1))
    routes = np.zeros(len(calibration['ids']), dtype=int)
    return (lambda values: np.zeros(len(values), dtype=int),
            {'lambda': None, 'config': {'constant': 'low'}, 'calibration_frontier': False,
             'calibration': budget_policy.route_stats(calibration, routes, indices)})


def checkpoint_digests(checkpoint):
    if checkpoint is None:
        return None
    if checkpoint.is_file():
        return {checkpoint.name: digest_file(checkpoint)}
    files = ('config.json', 'classification/config.json', 'classification/model.safetensors')
    return {name: digest_file(checkpoint / name) for name in files}


def load_car(root, dataset, profile, fit, calibration):
    policy_path = root / 'frozen_policy.json'
    policy = car.read(policy_path)
    fit_profile = {name: profile[name] for name in car.PROFILE_KEYS}
    if (policy['schema'], policy['stage'], policy['dataset'], policy['profile'], policy['repair_output']) != (
            'finance-car-v1', 'frozen', dataset, fit_profile, OUTPUT):
        raise ValueError('CAR requires a frozen policy for the matched local profile and dataset')
    for stage, split in (('fit', fit), ('calibration', calibration)):
        collection = car.read(root / stage / 'run.json')
        if (collection['schema'], collection['stage'], collection['dataset'],
                collection['profile'], collection['repair_output'], collection['draft_collection']) != (
                    'finance-car-collection-v1', stage, dataset, fit_profile, OUTPUT,
                    split['provenance']['outcomes.jsonl']):
            raise ValueError(f'CAR {stage} trials do not match the source draft collection')
        if (policy[f'{stage}_outcomes_sha256'] != digest_file(root / stage / 'outcomes.jsonl')
                or set(policy[f'{stage}_ids']) != set(split['ids'])):
            raise ValueError(f'CAR frozen policy does not match its {stage} trials')
    return car.RepairPlanner(policy), {
        'policy_sha256': digest_file(policy_path), 'ridge_alpha': policy['ridge']['alpha'],
        'gate_cutoff': policy['gate']['threshold'], 'fit_outcomes_sha256': policy['fit_outcomes_sha256'],
        'calibration_outcomes_sha256': policy['calibration_outcomes_sha256'],
        'probe_decoder': 'explicit_five_family_final_answer_v1',
    }


def load_local_baselines(args, benchmark, serving_profile_path):
    """Fit from fit/calibration only and return callable policies using public rows."""
    panel = benchmark / 'panel'
    fit, calibration = (budget_policy.read_split(panel / stage, benchmark / source, args.dataset,
                                                  decode_verifier_answer=True, metric_dir=args.metric_dir)
                        for stage, source in (('fit', 'reconciled_fit_v1/oda_fit_v1'),
                                              ('calibration', 'oda_calibration_v1')))
    profile = fit['profile']
    expected = {
        'model': MODEL, 'checkpoint': CHECKPOINT, 'endpoint': args.base,
        'serve_sha256': digest_file(serving_profile_path), 'opencode_sha256': digest_file(args.opencode),
        'seed': 17, 'context': 16384, 'temperature': .6,
        'output': {role: OUTPUT for role in ('solve', 'verify', 'probe')},
    }
    if (profile != calibration['profile'] or any(profile.get(name) != value for name, value in expected.items())
            or fit['feature_names'] != calibration['feature_names'] or fit['source_keys'] & calibration['source_keys']):
        raise ValueError('Live BudgetVerify requires disjoint fit/calibration and the matched ODA serving profile')
    planner, car_metadata = load_car(benchmark / 'car_oda_4096_v1' / args.dataset, args.dataset,
                                     profile, fit, calibration)
    checkpoint = getattr(args, 'tabfm_checkpoint', None)
    summary, policies = budget_policy.fit_policies(fit, calibration, checkpoint)
    predict, point = budgetverify_point(policies, calibration)
    cal_mask = np.isfinite(calibration['tokens']).all(axis=1)
    low_mean = float(calibration['tokens'][cal_mask, 0].mean())
    budget_metadata = {**summary, 'policy': point, 'calibration_mean_low_tokens': low_mean,
                       'calibration_token_cap_per_case': LOW_COST_MULTIPLE * low_mean,
                       'fit': fit['provenance'], 'calibration': calibration['provenance'],
                       'checkpoint_sha256': checkpoint_digests(checkpoint),
                       'verifier_decoder': 'exact_keep_or_use_new_final_answer_v1'}
    return {'car': lambda row, call: select_car(row, call, planner),
            'budgetverify': lambda row, call: select_budgetverify(row, call, predict, fit['feature_names'])}, {
                'car': car_metadata, 'budgetverify': budget_metadata}
