#!/usr/bin/env python3
"""Qualify SWE-ContextBench requests pairs. Private references must stay outside Git."""
from __future__ import annotations
import hashlib, json, shutil, subprocess, tarfile, time
from pathlib import Path, PurePosixPath
import pyarrow.parquet as pq

ROOT=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
DATA=ROOT/'swe_contextbench_data_20261104'
OUT=ROOT/'requests_qualification_20261105_v3'
ENV=ROOT/'requests_qualification_20261105'/'env'
LEGACY=Path('/home/testuser/miniconda3/envs/haiguan')
SITE=ENV/'lib/python3.8/site-packages'
IMAGE='sha256:648a1999badfe683239ec49e05b2a508e37f762213478122c58fa713f6c00f58'
MANIFEST='bfa76e90221cc82e2c33d24588ff3060756c57679d687f68b29e9e662d68b10c'
CASES={
 'source':('psf__requests-3362','SWEContextBench_Lite_Experience.parquet','36453b95b13079296776d11b09cab2567ea3e703','156642dda5466fb67948b5ef0d2fe85c3387a09a7653e18ee99b2e000a0a74b2'),
 'target':('psf__requests-3481','SWEContextBench_Related_Lite.parquet','b2f6173a3833153f57d9e3baa6728c5cc46c0b29','56a80321dcf9d379698c294c897e2f186418824759924e8b5b187f304b70aedb')}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def extract(archive, base, rev):
    base.mkdir(parents=True)
    with tarfile.open(archive, 'r:gz') as tf:
        for item in tf:
            p=PurePosixPath(item.name)
            if not p.parts or p.parts[0]!='requests-'+rev or p.is_absolute() or '..' in p.parts or not (item.isfile() or item.isdir()):
                raise ValueError('unsafe archive entry '+item.name)
            if len(p.parts)==1: continue
            dst=base.joinpath(*p.parts[1:])
            if item.isdir(): dst.mkdir(parents=True,exist_ok=True)
            else:
                dst.parent.mkdir(parents=True,exist_ok=True)
                with tf.extractfile(item) as a, dst.open('wb') as b: shutil.copyfileobj(a,b)

def patch(work, data, path):
    path.write_text(data, encoding='utf8')
    records=[]
    for cmd in (['git','apply','--check',str(path)],['git','apply',str(path)]):
        r=subprocess.run(cmd,cwd=work,capture_output=True,text=True,timeout=30)
        records.append({'exit':r.returncode,'stderr':r.stderr[-2000:]})
        if r.returncode: break
    return {'sha256':sha(path),'steps':records}

LAUNCHER = r"""
import json,sys,pytest
requested=json.loads(sys.argv[1])
renames={
 'tests/test_requests.py::SendRecordingAdapter::test_json_encodes_as_bytes':'tests/test_requests.py::test_json_encodes_as_bytes',
 'tests/test_requests.py::SendRecordingAdapter::test_prepare_requires_a_request_method':'tests/test_requests.py::test_prepare_requires_a_request_method',
 'tests/test_requests.py::SendRecordingAdapter::test_vendor_aliases':'tests/test_requests.py::test_vendor_aliases'}
expected={renames.get(n,n) for n in requested}
class Select:
 def pytest_collection_modifyitems(self, session, config, items):
  found={i.nodeid for i in items}; self.missing=sorted(expected-found)
  chosen=[i for i in items if i.nodeid in expected]; deselected=[i for i in items if i.nodeid not in expected]
  items[:]=chosen
  config.hook.pytest_deselected(items=deselected)
  print('QUALIFICATION_NODES',json.dumps({'requested':len(requested),'unique':len(expected),'selected':len(chosen),'missing':self.missing,'mapping':{k:v for k,v in renames.items() if k in requested}}))
 def pytest_sessionfinish(self,session,exitstatus):
  if self.missing: session.exitstatus=4
sys.exit(pytest.main(['-q','-p','no:cacheprovider','-p','pytest_httpbin.plugin','tests/test_requests.py'],plugins=[Select()]))
"""

def run(work,nodes,path,name):
    if not nodes: return {'status':'NO_TESTS'}
    name='requests-qualification-'+name+'-'+str(int(time.time()))
    cmd=['docker','run','--name',name,'--rm','--pull','never','--network','none','--read-only','--cpus','2','--memory','3g','--pids-limit','256','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=256m','-e','HOME=/tmp','-e','PYTHONPATH=/workspace:/deps','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1','--mount',f'type=bind,src={work},dst=/workspace,readonly','--mount',f'type=bind,src={LEGACY},dst=/opt/legacy,readonly','--mount',f'type=bind,src={SITE},dst=/deps,readonly','--workdir','/workspace','--entrypoint','/opt/legacy/bin/python',IMAGE,'-c',LAUNCHER,json.dumps(nodes)]
    start=time.monotonic()
    try:
        p=subprocess.run(cmd,capture_output=True,timeout=600)
        code,out=p.returncode,p.stdout+p.stderr
    except subprocess.TimeoutExpired as e:
        code,out=124,(e.stdout or b'')+(e.stderr or b'')
        subprocess.run(['docker','kill',name],capture_output=True,timeout=10)
    path.write_bytes(out)
    return {'exit':code,'nodes_requested':len(nodes),'seconds':round(time.monotonic()-start,3),'log_sha256':sha(path),'log_tail':out.decode('utf8',errors='replace').splitlines()[-20:]}

def main():
    if not SITE.is_dir(): raise ValueError('Private isolated Python 3.8 pytest/httpbin environment missing')
    manifest_path=DATA/'manifest.json'
    if sha(manifest_path)!=MANIFEST: raise ValueError('dataset manifest changed')
    for ent in json.loads(manifest_path.read_text())['files']:
        if sha(DATA/ent['name'])!=ent['sha256']: raise ValueError('dataset changed: '+ent['name'])
    package_list=subprocess.run([str(ENV/'bin/python'),'-m','pip','freeze'],capture_output=True,text=True,check=True,timeout=60).stdout
    (OUT/'dependencies.txt').write_text(package_list,encoding='utf8')
    result={'status':'IN_PROGRESS','scientific_model_calls':0,'training':0,'regression_note':'Complete PTP retained; two blackhole timeout tests fail equivalently under network-none and are excluded from the separately reported qualified subset.', 'dataset_manifest':MANIFEST,'script_sha256':sha(Path(__file__)),'dependencies_sha256':sha(OUT/'dependencies.txt'),'interpreter_sha256':sha(LEGACY/'bin/python3.8'),'image':IMAGE,'cases':{}}
    for label,(identity,dataset,rev,archive_sha) in CASES.items():
        archive=OUT/(label+'.tar.gz')
        if sha(archive)!=archive_sha: raise ValueError('archive hash changed')
        cols=['instance_id','base_commit','patch','test_patch','FAIL_TO_PASS','PASS_TO_PASS','problem_statement','hints_text']
        matches=[r for r in pq.read_table(DATA/dataset,columns=cols).to_pylist() if r['instance_id']==identity]
        if len(matches)!=1 or matches[0]['base_commit']!=rev: raise ValueError('identity mismatch')
        row=matches[0]; case=OUT/label; clean=case/'clean_base'
        if case.exists(): raise FileExistsError(str(case))
        extract(archive,clean,rev)
        task=case/'task.txt'
        task.write_text(row['problem_statement'].replace('\r\n','\n').rstrip()+'\n',encoding='utf8')
        hints_hash=hashlib.sha256((row['hints_text'] or '').encode('utf8')).hexdigest()
        excluded=['tests/test_requests.py::TestTimeout::test_connect_timeout','tests/test_requests.py::TestTimeout::test_total_timeout_connect']
        original=json.loads(row['PASS_TO_PASS'])
        if not all(node in original for node in excluded): raise ValueError('timeout exclusions mismatch')
        renames={
          'tests/test_requests.py::SendRecordingAdapter::test_json_encodes_as_bytes':'tests/test_requests.py::test_json_encodes_as_bytes',
          'tests/test_requests.py::SendRecordingAdapter::test_prepare_requires_a_request_method':'tests/test_requests.py::test_prepare_requires_a_request_method',
          'tests/test_requests.py::SendRecordingAdapter::test_vendor_aliases':'tests/test_requests.py::test_vendor_aliases'}
        selected=[renames.get(node,node) for node in original if node not in excluded]
        node_path=case/'qualified_regression_nodes.json'
        node_path.write_text(json.dumps(selected,indent=2)+'\n',encoding='utf8')
        c={'identity':identity,'base':rev,'archive_sha256':archive_sha,'task_sha256':sha(task),'hints_sha256':hints_hash,'task_contract':'problem_statement only; no hints/reference/tests/git','qualified_regression_nodes':{'path':str(node_path),'sha256':sha(node_path),'count':len(selected),'excluded':excluded,'reason':'network-none makes tarpit unreachable, not timed out; fails both base and gold','mapping':{k:v for k,v in renames.items() if k in original}},'arms':{}}
        result['cases'][label]=c
        for arm in ('base','gold'):
            work=case/arm; shutil.copytree(clean,work)
            tp=patch(work,row['test_patch'],case/(arm+'_test.patch')); detail={'test_patch':tp}
            if len(tp['steps'])==2 and all(x['exit']==0 for x in tp['steps']):
                gp=patch(work,row['patch'],case/'gold_reference.patch') if arm=='gold' else None
                if gp: detail['reference_patch']=gp
                if not gp or (len(gp['steps'])==2 and all(x['exit']==0 for x in gp['steps'])):
                    for metric,column in (('focus','FAIL_TO_PASS'),('regression','PASS_TO_PASS')):
                        detail[metric]=run(work,json.loads(row[column]),case/(arm+'_'+metric+'.log'),label+arm+metric)
                        if metric=='regression':
                            detail['qualified_regression']=run(work,selected,case/(arm+'_qualified_regression.log'),label+arm+'subset')
            c['arms'][arm]=detail
            (OUT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
        result['cases'][label]=c
        (OUT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    result['status']='COMPLETED_CONTROLS_NOT_ADJUDICATED'
    (OUT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
