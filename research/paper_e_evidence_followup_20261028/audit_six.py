"""Post-hoc BEIR six-system comparison; existing runs and labels, no generation."""
import json, sys, time, hashlib, itertools, tempfile, subprocess, pathlib
import numpy as np
sys.path.insert(0, '/home/testuser/wzh/beir_audit')
import beir_audit as a
DATA=pathlib.Path('/home/testuser/wzh/beir_audit/clean/data')
DENSE=pathlib.Path('/tmp/papere_conference_short_20261028/dense_probe.json')
TREC='/home/testuser/wzh/beir_audit/trec_eval-main/trec_eval'
OUT=pathlib.Path(sys.argv[1]); t=time.time()
dense=json.loads(DENSE.read_text()); result={'status':'POSTHOC_EXPLORATION','contract':'same test qrels, per-query, ndcg_cut raw grade vs binarized gain, k=10/100; paired sign flip 20000, Holm within 15 per dataset per metric; query resampling 2000','dense_input_sha256':hashlib.sha256(DENSE.read_bytes()).hexdigest(),'datasets':{}}
a.self_test()
for ds in ['scifact','nfcorpus']:
 d=DATA/ds; corpus={x['_id']:x for x in a.read_jsonl(str(d/'corpus.jsonl'))}; rel=a.read_qrels(str(d/'qrels/test.tsv')); qs={x['_id']:x['text'] for x in a.read_jsonl(str(d/'queries.jsonl'))}; rows=dense['datasets'][ds]['rows']; qids=[r['qid'] for r in rows]
 assert len(qids)==len(set(qids)) and set(qids)=={q for q in rel if q in qs and any(v>0 for v in rel[q].values())}
 for f,h in dense['datasets'][ds]['input_sha256'].items(): assert hashlib.sha256((d/f).read_bytes()).hexdigest()==h
 retr={'BM25_09_04':a.BM25(corpus,.9,.4),'BM25_12_075':a.BM25(corpus,1.2,.75),'BM25_05_03':a.BM25(corpus,.5,.3),'BM25_15_06':a.BM25(corpus,1.5,.6),'TFIDF':a.Tfidf(corpus)}
 names=list(retr)+['BGE']; vals={n:{f'{g}_{k}':[] for g in ['graded','binary'] for k in [10,100]} for n in names}; ranks={n:{} for n in names}; tie={n:{'boundary':0,'list_changed':0,'members_changed':0} for n in retr}; bmcheck=0
 for row in rows:
  q=row['qid']; rankings={'BGE':row['dense_top100']}; assert len(rankings['BGE'])==100 and len(set(rankings['BGE']))==100
  for n,model in retr.items():
   scores=model.scores(qs[q]); asc=a.rank(scores,model.ids,'id_asc',100); desc=a.rank(scores,model.ids,'id_desc',100); rankings[n]=asc
   if n=='BM25_12_075':
    assert asc==row['bm25_top100']; bmcheck+=1
   s=np.sort(scores)[::-1]; tie[n]['boundary']+=int(s[9]==s[10]); tie[n]['list_changed']+=int(asc[:10]!=desc[:10]); tie[n]['members_changed']+=int(set(asc[:10])!=set(desc[:10]))
  for n,r in rankings.items():
   assert len(r)==100 and len(set(r))==100 and all(x in corpus for x in r); ranks[n][q]=r
   for g in ['graded','binary']:
    for k in [10,100]: vals[n][f'{g}_{k}'].append(a.ndcg_cut(r,rel[q],k,g=='graded'))
 comparisons={}; means={}
 for metric in ['graded_10','binary_10','graded_100','binary_100']:
  means[metric]={n:float(np.mean(vals[n][metric])) for n in names}; pairs=[]
  for n,m in itertools.combinations(names,2):
   x=np.array(vals[n][metric]); y=np.array(vals[m][metric]); diff,lo,hi=a.paired_ci(x,y); p=a.sign_flip_p(x,y,n=20000); pairs.append({'a':n,'b':m,'diff':diff,'bootstrap_ci':[lo,hi],'p_signflip':p})
  for x,p in zip(pairs,a.holm([x['p_signflip'] for x in pairs])): x['p_holm']=p; x['supported']=p<.05
  comparisons[metric]=pairs
 # Verify full graded run per query against official trec_eval printed precision.
 maxerr=0.; count=0
 with tempfile.TemporaryDirectory() as tmp:
  qrelfile=pathlib.Path(tmp)/'qrels'; qrelfile.write_text(''.join(f'{q} 0 {doc} {grade}\n' for q in qids for doc,grade in rel[q].items()))
  for n in names:
   p=pathlib.Path(tmp)/'run'; p.write_text(''.join(f'{q} Q0 {doc} {i} {101-i} run\n' for q in qids for i,doc in enumerate(ranks[n][q],1)))
   raw=subprocess.check_output([TREC,'-q','-m','ndcg_cut.10,100',str(qrelfile),str(p)],text=True)
   ix={q:i for i,q in enumerate(qids)}
   for line in raw.splitlines():
    measure,q,v=line.split()
    if q=='all': continue
    k=int(measure.rsplit('_',1)[1]); e=abs(float(v)-vals[n][f'graded_{k}'][ix[q]]); maxerr=max(maxerr,e);count+=1
 assert count==len(qids)*len(names)*2 and maxerr<=0.000051
 result['datasets'][ds]={'queries':len(qids),'bm25_exact_top100_matches':bmcheck,'means':means,'comparisons':comparisons,'lexical_ties_counts':tie,'trec_eval_checks':count,'trec_eval_max_print_error':maxerr,'per_query':{'qids':qids,'scores':vals},'rankings':ranks}
 print(ds,'queries',len(qids),'checks',count,'maxerr',maxerr,flush=True)
result['elapsed_seconds']=time.time()-t; OUT.write_text(json.dumps(result,indent=2)); print('done',result['elapsed_seconds'])
