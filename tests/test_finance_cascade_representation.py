from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def runs(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(source))
    from benchmark_actions import action_cost, collect_case, digest_file
    from run_pilot import usage_from, write_json
    from school_benchmark import bind_provider_result, campus

    row = {'dataset': 'finqa', 'id': 'question', 'report': 'report',
           'question': 'What is the combined total?', 'pre_text': [], 'post_text': [],
           'table': [['', '2022', '2023'], ['Revenue', '2', '3'], ['Debt', '30', '40']]}
    gold = {'exe_ans': 35}
    panel = tmp_path / 'panel'
    panel.mkdir()

    def write_line(path, value):
        path.write_bytes((json.dumps(value) + '\n').encode())

    write_line(panel / 'public.jsonl', row)
    write_line(panel / 'references.jsonl', {k: row[k] for k in ('dataset', 'id')} | {'gold': gold})
    expected = {name: digest_file(panel / name) for name in ('public.jsonl', 'references.jsonl')}
    ledger, paths = [], []
    for i, (model, program) in enumerate((
        ('oda-fin-rl-8b', 'table_sum(Revenue, "2022", "2023"), add(#0, 30)'),
        (campus.QWEN_MODEL, 'add(34, 1)'),
        (campus.MODEL, 'add(31, 1)'),
    )):
        run = tmp_path / model
        run.mkdir()
        paths.append(run)
        actions = ['independent'] if i else ['low', 'independent', 'compiled_fallback']
        run_path = run / 'run.json'
        identity = {'api_profile_sha256': model, 'endpoint': campus.BASE_URL} if i else {'checkpoint': 'local'}
        write_json(run_path, {
            'schema': 'finance-benchmark-actions-v1', 'panel': expected,
            'dataset': 'finqa', 'actions': actions, 'model': model,
            'serve_sha256': model, 'opencode_sha256': 'test-opencode',
            'seed': 17, 'context': 16384, 'output': {'solve': 4096}, 'temperature': .6, **identity,
        })
        run_digest = digest_file(run_path)
        calls = {}

        def capture(name, actor, prompt):
            relative = Path('calls/finqa') / sha256(row['id'].encode()).hexdigest()[:24] / name
            target = run / relative
            target.mkdir(parents=True)
            reply = 'Final program: ' + program
            events = [{'type': 'text', 'part': {'text': reply}}, {
                'type': 'step_finish', 'part': {'reason': 'stop', 'tokens': {'input': 5, 'output': 9, 'total': 14}},
            }]
            call = {'text': reply, 'usage': usage_from(events), 'elapsed_seconds': 1.5, 'exit_code': 0,
                    'finish': ['stop'], 'errors': []}
            write_json(target / 'request.json', {'prompt_sha256': sha256(prompt.encode()).hexdigest(),
                                                 'run_contract': run_digest, 'actor': actor})
            (target / 'prompt.txt').write_bytes((prompt + '\n').encode())
            (target / 'raw.jsonl').write_bytes(''.join(json.dumps(e) + '\n' for e in events).encode())
            write_json(target / 'call.json', call)
            file = 'call.json'
            if i:
                provider = {'index': i, 'state': 'complete', 'model': model, 'http_status': 200,
                            'usage': {'prompt_tokens': 21, 'completion_tokens': 21, 'total_tokens': 42}}
                ledger.append(provider)
                call = bind_provider_result(target, run_digest, provider, call, model_id=model)
                file = 'provider_receipt.json'
            fields = ('usage', 'elapsed_seconds', 'exit_code', 'finish', 'errors')
            calls[name] = {key: call[key] for key in fields}
            if i:
                calls[name]['provider_posts'] = call['provider_posts']
            calls[name]['path'] = (relative / file).as_posix()
            return call

        native = collect_case(row, gold, actions, capture, None)
        for result in native.values():
            result['cost'] = action_cost([calls[name] for name in result['calls']])
        write_line(run / 'outcomes.jsonl',
                   {k: row[k] for k in ('dataset', 'id', 'report')} | {'actions': native, 'calls': calls})
    return panel, paths, ledger


def test_compiler_changes_labels_and_projected_execution_with_identical_costs(runs):
    from cascade_benchmark import read_oda_fallbacks, read_pool

    panel, paths, ledger = runs
    raw = read_pool(panel, 'finqa', paths)
    audited = read_pool(panel, 'finqa', paths, campus_rows=ledger)
    compiled = read_pool(panel, 'finqa', paths, representation='compiled', campus_rows=ledger)
    assert raw[0] == audited[0] == compiled[0]
    assert raw[1] == audited[1]
    assert raw[2].tolist() == audited[2].tolist() == [[0, 1, 0]]
    assert compiled[2].tolist() == [[1, 1, 0]]
    assert raw[3] == audited[3] == compiled[3]
    assert compiled[4].tolist() == [[14, 42, 42]]
    ode, number = compiled[1][0][0]
    assert number == 35 and ode[:5] == (1, 1, 2, 1, 0)
    fallback = read_oda_fallbacks(panel, 'finqa', paths[0], None)['question']
    assert fallback['strict'] and fallback['executable'] and fallback['calls'] == ['low']
    assert fallback['cost'] == compiled[3][0][0]


def test_compiler_refuses_wrong_role_or_unreconciled_receipt(runs):
    from cascade_benchmark import read_pool

    panel, paths, ledger = runs
    with pytest.raises(ValueError, match='qwen-27b role'):
        read_pool(panel, 'finqa', [paths[0], paths[2], paths[1]],
                  representation='compiled', campus_rows=ledger)
    wrong_ledger = [dict(ledger[0], http_status=500), ledger[1]]
    with pytest.raises(ValueError, match='no matching authoritative ledger row'):
        read_pool(panel, 'finqa', paths, representation='compiled', campus_rows=wrong_ledger)
    row_path = paths[0] / 'outcomes.jsonl'
    row = json.loads(row_path.read_text(encoding='utf-8'))
    row['actions']['independent']['cost']['known_tokens'] = 2
    row_path.write_bytes((json.dumps(row) + '\n').encode())
    with pytest.raises(ValueError, match='recorded native result or solve cost differs'):
        read_pool(panel, 'finqa', paths, representation='compiled', campus_rows=ledger)


def test_nonexecution_route_stops_at_first_executable_and_charges_only_queried_arms(runs):
    from cascade_benchmark import ARMS, NonexecutionCascade, realized

    def answer(executable):
        return ((1, executable), None)

    questions = [(ident, ()) for ident in ('exec_but_wrong', 'rescue', 'all_fail')]
    answers = [[answer(valid) for valid in row] for row in ((1, 1, 1), (0, 1, 1), (0, 0, 0))]
    correct = {(i, j): int((i, j) in ((0, 1), (0, 2), (1, 1))) for i in range(3) for j in range(3)}
    charges = [[dict(known_tokens=10 * (arm + 1), unknown_usage_calls=0, summed_call_seconds=1.)
                for arm in range(3)] for _ in questions]
    pool = questions, answers, correct, charges, None, None
    forward = realized(NonexecutionCascade((0, 1, 2)), pool)
    assert [row['selected'] for row in forward] == list(ARMS)
    assert [row['strict'] for row in forward] == [0, 1, 0]
    assert [row['known_tokens'] for row in forward] == [10, 30, 60]

    reverse = realized(NonexecutionCascade((2, 1)), pool)
    assert [row['selected'] for row in reverse] == [ARMS[2], ARMS[2], ARMS[1]]
    assert [row['known_tokens'] for row in reverse] == [30, 30, 50]


def test_author_routes_are_all_fitted_before_opening_evaluation(runs, monkeypatch):
    import numpy as np
    import cascade_benchmark as benchmark

    root = runs[0].parent
    events = []
    profiles = [{'checkpoint': arm, 'api_profile_sha256': None} for arm in benchmark.ARMS]
    receipt = dict(known_tokens=10, unknown_usage_calls=0, summed_call_seconds=1.)
    submissions = [[((1, 1), None)] * len(benchmark.ARMS) for _ in range(2)]
    labels = np.ones((2, len(benchmark.ARMS)), dtype=int)

    def split(path, _dataset, _runs, **_options):
        events.append(path.name)
        questions = [(f'{path.name}_{i}', ()) for i in range(2)]
        return questions, submissions, labels, [[receipt] * 3] * 2, labels * 10, profiles

    class Router:
        gamma = 0.

        def __init__(self, *_args, **_options):
            pass

        def fit(self, questions, *_args):
            assert all(ident.startswith('calibration_') for ident, _ in questions)
            events.append('route_fitted')
            np.random.random()

        def predict(self, _questions, seen):
            return [benchmark.ARMS[0] if state[0] is None else None for state in seen]

        def select_answer(self, _questions, seen):
            return [benchmark.ARMS[0]] * len(seen)

        def get_lambdas(self):
            return [0.]

    def estimators(*args):
        assert all(ident.startswith('fit_') for ident, _ in args[2])
        events.append('estimators_fitted')
        return None, None

    (root / 'eval').mkdir()
    (root / 'eval/exposure.json').write_text(json.dumps([
        {'dataset': 'finqa', 'id': f'eval_{i}', 'exposure': 'independent'} for i in range(2)
    ]), encoding='utf-8')
    monkeypatch.setattr(benchmark, 'read_pool', split)
    monkeypatch.setattr(benchmark, 'fit_estimators', estimators)
    monkeypatch.setattr(benchmark, 'upstream', lambda _path: (
        None, None, SimpleNamespace(CascadeRouter=Router), SimpleNamespace(ConstantStrategy=lambda *_a, **_k: None)))
    report = benchmark.compare(SimpleNamespace(panels=root, dataset='finqa', upstream=root,
                                               fit=[], calibration=[], eval=[], budgets=(1.25, 2.)))
    assert events == ['fit', 'calibration', 'estimators_fitted', *['route_fitted'] * 4, 'eval']
    assert report['policies']['cascade_routing_1.25']['all']['strict'] == 2


def test_contract_cascade_checks_public_output_before_using_teacher(runs):
    from cascade_benchmark import ARMS, contract_cascade, summarize

    def cost(tokens, unknown=0):
        return dict(known_tokens=tokens, unknown_usage_calls=unknown, summed_call_seconds=tokens / 10.)

    def local(executable, value, correct):
        return dict(executable=executable, submission={'answer': value}, strict=correct,
                    calls=['low'] if executable else ['low', 'free'], cost=cost(10 if executable else 19))

    fallbacks = {'local': local(True, None, False), 'free': local(False, 0, False),
                 'qwen': local(False, None, False), 'deepseek': local(False, None, False)}
    questions = [(ident, ()) for ident in fallbacks]
    answers = [[((1, 0), None), ((1, i != 3), None), ((1, 1), None)] for i in range(4)]
    labels = {(i, arm): int(arm != 0) for i in range(4) for arm in range(len(ARMS))}
    charges = [[cost(10), cost(20), cost(25, 1)] for _ in questions]
    choices = contract_cascade((questions, answers, labels, charges, None, None), fallbacks)
    assert [row['selected_stage'] for row in choices] == ['compiled_oda', 'free_oda', 'compiled_qwen-27b',
                                                          'compiled_deepseek']
    assert [row['strict'] for row in choices] == [0, 0, 1, 1]
    assert [row['known_tokens'] for row in choices] == [10, 19, 39, 64]
    assert choices[-1]['queried'] == [ARMS[0], 'oda-8b-free', *ARMS[1:]]
    assert summarize(choices)['tokens'] is None
    assert summarize(choices)['executable'] == 3
