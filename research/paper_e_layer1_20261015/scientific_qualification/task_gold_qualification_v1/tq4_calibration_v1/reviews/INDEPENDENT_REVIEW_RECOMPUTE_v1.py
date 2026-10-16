# -*- coding: utf-8 -*-
"""TQ-4 independent-review recomputation (read-only against the frozen tree).

Reads the committed tq4_calibration_v1 package + upstream TQ-3 material and re-executes
the A-E verification scope from scratch. Writes only its own JSON output (argv[1]).
No network, no model calls, no mutation of the reviewed tree (bytecode writes disabled).

Run:  python INDEPENDENT_REVIEW_RECOMPUTE_v1.py <out.json>
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

BASE = Path(__file__).resolve().parents[2]  # reviews/ -> tq4_calibration_v1 -> task_gold_qualification_v1
TQ4 = BASE / 'tq4_calibration_v1'
TQ3 = BASE / 'tq3_execution_prep_v1'
sys.path.insert(0, str(TQ4 / 'scorer_v2'))
sys.path.insert(0, str(TQ3 / 'tools'))
import tq4_scoring_entry as V2  # noqa: E402
import tq3_scoring_entry as V1  # noqa: E402


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


R = {'schema': 'tq4_independent_review_recompute_v1', 'checks': {}, 'notes': []}


def check_a():
    fx = load(TQ4 / 'scorer_v2/regression/tq4_regression_cases.json')
    rows, fails, diffs, diff_cases = [], [], 0, []
    for case in fx['cases']:
        for a in case['answers']:
            v2r = V2.score(case['case_id'], {'answer': a['answer']}, case['v2_config'])
            v1r = V1.score(case['case_id'], {'answer': a['answer']}, case['v1_config'])
            ok = v2r['status'] == a['expect_v2']
            diff = v1r['status'] != v2r['status']
            if diff:
                diffs += 1
                diff_cases.append(case['case_id'])
            if a.get('v1_diff_expected') and not diff:
                ok = False
            if not ok:
                fails.append({'case': case['case_id'], 'answer': a['answer'],
                              'expected': a['expect_v2'], 'got': v2r['status']})
            rows.append(True)
    frozen = load(TQ4 / 'scorer_v2/regression/regression_results.json')
    a = {'checks': len(rows), 'passed': len(rows) - len(fails), 'failed': fails,
         'v1_v2_diffs': diffs, 'diff_cases': sorted(set(diff_cases))}
    a['frozen_counts_match'] = (
        a['checks'] == frozen['counts']['checks']
        and a['passed'] == frozen['counts']['passed']
        and a['v1_v2_diffs'] == frozen['counts']['v1_v2_status_differences'])
    a['frozen_module_hashes_ok'] = (
        frozen['v1_module_sha256'] == sha(TQ3 / 'tools/tq3_scoring_entry.py')
        and frozen['v2_module_sha256'] == sha(TQ4 / 'scorer_v2/tq4_scoring_entry.py'))
    a['frozen_all_passed_flag'] = frozen['all_passed']
    R['checks']['A_regression'] = a
    print('A: checks=%s passed=%s diffs=%s frozen_match=%s' %
          (a['checks'], a['passed'], a['v1_v2_diffs'], a['frozen_counts_match']))


def check_b():
    RUN = TQ3 / 'runs/20261016T051556Z_af4c2db6'
    UNIT = {'Q10': 'ratio', 'Q03': 'plain', 'Q04': 'plain', 'Q12': 'plain'}
    rows = []
    for seq in range(1, 13):
        raws = sorted((RUN / 'raw').glob(str(seq).zfill(4) + '_actor_*.json'))
        if not raws:
            rows.append({'seq': seq, 'error': 'no raw'})
            continue
        raw = load(raws[0])
        case, variant, obj = raw['case'], raw['variant'], raw['parse']['result']
        old = load(TQ3 / 'dev_panel' / 'scoring' / (case + '.json'))
        v1r = V1.score(case, obj, old)
        cfg = dict(old)
        if old['compare_mode'] == 'span_containment_normalized':
            cfg['compare_mode'] = 'list_full_match'
            cfg['expected_full'] = old['expected_spans'][0]
            cfg['expected_items'] = old['expected_spans']
        elif old['compare_mode'] == 'numeric':
            cfg['unit_kind'] = UNIT[case]
        v2r = V2.score(case, obj, cfg)
        inp = load(TQ3 / 'dev_panel' / ('inputs_' + variant) / (case + '.json'))
        leg = V2.check_evidence_legality(inp['table'], inp['paragraphs'], obj.get('evidence'))
        rows.append({'seq': seq, 'task_id': case, 'variant': variant,
                     'v1': v1r['status'], 'v2': v2r['status'],
                     'legal': leg['legal'], 'issues': [i['issue'] for i in leg['issues']]})
    groups = [r for r in rows if 'error' not in r]
    counts = {'items': len(rows),
              'v1_match': sum(r['v1'] == 'MATCH' for r in groups),
              'v2_match': sum(r['v2'] == 'MATCH' for r in groups),
              'changed': sum(r['v1'] != r['v2'] for r in groups)}
    issue_types = {}
    for r in groups:
        for i in r['issues']:
            issue_types[i] = issue_types.get(i, 0) + 1
    legality = {'legal': sum(r['legal'] for r in groups),
                'illegal': sum(not r['legal'] for r in groups),
                'issue_types': issue_types}
    frozen = load(TQ4 / 'rescoring/rescore_results.json')
    frows = {r['seq']: r for r in frozen['rows']}
    rowlevel = all(
        r['v1'] == frows[r['seq']]['v1_status'] and r['v2'] == frows[r['seq']]['v2_status']
        for r in groups if r['seq'] in frows)
    b = {'counts': counts, 'legality': legality, 'rowlevel_matches_frozen': rowlevel,
         'rows': [{'seq': r['seq'], 'v1': r['v1'], 'v2': r['v2'], 'legal': r['legal']} for r in groups]}
    R['checks']['B_rescore'] = b
    print('B: counts=%s legality=%s rowmatch=%s' % (counts, legality, rowlevel))


def check_c():
    cands = load(TQ4 / 'panel_v2/candidates/candidates_v1.json')['candidates']
    clog = load(TQ4 / 'panel_v2/candidates/CANDIDATES_LOG.json')
    inp = {t: load(TQ4 / 'panel_v2/candidates/inputs' / (t + '.json')) for t in ['Q02', 'Q03', 'Q04']}
    ver = []
    for c in cands:
        src = inp[c['task_id']]
        leg = V2.check_evidence_legality(src['table'], src['paragraphs'], c['evidence'])
        exp = c['label']['evidence_legality'] == 'legal'
        ver.append({'cid': c['candidate_id'], 'legal': leg['legal'], 'expected': exp, 'ok': leg['legal'] == exp})
    clogv = {v['candidate_id']: v for v in clog['legality_verifications']}
    combos = sorted((c['label']['answer_kind'], c['label']['evidence_legality']) for c in cands)
    want = sorted([('correct', 'legal'), ('correct', 'illegal'),
                   ('incorrect', 'legal'), ('incorrect', 'illegal')] * 3)
    ans = {c['candidate_id']: c['answer'] for c in cands}
    spec_ok = (ans.get('Q02-C3') == 'accounts receivable, inventories'
               and 'net property' in str(ans.get('Q02-C1'))
               and ans.get('Q03-C1') == 14054 and ans.get('Q03-C3') == -14054
               and ans.get('Q04-C1') == -3 and ans.get('Q04-C3') == 3)
    c = {'n': len(cands),
         'order': [x['candidate_id'] for x in cands],
         'matrix_exact': combos == want,
         'legality_recompute_ok': all(v['ok'] for v in ver),
         'log_consistent': all(clogv[v['cid']]['legality']['legal'] == v['legal'] for v in ver),
         'inputs_hash_ok': all(sha(TQ4 / 'panel_v2/candidates' / rel) == h
                               for rel, h in clog['input_hashes'].items()),
         'candidates_file_sha_ok': sha(TQ4 / 'panel_v2/candidates/candidates_v1.json') == clog['candidates_file_sha256'],
         'spec_answers_ok': spec_ok,
         'verifications': ver}
    R['checks']['C_candidates'] = c
    print('C: n=%s matrix=%s legality=%s hashes=%s' %
          (c['n'], c['matrix_exact'], c['legality_recompute_ok'], c['inputs_hash_ok']))


def check_d():
    sel = load(TQ4 / 'panel_v2/natural/SELECTION_LOG.json')
    corpus_ok = {rel: (sha(BASE / rel) == h) for rel, h in sel['corpus_hashes'].items()}
    files_ok = True
    for s in sel['selected']:
        for rel, h in s['files'].items():
            if sha(TQ4 / 'panel_v2/natural' / rel) != h:
                files_ok = False
    uk, tol_ok, ref_selfcheck = {}, {}, {}
    for s in sel['selected']:
        tid = s['task_id']
        sc = load(TQ4 / 'panel_v2/natural/scoring' / (tid + '.json'))
        uk[tid] = sc.get('unit_kind')
        ans = s['reference_answer']
        s_repr = repr(ans)
        d = len(s_repr.split('.')[1]) if '.' in s_repr else 0
        tol_ok[tid] = abs(float(s['abs_tolerance']) - 0.5 * (10 ** -d)) < 1e-12
        try:
            r = V2.score(tid, {'answer': str(ans)}, sc)
            ref_selfcheck[tid] = r['status']
        except Exception as e:  # noqa: BLE001
            ref_selfcheck[tid] = 'ERROR:' + type(e).__name__
    joins = {}
    try:
        src = {x['uid']: x['table'] for x in load(BASE / 'raw/tatqa_tables.json')}
        inj = {x['uid']: x['table'] for x in load(BASE / 'raw/injected_tables.json')}
        for s in sel['selected']:
            uid, col = s['uid'], s['injected_col']
            st, it = src.get(uid), inj.get(uid)
            if st is None or it is None:
                joins[uid] = {'error': 'uid missing in corpora'}
                continue
            joins[uid] = {
                'header_original_ok': st[0][col] == s['original_header'],
                'header_injected_ok': it[0][col] == s['injected_header'],
                'rest_rows_equal': st[1:] == it[1:],
                'input_original_matches_source': load(TQ4 / 'panel_v2/natural/inputs' / (s['task_id'] + '_original.json'))['table'] == st,
                'input_perturbed_matches_injected': load(TQ4 / 'panel_v2/natural/inputs' / (s['task_id'] + '_perturbed.json'))['table'] == it,
            }
    except Exception as e:  # noqa: BLE001
        joins = {'error': type(e).__name__ + ':' + str(e)[:120]}
    recs = {}
    try:
        for split in ['train', 'dev']:
            data = load(BASE / 'raw' / ('tatqa_dataset_' + split + '.json'))
            for s in sel['selected']:
                if s['raw_file'] != 'tatqa_dataset_' + split + '.json':
                    continue
                rec = data[s['raw_record_index']]
                q = next((q for q in rec['questions'] if q.get('uid') == s['question_uid']), None)
                recs[s['task_id']] = {
                    'uid_ok': rec['table']['uid'] == s['uid'],
                    'question_found': q is not None,
                    'answer_present': bool(q and q.get('answer') not in (None, '')),
                    'answer_numeric_like': bool(q and re.search(r'[0-9]', str(q.get('answer', '')))),
                }
    except Exception as e:  # noqa: BLE001
        recs = {'error': type(e).__name__ + ':' + str(e)[:120]}
    d = {'strata_ok': sorted(s['stratum'] for s in sel['selected']) == ['S1', 'S2', 'S3', 'S4'],
         'tasks': [s['task_id'] for s in sel['selected']],
         'corpus_hashes_ok': corpus_ok,
         'files_hashes_ok': files_ok,
         'unit_kind': uk,
         'unit_kind_matches_derivation_rule': all(
             (('percent' if '%' in s['derivation'] else 'plain') == uk[s['task_id']])
             for s in sel['selected']),
         'tolerance_rule_ok': tol_ok,
         'reference_answer_selfcheck': ref_selfcheck,
         'joins': joins, 'records': recs}
    R['checks']['D_natural'] = d
    print('D: strata=%s corpus=%s files=%s ukrule=%s tol=%s joins=%s' %
          (d['strata_ok'], all(corpus_ok.values()), files_ok,
           d['unit_kind_matches_derivation_rule'], tol_ok, joins if isinstance(joins, dict) else joins))


def check_e():
    rc = (TQ4 / 'run_card_v2/RUN_CARD_v2.md').read_text(encoding='utf-8')
    ai = (TQ4 / 'run_card_v2/AUTHORIZATION_ITEMS_v2.md').read_text(encoding='utf-8')
    e = {'has_total36': ('36' in rc), 'has_cap40': ('40' in rc),
         'has_retry_leq4': any(x in rc for x in ['<= 4', '<=4', '≤ 4', '≤4']),
         'has_single_concurrency': ('单并发' in rc),
         'c_label_verbatim': ('同模型、独立上下文、可见候选答案' in rc),
         'auth_g1_g5': all(('G%d' % i) in ai for i in range(1, 6)),
         'auth_no_reuse': ('不得复用' in ai) or ('不复用' in ai),
         'budget_split_stated': ('12' in rc and '24' in rc)}
    R['checks']['E_run_card'] = e
    print('E:', e)


def check_f():
    m = load(TQ4 / 'MANIFEST.json')
    pm = load(TQ4 / 'panel_v2/PANEL_V2_MANIFEST.json')
    bad, badp = [], []
    for f in m['files']:
        p = TQ4 / f['path']
        if not (p.exists() and sha(p) == f['sha256'] and p.stat().st_size == f['bytes']):
            bad.append(f['path'])
    for f in pm['files']:
        p = TQ4 / 'panel_v2' / f['path']
        if not (p.exists() and sha(p) == f['sha256']):
            badp.append(f['path'])
    on_disk = []
    for p in sorted(TQ4.rglob('*')):
        if not p.is_file():
            continue
        rel = p.relative_to(TQ4).as_posix()
        if rel == 'MANIFEST.json' or '__pycache__' in p.parts or p.suffix == '.pyc':
            continue
        if rel.startswith('runs/') and rel != 'runs/.gitignore':
            continue
        on_disk.append(rel)
    inm = {f['path'] for f in m['files']}
    f = {'root_files': len(m['files']), 'root_bad': bad,
         'panel_files': len(pm['files']), 'panel_bad': badp,
         'self_excluded': 'MANIFEST.json' not in inm,
         'on_disk_not_in_manifest': [x for x in on_disk if x not in inm],
         'in_manifest_not_on_disk': [x for x in inm if x not in set(on_disk)],
         'reviews_registered': sorted(x for x in inm if x.startswith('reviews/'))}
    R['checks']['F_integrity'] = f
    print('F: root=%s/%s panel=%s/%s extra=%s missing=%s' %
          (f['root_files'] - len(bad), f['root_files'], f['panel_files'] - len(badp),
           f['panel_files'], f['on_disk_not_in_manifest'], f['in_manifest_not_on_disk']))


def check_g():
    probes = {}
    try:
        t = [['a', 'b'], ['c', 'd'], ['e', 'f']]
        leg = V2.check_evidence_legality(t, [], [{'kind': 'cell', 'table_row': True, 'table_col': 0}])
        probes['bool_as_int_cell'] = {'legal': leg['legal'], 'issues': leg['issues']}
    except Exception as e:  # noqa: BLE001
        probes['bool_as_int_cell'] = {'error': type(e).__name__}
    m = {'compare_mode': 'numeric', 'unit_kind': 'plain', 'expected_precise': 5, 'abs_tolerance': 0.01,
         'unit_scale_status': 'RESOLVED'}
    probes['percent_marker_on_plain'] = V2.score('P', {'answer': '5%'}, m)['status']
    probes['multi_number_refusal'] = V2.score(
        'P', {'answer': 'The difference is 14054, but the reverse order gives 13999.'}, m)['status']
    probes['list_superset'] = V2.score(
        'P', {'answer': 'a, b, c'},
        {'compare_mode': 'list_full_match', 'expected_items': ['a', 'b']})['status']
    probes['list_reorder'] = V2.score(
        'P', {'answer': 'b and a'},
        {'compare_mode': 'list_full_match', 'expected_items': ['a', 'b']})['status']
    R['checks']['G_probes'] = probes
    print('G:', probes)


def main():
    check_a()
    check_b()
    check_c()
    check_d()
    check_e()
    check_f()
    check_g()
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('INDEPENDENT_REVIEW_RECOMPUTE_v1.json')
    out.write_text(json.dumps(R, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')
    print('WROTE', out)


if __name__ == '__main__':
    main()
