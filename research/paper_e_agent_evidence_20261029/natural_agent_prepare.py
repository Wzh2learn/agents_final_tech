#!/usr/bin/env python3
"""Prepare four development tasks from prior public evidence; no model calls."""
import ast,hashlib,json,random,shutil
from pathlib import Path
from qrel_status import load_qrels,status

ROOT=Path('/home/testuser/wzh/research_evidence/paper_e_natural_agent_20261029')
if ROOT.exists(): raise SystemExit('refusing to overwrite previous experiment')
ROOT.mkdir(); src=Path('/home/testuser/wzh/paper_e_research_20261028')
old=src/'research/research_portfolio_v2/pymigbench_external_change_v1/ntripbrowser_qualification_v2'
rankpath=Path('/home/testuser/wzh/research_evidence/paper_e_20261028/six_system_result.json')
data=Path('/home/testuser/wzh/beir_audit/clean/data/scifact')
rank=json.loads(rankpath.read_text())['datasets']['scifact']['rankings']['BM25_12_075']
qs={r['_id']:r for r in map(json.loads,(data/'queries.jsonl').open())}
corp={r['_id']:r for r in map(json.loads,(data/'corpus.jsonl').open())}
qrels=load_qrels(data/'qrels/test.tsv')
ref={}; prompts={}; source=[]

def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare(name):
 p=ROOT/('docker_public_'+name);p.mkdir();return p
def structural_contract(path):
 tree=ast.parse(path.read_text());imports={x.name for n in ast.walk(tree) if isinstance(n,ast.Import) for x in n.names}
 calls={(n.func.value.id,n.func.attr) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name)}
 return 'cchardet' in imports and ('cchardet','detect') in calls and 'chardet' not in imports and ('chardet','detect') not in calls

for name,attempt in [('migration_base','attempt_001_BASE'),('migration_prose','attempt_002_PROSE_CHANGE_FACTS')]:
 inp=old/'raw'/attempt/'candidate/ntripbrowser/ntripbrowser.py'; p=prepare(name);shutil.copyfile(inp,p/'module.py')
 label='VALID' if structural_contract(inp) else 'INVALID'
 ref[name]={'kind':'real_migration_generated_candidate','source':str(inp.relative_to(src)),'source_sha256':h(inp),'oracle':label,'baseline_original_tests':'7/7 pass (historical recorded JUnit)','contract':'direct import/call; no alias generalization'}
 prompts[name]='Read /task/module.py with read tool. Decide if this narrow migration contract is satisfied: import cchardet, call cchardet.detect, and do not import chardet or call chardet.detect. Reply exactly VERDICT: VALID or VERDICT: INVALID.'

eligible=[]
for q,order in rank.items():
 if q not in qrels or q not in qs:continue
 positive=[doc for doc in order if status(qrels,q,doc)=='QRELS_POSITIVE']
 if positive and status(qrels,q,order[0])=='UNJUDGED':eligible.append((q,order[0],positive[0]))
assert len(eligible)>=2
for i,(qid,unknown,positive) in enumerate(eligible[:2]):
 name='scifact_'+str(i+1);p=prepare(name);A,B=(unknown,positive) if i==0 else (positive,unknown)
 for n,doc in [('A',A),('B',B)]:
  o=corp[doc];(p/(n+'.txt')).write_text('TITLE: '+o.get('title','')+'\nTEXT: '+o.get('text','')[:6000]+'\n',encoding='utf8')
 (p/'query.txt').write_text(qs[qid]['text']+'\n',encoding='utf8')
 ref[name]={'kind':'public_beir_qrel_partial','qid':qid,'A':A,'B':B,'positive_doc':positive,'unjudged_doc':unknown,'qrel_status':{'A':status(qrels,qid,A),'B':status(qrels,qid,B)},'bm25_baseline':'A' if A==unknown else 'B','judgment':'unjudged is not necessarily irrelevant','truncation':'maximum 6000 characters per document'}
 prompts[name]='Read /task/query.txt and both /task/A.txt and /task/B.txt using the read tool. Which document is more relevant to the query? Reply exactly CHOICE: A or CHOICE: B. Do not use other tools.'
for name in ref:
 p=ROOT/('docker_public_'+name)
 ref[name]['actor_file_sha256']={x.name:h(x) for x in sorted(p.iterdir())}
ref['_provenance']={'dataset':'BEIR SciFact public test qrels','qrels_sha256':h(data/'qrels/test.tsv'),'corpus_sha256':h(data/'corpus.jsonl'),'queries_sha256':h(data/'queries.jsonl'),'rankings_sha256':h(rankpath),'original_commit':'9161c1943a8623892b174c98cdf686a4a0ce8673','exposure':'existing datasets and cases, no new-family or model-pretraining isolation'}
(ROOT/'reference_hidden.json').write_text(json.dumps(ref,indent=2));(ROOT/'task_prompts.json').write_text(json.dumps(prompts,indent=2))
print(json.dumps({'directory':str(ROOT),'cases':list(prompts),'ref_sha256':h(ROOT/'reference_hidden.json'),'input_case_hashes':{n:ref[n]['actor_file_sha256'] for n in prompts}},indent=2))
