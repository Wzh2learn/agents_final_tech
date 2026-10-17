# -*- coding: utf-8 -*-
"""Loop C independent pre-run recompute for the TQ-5 source-separation panel (spec v2).

Fresh-context reviewer artifact (loopc_tq5_prereview). Re-implements the frozen
eligibility / classification / selection gates from scratch (no import of the
builder code) and compares the result against the frozen package artifacts.

Read-only over frozen materials. Writes only its own output JSON in this directory.
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../tq5_source_validation_v1/reviews
Q = HERE.parent                                  # tq5_source_validation_v1
B = Q.parent                                     # task_gold_qualification_v1

SEED = '20261016'
LAYERS = ['difference', 'ratio', 'percentage_change']
OK_ANSWER_FROM = ('table', 'table-text')


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(Path(p).read_bytes())


def jdump(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True)


def norm_expr(s):
    s = str(s).lower()
    for ch in ['$', chr(0xa5), chr(0xa3), chr(0x20ac), ',', '%', chr(9), chr(10), ' ']:
        s = s.replace(ch, '')
    return s


def norm_text(s):
    s = str(s)
    for ch in ['$', chr(0xa5), chr(0xa3), chr(0x20ac), ',', '%', chr(9), chr(10), chr(13), ' ']:
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
    out = {
        'schema': 'tq5_prereview_recompute_v1',
        'generated_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'reviewer': 'loopc_tq5_prereview',
        'role': 'Loop C fresh-context pre-run independent recompute (spec v2 gates)',
        'panel_root': str(Q),
        'seed': SEED,
    }
    problems = []

    # ---- 0. raw corpus files ----
    train = load(B / 'raw' / 'tatqa_dataset_train.json')
    dev = load(B / 'raw' / 'tatqa_dataset_dev.json')
    raw_sha = {
        'train': sha_file(B / 'raw' / 'tatqa_dataset_train.json'),
        'dev': sha_file(B / 'raw' / 'tatqa_dataset_dev.json'),
    }
    fetch_txt = (B / 'raw' / 'FETCH_RECEIPT.txt').read_text(encoding='utf-8-sig')
    out['raw'] = {
        'record_counts': {'train': len(train), 'dev': len(dev)},
        'sha256': raw_sha,
        'fetch_receipt_hash_lines_present': {k: (v in fetch_txt) for k, v in raw_sha.items()},
    }
    if not all(out['raw']['fetch_receipt_hash_lines_present'].values()):
        problems.append('raw_sha_vs_fetch_receipt')

    # ---- 1. manifest + LF pins + extras ----
    mf = load(Q / 'MANIFEST.json')
    pins = load(Q / 'execution_v1' / 'tq5_material_pins_lf_v1.json')
    bad, lf_bad, lf_missing = [], [], []
    for f in mf['files']:
        p = Q / f['path']
        if not p.exists():
            bad.append({'path': f['path'], 'why': 'missing'})
            continue
        b = p.read_bytes()
        if sha_bytes(b) != f['sha256']:
            bad.append({'path': f['path'], 'why': 'sha_raw'})
        lf = sha_bytes(b.replace(bytes([13, 10]), bytes([10])))
        if f['path'] not in pins.get('files', {}):
            lf_missing.append(f['path'])
        elif pins['files'][f['path']] != lf:
            lf_bad.append({'path': f['path']})
    listed = set(f['path'] for f in mf['files'])
    extra = []
    for p in sorted(Q.rglob('*')):
        if not p.is_file():
            continue
        rel = p.relative_to(Q).as_posix()
        if rel.startswith('runs/') or '__pycache__' in rel or rel.endswith('.pyc'):
            continue
        if rel in listed or rel in ('MANIFEST.json', 'execution_v1/tq5_material_pins_lf_v1.json'):
            continue
        if rel.startswith('reviews/'):
            continue
        extra.append(rel)
    out['pins'] = {
        'manifest_count': len(mf['files']),
        'raw_mismatches': bad,
        'lf_mismatches': lf_bad,
        'lf_missing': lf_missing,
        'pins_source_manifest_sha_ok': pins.get('source_manifest_sha256') == sha_file(Q / 'MANIFEST.json'),
        'files_outside_manifest': extra,
    }
    if bad or lf_bad or lf_missing or extra or not out['pins']['pins_source_manifest_sha_ok']:
        problems.append('pins')

    # ---- 2. exclusions ----
    om = load(Q / 'source_refs' / 'origin_manifest.json')
    od = set(o['uid'] for o in om['origins'])
    om_ids = set(o.get('origin_id') for o in om['origins'])
    pool = load(B / 'coordinator' / 'pool_inventory.json')
    pd = set(x['uid'] for x in pool)
    prov = load(B / 'coordinator' / 'case_provenance.json')
    td = set(x['uid'] for x in prov)
    nat = load(B / 'tq4_calibration_v1' / 'panel_v2' / 'natural' / 'SELECTION_LOG.json')
    nd = set(x['uid'] for x in nat['selected'])
    union = od | pd | td | nd

    log = load(Q / 'panel' / 'SELECTION_LOG.json')
    sel_uids = [r['uid'] for r in log['selected']]

    wp2 = load(Q / 'source_refs' / 'WP2_SPLIT_DRYRUN_RECEIPT.json')
    roles_info = {}
    for role, ids in (wp2.get('roles') or {}).items():
        s = set(ids)
        roles_info[role] = {'n': len(s), 'subset_of_origin_ids': s <= om_ids}

    prov_rows = []
    rec_by_split = {'train': train, 'dev': dev}
    for e in prov:
        split = e['raw_file'].split('_')[-1].replace('.json', '')
        rec = rec_by_split[split][e['raw_record_index']]
        prov_rows.append({
            'case_id': e['case_id'],
            'uid_ok': rec['table']['uid'] == e['uid'],
            'question_uid_ok': rec['questions'][e['question_index']]['uid'] == e['question_uid'],
        })

    src_log = log['exclusions']['sources']
    sha_ok = {
        'origin_manifest': src_log['origin_manifest']['sha256'] == sha_file(Q / 'source_refs' / 'origin_manifest.json'),
        'pool_inventory': src_log['pool_inventory']['sha256'] == sha_file(B / 'coordinator' / 'pool_inventory.json'),
        'tq_case_provenance': src_log['tq_case_provenance']['sha256'] == sha_file(B / 'coordinator' / 'case_provenance.json'),
        'tq4_natural_log': src_log['tq4_natural_log']['sha256'] == sha_file(B / 'tq4_calibration_v1' / 'panel_v2' / 'natural' / 'SELECTION_LOG.json'),
    }
    out['exclusion'] = {
        'counts': {
            'origin_manifest': len(od),
            'pool_inventory_distinct': len(pd),
            'case_provenance': len(td),
            'tq4_natural': len(nd),
        },
        'pool_entries_total': len(pool),
        'union_count_recomputed': len(union),
        'union_count_in_log': log['exclusions']['union_count'],
        'selected_unique_uids': len(set(sel_uids)),
        'selected_uids_in_union': [u for u in sel_uids if u in union],
        'pairwise_overlaps': {
            'om_pool': len(od & pd), 'om_prov': len(od & td), 'om_nat': len(od & nd),
            'pool_prov': len(pd & td), 'pool_nat': len(pd & nd), 'prov_nat': len(td & nd),
        },
        'source_file_shas_match_log': sha_ok,
        'provenance_rows_checked': prov_rows,
        'wp2_roles': roles_info,
        'wp2_origins_total_matches_manifest': (wp2.get('counts') or {}).get('origins_total') == len(od),
    }
    exo = out['exclusion']
    if exo['selected_uids_in_union'] or not all(sha_ok.values()):
        problems.append('exclusion')
    if not all(r['uid_ok'] and r['question_uid_ok'] for r in prov_rows):
        problems.append('provenance_rows')
    if not all(v['subset_of_origin_ids'] for v in roles_info.values()):
        problems.append('wp2_roles_subset')

    # ---- 3. independent rebuild of eligibility + selection ----
    records = []
    for split, arr in (('train', train), ('dev', dev)):
        for ridx, rec in enumerate(arr):
            records.append((split, ridx, rec))

    qualified = {l: [] for l in LAYERS}
    counts = {}
    eligible_records = 0

    def bump(k):
        counts[k] = counts.get(k, 0) + 1

    for split, ridx, rec in records:
        uid = rec['table']['uid']
        if uid in union:
            bump('record_excluded')
            continue
        eligible_records += 1
        corpus = norm_text(jdump(rec['table']['table'])) + '|' + norm_text(jdump(rec['paragraphs']))
        for qi, q in enumerate(rec['questions']):
            a = q.get('answer')
            if q.get('answer_from') not in OK_ANSWER_FROM:
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
            ops = num_tokens(expr.replace('*100', ''))
            missing = [o for o in ops if norm_text(o) not in corpus]
            if missing:
                bump('skip_operand_missing')
                continue
            bump('qualified_' + layer)
            qualified[layer].append({
                'layer': layer, 'uid': uid, 'split': split, 'ridx': ridx, 'qi': qi,
                'key': sha_bytes((SEED + '|' + uid + '|' + q['uid']).encode('utf-8')),
                'q': q, 'rec': rec,
            })

    used = set()
    mine = []
    for layer in LAYERS:
        cands = sorted(qualified[layer], key=lambda x: x['key'])
        got = 0
        for c in cands:
            if c['uid'] in used:
                continue
            used.add(c['uid'])
            mine.append(c)
            got += 1
            if got == 4:
                break

    mine_rows = [{
        'task_id': 'T%02d' % (i + 1), 'layer': c['layer'], 'uid': c['uid'],
        'question_uid': c['q']['uid'], 'rank16': c['key'][:16],
    } for i, c in enumerate(mine)]
    log_rows = [{
        'task_id': r['task_id'], 'layer': r['layer'], 'uid': r['uid'],
        'question_uid': r['question_uid'], 'rank16': r.get('rank_key'),
    } for r in log['selected']]

    counts_diff = {}
    log_skip = log['skip_counts']
    for k in sorted(set(counts) | set(log_skip)):
        if counts.get(k, 0) != log_skip.get(k, 0):
            counts_diff[k] = {'mine': counts.get(k, 0), 'log': log_skip.get(k, 0)}

    out['selection_recompute'] = {
        'skip_counts_match': not counts_diff,
        'skip_counts_diff': counts_diff,
        'my_skip_counts': counts,
        'my_qualified_counts': {l: len(qualified[l]) for l in LAYERS},
        'my_eligible_records': eligible_records,
        'log_eligible_records': log.get('eligible_records'),
        'selected_rows_match': mine_rows == log_rows,
        'selected_mine': mine_rows,
        'selected_log': log_rows,
    }
    if counts_diff or mine_rows != log_rows:
        problems.append('selection_recompute')

    # ---- 4. per-task deep checks ----
    groups = load(Q / 'panel' / 'GROUPS.json')
    per_task = []
    for r in log['selected']:
        tid = r['task_id']
        split = r['split']
        rec = (train if split == 'train' else dev)[r['record_index']]
        q = next(qq for qq in rec['questions'] if qq['uid'] == r['question_uid'])
        ref = load(Q / 'panel' / 'reference' / (tid + '.json'))
        sc = load(Q / 'panel' / 'scoring' / (tid + '.json'))
        inp = load(Q / 'panel' / 'inputs' / (tid + '.json'))
        row = {'task_id': tid, 'uid': r['uid']}
        row['raw_uid_ok'] = rec['table']['uid'] == r['uid']
        ofr = ref['official_reference']
        row['reference_matches_raw'] = (
            ofr.get('answer') == q.get('answer')
            and ofr.get('derivation') == q.get('derivation')
            and ofr.get('answer_type') == q.get('answer_type')
            and ofr.get('answer_from') == q.get('answer_from')
            and ofr.get('scale') == q.get('scale')
            and ofr.get('rel_paragraphs') == q.get('rel_paragraphs')
            and ofr.get('req_comparison') == q.get('req_comparison')
        )
        expr = norm_expr(q['derivation'])
        expr2 = expr.replace('*100', '')
        shape = classify_shape(expr2)
        val = eval_expr(expr)
        tolr = tolerance(q['answer'])
        enc = None
        if val is not None and abs(val - float(q['answer'])) <= tolr:
            enc = 'direct'
        elif val is not None and abs(val * 100.0 - float(q['answer'])) <= tolr:
            enc = 'x100'
        if shape == 'change_div':
            my_layer = 'percentage_change' if ('*100' in expr or enc == 'x100') else None
        elif shape == 'div':
            my_layer = 'ratio'
        elif shape == 'sub' and enc == 'direct':
            my_layer = 'difference'
        else:
            my_layer = None
        row['layer_recomputed'] = my_layer
        row['layer_ok'] = (my_layer == r['layer'] == groups.get(tid)) and (sc.get('notes') == 'layer=' + r['layer'])
        row['tolerance_ok'] = sc.get('abs_tolerance') == tolr
        row['expected_ok'] = sc.get('expected') == q['answer'] and sc.get('expected_precise') == float(q['answer'])
        if my_layer == 'percentage_change':
            uk = 'percent'
        elif my_layer == 'ratio':
            uk = 'percent' if enc == 'x100' else 'ratio'
        else:
            uk = 'percent' if '%' in str(q['derivation']) else 'plain'
        row['unit_kind_recomputed'] = uk
        row['unit_kind_ok'] = sc.get('unit_kind') == uk
        row['scoring_meta_ok'] = sc.get('scoring_version') == 'v21' and sc.get('compare_mode') == 'numeric'
        row['input_keys_ok'] = set(inp.keys()) == {'task_id', 'variant', 'question', 'table', 'paragraphs'}
        row['input_variant_original'] = inp.get('variant') == 'original'
        row['input_question_ok'] = inp.get('question') == q['question']
        row['input_table_eq_raw'] = jdump(inp['table']) == jdump(rec['table']['table'])
        row['input_paragraphs_eq_raw'] = jdump(inp['paragraphs']) == jdump(rec['paragraphs'])
        text = jdump(inp)
        hits = [kw for kw in ['*100', chr(0xd7) + '100', '"answer"', '"derivation"', '"reference"',
                              'perturb', 'stratum', 'injected', 'candidate'] if kw in text]
        row['leak_keyword_hits'] = hits
        row['no_uid_strings_in_input'] = (r['uid'] not in text) and (q['uid'] not in text)
        corpus = norm_text(jdump(inp['table'])) + '|' + norm_text(jdump(inp['paragraphs']))
        ops = num_tokens(expr.replace('*100', ''))
        row['operands_localizable'] = all(norm_text(o) in corpus for o in ops)
        log_files = None
        for lr in log['selected']:
            if lr['task_id'] == tid:
                log_files = lr.get('files') or {}
        if log_files:
            fs_ok = all(sha_file(Q / 'panel' / rel) == h for rel, h in log_files.items())
        else:
            fs_ok = None
        row['log_recorded_file_shas_ok'] = fs_ok
        per_task.append(row)

    flags = ['raw_uid_ok', 'reference_matches_raw', 'layer_ok', 'tolerance_ok', 'expected_ok',
             'unit_kind_ok', 'scoring_meta_ok', 'input_keys_ok', 'input_variant_original',
             'input_question_ok', 'input_table_eq_raw', 'input_paragraphs_eq_raw',
             'no_uid_strings_in_input', 'operands_localizable']
    bad_tasks = [t['task_id'] for t in per_task
                 if (not all(t[f] for f in flags)) or t['leak_keyword_hits'] or t['log_recorded_file_shas_ok'] is False]
    out['per_task'] = {'checked': len(per_task), 'bad': bad_tasks, 'rows': per_task}
    if bad_tasks:
        problems.append('per_task:' + ','.join(bad_tasks))

    # ---- 5. config / budget / schedule ----
    cfg = load(Q / 'execution_v1' / 'chain_config_tq5.json')
    steps = cfg['steps']
    kinds = {}
    for s in steps:
        kinds[s['kind']] = kinds.get(s['kind'], 0) + 1
    exp_bc = []
    for i in range(12):
        pair = ('b', 'c') if i % 2 == 0 else ('c', 'b')
        for k in pair:
            exp_bc.append(k + '|T%02d' % (i + 1))
    actual_bc = [s['key'] for s in steps[12:]]
    actors_ok = [s['key'] for s in steps[:12]] == ['actor|T%02d' % (i + 1) for i in range(12)]
    src_ok = all(s.get('source_key') == 'actor|' + s['task_id'] for s in steps if s['kind'] in ('b', 'c'))
    budget = cfg.get('budget') or {}
    budget_ok = (
        budget.get('gen_cap') == 40 and budget.get('retry_cap') == 4
        and budget.get('token_cap') == 400000 and budget.get('window_min') == 90
        and budget.get('allowed_dates') == ['2026-10-16', '2026-10-17', '2026-10-18', '2026-10-19']
    )
    paths = {
        'templates_md': B / 'tq4_calibration_v1' / 'run_card_v2' / 'prompt_templates_v2.md',
        'material_manifest': Q / 'MANIFEST.json',
        'material_pins_lf': Q / 'execution_v1' / 'tq5_material_pins_lf_v1.json',
        'scoring_dir': Q / 'panel' / 'scoring',
        'groups_file': Q / 'panel' / 'GROUPS.json',
        'authorization_file': B / 'tq4_calibration_v1' / 'run_card_v2' / 'OWNER_DELEGATED_AUTHORIZATION_20261016_v1.md',
        'master_ledger': B / 'tq4_calibration_v1' / 'runs' / '_chain' / 'chain_master_ledger.jsonl',
    }
    paths_ok = {k: v.exists() for k, v in paths.items()}
    ledger_path = paths['master_ledger']
    ledger_lines = ledger_path.read_text(encoding='utf-8').strip().splitlines()
    ledger_panels = set()
    ledger_ops = {}
    for line in ledger_lines:
        j = json.loads(line)
        ledger_panels.add(j.get('panel'))
        ledger_ops[j.get('op')] = ledger_ops.get(j.get('op'), 0) + 1
    runs_dir_items = [p.name for p in (Q / 'runs').iterdir() if p.name != '.gitignore']

    point5 = load(B / 'tq4_calibration_v1' / 'execution_v1' / 'tests'
                  / 'chain_point_checks_tq5_DESKTOP-EKG77SP_20261016T084722Z.json')
    runner_sha = sha_file(B / 'tq4_calibration_v1' / 'execution_v1' / 'chain_runner.py')

    out['config'] = {
        'steps_total': len(steps), 'kinds': kinds, 'unique_keys': len(set(s['key'] for s in steps)),
        'actors_first_in_layer_order': actors_ok,
        'bc_alternation_pattern_ok': actual_bc == exp_bc,
        'bc_source_same_actor_output': src_ok,
        'budget_ok': budget_ok,
        'paths_exist': paths_ok,
        'master_ledger': {'lines': len(ledger_lines), 'panels': sorted(str(x) for x in ledger_panels), 'ops': ledger_ops},
        'runs_dir_items': runs_dir_items,
        'point_checks_tq5_all_passed': bool(point5.get('all_passed')),
        'runner_sha256_current': runner_sha,
        'runner_sha256_pointcheck': point5.get('runner_sha256'),
        'runner_sha_matches_pointcheck': runner_sha == point5.get('runner_sha256'),
    }
    c = out['config']
    if not (c['steps_total'] == 36 and c['kinds'] == {'actor': 12, 'b': 12, 'c': 12}
            and c['unique_keys'] == 36 and actors_ok and c['bc_alternation_pattern_ok']
            and src_ok and budget_ok and all(paths_ok.values())
            and c['master_ledger']['panels'] == ['TQ-4'] and not runs_dir_items
            and c['point_checks_tq5_all_passed'] and c['runner_sha_matches_pointcheck']):
        problems.append('config')

    # ---- 6. v1 inoperability statistics ----
    slash_all = slash_star_all = 0
    slash_elig = slash_star_elig = 0
    multi_sign = 0
    for split, arr in (('train', train), ('dev', dev)):
        for rec in arr:
            in_excl = rec['table']['uid'] in union
            for q in rec['questions']:
                d = q.get('derivation') or ''
                if not str(d).strip():
                    continue
                e = norm_expr(str(d))
                if '/' not in e:
                    continue
                slash_all += 1
                hit = ('*100' in e)
                if hit:
                    slash_star_all += 1
                if not in_excl:
                    slash_elig += 1
                    if hit:
                        slash_star_elig += 1
                if chr(0xd7) in e:
                    multi_sign += 1
    out['v1_inoperability_stats'] = {
        'slash_derivations_all_records': slash_all,
        'slash_with_star100_all_records': slash_star_all,
        'slash_derivations_eligible_records': slash_elig,
        'slash_with_star100_eligible_records': slash_star_elig,
        'derivations_with_multiplication_sign': multi_sign,
    }

    v1_pct = 0
    for split, ridx, rec in records:
        if rec['table']['uid'] in union:
            continue
        corpus = norm_text(jdump(rec['table']['table'])) + '|' + norm_text(jdump(rec['paragraphs']))
        for q in rec['questions']:
            a = q.get('answer')
            if q.get('answer_from') not in OK_ANSWER_FROM:
                continue
            if not isinstance(a, (int, float)) or isinstance(a, bool):
                continue
            d = q.get('derivation') or ''
            if not str(d).strip():
                continue
            expr = norm_expr(str(d))
            if '*100' not in expr:
                continue
            expr2 = expr.replace('*100', '')
            if classify_shape(expr2) != 'change_div':
                continue
            val = eval_expr(expr)
            tolr = tolerance(a)
            if val is None:
                continue
            if not (abs(val - float(a)) <= tolr or abs(val * 100.0 - float(a)) <= tolr):
                continue
            ops = num_tokens(expr2)
            if any(norm_text(o) not in corpus for o in ops):
                continue
            v1_pct += 1
    out['v1_inoperability_stats']['v1_style_pct_qualified_upper_bound'] = v1_pct

    v1log = load(Q / 'panel_v1_shortage_record' / 'SELECTION_LOG_v1_NOT_RUN.json')
    v1_traces = v1log.get('layer_scan_traces') or {}
    v1_sel_counts = {l: len([t for t in v1_traces.get(l, []) if t.get('outcome') == 'selected']) for l in v1_traces}
    out['v1_shortage_record'] = {
        'status': v1log.get('status'),
        'selected_counts_from_traces': v1_sel_counts,
        'skip_counts': v1log.get('skip_counts'),
    }
    if v1_sel_counts.get('percentage_change') != 1:
        problems.append('v1_shortage_record_unexpected')

    out['problems'] = problems
    out['verdict'] = 'NO_SUBSTANTIVE_BLOCKER' if not problems else 'BLOCKERS:' + ';'.join(problems)

    dst = HERE / 'TQ5_PREREVIEW_RECOMPUTE_v1.json'
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')
    print(json.dumps({
        'verdict': out['verdict'],
        'skip_counts_match': out['selection_recompute']['skip_counts_match'],
        'selected_match': out['selection_recompute']['selected_rows_match'],
        'pins_ok': not (bad or lf_bad or lf_missing or extra),
        'per_task_bad': out['per_task']['bad'],
        'config_ok': 'config' not in problems,
        'v1_stats': out['v1_inoperability_stats'],
    }, ensure_ascii=False))
    return 0 if not problems else 1


if __name__ == '__main__':
    sys.exit(main())
