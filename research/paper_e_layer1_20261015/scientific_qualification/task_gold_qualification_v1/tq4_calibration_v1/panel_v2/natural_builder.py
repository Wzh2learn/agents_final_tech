# -*- coding: utf-8 -*-
'''Build the four frozen TQ-4 natural tasks (selection spec v1). Deterministic; refuses to overwrite.'''
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TQ4 = HERE.parent
BASE = TQ4.parent

STOP = set('the a an of in on for and or to from between what which was were is are how much many company companies its as at by with does do has have did value total'.split())


def tokens(x):
    return set(re.findall('[a-z]+', x.lower())) - STOP


def qrank(q, h):
    return (-len(tokens(h) & tokens(q['question'])), -(q.get('answer_type') == 'arithmetic'), int(q.get('order', 0)), q['uid'])


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def write_json(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')


def tolerance(a):
    s = str(a)
    d = len(s.split('.')[1]) if '.' in s else 0
    return 0.5 * (10 ** (-d))


def main():
    out = HERE / 'natural'
    if out.exists() and any(out.rglob('*.json')):
        print('STOP: natural materials already exist; no overwrite')
        return 2
    (out / 'inputs').mkdir(parents=True, exist_ok=True)
    (out / 'reference').mkdir(exist_ok=True)
    (out / 'scoring').mkdir(exist_ok=True)

    pool = load(BASE / 'coordinator' / 'pool_inventory.json')
    prov = load(BASE / 'coordinator' / 'case_provenance.json')
    used_inj = {p['injection_id'] for p in prov}
    used_uid = {p['uid'] for p in prov}
    src = {x['uid']: x['table'] for x in load(BASE / 'raw' / 'tatqa_tables.json')}
    inj = {x['uid']: x['table'] for x in load(BASE / 'raw' / 'injected_tables.json')}
    raw_index = {}
    raw_files = ['tatqa_dataset_train.json', 'tatqa_dataset_dev.json']
    for name in raw_files:
        for ri, rec in enumerate(load(BASE / 'raw' / name)):
            raw_index[rec['table']['uid']] = (name, ri, rec)

    logs = []
    selected = []
    used = set(used_uid)
    for stratum in ['S1', 'S2', 'S3', 'S4']:
        cands = sorted([e for e in pool if e['stratum'] == stratum and e['injection_id'] not in used_inj],
                       key=lambda e: sha_bytes(e['injection_id'].encode('utf-8')))
        picked = None
        for e in cands:
            rec_log = {'stratum': stratum, 'uid': e['uid'],
                       'injection_id_sha256': sha_bytes(e['injection_id'].encode('utf-8')), 'checks': {}}
            if e['uid'] in used:
                rec_log['checks']['skip'] = 'uid_already_used'
                logs.append(rec_log)
                continue
            if e['uid'] not in src or e['uid'] not in inj or e['uid'] not in raw_index:
                rec_log['checks']['skip'] = 'corpus_join_missing'
                logs.append(rec_log)
                continue
            s, i = src[e['uid']], inj[e['uid']]
            ok_join = (s[0][e['col']] == e['original'] and i[0][e['col']] == e['injected'] and s[1:] == i[1:])
            rec_log['checks']['join'] = ok_join
            if not ok_join:
                logs.append(rec_log)
                continue
            name, ri, rec = raw_index[e['uid']]
            qs = [q for q in rec['questions'] if q.get('answer_from') in ('table', 'table-text')]
            qs = sorted(qs, key=lambda q: qrank(q, e['original']))
            chosen = None
            sanity = []
            for q in qs:
                a = q.get('answer')
                present = not (a is None or (isinstance(a, str) and a.strip() == '') or (isinstance(a, list) and not a))
                numeric = isinstance(a, (int, float))
                sanity.append({'question_uid': q['uid'], 'answer_present': bool(present), 'answer_numeric': bool(numeric)})
                if present and numeric:
                    chosen = q
                    break
            rec_log['checks']['questions_considered'] = sanity
            if chosen is None:
                rec_log['checks']['skip'] = 'no_structurally_valid_question'
                logs.append(rec_log)
                continue
            picked = (e, name, ri, rec, chosen)
            rec_log['checks']['picked'] = True
            logs.append(rec_log)
            break
        if picked is None:
            print('STOP: no candidate passed for', stratum)
            return 3
        selected.append((stratum, picked))
        used.add(picked[0]['uid'])

    case_rows = []
    for n, (stratum, (e, name, ri, rec, q)) in enumerate(selected, 1):
        tid = 'N' + str(n)
        s, i = src[e['uid']], inj[e['uid']]
        deriv = q.get('derivation') or ''
        unit_kind = 'percent' if '%' in deriv else 'plain'
        tol = tolerance(q['answer'])
        files = {}
        for variant, table in (('original', s), ('perturbed', i)):
            rel = 'inputs/' + tid + '_' + variant + '.json'
            write_json(out / rel, {'task_id': tid, 'variant': variant, 'question': q['question'], 'table': table, 'paragraphs': rec['paragraphs']})
            files[rel] = sha_file(out / rel)
        ref = {'task_id': tid, 'reference_version': 'v1',
               'source': 'raw TAT-QA record (' + name + '#/' + str(ri) + ', frozen corpus)',
               'official_reference': {k: q.get(k) for k in ['answer', 'derivation', 'answer_type', 'answer_from', 'scale', 'rel_paragraphs', 'req_comparison']},
               'applies_to_variants': ['original', 'perturbed'],
               'provisional': 'reference_validity NOT_ESTABLISHED; selection was structural (no model outputs); TQ-4 has not run'}
        rel = 'reference/' + tid + '.json'
        write_json(out / rel, ref)
        files[rel] = sha_file(out / rel)
        sc = {'task_id': tid, 'scoring_version': 'v2', 'compare_mode': 'numeric', 'unit_kind': unit_kind,
              'expected': q['answer'], 'expected_precise': float(q['answer']), 'abs_tolerance': tol,
              'tolerance_rule': '0.5 x 10^-d; d = decimal digits of recorded answer',
              'unit_scale_status': 'RESOLVED',
              'status_labels': {'reference_validity': 'NOT_ESTABLISHED', 'system_outcome': 'NOT_RUN', 'panel': 'TQ4_PART1_NATURAL_FROZEN'},
              'notes': 'unit_kind derived from recorded derivation (% -> percent); frozen pre-output'}
        rel = 'scoring/' + tid + '.json'
        write_json(out / rel, sc)
        files[rel] = sha_file(out / rel)
        case_rows.append({'task_id': tid, 'stratum': stratum, 'uid': e['uid'], 'type': e['type'],
                          'original_header': e['original'], 'injected_header': e['injected'], 'injected_col': e['col'],
                          'raw_file': name, 'raw_record_index': ri, 'question_uid': q['uid'],
                          'question_rank': list(qrank(q, e['original'])), 'question': q['question'],
                          'reference_answer': q['answer'], 'derivation': deriv, 'unit_kind': unit_kind,
                          'abs_tolerance': tol, 'files': files})
    corpus = {'raw/tatqa_tables.json': sha_file(BASE / 'raw' / 'tatqa_tables.json'),
              'raw/injected_tables.json': sha_file(BASE / 'raw' / 'injected_tables.json'),
              'raw/tatqa_dataset_train.json': sha_file(BASE / 'raw' / 'tatqa_dataset_train.json'),
              'raw/tatqa_dataset_dev.json': sha_file(BASE / 'raw' / 'tatqa_dataset_dev.json'),
              'coordinator/pool_inventory.json': sha_file(BASE / 'coordinator' / 'pool_inventory.json')}
    log = {'schema': 'tq4_natural_selection_log_v1',
           'frozen_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'spec': 'NATURAL_SELECTION_SPEC_v1.md',
           'freeze_note': 'No TQ-4 model outputs exist at freeze time; selection is structural only.',
           'corpus_hashes': corpus, 'selected': case_rows, 'skips_and_attempts': logs}
    write_json(out / 'SELECTION_LOG.json', log)
    print(json.dumps({'selected': [(c['task_id'], c['stratum'], c['uid'][:8], c['type']) for c in case_rows]}, ensure_ascii=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
