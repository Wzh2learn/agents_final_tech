#!/usr/bin/env python3
"""Private Matplotlib ContextBench agent runner; no model calls in preflight."""
from __future__ import annotations
import argparse, ast, difflib, hashlib, json, os, re, shlex, shutil, stat, subprocess, sys, tarfile
from collections import Counter
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
import pyarrow.parquet as pq
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.graph.research_auto_record import recorded_episode
from scripts.graph.research_tool_runtime import ripgrep_binding, RG_SHA256, OPENCODE
from scripts.graph.research_actor_dependencies import verify_projection
import scripts.graph.research_actor_dependencies as actor_dependencies
import scripts.graph.research_auto_record as auto_record
import scripts.graph.research_evidence_graph as evidence_graph
import scripts.graph.research_tool_runtime as tool_runtime
import qualify_swe_contextbench_matplotlib_20261106 as qual
import qualify_swe_contextbench_sympy_20261104 as shared
import run_swe_contextbench_sympy_20261104 as core
import run_swe_contextbench_requests_20261105 as requests_runner
import run_swe_contextbench_sphinx_20261105 as sphinx_runner
from run_swe_contextbench_sphinx_20261105 import inspect_experience_reads

PARENT=qual.ROOT/'matplotlib_agent_20261106'
ACTOR_DEPS=qual.ROOT/'matplotlib_actor_dependencies_20261106_v2'
ACTOR_DEPS_SHA='e63a69c6c719bdcc56aa8d08b7ba7635de6bafe90f826b51b7eda79cdad0f75b'
QUAL_SHA='b23f6980004b249b60902a6f68f82a561170a7d41209b8eecc4239609d1b9a25'
QUAL_SCRIPT_SHA='b7910caf78f36ca35828a71874c8a76b46fd6d808444cde7c8f9fa3c1ec68ece'
OVERLAYS={'source':'7591391ae24530151c051d1ec4e5c9cc92578d672929b82a3adaec6c54457e2f','target':'2aac128017a6ec3838809d260d270daabe754e7a80e55d475bb39c8f7393142c'}
TARGET_MARKERS=('matplotlib__matplotlib-27361','pull/27361','issues/27361','#27361')
DEFAULT_CONTEXT=65536; DEFAULT_OUTPUT=16384; DEFAULT_POSTS=48; DEFAULT_SECONDS=1500

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def env_for(task):return qual.OUT/'source_env' if task=='source' else qual.ROOT/'matplotlib_qualification_20261106/target_env'
def site_for(task):return env_for(task)/'lib/python3.10/site-packages'
def actor_site_for(task):return ACTOR_DEPS/'deps'/task
def protocol(task):return SimpleNamespace(OUT=qual.OUT,SITE=actor_site_for(task),LEGACY=ACTOR_DEPS/'runtime')

def row_for(task):
 identity,dataset,rev,*_=qual.CASES[task]
 cols=['instance_id','base_commit','problem_statement','test_patch','FAIL_TO_PASS','PASS_TO_PASS']
 rows=[r for r in pq.read_table(qual.DATA/dataset,columns=cols).to_pylist() if r['instance_id']==identity]
 if len(rows)!=1 or rows[0]['base_commit']!=rev:raise ValueError('identity mismatch')
 return rows[0]

def verify_source(task):
 _,_,rev,archive_hash,_,_=qual.CASES[task];archive=qual.OUT/(task+'.tar.gz');clean=qual.OUT/task/'clean_base'
 if sha(archive)!=archive_hash or not clean.is_dir() or any(p.is_symlink() for p in clean.rglob('*')):raise ValueError('archive or source links changed')
 expected={}; materialized={}
 with tarfile.open(archive,'r:gz') as tf:
  for it in tf:
   p=PurePosixPath(it.name)
   if not p.parts or p.parts[0]!='matplotlib-'+rev or p.is_absolute() or '..' in p.parts or not(it.isdir() or it.isfile() or it.issym()):raise ValueError('unsafe archive')
   if it.isdir():continue
   rel=PurePosixPath(*p.parts[1:]).as_posix(); member=it
   if it.issym():
    link=PurePosixPath(it.linkname)
    if len(link.parts)!=1 or link.name in ('.','..'):raise ValueError('unsafe link')
    member=tf.getmember(str(p.parent/link))
    if not member.isfile():raise ValueError('unsafe link target')
   with tf.extractfile(member) as fp:digest=hashlib.sha256(fp.read()).hexdigest()
   expected[rel]=digest
   if it.issym():materialized[rel]={'target':it.linkname,'sha256':digest}
 actual={p.relative_to(clean).as_posix():sha(p) for p in clean.rglob('*') if p.is_file()}
 if actual!=expected or (clean/'.git').exists():raise ValueError('clean base changed')
 if json.loads((qual.OUT/task/'materialized_links.json').read_text())!=materialized:raise ValueError('materialized link manifest changed')

def check_overlay(task):
 path=qual.OUT/task/'base_overlay.json'
 if sha(path)!=OVERLAYS[task]:raise ValueError('overlay manifest changed')
 result=json.loads(path.read_text());site=site_for(task)/'matplotlib'
 for rel,digest in result.items():
  p=PurePosixPath(rel)
  if p.is_absolute() or '..' in p.parts or not (rel.endswith('.so') or rel=='_version.py') or sha(site/rel)!=digest:raise ValueError('overlay changed')
 return result

def preflight(task):
 shared.checked_dataset()
 projection=verify_projection(ACTOR_DEPS,ACTOR_DEPS_SHA)
 if projection['blocked_packages']!=['matplotlib','mpl_toolkits'] or set(projection['sites'])!={'source','target'}:raise ValueError('actor projection policy mismatch')
 frozen=qual.OUT/'qualify.py';current=Path(qual.__file__)
 if sha(frozen)!=QUAL_SCRIPT_SHA or frozen.read_bytes().replace(b'\r\n',b'\n')!=current.read_bytes().replace(b'\r\n',b'\n'):raise ValueError('qualification script mismatch')
 if sha(core.BASE)!=core.BASE_SHA or sha(qual.OUT/'receipt.json')!=QUAL_SHA:raise ValueError('base harness or receipt mismatch')
 receipt=json.loads((qual.OUT/'receipt.json').read_text());c=receipt['cases'][task];spec=qual.CASES[task]
 if c['id']!=spec[0] or c['base_commit']!=spec[2]:raise ValueError('qualification identity mismatch')
 verify_source(task);check_overlay(task)
 wheel=qual.OUT/'wheelhouse'/c['wheel_name']
 if sha(wheel)!=c['wheel_sha256']:raise ValueError('wheel changed')
 deps=subprocess.run([str(env_for(task)/'bin/python'),'-m','pip','freeze'],capture_output=True,text=True,check=True,timeout=60).stdout
 if hashlib.sha256(deps.encode()).hexdigest()!=c['dependency_sha256'] or sha(qual.LEGACY/'bin/python3.10')!=receipt['python_sha256']:raise ValueError('environment changed')
 row=row_for(task);task_file=qual.OUT/task/'task.txt'
 if task_file.read_text()!=row['problem_statement'].replace('\r\n','\n').rstrip()+'\n' or sha(task_file)!=c['task_sha256']:raise ValueError('task mismatch')
 if hashlib.sha256(row['test_patch'].encode()).hexdigest()!=c['arms']['base']['test_patch']['sha256']:raise ValueError('test patch mismatch')
 for name,col in (('focus','FAIL_TO_PASS'),('regression','PASS_TO_PASS')):
  p=qual.OUT/task/(name+'_nodes.json')
  if sha(p)!=c[name+'_nodes_sha256'] or json.loads(p.read_text())!=json.loads(row[col]):raise ValueError('nodes changed')
 for arm in ('base','gold'):
  a=c['arms'][arm]
  if a['focus']['exit']!=(1 if arm=='base' else 0) or a['regression']['exit']!=0:raise ValueError('unqualified tests')
  for metric in ('focus','regression','issue_probe'):
   log=qual.OUT/task/(arm+'_'+metric+'.log')
   if sha(log)!=a[metric]['log_sha256']:raise ValueError('control log changed')
  for metric in ('focus','regression'):
   log=qual.OUT/task/(arm+'_'+metric+'.log')
   rows=[l for l in log.read_text(errors='replace').splitlines() if l.startswith('QUALIFICATION_NODES ')]
   if len(rows)!=1:raise ValueError('missing selection record')
   selected=json.loads(rows[0].split(' ',1)[1]);expected=a[metric]['nodes_requested']
   if selected['requested']!=expected or selected['selected']!=expected or selected['missing'] or selected['ambiguous']:raise ValueError('incomplete test coverage')
  lines=(qual.OUT/task/(arm+'_issue_probe.log')).read_text(errors='replace').splitlines()
  probes=[json.loads(l) for l in lines if l.startswith('{')]
  if len(probes)!=1:raise ValueError('issue probe absent')
  entries=probes[0]['cases']; expected_keys=('issue_get_facecolors_before_draw',) if task=='source' else ('issue_save_pdf','issue_save_png_300dpi')
  for key in expected_keys:
   v=entries[key]
   if arm=='base' and (not v.get('exception') or v['exception']['type']!='AttributeError'):raise ValueError('base issue not reproduced')
   if arm=='gold' and (v.get('exception') or not v.get('finite_rgba_and_shape_stable',v.get('render_semantics_pass'))):raise ValueError('gold issue not resolved')
 ripgrep_binding();return c

def derive(root,task,condition,experience,*,seed,max_posts,max_seconds,context_limit,output_limit):
 code=requests_runner.derive(root,task,condition,experience,protocol=protocol(task),seed=seed)
 base="shutil.copytree(src/'clean_base',work,dirs_exist_ok=True)"
 ov=(base+'\nimport json as _overlay_json\n'+f"_manifest=Path({str(qual.OUT/task/'base_overlay.json')!r})\n"+f"if hashlib.sha256(_manifest.read_bytes()).hexdigest()!={OVERLAYS[task]!r}:raise ValueError('overlay manifest changed')\n"+f"_site=Path({str(site_for(task)/'matplotlib')!r})\n"+"for _rel,_sha in _overlay_json.loads(_manifest.read_text()).items():\n _s=_site/_rel;_d=work/'lib/matplotlib'/_rel\n if _d.exists() or hashlib.sha256(_s.read_bytes()).hexdigest()!=_sha:raise ValueError('unsafe or changed overlay')\n _d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(_s,_d)\n")
 code=core.replace_once(code,base,ov)
 code=core.replace_once(code,"'--entrypoint','python3'","'--entrypoint','/extra/bin/python'")
 code=core.replace_once(code,"'-e','PYTHONPATH=/deps'","'-e','PYTHONPATH=/root/lib:/deps','-e','MPLBACKEND=Agg','-e','MPLCONFIGDIR=/tmp/mpl'")
 code=core.replace_once(code,'Use the checked-out repository and local Python dependencies; network access is unavailable.','Use the checked-out repository and local Python 3.10 dependencies; network access is unavailable. Use MPLBACKEND=Agg for graphics and python -m pytest -o addopts= followed by tests you choose.')
 code=core.replace_once(code,'calls=[]; payload_bytes=[]; sampling=[];','calls=[]; payload_bytes=[]; sampling=[]; post_lock=threading.Lock(); post_count=[0];')
 line="  line=first.split(b'\\r\\n',1)[0].rsplit(b' ',1)[0]"
 guard=line+f"\n  if line.startswith(b'POST'):\n   with post_lock:\n    if post_count[0]>={max_posts}:\n     calls.append('DENIED_POST_LIMIT');self.request.sendall(b'HTTP/1.1 403 Forbidden\\r\\nContent-Length: 0\\r\\nConnection: close\\r\\n\\r\\n');return\n    post_count[0]+=1"
 code=core.replace_once(code,line,guard)
 code=core.replace_once(code,'line not in allowed or len(calls)>=24 or ','line not in allowed or ')
 if max_seconds!=900:code=core.replace_once(code,'timeout=900)',f'timeout={max_seconds})')
 code=core.replace_once(code,"{'context':32768,'output':8192}",repr({'context':context_limit,'output':output_limit}) if (context_limit,output_limit)!=(32768,8192) else "{'context':32768,'output':8192}")
 code=core.replace_once(code,'cmd[_at:_at]=[','cmd[_at:_at]='+repr(ripgrep_binding())+'+[')
 compile(code,'<matplotlib-agent-harness>','exec');return code

def candidate_manifest(work):
 """Fingerprint every candidate file/link without following symlinks."""
 if work.is_symlink() or not work.is_dir():raise ValueError('candidate root is not a regular directory')
 entries={}
 for directory,dirs,files in os.walk(work,topdown=True,followlinks=False):
  dirs.sort();files.sort()
  for name in dirs+files:
   path=Path(directory)/name;rel=path.relative_to(work).as_posix();info=path.lstat()
   if stat.S_ISLNK(info.st_mode):entries[rel]={'type':'symlink','target':os.readlink(path)}
   elif stat.S_ISREG(info.st_mode):entries[rel]={'type':'file','sha256':sha(path),'bytes':info.st_size}
   elif stat.S_ISDIR(info.st_mode):entries[rel]={'type':'directory'}
   else:raise ValueError('unsupported candidate entry '+rel)
 return entries

def inspect_candidate_artifacts(work,clean):
 """Only exclude a newly generated, non-symlink root result_images directory."""
 artifact=work/'result_images';frozen=clean/'result_images'
 eligible=not os.path.lexists(frozen) and not artifact.is_symlink() and artifact.is_dir()
 excluded=[];excluded_files=[];unresolved=[]
 for directory,dirs,files in os.walk(work,topdown=True,followlinks=False):
  dirs.sort();files.sort()
  for name in dirs+files:
   path=Path(directory)/name
   rel=path.relative_to(work).as_posix()
   if path.is_symlink():
    entry={'path':rel,'target':os.readlink(path)}
    if eligible and rel.startswith('result_images/') and path.name.endswith('-expected.png') and entry['target'].startswith('/root/lib/mpl_toolkits/') and '/baseline_images/' in entry['target'] and '..' not in PurePosixPath(entry['target']).parts:excluded.append(entry)
    else:unresolved.append(entry)
   elif eligible and rel.startswith('result_images/') and path.is_file() and path.suffix=='.png':excluded_files.append(rel)
 return {'excluded_root':'result_images' if eligible else None,'excluded_symlinks':excluded,'excluded_files':excluded_files,'unresolved_symlinks':unresolved,'frozen_root_absent':not os.path.lexists(frozen)}

def new_evaluation_dir(case,name):
 if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_-]{0,63}',name):raise ValueError('invalid evaluation directory')
 out=case/name;out.mkdir(exist_ok=False);return out

def evaluate(task,case,*,output_name='post_run_evaluation_restored_tests'):
 work=case/'work';clean=qual.OUT/task/'clean_base';artifacts=inspect_candidate_artifacts(work,clean)
 if artifacts['unresolved_symlinks']:return {'status':'UNRESOLVED_SYMLINK','artifacts':artifacts}
 out=new_evaluation_dir(case,output_name);copy=out/'candidate'
 standard=shutil.ignore_patterns('.git','__pycache__','.pytest_cache','instructions.txt','opencode.json','source_experience.md')
 artifact_paths=set(artifacts['excluded_files'])|{entry['path'] for entry in artifacts['excluded_symlinks']}
 def ignore(directory,names):
  ignored=set(standard(directory,names))
  for name in names:
   if (Path(directory)/name).relative_to(work).as_posix() in artifact_paths:ignored.add(name)
  return ignored
 shutil.copytree(work,copy,ignore=ignore)
 testfile=Path(qual.CASES[task][5]);testdir=testfile.parent
 if (copy/testdir).exists():shutil.rmtree(copy/testdir)
 shutil.copytree(clean/testdir,copy/testdir)
 restored=[]
 for parent in [Path('.'),*list(testdir.parents)[::-1][1:]]+[testdir]:
  rel=parent/'conftest.py';src=clean/rel;dst=copy/rel
  if dst.is_symlink():raise ValueError('unsafe conftest')
  if src.is_file():dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);restored.append(rel.as_posix())
  elif dst.exists():dst.unlink();restored.append(rel.as_posix()+' (candidate-only removed)')
 for name in ('pytest.ini','pyproject.toml','setup.cfg','tox.ini'):
  src=clean/name;dst=copy/name
  if src.is_file():shutil.copyfile(src,dst);restored.append(name)
  elif dst.exists():dst.unlink();restored.append(name+' (candidate-only removed)')
 patch=qual.patch(copy,row_for(task)['test_patch'],out/'test.patch')
 result={'status':'TEST_PATCH_CONFLICT','test_source':'FROZEN_BASE','restored':restored,'test_patch':patch,'artifacts':artifacts,'regression_scope':'complete frozen PASS_TO_PASS with unique exact/prefix/class resolution'}
 if len(patch['steps'])==2 and all(x['exit']==0 for x in patch['steps']):
  result['status']='EVALUATED';result['issue_probe']=qual.run(copy,site_for(task),['-c',qual.PROBE,task],out/'issue_probe.log',task+'agentissue')
  for m,col in (('focus','FAIL_TO_PASS'),('regression','PASS_TO_PASS')):
   nodes=json.loads(row_for(task)[col]);result[m]=qual.run(copy,site_for(task),['-c',qual.LAUNCHER,json.dumps(nodes),qual.CASES[task][5]],out/(m+'.log'),task+'agent'+m);result[m]['nodes_requested']=len(nodes)
 return result

POSTHOC_NAME='post_run_recheck_generated_images_v1'

def source_revision(root,seed,expected_sha=None):
 case=root/f'source__none__seed{seed}';completed=root/f'source__none__seed{seed}.completed.json';raw=case/'raw.jsonl';out=case/POSTHOC_NAME;path=out/'receipt.json'
 if path.is_symlink() or not path.is_file():raise ValueError('missing source revision')
 digest=sha(path)
 if expected_sha is not None and digest!=expected_sha:raise ValueError('source revision hash changed')
 revision=json.loads(path.read_text())
 if (revision.get('scope')!='POSTHOC_GENERATED_IMAGE_ARTIFACT_RECHECK' or revision.get('original_completed_sha256')!=sha(completed) or revision.get('original_raw_sha256')!=sha(raw) or not revision.get('candidate_unchanged') or not revision.get('original_completed_unchanged') or not revision.get('original_raw_unchanged') or revision.get('model_calls')!=0):raise ValueError('source revision provenance mismatch')
 if json.loads(completed.read_text()).get('post_run_evaluation',{}).get('status')!='UNRESOLVED_SYMLINK' or revision.get('result',{}).get('status')!='EVALUATED':raise ValueError('original or revised source status mismatch')
 for metric in ('focus','regression','issue_probe'):
  if sha(out/(metric+'.log'))!=revision['result'][metric]['log_sha256']:raise ValueError('source revision log mismatch')
 before=out/'candidate_manifest_before.json';after=out/'candidate_manifest_after.json'
 if sha(before)!=revision['candidate_manifest_before_sha256'] or sha(after)!=revision['candidate_manifest_after_sha256'] or before.read_bytes()!=after.read_bytes():raise ValueError('source revision manifest mismatch')
 current=json.dumps(candidate_manifest(case/'work'),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf8')+b'\n'
 if hashlib.sha256(current).hexdigest()!=revision['candidate_manifest_after_sha256']:raise ValueError('source candidate changed since recheck')
 return revision,digest

def reevaluate_source(root,seed):
 case=root/f'source__none__seed{seed}';completed=root/f'source__none__seed{seed}.completed.json';raw=case/'raw.jsonl'
 record=json.loads(completed.read_text())
 if record.get('status')!='COMPLETED' or record.get('post_run_evaluation',{}).get('status')!='UNRESOLVED_SYMLINK' or sha(raw)!=record.get('raw_sha256'):raise ValueError('no matching frozen unresolved episode')
 out=case/POSTHOC_NAME
 if os.path.lexists(out):raise FileExistsError('posthoc evaluation already exists')
 original_sha=sha(completed);raw_sha=sha(raw);before=candidate_manifest(case/'work')
 result=evaluate('source',case,output_name=POSTHOC_NAME)
 if not out.is_dir():raise ValueError('candidate has unresolved non-artifact symlinks')
 after=candidate_manifest(case/'work');unchanged=before==after
 before_path=out/'candidate_manifest_before.json';after_path=out/'candidate_manifest_after.json'
 for path,data in ((before_path,before),(after_path,after)):
  with path.open('xb') as f:f.write(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf8')+b'\n')
 revision={'scope':'POSTHOC_GENERATED_IMAGE_ARTIFACT_RECHECK','original_completed_sha256':original_sha,'original_raw_sha256':raw_sha,'candidate_unchanged':unchanged,'candidate_manifest_before_sha256':sha(before_path),'candidate_manifest_after_sha256':sha(after_path),'original_completed_unchanged':sha(completed)==original_sha,'original_raw_unchanged':sha(raw)==raw_sha,'model_calls':0,'result':result}
 path=out/'receipt.json'
 with path.open('x',encoding='utf8') as f:f.write(json.dumps(revision,indent=2)+'\n')
 print(json.dumps({'revision':str(path),'sha256':sha(path),'candidate_unchanged':unchanged,'result':result}))

def source_tree(root,ignored,cache_paths):
 return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*')
         if p.relative_to(root).as_posix() not in cache_paths and not p.is_symlink() and p.is_file()
         and p.relative_to(root).as_posix() not in ignored
         and not any(x in ('.git','__pycache__','.pytest_cache') for x in p.parts)
         and p.name not in ('instructions.txt','opencode.json')}

def source_semantic_detail(root,seed,expected_sha=None):
 case=root/f'source__none__seed{seed}';directory=case/'semantic_detail_v1';receipt=directory/'receipt.json';log=directory/'detail.log'
 if receipt.is_symlink() or not receipt.is_file() or log.is_symlink() or not log.is_file():raise ValueError('semantic detail unavailable')
 digest=sha(receipt)
 if expected_sha is not None and digest!=expected_sha:raise ValueError('semantic detail receipt changed')
 detail=json.loads(receipt.read_text())
 if detail.get('result',{}).get('exit')!=0 or detail['result'].get('log_sha256')!=sha(log):raise ValueError('semantic detail log changed')
 rows=[json.loads(line) for line in log.read_text(errors='replace').splitlines() if line.startswith('{')]
 if len(rows)!=1 or 'issue_get_facecolors_before_draw' not in rows[0]['cases']:raise ValueError('semantic detail malformed')
 return rows[0]['cases']['issue_get_facecolors_before_draw'],digest

def verify_source_actor_projection(root,seed):
 eid=f'source__none__seed{seed}';completed=root/(eid+'.completed.json');started=root/(eid+'.started.json');harness=root/(eid+'.harness.py')
 record=json.loads(completed.read_text());initial=json.loads(started.read_text())
 if (record.get('status')!='COMPLETED' or record.get('actor_projection_sha256')!=ACTOR_DEPS_SHA or initial.get('actor_projection_sha256')!=ACTOR_DEPS_SHA or record.get('started_sha256')!=sha(started) or record.get('harness_sha256')!=sha(harness) or initial.get('harness_sha256')!=sha(harness)):
  raise ValueError('source episode did not use the current verified actor projection')
 text=harness.read_text()
 if f'type=bind,src={ACTOR_DEPS}/deps/source,dst=/deps,readonly' not in text or f'type=bind,src={ACTOR_DEPS}/runtime,dst=/extra,readonly' not in text:
  raise ValueError('source harness actor projection mounts missing')
 return record

def build_experience(root,seed,*,use_revision=False):
 verify_source_actor_projection(root,seed)
 completed=root/f'source__none__seed{seed}.completed.json';record=json.loads(completed.read_text());case=root/f'source__none__seed{seed}';raw=case/'raw.jsonl';feedback=record['post_run_evaluation']
 revision_sha=None;log_dir=case/'post_run_evaluation_restored_tests'
 if use_revision:
  revision,revision_sha=source_revision(root,seed);feedback=revision['result'];log_dir=case/POSTHOC_NAME
 if record['status']!='COMPLETED' or feedback['status']!='EVALUATED' or sha(raw)!=record['raw_sha256']:raise ValueError('incomplete source episode')
 for metric in ('focus','regression','issue_probe'):
  if sha(log_dir/(metric+'.log'))!=feedback[metric]['log_sha256']:raise ValueError('source feedback changed')
 actions=[]
 for line in raw.read_text().splitlines():
  ev=json.loads(line)
  if ev.get('type')!='tool_use':continue
  part=ev['part'];state=part.get('state',{});inp=json.dumps(state.get('input',{}),ensure_ascii=False);out=str(state.get('output',''))
  actions.append({'tool':part.get('tool'),'status':state.get('status'),'input_prefix':inp[:600],'input_chars':len(inp),'input_sha256':hashlib.sha256(inp.encode()).hexdigest(),'output_tail':out[-800:],'output_chars':len(out),'output_sha256':hashlib.sha256(out.encode()).hexdigest()})
 if not actions:raise ValueError('no source actions')
 probe_lines=(log_dir/'issue_probe.log').read_text(errors='replace').splitlines()
 probes=[json.loads(line) for line in probe_lines if line.startswith('{')]
 if len(probes)!=1 or 'issue_get_facecolors_before_draw' not in probes[0]['cases']:raise ValueError('source issue probe missing')
 source_issue=probes[0]['cases']['issue_get_facecolors_before_draw'];semantic_detail_sha=None
 if use_revision:
  source_issue,semantic_detail_sha=source_semantic_detail(root,seed)
  source_issue=dict(source_issue)
 pre_shape=source_issue.get('facecolors_shape');post_shape=source_issue.get('post_draw_facecolors_shape')
 supplementary={'pre_draw_shape':pre_shape,'post_draw_shape':post_shape,'pre_post_cardinality_stable':pre_shape==post_shape if pre_shape is not None and post_shape is not None else None,'scope':'Motivated additional property, not explicitly required by source issue; a singleton color is valid in the collection API. This observation does not settle the full task.'}
 base=qual.OUT/'source/clean_base';work=case/'work';ignored={'lib/matplotlib/'+x for x in check_overlay('source')}
 artifacts=inspect_candidate_artifacts(work,base)
 if artifacts['unresolved_symlinks']:raise ValueError('unresolved source symlinks')
 cache_paths=set(artifacts['excluded_files'])|{entry['path'] for entry in artifacts['excluded_symlinks']}
 cache_manifest={name:entry for name,entry in candidate_manifest(work).items() if name in cache_paths}
 before,after=source_tree(base,ignored,cache_paths),source_tree(work,ignored,cache_paths);changed=sorted(k for k in before.keys()|after.keys() if before.get(k)!=after.get(k));parts=[];omitted=[]
 for name in changed:
  a,b=base/name,work/name
  if Path(name).suffix not in ('.py','.md','.txt') or any(p.is_file() and p.stat().st_size>1000000 for p in (a,b)):omitted.append(name);continue
  left=a.read_text(encoding='utf8',errors='replace').splitlines(True) if a.is_file() else [];right=b.read_text(encoding='utf8',errors='replace').splitlines(True) if b.is_file() else []
  parts.extend(difflib.unified_diff(left,right,fromfile='source-base/'+name,tofile='source-agent/'+name))
 diff=''.join(parts)
 source={'source_task':(qual.OUT/'source/task.txt').read_text(),'source_result':{'seed':seed,'agent_exit':record['agent_exit'],'posts':record['posts'],'request_limit_reached':record['posts']>=record['max_posts'],'focus_exit':feedback['focus']['exit'],'focus_count':feedback['focus']['nodes_requested'],'regression_exit':feedback['regression']['exit'],'regression_count':feedback['regression']['nodes_requested'],'regression_scope':feedback['regression_scope'],'published_no_exception_observed':source_issue.get('exception') is None,'source_issue_observation':source_issue,'supplementary_probe':supplementary,'original_evaluation_status':record['post_run_evaluation']['status'],'posthoc_revision_sha256':revision_sha},'changed_paths':changed}
 digest=json.dumps(source,ensure_ascii=False,indent=2);history=json.dumps({**source,'source_artifact_diff_prefix':diff[:10000],'source_artifact_diff_chars':len(diff),'source_artifact_diff_sha256':hashlib.sha256(diff.encode()).hexdigest(),'source_artifact_diff_omitted_paths':omitted,'source_actions':actions},ensure_ascii=False,indent=2)
 if any(m.casefold() in (history+raw.read_text()).casefold() for m in TARGET_MARKERS):raise ValueError('target literal in source experience')
 out=root/'source_experience';out.mkdir()
 (out/'ignored_generated_cache_manifest.json').write_text(json.dumps(cache_manifest,indent=2,sort_keys=True)+'\n',encoding='utf8')
 (out/'source_history.md').write_text('Source-only clipped history; feedback is stated first.\n'+history+'\n',encoding='utf8');(out/'feedback_card.md').write_text('Transparent source-only result digest; no inferred repair instructions.\n'+digest+'\n',encoding='utf8')
 meta={'source_seed':seed,'source_revision_sha256':revision_sha,'source_semantic_detail_sha256':semantic_detail_sha,'ignored_generated_cache':{'excluded_root':artifacts['excluded_root'],'entries':len(cache_manifest),'symlinks':len(artifacts['excluded_symlinks']),'manifest_sha256':sha(out/'ignored_generated_cache_manifest.json'),'scope':'private source output only; excluded from code-change inventory; candidate and raw retained'},'source_raw_sha256':sha(raw),'source_completion_sha256':sha(completed),'actions':len(actions),'clipped_inputs':sum(a['input_chars']>600 for a in actions),'clipped_outputs':sum(a['output_chars']>800 for a in actions),'artifact_diff':{'cap':10000,'chars':len(diff),'sha256':hashlib.sha256(diff.encode()).hexdigest(),'omitted_paths':omitted},'scope':'source-only; literal screen is not evidence of semantic/pretraining isolation','artifacts':{p.name:sha(p) for p in out.iterdir() if p.is_file()}}
 (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))

def inspect_frozen_actor_canary(work,task):
 path=work/'lib/mpl_toolkits/mplot3d/art3d.py';tree=ast.parse(path.read_text(encoding='utf8'))
 class_name,methods=('Poly3DCollection',('get_facecolor','get_edgecolor')) if task=='source' else ('Patch3D',('get_path',))
 classes=[node for node in tree.body if isinstance(node,ast.ClassDef) and node.name==class_name]
 if len(classes)!=1:raise ValueError('canary class missing')
 for name in methods:
  targets=[node for node in classes[0].body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name]
  if len(targets)!=1:raise ValueError('canary method missing')
  if any(isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='do_3d_projection' for node in ast.walk(targets[0])):raise ValueError('gold lazy projection in actor source')
 return {'class':class_name,'methods':list(methods),'gold_lazy_projection_present':False,'art3d_sha256':sha(path)}

def environment_preflight(root,task):
 out=root/('preflight_'+task);out.mkdir(parents=True,exist_ok=False);work=out/'work';shutil.copytree(qual.OUT/task/'clean_base',work)
 if qual.overlay(work,site_for(task))!=check_overlay(task):raise ValueError('overlay mismatch')
 canary=inspect_frozen_actor_canary(work,task)
 cmd=['docker','run','--rm','--pull','never','--network','none','--read-only','--cpus','1','--memory','2g','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=128m','--tmpfs','/home/agent:rw,nosuid,size=128m','-e','HOME=/home/agent','-e','MPLBACKEND=Agg','-e','MPLCONFIGDIR=/tmp/mpl','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH=/workspace/lib:/deps','--mount',f'type=bind,src={work},dst=/workspace,readonly','--mount',f'type=bind,src={ACTOR_DEPS}/runtime,dst=/extra,readonly','--mount',f'type=bind,src={actor_site_for(task)},dst=/deps,readonly',*ripgrep_binding(),'--workdir','/workspace','--entrypoint','/bin/sh',qual.IMAGE,'-c',
      'set -eu; for p in python python3 python3.10; do /extra/bin/$p -c '+shlex.quote('import sys,matplotlib,numpy; import matplotlib.pyplot as p; import mpl_toolkits.mplot3d.art3d as a; f=p.figure(); f.add_subplot(111).plot([0,1]); f.canvas.draw(); print(sys.version_info[:3],matplotlib.__version__,numpy.__version__,matplotlib.__file__,a.__file__)')+'; done']
 p=subprocess.run(cmd,capture_output=True,timeout=90);(out/'python.stdout').write_bytes(p.stdout);(out/'python.stderr').write_bytes(p.stderr)
 if p.returncode or len(p.stdout.decode().splitlines())!=3 or len(set(p.stdout.decode().splitlines()))!=1:raise ValueError('python aliases/rendering preflight failed')
 cmd=['docker','run','--rm','--pull','never','--network','none','--read-only','--cpus','1','--memory','1g','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=128m','--tmpfs','/home/agent:rw,nosuid,size=128m','-e','HOME=/home/agent','-e','OPENCODE_DISABLE_MODELS_FETCH=1','--mount',f'type=bind,src={work},dst=/root,readonly','--mount',f'type=bind,src={OPENCODE},dst=/opt/opencode,readonly',*ripgrep_binding(),'--workdir','/root','--entrypoint','/opt/opencode',qual.IMAGE,'debug','rg','search','do_3d_projection','--pure']
 r=subprocess.run(cmd,capture_output=True,timeout=90);(out/'rg.stdout').write_bytes(r.stdout);(out/'rg.stderr').write_bytes(r.stderr)
 if r.returncode or not r.stdout:raise ValueError('offline opencode rg failed')
 scan=r'set -eu; for p in /deps/mpl_toolkits/mplot3d/art3d.py /deps/matplotlib/__init__.py /extra/lib/python3.10/site-packages/mpl_toolkits/mplot3d/art3d.py /extra/lib/python3.10/site-packages/matplotlib/__init__.py; do if cat "$p" >/dev/null 2>&1; then echo READABLE:$p; exit 1; elif [ -e "$p" ]; then echo UNEXPECTED_PATH:$p; exit 1; fi; done; if ls -A /var/cache/apt/archives/partial >/dev/null 2>&1; then echo UNEXPECTED_APT_CACHE_READABLE; exit 1; fi; find / -path /proc -prune -o -path /sys -prune -o -path /dev -prune -o -path /var/cache/apt/archives/partial -prune -o -type f \( -path "*/mpl_toolkits/mplot3d/art3d.py" -o -path "*/astropy/nddata/mixins/ndarithmetic.py" \) -print'
 cmd=['docker','run','--rm','--pull','never','--network','none','--read-only','--cpus','1','--memory','1g','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=128m','--tmpfs','/home/agent:rw,nosuid,size=128m','-e','HOME=/home/agent','--mount',f'type=bind,src={work},dst=/root,readonly','--mount',f'type=bind,src={ACTOR_DEPS}/runtime,dst=/extra,readonly','--mount',f'type=bind,src={actor_site_for(task)},dst=/deps,readonly','--mount',f'type=bind,src={OPENCODE},dst=/opt/opencode,readonly',*ripgrep_binding(),'--workdir','/root','--entrypoint','/bin/sh',qual.IMAGE,'-c',scan]
 scan_result=subprocess.run(cmd,capture_output=True,timeout=90);(out/'leak_scan.stdout').write_bytes(scan_result.stdout);(out/'leak_scan.stderr').write_bytes(scan_result.stderr);(out/'leak_scan.exit').write_text(str(scan_result.returncode)+'\n')
 if scan_result.returncode or scan_result.stdout.decode().splitlines()!=['/root/lib/mpl_toolkits/mplot3d/art3d.py']:raise ValueError('unexpected actor-readable mplot3d path')
 ns={'json':json};exec(core.CAPTURE,ns);body=json.dumps({'model':'mock'}).encode();head=b'POST /v1/chat/completions HTTP/1.1\r\nContent-Length: '+str(len(body)).encode()+b'\r\n\r\n';forwarded,meta,_=ns['capture_sampling'](head+body,len(body),lambda _:b'',core.TEMPERATURE,7201)
 if json.loads(forwarded.split(b'\r\n\r\n',1)[1])['seed']!=7201 or meta['temperature']!=core.TEMPERATURE:raise ValueError('sampling override failed')
 try:ns['capture_sampling'](head,len(body),lambda _:b'',core.TEMPERATURE,7201)
 except EOFError:pass
 else:raise ValueError('short request accepted')
 return {'python_stdout_sha256':sha(out/'python.stdout'),'python_stderr_sha256':sha(out/'python.stderr'),'rg_stdout_sha256':sha(out/'rg.stdout'),'rg_stderr_sha256':sha(out/'rg.stderr'),'overlay_sha256':OVERLAYS[task],'ripgrep_sha256':RG_SHA256,'actor_projection_sha256':ACTOR_DEPS_SHA,'canary':canary,'readable_art3d_paths':['/root/lib/mpl_toolkits/mplot3d/art3d.py'],'excluded_virtual_paths':['/proc','/sys','/dev'],'excluded_verified_unreadable_paths':['/var/cache/apt/archives/partial'],'leak_scan_stdout_sha256':sha(out/'leak_scan.stdout'),'leak_scan_stderr_sha256':sha(out/'leak_scan.stderr'),'scope':'specific mplot3d art3d and Astropy ndarithmetic paths across actor mounts and image; not a general untrusted-sandbox guarantee','sampling_mock':'PASS'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--attempt-id',required=True);p.add_argument('--source-attempt-id');p.add_argument('--source-seed',type=int,default=core.SEED);p.add_argument('--seed',type=int,default=core.SEED);p.add_argument('--max-posts',type=int,default=DEFAULT_POSTS);p.add_argument('--max-seconds',type=int,default=DEFAULT_SECONDS);p.add_argument('--context-limit',type=int,default=DEFAULT_CONTEXT);p.add_argument('--output-limit',type=int,default=DEFAULT_OUTPUT)
 a=p.add_mutually_exclusive_group(required=True);a.add_argument('--task',choices=('source','target'));a.add_argument('--build-experience',action='store_true');a.add_argument('--generate-skill',action='store_true');a.add_argument('--reevaluate-source',action='store_true')
 p.add_argument('--use-source-revision',action='store_true');p.add_argument('--condition',choices=('none','source_history','feedback_card','generated_skill'),default='none');p.add_argument('--experience',type=Path);p.add_argument('--experience-sha256');p.add_argument('--preflight-only',action='store_true');args=p.parse_args()
 for x in (args.attempt_id,args.source_attempt_id):
  if x is not None and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',x):p.error('invalid attempt id')
 if not (0<=args.seed<2**31 and 0<=args.source_seed<2**31 and args.max_posts>0 and args.max_seconds>0 and 4096<=args.context_limit<=65536 and 0<args.output_limit<args.context_limit):p.error('invalid seed/limits')
 root=PARENT/'attempts'/args.attempt_id;source_root=PARENT/'attempts'/(args.source_attempt_id or args.attempt_id)
 if args.build_experience or args.generate_skill or args.reevaluate_source:
  if args.condition!='none' or args.experience or args.experience_sha256 or args.preflight_only or (args.use_source_revision and not args.build_experience):p.error('incompatible arguments')
  preflight('source')
  if args.build_experience:build_experience(source_root,args.source_seed,use_revision=args.use_source_revision)
  elif args.reevaluate_source:reevaluate_source(source_root,args.source_seed)
  else:
   verify_source_actor_projection(source_root,args.source_seed)
   requests_runner.generate_skill(source_root)
  return
 if args.use_source_revision:p.error('--use-source-revision applies to --build-experience only')
 if (args.condition=='none')!=(args.experience is None) or ((args.experience is None)!=(args.experience_sha256 is None)):p.error('experience and hash required together')
 if args.task=='source' and args.condition!='none':p.error('source must have no experience')
 if args.experience and (args.experience.is_symlink() or sha(args.experience)!=args.experience_sha256):raise ValueError('experience changed')
 control=preflight(args.task);code=derive(root,args.task,args.condition,args.experience,seed=args.seed,max_posts=args.max_posts,max_seconds=args.max_seconds,context_limit=args.context_limit,output_limit=args.output_limit)
 if args.preflight_only:
  root.mkdir(parents=True,exist_ok=True);harness=root/('preflight_'+args.task+'.harness.py');report=root/('preflight_'+args.task+'.json')
  if any(x.exists() for x in (harness,report,root/('preflight_'+args.task))):raise FileExistsError('preflight already exists')
  with harness.open('x') as f:f.write(code)
  env=environment_preflight(root,args.task);result={'status':'PREFLIGHT_PASS_NO_MODEL','task':args.task,'attempt_id':args.attempt_id,'runner_sha256':sha(Path(__file__)),'qualification_sha256':QUAL_SHA,'harness_sha256':sha(harness),'environment':env,'model_calls':0}
  with report.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
  print(json.dumps(result));return
 target_freeze=None
 if args.task=='target':
  verify_source_actor_projection(source_root,args.source_seed)
  d=source_root/'source_experience';freeze=d/'target_input_freeze.json';files=('source_history.md','feedback_card.md','generated_skill.md');completed=source_root/f'source__none__seed{args.source_seed}.completed.json'
  if not freeze.exists():
   ledger=json.loads((d/'skill_generation_ledger.json').read_text());meta=json.loads((d/'metadata.json').read_text())
   if ledger['status']!='RECEIVED' or ledger['finish_reason']!='stop' or meta['source_seed']!=args.source_seed or meta['source_completion_sha256']!=sha(completed):raise ValueError('source evidence or generated skill incomplete')
   if any(meta['artifacts'][n]!=sha(d/n) for n in ('source_history.md','feedback_card.md')) or ledger['source_history_sha256']!=sha(d/'source_history.md') or ledger['skill_sha256']!=sha(d/'generated_skill.md'):raise ValueError('source artifact provenance mismatch')
   if meta['source_raw_sha256']!=sha(source_root/f'source__none__seed{args.source_seed}'/'raw.jsonl'):raise ValueError('source raw changed')
   if meta.get('source_revision_sha256'):
    source_revision(source_root,args.source_seed,meta['source_revision_sha256'])
    source_semantic_detail(source_root,args.source_seed,meta['source_semantic_detail_sha256'])
   record={'source_semantic_detail_sha256':meta.get('source_semantic_detail_sha256'),'source_revision_sha256':meta.get('source_revision_sha256'),'source_completion_sha256':sha(completed),'source_metadata_sha256':sha(d/'metadata.json'),'skill_generation_ledger_sha256':sha(d/'skill_generation_ledger.json'),'source_seed':args.source_seed,'artifacts':{n:sha(d/n) for n in files},'scope':'source-only; frozen before first target call; research team has seen target references'}
   with freeze.open('x') as f:json.dump(record,f,indent=2)
  record=json.loads(freeze.read_text())
  if record.get('source_revision_sha256'):
   source_revision(source_root,args.source_seed,record['source_revision_sha256'])
   source_semantic_detail(source_root,args.source_seed,record['source_semantic_detail_sha256'])
  if record['source_seed']!=args.source_seed or record['source_completion_sha256']!=sha(completed) or record['source_metadata_sha256']!=sha(d/'metadata.json') or record['skill_generation_ledger_sha256']!=sha(d/'skill_generation_ledger.json') or any(sha(d/n)!=h for n,h in record['artifacts'].items()):raise ValueError('source inputs changed')
  if args.experience and (args.experience.resolve().parent!=d.resolve() or record['artifacts'].get(args.experience.name)!=args.experience_sha256 or args.experience.name!={'source_history':'source_history.md','feedback_card':'feedback_card.md','generated_skill':'generated_skill.md'}[args.condition]):raise ValueError('experience outside frozen set')
  target_freeze=sha(freeze)
 (root/'runtime').mkdir(parents=True,exist_ok=True)
 if any((root/'runtime').iterdir()):raise ValueError('actor runtime mount must be empty')
 @recorded_episode(root,args.seed)
 def run(task,condition):
  eid=f'{task}__{condition}__seed{args.seed}';case=root/eid;harness=root/(eid+'.harness.py');snapshot=root/(eid+'.outer_runner.py')
  if any(q.exists() for q in (case,harness,snapshot,root/(eid+'.started.json'),root/(eid+'.completed.json'))):raise FileExistsError('episode already exists')
  with harness.open('x') as f:f.write(code)
  with snapshot.open('xb') as f:f.write(Path(__file__).read_bytes())
  components={'core':Path(core.__file__),'requests_runner':Path(requests_runner.__file__),'qualification':Path(qual.__file__),'auto_record':Path(auto_record.__file__),'evidence_graph':Path(evidence_graph.__file__),'tool_runtime':Path(tool_runtime.__file__),'actor_dependencies':Path(actor_dependencies.__file__),'shared_qualification':Path(shared.__file__),'sphinx_runner':Path(sphinx_runner.__file__),'opencode':OPENCODE};component_hashes={n:sha(v) for n,v in components.items()}
  plan={'status':'STARTED','component_sha256':component_hashes,'task':task,'condition':condition,'attempt_id':args.attempt_id,'seed':args.seed,'temperature':core.TEMPERATURE,'source_attempt_id':source_root.name,'source_seed':args.source_seed,'max_posts':args.max_posts,'max_seconds':args.max_seconds,'context_limit':args.context_limit,'output_limit':args.output_limit,'proxy_max_bytes':core.MAX_BYTES,'task_identity':control['id'],'base_commit':control['base_commit'],'harness_sha256':sha(harness),'outer_runner_snapshot_sha256':sha(snapshot),'runner_sha256':sha(Path(__file__)),'qualification_sha256':QUAL_SHA,'actor_projection_sha256':ACTOR_DEPS_SHA,'overlay_sha256':OVERLAYS[task],'ripgrep_sha256':RG_SHA256,'task_text_sha256':control['task_sha256'],'experience_sha256':args.experience_sha256,'target_input_freeze_sha256':target_freeze,'candidate_reference_hidden':True}
  start=root/(eid+'.started.json');start.write_text(json.dumps(plan,indent=2)+'\n')
  proc=subprocess.run([sys.executable,str(harness),task,'no_skill'],stdin=subprocess.DEVNULL,capture_output=True,timeout=args.max_seconds+120);(root/(eid+'.runner.stdout')).write_bytes(proc.stdout);(root/(eid+'.runner.stderr')).write_bytes(proc.stderr);plan.update({'runner_exit':proc.returncode,'started_sha256':sha(start)})
  if sha(snapshot)!=plan['outer_runner_snapshot_sha256'] or any(sha(path)!=component_hashes[n] for n,path in components.items()):raise ValueError('runner snapshot or component changed')
  ripgrep_binding();verify_projection(ACTOR_DEPS,ACTOR_DEPS_SHA)
  if any((root/'runtime').iterdir()):raise ValueError('actor runtime mount changed')
  if proc.returncode==0 and (case/'receipt.json').is_file():
   r=json.loads((case/'receipt.json').read_text());raw=case/'raw.jsonl'
   if sha(raw)!=r['raw_sha256']:raise ValueError('raw changed')
   sample=case/'sampling_metadata.jsonl';metadata=[json.loads(s) for s in sample.read_text().splitlines()] if sample.is_file() else []
   if Counter(json.dumps(x,sort_keys=True) for x in metadata)!=Counter(json.dumps(x,sort_keys=True) for x in r['sampling_metadata']):raise ValueError('sampling mismatch')
   if (case/'frozen_instructions.txt').read_bytes()!=(qual.OUT/task/'task.txt').read_text().strip().encode():raise ValueError('task mismatch')
   if args.experience and sha(args.experience)!=args.experience_sha256:raise ValueError('experience changed during run')
   plan.update({'status':'COMPLETED','agent_exit':r['agent_exit'],'raw_sha256':r['raw_sha256'],'posts':sum(x.startswith('POST ') for x in r['model_http_requests']),'denied':[x for x in r['model_http_requests'] if x.startswith('DENIED')],'reported_tokens':sum(x.get('total',0) for x in r['step_finish_tokens']),'cache_read_included':sum(x.get('cache',{}).get('read',0) for x in r['step_finish_tokens']),'seed_and_temperature_forwarded':bool(metadata) and all(x['seed']==args.seed and x['temperature']==core.TEMPERATURE for x in metadata),'experience_read':inspect_experience_reads(raw,args.experience) if args.experience else None,'post_run_evaluation':evaluate(task,case)})
  else:plan['status']='RUNNER_ERROR_REVIEW_RAW_AND_PROXY_LOG'
  complete=root/(eid+'.completed.json');complete.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({'receipt':str(complete),'sha256':sha(complete),'result':plan}))
 run(args.task,args.condition)
if __name__=='__main__':main()
