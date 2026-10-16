# -*- coding: utf-8 -*-
'''Re-score the 12 saved TQ-3 actor outputs with the v2 scorer; report v1 vs v2 differences.

Reads (read-only): the mirrored TQ-3 run dir + dev_panel scoring/inputs.
Writes: rescore_results.json (this directory only). No model calls, no network.
'''
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TQ4 = HERE.parent
BASE = TQ4.parent
TQ3 = BASE / 'tq3_execution_prep_v1'
RUN = TQ3 / 'runs' / '20261016T051556Z_af4c2db6'
sys.path.insert(0, str(TQ4 / 'scorer_v2'))
sys.path.insert(0, str(TQ3 / 'tools'))
import tq4_scoring_entry as V2
import tq3_scoring_entry as V1

V2_UNIT_KIND = {'Q10': 'ratio', 'Q03': 'plain', 'Q04': 'plain', 'Q12': 'plain'}


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def to_v2_config(case, old):
    cfg = dict(old)
    if old['compare_mode'] == 'span_containment_normalized':
        cfg['compare_mode'] = 'list_full_match'
        cfg['expected_full'] = old['expected_spans'][0]
        cfg['expected_items'] = old['expected_spans']
    elif old['compare_mode'] == 'numeric':
        cfg['unit_kind'] = V2_UNIT_KIND[case]
    return cfg


def main():
    rows = []
    changed = []
    legality_summary = {'legal': 0, 'illegal': 0, 'issue_types': {}}
    for seq in range(1, 13):
        raws = sorted((RUN / 'raw').glob(str(seq).zfill(4) + '_actor_*.json'))
        raw = load(raws[0])
        case = raw['case']
        variant = raw['variant']
        obj = raw['parse']['result']
        old = load(TQ3 / 'dev_panel' / 'scoring' / (case + '.json'))
        v1r = V1.score(case, obj, old)
        v2cfg = to_v2_config(case, old)
        v2r = V2.score(case, obj, v2cfg)
        inp = load(TQ3 / 'dev_panel' / ('inputs_' + variant) / (case + '.json'))
        leg = V2.check_evidence_legality(inp['table'], inp['paragraphs'], obj.get('evidence'))
        if leg['legal']:
            legality_summary['legal'] += 1
        else:
            legality_summary['illegal'] += 1
        for i in leg['issues']:
            legality_summary['issue_types'][i['issue']] = legality_summary['issue_types'].get(i['issue'], 0) + 1
        row = {'seq': seq, 'task_id': case, 'variant': variant,
               'answer': obj.get('answer'),
               'v1_status': v1r['status'], 'v2_status': v2r['status'],
               'changed': v1r['status'] != v2r['status'],
               'v2_detail': v2r.get('detail'),
               'legality_v2_view': leg}
        if row['changed']:
            changed.append(row)
        rows.append(row)
    out = {'schema': 'tq4_rescore_results_v1',
           'generated_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'run_id': RUN.name,
           'v1_module_sha256': hashlib.sha256((TQ3 / 'tools' / 'tq3_scoring_entry.py').read_bytes()).hexdigest(),
           'v2_module_sha256': hashlib.sha256((TQ4 / 'scorer_v2' / 'tq4_scoring_entry.py').read_bytes()).hexdigest(),
           'notes': ['Mapping: span_containment_normalized -> list_full_match; numeric gains frozen unit_kind (Q10 ratio; Q03/Q04/Q12 plain).',
                     'The v2 legality view of old evidence is reported for interpretation only; old outputs are not rewritten.'],
           'counts': {'items': len(rows), 'v1_match': sum(1 for r in rows if r['v1_status'] == 'MATCH'),
                      'v2_match': sum(1 for r in rows if r['v2_status'] == 'MATCH'),
                      'changed': len(changed)},
           'legality_v2_view_summary': legality_summary,
           'changed_rows': changed, 'rows': rows}
    (HERE / 'rescore_results.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')
    print(json.dumps({'counts': out['counts'], 'legality': legality_summary}, ensure_ascii=True))
    for r in rows:
        print(r['seq'], r['task_id'], r['variant'], '|', r['v1_status'], '->', r['v2_status'], '|', json.dumps(r['answer'], ensure_ascii=False)[:40], '| legality_issues:', len(r['legality_v2_view']['issues']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
