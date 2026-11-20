import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


@pytest.fixture
def live_cascade(monkeypatch):
    pilot = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(pilot))
    import live_author_cascade

    return live_author_cascade


def test_live_router_only_observes_queried_compiled_replies(live_cascade):
    live = live_cascade
    oda, qwen, deepseek = live.ARMS
    row = {'dataset': 'finqa', 'id': 'test', 'report': 'test', 'question': 'What is the combined revenue?',
           'pre_text': [], 'post_text': [], 'table': [['', '2022', '2023'], ['Revenue', '2', '3']]}
    requests = []
    replies = {live.MODELS[1]: 'Final program: table_sum(Revenue, "2022", "2023")',
               'low': 'Final program: add(2, 3)'}

    def call(name, role, prompt):
        assert role == 'solve' and prompt == live.paired_prompt(row, 'dsl')
        requests.append(name)
        return {'text': replies[name], 'exit_code': 0, 'errors': [], 'finish': ['stop']}

    class Router:
        def predict(self, questions, answers):
            assert questions == [(row['id'], live.public_features(row))]
            state, = answers
            if not requests:
                assert state == [None, None, None]
                return [qwen]
            assert state[1][1] == 5
            assert state[2] is None
            if len(requests) == 1:
                assert state[0] is None
                return [oda]
            assert state[0][1] == 5
            return [None]

        def select_answer(self, questions, answers):
            assert [answer is not None for answer in answers[0]] == [True, True, False]
            return [qwen]

    selected, projection = live.select_author_cascade(row, call, Router())
    assert selected['calls'] == requests == [live.MODELS[1], 'low']
    assert selected['selected_model'] == live.MODELS[1]
    assert selected['decision'] == 'table_scope'
    assert projection['table'] == [['typed_scope_step_0', '2', '3']]

    class UnqueriedWinner(Router):
        def select_answer(self, questions, answers):
            return [deepseek]

    requests.clear()
    with pytest.raises(RuntimeError, match='not requested'):
        live.select_author_cascade(row, call, UnqueriedWinner())


def test_loader_only_fits_train_and_uses_known_calibration_costs(live_cascade, monkeypatch, tmp_path):
    live = live_cascade
    scope = tmp_path / 'benchmark'
    oda_fit = scope / 'reconciled_fit_v1/oda_fit_v1'
    oda_cal = scope / 'oda_calibration_v1'
    campus_paths = {split: [scope / f'campus_{split}_{model}_v1' for model in live.MODELS[1:]]
                    for split in ('fit', 'calibration')}
    for directory in (oda_fit, oda_cal, *campus_paths['fit'], *campus_paths['calibration']):
        directory.mkdir(parents=True)
        (directory / 'outcomes.jsonl').write_text('{}\n')
    ledger = tmp_path / 'ledger.json'
    ledger.write_text('[{"index": 1}]')
    profiles = [{'checkpoint': 'oda', 'api_profile_sha256': None}]
    profiles.extend({'checkpoint': None, 'api_profile_sha256': model} for model in live.MODELS[1:])
    seen = []

    def read_pool(panel, dataset, paths, *, representation, metric_dir, campus_rows):
        assert representation == 'compiled' and dataset == 'finqa' and campus_rows == [{'index': 1}]
        assert panel.parent == scope / 'panel'
        seen.append(panel.name)
        if panel.name == 'fit':
            assert paths == [oda_fit, *campus_paths['fit']]
            return [('fit', ())], [[None] * 3], np.ones((1, 3)), [[]], np.full((1, 3), 21.), profiles
        assert panel.name == 'calibration' and paths == [oda_cal, *campus_paths['calibration']]
        tokens = np.array([[20, 30, 40], [50, np.nan, 60], [30, 40, 50]])
        return [(f'cal-{i}', ()) for i in range(3)], [[None] * 3] * 3, np.ones((3, 3)), [[], [], []], tokens, profiles

    def estimators(_q, _c, questions, answers, labels, tokens):
        assert questions == [('fit', ())]
        return 'quality', 'cost'

    class Router:
        gamma = .4

        def __init__(self, quality, cost, arms, target, *, strategies, force_order, cascade):
            assert (quality, cost, arms, target) == ('quality', 'cost', list(live.ARMS), 37.5)
            assert strategies == [(1, 16)] and force_order and not cascade

        def fit(self, questions, answers, labels, tokens):
            assert questions == [('cal-0', ()), ('cal-2', ())]
            assert tokens.tolist() == [[20, 30, 40], [30, 40, 50]]

        def get_lambdas(self):
            return [.2, .3]

    monkeypatch.setattr(live, 'read_pool', read_pool)
    monkeypatch.setattr(live, 'fit_estimators', estimators)
    monkeypatch.setattr(live, 'check_live_profiles', lambda *args: None)
    monkeypatch.setattr(live, 'upstream', lambda path: (
        None, None, SimpleNamespace(CascadeRouter=Router),
        SimpleNamespace(ConstantStrategy=lambda n, n_iterations: (n, n_iterations)),
    ))
    _, metadata = live.load_author_cascade(SimpleNamespace(dataset='finqa', metric_dir=None, upstream='source'),
                                           scope, tmp_path / 'serve.json', ledger)
    assert seen == ['fit', 'calibration']
    assert metadata['policy'] == 'cascade_routing_1.5'
    assert metadata['lambdas'] == [.2, .3]
    assert metadata['calibration_excluded_unknown'] == 1
    assert set(metadata['matched_input_sha256']) == {'fit', 'calibration'}
    assert len(metadata['campus_ledger_sha256']) == 64
    json.dumps(metadata, allow_nan=False)
