#!/usr/bin/env python3
"""Read-only recomputation of the frozen Paper E negative results (bug / synthetic-data audit, 2026-10-13)."""
import collections
import hashlib
import json
import math
import pathlib

ROOT = pathlib.Path('.').resolve()
OUTDIR = ROOT / 'data/research/negative_result_robustness_20261013'


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding='utf-8'))


def record(receipt, name, value):
    receipt['checks'][name] = value


receipt = {'audit': 'negative_result_robustness_v1', 'date_utc': '2026-10-13', 'checks': {}, 'summary': {}}

# ---------------- A. Stage E ----------------
t2 = load('logs/graph/eval/t2_visibility_sensitivity.json')
inj = t2['injections']
record(receipt, 'A_injections_n', len(inj))

by = collections.defaultdict(lambda: {'n': 0, 'visible_frozen': 0})
for r in inj:
    by[r['type']]['n'] += 1
    if r.get('visible_frozen'):
        by[r['type']]['visible_frozen'] += 1
fam = {k: dict(v) for k, v in sorted(by.items())}
record(receipt, 'A_family_visible_frozen', fam)
record(receipt, 'A_total_visible', sum(v['visible_frozen'] for v in by.values()))
record(receipt, 'A_total_absorbed', len(inj) - sum(v['visible_frozen'] for v in by.values()))

paper_fam = {
    'alias_variant': {'n': 47, 'visible_frozen': 43},
    'date_variant': {'n': 17, 'visible_frozen': 15},
    'mixed_lang': {'n': 20, 'visible_frozen': 20},
    'ocr_similar': {'n': 13, 'visible_frozen': 0},
    'prefix_noise': {'n': 16, 'visible_frozen': 13},
    'unit_suffix': {'n': 5, 'visible_frozen': 5},
}
receipt['summary']['A_family_counts_match_paper'] = (fam == paper_fam)
receipt['summary']['A_total_96_match'] = (sum(v['visible_frozen'] for v in by.values()) == 96)

ocr = [r for r in inj if r['type'] == 'ocr_similar']
record(receipt, 'A_ocr_n', len(ocr))
record(receipt, 'A_ocr_clusters', len({r['uid'] for r in ocr}))
record(receipt, 'A_ocr_all_gamma_invisible', all(not any(r['visible_by_gamma'].values()) for r in ocr))
record(receipt, 'A_ocr_mapping_keys_same_full', sum(1 for r in ocr if r.get('mapping_keys_same_full')))
record(receipt, 'A_ocr_absorbed_full', sum(1 for r in ocr if r.get('absorbed_full_injection')))


def lev(a, b):
    if abs(len(a) - len(b)) > 2:
        return 99
    prev = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
        prev = cur
    return prev[-1]


cases = []
for r in ocr:
    o, i2 = r['original'], r['injected']
    ot, it = o.split(), i2.split()
    diff_idx = [k for k in range(len(ot)) if ot[k] != it[k]] if len(ot) == len(it) else []
    k = diff_idx[0] if len(diff_idx) == 1 else None
    cases.append({
        'uid': r['uid'][:8], 'col': r['col'], 'original': o, 'injected': i2,
        'single_token_diff': len(diff_idx) == 1,
        'orig_token': ot[k] if k is not None else None,
        'inj_token': it[k] if k is not None else None,
        'casefolded_token_lev': lev(ot[k].casefold(), it[k].casefold()) if k is not None else None,
        'inj_token_lowercase': (it[k] == it[k].lower()) if k is not None else False,
    })
record(receipt, 'A_ocr_cases', cases)
record(receipt, 'A_ocr_morphology_definition', 'exactly one token differs; injected token lowercase; casefolded token-level Levenshtein distance == 1')
record(receipt, 'A_ocr_morphology_all_ok', all((c['single_token_diff'] and c['casefolded_token_lev'] == 1 and c['inj_token_lowercase']) for c in cases))
record(receipt, 'A_all_injections_change_text', all(r['original'] != r['injected'] for r in inj))

grid = t2['e2_1_gamma_grid']
grid_ok = {}
for g in ['0.2', '0.3', '0.5', '0.7', '0.9']:
    ok = True
    for t, v in grid[g]['by_type'].items():
        calc_v = sum(1 for r in inj if r['type'] == t and r['visible_by_gamma'][g])
        if v.get('visible') != calc_v or v.get('n') != by[t]['n']:
            ok = False
    grid_ok[g] = ok
record(receipt, 'A_gamma_grid_matches_injections', grid_ok)
receipt['summary']['A_gamma_grid_all_match'] = all(grid_ok.values())

cd = load('logs/graph/eval/checkpoint_discrimination_tables_v2.json')
rate_ok = all(math.isclose(cd['by_type'][t]['visibility_rate'], by[t]['visible_frozen'] / by[t]['n'], abs_tol=1e-9) for t in by)
record(receipt, 'A_checkpoint_rates_match', rate_ok)

record(receipt, 'A_frozen_hashes', {
    't2_visibility_sensitivity': sha('logs/graph/eval/t2_visibility_sensitivity.json'),
    'checkpoint_discrimination_tables_v2': sha('logs/graph/eval/checkpoint_discrimination_tables_v2.json'),
    'injection_map': sha('data/research/drift_v0/output/injection_map.json'),
    'tatqa_tables_input': sha('data/research/drift_v0/input/tatqa_tables.json'),
})

d2 = load('logs/graph/eval/d2_cross_matcher_det.json')['payload']
record(receipt, 'A_blind_types_by_matcher', d2['blind_types'])
record(receipt, 'A_blind_single_family_ocr_all_matchers', all(v == ['ocr_similar'] for v in d2['blind_types'].values()))
gn = d2['matcher_class_transitions']['greedy_normalized']
record(receipt, 'A_normalization_flips', {'n_flips': gn['n_flips'], 'flip_types': gn['flip_types']})
receipt['summary']['A_normalization_flips_all_date_variant'] = (gn['n_flips'] == 5 and list(gn['flip_types'].keys()) == ['date_variant'])

# ---------------- B. matched-FPR ----------------
fpr = load('research/stage_e_method_revision_20261009/matched_fpr_reanalysis.json')
se = fpr['structural_equivalence']
dat = fpr['data']
ident = fpr['identification']
slopes = se['slope_layered_over_flat']
record(receipt, 'B_slopes', slopes)
record(receipt, 'B_max_dev_from_0375', max(abs(s - 0.375) for s in slopes))
record(receipt, 'B_grid_differences_unique', sorted({pt['difference'] for f in fpr['cross_fit'] for pt in f['fixed_affine_grid_sensitivity']}))
record(receipt, 'B_supports', {'clean_flat_support': dat['clean_flat_support'], 'clean_layered_support': dat['clean_layered_support'], 'n_clean_usable': dat['n_clean_usable'], 'n_harmful_H_union_HI': dat['n_harmful_H_union_HI']})
record(receipt, 'B_identification', {'threshold_identifiable': ident['threshold_identifiable'], 'reason_head': ident['reason'][:110]})
frozen_paths = {
    'd3_matched_fpr_stage_a': 'logs/graph/eval/d3_matched_fpr_stage_a.json',
    'd1_mutant_validity_audit': 'logs/graph/eval/d1_mutant_validity_audit.json',
}
record(receipt, 'B_frozen_inputs_match', {name: (sha(path) == fpr['frozen_inputs'].get(name)) for name, path in frozen_paths.items()})
record(receipt, 'B_folds', len(fpr['cross_fit']))
receipt['summary']['B_slopes_all_approx_0375'] = all(abs(s - 0.375) < 1e-6 for s in slopes)
receipt['summary']['B_grid_all_zero'] = sorted({pt['difference'] for f in fpr['cross_fit'] for pt in f['fixed_affine_grid_sensitivity']}) == [0]
receipt['summary']['B_supports_zero'] = (dat['clean_flat_support'] == [0.0] and dat['clean_layered_support'] == [0.0])

# ---------------- C. multi-leaf ----------------
rows = [json.loads(line) for line in (ROOT / 'research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl').read_text().splitlines() if line.strip()]
record(receipt, 'C_rows', len(rows))
clusters = sorted({r['cluster_id'] for r in rows})
record(receipt, 'C_clusters', len(clusters))
abl = load('research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json')
leaves = abl['feature_sets']['full_vector']['features']
record(receipt, 'C_leaves', leaves)

stages = ('M', 'R', 'N')
DIRECT = {'parse.field.hit_rate', 'qa.retrieval.source_required', 'parse.reconcile.equations'}
subsets = {
    'full_vector': leaves,
    'direct_target_codebook': [f for f in leaves if f in DIRECT],
    'non_direct_leaves_only': [f for f in leaves if f not in DIRECT],
}
TIE = '__TIE__'
EPS = 1e-12


def predict(vecs, labels, clus, feats):
    preds = [None] * len(vecs)
    for c in sorted(set(clus)):
        train = [i for i in range(len(vecs)) if clus[i] != c]
        cents = {}
        for s in stages:
            idx = [i for i in train if labels[i] == s]
            cents[s] = [sum(vecs[i][f] for i in idx) / len(idx) for f in feats]
        for i in range(len(vecs)):
            if clus[i] != c:
                continue
            d = {s: math.sqrt(sum((vecs[i][f] - cents[s][k]) ** 2 for k, f in enumerate(feats))) for s in stages}
            mn = min(d.values())
            tied = [s for s in stages if abs(d[s] - mn) <= EPS]
            preds[i] = TIE if len(tied) > 1 else min(d, key=d.get)
    return preds


def macro_f1(labels, preds):
    vals = []
    for s in stages:
        tp = sum(1 for a, b in zip(labels, preds) if a == s and b == s)
        fp = sum(1 for a, b in zip(labels, preds) if a != s and b == s)
        fn = sum(1 for a, b in zip(labels, preds) if a == s and b != s)
        den = 2 * tp + fp + fn
        vals.append(0.0 if den == 0 else 2 * tp / den)
    return sum(vals) / 3


vecs = [{f: float(r['response_vector'][f]) for f in leaves} for r in rows]
labels = [r['true_stage'] for r in rows]
clus = [r['cluster_id'] for r in rows]
C = {}
for name, feats in subsets.items():
    preds = predict(vecs, labels, clus, feats)
    C[name] = {'macro_f1': macro_f1(labels, preds),
               'top1': sum(1 for a, b in zip(labels, preds) if a == b) / len(rows),
               'tie_rate': sum(1 for p in preds if p == TIE) / len(rows)}
scalar_vecs = [{'any': float(any(v > 0 for v in r['response_vector'].values()))} for r in rows]
sp = predict(scalar_vecs, labels, clus, ['any'])
C['any_response_scalar'] = {'macro_f1': macro_f1(labels, sp),
                            'top1': sum(1 for a, b in zip(labels, sp) if a == b) / len(rows),
                            'tie_rate': sum(1 for p in sp if p == TIE) / len(rows)}
record(receipt, 'C_recomputed', C)

stored = abl['feature_sets']
compare = {}
for name in ('full_vector', 'direct_target_codebook', 'non_direct_leaves_only', 'any_response_scalar'):
    s = stored[name]
    compare[name] = (abs(s['macro_f1'] - C[name]['macro_f1']) <= 1e-9
                     and abs(s['top1_accuracy'] - C[name]['top1']) <= 1e-9
                     and abs(s['tie_rate'] - C[name]['tie_rate']) <= 1e-9)
record(receipt, 'C_matches_stored', compare)
receipt['summary']['C_matches_stored_all'] = all(compare.values())

zero_cols = [f for f in leaves if all(float(r['response_vector'][f]) == 0 for r in rows)]
record(receipt, 'C_zero_leaf_columns', {'count': len(zero_cols), 'leaves': zero_cols})
patterns = {}
for s in stages:
    srows = [r for r in rows if r['true_stage'] == s]
    patterns[s] = len({tuple(r['response_vector'][f] for f in leaves) for r in srows})
record(receipt, 'C_patterns_per_stage_unique', patterns)
record(receipt, 'C_m_profile', {
    'field_hit_rate_all_1': all(float(r['response_vector']['parse.field.hit_rate']) == 1 for r in rows if r['true_stage'] == 'M'),
    'table_regression_all_1': all(float(r['response_vector']['parse.table.regression']) == 1 for r in rows if r['true_stage'] == 'M'),
})
record(receipt, 'C_r_profile', {'source_required_all_1': all(float(r['response_vector']['qa.retrieval.source_required']) == 1 for r in rows if r['true_stage'] == 'R')})
record(receipt, 'C_n_profile', {'reconcile_all_1': all(float(r['response_vector']['parse.reconcile.equations']) == 1 for r in rows if r['true_stage'] == 'N')})

formal = load('research/stage_e_multileaf_20261010/results/multileaf_formal_results.json')
record(receipt, 'C_leakage_audit', formal['leakage_audit'])
record(receipt, 'C_primary', formal['primary'])
record(receipt, 'C_baseline', formal['baseline'])
runrec = load('research/stage_e_multileaf_20261010/results/multileaf_run_receipt.json')
files = {
    'predictions_sha256': 'research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl',
    'result_json_sha256': 'research/stage_e_multileaf_20261010/results/multileaf_formal_results.json',
    'formal_runner_sha256': 'research/stage_e_multileaf_20261010/run_multileaf_formal.py',
}
record(receipt, 'C_receipt_hash_checks', {k: (sha(v) == runrec.get(k)) for k, v in files.items()})
freeze = load('research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json')
record(receipt, 'C_freeze_fields', {
    'status': freeze.get('status'),
    'temporal_order': freeze.get('temporal_order'),
    'result_artifacts_absent_at_freeze': freeze.get('result_artifacts_absent_at_freeze'),
})
receipt['summary']['C_zero_columns_8'] = (len(zero_cols) == 8)
receipt['summary']['C_patterns_unique_1_each'] = (set(patterns.values()) == {1})

OUTDIR.mkdir(parents=True, exist_ok=True)
(OUTDIR / 'recompute_receipt.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False, default=str) + '\n', encoding='utf-8')
print(json.dumps(receipt['summary'], indent=1))
print('receipt:', OUTDIR / 'recompute_receipt.json')
