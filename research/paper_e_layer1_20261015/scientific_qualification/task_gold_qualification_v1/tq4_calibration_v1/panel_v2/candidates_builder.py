# -*- coding: utf-8 -*-
'''Build the 12 frozen TQ-4 manual candidates (spec v1). Deterministic; refuses to overwrite.'''
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
TQ4 = HERE.parent
BASE = TQ4.parent
TQ3 = BASE / 'tq3_execution_prep_v1'
sys.path.insert(0, str(TQ4 / 'scorer_v2'))
import tq4_scoring_entry as V2


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def write_json(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


TASK_SPECS = {
    'Q02': {'correct': 'accounts receivable, inventories, and net property, plant, and equipment',
            'incorrect': 'accounts receivable, inventories',
            'legal': [{'kind': 'paragraph', 'paragraph_uid': '5a443fa1-ad91-4454-8ba2-9992a29bd813'}],
            'illegal': [{'kind': 'paragraph', 'paragraph_uid': '00000000-0000-0000-0000-000000000000'}]},
    'Q03': {'correct': 14054, 'incorrect': -14054,
            'legal': [{'kind': 'cell', 'table_row': 2, 'table_col': 2}, {'kind': 'cell', 'table_row': 3, 'table_col': 2}],
            'illegal': [{'kind': 'cell', 'table_row': 99, 'table_col': 0}]},
    'Q04': {'correct': -3, 'incorrect': 3,
            'legal': [{'kind': 'cell', 'table_row': 1, 'table_col': 1}, {'kind': 'cell', 'table_row': 2, 'table_col': 1}],
            'illegal': [{'kind': 'cell', 'table_row': 1, 'table_col': 9}]},
}


def main():
    out = HERE / 'candidates'
    if (out / 'candidates_v1.json').exists():
        print('STOP: candidates already exist; no overwrite')
        return 2
    (out / 'inputs').mkdir(parents=True, exist_ok=True)
    inputs = {}
    input_hashes = {}
    for tid in ['Q02', 'Q03', 'Q04']:
        src = load(TQ3 / 'dev_panel' / 'inputs_perturbed' / (tid + '.json'))
        rel = 'inputs/' + tid + '.json'
        write_json(out / rel, src)
        inputs[tid] = src
        input_hashes[rel] = sha_file(out / rel)
    order = [(1, 'correct', 'legal'), (2, 'correct', 'illegal'), (3, 'incorrect', 'legal'), (4, 'incorrect', 'illegal')]
    cands = []
    verifications = []
    for tid in ['Q02', 'Q03', 'Q04']:
        spec = TASK_SPECS[tid]
        inp = inputs[tid]
        for n, ak, lk in order:
            cid = tid + '-C' + str(n)
            c = {'candidate_id': cid, 'task_id': tid, 'variant': 'perturbed',
                 'label': {'answer_kind': ak, 'evidence_legality': lk},
                 'answer': spec[ak], 'evidence': spec[lk],
                 'construction': {'answer_rule': 'frozen spec v1; see CANDIDATE_BUILD_SPEC_v1.md',
                                  'evidence_rule': 'frozen spec v1; see CANDIDATE_BUILD_SPEC_v1.md'},
                 'frozen_design_target': {'support_target': 'accept' if ak == 'correct' else 'alarm',
                                          'notes': 'targets are semantic hypotheses; citation legality is visible to B only'}}
            leg = V2.check_evidence_legality(inp['table'], inp['paragraphs'], c['evidence'])
            expect_legal = lk == 'legal'
            verifications.append({'candidate_id': cid, 'legality': leg, 'expected_legal': expect_legal, 'ok': leg['legal'] == expect_legal})
            cands.append(c)
    ok_all = all(v['ok'] for v in verifications)
    log = {'schema': 'tq4_candidates_log_v1',
           'frozen_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
           'spec': 'CANDIDATE_BUILD_SPEC_v1.md',
           'freeze_note': 'No TQ-4 model outputs exist at freeze time; candidates are manual constructions.',
           'input_hashes': input_hashes, 'legality_verifications': verifications,
           'candidate_count': len(cands), 'all_verifications_ok': ok_all}
    write_json(out / 'candidates_v1.json', {'schema': 'tq4_candidates_v1', 'order': 'C1..C4 = (correct,legal),(correct,illegal),(incorrect,legal),(incorrect,illegal)', 'candidates': cands})
    log['candidates_file_sha256'] = sha_file(out / 'candidates_v1.json')
    write_json(out / 'CANDIDATES_LOG.json', log)
    print(json.dumps({'candidates': len(cands), 'all_verifications_ok': ok_all, 'legality': [(v['candidate_id'], v['legality']['legal']) for v in verifications]}, ensure_ascii=True))
    return 0 if ok_all else 4


if __name__ == '__main__':
    raise SystemExit(main())
