"""Independent retrospective Monte Carlo sensitivity check of 15 paired tests."""
import itertools,json,math,sys,time
import numpy as np
source=json.load(open(sys.argv[1])); output={'purpose':'post-hoc Monte Carlo sensitivity; no new outcome data','seed':20261029,'iterations_per_pair':200000,'batch':1000,'p_definition':'(1+count(|mean(sign*d)| >= |mean(d)|))/(iterations+1); two-sided','null_assumptions':'sign flips require within-query exchangeability under sharp null, or appropriate symmetry of paired differences; independent queries are assumed for inference; sample size and dependence may limit generalization','datasets':{}}
rng=np.random.default_rng(output['seed']);start=time.time()
for ds,v in source['datasets'].items():
 scores=v['per_query']['scores']; names=list(scores); rows=[]
 for a,b in itertools.combinations(names,2):
  d=np.array(scores[a]['graded_10'],dtype=np.float64)-np.array(scores[b]['graded_10'],dtype=np.float64); target=abs(d.sum()); exceed=0
  for offset in range(0,output['iterations_per_pair'],output['batch']):
   sz=min(output['batch'],output['iterations_per_pair']-offset)
   signs=rng.integers(0,2,size=(sz,len(d)),dtype=np.int8).astype(np.float64)*2-1
   exceed+=int(np.count_nonzero(np.abs(signs@d)>=target-1e-12))
  p=(exceed+1)/(output['iterations_per_pair']+1)
  rows.append({'a':a,'b':b,'difference':float(d.mean()),'exceedances':exceed,'p':p,'mc_standard_error_approx':float(math.sqrt(p*(1-p)/output['iterations_per_pair']))})
 order=sorted(range(len(rows)),key=lambda i:rows[i]['p']); last=0
 for j,idx in enumerate(order):
  last=max(last,min(1.,rows[idx]['p']*(len(rows)-j))); rows[idx]['p_holm']=last
 output['datasets'][ds]={'queries':v['queries'],'pairs':rows};print(ds,flush=True)
output['elapsed_seconds']=time.time()-start
with open(sys.argv[2],'w') as f: json.dump(output,f,indent=2)
