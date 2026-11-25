from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def draft_run(tmp_path, monkeypatch):
    pilot = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(pilot))
    from benchmark_actions import FAMILIES, action_cost, collect_case, digest_file
    from run_pilot import usage_from, write_json

    panel_root = tmp_path / 'panels'
    panel = panel_root / 'fit'
    panel.mkdir(parents=True)
    run = tmp_path / 'drafts'
    run.mkdir()
    fields = {'dataset': 'finqa', 'question': 'What is the total?', 'pre_text': [],
              'post_text': [], 'table': [['Label', '2023'], ['Revenue', '3']]}
    rows = [dict(fields, id=label, report=label) for label in ('plain', 'wrapped', 'relaxed', 'short')]
    gold = {'exe_ans': 3.0}

    def write_lines(path, entries):
        path.write_bytes(''.join(json.dumps(entry) + '\n' for entry in entries).encode())

    write_lines(panel / 'public.jsonl', rows)
    write_lines(panel / 'references.jsonl',
                ({'id': row['id'], 'dataset': 'finqa', 'gold': gold} for row in rows))
    contract = run / 'run.json'
    write_json(contract, {'panel': {name: digest_file(panel / name) for name in ('public.jsonl', 'references.jsonl')},
                          'dataset': 'finqa', 'model': 'test', 'checkpoint': 'test',
                          'serve_sha256': 'test', 'opencode_sha256': 'test', 'seed': 17,
                          'context': 16384, 'output': {'solve': 4096, 'probe': 4096}, 'temperature': .6})
    run_digest = digest_file(contract)
    judgment_lines = [f'{name}: no, rationale: No issue found.' for name in FAMILIES]
    plain = '\n'.join(judgment_lines)
    relaxed = '\n'.join(line.replace('rationale: ', '') for line in reversed(judgment_lines))
    probe_text = {'plain': plain, 'wrapped': f'<answer>\n{plain}\n</answer>', 'relaxed': relaxed,
                  'short': '<answer>\n' + '\n'.join(judgment_lines[:4])}
    outcomes = []
    for row in rows:
        ident = row['id']
        calls = {}

        def record(name, actor, prompt):
            relative = Path('calls/finqa') / sha256(ident.encode()).hexdigest()[:24] / name
            target = run / relative
            target.mkdir(parents=True)
            text = 'Final program: add(1, 2)' if name == 'low' else probe_text[ident]
            finish = 'length' if name == 'car_probe' and ident == 'short' else 'stop'
            events = [{'type': 'text', 'part': {'text': text}},
                      {'type': 'step_finish', 'part': {'reason': finish,
                                                        'tokens': {'input': 8, 'output': 5, 'total': 13}}}]
            receipt = {'text': text, 'finish': [finish], 'errors': [],
                       'elapsed_seconds': 1.0, 'exit_code': 0, 'usage': usage_from(events)}
            write_json(target / 'request.json', {'prompt_sha256': sha256(prompt.encode()).hexdigest(),
                                                 'run_contract': run_digest, 'actor': actor})
            (target / 'prompt.txt').write_bytes((prompt + '\n').encode())
            write_lines(target / 'raw.jsonl', events)
            write_json(target / 'call.json', receipt)
            calls[name] = {key: value for key, value in receipt.items() if key != 'text'}
            calls[name]['path'] = (relative / 'call.json').as_posix()
            return receipt

        actions = collect_case(row, gold, ['low', 'car_probe'], record, None)
        for action in actions.values():
            action['cost'] = action_cost([calls[name] for name in action['calls']])
        outcomes.append({'id': ident, 'dataset': 'finqa', 'report': row['report'],
                         'actions': actions, 'calls': calls})
    write_lines(run / 'outcomes.jsonl', outcomes)
    return SimpleNamespace(panel_root=panel_root, drafts=run, dataset='finqa')


def test_probe_replay_recovers_only_complete_judgments(draft_run):
    from car_adapter import source_rows

    outcome_path = draft_run.drafts / 'outcomes.jsonl'
    before = outcome_path.read_bytes()
    entries, _, _, _, coverage = source_rows(draft_run, 'fit')
    assert coverage == {'decoder': 'explicit_five_family_final_answer_v1', 'questions': 4,
                        'saved_valid': 1, 'recovered_by_replay': 2, 'missing': 1}
    probes = {row['id']: entry['actions']['car_probe'] for row, entry in entries}
    assert probes['wrapped']['judgments'] == probes['plain']['judgments']
    assert probes['relaxed']['judgments'] == probes['plain']['judgments']
    assert probes['short']['judgments'] is None
    assert probes['wrapped']['cost'] == probes['short']['cost']
    assert outcome_path.read_bytes() == before


def test_probe_replay_rejects_unbound_prompt(draft_run):
    from car_adapter import source_rows

    case = sha256(b'wrapped').hexdigest()[:24]
    prompt = draft_run.drafts / 'calls' / 'finqa' / case / 'car_probe' / 'prompt.txt'
    prompt.write_bytes(prompt.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='recorded prompt or request differs'):
        source_rows(draft_run, 'fit')


def test_repair_preserves_optional_thinking_contract(draft_run, monkeypatch, tmp_path):
    import car_adapter

    contract_path = draft_run.drafts / 'run.json'
    contract = json.loads(contract_path.read_text(encoding='utf-8'))
    legacy = car_adapter.checked_profile(contract)
    disabled = car_adapter.checked_profile({**contract, 'chat_template_kwargs': {'enable_thinking': False}})
    assert 'chat_template_kwargs' not in legacy
    assert disabled == {**legacy, 'chat_template_kwargs': {'enable_thinking': False}}
    with pytest.raises(ValueError, match='disable-thinking'):
        car_adapter.checked_profile({**contract, 'chat_template_kwargs': {'enable_thinking': True}})

    contract_path.write_text(json.dumps({**contract, 'chat_template_kwargs': {'enable_thinking': False}}), encoding='utf-8')
    contract_digest = sha256(contract_path.read_bytes()).hexdigest()
    for path in draft_run.drafts.rglob('request.json'):
        receipt = json.loads(path.read_text(encoding='utf-8'))
        path.write_text(json.dumps({**receipt, 'run_contract': contract_digest}), encoding='utf-8')
    _, _, retained_profile, _, _ = car_adapter.source_rows(draft_run, 'fit')
    assert retained_profile == disabled

    calls = []
    monkeypatch.setattr(car_adapter, 'OpenCode', lambda *args, **kwargs: calls.append((args, kwargs)))
    args = SimpleNamespace(opencode=Path('opencode'), base='http://127.0.0.1:18157/v1', repair_output=384)
    car_adapter.repair_actor(tmp_path, args, legacy)
    car_adapter.repair_actor(tmp_path, args, retained_profile)
    assert calls[0][1] == {} and calls[1][1] == {'disable_thinking': True}
