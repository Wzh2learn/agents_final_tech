"""Local material preparation only. No inference, labels, network, or experiment execution.
Python 3.12 stdlib. Refuses to overwrite an existing packet. Not a task-gold evaluator.
"""
import csv
import hashlib
import html
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

B = Path(__file__).resolve().parent
REPO = B.parents[3]
V4 = B.parent.parent / 'v4'

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write_json(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def write_csv(p, fields, rows):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

STOP = set('the a an of in on for and or to from between what which was were is are how much many company companies its as at by with does do has have did value total'.split())

def tokens(x):
    return set(re.findall(r'[a-z]+', x.lower())) - STOP

def question_rank(q, header):
    return (-len(tokens(header) & tokens(q['question'])),
            -(q.get('answer_type') == 'arithmetic'), int(q.get('order', 0)), q['uid'])

def layer(x, table):
    n = sum(isinstance(h, str) and bool(h.strip()) for h in table[0])
    if n == 1:
        return 'S1'
    if x['type'] == 'ocr_similar':
        return 'S2'
    if x['type'] in ('date_variant', 'unit_suffix'):
        return 'S4'
    if x['type'] in ('alias_variant', 'mixed_lang'):
        return 'S3'
    return 'RESERVE'

def table_html(t):
    n = max(map(len, t))
    out = ['<div class="scroll"><table><thead><tr><th>row/col</th>']
    out.extend(f'<th>c{c}</th>' for c in range(n))
    out.append('</tr></thead><tbody>')
    for ri, row in enumerate(t):
        out.append(f'<tr><th>r{ri}</th>')
        out.extend(f'<td>{html.escape(str(c))}</td>' for c in row)
        out.append('</tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)

def render_case(c, stage):
    esc = lambda x: html.escape(str(x))
    z = [f'<section id="{c["case_id"]}"><h2>{c["case_id"]}</h2>',
         f'<p class="question">{esc(c["question"])}</p>', '<h3>扰动条件完整表格</h3>', table_html(c['perturbed_table']),
         '<h3>完整上下文（未删减）</h3>']
    for p in c['paragraphs']:
        z.append(f'<p><b>段落 {esc(p.get("order"))} · {esc(p.get("uid"))}</b><br>{esc(p["text"])}</p>')
    if stage == 2:
        z += ['<h3>原始表格</h3>', table_html(c['source_table']),
              '<h3>官方参考：待人工核验，不是已完成的 gold</h3>',
              '<pre>' + esc(json.dumps(c['official_reference'], ensure_ascii=False, indent=2)) + '</pre>']
    z.append('<p>请在同目录 responses.csv 或 responses.json 中记录；二选一为正式提交，不要同时填写两份。</p></section>')
    return ''.join(z)

def render_packet(cases, stage, person):
    title = f'{person} · Stage {stage} · Paper E 人工资格核验'
    css = 'body{font-family:Arial,"Microsoft YaHei",sans-serif;max-width:1280px;margin:32px auto;padding:0 24px;color:#172238;line-height:1.6}h1,h2,h3{color:#133b66}section{border-top:3px solid #d9e5ef;margin-top:48px;padding-top:20px}table{border-collapse:collapse;font-size:14px}td,th{border:1px solid #ccd5df;padding:7px 10px;vertical-align:top;min-width:75px}th{background:#edf3f8}.scroll{overflow-x:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7fa;padding:16px}.question{font-size:19px;font-weight:bold}nav a{margin-right:16px}@media print{section{break-before:page}.scroll{overflow:visible}body{font-size:11px;margin:0}td,th{padding:3px;min-width:0}}'
    nav = ''.join(f'<a href="#{c["case_id"]}">{c["case_id"]}</a>' for c in cases)
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{css}</style></head><body><h1>{title}</h1><p>先读 ANNOTATOR_GUIDE.md。不要查看另一名标注者的记录。所有案例为已有材料的诊断用途，不是未见确认集。</p><nav>{nav}</nav>' + ''.join(render_case(c, stage) for c in cases) + '</body></html>'

def main():
    if (B / 'packets').exists():
        raise SystemExit('STOP: packets already exist; no overwrite/rebuild of issued annotation material.')
    contract = read(V4 / 'LAYER1_V4_COMPACT_CONTRACT_v3.json')
    sources = []
    for name in ['injection_map', 'source_tables', 'injected_tables']:
        spec = contract['inputs'][name]
        p = B / 'raw' / Path(spec['path']).name
        assert sha(p) == spec['sha256'], ('PIN_MISMATCH', name)
        sources.append({'role': name, 'local_path': str(p), 'relative_path': str(p.relative_to(B)), 'remote_path': '/home/testuser/wzh/projects/agents_final_tech/' + spec['path'], 'sha256': sha(p), 'bytes': p.stat().st_size, 'verified_against': 'frozen v4 contract'})
    expected = {}
    for line in (B / 'raw/FETCH_RECEIPT.sha256').read_text().splitlines():
        digest, name = line.split()
        expected[name] = digest
    raw_index = {}
    for split in ['train', 'dev']:
        name = f'tatqa_dataset_{split}.json'
        p = B / 'raw' / name
        assert sha(p) == expected[name], ('FETCH_PIN_MISMATCH', name)
        sources.append({'role': 'raw_qa_' + split, 'local_path': str(p), 'relative_path': str(p.relative_to(B)), 'remote_path': '/home/testuser/wzh/projects/agents_final_tech/data/research/tatqa_raw_2026/' + name, 'sha256': sha(p), 'bytes': p.stat().st_size, 'verified_against': '2026-10-13 FETCH_RECEIPT.sha256'})
        for ri, rec in enumerate(read(p)):
            uid = rec['table']['uid']
            assert uid not in raw_index, ('DUPLICATE_UID', uid)
            raw_index[uid] = (name, ri, rec)
    src = {x['uid']: x['table'] for x in read(B / 'raw/tatqa_tables.json')}
    inj = {x['uid']: x['table'] for x in read(B / 'raw/injected_tables.json')}
    pool = [{k: r[k] for k in ['injection_id', 'uid', 'col', 'type', 'original', 'injected']} for r in read(V4 / 'V4_RESULTS_v1.json')['case_rows']]
    assert len(pool) == 59
    groups = defaultdict(list)
    for x in pool:
        uid = x['uid']
        assert src[uid] == raw_index[uid][2]['table']['table'], ('RAW_TABLE_MISMATCH', uid)
        assert src[uid][0][x['col']] == x['original']
        assert inj[uid][0][x['col']] == x['injected']
        assert src[uid][1:] == inj[uid][1:], ('NON_HEADER_CHANGE', uid)
        x['stratum'] = layer(x, src[uid])
        groups[x['stratum']].append(x)
    selected, used = [], set()
    for g in ['S1', 'S2', 'S3', 'S4']:
        n = 0
        for x in sorted(groups[g], key=lambda x: hashlib.sha256(x['injection_id'].encode('utf-8')).hexdigest()):
            if x['uid'] in used:
                continue
            selected.append(x)
            used.add(x['uid'])
            n += 1
            if n == 3:
                break
        assert n == 3, ('STRATUM_SHORTFALL', g, n)
    selected.sort(key=lambda x: hashlib.sha256(('case-order-v1|' + x['uid']).encode()).hexdigest())
    c1, c2, provenance = [], [], []
    for n, x in enumerate(selected, 1):
        uid = x['uid']
        filename, ri, rec = raw_index[uid]
        qs = [q for q in rec['questions'] if q.get('answer_from') in ('table', 'table-text')]
        assert qs, ('NO_REAL_TASK', uid)
        q = sorted(qs, key=lambda q: question_rank(q, x['original']))[0]
        qi = rec['questions'].index(q)
        cid = f'Q{n:02d}'
        one = {'case_id': cid, 'question': q['question'], 'perturbed_table': inj[uid], 'paragraphs': rec['paragraphs']}
        ref = {k: q.get(k) for k in ['answer', 'derivation', 'answer_type', 'answer_from', 'scale', 'rel_paragraphs', 'req_comparison']}
        two = dict(one, source_table=src[uid], official_reference=ref)
        c1.append(one)
        c2.append(two)
        changes = [{'row': r, 'col': c, 'source': a, 'perturbed': inj[uid][r][c]} for r, row in enumerate(src[uid]) for c, a in enumerate(row) if a != inj[uid][r][c]]
        provenance.append({'case_id': cid, **x, 'raw_file': filename, 'raw_record_index': ri, 'question_index': qi, 'question_uid': q['uid'], 'question_json_pointer': f'/{ri}/questions/{qi}', 'table_json_pointer': f'/{ri}/table/table', 'paragraphs_json_pointer': f'/{ri}/paragraphs', 'source_document_id': 'UNRESOLVED', 'paragraph_context_sha256': hashlib.sha256(json.dumps(rec['paragraphs'], ensure_ascii=False, sort_keys=True).encode()).hexdigest(), 'all_changed_cells': changes, 'task_relevance': 'HUMAN_TO_ASSESS', 'question_selection_rank': list(question_rank(q, x['original'])), 'reference_evidence_coordinates': 'HUMAN_TO_ANNOTATE'})
    write_json(B / 'coordinator/selection_policy.json', {'strata_order': ['S1', 'S2', 'S3', 'S4'], 'per_stratum': 3, 'case_sort': 'sha256(injection_id UTF8)', 'unique_table': True, 'question_sort': 'negative token overlap; arithmetic first; question order; question uid', 'token_regex': '[a-z]+', 'stop_words': sorted(STOP), 'output_label_access_in_selection': False, 'designer_prior_exposure_to_results': True, 'confirmatory': False})
    write_json(B / 'coordinator/pool_inventory.json', pool)
    write_json(B / 'coordinator/case_provenance.json', provenance)
    write_json(B / 'packets/stage1_cases.json', c1)
    write_json(B / 'packets/stage2_cases.json', c2)
    base = ['case_id', 'annotator_id', 'annotator_kind', 'started_at', 'submitted_at', 'elapsed_minutes', 'prior_exposure', 'notes']
    f1 = base + ['perturbed_answer', 'unit', 'scale', 'period', 'entity', 'derivation', 'evidence_cells', 'evidence_paragraphs', 'answerability', 'uncertainty_reason']
    f2 = base + ['reference_status', 'verified_reference_answer', 'unit', 'scale', 'period', 'entity', 'verified_derivation', 'reference_cells', 'reference_paragraphs', 'reference_issue', 'task_effect', 'perturbed_answerability', 'change_relevance', 'perturbed_evidence_cells', 'perturbed_evidence_paragraphs', 'effect_reason', 'alternative_interpretations', 'tolerance_and_basis', 'stage1_revision_reason']
    guide = (B / 'ANNOTATOR_GUIDE.md').read_text(encoding='utf-8')
    for person in ['R1', 'R2']:
        for stage, cases, fields in [(1, c1, f1), (2, c2, f2)]:
            order = sorted(cases, key=lambda c: hashlib.sha256((person + '|' + c['case_id']).encode()).hexdigest())
            d = B / f'exports/{person}_stage{stage}'
            d.mkdir(parents=True)
            write_json(d / 'cases.json', order)
            (d / 'PACKET.html').write_text(render_packet(order, stage, person), encoding='utf-8')
            (d / 'ANNOTATOR_GUIDE.md').write_text(guide, encoding='utf-8')
            rows = [dict.fromkeys(fields, '') | {'case_id': c['case_id']} for c in order]
            write_csv(d / 'responses.csv', fields, rows)
            write_json(d / 'responses.json', rows)
            (d / 'README.md').write_text(f'# {person} / Stage {stage}\n\n打开 PACKET.html 阅读，先读 ANNOTATOR_GUIDE.md。responses.csv 与 responses.json 二选一，另一份保持空白。本阶段只发放本目录，不分享上级目录。真实身份与时间由本人填写。\n', encoding='utf-8')
    write_json(B / 'coordinator/annotator_roster.json', [{'slot': r, 'role': 'independent_annotator' if r != 'R3' else 'adjudicator', 'person_id': None, 'human_confirmed': None, 'financial_and_bilingual_competence': None, 'prior_exposure': None, 'assigned_at': None, 'status': 'UNASSIGNED'} for r in ['R1', 'R2', 'R3']])
    write_json(B / 'coordinator/seal_log.json', {'status': 'NO_HUMAN_SUBMISSIONS', 'stage1_submissions': [], 'stage2_release_events': [], 'instructions': 'Only record actual files, SHA256 and timestamps; release stage2 after BOTH complete stage1 submissions are sealed.'})
    write_csv(B / 'annotations/adjudication_template.csv', ['case_id', 'r1_effect', 'r2_effect', 'disagreement_dimensions', 'r3_person_id', 'reference_status', 'final_task_effect', 'evidence_cells', 'evidence_paragraphs', 'reason', 'remaining_uncertainty', 'elapsed_minutes', 'submitted_at'], [{'case_id': c['case_id']} for c in c1])
    write_json(B / 'annotations/TASK_GOLD_QUALIFICATION_v1.json', {'status': 'AWAITING_HUMAN_ANNOTATION', 'n_cases': 12, 'human_records_received': 0, 'qualified': None, 'label_counts': None, 'agreement': None, 'u_rate': None, 'human_hours': None, 'scientific_reviewer': None, 'signature': None, 'layer2_authorized': False, 'thesis_feedback_use_authorized': False})
    write_json(B / 'SOURCE_MANIFEST.json', {'created_at': datetime.now(timezone.utc).isoformat(), 'transport': 'read-only SSH/SCP from existing GB10 research files', 'upstream': 'https://github.com/NExTplusplus/TAT-QA', 'upstream_ref_as_recorded': 'master', 'upstream_commit': 'UNRESOLVED', 'upstream_fetch_date_as_recorded': '2026-10-13T05:07:45Z', 'attribution': 'TAT-QA dataset, Fengbin Zhu et al.; dataset CC BY 4.0 per existing project licence record; project-added header perturbations; no endorsement or public release implied', 'sources': sources})
    old_paths = [p for p in (B.parent.parent).rglob('*') if p.is_file() and B not in p.parents]
    old_paths += [p for p in (REPO / 'paper').rglob('*') if p.is_file()]
    write_json(B / 'FROZEN_INPUT_SNAPSHOT.json', [{'path': str(p.relative_to(REPO)), 'sha256': sha(p)} for p in sorted(old_paths)])
    write_json(B / 'PREPARATION_RECEIPT.json', {'status': 'MATERIALS_PREPARED_NOT_HUMAN_VALIDATED', 'runtime': 'Python 3.12.14 local stdlib', 'raw_pin_checks': len(sources), 'pool_rows': len(pool), 'pool_exact_raw_table_joins': 59, 'selected_cases': len(c1), 'selected_unique_tables': len(used), 'selected_strata': dict(Counter(x['stratum'] for x in selected)), 'source_strata': {k: len(v) for k, v in groups.items()}, 'multi_header_selected_tables': sum(len(p['all_changed_cells']) > 1 for p in provenance), 'human_labels_created': 0, 'model_calls': 0, 'judge_calls': 0, 'training_calls': 0, 'production_service_calls': 0, 'network_used': 'SSH/SCP static-file retrieval only', 'scientific_verdict': 'NOT_ASSESSED', 'limitations': ['No human annotation yet', 'Input strata are not semantic labels', 'Existing exposed diagnostic pool', 'Report/document IDs and original upstream commit unresolved', 'No independent external audit of this package']})
    print(json.dumps(read(B / 'PREPARATION_RECEIPT.json'), ensure_ascii=True))

if __name__ == '__main__':
    main()
