#!/usr/bin/env python3
"""Qualify Astropy SWE-ContextBench with issue reproductions and frozen tests.

Run under GB10 agent_sft Python; all raw source, patches and outputs stay private.
Python sources are from pinned commits; missing native extensions and _version.py
are overlaid from the recorded Astropy 5.3.2 wheel, not built from these commits.
"""
from __future__ import annotations
import hashlib,json,shutil,subprocess,sys,tarfile,time
from pathlib import Path,PurePosixPath
import pyarrow.parquet as pq
ROOT=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
OUT=ROOT/'astropy_qualification_20261105'
DATA=ROOT/'swe_contextbench_data_20261104'
ENV=OUT/'env'; SITE=ENV/'lib/python3.10/site-packages'
LEGACY=Path('/home/testuser/miniconda3/envs/agent_sft')
IMAGE='sha256:648a1999badfe683239ec49e05b2a508e37f762213478122c58fa713f6c00f58'
MANIFEST='bfa76e90221cc82e2c33d24588ff3060756c57679d687f68b29e9e662d68b10c'
CASES={
 'source':('astropy__astropy-14995','SWEContextBench_Lite_Experience.parquet','b16c7d12ccbc7b2d20364b89fb44285bcbfede54','535f337c32d8f446046d577548f9f306d8295bfc25e1ac9575b8bab12e96b22e'),
 'target':('astropy__astropy-15082','SWEContextBench_Related_Lite.parquet','c5e2521db013d9641999be9c79d1d807741bc39a','5723f29ee0c56ee4d0c6eda77ff95053b7cbd0225d55f6db9da27a32c7f741e8')}
TESTFILE='astropy/nddata/mixins/tests/test_ndarithmetic.py'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def extract(archive,base,rev):
 base.mkdir(parents=True)
 with tarfile.open(archive,'r:gz') as tf:
  for it in tf:
   p=PurePosixPath(it.name)
   if not p.parts or p.parts[0]!='astropy-'+rev or p.is_absolute() or '..' in p.parts or not (it.isfile() or it.isdir()):raise ValueError('unsafe archive entry '+it.name)
   if len(p.parts)==1:continue
   d=base.joinpath(*p.parts[1:])
   if it.isdir():d.mkdir(parents=True,exist_ok=True)
   else:
    d.parent.mkdir(parents=True,exist_ok=True)
    with tf.extractfile(it) as a,d.open('wb') as b:shutil.copyfileobj(a,b)

def patch(work,text,path):
 path.write_text(text,encoding='utf8');out=[]
 for cmd in (['git','apply','--check',str(path)],['git','apply',str(path)]):
  p=subprocess.run(cmd,cwd=work,capture_output=True,text=True,timeout=30);out.append({'exit':p.returncode,'stderr':p.stderr[-2000:]})
  if p.returncode:break
 return {'sha256':sha(path),'steps':out}

def overlay(work):
 source=SITE/'astropy'; result={}
 for f in [*source.rglob('*.so'),source/'_version.py']:
  if not f.is_file():raise FileNotFoundError(f)
  rel=f.relative_to(source);d=work/'astropy'/rel
  if d.exists():raise ValueError('overlay would replace source '+str(rel))
  d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d);result[str(rel)]=sha(d)
 return result

LAUNCHER=r"""
import json,sys,pytest
expected=set(json.loads(sys.argv[1]))
class Select:
 def pytest_collection_modifyitems(self,session,config,items):
  seen={i.nodeid for i in items};self.missing=sorted(expected-seen)
  keep=[i for i in items if i.nodeid in expected];dropped=[i for i in items if i.nodeid not in expected]
  items[:]=keep;config.hook.pytest_deselected(items=dropped)
  print('QUALIFICATION_NODES',json.dumps({'requested':len(expected),'selected':len(keep),'missing':self.missing}))
 def pytest_sessionfinish(self,session,exitstatus):
  if self.missing:session.exitstatus=4
sys.exit(pytest.main(['-q','-o','addopts=','-p','no:cacheprovider','astropy/nddata/mixins/tests/test_ndarithmetic.py'],plugins=[Select()]))
"""

PROBE=r"""
import json,sys,traceback,numpy as np,astropy
from astropy.nddata import NDDataArray,NDDataRef
out={'astropy_runtime_version':astropy.__version__,'numpy_version':np.__version__,'cases':{}}
def examine(name,fn,expected_data=None,expected_mask=None,expected_unit=None):
 try:
  result=fn();out['cases'][name]={'exception':None,'data':np.asarray(result.data).tolist(),
    'mask':None if result.mask is None else np.asarray(result.mask).tolist(),
    'unit':None if result.unit is None else str(result.unit),
    'data_matches':None if expected_data is None else bool(np.array_equal(result.data,expected_data)),
    'mask_matches':None if expected_mask is None else bool(np.array_equal(result.mask,expected_mask)),
    'unit_matches':(None if expected_unit is None else str(result.unit)==expected_unit)}
 except Exception as e:out['cases'][name]={'exception':{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}}
if sys.argv[1]=='target':
 data=np.arange(24).reshape(2,3,4); expected=np.sum(data,axis=(0,1))
 examine('issue_no_mask_with_unit',lambda:NDDataArray(data=data,unit='Jy').sum(axis=(0,1)),expected_data=expected,expected_unit='Jy')
 examine('issue_no_mask_no_unit',lambda:NDDataArray(data=data).sum(axis=(0,1)),expected_data=expected)
else:
 array=np.array([[0,1,0],[1,0,1],[0,1,0]]);mask=np.array([[0,1,64],[8,0,1],[2,1,0]])
 nm=NDDataRef(array);m=NDDataRef(array,mask=mask)
 examine('issue_mask_times_constant',lambda:m.multiply(1.,handle_mask=np.bitwise_or),expected_data=array,expected_mask=mask)
 examine('issue_mask_times_nomask',lambda:m.multiply(nm,handle_mask=np.bitwise_or),expected_data=array*array,expected_mask=mask)
 examine('issue_mask_times_mask',lambda:m.multiply(m,handle_mask=np.bitwise_or),expected_data=array*array,expected_mask=mask)
 examine('issue_nomask_times_nomask',lambda:nm.multiply(nm,handle_mask=np.bitwise_or),expected_data=array*array)
print(json.dumps(out))
"""

def run(work,args,path,name):
 name='astropy-qual-'+name+'-'+str(int(time.time()))
 cmd=['docker','run','--name',name,'--rm','--pull','never','--network','none','--read-only','--cpus','2','--memory','4g','--pids-limit','256','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=256m','-e','HOME=/tmp','-e','PYTHONPATH=/workspace:/deps','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1','-e','HYPOTHESIS_STORAGE_DIRECTORY=/tmp/hypothesis','--mount',f'type=bind,src={work},dst=/workspace,readonly','--mount',f'type=bind,src={LEGACY},dst=/opt/legacy,readonly','--mount',f'type=bind,src={SITE},dst=/deps,readonly','--workdir','/workspace','--entrypoint','/opt/legacy/bin/python',IMAGE,*args]
 start=time.monotonic()
 try:p=subprocess.run(cmd,capture_output=True,timeout=600);code,out=p.returncode,p.stdout+p.stderr
 except subprocess.TimeoutExpired as e:
  code,out=124,(e.stdout or b'')+(e.stderr or b'');subprocess.run(['docker','kill',name],capture_output=True,timeout=10)
 path.write_bytes(out)
 return {'exit':code,'seconds':round(time.monotonic()-start,3),'log_sha256':sha(path),'log_tail':out.decode('utf8',errors='replace').splitlines()[-15:]}

def main():
 if not SITE.is_dir():raise ValueError('isolated venv required')
 if sha(DATA/'manifest.json')!=MANIFEST:raise ValueError('dataset manifest changed')
 for ent in json.loads((DATA/'manifest.json').read_text())['files']:
  if sha(DATA/ent['name'])!=ent['sha256']:raise ValueError('dataset file mismatch')
 dependencies=subprocess.run([str(ENV/'bin/python'),'-m','pip','freeze'],capture_output=True,text=True,check=True,timeout=30).stdout
 (OUT/'dependencies.txt').write_text(dependencies,encoding='utf8')
 receipt={'status':'IN_PROGRESS','model_calls':0,'training':0,'dataset_manifest':MANIFEST,'script_sha256':sha(Path(__file__)),'dependencies_sha256':sha(OUT/'dependencies.txt'),'python_sha256':sha(LEGACY/'bin/python3.10'),'image':IMAGE,'overlay_warning':'Native binaries and _version.py from released 5.3.2 wheel, not compiled from pinned git commits; version is wheel overlay metadata. ndarithmetic.py is frozen Python source, never overlaid.','cases':{}}
 for label,(identity,filename,rev,archive_sha) in CASES.items():
  archive=OUT/(label+'.tar.gz')
  if sha(archive)!=archive_sha:raise ValueError('archive hash mismatch')
  cols=['instance_id','base_commit','patch','test_patch','FAIL_TO_PASS','PASS_TO_PASS','problem_statement','hints_text']
  matches=[r for r in pq.read_table(DATA/filename,columns=cols).to_pylist() if r['instance_id']==identity]
  if len(matches)!=1 or matches[0]['base_commit']!=rev:raise ValueError('dataset identity mismatch')
  row=matches[0];case=OUT/label;clean=case/'clean_base';extract(archive,clean,rev)
  (case/'task.txt').write_text(row['problem_statement'].replace('\r\n','\n').rstrip()+'\n',encoding='utf8')
  (case/'focus_nodes.json').write_text(json.dumps(json.loads(row['FAIL_TO_PASS']),indent=2)+'\n')
  (case/'regression_nodes.json').write_text(json.dumps(json.loads(row['PASS_TO_PASS']),indent=2)+'\n')
  c={'id':identity,'base_commit':rev,'archive_sha256':archive_sha,'task_sha256':sha(case/'task.txt'),'hints_sha256':hashlib.sha256((row['hints_text'] or '').encode()).hexdigest(),'focus_nodes_sha256':sha(case/'focus_nodes.json'),'regression_nodes_sha256':sha(case/'regression_nodes.json'),'arms':{}}
  receipt['cases'][label]=c
  for arm in ('base','gold'):
   work=case/arm;shutil.copytree(clean,work);ov=overlay(work);(case/(arm+'_overlay.json')).write_text(json.dumps(ov,indent=2,sort_keys=True)+'\n')
   detail={'overlay_sha256':sha(case/(arm+'_overlay.json')),'source_ndarithmetic_sha256':sha(work/'astropy/nddata/mixins/ndarithmetic.py')};c['arms'][arm]=detail
   tp=patch(work,row['test_patch'],case/(arm+'_test.patch'));detail['test_patch']=tp
   if len(tp['steps'])==2 and all(z['exit']==0 for z in tp['steps']):
    gp=patch(work,row['patch'],case/'gold_reference.patch') if arm=='gold' else None
    if gp:detail['reference_patch']=gp
    if not gp or (len(gp['steps'])==2 and all(z['exit']==0 for z in gp['steps'])):
     detail['issue_probe']=run(work,['-c',PROBE,label],case/(arm+'_issue_probe.log'),label+arm+'i')
     for metric,col in (('focus','FAIL_TO_PASS'),('regression','PASS_TO_PASS')):
      nodes=json.loads(row[col]); detail[metric]=run(work,['-c',LAUNCHER,json.dumps(nodes)],case/(arm+'_'+metric+'.log'),label+arm+metric);detail[metric]['nodes_requested']=len(nodes)
   (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 receipt['status']='COMPLETED_CONTROLS_NOT_ADJUDICATED'
 (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
