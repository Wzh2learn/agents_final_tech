# -*- coding: utf-8 -*-
'''TQ-4 scoring entry v2.1 (v2 semantics + N-1 hardening, authorized 2026-10-16).\nv2.1 change: check_evidence_legality requires cell coordinates to be true ints (bool rejected,\n'cell_not_integer'); scoring semantics, references and tolerances are unchanged from v2.

Fixes vs tq3_scoring_entry v1:
- percent conversion is driven ONLY by explicit unit markers; numeric magnitude
  never decides whether to divide by 100;
- numeric answers containing multiple candidate numbers are UNSCORABLE
  (no cherry-picking among numbers);
- list answers require full-set equality after defined normalization
  (no substring containment in either direction);
- unparseable or ambiguous answers return explicit UNSCORABLE_* statuses
  instead of guessing.

Carried unchanged from v1 for compatibility: load_input and
validate_reference_coords helpers (input isolation + reference coordinate check).

No network. No model calls. Stdlib only.
'''
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

ALLOWED_INPUT_KEYS = {'task_id', 'variant', 'question', 'table', 'paragraphs'}
FORBIDDEN_KEYS = {
    'official_reference', 'answer', 'derivation', 'gold', 'v4_label',
    'checker_verdict', 'injection_id', 'col', 'original', 'injected',
    'source_table', 'rel_paragraphs', 'scale', 'answer_from', 'answer_type',
}
ALLOWED_VARIANTS = {'original', 'perturbed'}


class InputRejected(Exception):
    '''Raised when an input fails schema/leakage/hash checks; no object is returned.'''


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _scan_forbidden(obj, path=''):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_KEYS:
                hits.append(path + '/' + str(k))
            hits += _scan_forbidden(v, path + '/' + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += _scan_forbidden(v, path + '/' + str(i))
    return hits


def load_input(path, expected_sha256=None):
    raw = Path(path).read_bytes()
    actual = sha256_bytes(raw)
    if expected_sha256 is not None and actual != expected_sha256:
        raise InputRejected('INPUT_HASH_MISMATCH: expected ' + expected_sha256[:12] + '..., got ' + actual[:12] + '...')
    obj = json.loads(raw.decode('utf-8'))
    if not isinstance(obj, dict):
        raise InputRejected('INPUT_NOT_OBJECT')
    hits = _scan_forbidden(obj)
    if hits:
        raise InputRejected('INPUT_LEAKAGE: ' + ';'.join(hits))
    keys = set(obj.keys())
    if keys != ALLOWED_INPUT_KEYS:
        raise InputRejected('INPUT_SCHEMA_KEYS: ' + ','.join(sorted(keys)))
    if obj.get('variant') not in ALLOWED_VARIANTS:
        raise InputRejected('INPUT_VARIANT_INVALID: ' + repr(obj.get('variant')))
    if not isinstance(obj.get('table'), list) or not obj['table']:
        raise InputRejected('INPUT_TABLE_INVALID')
    return obj


def check_evidence_legality(table, paragraphs, evidence):
    '''Protocol v2 MECHANICAL legality check only (kind / 0-based cell bounds /
    paragraph uid existence). It does NOT judge whether evidence supports the
    answer; support is recorded separately by the semantic checkers (B/C).'''
    p_uids = set()
    for p in paragraphs or []:
        if isinstance(p, dict) and p.get('uid'):
            p_uids.add(p['uid'])
    if not isinstance(evidence, list):
        return {'legal': False, 'issues': [{'index': None, 'issue': 'evidence_not_list'}], 'checked': 0}
    issues = []
    for i, e in enumerate(evidence):
        if not isinstance(e, dict):
            issues.append({'index': i, 'issue': 'not_object'})
            continue
        kind = e.get('kind')
        if kind == 'cell':
            r0 = e.get('table_row')
            c0 = e.get('table_col')
            if type(r0) is not int or type(c0) is not int:
                issues.append({'index': i, 'issue': 'cell_not_integer', 'table_row': r0, 'table_col': c0})
            elif r0 < 0 or c0 < 0 or r0 >= len(table) or c0 >= len(table[r0]):
                issues.append({'index': i, 'issue': 'cell_out_of_bounds', 'table_row': r0, 'table_col': c0})
        elif kind == 'paragraph':
            uid = e.get('paragraph_uid')
            if uid not in p_uids:
                issues.append({'index': i, 'issue': 'paragraph_uid_unknown', 'paragraph_uid': uid})
        else:
            issues.append({'index': i, 'issue': 'kind_invalid', 'kind': kind})
    return {'legal': not issues, 'issues': issues, 'checked': len(evidence)}


_NUM_RE = re.compile('(?<![A-Za-z0-9.,-])[-+]?[0-9][0-9,]*(?:[.][0-9]+)?[ ]*%?')


def _extract_numbers_v2(text):
    out = []
    for m in _NUM_RE.finditer(str(text)):
        tok = m.group(0)
        has_pct = tok.rstrip().endswith('%')
        t = tok.replace(',', '').replace('%', '').strip()
        try:
            out.append((float(t), has_pct))
        except ValueError:
            pass
    return out


def _norm_text(s):
    s = str(s).lower().strip().rstrip('.').strip()
    return ' '.join(s.split())


def _split_items(s):
    t = ' ' + _norm_text(s) + ' '
    t = t.replace(' and ', '|||').replace('&', '|||').replace(';', '|||').replace(',', '|||')
    return [x.strip(' .') for x in t.split('|||') if x.strip(' .')]


def _score_numeric(answer, mat):
    if 'unit_scale_status' in mat and mat.get('unit_scale_status') is None:
        return {'status': 'BLOCKED_SCALE_MISSING', 'score': None}
    if str(mat.get('unit_scale_status', '')).startswith('UNRESOLVED'):
        return {'status': 'BLOCKED_SCALE_UNRESOLVED', 'score': None}
    nums = _extract_numbers_v2(answer)
    if len(nums) == 0:
        return {'status': 'UNSCORABLE_NO_NUMERIC', 'score': None, 'detail': {'answer': str(answer)[:120]}}
    if len(nums) > 1:
        return {'status': 'UNSCORABLE_MULTIPLE_NUMBERS', 'score': None, 'detail': {'values': [n[0] for n in nums]}}
    v, has_pct = nums[0]
    unit_kind = mat.get('unit_kind')
    if unit_kind not in ('ratio', 'percent', 'plain'):
        return {'status': 'UNSCORABLE_UNIT_KIND_UNSPECIFIED', 'score': None, 'detail': {'unit_kind': unit_kind}}
    if unit_kind == 'ratio':
        cand = v / 100.0 if has_pct else v
    elif unit_kind == 'percent':
        cand = v
    else:
        if has_pct:
            return {'status': 'UNSCORABLE_PERCENT_MARKER_ON_PLAIN_UNIT', 'score': None, 'detail': {'value': v}}
        cand = v
    expected = float(mat['expected_precise'])
    tol = float(mat['abs_tolerance'])
    ok = abs(cand - expected) <= tol
    return {'status': 'MATCH' if ok else 'NO_MATCH', 'score': 1.0 if ok else 0.0,
            'detail': {'answer_value': v, 'normalized': cand, 'expected': expected, 'tolerance': tol, 'percent_marker': has_pct}}


def _score_list(answer, mat):
    expected_full = mat.get('expected_full')
    if isinstance(expected_full, str) and _norm_text(answer) == _norm_text(expected_full):
        return {'status': 'MATCH', 'score': 1.0, 'detail': {'via': 'normalized_full_equality'}}
    exp_items = mat.get('expected_items')
    if not isinstance(exp_items, list) or not exp_items:
        return {'status': 'UNSCORABLE_EXPECTED_ITEMS_MISSING', 'score': None}
    exp_set = set()
    for item in exp_items:
        exp_set |= set(_split_items(item))
    ans_set = set(_split_items(answer))
    if not ans_set:
        return {'status': 'UNSCORABLE_EMPTY_ITEMS', 'score': None}
    ok = ans_set == exp_set
    return {'status': 'MATCH' if ok else 'NO_MATCH', 'score': 1.0 if ok else 0.0,
            'detail': {'expected_items': sorted(exp_set), 'answer_items': sorted(ans_set)}}


def _score_date(answer, mat):
    fmts = mat.get('accepted_formats') or ['%d %B %Y']
    parsed = None
    for f in fmts:
        try:
            parsed = datetime.strptime(str(answer).strip(), f)
            break
        except ValueError:
            parsed = None
    if parsed is None:
        return {'status': 'UNSCORABLE_DATE_PARSE', 'score': None}
    exp_dt = datetime.strptime(mat['expected'], '%d %B %Y')
    ok = parsed.date() == exp_dt.date()
    return {'status': 'MATCH' if ok else 'NO_MATCH', 'score': 1.0 if ok else 0.0}


def score(task_id, actor_output, scoring_material):
    '''Score one answer under v2 rules. Returns dict with status and score
    (score is None whenever no valid MATCH/NO_MATCH verdict could be produced).'''
    out = {'task_id': task_id, 'status': None, 'score': None}
    if not isinstance(actor_output, dict):
        out['status'] = 'INVALID_ACTOR_OUTPUT'
        return out
    answer = actor_output.get('answer')
    if answer is None or str(answer).strip() == '':
        out['status'] = 'INVALID_ACTOR_OUTPUT'
        return out
    mode = scoring_material.get('compare_mode')
    if mode == 'numeric':
        res = _score_numeric(answer, scoring_material)
    elif mode == 'list_full_match':
        res = _score_list(answer, scoring_material)
    elif mode == 'date':
        res = _score_date(answer, scoring_material)
    else:
        raise InputRejected('UNSUPPORTED_COMPARE_MODE: ' + str(mode))
    out.update(res)
    return out
