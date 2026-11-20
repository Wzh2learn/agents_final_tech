from hashlib import sha256
import json
from pathlib import Path

import pytest


@pytest.fixture
def frozen_high(tmp_path, monkeypatch):
    pilot = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(pilot))
    from benchmark_actions import action_cost, collect_case, digest_file
    from run_pilot import usage_from, write_json

    panel, run = tmp_path / 'panel', tmp_path / 'run'
    panel.mkdir()
    run.mkdir()
    rows = [{'dataset': 'finqa', 'id': ident, 'report': ident, 'question': 'What is the total?',
             'pre_text': [], 'post_text': [], 'table': [['Label', '2023', '2024'], ['Revenue', '11', '7']]}
            for ident in ('grounded', 'ungrounded')]
    gold = {row['id']: {'exe_ans': 18} for row in rows}

    def write_lines(path, data):
        path.write_bytes(''.join(json.dumps(entry) + '\n' for entry in data).encode())

    write_lines(panel / 'public.jsonl', rows)
    write_lines(panel / 'references.jsonl',
                ({'dataset': 'finqa', 'id': ident, 'gold': answer} for ident, answer in gold.items()))
    names = ('public.jsonl', 'references.jsonl')
    actions = ['low', 'mid', 'high']
    contract = run / 'run.json'
    write_json(contract, {'schema': 'finance-benchmark-actions-v1', 'dataset': 'finqa',
                          'actions': actions, 'panel': {name: digest_file(panel / name) for name in names}})
    run_digest = digest_file(contract)
    outcomes = []
    for row in rows:
        ident = row['id']
        calls = {}
        valid = ident == 'grounded'
        replies = {'low': 'Final program: add(11, 8)', 'mid': 'KEEP',
                   'high_solve': 'Final program: add(11, 7)' if valid else 'Final program: add(10, 8)',
                   'high_compare': '<answer>USE_NEW</answer>'}

        def record(name, actor, prompt):
            relative = Path('calls/finqa') / sha256(ident.encode()).hexdigest()[:24] / name
            target = run / relative
            target.mkdir(parents=True)
            finish = {'reason': 'stop'}
            if valid or name != 'high_compare':
                finish['tokens'] = {'input': 12, 'output': 8, 'total': 20}
            events = [{'type': 'text', 'part': {'text': replies[name]}},
                      {'type': 'step_finish', 'part': finish}]
            receipt = {'text': replies[name], 'usage': usage_from(events), 'elapsed_seconds': 0.5,
                       'finish': ['stop'], 'errors': [], 'exit_code': 0}
            write_json(target / 'request.json', {'actor': actor, 'run_contract': run_digest,
                                                 'prompt_sha256': sha256(prompt.encode()).hexdigest()})
            (target / 'prompt.txt').write_bytes((prompt + '\n').encode())
            write_lines(target / 'raw.jsonl', events)
            write_json(target / 'call.json', receipt)
            calls[name] = {key: value for key, value in receipt.items() if key != 'text'}
            calls[name]['path'] = (relative / 'call.json').as_posix()
            return receipt

        results = collect_case(row, gold[ident], actions, record, None)
        for result in results.values():
            result['cost'] = action_cost([calls[name] for name in result['calls']])
        outcomes.append({'dataset': 'finqa', 'id': ident, 'report': row['report'],
                         'actions': results, 'calls': calls})
    write_lines(run / 'outcomes.jsonl', outcomes)
    return panel, run


def test_decoding_changes_only_high_label_and_retains_guarded_fallback(frozen_high):
    import numpy as np

    from budget_policy import read_split

    panel, run = frozen_high
    path = run / 'outcomes.jsonl'
    before = path.read_bytes()
    raw = read_split(panel, run, 'finqa')
    adjusted = read_split(panel, run, 'finqa', decode_verifier_answer=True)
    assert raw['correct'].tolist() == [[0, 0, 0], [0, 0, 0]]
    assert adjusted['correct'].tolist() == [[0, 0, 1], [0, 0, 0]]
    np.testing.assert_array_equal(adjusted['features'], raw['features'])
    np.testing.assert_array_equal(adjusted['tokens'], raw['tokens'])
    assert adjusted['costs'] == raw['costs']
    assert adjusted['costs'][1][2]['unknown_usage_calls'] == 1
    assert adjusted['verifier_replay'] == {
        'decoder': 'exact_keep_or_use_new_final_answer_v1', 'questions': 2, 'comparison_changed': 2,
        'selection_changed': 1, 'old_high_correct': 0, 'new_high_correct': 1, 'recovered': 1, 'harmed': 0,
    }
    assert path.read_bytes() == before


def test_decoding_refuses_unbound_comparison(frozen_high):
    from budget_policy import read_split

    panel, run = frozen_high
    case = sha256(b'grounded').hexdigest()[:24]
    prompt = run / 'calls/finqa' / case / 'high_compare' / 'prompt.txt'
    prompt.write_bytes(prompt.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='recorded prompt or request differs'):
        read_split(panel, run, 'finqa', decode_verifier_answer=True)
