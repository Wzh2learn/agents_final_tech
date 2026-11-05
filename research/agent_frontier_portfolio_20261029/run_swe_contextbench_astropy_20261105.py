#!/usr/bin/env python3
"""Bounded Astropy execution with source-only experience and post-run evaluation."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib,json,re,shutil,subprocess,sys,tarfile,time
from pathlib import Path,PurePosixPath
from types import SimpleNamespace
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.graph.research_auto_record import recorded_episode
from scripts.graph.research_tool_runtime import ripgrep_binding,RG_SHA256,OPENCODE
import scripts.graph.research_auto_record as auto_record_module
import scripts.graph.research_evidence_graph as evidence_graph_module
import scripts.graph.research_tool_runtime as tool_runtime_module
import scripts.graph.research_actor_dependencies as actor_dependencies
import qualify_swe_contextbench_astropy_20261105 as qual
import qualify_swe_contextbench_sympy_20261104 as shared
import run_swe_contextbench_sympy_20261104 as core
import run_swe_contextbench_requests_20261105 as requests_runner
import prepare_astropy_evidence_profiles_20261106 as evidence_profiles
from run_swe_contextbench_sphinx_20261105 import inspect_experience_reads

PARENT=qual.ROOT/'astropy_agent_20261105'
QUAL_SHA='e0ed1ac9cb580b36f65a9c90e4f99b418963e72554be92a031be955afa1fd71d'
QUAL_SCRIPT_SHA='02f539e02cdef698f540bb4bac29ea38e2fd469c0441eb9625b0cd697ed8440f'  # original frozen execution bytes
OVERLAY_SHA='08e6caf6ff363d2e3175af60b017b1030f32bf08ed34949ddc909cbf6b9c6300'
MAX_POSTS=24; MAX_SECONDS=900
TARGET_MARKERS=('astropy__astropy-15082','pull/15082','issues/15082','#15082')
ACTOR_PROJECTION=PARENT/'actor_dependencies_v2'
ACTOR_PROJECTION_SHA='32fd788dae461e4eca1f792c9f9e569c70bac9ee7d0befb3335848f98efe1aed'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def actor_protocol():
 actor_dependencies.verify_projection(ACTOR_PROJECTION,ACTOR_PROJECTION_SHA)
 return SimpleNamespace(OUT=qual.OUT,SITE=ACTOR_PROJECTION/'deps/default',LEGACY=ACTOR_PROJECTION/'runtime')

def check_source_projection(root):
 completed=root/f'source__none__seed{core.SEED}.completed.json'
 record=json.loads(completed.read_text())
 if record.get('actor_projection_sha256')!=ACTOR_PROJECTION_SHA:
  raise ValueError('source experience was not produced on the current isolated dependency surface')
 started=root/f'source__none__seed{core.SEED}.started.json'
 harness=root/f'source__none__seed{core.SEED}.harness.py'
 if sha(started)!=record['started_sha256'] or sha(harness)!=record['harness_sha256']:
  raise ValueError('source runtime provenance changed')
 start=json.loads(started.read_text())
 if start.get('actor_projection_sha256')!=ACTOR_PROJECTION_SHA or start['harness_sha256']!=sha(harness):
  raise ValueError('source runtime identity mismatch')
 mounts=re.findall(r'type=bind,src=([^,\x27\x22]+),dst=(/deps|/extra)',harness.read_text())
 expected={(str(ACTOR_PROJECTION/'deps/default'),'/deps'),(str(ACTOR_PROJECTION/'runtime'),'/extra')}
 if set(mounts)!=expected or len(mounts)!=len(expected):raise ValueError('source exposed an unexpected dependency surface')

def row_for(task):
 identity,dataset,rev,_=qual.CASES[task]
 cols=['instance_id','base_commit','problem_statement','hints_text','test_patch','FAIL_TO_PASS','PASS_TO_PASS']
 found=[r for r in pq.read_table(qual.DATA/dataset,columns=cols).to_pylist() if r['instance_id']==identity]
 if len(found)!=1 or found[0]['base_commit']!=rev:raise ValueError('task identity mismatch')
 return found[0]

def check_source(task):
 _,_,rev,archive_sha=qual.CASES[task]; archive=qual.OUT/(task+'.tar.gz'); clean=qual.OUT/task/'clean_base'
 if sha(archive)!=archive_sha or not clean.is_dir() or any(p.is_symlink() for p in clean.rglob('*')):raise ValueError('source archive/links changed')
 expected={}
 with tarfile.open(archive,'r:gz') as tf:
  for it in tf:
   p=PurePosixPath(it.name)
   if not p.parts or p.parts[0]!='astropy-'+rev or p.is_absolute() or '..' in p.parts or not (it.isfile() or it.isdir()):raise ValueError('unsafe archive')
   if it.isfile():
    with tf.extractfile(it) as fp:expected[PurePosixPath(*p.parts[1:]).as_posix()]=hashlib.sha256(fp.read()).hexdigest()
 actual={p.relative_to(clean).as_posix():sha(p) for p in clean.rglob('*') if p.is_file()}
 if actual!=expected or (clean/'.git').exists():raise ValueError('clean base changed')

def check_overlay(task):
 manifest=qual.OUT/task/'base_overlay.json'
 if sha(manifest)!=OVERLAY_SHA:raise ValueError('overlay manifest changed')
 items=json.loads(manifest.read_text())
 for rel,digest in items.items():
  p=PurePosixPath(rel)
  if p.is_absolute() or '..' in p.parts or not (rel.endswith('.so') or rel=='_version.py'):raise ValueError('unsafe overlay')
  if sha(qual.SITE/'astropy'/rel)!=digest:raise ValueError('overlay source changed '+rel)
 return items

def verify_qualification_script(frozen,current):
 if sha(frozen)!=QUAL_SCRIPT_SHA:raise ValueError('frozen qualification script changed')
 normalize=lambda p:p.read_bytes().replace(b'\r\n',b'\n')
 if normalize(frozen)!=normalize(current):raise ValueError('versioned qualification script differs beyond line endings')

def preflight(task):
 actor_protocol()
 shared.checked_dataset()
 verify_qualification_script(qual.OUT/'qualify.py',Path(qual.__file__))
 if sha(core.BASE)!=core.BASE_SHA or sha(qual.OUT/'receipt.json')!=QUAL_SHA:raise ValueError('qualification or base harness changed')
 controls=json.loads((qual.OUT/'receipt.json').read_text());c=controls['cases'][task]
 if c['id']!=qual.CASES[task][0] or c['base_commit']!=qual.CASES[task][2]:raise ValueError('control identity changed')
 check_source(task);check_overlay(task)
 for arm in ('base','gold'):
  d=c['arms'][arm]
  if d['focus']['exit']!=(1 if arm=='base' else 0) or d['regression']['exit']!=0 or d['issue_probe']['exit']!=0:raise ValueError('controls not qualified')
  for metric in ('focus','regression','issue_probe'):
   if sha(qual.OUT/task/(arm+'_'+metric+'.log'))!=d[metric]['log_sha256']:raise ValueError('control log changed')
  for metric in ('focus','regression'):
   if '0 failed' in ' '.join(d[metric]['log_tail']):raise ValueError('unexpected failure accounting')
 row=row_for(task)
 text=row['problem_statement'].replace('\r\n','\n').rstrip()+'\n'
 if (qual.OUT/task/'task.txt').read_text()!=text or sha(qual.OUT/task/'task.txt')!=c['task_sha256']:raise ValueError('task mismatch')
 if hashlib.sha256(row['test_patch'].encode()).hexdigest()!=c['arms']['base']['test_patch']['sha256']:raise ValueError('test patch changed')
 for name,col in (('focus','FAIL_TO_PASS'),('regression','PASS_TO_PASS')):
  p=qual.OUT/task/(name+'_nodes.json')
  if sha(p)!=c[name+'_nodes_sha256'] or json.loads(p.read_text())!=json.loads(row[col]):raise ValueError('node list mismatch')
 p=subprocess.run([str(qual.ENV/'bin/python'),'-m','pip','freeze'],capture_output=True,text=True,check=True,timeout=60)
 if hashlib.sha256(p.stdout.encode()).hexdigest()!=controls['dependencies_sha256'] or sha(qual.LEGACY/'bin/python3.10')!=controls['python_sha256']:raise ValueError('environment changed')
 ripgrep_binding()
 return c

def derive(root,task,condition,experience,*,seed=core.SEED,max_posts=MAX_POSTS,max_seconds=MAX_SECONDS,context_limit=32768,output_limit=8192):
 code=requests_runner.derive(root,task,condition,experience,protocol=actor_protocol(),seed=seed)
 base="shutil.copytree(src/'clean_base',work,dirs_exist_ok=True)"
 ov=(base+"\nimport json as _overlay_json\n"
     +f"_manifest=Path({str(qual.OUT/task/'base_overlay.json')!r})\n"
     +f"if hashlib.sha256(_manifest.read_bytes()).hexdigest()!={OVERLAY_SHA!r}:raise ValueError('overlay manifest changed')\n"
     +f"_site=Path({str(qual.SITE/'astropy')!r})\n"
     +"for _rel,_sha in _overlay_json.loads(_manifest.read_text()).items():\n"
     +" _s=_site/_rel;_d=work/'astropy'/_rel\n"
     +" if _d.exists() or hashlib.sha256(_s.read_bytes()).hexdigest()!=_sha:raise ValueError('unsafe or changed overlay')\n"
     +" _d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(_s,_d)\n")
 code=core.replace_once(code,base,ov)
 code=core.replace_once(code,"'--entrypoint','python3'", "'--entrypoint','/extra/bin/python'")
 code=core.replace_once(code,'Use the checked-out repository and local Python dependencies; network access is unavailable.', 'Use the checked-out repository and local Python 3.10 dependencies; network access is unavailable. To run pytest in this isolated environment, use python -m pytest -o addopts= followed by the tests you choose.')
 code=core.replace_once(code,'calls=[]; payload_bytes=[]; sampling=[];', 'calls=[]; payload_bytes=[]; sampling=[]; post_lock=threading.Lock(); post_count=[0];')
 line="  line=first.split(b'\\r\\n',1)[0].rsplit(b' ',1)[0]"
 guard=(line+f"\n  if line.startswith(b'POST'):\n   with post_lock:\n    if post_count[0]>={max_posts}:\n     calls.append('DENIED_POST_LIMIT');self.request.sendall(b'HTTP/1.1 403 Forbidden\\r\\nContent-Length: 0\\r\\nConnection: close\\r\\n\\r\\n');return\n    post_count[0]+=1")
 code=core.replace_once(code,line,guard)
 if max_seconds!=MAX_SECONDS:code=core.replace_once(code,f'timeout={MAX_SECONDS})',f'timeout={max_seconds})')
 code=core.replace_once(code,"{'context':32768,'output':8192}",repr({'context':context_limit,'output':output_limit}) if (context_limit,output_limit)!=(32768,8192) else "{'context':32768,'output':8192}")
 code=core.replace_once(code,'line not in allowed or len(calls)>=24 or ', 'line not in allowed or ')
 binding=ripgrep_binding()
 code=core.replace_once(code, 'cmd[_at:_at]=[', 'cmd[_at:_at]='+repr(binding)+'+[')
 compile(code,'<astropy-agent-harness>','exec')
 return code

def evaluate(task,case):
 work=case/'work'
 if any(p.is_symlink() for p in work.rglob('*')):return {'status':'UNRESOLVED_SYMLINK'}
 out=case/'post_run_evaluation_restored_tests';out.mkdir();copy=out/'candidate'
 shutil.copytree(work,copy,ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache','instructions.txt','opencode.json','source_experience.md'))
 clean=qual.OUT/task/'clean_base'
 testdir=Path('astropy/nddata/mixins/tests')
 if (copy/testdir).is_symlink():raise ValueError('unsafe test path')
 if (copy/testdir).exists():shutil.rmtree(copy/testdir)
 shutil.copytree(clean/testdir,copy/testdir)
 restored=[]
 for rel in ('conftest.py','astropy/conftest.py','astropy/nddata/conftest.py','astropy/nddata/mixins/conftest.py'):
  original=clean/rel;target=copy/rel
  if target.is_symlink():raise ValueError('unsafe conftest')
  if original.is_file():target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,target);restored.append(rel)
  elif target.exists():target.unlink();restored.append(rel+' (candidate-only removed)')
 patch=qual.patch(copy,row_for(task)['test_patch'],out/'test.patch')
 result={'status':'TEST_PATCH_CONFLICT','test_source':'FROZEN_BASE','restored':restored,'test_patch':patch,'regression_scope':'complete frozen PASS_TO_PASS'}
 if len(patch['steps'])==2 and all(x['exit']==0 for x in patch['steps']):
  result['status']='EVALUATED'
  result['issue_probe']=qual.run(copy,['-c',qual.PROBE,task],out/'issue_probe.log',task+'agentissue')
  for m,col in (('focus','FAIL_TO_PASS'),('regression','PASS_TO_PASS')):
   nodes=json.loads(row_for(task)[col]);result[m]=qual.run(copy,['-c',qual.LAUNCHER,json.dumps(nodes)],out/(m+'.log'),task+'agent'+m);result[m]['nodes_requested']=len(nodes)
 return result

def environment_preflight(root,task):
 actor=actor_protocol()
 tmp=root/('preflight_'+task);tmp.mkdir(parents=True,exist_ok=False);work=tmp/'work'
 shutil.copytree(qual.OUT/task/'clean_base',work)
 overlay=qual.overlay(work)
 expected=check_overlay(task)
 if overlay!=expected:raise ValueError('overlay content differs')
 cmd=['docker','run','--rm','--pull','never','--network','none','--read-only','--cpus','2','--memory','3g','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=128m','--tmpfs','/home/agent:rw,nosuid,size=128m','-e','HOME=/home/agent','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH=/workspace:/deps','-e','PATH=/extra/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin','--mount',f'type=bind,src={work},dst=/workspace,readonly','--mount',f'type=bind,src={actor.LEGACY},dst=/extra,readonly','--mount',f'type=bind,src={actor.SITE},dst=/deps,readonly',*ripgrep_binding(),'--workdir','/workspace','--entrypoint','/extra/bin/python',qual.IMAGE,'-c','import astropy,numpy; from astropy.nddata import NDDataArray; from pathlib import Path; assert not (Path("/deps")/"astropy").exists(); assert not (Path("/extra/lib/python3.10/site-packages")).exists(); print(astropy.__version__,numpy.__version__,NDDataArray.__module__)']
 p=subprocess.run(cmd,capture_output=True,timeout=90);(tmp/'python.stdout').write_bytes(p.stdout);(tmp/'python.stderr').write_bytes(p.stderr)
 if p.returncode:raise ValueError('python import preflight failed')
 cmd=['docker','run','--rm','--pull','never','--network','none','--read-only','--cpus','1','--memory','1g','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=128m','--tmpfs','/home/agent:rw,nosuid,size=128m','-e','HOME=/home/agent','-e','OPENCODE_DISABLE_MODELS_FETCH=1','--mount',f'type=bind,src={work},dst=/root,readonly','--mount',f'type=bind,src={OPENCODE},dst=/opt/opencode,readonly',*ripgrep_binding(),'--workdir','/root','--entrypoint','/opt/opencode',qual.IMAGE,'debug','rg','search','_arithmetic_mask','--pure']
 r=subprocess.run(cmd,capture_output=True,timeout=90);(tmp/'rg.stdout').write_bytes(r.stdout);(tmp/'rg.stderr').write_bytes(r.stderr)
 if r.returncode or not r.stdout:raise ValueError('opencode rg preflight failed')
 return {'python_stdout_sha256':sha(tmp/'python.stdout'),'python_stderr_sha256':sha(tmp/'python.stderr'),'rg_stdout_sha256':sha(tmp/'rg.stdout'),'rg_stderr_sha256':sha(tmp/'rg.stderr'),'overlay_sha256':OVERLAY_SHA,'ripgrep_sha256':RG_SHA256}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt-id',required=True)
 parser.add_argument('--seed',type=int,default=core.SEED);parser.add_argument('--source-attempt-id');parser.add_argument('--inputs-dir',type=Path);parser.add_argument('--input-label',default='original_source_inputs')
 parser.add_argument('--max-posts',type=int,default=MAX_POSTS);parser.add_argument('--max-seconds',type=int,default=MAX_SECONDS)
 parser.add_argument('--context-limit',type=int,default=32768);parser.add_argument('--output-limit',type=int,default=8192)
 action=parser.add_mutually_exclusive_group(required=True);action.add_argument('--task',choices=('source','target'));action.add_argument('--build-experience',action='store_true');action.add_argument('--generate-skill',action='store_true')
 parser.add_argument('--condition',choices=('none','source_history','generated_skill','feedback_card'),default='none');parser.add_argument('--experience',type=Path);parser.add_argument('--experience-sha256');parser.add_argument('--preflight-only',action='store_true')
 args=parser.parse_args()
 if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}',args.attempt_id):parser.error('invalid attempt id')
 if not 0<=args.seed<2**31:parser.error('invalid seed')
 if args.max_posts<1 or args.max_seconds<1:parser.error('execution limits must be positive')
 if not 4096<=args.context_limit<=65536 or not 1<=args.output_limit<args.context_limit:parser.error('context/output outside verified backend range')
 if args.source_attempt_id and not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}',args.source_attempt_id):parser.error('invalid source attempt id')
 if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}',args.input_label):parser.error('invalid input label')
 root=PARENT/'attempts'/args.attempt_id
 source_root=PARENT/'attempts'/(args.source_attempt_id or args.attempt_id)
 inputs=args.inputs_dir or source_root/'source_experience'
 if (args.task=='target' and not args.preflight_only) or args.build_experience or args.generate_skill:check_source_projection(source_root)
 if inputs.is_symlink() or not inputs.resolve().is_relative_to((PARENT/'attempts').resolve()):raise ValueError('inputs outside declared private attempts')
 if args.build_experience or args.generate_skill:
  if args.condition!='none' or args.experience or args.experience_sha256 or args.preflight_only or args.seed!=core.SEED or args.source_attempt_id or args.inputs_dir or args.input_label!='original_source_inputs' or (args.max_posts,args.max_seconds,args.context_limit,args.output_limit)!=(MAX_POSTS,MAX_SECONDS,32768,8192):parser.error('incompatible arguments')
  preflight('source')
  if args.build_experience:
   ignored={'astropy/'+x for x in check_overlay('source')}
   requests_runner.build_experience(root,protocol=qual,target_markers=TARGET_MARKERS,ignored_paths=ignored,include_artifact_diff=True)
  else:requests_runner.generate_skill(root)
  return
 if (args.condition=='none')!=(args.experience is None) or ((args.experience is None)!=(args.experience_sha256 is None)):parser.error('experience and hash required together')
 if args.task=='source' and args.condition!='none':parser.error('source must have no history')
 if args.task=='source' and (args.seed!=core.SEED or args.source_attempt_id or args.inputs_dir or args.input_label!='original_source_inputs'):parser.error('source seed is fixed at 7201; source reuse/profile options are target-only')
 if args.experience and (args.experience.is_symlink() or sha(args.experience)!=args.experience_sha256):raise ValueError('experience changed')
 control=preflight(args.task);code=derive(root,args.task,args.condition,args.experience,seed=args.seed,max_posts=args.max_posts,max_seconds=args.max_seconds,context_limit=args.context_limit,output_limit=args.output_limit)
 if args.preflight_only:
  root.mkdir(parents=True,exist_ok=True);harness=root/('preflight_'+args.task+'.harness.py');report=root/('preflight_'+args.task+'.json')
  if any(p.exists() for p in (harness,report,root/('preflight_'+args.task))):raise FileExistsError('preflight already attempted; preserve it and use a new attempt id')
  with harness.open('x',encoding='utf8') as f:f.write(code)
  env=environment_preflight(root,args.task)
  result={'status':'PREFLIGHT_PASS_NO_MODEL','task':args.task,'attempt_id':args.attempt_id,'runner_sha256':sha(Path(__file__)),'qualification_sha256':QUAL_SHA,'harness_sha256':sha(harness),'actor_projection_sha256':ACTOR_PROJECTION_SHA,'environment':env,'model_calls':0}
  with report.open('x',encoding='utf8') as f:f.write(json.dumps(result,indent=2)+'\n')
  print(json.dumps(result));return
 target_freeze=None
 if args.task=='target':
  d=inputs;freeze=d/'target_input_freeze.json';files=('source_history.md','feedback_card.md','generated_skill.md')
  profile_manifest=d/'input_profile_manifest.json'
  profile_sha=evidence_profiles.validate_profile(d,source_root)
  if not freeze.exists():
   ledger=json.loads((d/'skill_generation_ledger.json').read_text())
   if ledger['status']!='RECEIVED' or ledger['finish_reason']!='stop':raise ValueError('ordinary skill incomplete')
   if ledger.get('source_history_sha256')!=sha(source_root/'source_experience/source_history.md') or ledger.get('skill_sha256')!=sha(d/'generated_skill.md'):raise ValueError('ordinary skill generation provenance changed')
   record={'source_completion_sha256':sha(source_root/f'source__none__seed{core.SEED}.completed.json'),'skill_generation_ledger_sha256':sha(d/'skill_generation_ledger.json'),'artifacts':{n:sha(d/n) for n in files},'scope':'source-only inputs frozen before first target run; researchers have seen references'}
   if profile_sha:record.update({'input_profile_manifest_sha256':profile_sha,'source_attempt_id':source_root.name,'input_label':args.input_label})
   with freeze.open('x') as f:json.dump(record,f,indent=2)
  record=json.loads(freeze.read_text())
  if record.get('input_profile_manifest_sha256')!=profile_sha:raise ValueError('input profile manifest changed')
  if profile_sha and (record.get('source_attempt_id')!=source_root.name or record.get('input_label')!=args.input_label):raise ValueError('input profile identity changed')
  if record['source_completion_sha256']!=sha(source_root/f'source__none__seed{core.SEED}.completed.json') or record['skill_generation_ledger_sha256']!=sha(d/'skill_generation_ledger.json') or any(sha(d/n)!=v for n,v in record['artifacts'].items()):raise ValueError('source freeze changed')
  if args.experience and (args.experience.resolve().parent!=d.resolve() or record['artifacts'].get(args.experience.name)!=args.experience_sha256 or args.experience.name!={'source_history':'source_history.md','feedback_card':'feedback_card.md','generated_skill':'generated_skill.md'}[args.condition]):raise ValueError('experience outside source freeze')
  target_freeze=sha(freeze)
 (root/'runtime').mkdir(parents=True,exist_ok=True)
 @recorded_episode(root,args.seed)
 def run(task,condition):
  eid=f'{task}__{condition}__seed{args.seed}';case=root/eid;harness=root/(eid+'.harness.py');snapshot=root/(eid+'.outer_runner.py')
  if any(p.exists() for p in (case,harness,snapshot,root/(eid+'.started.json'),root/(eid+'.completed.json'))):raise FileExistsError('episode already started')
  with harness.open('x',encoding='utf8') as f:f.write(code)
  with snapshot.open('xb') as f:f.write(Path(__file__).read_bytes())
  components={'core':Path(core.__file__),'requests_runner':Path(requests_runner.__file__),'qualification':Path(qual.__file__),'auto_record':Path(auto_record_module.__file__),'evidence_graph':Path(evidence_graph_module.__file__),'tool_runtime':Path(tool_runtime_module.__file__),'evidence_profiles':Path(evidence_profiles.__file__),'actor_dependencies':Path(actor_dependencies.__file__)}
  component_hashes={name:sha(path) for name,path in components.items()}
  plan={'actor_projection_sha256':ACTOR_PROJECTION_SHA,'component_sha256':component_hashes,'status':'STARTED','task':task,'condition':condition,'attempt_id':args.attempt_id,'seed':args.seed,'temperature':core.TEMPERATURE,'source_attempt_id':source_root.name,'source_reused':source_root!=root,'input_label':args.input_label,'input_profile_manifest_sha256':profile_sha if task=='target' else None,'max_posts':args.max_posts,'proxy_max_bytes':core.MAX_BYTES,'max_seconds':args.max_seconds,'context_limit':args.context_limit,'output_limit':args.output_limit,'task_identity':control['id'],'base_commit':control['base_commit'],'harness_sha256':sha(harness),'outer_runner_snapshot_sha256':sha(snapshot),'runner_sha256':sha(Path(__file__)),'qualification_sha256':QUAL_SHA,'overlay_sha256':OVERLAY_SHA,'ripgrep_sha256':RG_SHA256,'task_text_sha256':control['task_sha256'],'experience_sha256':args.experience_sha256,'target_input_freeze_sha256':target_freeze,'candidate_reference_hidden':True,'attempt_policy':'explicit isolated output; no automatic retry'}
  start=root/(eid+'.started.json');start.write_text(json.dumps(plan,indent=2)+'\n')
  proc=subprocess.run([sys.executable,str(harness),task,'no_skill'],stdin=subprocess.DEVNULL,capture_output=True,timeout=args.max_seconds+120)
  (root/(eid+'.runner.stdout')).write_bytes(proc.stdout);(root/(eid+'.runner.stderr')).write_bytes(proc.stderr)
  plan.update({'runner_exit':proc.returncode,'started_sha256':sha(start)})
  actor_protocol()
  if sha(snapshot)!=plan['outer_runner_snapshot_sha256'] or any(sha(path)!=component_hashes[name] for name,path in components.items()):raise ValueError('outer snapshot or component changed')
  if proc.returncode==0 and (case/'receipt.json').is_file():
   r=json.loads((case/'receipt.json').read_text());raw=case/'raw.jsonl'
   if sha(raw)!=r['raw_sha256']:raise ValueError('raw changed')
   sample=case/'sampling_metadata.jsonl';metadata=[json.loads(s) for s in sample.read_text().splitlines()] if sample.is_file() else []
   if Counter(json.dumps(x,sort_keys=True) for x in metadata)!=Counter(json.dumps(x,sort_keys=True) for x in r['sampling_metadata']):raise ValueError('sampling mismatch')
   if (case/'frozen_instructions.txt').read_bytes()!=(qual.OUT/task/'task.txt').read_text().strip().encode():raise ValueError('task mismatch')
   if args.experience and sha(args.experience)!=args.experience_sha256:raise ValueError('experience changed during run')
   plan.update({'status':'COMPLETED','agent_exit':r['agent_exit'],'raw_sha256':r['raw_sha256'],'posts':sum(s.startswith('POST ') for s in r['model_http_requests']),'denied':[s for s in r['model_http_requests'] if s.startswith('DENIED')],'reported_tokens':sum(t.get('total',0) for t in r['step_finish_tokens']),'cache_read_included':sum(t.get('cache',{}).get('read',0) for t in r['step_finish_tokens']),'seed_and_temperature_forwarded':bool(metadata) and all(x['seed']==args.seed and x['temperature']==core.TEMPERATURE for x in metadata),'experience_read':inspect_experience_reads(raw,args.experience) if args.experience else None,'post_run_evaluation':evaluate(task,case)})
  else:plan['status']='RUNNER_ERROR_REVIEW_RAW_AND_PROXY_LOG'
  complete=root/(eid+'.completed.json');complete.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({'receipt':str(complete),'sha256':sha(complete),'result':plan}))
 run(args.task,args.condition)
if __name__=='__main__':main()
