"""Mechanical verification/rendering of an explicitly AI-authored diagnostic review.
No label generation, inference requests, human submissions or experiments.
"""
import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

B = Path(__file__).resolve().parent
P = B.parent
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

review = read(B / 'AI_ANNOTATIONS_v1.json')
cases = {x['case_id']: x for x in read(P / 'packets/stage2_cases.json')}
checks = []
def check(name, passed, detail):
    checks.append({'check': name, 'passed': bool(passed), 'detail': detail})

check('explicit_ai_identity', review['actor_kind'] == 'AI' and not review['human'] and not review['blind'] and review['signature'] is None, 'One exposed AI review, not two independent humans.')
check('12_distinct_existing_cases', len(review['cases']) == 12 and {x['case_id'] for x in review['cases']} == set(cases), 'Each original question represented once.')
bad_refs = []
for x in review['cases']:
    case = cases[x['case_id']]
    for f,t in [('source_cells','source_table'),('perturbed_cells','perturbed_table')]:
        for coord in x[f]:
            m = re.fullmatch(r'r(\d+)c(\d+)',coord)
            if not m:
                bad_refs.append([x['case_id'],coord]);continue
            r,c = map(int,m.groups())
            if r >= len(case[t]) or c >= len(case[t][r]):bad_refs.append([x['case_id'],coord])
    for n in x['paragraphs']:
        if n not in [z['order'] for z in case['paragraphs']]:bad_refs.append([x['case_id'],'paragraph',n])
check('all_evidence_coordinates_exist', not bad_refs, bad_refs)
check('reference_uncertainty_not_promoted', all(x['effect']=='UNDETERMINED' for x in review['cases'] if x['reference_status']!='CONFIRMED'), 'Questionable official references remain U.')

# Expected original strings and operands are explicit review assertions, not labels.
specs = {
 'Q01': [('r1c2','$19.83','19.83'),('r2c2','18.80','18.80')],
 'Q03': [('r3c2','15,363','15363'),('r2c2','1,309','1309')],
 'Q04': [('r2c1','135','135'),('r1c1','$138','138')],
 'Q06': [('r2c3','319','319'),('r3c3','11','11')],
 'Q07': [('r6c1','13,846','13846'),('r6c2','13,434','13434')],
 'Q09': [('r5c1','28,128','28128'),('r5c2','25,633','25633')],
 'Q10': [('r2c1','445,000(1)','445000'),('r4c1','945,000','945000')],
 'Q11': [('r1c1','2,493','2493'),('r1c2','2,407','2407')],
 'Q12': [('r5c1','10','10'),('r5c2','4','4')],
}
calc_report=[]
byid={x['case_id']:x for x in review['cases']}
for cid, pairs in specs.items():
    provenance_ok=True
    for coord,string,num in pairs:
        r,c=map(int,re.fullmatch(r'r(\d+)c(\d+)',coord).groups())
        for t in ['source_table','perturbed_table']:
            provenance_ok &= cases[cid][t][r][c]==string
        normalized=string.replace('$','').replace(',','')
        if cid=='Q10' and coord=='r2c1':normalized=normalized.removesuffix('(1)')
        provenance_ok &= Decimal(normalized)==Decimal(num)
    a,b=map(lambda p:Decimal(p[2]),pairs)
    if cid=='Q07':value=(a+b)/2
    elif cid=='Q09':value=(a-b)/b*100
    elif cid=='Q10':value=a/b
    elif cid=='Q11':value=a+b
    else:value=a-b
    claim=byid[cid]['calculation']
    rounded=value.quantize(Decimal(1).scaleb(-claim['digits']),rounding=ROUND_HALF_UP)
    ok=provenance_ok and rounded==Decimal(claim['expected'])
    calc_report.append({'case_id':cid,'operands':pairs,'expression':claim['expression'],'raw_result':str(value),'rounded_result':str(rounded),'expected':claim['expected'],'passed':ok,'semantic_validity':'NOT_CERTIFIED'})
check('nine_numeric_recalculations',all(x['passed'] for x in calc_report),calc_report)
q5=cases['Q05']
date=datetime.strptime(q5['source_table'][12][0],'%d %B %Y')
term=date.replace(year=date.year+10).strftime('%d %B %Y')
check('Q05_date_and_term_text',term=='31 January 2029' and '10 years from the date of grant' in q5['paragraphs'][4]['text'],{'date_plus_10_calendar_years':term,'not_a_semantic_independence_test':True})
q8=cases['Q08']
counts=[int(q8['source_table'][r][5].strip('()').replace(',','')) for r in [1,2,3]]
best=[1,2,3][counts.index(max(counts))]
check('Q08_maximum_cohort_excludes_total',best==3 and q8['source_table'][best][1]=='2 Jul 2017',{'cohort_counts':counts,'max_row':best,'exercise_date':q8['source_table'][best][1],'aggregate_row_excluded':6})
q2=cases['Q02']
check('Q02_direct_definition', 'accounts receivable, inventories, and net property, plant, and equipment' in q2['paragraphs'][1]['text'], 'Explicit paragraph definition exists; no numeric inference.')
old=read(P/'PACKAGE_MANIFEST.json')['files']
changed=[x['path'] for x in old if sha(P/x['path'])!=x['sha256']]
check('original_53_material_files_unchanged',not changed,{'checked':len(old),'changed':changed})
check('human_roster_and_seals_untouched',all(x['person_id'] is None for x in read(P/'coordinator/annotator_roster.json')) and read(P/'coordinator/seal_log.json')['stage1_submissions']==[], 'No human assignments or Stage1 submissions fabricated.')
loop_hash=sha(P/'LOOP_D_RETURN.md')
check('reported_loop_d_return_hash',loop_hash=='a7f33e1a185a6974057a55680fb1e1bf8638ec4819bdaab93abf6c4e4950809f',loop_hash)

report={'status':'PASS_MECHANICAL_CHECKS_ONLY' if all(x['passed'] for x in checks) else 'FAIL','ai_provisional_effect_counts':dict(Counter(x['effect'] for x in review['cases'])),'human_annotations':0,'scientific_gold_validity':'NOT_ESTABLISHED','semantic_audit_independence':'NONE_THIS_IS_AUTHOR_SELF_CHECK','checks':checks}
(B/'MECHANICAL_CHECKS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
fields=['case_id','reference_status','effect','answerability','relevance','source_answer','perturbed_answer','unit','scale','period','entity','source_cells','perturbed_cells','paragraphs','reference_issue','reason','alternative','review_question']
with (B/'AI_ANNOTATIONS_v1.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
    for x in review['cases']:
        writer.writerow({k:json.dumps(x[k],ensure_ascii=False) if isinstance(x[k],list) else x[k] for k in fields})
md=['# 12 题 AI 辅助初标逐例记录\n','日期：2026-10-16。作者 A1 是 AI，已看官方参考和旧材料。以下是开放参考的暂定判断，不是盲态实验或人工 gold。\n','暂定计数：PRESERVED 6 / ALTERED 1 / UNDETERMINED 5；不能外推比例或计算 checker 错误率。\n']
for x in review['cases']:
    md += [f'## {x["case_id"]} — {x["effect"]}\n',f'问题：{cases[x["case_id"]]["question"]}\n',f'原参考核验（AI）：{x["reference_status"]}。{x["source_answer"]}\n',f'扰动条件答案判断：{x["perturbed_answer"]}\n',f'单位/scale：{x["unit"]} / {x["scale"]}；期间：{x["period"]}。\n',f'原表坐标：{", ".join(x["source_cells"])}；扰动坐标：{", ".join(x["perturbed_cells"])}；段落：{x["paragraphs"]}。\n',f'判断依据：{x["reason"]}\n',f'参考缺口：{x["reference_issue"] or "未发现阻断性参考问题；仍属AI判断"}\n',f'竞争解释：{x["alternative"]}\n',f'Loop D 复核重点：{x["review_question"]}\n']
(B/'CASE_REVIEW.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failed':[x for x in checks if not x['passed']],'ai_effect_counts':report['ai_provisional_effect_counts'],'human_annotations':0},ensure_ascii=True))
if report['status']=='FAIL':raise SystemExit(1)
