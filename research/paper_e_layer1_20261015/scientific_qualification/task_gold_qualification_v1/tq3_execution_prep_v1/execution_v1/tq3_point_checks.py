#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''TQ-3 offline point checks (no generation HTTP, no model calls).

Covers: hard-budget logic, ledger reserve/settle math, prompt-cap logic,
input isolation (actor/B/C), template extraction, schedule order,
anomaly-output parsing, crash-resume item states, real scoring entry,
dual-channel pin hashing, full 52-file manifest check.
Writes execution_v1/tests/point_checks_<host>_<ts>.json.
'''
import hashlib
import json
import socket
import sys
import tempfile
from pathlib import Path

EXEC = Path(__file__).resolve().parent
TQ3 = EXEC.parent
sys.path.insert(0, str(EXEC))
sys.path.insert(0, str(TQ3 / 'tools'))

import tq3_runner as R
import tq3_scoring_entry as SE

TESTS = []


def add(name, ok, detail):
    TESTS.append({'test': name, 'passed': bool(ok), 'detail': detail})


def t_constants():
    ok = (R.GEN_REQUEST_CAP == 40 and R.TOTAL_TOKEN_CAP == 400000 and R.RESERVE_TOKENS == 10240
          and R.PROMPT_TOKEN_CAP == 8192 and R.GEN_TOKEN_CAP == 2048 and R.RETRY_CAP == 4
          and R.WINDOW_CAP_MIN == 90 and R.REQUEST_TIMEOUT_S == 120)
    add('constants_hard_budgets', ok, {'gen_cap': R.GEN_REQUEST_CAP, 'token_cap': R.TOTAL_TOKEN_CAP,
                                       'reserve': R.RESERVE_TOKENS, 'prompt_cap': R.PROMPT_TOKEN_CAP,
                                       'retry_cap': R.RETRY_CAP, 'window_min': R.WINDOW_CAP_MIN})


def t_ledger_math():
    with tempfile.TemporaryDirectory() as td:
        led = R.Ledger(Path(td) / 'l.jsonl')
        led.append({'op': 'reserve', 'seq': 1, 'item_key': 'x', 'retry': False, 'reserved': 10240})
        a = led.unsettled_tokens()
        led.append({'op': 'settle', 'seq': 1, 'item_key': 'x', 'ok': True, 'settled': 500, 'freed': 9740})
        b = led.unsettled_tokens()
        add('ledger_reserve_settle_math', a == 10240 and b == 500, {'after_reserve': a, 'after_settle': b})


def t_token_cap_refusal():
    with tempfile.TemporaryDirectory() as td:
        led = R.Ledger(Path(td) / 'l.jsonl')
        for i in range(39):
            led.append({'op': 'reserve', 'seq': i + 1, 'item_key': 'k' + str(i), 'retry': False, 'reserved': 10240})
        u = led.unsettled_tokens()
        would = u + R.RESERVE_TOKENS
        add('token_cap_refusal_logic', u == 399360 and would > R.TOTAL_TOKEN_CAP,
            {'unsettled': u, 'would_be': would, 'cap': R.TOTAL_TOKEN_CAP})


def t_retry_cap_counter():
    with tempfile.TemporaryDirectory() as td:
        led = R.Ledger(Path(td) / 'l.jsonl')
        for i in range(4):
            led.append({'op': 'reserve', 'seq': i + 1, 'item_key': 'k', 'retry': True, 'reserved': 10240})
        add('retry_cap_counter', led.retries_used() == 4, {'retries_used': led.retries_used()})


def t_prompt_estimates():
    tpl = R.parse_templates()
    inputs = R.load_inputs()
    phase1, phase2 = R.build_schedule()
    mx = 0
    for item in phase1:
        msgs = R.render_actor(tpl, item['case'], inputs[(item['case'], item['variant'])])
        est = len((msgs[0]['content'] + chr(10) + msgs[1]['content']).encode('utf-8')) + 512
        mx = max(mx, est)
    add('prompt_estimates_under_cap', mx < R.PROMPT_TOKEN_CAP, {'max_byte_bound': mx, 'cap': R.PROMPT_TOKEN_CAP})


def t_isolation_actor():
    tpl = R.parse_templates()
    inputs = R.load_inputs()
    forbidden = ['perturbed', 'variant', 'official_reference', 'dev_panel', 'specs_rev1', 'injection', 'checker_verdict']
    bad = []
    for (case, var), rec in inputs.items():
        msgs = R.render_actor(tpl, case, rec)
        joined = msgs[0]['content'] + chr(10) + msgs[1]['content']
        src = json.dumps({'q': rec['question'], 't': rec['table'], 'p': rec['paragraphs']}, ensure_ascii=False)
        for f in forbidden:
            if f in joined and f not in src:
                bad.append({'case': case, 'variant': var, 'token': f})
        if rec['question'] not in joined:
            bad.append({'case': case, 'variant': var, 'token': 'question_missing'})
    add('isolation_actor_no_pipeline_leak', not bad, {'violations': bad})


def t_isolation_bc():
    tpl = R.parse_templates()
    inputs = R.load_inputs()
    rec = inputs[('Q03', 'original')]
    fx = {'task_id': 'Q03', 'answer': '14054', 'evidence': [{'table_row': 2, 'table_col': 2}], 'notes': 'MARKER-NOTE-3141'}
    mb = R.render_b(tpl, rec, fx)
    mc = R.render_c(tpl, rec, fx)
    jb = mb[0]['content'] + chr(10) + mb[1]['content']
    jc = mc[0]['content'] + chr(10) + mc[1]['content']
    ok = ('MARKER-NOTE-3141' in jb and 'table_row' in jb and '14054' in jc
          and 'MARKER-NOTE-3141' not in jc and 'table_row' not in jc)
    add('isolation_b_vs_c_evidence_exposure', ok,
        {'b_has_notes': 'MARKER-NOTE-3141' in jb, 'c_has_notes': 'MARKER-NOTE-3141' in jc,
         'c_has_table_row': 'table_row' in jc, 'c_has_answer': '14054' in jc})


def t_template_extraction():
    tpl = R.parse_templates()
    ok = True
    detail = {}
    for k in ('a', 'b', 'c'):
        s, u = tpl[k]
        detail[k] = {'system_len': len(s), 'user_len': len(u), 'system_head': s[:45], 'sha256': hashlib.sha256((s + chr(10) + u).encode('utf-8')).hexdigest()}
        if len(s) < 30 or len(u) < 30:
            ok = False
    if not tpl['a'][0].startswith('You answer financial table questions.'):
        ok = False
    if not tpl['b'][0].startswith('You are a careful verifier'):
        ok = False
    if not tpl['c'][0].startswith('You independently solve the task'):
        ok = False
    add('template_extraction', ok, detail)


def t_schedule_order():
    p1, p2 = R.build_schedule()
    ok1 = [i['key'] for i in p1] == ['actor|' + c + '|' + v for c in R.CASES for v in R.VARIANTS]
    seq = [i['arm'] for i in p2[:4]]
    ok2 = seq == ['b', 'c', 'c', 'b']
    ok3 = len(p1) == 12 and len(p2) == 24
    add('schedule_order', ok1 and ok2 and ok3, {'phase1_ok': ok1, 'first_four_arms': seq, 'counts': [len(p1), len(p2)]})


def t_anomaly_parsing():
    obj, valid, err = R.parse_actor_text('not json')
    a = (obj is None and valid is False and err == 'json_parse_error')
    obj2, valid2, err2 = R.parse_actor_text('{"task_id": "Q02"}')
    b = (valid2 is False and err2 == 'missing_or_empty_answer')
    obj3, valid3, err3 = R.parse_actor_text('{"answer": "x"}')
    c = (valid3 is True and err3 is None)
    d1, de1 = R.parse_decision_text('{"decision": "maybe"}')
    d2, de2 = R.parse_decision_text('{"decision": "accept"}')
    d = (d1 is None and de1 == 'invalid_decision' and d2 is not None and de2 is None)
    add('anomaly_output_parsing', a and b and c and d,
        {'bad_json_rejected': a, 'missing_answer_invalid': b, 'good_valid': c, 'decision_validation': d})


def t_crash_resume_state():
    with tempfile.TemporaryDirectory() as td:
        led = R.Ledger(Path(td) / 'l.jsonl')
        led.append({'op': 'reserve', 'seq': 1, 'item_key': 'k1', 'retry': False, 'reserved': 10240})
        led.append({'op': 'settle', 'seq': 1, 'item_key': 'k1', 'ok': True, 'settled': 300, 'freed': 9940})
        led.append({'op': 'reserve', 'seq': 2, 'item_key': 'k2', 'retry': False, 'reserved': 10240})
        s1 = led.item_state('k1')
        s2 = led.item_state('k2')
        s3 = led.item_state('k3')
        gen = led.gen_attempts()
        add('crash_resume_item_state', s1 == 'done' and s2 == 'inflight' and s3 == 'pending' and gen == 2,
            {'k1': s1, 'k2': s2, 'k3': s3, 'gen_attempts': gen})


def t_scoring_entry():
    def load(case):
        return json.loads((TQ3 / 'dev_panel' / 'scoring' / (case + '.json')).read_text(encoding='utf-8-sig'))
    r1 = SE.score('Q03', {'answer': '14054'}, load('Q03'))
    r2 = SE.score('Q03', {'answer': '9999'}, load('Q03'))
    r3 = SE.score('Q02', {'answer': 'Segment assets are composed of accounts receivable, inventories, and net property, plant, and equipment.'}, load('Q02'))
    r4 = SE.score('Q05', {'answer': '2029-01-31'}, load('Q05'))
    fake = {'task_id': 'X', 'compare_mode': 'numeric', 'expected_precise': 1.0, 'abs_tolerance': 0.01, 'unit_scale_status': 'UNRESOLVED'}
    r5 = SE.score('X', {'answer': '1.0'}, fake)
    ok = (r1['status'] == 'MATCH' and r2['status'] == 'NO_MATCH' and r3['status'] == 'MATCH'
          and r4['status'] == 'MATCH' and r5['status'] == 'BLOCKED_SCALE_UNRESOLVED' and r5['score'] is None)
    add('scoring_entry_integration', ok, {'q03_match': r1, 'q03_no_match': r2, 'q02_span': r3, 'q05_date': r4, 'unresolved': r5})


def t_pin_channel():
    data_lf = ('line1' + chr(10) + 'line2' + chr(10)).encode('utf-8')
    data_crlf = data_lf.replace(R.LF, R.CRLF)
    exp_crlf = hashlib.sha256(data_crlf).hexdigest()
    exp_lf = hashlib.sha256(data_lf).hexdigest()
    o1 = R.seamash_expected(exp_crlf, data_lf)
    o2 = R.seamash_expected(exp_lf, data_crlf)
    o3 = R.seamash_expected(exp_lf, data_lf)
    o4 = R.seamash_expected('0' * 64, data_lf)
    ok = (o1 == 'crlf' and o2 == 'lf' and o3 == 'raw' and o4 is None)
    add('pin_hash_dual_channel', ok, {'gb10_lf_vs_crlf_expected': o1, 'crlf_vs_lf_expected': o2, 'same_channel': o3, 'wrong_hash': o4})


def t_full_pins():
    r = R.check_material_pins()
    add('material_pin_check_full', r['ok'], {'checked': r['checked'], 'mismatch_count': len(r['mismatches']), 'unreadable': len(r['unreadable'])})


def main():
    host = socket.gethostname()
    t_constants()
    t_ledger_math()
    t_token_cap_refusal()
    t_retry_cap_counter()
    t_prompt_estimates()
    t_isolation_actor()
    t_isolation_bc()
    t_template_extraction()
    t_schedule_order()
    t_anomaly_parsing()
    t_crash_resume_state()
    t_scoring_entry()
    t_pin_channel()
    t_full_pins()
    report = {'schema': 'tq3_point_checks_v1', 'host': host, 'generated_utc': R.iso(),
              'runner_sha256': hashlib.sha256(Path(R.__file__).read_bytes()).hexdigest(),
              'auth_sha256': hashlib.sha256(R.AUTH_FILE.read_bytes()).hexdigest() if R.AUTH_FILE.exists() else None,
              'templates_sha256': hashlib.sha256(R.TEMPLATES_MD.read_bytes()).hexdigest(),
              'python': sys.version,
              'tests': TESTS, 'all_passed': all(t['passed'] for t in TESTS)}
    out_dir = EXEC / 'tests'
    out_dir.mkdir(exist_ok=True)
    ts = R.now_utc().strftime('%Y%m%dT%H%M%SZ')
    out = out_dir / ('point_checks_' + host + '_' + ts + '.json')
    R.write_json(out, report)
    print(json.dumps({'all_passed': report['all_passed'], 'failed': [t['test'] for t in TESTS if not t['passed']], 'out': str(out)}, ensure_ascii=True))
    return 0 if report['all_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
