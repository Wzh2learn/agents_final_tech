from hashlib import sha256
import json
from pathlib import Path

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
        actions = ['independent'] if i else ['low', 'independent']
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
    from cascade_benchmark import read_pool

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
