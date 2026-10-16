"""Validate local annotation packaging, not scientific labels. Read-only except report."""
import csv
import hashlib
import json
from pathlib import Path

B = Path(__file__).resolve().parent
REPO = B.parents[3]

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    checks = []
    def check(name, passed, detail):
        checks.append({'check': name, 'passed': bool(passed), 'detail': detail})
    sources = read(B / 'SOURCE_MANIFEST.json')['sources']
    check('source_bytes_still_pinned', all(sha(B / x['relative_path']) == x['sha256'] for x in sources), {'files': len(sources)})
    lineage = read(B / 'coordinator/case_provenance.json')
    one = {c['case_id']: c for c in read(B / 'packets/stage1_cases.json')}
    two = {c['case_id']: c for c in read(B / 'packets/stage2_cases.json')}
    check('12_unique_cases_and_tables', len(one) == len(two) == len(lineage) == len({x['uid'] for x in lineage}) == 12, {'cases': len(one), 'tables': len({x['uid'] for x in lineage})})
    raw = {n: read(B / 'raw' / n) for n in ['tatqa_dataset_train.json', 'tatqa_dataset_dev.json']}
    src = {r['uid']: r['table'] for r in read(B / 'raw/tatqa_tables.json')}
    inj = {r['uid']: r['table'] for r in read(B / 'raw/injected_tables.json')}
    failed = []
    for p in lineage:
        cid = p['case_id']
        rec = raw[p['raw_file']][p['raw_record_index']]
        q = rec['questions'][p['question_index']]
        ok = (rec['table']['uid'] == p['uid'] and q['uid'] == p['question_uid']
              and rec['table']['table'] == src[p['uid']] == two[cid]['source_table']
              and one[cid]['perturbed_table'] == inj[p['uid']] == two[cid]['perturbed_table']
              and one[cid]['question'] == q['question'] == two[cid]['question']
              and one[cid]['paragraphs'] == rec['paragraphs'] == two[cid]['paragraphs']
              and two[cid]['official_reference'] == {k: q.get(k) for k in two[cid]['official_reference']})
        if not ok:
            failed.append(cid)
    check('exact_question_table_context_reference_lineage', not failed, {'failed_cases': failed})
    allowed_one = {'case_id', 'question', 'perturbed_table', 'paragraphs'}
    allowed_two = allowed_one | {'source_table', 'official_reference'}
    check('stage1_no_reference_or_proxy_fields', all(set(c) == allowed_one for c in one.values()), 'Allowlisted projection; paragraphs retain authentic information, not artificially redacted.')
    check('stage2_no_v4_or_checker_fields', all(set(c) == allowed_two for c in two.values()), 'Only official raw reference added, no inferred label.')
    export_fail = []
    empty_count = 0
    for r in ['R1', 'R2']:
        for stage in [1, 2]:
            d = B / f'exports/{r}_stage{stage}'
            cases = read(d / 'cases.json')
            target = one if stage == 1 else two
            rows = read(d / 'responses.json')
            with (d / 'responses.csv').open(encoding='utf-8-sig', newline='') as f:
                csvrows = list(csv.DictReader(f))
            ok = ({c['case_id']: c for c in cases} == target and len(rows) == len(csvrows) == 12
                  and rows == csvrows and {x['case_id'] for x in rows} == set(target)
                  and all(all(v == '' for k, v in x.items() if k != 'case_id') for x in rows))
            if not ok:
                export_fail.append(str(d.relative_to(B)))
            empty_count += len(rows)
            rendered = (d / 'PACKET.html').read_text(encoding='utf-8')
            if any(f'id="{cid}"' not in rendered for cid in target) or '�' in rendered:
                export_fail.append(str(d.relative_to(B)) + ':render')
    check('four_complete_exports_and_blank_human_forms', not export_fail, {'failures': export_fail, 'blank_stage_rows': empty_count})
    frozen = read(B / 'FROZEN_INPUT_SNAPSHOT.json')
    changed = [x['path'] for x in frozen if not (REPO / x['path']).exists() or sha(REPO / x['path']) != x['sha256']]
    check('old_layer1_and_paper_files_unchanged', not changed, {'files_checked': len(frozen), 'changed': changed})
    roster = read(B / 'coordinator/annotator_roster.json')
    qual = read(B / 'annotations/TASK_GOLD_QUALIFICATION_v1.json')
    check('no_fabricated_humans_or_qualification', all(x['person_id'] is None for x in roster) and qual['qualified'] is None and qual['human_records_received'] == 0 and qual['signature'] is None, 'All human identity, label and signature fields remain unfilled.')
    report = {'status': 'PASS_MATERIAL_PREPARATION_ONLY' if all(c['passed'] for c in checks) else 'FAIL', 'independent_human_review': 'NOT_PERFORMED', 'scientific_gold_validity': 'NOT_ASSESSED', 'checks': checks}
    (B / 'VALIDATION_REPORT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True))
    if report['status'] == 'FAIL':
        raise SystemExit(1)

if __name__ == '__main__':
    main()
