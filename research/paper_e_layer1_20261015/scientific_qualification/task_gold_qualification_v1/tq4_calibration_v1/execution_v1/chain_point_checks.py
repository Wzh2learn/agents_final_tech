# -*- coding: utf-8 -*-
'''TQ chain offline point checks (TQ-4 config): budget, isolation, schedule, duplicate stimuli, scorer v2.1.'''
import hashlib
import json
import socket
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

EXEC = Path(__file__).resolve().parent
Q = EXEC.parent
sys.path.insert(0, str(EXEC))
import chain_runner as R

TESTS = []


def add(name, ok, detail):
    TESTS.append({'test': name, 'passed': bool(ok), 'detail': detail})


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


import sys as _sys
_cfg_arg = _sys.argv[1] if len(_sys.argv) > 1 else str(Q / 'execution_v1' / 'chain_config_tq4.json')
_root_arg = _sys.argv[2] if len(_sys.argv) > 2 else str(Q)
CFG = R.load_config(_cfg_arg, root_override=_root_arg)


def t_config():
    steps = CFG['steps']
    kinds = {}
    for s in steps:
        kinds[s['kind']] = kinds.get(s['kind'], 0) + 1
    keys = [s['key'] for s in steps]
    nums = [s['step'] for s in steps]
    actors = sum(1 for s in steps if s['kind'] == 'actor')
    cands = len(load_candidates())
    exp_total = actors + 2 * (actors + cands)
    ok = (len(steps) == 36 and len(steps) == exp_total and actors in (4, 12)
          and kinds.get('b', 0) == actors + cands and kinds.get('c', 0) == actors + cands
          and len(set(keys)) == 36 and nums == list(range(1, 37))
          and CFG['budget']['gen_cap'] == 40 and CFG['budget']['retry_cap'] == 4
          and CFG['budget']['token_cap'] == 400000 and CFG['budget']['window_min'] == 90)
    add('config_schedule_counts', ok, {'kinds': kinds, 'unique_keys': len(set(keys)), 'exp_total': exp_total})
def t_template():
    tpl = R.parse_templates(CFG['_templates'])
    ok = (tpl['a'][0].startswith('You answer financial table questions.')
          and tpl['b'][0].startswith('You are a careful verifier')
          and tpl['c'][0].startswith('You independently solve the task')
          and chr(34) + 'kind' + chr(34) in tpl['a'][1] and '0-based' in tpl['a'][1] and 'paragraph_uid' in tpl['a'][1])
    add('template_v2_extraction', ok, {'a_head': tpl['a'][0][:40]})


def load_candidates():
    if not CFG.get('candidates_file'):
        return {}
    return {c['candidate_id']: c for c in load(CFG['_root'] / CFG['candidates_file'])['candidates']}


def render_steps():
    tpl = R.parse_templates(CFG['_templates'])
    cands = load_candidates()
    cache = {}
    out = []
    for step in CFG['steps']:
        rec = cache.get(step['input'])
        if rec is None:
            rec = load(CFG['_root'] / step['input'])
            cache[step['input']] = rec
        if step['kind'] == 'actor':
            msgs = R.render_actor(tpl, step['task_id'], rec)
        else:
            if step.get('source') == 'candidate':
                src = R.strip_candidate(cands[step['candidate_id']])
            else:
                src = {'task_id': step['task_id'], 'answer': '0000', 'evidence': []}
            msgs = R.render_b(tpl, rec, src) if step['kind'] == 'b' else R.render_c(tpl, rec, src)
        out.append((step, rec, msgs))
    return out


def t_prompt_caps():
    mx = 0
    for step, rec, msgs in render_steps():
        est = len((msgs[0]['content'] + chr(10) + msgs[1]['content']).encode('utf-8')) + 512
        mx = max(mx, est)
    add('prompt_byte_bounds_under_cap', mx < R.PROMPT_TOKEN_CAP, {'max_byte_bound': mx, 'cap': R.PROMPT_TOKEN_CAP})


def t_isolation():
    cands = load_candidates()
    cand_ids = list(cands.keys())
    forbidden_tokens = ['incorrect', 'correct', 'illegal', 'legal', 'stratum', 'variant', 'official_reference',
                        'injection', 'candidate_id', '.json', 'perturbed', 'original header']
    violations = []
    for step, rec, msgs in render_steps():
        joined = msgs[0]['content'] + chr(10) + msgs[1]['content']
        src = json.dumps({'q': rec['question'], 't': rec['table'], 'p': rec['paragraphs']}, ensure_ascii=False)
        for tok in forbidden_tokens:
            if tok in joined and tok not in src:
                violations.append({'key': step['key'], 'token': tok})
        for cid in cand_ids:
            if cid in joined:
                violations.append({'key': step['key'], 'token': 'candidate_id_literal:' + cid})
    add('prompt_isolation_no_labels', not violations, {'violations': violations[:20]})


def t_bc_exposure():
    cands = load_candidates()
    bad = []
    for step, rec, msgs in render_steps():
        joined = msgs[0]['content'] + chr(10) + msgs[1]['content']
        if step['kind'] == 'b':
            if step.get('source') == 'candidate':
                c = cands[step['candidate_id']]
                if 'table_row' in c['evidence'][0].get('kind', '') or c['evidence'][0]['kind'] == 'cell':
                    if 'table_row' not in joined:
                        bad.append(step['key'])
                if c['evidence'][0]['kind'] == 'paragraph':
                    if 'paragraph_uid' not in joined:
                        bad.append(step['key'])
        if step['kind'] == 'c':
            if 'table_row' in joined or 'paragraph_uid' in joined:
                bad.append({'c_has_evidence': step['key']})
    add('b_sees_evidence_c_does_not', not bad, {'bad': bad})


def t_duplicate_stimuli():
    cd = {'by_key': {}}
    for step, rec, msgs in render_steps():
        if step['kind'] != 'c' or step.get('source') != 'candidate':
            continue
        key = msgs[0]['content'] + chr(11) + msgs[1]['content']
        cd.setdefault('by_key', {})
        cd['by_key'].setdefault(hashlib.sha256(key.encode('utf-8')).hexdigest(), []).append(step['candidate_id'])
    groups = [v for v in cd['by_key'].values() if len(v) > 1]
    expected_pairs = 6 if CFG.get('candidates_file') else 0
    ok = len(groups) == expected_pairs and all(len(g) == 2 for g in groups)
    add('c_duplicate_stimulus_pairs_identical', ok, {'groups': sorted([sorted(g) for g in groups])})


def t_schedule_order():
    steps = CFG['steps']
    actors = [s for s in steps if s['kind'] == 'actor']
    ok1 = actors == steps[:len(actors)]
    expected = []
    for i, a in enumerate(actors):
        arms = ['b', 'c'] if i % 2 == 0 else ['c', 'b']
        for arm in arms:
            expected.append(arm + '|' + a['task_id'])
    seen = []
    for s in steps:
        if s.get('source') == 'candidate' and s.get('candidate_id') not in seen:
            seen.append(s.get('candidate_id'))
    for j, cid in enumerate(seen):
        arms = ['b', 'c'] if j % 2 == 0 else ['c', 'b']
        for arm in arms:
            expected.append(arm + '|' + cid)
    ok2 = [s['key'] for s in steps[len(actors):]] == expected
    add('schedule_order_frozen', ok1 and ok2, {'actors': [s['task_id'] for s in actors], 'bc_head': expected[:6], 'candidates': len(seen)})
def t_ledger_math():
    with tempfile.TemporaryDirectory() as td:
        led = R.Ledger(Path(td) / 'l.jsonl')
        led.append({'op': 'reserve', 'seq': 1, 'item_key': 'x', 'retry': False, 'reserved': 10240})
        a = led.unsettled_tokens()
        led.append({'op': 'settle', 'seq': 1, 'item_key': 'x', 'ok': True, 'settled': 500, 'freed': 9740})
        b = led.unsettled_tokens()
        add('ledger_reserve_settle_math', a == 10240 and b == 500, {'after_reserve': a, 'after_settle': b})


def t_dual_ledger():
    with tempfile.TemporaryDirectory() as td:
        led = R.DualLedger(Path(td) / 'run.jsonl', Path(td) / 'master.jsonl', {'panel': 'T', 'run_id': 'r1'})
        led.append({'op': 'reserve', 'seq': 1, 'item_key': 'k', 'retry': False, 'reserved': 10})
        m = [json.loads(x) for x in (Path(td) / 'master.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
        ok = len(m) == 1 and m[0]['panel'] == 'T' and m[0]['run_id'] == 'r1' and m[0]['reserved'] == 10
        add('dual_ledger_mirror', ok, {'master_entries': len(m)})


def t_resume_states():
    with tempfile.TemporaryDirectory() as td:
        led = R.Ledger(Path(td) / 'l.jsonl')
        led.append({'op': 'reserve', 'seq': 1, 'item_key': 'k1', 'retry': False, 'reserved': 10240})
        led.append({'op': 'settle', 'seq': 1, 'item_key': 'k1', 'ok': True, 'settled': 300, 'freed': 9940})
        led.append({'op': 'reserve', 'seq': 2, 'item_key': 'k2', 'retry': False, 'reserved': 10240})
        s1 = led.item_state('k1')
        s2 = led.item_state('k2')
        s3 = led.item_state('k3')
        add('crash_resume_item_state', s1 == 'done' and s2 == 'inflight' and s3 == 'pending', {'k1': s1, 'k2': s2, 'k3': s3})


def t_anomaly_parsing():
    obj, valid, err = R.parse_actor_text('not json')
    a = obj is None and valid is False and err == 'json_parse_error'
    obj2, valid2, err2 = R.parse_actor_text('{"task_id": "N1"}')
    b = valid2 is False and err2 == 'missing_or_empty_answer'
    d1, de1 = R.parse_decision_text('{"decision": "maybe"}')
    d2, de2 = R.parse_decision_text('{"decision": "accept"}')
    d = d1 is None and de1 == 'invalid_decision' and d2 is not None and de2 is None
    add('anomaly_output_parsing', a and b and d, {'bad_json': a, 'missing_answer': b, 'decisions': d})


def t_scorer_v21():
    sys.path.insert(0, str(EXEC))
    sys.path.insert(0, str(Q / 'scorer_v2'))
    import tq4_scoring_entry_v21 as V21
    import tq4_scoring_entry as V2
    rr = load(Q / 'scorer_v2' / 'regression' / 'regression_results.json')
    same = True
    mismatch = []
    for row in rr['rows']:
        fixture = next(c for c in load(Q / 'scorer_v2' / 'regression' / 'tq4_regression_cases.json')['cases'] if c['case_id'] == row['case_id'])
        r2 = V2.score(row['case_id'], {'answer': row['answer']}, fixture['v2_config'])
        r21 = V21.score(row['case_id'], {'answer': row['answer']}, fixture['v2_config'])
        if r21['status'] != r2['status']:
            same = False
            mismatch.append({'case': row['case_id'], 'answer': row['answer'], 'v2': r2['status'], 'v21': r21['status']})
    add('scorer_v21_scoring_identical_to_v2', same, {'mismatches': mismatch})

    table = [['a', 'b'], ['c', 'd'], ['e', 'f']]
    paragraphs = [{'uid': 'p1', 'order': 1, 'text': 'x'}]
    cases = [
        ('bool_row_true', [{'kind': 'cell', 'table_row': True, 'table_col': 0}], False, 'cell_not_integer'),
        ('bool_col_false', [{'kind': 'cell', 'table_row': 1, 'table_col': False}], False, 'cell_not_integer'),
        ('float_coord', [{'kind': 'cell', 'table_row': 1.0, 'table_col': 0}], False, 'cell_not_integer'),
        ('valid_int', [{'kind': 'cell', 'table_row': 1, 'table_col': 0}], True, None),
        ('bool_before_bounds', [{'kind': 'cell', 'table_row': True, 'table_col': 99}], False, 'cell_not_integer'),
        ('paragraph_ok', [{'kind': 'paragraph', 'paragraph_uid': 'p1'}], True, None),
    ]
    bad = []
    for name, ev, exp_legal, exp_issue in cases:
        leg = V21.check_evidence_legality(table, paragraphs, ev)
        ok = leg['legal'] == exp_legal and (not exp_issue or (leg['issues'] and leg['issues'][0]['issue'] == exp_issue))
        if not ok:
            bad.append({'case': name, 'legality': leg})
    add('scorer_v21_bool_hardening', not bad, {'bad': bad})


def t_pins():
    r = R.check_material_pins(CFG)
    add('material_pin_check_full', r['ok'], {'checked': r['checked'], 'mismatches': len(r['mismatches']), 'channels': r['channels']})


def main():
    host = socket.gethostname()
    t_config()
    t_template()
    t_prompt_caps()
    t_isolation()
    t_bc_exposure()
    t_duplicate_stimuli()
    t_schedule_order()
    t_ledger_math()
    t_dual_ledger()
    t_resume_states()
    t_anomaly_parsing()
    t_scorer_v21()
    t_pins()
    report = {'schema': 'tq_chain_point_checks_v1', 'panel': CFG['panel_id'], 'host': host,
              'generated_utc': R.iso(), 'runner_sha256': hashlib.sha256(Path(R.__file__).read_bytes()).hexdigest(),
              'tests': TESTS, 'all_passed': all(t['passed'] for t in TESTS)}
    out_dir = EXEC / 'tests'
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = out_dir / ('chain_point_checks_' + CFG['panel_id'].replace('-', '').lower() + '_' + host + '_' + ts + '.json')
    R.write_json(out, report)
    print(json.dumps({'all_passed': report['all_passed'],
                      'failed': [t['test'] for t in TESTS if not t['passed']], 'out': str(out)}, ensure_ascii=True))
    return 0 if report['all_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
