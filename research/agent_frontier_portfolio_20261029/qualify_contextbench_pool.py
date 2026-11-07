"""Frozen target/source CPU qualification; check never starts a container or model."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, importlib, json, os, re, shutil, subprocess, sys, tarfile, time

ROOT=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
HERE=Path(__file__).resolve().parent
LEGACY=Path('/home/testuser/miniconda3/envs/haiguan')
IMAGE='sha256:648a1999badfe683239ec49e05b2a508e37f762213478122c58fa713f6c00f58'
TARGETS={'django__django-31051':('django/django',12,25),'sympy__sympy-9384':('sympy/sympy',2,320),'sympy__sympy-19006':('sympy/sympy',4,48)}
SOURCES={'django__django-12453':('django/django',1,5,'django__django-31051'),'sympy__sympy-21055':('sympy/sympy',1,13,'sympy__sympy-9384')}
QUALIFIED_TARGETS_SHA='01493c013446b832b084aa914a578d4a0b0fe5b2645665792d59f43a7479da2f'
PINS={'qualify_swe_contextbench_sympy_20261104':'98e20dc49a8b01dd956aed5035b09e7aeeeba11a454fdaf9a17d1d315a61e085','qualify_swe_contextbench_django_20261104':'d232272dd6538cebe67b7867ce0b9fc133b7af9800cf6d64d57569aea71cb078'}
MARKER='CONTEXTBENCH_RESULT='


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def safe(path,root=None):
    path=Path(path);root=ROOT if root is None else root
    if not path.is_absolute() or path!=path.resolve() or root not in path.parents or any(p.is_symlink() for p in [path,*path.parents]):raise ValueError('unsafe private path')
    return path


def checked(ref,bindings):
    if type(ref) is not dict or set(ref)!={'path','sha256'} or not re.fullmatch('[a-f0-9]{64}',ref['sha256']):raise ValueError('invalid frozen reference')
    path=safe(ref['path'])
    if sha(path)!=ref['sha256']:raise ValueError('frozen input hash changed')
    bindings[str(path)]=ref['sha256'];return json.loads(path.read_text())


def helpers():
    for name,digest in PINS.items():
        if sha(HERE/(name+'.py'))!=digest:raise ValueError('qualification helper changed')
    inserted=str(HERE) not in sys.path
    if inserted:sys.path.insert(0,str(HERE))
    try:return tuple(importlib.import_module(name) for name in PINS)
    finally:
        if inserted:sys.path.remove(str(HERE))


def mapped_labels(repo,items):
    if type(items) is not list or not items or len(set(items))!=len(items):raise ValueError('empty/duplicate labels')
    mapped=[]
    for label in items:
        if type(label) is not str or any(ord(c)<32 for c in label) or '\\' in label:raise ValueError('invalid label')
        parts=label.split('::');path=PurePosixPath(parts[0])
        if path.is_absolute() or '..' in path.parts or '.' in parts[0].split('/') or len(parts)<2 or any(not p for p in parts) or not parts[0].endswith('.py'):raise ValueError('unmapped path label')
        if repo=='django/django':
            if not parts[0].startswith('tests/') or any(not re.fullmatch('[A-Za-z_]\\w*',p) for p in parts[1:]):raise ValueError('unmapped Django label')
            mapped.append(parts[0][6:-3].replace('/','.')+'.'+'.'.join(parts[1:]))
        elif repo=='sympy/sympy' and parts[0].startswith('sympy/'):mapped.append(label)
        else:raise ValueError('unmapped repository/label')
    if len(set(mapped))!=len(mapped):raise ValueError('duplicate mapped labels')
    return mapped


def dependencies(kind,ref,bindings):
    manifest=checked(ref,bindings);env=ROOT/('swe_contextbench_django_env_20261104' if kind=='django' else 'swe_contextbench_sympy_python38_env_20261104')
    for key,directory in [('site_files',env/'site'),('wheels',env/'wheelhouse')]:
        expected=manifest[key]
        actual={p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
        if not expected or actual!=set(expected):raise ValueError('dependency file inventory changed')
        for name,digest in expected.items():
            path=safe(directory/name)
            if sha(path)!=digest:raise ValueError('dependency content changed')
            bindings[str(path)]=digest
    if kind=='sympy':
        binary=LEGACY/'bin/python'
        if manifest['container_image']!=IMAGE or not binary.resolve().is_relative_to(LEGACY) or sha(binary)!=manifest['python_binary_sha256']:raise ValueError('legacy interpreter changed')
        bindings[str(binary)]=manifest['python_binary_sha256']
    return 'Python3.8 via shared SHA-bound read-only LEGACY; repository site/wheels frozen; full conda runtime library tree not frozen. '+manifest.get('limits','')


def archive_members(path,repo,revision):
    prefix=repo.split('/')[1]+'-'+revision;count=links=0;license=False
    with tarfile.open(path,'r:gz') as stream:
        for member in stream:
            p=PurePosixPath(member.name)
            if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0]!=prefix or '.git' in p.parts:raise ValueError('unsafe archive path')
            if member.issym() and repo=='django/django' and member.name.startswith(prefix+'/docs/_theme/djangodocs-epub/static/') and member.linkname.startswith('../../djangodocs/static/'):links+=1;continue
            if not (member.isfile() or member.isdir()):raise ValueError('unsafe archive member type')
            count+=member.isfile();license=license or member.name==prefix+'/LICENSE'
    if not license or links!=(4 if repo=='django/django' else 0):raise ValueError('archive license/link contract changed')
    return count


def source_labels(spec,row):
    mapping=spec['label_map'];result={}
    if type(mapping) is not dict or set(mapping)!={'f2p','ptp'}:raise ValueError('invalid source label map')
    module='tests/backends/base/test_creation.py' if spec['repo']=='django/django' else 'sympy/assumptions/tests/test_refine.py'
    if module not in {s[6:] for s in row['test_patch'].splitlines() if s.startswith('+++ b/')}:raise ValueError('source module absent from published test patch')
    for suite,field in [('f2p','FAIL_TO_PASS'),('ptp','PASS_TO_PASS')]:
        entries=mapping[suite];published=json.loads(row[field])
        if type(entries) is not list or any(type(e) is not dict or set(e)!={'published','node'} for e in entries) or [e['published'] for e in entries]!=published:raise ValueError('source map must cover published labels exactly in order')
        nodes=[e['node'] for e in entries];converted=mapped_labels(spec['repo'],nodes)
        for e,node in zip(entries,converted):
            if e['node'].split('::')[0]!=module:raise ValueError('source node outside fixed test module')
            if spec['repo']=='django/django':
                old=re.fullmatch(r'([A-Za-z_]\w*)\s+\(([A-Za-z_][\w.]*)\)',e['published'])
                if len(e['node'].split('::'))!=3 or not old or node!=old.group(2)+'.'+old.group(1):raise ValueError('source Django mapping lost or changed method')
            elif not re.fullmatch(r'test_[A-Za-z_]\w*',e['published']) or node!=module+'::'+e['published']:raise ValueError('source SymPy bare name mapping differs')
        result[suite]=converted
    flat=result['f2p']+result['ptp']
    if len(flat)!=len(set(flat)):raise ValueError('source labels alias one executable node')
    return result


def load_contract(path,digest,output):
    bindings={};c=checked(dict(path=str(path),sha256=digest),bindings);output=safe(output)
    if output.exists():raise FileExistsError('fresh private output required')
    source=c.get('schema')=='contextbench_pool_qualification_source_v2';catalog=SOURCES if source else TARGETS
    keys={'schema','dataset_manifest','ancestry','cases','runtime'}|({'qualified_targets'} if source else set())
    if set(c)!=keys or c.get('schema') not in ('contextbench_pool_qualification_v1','contextbench_pool_qualification_source_v2'):raise ValueError('unknown contract schema')
    if [r['instance_id'] for r in c['cases']]!=list(catalog):raise ValueError('duplicate/unknown/misordered cases')
    h,d=helpers();dataset=checked(c['dataset_manifest'],bindings)
    if Path(c['dataset_manifest']['path']).parent!=h.DATA:raise ValueError('dataset helper root differs')
    for row in dataset['files']:
        if Path(row['name']).name!=row['name']:raise ValueError('unsafe dataset basename')
        file=safe(h.DATA/row['name'])
        if sha(file)!=row['sha256']:raise ValueError('dataset file changed')
        bindings[str(file)]=row['sha256']
    ancestry=checked(c['ancestry'],bindings);inventory=checked(ancestry['input'],bindings)
    selected={r['target']['instance_id']:r['target'] for r in inventory['qualification_candidates']}
    if source:
        if c['qualified_targets']['sha256']!=QUALIFIED_TARGETS_SHA:raise ValueError('source qualified-target registry changed')
        registry=checked(c['qualified_targets'],bindings);registered={r['instance_id']:r for r in registry['cases']}
        if registry['schema']!='qualified_code_development_pool_v1' or len(registry['cases'])!=2 or set(registered)!={r[3] for r in SOURCES.values()}:raise ValueError('source targets are not the frozen qualified pair')
    if set(c['runtime'])!={'image','django_dependency_manifest','sympy_dependency_manifest'} or c['runtime']['image']!=IMAGE:raise ValueError('runtime image/schema changed')
    limits={k:dependencies(k,c['runtime'][k+'_dependency_manifest'],bindings) for k in ('django','sympy')};cases=[]
    for spec in c['cases']:
        fields={'instance_id','repo','base_commit','dataset_file','archive'}|({'role','related_target_id','label_map'} if source else set())
        if set(spec)!=fields or Path(spec['dataset_file']).name!=spec['dataset_file'] or spec['dataset_file'] not in {r['name'] for r in dataset['files']}:raise ValueError('invalid case/path schema')
        if source:
            if spec['role']!='source' or spec['dataset_file']!='SWEContextBench_Lite_Experience.parquet' or spec['related_target_id']!=catalog[spec['instance_id']][3]:raise ValueError('source role/dataset/related target changed')
            related=spec['related_target_id'];identity={k:spec[k] for k in ('repo','instance_id','base_commit')};target=selected[related]
            bound=registered[related];earlier=bound['earlier_experience_candidate']
            if any(earlier[k]!=identity[k] or bound[k]!=target[k] for k in identity):raise ValueError('source or related qualified-target identity differs')
            a=[r for r in ancestry['rows'] if r['target']==target and all(r['source'][k]==v for k,v in identity.items())]
        else:
            target=selected[spec['instance_id']];a=[r for r in ancestry['rows'] if r['target']==target]
        if spec['repo']!=catalog[spec['instance_id']][0] or (not source and spec['base_commit']!=target['base_commit']) or len(a)!=1 or a[0]['source_merge_is_ancestor'] is not True or a[0]['status']!='ANCESTRY_CONFIRMED':raise ValueError('case ancestry/binding changed')
        row=h.dataset_row(dict(id=spec['instance_id'],rev=spec['base_commit'],data=spec['dataset_file']))
        labels=source_labels(spec,row) if source else {key:mapped_labels(spec['repo'],json.loads(row[field])) for key,field in [('f2p','FAIL_TO_PASS'),('ptp','PASS_TO_PASS')]}
        if tuple(map(len,labels.values()))!=catalog[spec['instance_id']][1:3]:raise ValueError('published label counts changed')
        if spec['repo']=='django/django' and not source:
            converted,unresolved=d.regression_labels(dict(id=spec['instance_id'],rev=spec['base_commit'],data=spec['dataset_file']))
            if unresolved or converted!=labels['ptp']:raise ValueError('Django helper mapping differs')
        ref=spec['archive'];archive=safe(ref['path'])
        if set(ref)!={'path','sha256'} or sha(archive)!=ref['sha256']:raise ValueError('archive hash changed')
        bindings[str(archive)]=ref['sha256'];archive_members(archive,spec['repo'],spec['base_commit'])
        cases.append(dict(spec=spec,row=row,labels=labels))
    bindings.update({str(HERE/(name+'.py')):digest for name,digest in PINS.items()})
    bindings[str(Path(__file__).resolve())]=sha(__file__)
    return dict(contract=c,bindings=bindings,cases=cases,helpers=(h,d),limits=limits,output=output)


# Runs only inside the owned container. No helper globals or project files patched.
RUNNER=r'''import json,runpy,sys,traceback,unittest
kind=sys.argv[1];labels=sys.argv[2:];result={'tests':{},'fatal':[]}
def status(test,value):result['tests'][test]=value
def error_kind(test,err):
 return 'error' if issubclass(err[0],(ImportError,SyntaxError)) or test.__class__.__name__.startswith('_') else 'failed'
try:
 assert sys.version_info[:2]==(3,8), 'wrong historical Python runtime'
 if kind=='django':
  sys.path.insert(0,'/workspace/tests')
  class Recorded(unittest.TextTestResult):
   def addSuccess(self,test):status(test.id(),'passed');super().addSuccess(test)
   def addFailure(self,test,err):status(test.id(),'failed');super().addFailure(test,err)
   def addError(self,test,err):status(test.id(),error_kind(test,err));super().addError(test,err)
   def addSkip(self,test,reason):status(test.id(),'skipped');super().addSkip(test,reason)
   def addExpectedFailure(self,test,err):status(test.id(),'xfailed');super().addExpectedFailure(test,err)
   def addUnexpectedSuccess(self,test):status(test.id(),'xpassed');super().addUnexpectedSuccess(test)
   def addSubTest(self,test,subtest,err):
    if err:status(test.id(),error_kind(test,err))
    super().addSubTest(test,subtest,err)
  unittest.TextTestRunner.resultclass=Recorded
  sys.argv=['tests/runtests.py','--settings=test_sqlite','--parallel=1','--verbosity=2']+labels
  runpy.run_path('tests/runtests.py',run_name='__main__');code=0
 else:
  import pytest
  class Plugin:
   def pytest_collectreport(self,report):
    if report.failed:result['fatal'].append('collection_error')
   def pytest_runtest_logreport(self,report):
    if report.failed and report.when!='call':status(report.nodeid,'error')
    elif report.when=='call' or report.skipped:
     value='error' if report.failed and any(k in report.longreprtext for k in ('ImportError','ModuleNotFoundError')) else report.outcome
     if hasattr(report,'wasxfail') and report.skipped:value='xfailed'
     elif hasattr(report,'wasxfail') and report.passed:value='xpassed'
     status(report.nodeid,value)
  code=pytest.main(['-q','-p','no:cacheprovider']+labels,plugins=[Plugin()])
except SystemExit as exc:code=exc.code
except BaseException as exc:code=2;result['fatal'].append(type(exc).__name__);traceback.print_exc()
print('CONTEXTBENCH_RESULT='+json.dumps(result),flush=True)
raise SystemExit(code)
'''


def classify(labels,record):
    payload=record.get('result') or {};tests=payload.get('tests') or {};mapped={};used=set()
    for label in labels:
        ids=[n for n in tests if n==label or n.startswith(label+'[')];used.update(ids);states=[tests[n] for n in ids]
        mapped[label]='missing' if not ids else 'error' if any(s not in ('passed','failed') for s in states) else 'failed' if 'failed' in states else 'passed'
    complete=not payload.get('fatal') and set(tests)==used and all(v in ('passed','failed') for v in mapped.values()) and record.get('exit') in (0,1)
    return dict(labels=mapped,complete=complete,reported_tests=len(tests),extra_ids=sorted(set(tests)-used))


def command(work,repo,labels,runner_path,name):
    kind='django' if repo=='django/django' else 'sympy';site=ROOT/('swe_contextbench_'+('django_env_20261104' if kind=='django' else 'sympy_python38_env_20261104'))/'site'
    cmd=['docker','run','--name',name,'--rm','--pull','never','--network','none','--read-only','--cpus','1','--memory','1g','--pids-limit','256','--cap-drop','ALL','--security-opt','no-new-privileges','--user',str(os.getuid())+':'+str(os.getgid()),'--tmpfs','/tmp:rw,nosuid,size=128m','-e','PYTHONPATH=/workspace:/deps','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1','-e','HYPOTHESIS_STORAGE_DIRECTORY=/tmp/hypothesis','--workdir','/workspace']
    for src,dst in ((work,'/workspace'),(site,'/deps'),(runner_path,'/qualifier.py')):cmd+=['--mount','type=bind,src='+str(src)+',dst='+dst+',readonly']
    cmd+=['--mount','type=bind,src='+str(LEGACY)+',dst=/opt/legacy,readonly']
    return cmd+['--entrypoint','/opt/legacy/bin/python',IMAGE,'/qualifier.py',kind,*labels]


def mem_available():
    return int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024


def new(path,value):
    with Path(path).open('x',encoding='utf8') as f:json.dump(value,f,indent=2);f.write('\n')


def run_tests(work,repo,labels,runner_path,log):
    available=mem_available()
    if available<4*1024**3:return dict(status='DEFERRED',MemAvailable=available)
    name='cb-pool-'+str(os.getpid())+'-'+str(time.monotonic_ns());cmd=command(work,repo,labels,runner_path,name);started=time.monotonic();cleanup=None
    new(log.with_suffix('.command.json'),dict(argv=cmd,container=name,timeout_seconds=240))
    try:
        proc=subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240);code,raw=proc.returncode,proc.stdout
    except subprocess.TimeoutExpired as exc:
        code,raw=124,exc.stdout or b'';log.write_bytes(raw);cleanup=dict(argv=['docker','rm','-f',name],timeout_seconds=15)
        try:
            done=subprocess.run(cleanup['argv'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=15,check=False)
            cleanup['exit']=done.returncode;cleanup_raw=done.stdout or b''
        except Exception as error:cleanup.update(exit=None,error=type(error).__name__);cleanup_raw=getattr(error,'stdout',None) or b''
        cleanup_log=log.with_suffix('.cleanup.log');cleanup_log.write_bytes(cleanup_raw);cleanup['log_sha256']=sha(cleanup_log)
    log.write_bytes(raw);markers=[s[len(MARKER):] for s in raw.decode('utf8',errors='replace').splitlines() if s.startswith(MARKER)]
    try:result=json.loads(markers[0]) if len(markers)==1 else {'fatal':['missing/duplicate machine result']}
    except ValueError:result={'fatal':['invalid machine result']}
    record=dict(exit=code,result=result,seconds=time.monotonic()-started,log_sha256=sha(log),MemAvailable=available,cleanup=cleanup)
    if cleanup is not None and cleanup['exit']!=0:record['status']='CLEANUP_FAILED'
    record['coverage']=classify(labels,record);return record


def qualification(base_f2p,gold_f2p,base_ptp,gold_ptp):
    records=(base_f2p,gold_f2p,base_ptp,gold_ptp);expected=('failed','passed','passed','passed')
    checks=[r.get('coverage',{}).get('complete',False) and all(v==state for v in r['coverage']['labels'].values()) and r.get('exit')==(1 if state=='failed' else 0) for r,state in zip(records,expected)]
    return dict(qualified=all(checks),base_all_f2p_reproduced=checks[0],gold_all_f2p_pass=checks[1],base_all_ptp_pass=checks[2],gold_all_ptp_pass=checks[3])


def tree(root):
    paths=sorted(root.rglob('*'))
    if any(p.is_symlink() for p in paths):raise ValueError('patched tree contains a symbolic link')
    return {str(p.relative_to(root)):sha(p) for p in paths if p.is_file()}


def patched(h,work,content,source):
    started=time.monotonic();result=h.apply_patch(work,content)
    commands=[['git','apply','--check','-']]+([['git','apply','-']] if result['check_exit']==0 else [])
    return dict(result,commands=commands,cwd=str(work),input_path=str(source),input_sha256=sha(source),seconds=time.monotonic()-started)


def execute(c):
    out=c['output'];out.mkdir();h,d=c['helpers'];runner=out/'qualifier.py';runner.write_text(RUNNER)
    result=dict(status='STARTED',input_sha256=c['bindings'],runner_sha256=sha(runner),dependency_limits=c['limits'],model_calls=0,cases={})
    try:
        for case in c['cases']:
            available=mem_available()
            if available<4*1024**3:result.update(status='DEFERRED',deferred_MemAvailable=available);break
            if any(sha(p)!=digest for p,digest in c['bindings'].items()):raise ValueError('frozen qualification inputs changed')
            spec,row,labels=case['spec'],case['row'],case['labels'];root=out/spec['instance_id'];root.mkdir();base=root/'clean_base'
            extraction=(d.extract if spec['repo']=='django/django' else h.extract_safe)(Path(spec['archive']['path']),base,spec['base_commit']);clean=tree(base)
            for name,field in [('task.txt','problem_statement'),('test.patch','test_patch'),('reference.patch','patch')]: (root/name).write_text(row[field],encoding='utf8')
            record=dict(spec=spec,extraction=extraction,clean_base_sha256=clean,input_sha256={name:sha(root/name) for name in ('task.txt','test.patch','reference.patch')},labels=labels,arms={});result['cases'][spec['instance_id']]=record
            for arm in ('base_with_tests','gold_with_tests'):
                work=root/arm;shutil.copytree(base,work);a=dict(test_patch=patched(h,work,row['test_patch'],root/'test.patch'));record['arms'][arm]=a
                if a['test_patch']['apply_exit']!=0:continue
                if arm=='gold_with_tests':
                    a['reference_patch']=patched(h,work,row['patch'],root/'reference.patch')
                    if a['reference_patch']['apply_exit']!=0:continue
                a['tree_sha256']=tree(work)
                for suite in ('f2p','ptp'):
                    a[suite]=run_tests(work,spec['repo'],labels[suite],runner,root/(arm+'_'+suite+'.log'))
                    if a[suite].get('status')=='CLEANUP_FAILED':raise RuntimeError('owned container cleanup failed; stop queue')
                    if a[suite].get('status')=='DEFERRED':result['status']='DEFERRED';break
                if result['status']=='DEFERRED':break
            if tree(base)!=clean:raise ValueError('clean actor base was changed')
            arms=record['arms'];record['qualification']=qualification(*(arms.get(a,{}).get(s,{}) for a,s in [('base_with_tests','f2p'),('gold_with_tests','f2p'),('base_with_tests','ptp'),('gold_with_tests','ptp')]))
            if result['status']=='DEFERRED':break
        if result['status']!='DEFERRED':
            if any(sha(p)!=digest for p,digest in c['bindings'].items()):raise ValueError('qualification inputs changed during tests')
            result['status']='QUALIFIED' if len(result['cases'])==len(c['cases']) and all(r['qualification']['qualified'] for r in result['cases'].values()) else 'NOT_QUALIFIED'
    except Exception as exc:result.update(status='ERROR',error=dict(type=type(exc).__name__,message=str(exc)))
    finally:new(out/'receipt.json',result)
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);mode=p.add_mutually_exclusive_group(required=True);mode.add_argument('--check',action='store_true');mode.add_argument('--execute',action='store_true')
    p.add_argument('--contract',type=Path,required=True);p.add_argument('--contract-sha',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--check-report',type=Path);args=p.parse_args(argv)
    c=load_contract(args.contract,args.contract_sha,args.output)
    if args.check:
        result=dict(status='CPU_CHECK_ONLY',input_sha256=c['bindings'],dependency_limits=c['limits'],cases={r['spec']['instance_id']:{k:len(v) for k,v in r['labels'].items()} for r in c['cases']},model_calls=0,container_runs=0)
        if args.check_report:
            report=safe(args.check_report)
            if args.output==report or args.output in report.parents:raise ValueError('check report must be outside planned output')
            new(report,result)
    else:
        if args.check_report:p.error('--check-report is check only')
        result=execute(c)
    print(json.dumps(dict(status=result['status'],cases=len(result['cases']),model_calls=0)))
    return 0 if result['status'] in ('CPU_CHECK_ONLY','QUALIFIED','DEFERRED') else 1


if __name__=='__main__':raise SystemExit(main())
