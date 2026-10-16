import json
from pathlib import Path
B = Path('D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/')
OUT = B / 'measurement_contract_v2'
cases = {c['case_id']: c for c in json.loads((B/'packets/stage2_cases.json').read_text(encoding='utf-8'))}
ai = {c['case_id']: c for c in json.loads((B/'ai_assisted_review_v1/AI_ANNOTATIONS_v1.json').read_text(encoding='utf-8'))['cases']}
ld = {c['case_id']: c for c in json.loads((B/'ai_assisted_review_v1/loop_d_review_v1/LOOP_D_CASE_REVIEW.json').read_text(encoding='utf-8'))['cases']}

def req(obj, period, unit, direction, granularity, tolerance):
    return {'object': obj, 'period': period, 'unit_scale': unit, 'direction': direction, 'required_granularity': granularity, 'tolerance': tolerance}

def spec(cid, requirements, expression, expected, precision, evidence, assumptions, status, limitations):
    return {'task_id': cid, 'source': {'question_uid': None, 'table_uid': None, 'source_table_sha256': '3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302', 'perturbed_table_sha256': '827092cf6af2212ae334a9ad5f7b9ea12122d90ff9117353baf79bb1936e4fa9'},
        'question': cases[cid]['question'], 'task_requirements': requirements, 'reference_paths': [evidence],
        'expression': expression, 'expected': expected, 'precision': precision, 'semantic_assumptions': assumptions,
        'evidence_effect_ai': ld[cid]['review_effect'], 'reference_status_ai': ld[cid]['reference_status'], 'status': status,
        'isolation': {'reference_side_only': True, 'public_input_keys': ['task_id','question','perturbed_table','paragraphs']},
        'limitations': limitations}

specs = {}
specs['Q02'] = spec('Q02', req('Total segment assets composition','NOT_APPLICABLE (definition)','NOT_APPLICABLE','span retrieval','paragraph definition','exact span'),
    'span', 'accounts receivable, inventories, and net property, plant, and equipment.', 'exact',
    {'path_id':'P1','description':'paragraph 2 direct definition','where':['paragraph order 2'],'expression':'span','attribution':'SOURCE_EXPLICIT'},
    [{'assumption':'the composition definition in paragraph 2 is the task answer','attribution':'SOURCE_EXPLICIT','note':'paragraph unchanged'}, {'assumption':'changed top header Segment Assets does not affect this definition question','attribution':'AI_INFERENCE','note':'row r7c0 still names Total segment assets'}],
    'REFERENCE_REPLAY_READY', ['P applies only to this composition question, not to all asset values in the table.'])
specs['Q03'] = spec('Q03', req('capital stock value difference','2019-12-31','SEK million','Class B minus Class A','integer million','0 digits'),
    '15363 - 1309', '14054', '0 digits',
    {'path_id':'P1','description':'lower-level unit header and Class A/B rows','where':['r1c2','r2c2','r3c2'],'expression':'15363-1309','attribution':'SOURCE_EXPLICIT'},
    [{'assumption':'difference direction is Class B minus Class A','attribution':'DETERMINISTIC_DERIVATION','note':'official derivation 15,363-1,309'}, {'assumption':'unit is SEK million from unchanged r1c2 header','attribution':'SOURCE_EXPLICIT','note':'lower-level header survives perturbation'}],
    'REFERENCE_REPLAY_READY', ['Top-level capitai stock typo is not used by this question.'])
specs['Q04'] = spec('Q04', req('change in operating lease payments','2021 to 2022','million (paragraph 1)','2022 minus 2021','integer million','0 digits'),
    '135 - 138', '-3', '0 digits',
    {'path_id':'P1','description':'operating lease row and paragraph 1 unit statement','where':['r1c1','r2c1','paragraph order 1'],'expression':'135-138','attribution':'SOURCE_EXPLICIT'},
    [{'assumption':'operat1ng Leases denotes the operating-lease column','attribution':'AI_INFERENCE','note':'Finance Leases column and paragraph 1 provide cross-check'}, {'assumption':'table is in millions per paragraph 1','attribution':'SOURCE_EXPLICIT','note':'explicit parenthetical'}],
    'REFERENCE_REPLAY_READY', ['OCR-like spelling recovery uses context; not a general rule.'])
specs['Q05'] = spec('Q05', req('end date of option term','grant 2019-01-31 + 10 years','calendar date','add 10 calendar years','date','exact date'),
    '2019-01-31 + 10 years', '31 January 2029', 'exact',
    {'path_id':'P1','description':'grant-date row and paragraph 5 term definition','where':['r12c0','paragraph order 5'],'expression':'31 January 2019 + 10 years','attribution':'SOURCE_EXPLICIT'},
    [{'assumption':'term equals 10 years from grant date','attribution':'SOURCE_EXPLICIT','note':'paragraph 5 explicit'}, {'assumption':'4-year vesting is not the term','attribution':'SOURCE_EXPLICIT','note':'paragraph 3 and 5 are separate'}],
    'REFERENCE_REPLAY_READY', ['equity-settled header mutation is not used for this question.'])
specs['Q06'] = spec('Q06', req('difference in purchased intangible assets','fiscal 2019','millions (paragraph 3); perturbed c3 adds 元','Luxtera minus Others','integer million','0 digits'),
    '319 - 11', '308', '0 digits',
    {'path_id':'P1_original_reference_only','description':'original source columns r0c3= Purchased Intangible Assets; r2c3=319; r3c3=11; paragraph 3 gives in millions','where':['r0c3','r2c3','r3c3','paragraph order 3'],'expression':'319-11','attribution':'SOURCE_EXPLICIT'},
    [{'assumption':'c3 denotes Purchased Intangible Assets in the original reference','attribution':'SOURCE_EXPLICIT','note':'true in source table only'}, {'assumption':'c3 identity and unit are recoverable from perturbed table alone','attribution':'UNRESOLVED','note':'c2/c3 become assets labels; 元 conflicts with millions; no paragraph mapping'}],
    'PARTIAL_REFERENCE_REPLAY', ['Original reference replay is computable; perturbed evidence path is blocked. This is a column-identity/unit damage candidate, not an observed system failure and not proof of formal unrecoverability.'])
specs['Q08'] = spec('Q08', req('exercise date of maximum exercised/lapsed cohort','year ended 30 June 2018','calendar date','exclude Total row; argmax absolute exercised/lapsed','cohort row','exact date'),
    'argmax(exercised_or_lapsed excluding Total)', '2 Jul 2017', 'exact',
    {'path_id':'P1','description':'cohort rows r1-r3; exclude Total r6; max 405,000 at r3; r3c1=2 Jul 2017','where':['r1c5','r2c5','r3c5','r3c1','r6c5'],'expression':'argmax','attribution':'SOURCE_EXPLICIT'},
    [{'assumption':'Total row is aggregate and must be excluded','attribution':'DETERMINISTIC_DERIVATION','note':'explicit operation condition'}, {'assumption':'added 2021 qualifier on Exercise date does not affect the necessary dimension','attribution':'UNRESOLVED','note':'no conflict-priority rule in contract'}],
    'PARTIAL_REFERENCE_REPLAY', ['Reference replay ready; perturbed evidence effect remains UNDETERMINED.'])
specs['Q09'] = spec('Q09', req('percentage change in total dividends paid','2018 to 2019','percent','(2019-2018)/2018 x100','two decimals','0.01 percentage point'),
    '(28128 - 25633) / 25633 * 100', '9.73', '2 decimals',
    {'path_id':'P1','description':'dividend total row r5 values and percent operation','where':['r5c1','r5c2'],'expression':'(28128-25633)/25633*100','attribution':'SOURCE_EXPLICIT'},
    [{'assumption':'values are totals for 2019 and 2018','attribution':'SOURCE_EXPLICIT','note':'year columns and row labels'}, {'assumption':'Consoli2021期末d scope qualifier does not affect this question','attribution':'UNRESOLVED','note':'no scope-word priority rule'}],
    'PARTIAL_REFERENCE_REPLAY', ['Reference replay ready; perturbed evidence effect remains UNDETERMINED.'])
specs['Q10'] = spec('Q10', req('proportion of approved-plan securities to total column(a)','2019-12-31','dimensionless ratio','approved divided by total','two decimals','0.01 ratio'),
    '445000 / 945000', '0.47', '2 decimals',
    {'path_id':'P1','description':'column(a) row values; row labels unchanged','where':['r2c1','r4c1'],'expression':'445000/945000','attribution':'SOURCE_EXPLICIT'},
    [{'assumption':'0.47 is a ratio, not a percentage','attribution':'DETERMINISTIC_DERIVATION','note':'no x100 requested'}, {'assumption':'column(c) equty typo is not used by this question','attribution':'SOURCE_EXPLICIT','note':'question uses column(a)'}],
    'REFERENCE_REPLAY_READY', ['P applies only to this column(a) ratio question.'])
specs['Q12'] = spec('Q12', req('change in collaborative technology project receipts revenue','2019 to 2020','million (paragraph 1)','2020 minus 2019','integer million','0 digits'),
    '10 - 4', '6', '0 digits',
    {'path_id':'P1','description':'row r5 left-side values for Jan 31 2020 and Feb 1 2019; right-side unearned is n/a; paragraph 1 gives table in millions','where':['r5c1','r5c2','r5c4','paragraph order 1'],'expression':'10-4','attribution':'SOURCE_EXPLICIT'},
    [{'assumption':'left For the Year columns are revenue/receipts; right As of columns are unearned revenue','attribution':'AI_INFERENCE','note':'row label and n/a structure select left group; this is a recovery/alternative-path case'}],
    'REFERENCE_REPLAY_READY', ['P applies only to this receipts question, not to Reseller revenue or whole-table revenue/unearned distinction.'])

for cid,s in specs.items():
    (OUT/'cases'/(cid+'.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

for cid in specs:
    c=cases[cid]
    pub={'task_id':cid,'question':c['question'],'perturbed_table':c['perturbed_table'],'paragraphs':c['paragraphs']}
    (OUT/'public_inputs'/(cid+'.json')).write_text(json.dumps(pub,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

quarantine={
'Q01':'# Q01 quarantine card\n\n- gap: question says `in 2018`, but Forfeited is in a Dec-31-2018 to Dec-31-2019 rollforward; official reference 19.83-18.80 has no period-alignment argument.\n- checked: source table, perturbed table, paragraphs, official reference.\n- needed evidence: original report definition of forfeiture period or a corrected question; do not rewrite the question here.\n- action: keep original question/reference isolated; do not attribute to perturbation.\n',
'Q07':'# Q07 quarantine card\n\n- gap: question says `2019 average adjusted EBITDA, guidance basis`; official reference averages 2018 and 2019 Guidance basis values (13,846+13,434)/2.\n- checked: table columns, paragraph 1-3, official reference.\n- needed evidence: original definition of `2019 average` or corrected question; do not silently average both years.\n- action: keep original question/reference isolated; perturbation `cashflow` is irrelevant to this question.\n',
'Q11':'# Q11 quarantine card\n\n- gap: no direct table-level/report-level `in millions` statement for the Bell Wireless operating revenues table; official rel_paragraphs=11 discusses capex, not operating revenues.\n- checked: table, paragraphs 1-20, official reference.\n- needed evidence: original report unit statement covering this table; do not infer million from another metric.\n- action: keep original question/reference isolated; `turnover` may preserve operating-revenue semantics but cannot supply the missing scale.\n'}
for cid,t in quarantine.items():
    (OUT/'quarantine'/(cid+'.md')).write_text(t,encoding='utf-8')

contract='''# Task Measurement Contract v2\n\n> Status: DEVELOPMENT_ONLY; AI-authored; not independent gold. Date: 2026-10-16.\n\n## Three separate judgments\n\n- reference_validity: traceable support for question/reference. Record computation replay, semantic mapping, and unit/period gaps separately.\n- evidence_effect: whether perturbed material still supports the fixed task answer requirements. P/A/U remain provisional semantic judgments.\n- system_outcome: future system output. This round is `NOT_RUN`; never derive it from evidence_effect.\n\n## Requirements before evidence paths\n\nEach task fixes question, object, period, unit/scale, operation direction, granularity, and tolerance. NOT_APPLICABLE needs question-based justification; UNRESOLVED cannot be renamed NOT_APPLICABLE. A reference cell set is not automatically the unique necessary evidence. Each evidence path must support all necessary dimensions and is marked SOURCE_EXPLICIT / DETERMINISTIC_DERIVATION / AI_INFERENCE / UNRESOLVED. Paths are non-exhaustive unless proven otherwise.\n\n## Context and units\n\nAllowed context: full paragraphs, lower-level headers, row names, footnotes, explicit table-wide unit statements. Inference from lexical nearest neighbours, financial convention, or AI reasoning is marked AI_INFERENCE and never becomes gold. A report-level unit rule may be used only when its scope is located.\n\n## Extra year/scope words\n\nNo global rule to ignore years or to treat extra words as harmful. First decide whether the word acts on a necessary dimension. If it conflicts and cannot be resolved, keep UNDETERMINED. Q08/Q09 may remain U.\n\n## Q06 proof burden\n\nKeep `COLUMN_IDENTITY_UNIT_DAMAGE_CANDIDATE`. To strengthen to non-recoverable, list competing interpretations and their task meanings and show exclusion evidence. Otherwise preserve the candidate status. Do not claim formal unrecoverability.\n\n## Offline verification boundary\n\nMechanical PASS only means reference operations and permission boundaries are executable. It does not establish task gold, semantic mapping, or system performance. Four negative checks are required: invalid evidence coordinate, changed-copy input hash, unresolved necessary scale, and official-reference leakage in public inputs. All must be rejected or blocked.\n\n## Statuses\n\nREFERENCE_REPLAY_READY / PARTIAL_REFERENCE_REPLAY / MEASUREMENT_SPEC_BLOCKED. `scientific_gold_validity` remains NOT_ESTABLISHED. Layer-2 is not authorized.\n'''
(OUT/'CONTRACT_v2.md').write_text(contract,encoding='utf-8')

delta='''# Claim and Attribution Delta\n\n## Existing consensus\n\n- Q01/Q07/Q11 reference gaps were already recorded by A1; Loop D D2/D3/D5 are repeat confirmations, not new discoveries.\n- Q06 was already an ALTERED evidence-damage candidate; Loop D only narrowed the wording.\n- Q08/Q09 unresolved extra-year/scope words were already recorded.\n\n## Wording clarifications\n\n- whole-table condition is an input scope, not a claim that every cell is damaged.\n- Q06 damage is localized to column identity/unit evidence for c2/c3; Goodwill, Purchase Consideration, rows, and values remain.\n- 12/12 ACCEPT_PROVISIONAL means no label reversal was proposed; it is not independent validation or inter-human agreement.\n\n## Category correction\n\n- Q12 is not strictly perturbation-irrelevant: top headers changed to sales. It is a recovery/alternative evidence path case because row name, For the Year columns, and right-side n/a select the left group.\n- Q02/Q05/Q10 are controls where the task does not depend on the changed header.\n- Q03 relies on an unchanged lower-level unit header; Q04 is context recovery.\n\n## New evidence from Loop D\n\n- A negative recovery search for Q06: no unique text-based recovery path under allowed assumptions; still only a candidate.\n- Explicit separation of recovery/alternative-path cases from irrelevant-header cases.\n- Formal identification of Q08/Q09 conflict-priority gap; no new priority rule created.\n- No label reversals and no new human gold.\n'''
(OUT/'CLAIM_AND_ATTRIBUTION_DELTA.md').write_text(delta,encoding='utf-8')
print('built', len(specs), 'specs')
