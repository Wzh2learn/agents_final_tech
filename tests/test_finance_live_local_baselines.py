import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


@pytest.fixture
def baselines(monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(source))
    import live_local_baselines

    return live_local_baselines


@pytest.fixture
def question():
    return {'dataset': 'finqa', 'id': 'fixture', 'report': 'fixture-report',
            'question': 'What is the total?', 'pre_text': [], 'post_text': [],
            'table': [['Row', '2023'], ['Revenue', '3']]}


def receipt(text):
    return {'text': text, 'exit_code': 0, 'errors': []}


@pytest.mark.parametrize('tier', [0, 1, 2])
def test_budgetverify_dispatches_shared_low_once_and_only_chosen_tier(baselines, question, tier):
    calls = []

    def dispatch(name, role, prompt):
        calls.append((name, role))
        assert question['question'] in prompt
        return receipt('Final program: add(1, 2)' if role == 'solve' else '<answer>KEEP</answer>')

    draft = baselines.parse_dsl('Final program: add(1, 2)')
    features = baselines.budget_policy.features(question, draft)

    def predict(matrix):
        assert matrix.tolist() == [list(features.values())]
        return [tier]

    selected, projection = baselines.select_budgetverify(question, dispatch, predict, list(features))
    expected = [[], [('mid', 'verify')], [('high_solve', 'solve'), ('high_compare', 'verify')]][tier]
    assert calls == [('low', 'solve'), *expected]
    assert selected['calls'] == [name for name, _ in calls]
    assert selected['selected_model'] == baselines.MODEL
    assert projection == question
    if tier == 2:
        assert selected['comparison'] == 'KEEP'


@pytest.mark.parametrize('miss, gain, repair', [(.49, .2, False), (.5, 0, False), (.5, .2, True)])
def test_car_uses_frozen_gate_and_decodes_probe(baselines, question, miss, gain, repair):
    draft = 'Final program: add(1, 2)'
    checks = '\n'.join(f'{name}: yes, rationale: generated from fixture'
                       for name in baselines.car.FAMILIES)
    calls = []

    def dispatch(name, role, prompt):
        calls.append((name, role))
        if role == 'probe':
            assert draft in prompt
        return receipt({'solve': draft, 'probe': f'<answer>\n{checks}\n</answer>', 'repair': ''}[role])

    def predict(row, parsed, judgments):
        assert row == question and parsed['program'] == 'add(1, 2)'
        assert {name for name, decision in judgments.items() if decision['suspect']} == set(baselines.car.FAMILIES)
        return miss

    planner = SimpleNamespace(predict=predict, check=lambda *_: ('Binding', gain, []),
                              policy={'gate': {'threshold': .5}})
    selected, projection = baselines.select_car(question, dispatch, planner)
    expected = [('low', 'solve'), ('car_probe', 'probe')]
    assert calls == expected + ([('car_repair', 'repair')] if repair else [])
    assert selected['decision'] == ('repair_undelivered' if repair else 'gate_closed')
    assert selected['calls'] == [name for name, _ in calls]
    assert projection == question


def test_budgetverify_point_selects_matched_calibration_frontier(baselines):
    def point(alpha, accuracy, tokens, frontier=True):
        return None, {'lambda': alpha, 'calibration_frontier': frontier,
                      'calibration': {'accuracy': accuracy, 'total_tokens': tokens,
                                      'normalized_token_cost': tokens / 100}}

    points = [point(.04, .55, 195), point(.05, .55, 170), point(.03, .7, 201), point(.06, .8, 175, False)]
    assert baselines.budgetverify_point(points, None) == points[1]


def test_checkpoint_digests_cover_classification_directory(baselines, tmp_path):
    (tmp_path / 'classification').mkdir()
    (tmp_path / 'regression').mkdir()
    files = ['config.json', 'classification/config.json', 'classification/model.safetensors']
    for name in [*files, 'regression/model.safetensors']:
        (tmp_path / name).write_text(name, encoding='utf-8')
    assert baselines.checkpoint_digests(tmp_path) == {
        name: baselines.digest_file(tmp_path / name) for name in files}


def test_loader_uses_only_matched_fit_and_calibration_even_for_eval(baselines, monkeypatch, tmp_path):
    staging = tmp_path / 'car_oda_4096_v1' / 'finqa'
    serve, opencode = tmp_path / 'serve.json', tmp_path / 'opencode'
    for path in [serve, opencode]:
        path.write_text('fixture', encoding='utf-8')
    profile = {'model': baselines.MODEL, 'checkpoint': baselines.CHECKPOINT, 'endpoint': 'fixture',
               'serve_sha256': baselines.digest_file(serve), 'opencode_sha256': baselines.digest_file(opencode),
               'seed': 17, 'context': 16384, 'temperature': .6,
               'output': {role: 4096 for role in ('solve', 'verify', 'probe')}}
    car_profile = {name: profile[name] for name in baselines.car.PROFILE_KEYS}
    policy = {'schema': 'finance-car-v1', 'stage': 'frozen', 'dataset': 'finqa', 'profile': car_profile,
              'repair_output': 4096, 'gate': {'threshold': .3}, 'ridge': {'alpha': .01}}
    stages = ('fit', 'calibration')
    for stage in stages:
        directory = staging / stage
        directory.mkdir(parents=True)
        outcomes = directory / 'outcomes.jsonl'
        outcomes.write_text(stage, encoding='utf-8')
        contract = {'schema': 'finance-car-collection-v1', 'stage': stage, 'dataset': 'finqa',
                    'profile': car_profile, 'draft_collection': f'draft-{stage}', 'repair_output': 4096}
        (directory / 'run.json').write_text(json.dumps(contract), encoding='utf-8')
        policy[f'{stage}_outcomes_sha256'] = baselines.digest_file(outcomes)
        policy[f'{stage}_ids'] = [stage]
    (staging / 'frozen_policy.json').write_text(json.dumps(policy), encoding='utf-8')
    opened = []

    def read_split(panel, run, dataset, **kwargs):
        stage = panel.name
        assert stage in stages and dataset == 'finqa' and kwargs['decode_verifier_answer']
        assert run == tmp_path / ('reconciled_fit_v1/oda_fit_v1' if stage == 'fit' else 'oda_calibration_v1')
        opened.append(stage)
        return {'profile': profile, 'feature_names': ['fixture'], 'ids': [stage], 'source_keys': {stage},
                'tokens': np.asarray([[10, 15, 30]]), 'provenance': {'outcomes.jsonl': f'draft-{stage}'}}

    point = {'lambda': .02, 'calibration_frontier': True,
             'calibration': {'accuracy': 1, 'total_tokens': 15, 'normalized_token_cost': 1.5}}
    monkeypatch.setattr(baselines.budget_policy, 'read_split', read_split)
    monkeypatch.setattr(baselines.budget_policy, 'fit_policies', lambda *_: ({}, [(None, point)]))
    monkeypatch.setattr(baselines.car, 'RepairPlanner', lambda saved: saved)
    args = SimpleNamespace(dataset='finqa', stage='eval', base='fixture', opencode=opencode, metric_dir=None)
    selectors, metadata = baselines.load_local_baselines(args, tmp_path, serve)
    assert opened == list(stages) and set(selectors) == {'car', 'budgetverify'}
    assert metadata['car']['ridge_alpha'] == .01
    assert metadata['budgetverify']['calibration_token_cap_per_case'] == 20
    (staging / 'calibration' / 'outcomes.jsonl').write_text('changed', encoding='utf-8')
    with pytest.raises(ValueError, match='frozen policy does not match its calibration trials'):
        baselines.load_local_baselines(args, tmp_path, serve)
