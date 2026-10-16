# -*- coding: utf-8 -*-
'''Run TQ-4 regression: execute each fixture answer through v1 (old) and v2 (fixed) scorers.'''
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCORER_V2 = HERE.parent
TQ4 = SCORER_V2.parent
BASE = TQ4.parent
TQ3_TOOLS = BASE / 'tq3_execution_prep_v1' / 'tools'
sys.path.insert(0, str(SCORER_V2))
sys.path.insert(0, str(TQ3_TOOLS))
import tq4_scoring_entry as V2
import tq3_scoring_entry as V1


def main():
    fx = json.loads((HERE / 'tq4_regression_cases.json').read_text(encoding='utf-8-sig'))
    rows = []
    fails = []
    v1_diff_count = 0
    for case in fx['cases']:
        for a in case['answers']:
            v2r = V2.score(case['case_id'], {'answer': a['answer']}, case['v2_config'])
            v1r = V1.score(case['case_id'], {'answer': a['answer']}, case['v1_config'])
            ok = v2r['status'] == a['expect_v2']
            diff = v1r['status'] != v2r['status']
            if diff:
                v1_diff_count += 1
            if a.get('v1_diff_expected') and not diff:
                ok = False
            if not ok:
                fails.append({'case': case['case_id'], 'answer': a['answer']})
            rows.append({'case_id': case['case_id'], 'family': case['family'], 'answer': a['answer'],
                         'v2_status': v2r['status'], 'v1_status': v1r['status'],
                         'expect_v2': a['expect_v2'], 'v1_diff_expected': bool(a.get('v1_diff_expected')),
                         'v1_diff_observed': diff, 'pass': ok, 'note': a.get('note', '')})
    out = {'schema': 'tq4_regression_results_v1',
           'generated_utc': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'v1_module_sha256': hashlib.sha256((TQ3_TOOLS / 'tq3_scoring_entry.py').read_bytes()).hexdigest(),
           'v2_module_sha256': hashlib.sha256((SCORER_V2 / 'tq4_scoring_entry.py').read_bytes()).hexdigest(),
           'counts': {'checks': len(rows), 'passed': len(rows) - len(fails), 'failed': len(fails),
                      'v1_v2_status_differences': v1_diff_count},
           'all_passed': not fails, 'failures': fails, 'rows': rows}
    (HERE / 'regression_results.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')
    print(json.dumps({'all_passed': out['all_passed'], 'checks': len(rows), 'failed': fails,
                      'v1_v2_diffs': v1_diff_count}, ensure_ascii=True))
    return 0 if out['all_passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
