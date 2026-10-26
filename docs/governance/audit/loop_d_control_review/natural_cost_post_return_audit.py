import hashlib,importlib.util,json,math,re,subprocess
from collections import Counter
from pathlib import Path
root=Path('/home/testuser/wzh/projects/agents_final_tech')
base=root/'research/natural_error_evidence_cost_20261026_v1'
path=base/'a_closeout/P2_RECOVERY_RECOMPUTE_FINAL.py'
spec=importlib.util.spec_from_file_location('p2_frozen_audit',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
fixtures=[
 {'id':'numeric_substring_in_wrong_quantity','q':{'question':'What was revenue?','answer_type':'arithmetic','answer':5,'derivation':'5','scale':''},'table':'[["Year","Employees"],["2015","100"]]','paragraph':'Revenue was 5.','expected_source':'paragraph'},
 {'id':'same_literal_wrong_semantic_role','q':{'question':'What was revenue?','answer_type':'arithmetic','answer':5,'derivation':'5','scale':''},'table':'[["Metric","Value"],["employees","5"],["revenue","not reported"]]','paragraph':'Revenue was 5.','expected_source':'paragraph'}]
probes=[]
for fixture in fixtures:
 actual=m.classify_source_requirement(fixture['q'],fixture['table'],fixture['paragraph'])
 probes.append({'id':fixture['id'],'expected_source':fixture['expected_source'],'actual_source':actual['source_requirement'],'classification':actual,'identity':'AUDIT_AUTHORED_COUNTEREXAMPLE_NOT_NATURAL_RESEARCH_RESULT'})
assert all(x['actual_source']=='table' and x['expected_source']=='paragraph' for x in probes)
rawpath=root/'data/research/tatqa_raw_2026/tatqa_dataset_dev.json'
raw=rawpath.read_bytes();data=json.loads(raw)
counts=Counter();boundary_flagged=[]
for rec in data:
 table=m.serialize_table(rec['table'])
 for q in rec['questions']:
  if q['answer_from']!='table-text':continue
  para=' '.join(p['text'] for p in rec['paragraphs'] if str(p['order']) in map(str,q['rel_paragraphs']))
  cl=m.classify_source_requirement(q,table,para);counts[cl['source_requirement']]+=1
  if cl['source_requirement']=='table':
   missed=[]
   for term in m._target_terms(q):
    nt=m.normalize_text(term)
    if re.fullmatch(r'\d+(?:\.\d+)?',nt) and not re.search(r'(?<![\d.])'+re.escape(nt)+r'(?![\d.])',m.normalize_text(table)):
     missed.append(nt)
   if missed:boundary_flagged.append({'uid':q['uid'],'terms_missing_as_numeric_tokens':missed})
frozen=json.loads((base/'a_closeout/P2_RECOVERY_RECOMPUTE_FINAL.json').read_text())
rows=frozen['row_results'];counts_by_frontier={}
for name in m.FRONTIER_ORDER:
 r=[x['deployable_actions']['frontiers'][name] for x in rows]
 counts_by_frontier[name]={'potential':sum(x['semantic_reference_potential_offline'] for x in r),'characters':sum(x['visible_evidence_characters'] for x in r)}
assert dict(counts)=={'both':265,'table':197,'paragraph':44,'unresolved':1}
assert {k:v['potential'] for k,v in counts_by_frontier.items()}=={'table_only':197,'small_topk_3':452,'fixed_top1_neighbor':414,'larger_topk_5':486,'always_expand':506,'transparent_stop_expand':481}
canonical=json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
assert hashlib.sha256(canonical).hexdigest()==frozen['row_results_sha256']
ledger=json.loads((base/'a_closeout/P1_SEMANTIC_LEDGER_FINAL.json').read_text())
p1exec=[str(p.relative_to(base)) for p in base.rglob('*') if p.suffix in ['.py','.sh'] and 'VISIBLE_AXIS_SCOPE_POLICY_V1' in p.read_text(errors='replace')]
result={'schema':'natural_cost_post_return_audit_v1','date':'2026-10-26','baseline_commit':'0af5f5444feff8190ca9bf87cadab98e5f3ebe13','observed_checkout_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip(),'source_sha256':hashlib.sha256(raw).hexdigest(),'source_requirement_recompute':dict(counts),'frozen_rows':len(rows),'frozen_row_hash':frozen['row_results_sha256'],'frontier_arithmetic_recompute':counts_by_frontier,'classifier_counterexamples':probes,'numeric_substring_flags':{'count':len(boundary_flagged),'examples':boundary_flagged[:8],'limit':'lexical sensitivity flags, not independently adjudicated natural semantic errors'},'p1':{'policy_declared':ledger['deployable_policy']['policy_id'],'policy_replay_count':len(ledger['policy_replay']['per_candidate']),'ordinary_original_denominator':ledger['denominators']['ordinary_original_questions'],'delivered_executable_files_containing_policy_id':p1exec,'limit':'No general executable P1 actor or all-24 regression is located in delivered stage artifacts; inline commands or external runners remain unverified.'},'scientific_calls':0,'training_runs':0,'harness_dispatches':0}
print(json.dumps(result,ensure_ascii=False))
