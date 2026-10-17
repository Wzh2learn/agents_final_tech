# -*- coding: utf-8 -*-
"""TQ-4 run-post independent recomputation (read-only against the run tree).

Scope: the executed TQ-4 run 20261016T082849Z_430d927a (S3 focused review).
Re-derives, from raw artifacts only: receipt/ledger accounting, budget/window,
Part 1 scoring+legality, Part 2 decisions/matrix/duplicate pairs, prompt
isolation, and report consistency. Writes only its own JSON output (argv[1]).
No network, no model calls, no mutation of the reviewed tree (bytecode writes
disabled).

Run:  python POST_RUN_RECOMPUTE_v1.py POST_RUN_RECOMPUTE_v1.json
"""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent          # reviews/
TQ4 = HERE.parent                               # tq4_calibration_v1/
BASE = TQ4.parent                               # task_gold_qualification_v1/
RUN = TQ4 / 'runs' / '20261016T082849Z_430d927a'
EXEC = TQ4 / 'execution_v1'
sys.path.insert(0, str(EXEC))
import tq4_scoring_entry_v21 as V21  # noqa: E402


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha_lf(p):
    return hashlib.sha256(Path(p).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def nsp(s):
    return re.sub(r'\s+', '', str(s))


R = {'schema': 'tq4_post_run_recompute_v1', 'run_id': RUN.name, 'checks': {}, 'notes': []}

cfg = load(EXEC / 'chain_config_tq4.json')
meta = load(RUN / 'RUN_META.json')
receipt = load(RUN / 'RECEIPT.json')
ledger_lines = [json.loads(l) for l in (RUN / 'request_ledger.jsonl').read_text(encoding='utf-8-sig').splitlines() if l.strip()]
aux_lines = [json.loads(l) for l in (RUN / 'aux_ledger.jsonl').read_text(encoding='utf-8-sig').splitlines() if l.strip()]


def find_raw(seq):
    hits = sorted((RUN / 'raw').glob(str(seq).zfill(4) + '_*.json'))
    assert len(hits) == 1, 'raw seq %s hits=%s' % (seq, hits)
    return load(hits[0])


def find_prompt(seq):
    hits = sorted((RUN / 'prompts').glob(str(seq).zfill(4) + '_*.json'))
    assert len(hits) == 1, 'prompt seq %s hits=%s' % (seq, hits)
    return load(hits[0])


def step_by_key(key):
    return next(s for s in cfg['steps'] if s['key'] == key)


def check_a():
    """A. Run tree integrity, receipts vs ledgers, pins, config hashes."""
    a = {}
    m = load(RUN / 'RUN_MANIFEST.json')
    bad = []
    for e in m['files']:
        p = RUN / e['path']
        if not p.exists() or sha(p) != e['sha256'] or p.stat().st_size != e['bytes']:
            bad.append(e['path'])
    on_disk = sorted(p.relative_to(RUN).as_posix() for p in RUN.rglob('*') if p.is_file())
    listed = {e['path'] for e in m['files']}
    a['manifest'] = {'files': len(m['files']), 'bad': bad, 'self_excluded': m.get('self_excluded'),
                     'extra_on_disk': sorted(set(on_disk) - listed),
                     'listed_not_on_disk': sorted(listed - set(on_disk))}

    reserve = [e for e in ledger_lines if e.get('op') == 'reserve']
    settle = [e for e in ledger_lines if e.get('op') == 'settle']
    a['ledger'] = {
        'reserves': len(reserve), 'settles': len(settle),
        'retries': sum(1 for e in reserve if e.get('retry')),
        'settled_tokens': sum(int(e.get('settled', 0)) for e in settle),
        'reserved_total': sum(int(e.get('reserved', 0)) for e in reserve),
        'freed_total': sum(int(e.get('freed', 0)) for e in settle),
        'first_reserve_utc': reserve[0]['utc'], 'last_settle_utc': settle[-1]['utc'],
        'seqs': [e['seq'] for e in reserve],
    }
    a['ledger']['unsettled_net'] = a['ledger']['reserved_total'] - a['ledger']['freed_total']
    # serialization: each settle must precede the next reserve
    viol = 0
    for i in range(len(reserve) - 1):
        s = [e for e in settle if e['seq'] == reserve[i]['seq']]
        if not s or s[0]['utc'] > reserve[i + 1]['utc']:
            viol += 1
    a['ledger']['serial_violations'] = viol
    a['receipt_vs_ledger'] = {
        'gen_attempts': receipt['gen_attempts'] == len(reserve),
        'retries': receipt['retries_used'] == a['ledger']['retries'],
        'tokens': receipt['tokens_settled'] == a['ledger']['settled_tokens'],
        'steps_total': receipt['steps_total'] == len(cfg['steps']),
        'first_request_utc': receipt['first_request_utc'] == reserve[0]['utc'],
        'status': receipt['status'] == 'COMPLETED' and receipt['stop_reason'] is None,
        'tokens_unsettled_equals_settled': receipt['tokens_unsettled'] == receipt['tokens_settled'],
    }
    from collections import Counter
    a['aux'] = {
        'lines': len(aux_lines),
        'by_type_done': dict(Counter(e.get('type') for e in aux_lines if e.get('op') == 'aux_done')),
        'sends': sum(1 for e in aux_lines if e.get('op') == 'aux_send'),
        'receipt_aux_ops': receipt.get('aux_ops'),
    }
    a['pins'] = {'before': load(RUN / 'PIN_CHECK_BEFORE.json'), 'after': load(RUN / 'PIN_CHECK_AFTER.json')}
    pins = load(EXEC / 'tq4_material_pins_lf_v1.json')
    pin_bad, pin_missing = [], []
    for rel, h in pins['files'].items():
        p = TQ4 / rel
        if not p.exists():
            pin_missing.append(rel)
        elif sha_lf(p) != h:
            pin_bad.append(rel)
    a['material_pins'] = {'count': len(pins['files']), 'mismatch_lf': pin_bad, 'missing': pin_missing,
                          'source_manifest_sha_ok': sha(TQ4 / 'MANIFEST.json') == pins['source_manifest_sha256']}
    mp = load(RUN / 'MODEL_PIN.json')
    a['model_pin'] = {
        'identity_ok': mp.get('identity_ok'),
        'model_sha_matches_authorization': mp.get('model_file_sha256') == '4ac6a06bce551257267f49ad2226f8671a22519ccc1a4dde9d5b433d1f2a410d',
        'server_sha_matches_authorization': mp.get('server_bin_sha256') == '037e02419e78256ed4227af31fc0b2602ff04c670fb7ad4fa2429fafb03bd55d',
        'model_id': mp.get('model_id'), 'base_url': mp.get('base_url'),
    }
    hash_targets = [('config_sha256', EXEC / 'chain_config_tq4.json'),
                    ('runner_sha256', EXEC / 'chain_runner.py'),
                    ('templates_md_sha256', TQ4 / 'run_card_v2' / 'prompt_templates_v2.md'),
                    ('authorization_sha256', TQ4 / 'run_card_v2' / 'OWNER_DELEGATED_AUTHORIZATION_20261016_v1.md')]
    hm = {}
    for k, p in hash_targets:
        hm[k] = {'raw_match': meta.get(k) == sha(p), 'lf_match': meta.get(k) == sha_lf(p)}
    a['run_meta_hashes'] = hm
    cfgpath = EXEC / 'chain_config_tq4.json'
    a['config_pin_detail'] = {
        'recorded': meta.get('config_sha256'),
        'current_raw': sha(cfgpath),
        'current_lf': sha_lf(cfgpath),
        'reproducible_raw_or_lf': meta.get('config_sha256') in (sha(cfgpath), sha_lf(cfgpath)),
        'file_mtime_local': datetime.fromtimestamp(cfgpath.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
    }
    a['exec_files_pinned'] = {
        'run_card_v2/prompt_templates_v2.md': 'run_card_v2/prompt_templates_v2.md' in pins['files'],
        'execution_v1/chain_config_tq4.json': 'execution_v1/chain_config_tq4.json' in pins['files'],
        'execution_v1/chain_runner.py': 'execution_v1/chain_runner.py' in pins['files'],
        'execution_v1/tq4_scoring_entry_v21.py': 'execution_v1/tq4_scoring_entry_v21.py' in pins['files'],
    }
    return a


def check_b():
    """B. Budget / window / parameter uniformity across all 36 raw files."""
    b = {}
    expect_params = {'temperature': 0, 'top_p': 1, 'seed': 20261016, 'max_tokens': 2048, 'stream': False,
                     'response_format': {'type': 'json_object'}, 'chat_template_kwargs': {'enable_thinking': False}}
    probs = []
    raw_summary = []
    for s in cfg['steps']:
        r = find_raw(s['step'])
        req = r.get('request') or {}
        ok = (r['item_key'] == s['key'] and r['arm'] == s['kind'] and r['case'] == s['task_id']
              and r.get('retry') is False and (r.get('http') or {}).get('ok') is True
              and (r.get('http') or {}).get('status') == 200
              and req.get('model') == 'Qwen3.6-35B-A3B-Q4_K_M.gguf'
              and req.get('params') == expect_params
              and r.get('variant') == 'perturbed')
        if not ok:
            probs.append({'seq': s['step'], 'key': s['key'], 'item': r['item_key'], 'retry': r.get('retry'),
                          'http': r.get('http', {}).get('status'), 'model': req.get('model'),
                          'params_match': req.get('params') == expect_params})
        u = r.get('usage') or {}
        raw_summary.append({'seq': s['step'], 'key': s['key'], 'valid': bool((r.get('parse') or {}).get('valid')),
                            'tokens': u.get('total_tokens'), 'variant': r.get('variant'),
                            'elapsed_s': (r.get('http') or {}).get('elapsed_s')})
    b['raw_uniformity'] = {'problems': probs, 'checked': len(raw_summary),
                           'total_tokens_from_raw': sum(x['tokens'] or 0 for x in raw_summary),
                           'variant_perturbed_all': all(x['variant'] == 'perturbed' for x in raw_summary)}
    # window in Beijing time
    first = receipt['first_request_utc']
    last_utc = [e for e in ledger_lines if e.get('op') == 'settle'][-1]['utc']
    dur_s = 0
    from datetime import datetime, timezone, timedelta
    t0 = datetime.strptime(first, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    t1 = datetime.strptime(last_utc, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    dur_s = (t1 - t0).total_seconds()
    bj = t0.astimezone(timezone(timedelta(hours=8)))
    b['window'] = {'first_bj': bj.strftime('%Y-%m-%d %H:%M:%S'), 'duration_s': dur_s,
                   'start_in_09_00_18_30': (9 <= bj.hour < 18) or (bj.hour == 18 and bj.minute <= 30),
                   'date_allowed': bj.strftime('%Y-%m-%d') in cfg['budget']['allowed_dates'],
                   'within_90min': dur_s <= 90 * 60}
    b['caps'] = {'attempts_le_40': len([e for e in ledger_lines if e.get('op') == 'reserve']) <= cfg['budget']['gen_cap'],
                 'retries_le_4': sum(1 for e in ledger_lines if e.get('op') == 'reserve' and e.get('retry')) <= cfg['budget']['retry_cap'],
                 'tokens_le_cap': receipt['tokens_settled'] <= cfg['budget']['token_cap']}
    return b


def check_c():
    """C. Part 1: recompute scoring, legality, B/C decisions from raw."""
    c = {'rows': []}
    for s in cfg['steps']:
        if s['kind'] != 'actor':
            continue
        r = find_raw(s['step'])
        actor = r['parse']['result']
        mat = load(TQ4 / cfg['scoring_dir'] / (s['task_id'] + '.json'))
        inp = load(TQ4 / s['input'])
        sc = V21.score(s['task_id'], actor, mat)
        leg = V21.check_evidence_legality(inp['table'], inp['paragraphs'], actor.get('evidence'))
        bstep = step_by_key('b|' + s['task_id'])
        cstep = step_by_key('c|' + s['task_id'])
        rb = find_raw(bstep['step'])
        rc = find_raw(cstep['step'])
        c['rows'].append({'task_id': s['task_id'], 'answer': actor.get('answer'),
                          'my_scoring': sc['status'], 'my_score_detail': sc.get('detail'),
                          'my_legality': leg['legal'], 'my_legality_issues': [i['issue'] for i in leg['issues']],
                          'b': (rb['parse']['result'] or {}).get('decision'),
                          'c': (rc['parse']['result'] or {}).get('decision')})
    stored = load(RUN / 'part1_results.json')
    rowwise = []
    for mrow, srow in zip(c['rows'], stored['rows']):
        rowwise.append({
            'task': mrow['task_id'],
            'scoring_match': mrow['my_scoring'] == srow['scoring_v21']['status'],
            'detail_match': mrow['my_score_detail'] == srow['scoring_v21'].get('detail'),
            'legality_match': mrow['my_legality'] == srow['legality_v21']['legal'],
            'b_match': mrow['b'] == srow['b'], 'c_match': mrow['c'] == srow['c']})
    summ = stored['summary']
    c['rowwise'] = rowwise
    c['recomputed_summary'] = {
        'match': sum(1 for r in c['rows'] if r['my_scoring'] == 'MATCH'),
        'legality': {'legal': sum(1 for r in c['rows'] if r['my_legality']),
                     'illegal': sum(1 for r in c['rows'] if not r['my_legality'])},
        'b': dict((d, sum(1 for r in c['rows'] if r['b'] == d)) for d in ('accept', 'alarm', 'abstain')),
        'c': dict((d, sum(1 for r in c['rows'] if r['c'] == d)) for d in ('accept', 'alarm', 'abstain')),
    }
    c['summary_claims_ok'] = (
        summ['valid'] == 4 and summ['match_over_planned'] == 1.0 and summ['match_over_valid'] == 1.0
        and summ['legality'] == {'legal': 4, 'illegal': 0})
    # key-event quotes (N1 B/C)
    rb = find_raw(step_by_key('b|N1')['step'])['parse']['result']
    rc = find_raw(step_by_key('c|N1')['step'])['parse']['result']
    c['n1_event'] = {
        'b': {'decision': rb['decision'], 'reason_head': rb['reason'][:500]},
        'c': {'decision': rc['decision'], 'reason_head': rc['reason'][:500]},
        'b_has_semantic_marker': any(t in rb['reason'].lower() for t in ['category error', 'semantically', 'semantic']),
        'c_has_semantic_marker': any(t in rc['reason'].lower() for t in ['category error', 'semantically', 'semantic']),
    }
    ref = load(TQ4 / 'panel_v2' / 'natural' / 'reference' / 'N1.json')
    c['n1_reference'] = ref['official_reference']
    c['n1_event']['b_has_category_error_phrase'] = 'category error' in rb['reason'].lower()
    c['n1_event']['c_has_semantically_awkward_phrase'] = 'semantically awkward' in rc['reason'].lower()
    c['n1_event']['c_contradiction_points'] = rc.get('contradiction_points')
    c['n1_event']['c_reason_ends_accept'] = 'I will accept it' in rc['reason']
    c['n1_event']['c_reason_tail'] = rc['reason'][-280:]
    def _reason(seq):
        return find_raw(seq)['parse']['result']['reason']
    c['spot_reasons'] = {
        'q03c3_b': _reason(25)[:500], 'q03c3_c': _reason(26)[:500],
        'q03c4_c': _reason(27)[:500], 'q03c4_b': _reason(28)[:500],
        'q03c2_b': _reason(24)[:420], 'q03c1_c': _reason(22)[:420],
        'q03c2_c': _reason(23)[:420], 'q04c3_c': _reason(34)[:420], 'q04c4_c': _reason(35)[:420],
    }
    c['quote_checks'] = {
        'q03_direction_quote_c3c4': 'can imply A - B or B - A' in _reason(26),
        'q03_c3_c4_same_reason': _reason(26) == _reason(27),
        'b_q03c3_matches_exactly': 'matches this calculation exactly' in _reason(25),
        'b_row99_q03c2': 'row 99' in _reason(24).lower(),
        'b_row99_q03c4': 'row 99' in _reason(28).lower(),
        'c_unit_missing_q03c1': 'SEK million' in _reason(22),
        'c_unit_missing_q03c2': 'SEK million' in _reason(23),
        'c_year_semantics_q04c3': ('chronological' in _reason(34).lower() or 'as of' in _reason(34).lower()),
        'c_year_semantics_q04c4': ('chronological' in _reason(35).lower() or 'as of' in _reason(35).lower()),
    }
    return c


def check_d():
    """D. Part 2: recompute decisions, validity, matrix (both semantics), pairs."""
    d = {'rows': [], 'pairs': []}
    cands = load(TQ4 / cfg['candidates_file'])['candidates']
    stored = load(RUN / 'part2_results.json')
    srows = {r['candidate_id']: r for r in stored['rows']}
    for cand in cands:
        cid = cand['candidate_id']
        bstep = next(s for s in cfg['steps'] if s.get('candidate_id') == cid and s['kind'] == 'b')
        cstep = next(s for s in cfg['steps'] if s.get('candidate_id') == cid and s['kind'] == 'c')
        rb = find_raw(bstep['step'])
        rc = find_raw(cstep['step'])
        pb, pc = rb.get('parse') or {}, rc.get('parse') or {}
        bdec = (pb.get('result') or {}).get('decision')
        cdec = (pc.get('result') or {}).get('decision')
        leg = V21.check_evidence_legality(load(TQ4 / bstep['input'])['table'],
                                          load(TQ4 / bstep['input'])['paragraphs'], cand.get('evidence'))
        d['rows'].append({
            'candidate_id': cid, 'label': cand['label'],
            'b_valid': bool(pb.get('valid')), 'b_error': pb.get('error'), 'b_decision': bdec,
            'c_valid': bool(pc.get('valid')), 'c_decision': cdec,
            'b_stored': srows[cid]['b'], 'c_stored': srows[cid]['c'],
            'b_stored_match_machine': (srows[cid]['b'] == (bdec or 'done')),
            'c_stored_match_machine': (srows[cid]['c'] == cdec),
            'legality_label': cand['label']['evidence_legality'], 'legality_recomputed': leg['legal'],
            'legality_recompute_ok': leg['legal'] == (cand['label']['evidence_legality'] == 'legal'),
        })
    b_valid = sum(1 for r in d['rows'] if r['b_valid'])
    c_valid = sum(1 for r in d['rows'] if r['c_valid'])
    d['valid_counts'] = {'b': b_valid, 'c': c_valid, 'b_invalid': len(d['rows']) - b_valid}
    d['matrix_machine'] = {}
    d['matrix_strict'] = {}
    for r in d['rows']:
        combo = r['label']['answer_kind'] + '+' + r['label']['evidence_legality']
        for name, bd, cd in (('matrix_machine', r['b_stored'], r['c_stored']),
                             ('matrix_strict', r['b_decision'] if r['b_valid'] else 'invalid',
                              r['c_decision'] if r['c_valid'] else 'invalid')):
            tgt = d[name].setdefault(combo, {'b': {}, 'c': {}})
            tgt['b'][bd] = tgt['b'].get(bd, 0) + 1
            tgt['c'][cd] = tgt['c'].get(cd, 0) + 1
    d['matrix_machine_matches_stored'] = d['matrix_machine'] == stored['matrix']
    # duplicate-stimulus pairs: recompute prompt equality + decision agreement
    for tid in ('Q02', 'Q03', 'Q04'):
        for p in (('C1', 'C2'), ('C3', 'C4')):
            a, b2 = tid + '-' + p[0], tid + '-' + p[1]
            sa = next(s for s in cfg['steps'] if s.get('candidate_id') == a and s['kind'] == 'c')
            sb = next(s for s in cfg['steps'] if s.get('candidate_id') == b2 and s['kind'] == 'c')
            pa, pbb = find_prompt(sa['step']), find_prompt(sb['step'])
            same = pa['messages'] == pbb['messages']
            canon_a = hashlib.sha256(json.dumps(pa['messages'], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            canon_b = hashlib.sha256(json.dumps(pbb['messages'], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            da = next(r['c_decision'] for r in d['rows'] if r['candidate_id'] == a)
            db = next(r['c_decision'] for r in d['rows'] if r['candidate_id'] == b2)
            d['pairs'].append({'pair': [a, b2], 'identical_prompt': same, 'canonical_sha_equal': canon_a == canon_b,
                               'c_decisions': [da, db], 'c_agree': da == db})
    d['pairs_all_identical'] = all(x['identical_prompt'] for x in d['pairs'])
    d['pairs_all_canonical'] = all(x.get('canonical_sha_equal') for x in d['pairs'])
    d['pairs_all_agree'] = all(x['c_agree'] for x in d['pairs'])
    # broken B output specifics
    rb = find_raw(next(s for s in cfg['steps'] if s.get('candidate_id') == 'Q04-C2' and s['kind'] == 'b')['step'])
    body = json.loads(rb['http']['body_text'])
    frag = body['choices'][0]['message']['content']
    try:
        json.loads(frag)
        parse_fail = False
        err = 'PARSE_OK'
    except Exception as e:  # noqa: BLE001
        parse_fail = True
        err = str(e)
    d['broken_b_q04c2'] = {'parse_fail_on_content': parse_fail, 'error': str(err)[:160],
                           'finish_reason': body['choices'][0].get('finish_reason'),
                           'completion_tokens': body.get('usage', {}).get('completion_tokens'),
                           'content_len': len(frag)}
    fl = frag.lower()
    d['broken_b_q04c2']['prose_has_citation_critique'] = ('citation' in fl)
    d['broken_b_q04c2']['prose_has_alarm_intent'] = ('"decision": "alarm"' in frag) or ('"decision":"alarm"' in frag)
    d['legality_all_ok'] = all(r['legality_recompute_ok'] for r in d['rows'])
    return d


def check_e():
    """E. Isolation: prompt scans, B-sees-evidence / C-does-not, payload anchors."""
    e = {'violations': [], 'checks': {'b_markers': 0, 'c_markers': 0, 'a_markers': 0}}
    bad_tokens = ['answer_kind', 'evidence_legality', 'candidate_id', 'frozen_design_target',
                  'support_target', 'injection', 'v4_label', 'checker_verdict', 'correct+', 'incorrect+',
                  '"variant"', 'perturbed']
    cid_list = [c['candidate_id'] for c in load(TQ4 / cfg['candidates_file'])['candidates']]
    def msg_text(pr):
        return nsp('\n'.join(str(m.get('content', '')) for m in pr['messages']))
    for s in cfg['steps']:
        pr = find_prompt(s['step'])
        text = msg_text(pr)
        for tok in bad_tokens:
            if tok in text:
                e['violations'].append({'seq': s['step'], 'key': s['key'], 'token': tok})
        for cid in cid_list:
            if cid in text:
                e['violations'].append({'seq': s['step'], 'key': s['key'], 'token': 'candidate_id:' + cid})
        if s['kind'] == 'b':
            if 'Candidate answer (from another system):' in text:
                e['checks']['b_markers'] += 1
        elif s['kind'] == 'c':
            if 'Candidate final answer:' in text:
                e['checks']['c_markers'] += 1
        else:
            e['checks']['a_markers'] += 1
    # B sees evidence / C does not: per candidate
    per = []
    cands = load(TQ4 / cfg['candidates_file'])['candidates']
    for cand in cands:
        cid = cand['candidate_id']
        bstep = next(s for s in cfg['steps'] if s.get('candidate_id') == cid and s['kind'] == 'b')
        cstep = next(s for s in cfg['steps'] if s.get('candidate_id') == cid and s['kind'] == 'c')
        tb = msg_text(find_prompt(bstep['step']))
        tc = msg_text(find_prompt(cstep['step']))
        compact = json.dumps({'task_id': cand['task_id'], 'answer': cand['answer'], 'evidence': cand['evidence']},
                             ensure_ascii=False, separators=(',', ':'))
        ev_json = json.dumps(cand['evidence'], ensure_ascii=False, separators=(',', ':'))
        answer_n = nsp(cand['answer'])
        per.append({'candidate_id': cid,
                    'b_contains_full_json': nsp(compact) in tb,
                    'b_contains_evidence': nsp(ev_json) in tb,
                    'c_contains_answer': answer_n in tc,
                    'c_contains_evidence': nsp(ev_json) in tc,
                    'c_contains_evidence_word': 'evidence' in tc.lower()})
    e['b_evidence_c_answer_only'] = per
    # Part 1: B sees actor answer+evidence; C sees answer only
    per1 = []
    for tid in ('N1', 'N2', 'N3', 'N4'):
        actor = find_raw(step_by_key('actor|' + tid)['step'])['parse']['result']
        tb = msg_text(find_prompt(step_by_key('b|' + tid)['step']))
        tc = msg_text(find_prompt(step_by_key('c|' + tid)['step']))
        ev_json = json.dumps(actor.get('evidence'), ensure_ascii=False, separators=(',', ':'))
        per1.append({'task_id': tid,
                     'b_contains_answer': nsp(actor['answer']) in tb,
                     'c_contains_answer': nsp(actor['answer']) in tc,
                     'b_contains_evidence': nsp(ev_json) in tb if actor.get('evidence') else None,
                     'c_contains_evidence_json': nsp(ev_json) in tc if actor.get('evidence') else None})
    e['part1_b_c'] = per1
    return e


def check_f():
    """F. Report consistency: RUN_RETURN vs machine artifacts; boundary claims."""
    f = {}
    rt = (EXEC / 'TQ4_RUN_RETURN.md').read_text(encoding='utf-8')
    summd = (RUN / 'SUMMARY.md').read_text(encoding='utf-8')
    results = load(RUN / 'RESULTS.json')
    f['return_boundaries'] = {
        'not_established': 'scientific_gold_validity = NOT_ESTABLISHED' in rt.replace('`', ''),
        'support_not_assessed': 'NOT_ASSESSED' in rt,
        'no_confirmatory': ('无 confirmatory claim' in rt) or ('无confirmatory' in rt),
        'duplicate_note': '同刺激重复' in rt,
    }
    f['machine_counts'] = {
        'part1_match_over_planned': results['part1']['summary']['match_over_planned'],
        'part2_b_valid': sum(1 for r in load(RUN / 'part2_results.json')['rows'] if 'invalid' not in str(r['b']) and str(r['b']) != 'done') + 0,
    }
    # narrative numeric claims vs machine files
    claims = {
        '36_36_success': ('36/36' in rt),
        'one_invalid': ('1/36' in rt),
        'denominator_35': ('35' in rt),
        'tokens_40205': ('40,205' in rt) or ('40205' in rt),
        'duplicate_6_6': ('6/6' in rt),
        'matrix_consistency_summary': ('done' in summd),
        'run_id': (RUN.name in rt),
    }
    f['narrative_claims'] = claims
    # point-check record summary (pre-run + post-run extras)
    pcs = {}
    for p in sorted((EXEC / 'tests').glob('chain_point_checks_tq4_*.json')):
        pc = load(p)
        pcs[p.name] = {'tests': len(pc['tests']), 'all_passed': pc['all_passed'],
                       'failed': [t['test'] for t in pc['tests'] if not t['passed']]}
    f['point_checks'] = pcs
    f['returns_13_13'] = ('13/13' in rt)
    # manifest self check + mirror claim present
    f['mirror_claim'] = {'dual_end_84': ('84' in rt and '\u53cc\u7aef' in rt)}
    times = re.findall(r'2026-10-16 (\d\d:\d\d:\d\d)', rt)
    f['timing_anchors'] = {
        'times_found': sorted(set(times)),
        'receipt_first_request_utc': receipt.get('first_request_utc'),
        'return_has_strict_first_request': ('16:29:02' in times),
        'return_has_created_time': ('16:28:49' in times),
    }
    hits = []
    for p2 in TQ4.rglob('*'):
        if not p2.is_file() or p2.suffix not in ('.md', '.json') or '__pycache__' in p2.parts or 'runs' in p2.parts:
            continue
        if 'POST_RUN' in p2.name or p2.name == 'TQ4_RUN_RETURN.md':
            continue
        try:
            tx = p2.read_text(encoding='utf-8', errors='ignore')
        except Exception:  # noqa: BLE001
            continue
        if '\u53cc\u7aef' in tx:
            hits.append(p2.relative_to(TQ4).as_posix())
    f['mirror_receipt_scan'] = hits[:10]
    return f


def main():
    R['checks']['A_integrity'] = check_a()
    R['checks']['B_budget_window'] = check_b()
    R['checks']['C_part1'] = check_c()
    R['checks']['D_part2'] = check_d()
    R['checks']['E_isolation'] = check_e()
    R['checks']['F_report'] = check_f()
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'POST_RUN_RECOMPUTE_v1.json'
    out.write_text(json.dumps(R, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')
    summary = {
        'A_manifest_bad': R['checks']['A_integrity']['manifest']['bad'],
        'A_pins_mismatch': R['checks']['A_integrity']['material_pins']['mismatch_lf'],
        'B_window': R['checks']['B_budget_window']['window'],
        'C_rowwise': R['checks']['C_part1']['rowwise'],
        'D_valid': R['checks']['D_part2']['valid_counts'],
        'D_pairs': R['checks']['D_part2']['pairs'],
        'E_violations': R['checks']['E_isolation']['violations'],
        'F_13_13': R['checks']['F_report']['returns_13_13'],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print('WROTE', out)


if __name__ == '__main__':
    main()
