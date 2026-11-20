from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def pilot(monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(source))
    from benchmark_actions import collect_case
    from run_pilot import paired_prompt
    from table_scope_replay import nested_contract

    return collect_case, paired_prompt, nested_contract


@pytest.fixture
def report():
    return {
        'dataset': 'finqa', 'id': 'test', 'report': 'report',
        'question': 'What is the difference?',
        'pre_text': [], 'post_text': [],
        'table': [['', '2022', '2023'], ['Revenue', '2', '3']],
    }


def test_one_call_uses_same_scoring_as_compiled_flat(pilot, report):
    collect_case, paired_prompt, _ = pilot
    flat = 'add(10, 5), subtract(2, 3), divide(#0, #1)'
    replies = {'low': flat, 'nested_compile': 'divide(add(10, 5), subtract(2, 3))'}
    calls = []

    def call(action, actor, prompt):
        assert actor == 'solve'
        assert prompt == paired_prompt(report, 'dsl' if action == 'low' else 'nested')
        calls.append(action)
        return {'text': f'Final program: {replies[action]}', 'exit_code': 0, 'errors': [], 'finish': ['stop']}

    gold = {'exe_ans': -15.0}
    result = collect_case(report, gold, ['nested_compile'], call, None)
    assert calls == ['nested_compile']
    assert set(result) == {'nested_compile'}
    nested = result['nested_compile']
    assert nested['strict'] and nested['executable']
    assert nested['calls'] == ['nested_compile']
    assert nested['submission']['program'] == flat

    calls.clear()
    flat_action = collect_case(report, gold, ['contract_compile'], call, None)['contract_compile']
    assert calls == ['low']
    assert flat_action['strict'] and flat_action['submission'] == nested['submission']


def test_nested_keeps_scale_and_applies_shared_repairs(pilot, report):
    _, _, compile_reply = pilot
    projected, prediction, decision, cells = compile_reply(
        dict(report, dataset='tatqa'),
        'Final program: add(table_sum("Revenue", "2022", "2023"), 1)\nScale: million',
        stopped=True,
    )
    assert prediction['scale'] == 'million'
    assert decision == 'nested_table_scope'
    assert projected['table'][-1][1:] == ['2', '3']
    assert [entry['column'] for entry in cells] == [1, 2]
    assert prediction['program'].endswith('add(#0, 1)')

    _, prediction, decision, _ = compile_reply(
        dict(report, question='What percentage of the total?'),
        'Final program: multiply(divide(10, 20), const_100)', stopped=True,
    )
    assert decision == 'nested_finqa_ratio'
    assert prediction['program'] == 'divide(10, 20)'

    _, prediction, _, _ = compile_reply(
        dict(report, dataset='tatqa'),
        'Scale: million\n{"program": "add(1, 2)"}', stopped=True,
    )
    assert prediction['scale'] == 'million'


@pytest.mark.parametrize('reply', [
    'Final program: add(1, 2)\nFinal program: add(3, 4)',
    'Final program: add(1, 2)\n{"program": "add(3, 4)"}',
    '{"program": "add(3, 4)"}\nFinal program: add(1, 2)',
    '{\n  "program": "add(3, 4)"\n}\nFinal program: add(1, 2)',
    'Scale: million\n{"program": "add(1, 2)", "scale": "percent"}',
    'Final program: add(1, 2)\nScale: percent\nScale: million',
    'Final program: add(1, 2), subtract(#0, 3)',
    'Final program: divide(#0, 2)',
    'Final program: sum(1, 2)',
    'Final program: ' + 'add(1, ' * 130 + '2' + ')' * 130,
])
def test_rejects_invalid_or_ambiguous_declarations(pilot, report, reply):
    _, _, compile_reply = pilot
    _, prediction, decision, cells = compile_reply(report, reply, stopped=True)
    assert decision == 'nested_rejected'
    assert prediction['program'] is None
    assert cells == []


def test_car_envelope_replay_preserves_five_explicit_judgments(pilot):
    from benchmark_actions import FAMILIES, parse_car

    plain = '\n'.join(f'{family}: {"yes" if family == "Binding" else "no"}, rationale: {family} reason'
                      for family in FAMILIES)
    compact = plain.replace('rationale: ', '').splitlines()
    swapped = '\n'.join([compact[1], compact[0], *compact[2:]])
    wrapped = f'<answer>\n{swapped}\n</answer>'
    assert parse_car(wrapped) is None
    assert parse_car(wrapped, unwrap_answer=True) == parse_car(plain)
    assert parse_car(wrapped.replace('Binding:', 'Omission:'), unwrap_answer=True) is None
    assert parse_car(wrapped.replace('Binding reason', 'rationale:'), unwrap_answer=True) is None
    assert parse_car(wrapped.removesuffix('</answer>'), unwrap_answer=True) is None


def test_high_envelope_replay_keeps_public_guards_and_call_plan(pilot, report):
    collect_case, _, _ = pilot
    replies = {'low': 'Final program: add(3, const_0)',
               'high_solve': 'Final program: add(2, const_0)',
               'high_compare': '<answer>USE_NEW</answer>'}

    def call(action, _actor, _prompt):
        return {'text': replies[action], 'exit_code': 0, 'errors': [], 'finish': ['stop']}

    old = collect_case(report, {'exe_ans': 2}, ['high'], call, None)['high']
    corrected = collect_case(report, {'exe_ans': 2}, ['high'], call, None,
                             decode_verifier_answer=True)['high']
    assert not old['strict'] and old['decision'] == 'keep'
    assert corrected['strict'] and corrected['decision'] == 'use_new'
    assert old['calls'] == corrected['calls'] == ['low', 'high_solve', 'high_compare']
    replies['high_solve'] = 'Final program: add(9, const_0)'
    assert collect_case(report, {'exe_ans': 9}, ['high'], call, None,
                        decode_verifier_answer=True)['high']['decision'] == 'keep'


def test_fresh_timing_measures_the_conditional_calls_before_gold_grading(pilot, report, monkeypatch):
    import benchmark_actions as benchmark

    ticks = iter((5., 8.))
    calls = []
    monkeypatch.setattr(benchmark, 'time', SimpleNamespace(monotonic=lambda: next(ticks)))

    def call(action, _actor, _prompt):
        calls.append(action)
        reply = 'Final program: unknown(2, 3)' if action == 'low' else 'Final answer: 3'
        return {'text': reply, 'exit_code': 0, 'errors': [], 'finish': ['stop']}

    outputs, grading_rows, elapsed = benchmark.timed_selection(report, 'compiled_fallback', call)
    assert elapsed == 3. and calls == ['low', 'free']
    assert 'strict' not in outputs['compiled_fallback']
    scored = benchmark.grade_case(report, {'exe_ans': 3}, outputs, grading_rows, None)
    assert scored['compiled_fallback']['strict'] and not scored['compiled_fallback']['executable']


def test_prioritize_direct_publishes_once_and_reuses_verified_low_receipts(pilot, report, monkeypatch, tmp_path):
    import benchmark_actions as benchmark
    from run_pilot import load_lines, usage_from, write_json

    panel = tmp_path / 'panel'
    panel.mkdir()
    rows = [dict(report, id=ident) for ident in ('cached', 'fresh')]
    (panel / 'public.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
    (panel / 'references.jsonl').write_text(''.join(
        json.dumps({'dataset': 'finqa', 'id': row['id'], 'gold': {'exe_ans': 3}}) + '\n' for row in rows
    ), encoding='utf-8')
    profile = tmp_path / 'serving.json'
    write_json(profile, {'model': 'oda', 'checkpoint': 'fixture'})
    args = SimpleNamespace(panel=panel, dataset=None, metric_dir=None, serving_profile=profile, model='oda',
                           checkpoint='fixture', base='http://localhost:1/v1', namespace='eval', opencode=profile,
                           actions=['low', 'contract_compile', 'independent', 'mid'], measure_wall=False,
                           solve_output=4096, verify_output=4096, probe_output=4096, context=16384, temperature=.6,
                           workers=1, prioritize_direct=True)
    root = tmp_path / 'eval'
    root.mkdir()
    direct = root / 'direct_outcomes.jsonl'
    issued = []

    class Actor:
        def __init__(self, root, *_):
            self.root = root

        def call(self, prompt, target):
            path = target / 'call.json'
            if path.is_file():
                return json.loads(path.read_bytes())
            if target.name == 'mid':
                assert direct.is_file() and len(load_lines(direct)) == len(rows)
            issued.append(target.name)
            text = 'Final program: add(1, 2)' if target.name == 'low' else 'Final answer: KEEP'
            events = [{'type': 'text', 'part': {'text': text}},
                      {'type': 'step_finish', 'part': {'reason': 'stop', 'tokens': {'total': 7}}}]
            (target / 'prompt.txt').write_bytes((prompt + '\n').encode())
            (target / 'raw.jsonl').write_text(''.join(json.dumps(event) + '\n' for event in events), encoding='utf-8')
            receipt = {'text': text, 'finish': ['stop'], 'errors': [], 'usage': usage_from(events),
                       'exit_code': 0, 'elapsed_seconds': 2}
            write_json(path, receipt)
            return receipt

    monkeypatch.setattr(benchmark, 'OpenCode', Actor)
    monkeypatch.setattr(benchmark, 'wait_service', lambda *_: None)
    original_collect = benchmark.recorded_call

    def interrupt(actor, prompt, target, digest):
        if issued:
            raise RuntimeError('Interrupted before the second low receipt')
        return original_collect(actor, prompt, target, digest)

    monkeypatch.setattr(benchmark, 'recorded_call', interrupt)
    with pytest.raises(RuntimeError, match='Interrupted'):
        benchmark.collect(args, root)
    assert issued == ['low'] and not direct.exists()

    monkeypatch.setattr(benchmark, 'recorded_call', original_collect)
    benchmark.collect(args, root)
    assert issued == ['low', 'low', 'mid', 'mid']
    published = direct.read_bytes()
    direct_rows = load_lines(direct)
    final_rows = load_lines(root / 'outcomes.jsonl')
    assert json.loads((root / 'collection.json').read_bytes())['new_calls_this_pass'] == 3
    assert json.loads((root / 'run.json').read_bytes())['actions'] == sorted(args.actions)
    for direct_row, final_row, cached in zip(direct_rows, final_rows, (True, False), strict=True):
        assert set(direct_row['actions']) == set(benchmark.DIRECT_ACTIONS) and list(direct_row['calls']) == ['low']
        assert set(final_row['actions']) == set(args.actions)
        assert {key: final_row['actions'][key] for key in benchmark.DIRECT_ACTIONS} == direct_row['actions']
        assert final_row['calls']['low'] == direct_row['calls']['low']
        assert final_row['calls']['low']['cached_this_pass'] is cached

    benchmark.collect(args, root)
    assert issued == ['low', 'low', 'mid', 'mid'] and direct.read_bytes() == published
    assert json.loads((root / 'collection.json').read_bytes())['new_calls_this_pass'] == 0
    raw = (root / direct_rows[0]['calls']['low']['path']).with_name('raw.jsonl')
    raw.write_text('', encoding='utf-8')
    with pytest.raises(ValueError, match='raw events, call receipt or recorded usage disagree'):
        benchmark.collect(args, root)
    assert issued == ['low', 'low', 'mid', 'mid'] and direct.read_bytes() == published


def test_ratio_prompt_control_is_one_dsl_call_with_only_the_declared_convention(pilot, report):
    collect_case, paired_prompt, _ = pilot
    old, old_report = paired_prompt(report, 'dsl').split('\n\n', 1)
    calls = []

    def call(action, actor, prompt):
        instructions, public = prompt.split('\n\n', 1)
        assert public == old_report and instructions.startswith(old)
        assert '25% should execute to 0.25' in instructions[len(old):]
        calls.append((action, actor))
        return {'text': 'Final program: divide(1, 4)', 'exit_code': 0, 'errors': [], 'finish': ['stop']}

    action = collect_case(report, {'exe_ans': .25}, ['finqa_ratio_prompt'], call, None)['finqa_ratio_prompt']
    assert calls == [('finqa_ratio_prompt', 'solve')] and action['strict'] and action['executable']
    with pytest.raises(ValueError, match='specific to FinQA'):
        paired_prompt(dict(report, dataset='tatqa'), 'finqa_ratio_prompt')


def test_literal_ratio_sensitivity_only_preserves_two_bare_operands(pilot, report):
    from scoring import public_execution
    from table_scope_replay import public_contract

    row = dict(report, question='What percentage of the total?')
    reply = 'Final program: divide(2, 8), multiply(#0, const_100)'
    _, original, stage, _ = public_contract(row, reply, stopped=True)
    _, guarded, _, _ = public_contract(row, reply, stopped=True, preserve_literal_ratio=True)
    assert stage == 'finqa_ratio'
    assert public_execution(row, original)['terminal_execution_answer'] == .25
    assert public_execution(row, guarded)['terminal_execution_answer'] == 25.
    constant = reply.replace('divide(2, 8)', 'divide(const_1, 8)')
    assert public_contract(row, constant, stopped=True) == public_contract(
        row, constant, stopped=True, preserve_literal_ratio=True)


@pytest.fixture
def paired_runs(tmp_path, pilot, report):
    from benchmark_actions import action_cost, digest_file
    from run_pilot import usage_from, write_json

    collect_case, _, _ = pilot
    public = [dict(report, id='percent', question='What percentage of the total?'),
              dict(report, id='absolute', report='other report')]
    gold = {'percent': {'exe_ans': .5}, 'absolute': {'exe_ans': 3.0}}
    panel = tmp_path / 'panel'
    panel.mkdir()
    public_path, ref_path = panel / 'public.jsonl', panel / 'references.jsonl'

    def write_lines(path, rows):
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')

    write_lines(public_path, public)
    write_lines(ref_path, ({'dataset': 'finqa', 'id': key, 'gold': value} for key, value in gold.items()))
    panel_identity = {path.name: digest_file(path) for path in (public_path, ref_path)}
    profile = {'schema': 'finance-benchmark-actions-v1', 'panel': panel_identity,
               'model': 'oda-fin-rl-8b', 'checkpoint': 'fixture', 'endpoint': 'http://127.0.0.1:18157/v1',
               'serve_sha256': 'fixture', 'opencode_sha256': 'fixture',
               'seed': 17, 'context': 16384, 'output': {'solve': 4096}, 'temperature': .6}
    for action, replies in (
        ('contract_compile', ['divide(10, 20), multiply(#0, const_100)', 'add(1, 2)']),
        ('nested_compile', ['divide(10, 20)', None]),
    ):
        run = tmp_path / action
        run.mkdir()
        contract_path = run / 'run.json'
        write_json(contract_path, dict(profile, namespace=action, actions=[action],
                                       dataset=None if action == 'contract_compile' else 'finqa'))
        digest = digest_file(contract_path)
        outcomes = []
        for row, program in zip(public, replies):
            saved_calls = {}

            def capture(name, actor, prompt):
                relative = Path('calls/finqa') / sha256(row['id'].encode()).hexdigest()[:24] / name
                target = run / relative
                target.mkdir(parents=True)
                text = f'Final program: {program}' if program is not None else ''
                events = [{'type': 'text', 'part': {'text': text}},
                          {'type': 'step_finish', 'part': {'reason': 'stop',
                                                           'tokens': {'input': 5, 'output': 9, 'total': 14}}}
                          ] if program is not None else []
                receipt = {'text': text, 'usage': usage_from(events), 'elapsed_seconds': 1.25,
                           'exit_code': 0 if events else 124, 'finish': ['stop'] if events else [], 'errors': []}
                write_json(target / 'request.json', {'actor': actor, 'run_contract': digest,
                                                     'prompt_sha256': sha256(prompt.encode()).hexdigest()})
                (target / 'prompt.txt').write_bytes((prompt + '\n').encode())
                write_lines(target / 'raw.jsonl', events)
                write_json(target / 'call.json', receipt)
                saved_calls[name] = {k: v for k, v in receipt.items() if k != 'text'}
                saved_calls[name]['path'] = (relative / 'call.json').as_posix()
                return receipt

            actions = collect_case(row, gold[row['id']], [action], capture, None)
            for output in actions.values():
                output['cost'] = action_cost([saved_calls[name] for name in output['calls']])
            outcomes.append(dict(dataset='finqa', id=row['id'], report=row['report'],
                                 actions=actions, calls=saved_calls))
        write_lines(run / 'outcomes.jsonl', reversed(outcomes) if action == 'nested_compile' else outcomes)
    return panel, tmp_path / 'contract_compile', tmp_path / 'nested_compile'


def test_paired_replay_preserves_failures_and_computes_matched_differences(paired_runs):
    from diagnose import compare_nested

    result = compare_nested(*paired_runs, 'finqa')
    assert result['arms']['low']['strict_correct'] == 1
    assert result['arms']['contract_compile']['strict_correct'] == 2
    assert result['arms']['low']['known_tokens'] == result['arms']['contract_compile']['known_tokens'] == 28
    assert result['arms']['nested_compile'] == {
        'n': 2, 'strict_correct': 1, 'executable': 1, 'delivered': 1, 'call_errors': 1, 'output_cap': 0,
        'known_tokens': 14, 'unknown_usage_calls': 1, 'summed_call_seconds': 2.5,
    }
    assert result['comparisons']['nested_minus_low']['gains'] == 1
    assert result['comparisons']['nested_minus_low']['losses'] == 1
    assert result['comparisons']['nested_minus_contract_compile']['net_pp'] == -50
    assert result['comparisons']['nested_minus_contract_compile']['paired_cluster_percentile_95_pp'] == [-100, 0]


@pytest.mark.parametrize(('file', 'old', 'new', 'message'), [
    ('run.json', '"temperature": 0.6', '"temperature": 0.7', 'serving profiles differ'),
    ('outcomes.jsonl', '"other report"', '"new report"', 'frozen IDs and reports'),
    ('outcomes.jsonl', '"known_tokens": 14', '"known_tokens": 15', 'recorded score or cost'),
    ('prompt.txt', 'nested', 'flat', 'recorded prompt or request'),
    ('request.json', '"actor": "solve"', '"actor": "probe"', 'recorded prompt or request'),
    ('raw.jsonl', '"total": 14', '"total": 15', 'raw events, call receipt or recorded usage'),
])
def test_paired_replay_refuses_record_drift(paired_runs, file, old, new, message):
    from diagnose import compare_nested

    _, _, nested = paired_runs
    candidates = sorted(p for p in nested.rglob(file) if old in p.read_text(encoding='utf-8'))
    assert candidates
    path = candidates[0]
    path.write_bytes(path.read_text(encoding='utf-8').replace(old, new, 1).encode())
    with pytest.raises(ValueError, match=message):
        compare_nested(*paired_runs, 'finqa')
