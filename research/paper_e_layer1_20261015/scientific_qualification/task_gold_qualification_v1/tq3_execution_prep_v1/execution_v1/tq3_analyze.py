#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''TQ-3 post-run analysis (deterministic; no HTTP, no model).

Usage: python3 execution_v1/tq3_analyze.py <run_id>
Reads runs/<run_id>/ (ledgers, raw responses) + dev_panel reference/scoring.
Writes into the run dir:
  a_decisions.json, b_decisions.json, c_decisions.json,
  scoring/per_task_scoring.json, RESULTS.json, SUMMARY.md, RUN_MANIFEST.json.
'''
import hashlib
import json
import sys
from pathlib import Path

EXEC = Path(__file__).resolve().parent
TQ3 = EXEC.parent
sys.path.insert(0, str(EXEC))
sys.path.insert(0, str(TQ3 / 'tools'))

import tq3_runner as R
import tq3_scoring_entry as SE

FROZEN_NUMERIC_KEYWORDS = ['difference', 'change', 'percentage', 'proportion']


def load_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def raw_for(run_dir, ledger, key):
    seq = ledger.last_seq(key)
    if seq is None:
        return None
    prefix = str(seq).zfill(4) + '_'
    for p in sorted((run_dir / 'raw').glob(prefix + '*.json')):
        return load_json(p)
    return None


def a_decide(rec, obj):
    checks = {}
    valid = isinstance(obj, dict) and obj.get('answer') not in (None, '')
    checks['schema'] = 'PASS' if valid else 'FAIL'
    q = (rec.get('question') or '').lower()
    applies = any(k in q for k in FROZEN_NUMERIC_KEYWORDS)
    if not applies or not valid:
        checks['numeric_presence'] = 'NOT_APPLICABLE'
    else:
        ans = str(obj.get('answer'))
        checks['numeric_presence'] = 'PASS' if any(ch.isdigit() for ch in ans) else 'FAIL'
    ev = obj.get('evidence') if isinstance(obj, dict) else None
    if isinstance(ev, list) and ev:
        table = rec.get('table') or []
        bad = []
        for e in ev:
            try:
                r0 = int(e.get('table_row'))
                c0 = int(e.get('table_col'))
                if r0 < 0 or c0 < 0 or r0 >= len(table) or c0 >= len(table[r0]):
                    bad.append(e)
            except Exception:
                bad.append(e)
        checks['evidence_bounds'] = 'FAIL' if bad else 'PASS'
        checks['evidence_bad'] = bad
    else:
        checks['evidence_bounds'] = 'NOT_APPLICABLE'
    fails = [k for k, v in checks.items() if v == 'FAIL']
    checks['decision'] = 'alarm' if fails else 'accept'
    return checks


def arm_agg(rows, arm):
    states = {}
    decisions = {}
    by_layer = {}
    for r in rows:
        layer = r['scoring_status']
        a = r[arm] or {'state': 'not_run'}
        st = a['state']
        states[st] = states.get(st, 0) + 1
        dkey = a['decision'] if a.get('decision') else st
        decisions[dkey] = decisions.get(dkey, 0) + 1
        bl = by_layer.setdefault(layer, {})
        bl[dkey] = bl.get(dkey, 0) + 1
    return {'state_counts': states, 'decision_counts': decisions, 'by_layer': by_layer}


def main():
    if len(sys.argv) != 2:
        print('usage: tq3_analyze.py <run_id>')
        return 1
    run_id = sys.argv[1]
    run_dir = TQ3 / 'runs' / run_id
    ledger = R.Ledger(run_dir / 'request_ledger.jsonl')
    receipt = load_json(run_dir / 'RECEIPT.json') if (run_dir / 'RECEIPT.json').exists() else {}
    inputs = R.load_inputs()
    phase1, phase2 = R.build_schedule()
    skips = {}
    if (run_dir / 'skips.jsonl').exists():
        for line in (run_dir / 'skips.jsonl').read_text(encoding='utf-8').splitlines():
            if line.strip():
                j = json.loads(line)
                skips[j['item_key']] = j
    rows = []
    actor_by_key = {}
    for item in phase1:
        rec = inputs[(item['case'], item['variant'])]
        st = ledger.item_state(item['key'])
        raw = raw_for(run_dir, ledger, item['key'])
        obj = None
        parse = (raw or {}).get('parse') or {}
        if parse.get('valid') and isinstance(parse.get('result'), dict):
            obj = parse['result']
        if st == 'done' and obj is not None:
            actor_status = 'valid'
        elif st == 'done':
            actor_status = 'invalid'
        elif st == 'inflight':
            actor_status = 'crashed_no_result'
        elif st == 'failed':
            actor_status = 'request_failed'
        elif st == 'refused':
            actor_status = 'refused'
        else:
            actor_status = 'not_run'
        scoring_mat = load_json(TQ3 / 'dev_panel' / 'scoring' / (item['case'] + '.json'))
        if obj is not None:
            sc = SE.score(item['case'], obj, scoring_mat)
        elif actor_status == 'invalid':
            sc = {'task_id': item['case'], 'status': 'INVALID_ACTOR_OUTPUT', 'score': None}
        elif actor_status == 'not_run':
            sc = {'task_id': item['case'], 'status': 'NOT_RUN', 'score': None}
        else:
            sc = {'task_id': item['case'], 'status': 'NO_RESULT_' + actor_status.upper(), 'score': None}
        a = a_decide(rec, obj) if obj is not None else {'decision': 'not_run', 'reason': actor_status}
        row = {'item_key': item['key'], 'task_id': item['case'], 'variant': item['variant'],
               'actor_status': actor_status, 'answer': (obj or {}).get('answer') if obj else None,
               'scoring_status': sc['status'], 'scoring_score': sc['score'], 'a': a, 'b': None, 'c': None}
        rows.append(row)
        actor_by_key[item['key']] = row
    for item in phase2:
        row = actor_by_key.get(item['actor_key'])
        st = ledger.item_state(item['key'])
        raw = raw_for(run_dir, ledger, item['key'])
        parse = (raw or {}).get('parse') or {}
        dec = None
        if st == 'done' and isinstance(parse.get('result'), dict):
            tr = parse['result']
            dec = {'decision': tr.get('decision'), 'reason': tr.get('reason'),
                   'contradiction_points': tr.get('contradiction_points'), 'own_answer': tr.get('own_answer')}
        if item['key'] in skips:
            rec2 = {'status': 'skipped', 'reason': skips[item['key']].get('reason')}
            dec = None
        elif st == 'done' and dec is not None:
            rec2 = {'status': 'recorded'}
        elif st == 'done':
            rec2 = {'status': 'invalid'}
        elif st == 'inflight':
            rec2 = {'status': 'crashed_no_result'}
        elif st == 'failed':
            rec2 = {'status': 'request_failed'}
        elif st == 'refused':
            rec2 = {'status': 'refused'}
        else:
            rec2 = {'status': 'not_run'}
        arm_res = {'state': rec2['status'],
                   'decision': (dec or {}).get('decision') if dec else None,
                   'reason': (dec or {}).get('reason') if dec else None,
                   'own_answer': (dec or {}).get('own_answer') if dec else None,
                   'skip_reason': rec2.get('reason')}
        if row is not None:
            row[item['arm']] = arm_res
    n = len(rows)
    v = sum(1 for r in rows if r['actor_status'] == 'valid')
    m = sum(1 for r in rows if r['scoring_status'] == 'MATCH')
    actor_agg = {'planned': n, 'valid': v,
                 'invalid': sum(1 for r in rows if r['actor_status'] == 'invalid'),
                 'request_failed': sum(1 for r in rows if r['actor_status'] == 'request_failed'),
                 'crashed_no_result': sum(1 for r in rows if r['actor_status'] == 'crashed_no_result'),
                 'not_run': sum(1 for r in rows if r['actor_status'] == 'not_run'),
                 'match_over_12': m / n if n else 'NOT_ESTIMABLE',
                 'match_over_valid': (m / v) if v else 'NOT_ESTIMABLE',
                 'valid_coverage': v / n if n else 'NOT_ESTIMABLE'}
    a_states = {}
    a_by_layer = {}
    for r in rows:
        a = r['a'] or {}
        d = a.get('decision', 'not_run')
        a_states[d] = a_states.get(d, 0) + 1
        bl = a_by_layer.setdefault(r['scoring_status'], {})
        bl[d] = bl.get(d, 0) + 1
    usage_totals = {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
    for e in ledger.entries:
        if e.get('op') == 'settle' and isinstance(e.get('usage'), dict):
            for k in list(usage_totals):
                u = e['usage'].get(k)
                if isinstance(u, int):
                    usage_totals[k] += u
    cost = {'gen_attempts': ledger.gen_attempts(), 'retries_used': ledger.retries_used(),
            'aux_ops': receipt.get('aux_ops'), 'tokens_settled': ledger.settled_tokens(),
            'tokens_unsettled': ledger.unsettled_tokens(), 'usage_totals': usage_totals,
            'first_request_utc': receipt.get('first_request_utc'), 'generated_utc': R.iso()}
    (run_dir / 'scoring').mkdir(exist_ok=True)
    write = R.write_json
    write(run_dir / 'a_decisions.json', {'run_id': run_id,
          'rule': 'simple deterministic baseline: schema, frozen-keyword numeric presence, evidence bounds. NOT a production checker.',
          'items': [{'item_key': r['item_key'], 'a': r['a']} for r in rows]})
    write(run_dir / 'b_decisions.json', {'run_id': run_id,
          'label': 'B = same-source model verification (same model as actor; receives full actor output).',
          'items': [{'item_key': r['item_key'], 'b': r['b']} for r in rows]})
    write(run_dir / 'c_decisions.json', {'run_id': run_id,
          'label': 'C = same-model, independent-context verification (NOT answer-blind; receives only the actor final answer; NOT an independent model).',
          'items': [{'item_key': r['item_key'], 'c': r['c']} for r in rows]})
    write(run_dir / 'scoring' / 'per_task_scoring.json', {'run_id': run_id,
          'items': [{'task_id': r['task_id'], 'variant': r['variant'], 'actor_status': r['actor_status'],
                     'scoring_status': r['scoring_status'], 'scoring_score': r['scoring_score']} for r in rows]})
    results = {'schema': 'tq3_run_results_v1', 'run_id': run_id, 'generated_utc': R.iso(),
               'actor_kind': 'AI', 'panel': 'tq3_developmental_dry_run_panel_v1',
               'heldout': False, 'confirmatory': False,
               'run_status': receipt.get('status'), 'stop_reason': receipt.get('stop_reason'),
               'system_outcome': receipt.get('status') or 'UNKNOWN',
               'scientific_gold_validity': 'NOT_ESTABLISHED',
               'counts': {'inputs': n, 'actor_valid': v, 'actor_match': m},
               'actor': actor_agg,
               'verification': {'a': {'state_counts': a_states, 'by_layer': a_by_layer},
                                'b': arm_agg(rows, 'b'), 'c': arm_agg(rows, 'c')},
               'per_item': rows, 'cost': cost,
               'notes': ['C is same-model, independent-context verification; NOT answer-blind and NOT an independent model.',
                         'B and C differences include evidence-chain exposure and instruction differences; do not attribute to path independence alone.',
                         'A is a simple deterministic rule baseline; NOT the production checker.',
                         'Primary match denominator = 12 planned inputs; valid-conditional denominator reported separately.',
                         'Pairing unit = task/table (6 groups), not 12 independent samples.',
                         'scientific_gold_validity remains NOT_ESTABLISHED; results are descriptive only.']}
    write(run_dir / 'RESULTS.json', results)
    lines = []
    lines.append('# TQ-3 Run Summary - ' + run_id)
    lines.append('')
    lines.append('> status=' + str(receipt.get('status')) + '; stop_reason=' + str(receipt.get('stop_reason')) +
                 '; system_outcome=' + str(results['system_outcome']) + '; scientific_gold_validity=NOT_ESTABLISHED')
    lines.append('> C = 同模型、独立上下文核验（非答案盲态、非独立模型）。B = 同源核验（全量 actor 输出可见）。A = 简单规则基线。')
    lines.append('')
    lines.append('## Cost / timing')
    lines.append('- gen_attempts=' + str(cost['gen_attempts']) + '; retries=' + str(cost['retries_used']) +
                 '; aux_ops=' + str(cost['aux_ops']) + '; tokens_settled=' + str(cost['tokens_settled']))
    lines.append('- usage_totals=' + json.dumps(usage_totals, ensure_ascii=True))
    lines.append('- first_request_utc=' + str(cost['first_request_utc']))
    lines.append('')
    lines.append('## Actor outputs (12 planned)')
    lines.append('| item | answer | scoring | A | B | C |')
    lines.append('|---|---|---|---|---|---|')
    for r in rows:
        ans = str(r['answer'])
        if len(ans) > 60:
            ans = ans[:57] + '...'
        bd = (r['b'] or {}).get('decision') or (r['b'] or {}).get('state')
        cd = (r['c'] or {}).get('decision') or (r['c'] or {}).get('state')
        lines.append('| ' + r['task_id'] + ' ' + r['variant'] + ' | ' + ans + ' | ' + str(r['scoring_status']) + ' | ' +
                     str((r['a'] or {}).get('decision')) + ' | ' + str(bd) + ' | ' + str(cd) + ' |')
    lines.append('')
    lines.append('## Aggregates')
    lines.append('- actor: ' + json.dumps(actor_agg, ensure_ascii=True))
    lines.append('- A: ' + json.dumps({'state_counts': a_states, 'by_layer': a_by_layer}, ensure_ascii=True))
    lines.append('- B: ' + json.dumps(arm_agg(rows, 'b'), ensure_ascii=True))
    lines.append('- C: ' + json.dumps(arm_agg(rows, 'c'), ensure_ascii=True))
    lines.append('')
    lines.append('## Notes')
    for x in results['notes']:
        lines.append('- ' + x)
    (run_dir / 'SUMMARY.md').write_text(chr(10).join(lines) + chr(10), encoding='utf-8')
    files = []
    for p in sorted(run_dir.rglob('*')):
        if p.is_file() and p.name != 'RUN_MANIFEST.json':
            files.append({'path': p.relative_to(run_dir).as_posix(), 'sha256': sha_file(p), 'bytes': p.stat().st_size})
    write(run_dir / 'RUN_MANIFEST.json', {'schema': 'tq3_run_manifest_v1', 'run_id': run_id,
          'generated_utc': R.iso(), 'files': files, 'self_excluded': True})
    print(json.dumps({'run_id': run_id, 'files': len(files), 'status': receipt.get('status'),
                      'actor': actor_agg, 'b': arm_agg(rows, 'b')['decision_counts'], 'c': arm_agg(rows, 'c')['decision_counts']}, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
