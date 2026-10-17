# -*- coding: utf-8 -*-
'''Build the TQ-5 source-separation developmental panel (spec v1). Deterministic; refuses to overwrite.'''
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

Q = Path(__file__).resolve().parent
B = Q.parent
SEED = '20261016'
LAYERS = ['difference', 'ratio', 'percentage_change']


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def write_json(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')


def norm_expr(s):
    s = str(s).lower()
    for ch in ['$', '¥', '£', '€', ',', '%', chr(9), chr(10), ' ']:
        s = s.replace(ch, '')
    return s


def norm_text(s):
    s = str(s)
    for ch in ['$', '¥', '£', '€', ',', '%', chr(9), chr(10), chr(13), ' ']:
        s = s.replace(ch, '')
    return s


def classify_shape(expr2):
    if '/' in expr2 and '-' in expr2 and '+' not in expr2 and '*' not in expr2:
        return 'change_div'
    if '/' in expr2 and '-' not in expr2 and '+' not in expr2 and '*' not in expr2:
        return 'div'
    if '-' in expr2 and '/' not in expr2 and '+' not in expr2 and '*' not in expr2:
        return 'sub'
    return None


ALLOWED = set('0123456789.+-*/() ')


def eval_expr(expr):
    if not expr or any(c not in ALLOWED for c in expr):
        return None
    try:
        return float(eval(expr, {'__builtins__': {}}, {}))
    except Exception:
        return None


def tolerance(a):
    s = str(a)
    d = len(s.split('.')[1]) if '.' in s else 0
    return 0.5 * (10 ** (-d))


def num_tokens(s):
    toks = []
    cur = ''
    for ch in s:
        if ch.isdigit() or ch in '.,':
            cur += ch
        elif cur:
            toks.append(cur)
            cur = ''
    if cur:
        toks.append(cur)
    out = []
    for t in toks:
        t2 = t.strip('.,')
        if t2:
            out.append(t2)
    return out


def main():
    out = Q / 'panel'
    if (out / 'SELECTION_LOG.json').exists():
        print('STOP: panel already exists; no overwrite')
        return 2
    (out / 'inputs').mkdir(parents=True, exist_ok=True)
    (out / 'reference').mkdir(exist_ok=True)
    (out / 'scoring').mkdir(exist_ok=True)

    om = load(Q / 'source_refs' / 'origin_manifest.json')
    od = set(o['uid'] for o in om['origins'])
    pool_p = B / 'coordinator' / 'pool_inventory.json'
    pool = load(pool_p)
    pd = set(x['uid'] for x in pool)
    prov_p = B / 'coordinator' / 'case_provenance.json'
    prov = load(prov_p)
    td = set(x['uid'] for x in prov)
    nat_p = B / 'tq4_calibration_v1' / 'panel_v2' / 'natural' / 'SELECTION_LOG.json'
    nat = load(nat_p)
    nd = set(x['uid'] for x in nat['selected'])
    excl = od | pd | td | nd

    records = []
    for split in ['train', 'dev']:
        for ridx, rec in enumerate(load(B / 'raw' / ('tatqa_dataset_' + split + '.json'))):
            records.append((split, ridx, rec))

    qualified = {l: [] for l in LAYERS}
    counts = {}
    def bump(k):
        counts[k] = counts.get(k, 0) + 1
    skip_details = []
    for split, ridx, rec in records:
        uid = rec['table']['uid']
        if uid in excl:
            bump('record_excluded')
            continue
        corpus = norm_text(json.dumps(rec['table']['table'], ensure_ascii=False)) + '|' + norm_text(json.dumps(rec['paragraphs'], ensure_ascii=False))
        for qi, q in enumerate(rec['questions']):
            a = q.get('answer')
            if q.get('answer_from') not in ('table', 'table-text'):
                bump('skip_answer_from')
                continue
            if not isinstance(a, (int, float)) or isinstance(a, bool):
                bump('skip_answer_not_numeric')
                continue
            d = q.get('derivation') or ''
            if not str(d).strip():
                bump('skip_derivation_missing')
                continue
            expr = norm_expr(str(d))
            expr2 = expr.replace('*100', '')
            shape = classify_shape(expr2)
            if shape is None:
                bump('skip_layer_unclassified')
                continue
            val = eval_expr(expr)
            tolr = tolerance(a)
            if val is None:
                bump('skip_eval_none')
                continue
            enc = None
            if abs(val - float(a)) <= tolr:
                enc = 'direct'
            elif abs(val * 100.0 - float(a)) <= tolr:
                enc = 'x100'
            if enc is None:
                bump('skip_eval_mismatch')
                if len(skip_details) < 200:
                    skip_details.append({'uid': uid, 'q': q['uid'], 'derivation': str(d), 'answer': a, 'eval': val, 'reason': 'eval_mismatch'})
                continue
            if shape == 'change_div':
                layer = 'percentage_change' if ('*100' in expr or enc == 'x100') else None
                if layer is None:
                    bump('skip_pct_encoding_ambiguous')
                    continue
            elif shape == 'div':
                layer = 'ratio'
            else:
                layer = 'difference'
                if enc != 'direct':
                    bump('skip_diff_encoding_nonstandard')
                    continue
            ops = num_tokens(expr.replace('*100', '').replace('×100', ''))
            missing = [o for o in ops if norm_text(o) not in corpus]
            if missing:
                bump('skip_operand_missing')
                if len(skip_details) < 200:
                    skip_details.append({'uid': uid, 'q': q['uid'], 'derivation': str(d), 'reason': 'operand_missing', 'missing': missing[:5]})
                continue
            bump('qualified_' + layer)
            qualified[layer].append({'layer': layer, 'uid': uid, 'split': split, 'ridx': ridx, 'qi': qi,
                                     'question': q, 'answer': a, 'derivation': str(d), 'tol': tolr,
                                     'encoding': enc, 'key': sha_bytes((SEED + '|' + uid + '|' + q['uid']).encode('utf-8')),
                                     'rec': rec})

    selected = []
    traces = {}
    used = set()
    ok = True
    for layer in LAYERS:
        cands = sorted(qualified[layer], key=lambda x: x['key'])
        trace = []
        got = 0
        for c in cands:
            if c['uid'] in used:
                trace.append({'uid': c['uid'], 'q': c['question']['uid'], 'outcome': 'uid_used'})
                continue
            used.add(c['uid'])
            selected.append(c)
            got += 1
            trace.append({'uid': c['uid'], 'q': c['question']['uid'], 'outcome': 'selected', 'rank_key': c['key'][:16]})
            if got == 4:
                break
        traces[layer] = trace
        if got < 4:
            ok = False
            (Q / 'TQ5_NOT_RUN.md').write_text('TQ-5 NOT_RUN: layer ' + layer + ' could not reach 4 valid tasks (got ' + str(got) + '). No criteria lowering; no substitution.\n', encoding='utf-8')
    if not ok:
        write_json(out / 'SELECTION_LOG.json', {'schema': 'tq5_selection_log_v1', 'status': 'NOT_RUN',
                                                'frozen_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                                                'skip_counts': counts, 'layer_scan_traces': traces})
        print('NOT_RUN: shortage', json.dumps({l: len(traces[l]) for l in LAYERS}))
        return 3

    case_rows = []
    for n, c in enumerate(selected, 1):
        tid = 'T' + str(n).zfill(2)
        rec = c['rec']
        q = c['question']
        files = {}
        inp = {'task_id': tid, 'variant': 'original', 'question': q['question'], 'table': rec['table']['table'], 'paragraphs': rec['paragraphs']}
        rel = 'inputs/' + tid + '.json'
        write_json(out / rel, inp)
        files[rel] = sha_file(out / rel)
        ref = {'task_id': tid, 'reference_version': 'v1',
               'source': 'raw TAT-QA record (' + c['split'] + '#' + str(c['ridx']) + ')',
               'official_reference': {k: q.get(k) for k in ['answer', 'derivation', 'answer_type', 'answer_from', 'scale', 'rel_paragraphs', 'req_comparison']},
               'applies_to_variants': ['original'],
               'provisional': 'reference_validity NOT_ESTABLISHED; TQ-5 had not run at freeze time'}
        rel = 'reference/' + tid + '.json'
        write_json(out / rel, ref)
        files[rel] = sha_file(out / rel)
        raw_deriv = c['derivation']
        if c['layer'] == 'percentage_change':
            uk = 'percent'
        elif c['layer'] == 'ratio':
            uk = 'percent' if c.get('encoding') == 'x100' else 'ratio'
        else:
            uk = 'percent' if '%' in raw_deriv else 'plain'
        sc = {'task_id': tid, 'scoring_version': 'v21', 'compare_mode': 'numeric', 'unit_kind': uk,
              'expected': q['answer'], 'expected_precise': float(q['answer']), 'abs_tolerance': c['tol'],
              'tolerance_rule': '0.5 x 10^-d; d = decimal digits of recorded answer',
              'unit_scale_status': 'RESOLVED',
              'status_labels': {'reference_validity': 'NOT_ESTABLISHED', 'system_outcome': 'NOT_RUN', 'panel': 'TQ5_SOURCE_SEPARATION_FROZEN'},
              'notes': 'layer=' + c['layer']}
        rel = 'scoring/' + tid + '.json'
        write_json(out / rel, sc)
        files[rel] = sha_file(out / rel)
        case_rows.append({'task_id': tid, 'layer': c['layer'], 'uid': c['uid'], 'question_uid': q['uid'],
                          'question': q['question'], 'answer': q['answer'], 'derivation': raw_deriv,
                          'encoding': c.get('encoding'), 'unit_kind': uk, 'abs_tolerance': c['tol'],
                          'split': c['split'], 'record_index': c['ridx'],
                          'rank_key': c['key'][:16], 'files': files})
    write_json(out / 'GROUPS.json', dict((r['task_id'], r['layer']) for r in case_rows))
    log = {'schema': 'tq5_selection_log_v1', 'status': 'FROZEN',
           'frozen_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'spec': 'TQ5_PANEL_SPEC_v2.md',
           'spec_revision_note': 'v1 (star100 rule) was inoperable on corpus encoding; revised to v2 (shape+encoding) before any model output; see spec v2 and v1 shortage record.', 'seed': SEED,
           'freeze_note': 'No TQ-5 model outputs exist at freeze time; selection is structural + recomputation gates only.',
           'exclusions': {'sources': {
               'origin_manifest': {'path': 'source_refs/origin_manifest.json', 'sha256': sha_file(Q / 'source_refs' / 'origin_manifest.json'), 'count': len(od)},
               'pool_inventory': {'path': 'coordinator/pool_inventory.json', 'sha256': sha_file(pool_p), 'count': len(pd)},
               'tq_case_provenance': {'sha256': sha_file(prov_p), 'count': len(td)},
               'tq4_natural_log': {'sha256': sha_file(nat_p), 'count': len(nd)}},
               'union_count': len(excl)},
           'eligible_records': sum(1 for s, r, rc in records if rc['table']['uid'] not in excl),
           'skip_counts': counts, 'skip_details_sample': skip_details,
           'layer_scan_traces': traces, 'selected': case_rows}
    write_json(out / 'SELECTION_LOG.json', log)
    print(json.dumps({'selected': [(r['task_id'], r['layer'], r['uid'][:8]) for r in case_rows],
                      'counts_keys': sorted(counts.keys())}, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
