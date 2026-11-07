"""Frozen target/source CPU qualification; check never starts a container or model."""
from pathlib import Path, PurePosixPath
import argparse, ast, hashlib, importlib, json, os, re, shutil, subprocess, sys, tarfile, time

ROOT=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
HERE=Path(__file__).resolve().parent
LEGACY=Path('/home/testuser/miniconda3/envs/haiguan')
IMAGE='sha256:648a1999badfe683239ec49e05b2a508e37f762213478122c58fa713f6c00f58'
TARGETS={'django__django-31051':('django/django',12,25),'sympy__sympy-9384':('sympy/sympy',2,320),'sympy__sympy-19006':('sympy/sympy',4,48)}
SOURCES={'django__django-12453':('django/django',1,5,'django__django-31051'),'sympy__sympy-21055':('sympy/sympy',1,13,'sympy__sympy-9384')}
QUALIFIED_TARGETS_SHA='01493c013446b832b084aa914a578d4a0b0fe5b2645665792d59f43a7479da2f'
PINS={'qualify_swe_contextbench_sympy_20261104':'98e20dc49a8b01dd956aed5035b09e7aeeeba11a454fdaf9a17d1d315a61e085','qualify_swe_contextbench_django_20261104':'d232272dd6538cebe67b7867ce0b9fc133b7af9800cf6d64d57569aea71cb078'}
MARKER='CONTEXTBENCH_RESULT='

MPL_CASES={
 'matplotlib__matplotlib-25332':('66ba515e671638971bd11a34cff12c107a437e0b','source','SWEContextBench_Lite_Experience.parquet',1,181,'lib/matplotlib/tests/test_pickle.py'),
 'matplotlib__matplotlib-25352':('3742e7e8385e70072fb2521a411a25dd69d22dbf','target','SWEContextBench_Related_Lite.parquet',1,60,'lib/matplotlib/tests/test_cbook.py')}
MPL_HELPER_SHA='c91d9af76f2f45674204189adc81802d187bbe1fe59f529cf786f36a4d03ba0c'
MPL_DEPS_SHA='6e24052dcb0ec25083b8f183129220cc7213bb682a0b53c2aa4563d5ce184a7c'
MPL_WARNING_RULES=[{'message': 'pkg_resources is deprecated as an API', 'category': 'DeprecationWarning', 'module': 'pkg_resources'}, {'message': 'pkg_resources is deprecated as an API', 'category': 'DeprecationWarning', 'module': 'mpl_toolkits'}, {'message': 'Deprecated call to `pkg_resources.declare_namespace', 'category': 'DeprecationWarning', 'module': 'pkg_resources'}, {'message': 'Deprecated call to `pkg_resources.declare_namespace', 'category': 'DeprecationWarning', 'module': 'mpl_toolkits'}]

def matplotlib_warning_options(rules):
    if rules not in ([],MPL_WARNING_RULES):raise ValueError("unapproved Matplotlib warning compatibility")
    return [arg for rule in rules for arg in ("-W","ignore:"+rule["message"]+":"+rule["category"]+":"+rule["module"])]



def matplotlib_assets(runtime,bindings):
    if set(runtime) not in ({'image','projection','native_overlays'},{'image','projection','native_overlays','warning_compatibility'}) or runtime['image']!=IMAGE:raise ValueError('Matplotlib runtime schema changed')
    compatibility=runtime.get('warning_compatibility');prior=None
    if compatibility is not None:
        if set(compatibility)!={'version','origin_failure','origin_log','prior_code_snapshot','rules'} or compatibility['version']!='cached_pkg_resources_warning_compat_v1' or compatibility['rules']!=MPL_WARNING_RULES:raise ValueError('unapproved warning compatibility')
        origin=checked(compatibility['origin_failure'],bindings);snap=checked(compatibility['prior_code_snapshot'],bindings)
        for entry in snap['files']:
            file=safe(entry['snapshot']['path'])
            if sha(file)!=entry['snapshot']['sha256']:raise ValueError('prior code snapshot changed')
            bindings[str(file)]=entry['snapshot']['sha256']
        logref=compatibility['origin_log'];log=safe(logref['path'])
        if set(logref)!={'path','sha256'} or sha(log)!=logref['sha256'] or b'pkg_resources is deprecated as an API' not in log.read_bytes() or origin['status']!='ERROR' or origin['container_runs']!=1:raise ValueError('warning origin failure differs')
        bindings[str(log)]=logref['sha256'];prior=dict(receipt=compatibility['origin_failure'],container_runs=origin['container_runs'],seconds=origin['seconds'])
    helper_path=HERE/'qualify_swe_contextbench_matplotlib_20261106.py';deps_path=HERE.parents[1]/'scripts/graph/research_actor_dependencies.py'
    for path,digest in ((helper_path,MPL_HELPER_SHA),(deps_path,MPL_DEPS_SHA)):
        if sha(path)!=digest:raise ValueError('Matplotlib helper changed')
        bindings[str(path)]=digest
    inserted=[str(p) for p in (HERE,HERE.parents[1]) if str(p) not in sys.path]
    sys.path[:0]=inserted
    try:
        helper=importlib.import_module('qualify_swe_contextbench_matplotlib_20261106')
        deps=importlib.import_module('scripts.graph.research_actor_dependencies')
    finally:
        for path in inserted:sys.path.remove(path)
    manifest=checked(runtime['projection'],bindings);directory=Path(runtime['projection']['path']).parent
    if (manifest['python'],manifest['blocked_packages'],manifest['site_names'])!=('3.10',['matplotlib','mpl_toolkits'],['source','target']):raise ValueError('Matplotlib projection differs')
    actor=deps.verify_projection(directory,runtime['projection']['sha256'])
    for name,entry in manifest['files'].items():bindings[str(safe(directory/name))]=entry['sha256']
    if set(runtime['native_overlays'])!={'source','target'} or set(manifest['source_site_paths'])!={'source','target'}:raise ValueError('Matplotlib dependency slots differ')
    overlays={}
    for slot,ref in runtime['native_overlays'].items():
        expected=checked(ref,bindings);site=safe(manifest['source_site_paths'][slot]);native=site/'matplotlib'
        files=[*native.rglob('*.so'),native/'_version.py'];actual={p.relative_to(native).as_posix():sha(safe(p)) for p in files}
        if not expected or actual!=expected:raise ValueError('cached native overlay differs from frozen original receipt')
        for name,digest in actual.items():bindings[str(native/name)]=digest
        overlays[slot]=actual
    return dict(runtime=actor['runtime'],sites=actor['sites'],native_sites=manifest['source_site_paths'],overlays=overlays,helper=helper,warning_rules=compatibility['rules'] if compatibility else [],prior_environment_control=prior)


def matplotlib_archive(path,revision):
    prefix='matplotlib-'+revision;seen=set();license=False
    with tarfile.open(path,'r:gz') as tf:
        for member in tf:
            q=PurePosixPath(member.name)
            if q.is_absolute() or '..' in q.parts or not q.parts or q.parts[0]!=prefix or '.git' in q.parts or member.name in seen:raise ValueError('unsafe Matplotlib archive path')
            seen.add(member.name)
            if member.issym():
                target=PurePosixPath(member.linkname)
                if len(target.parts)!=1 or target.name in ('.','..') or not tf.getmember(str(q.parent/target)).isfile():raise ValueError('unsafe Matplotlib archive link')
            elif not(member.isfile() or member.isdir()):raise ValueError('unsafe Matplotlib archive member')
            if member.isfile() and 'LICENSE' in q.parts[1:]:license=True
    if not license:raise ValueError('Matplotlib archive license missing')


def resolve_matplotlib_nodes(module, source, published):
    """Inspect one public test module; never execute or extract a function body."""
    paths=set()
    def definitions(body, classes=()):
        for node in body:
            if isinstance(node,ast.ClassDef):definitions(node.body,classes+(node.name,))
            elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):paths.add(classes+(node.name,))
    definitions(ast.parse(source).body);resolved=[]
    for label in mapped_labels('matplotlib/matplotlib',published):
        file,*parts=label.split('::');name=parts[-1].split('[',1)[0];suffix=parts[-1][len(name):]
        if file!=module or not re.fullmatch(r'[A-Za-z_]\w*',name) or (suffix and not suffix.endswith(']')):raise ValueError('invalid AST published node')
        exact=tuple(parts[:-1]+[name])
        if exact in paths:chosen=exact
        else:
            matches=[path for path in paths if path[-1]==name] if len(parts)==1 else []
            if len(matches)!=1:raise ValueError('missing or ambiguous public AST function path: '+label)
            chosen=matches[0]
        resolved.append(module+'::'+'::'.join((*chosen[:-1],chosen[-1]+suffix)))
    if len(resolved)!=len(set(resolved)):raise ValueError('published labels alias one exact AST node')
    return resolved


def load_matplotlib_pair(c,bindings,output):
    ast_mode=c['schema']=='contextbench_pool_qualification_matplotlib_pair_v2'
    if set(c)!=({'schema','dataset_manifest','ancestry','selection','cases','runtime'}|({'mapping_origin'} if ast_mode else set())):raise ValueError('Matplotlib pair schema changed')
    prior=[];caps=dict(container_runs=4,group_seconds=600,seconds=1800);mapping_counts={}
    if ast_mode:
        origin=c['mapping_origin']
        if (set(origin)!={'policy','prior_runs','prior_code_snapshot','caps','target_task_nature'} or origin['policy']!='exact_or_unique_ast_class_path_v1' or origin['caps']!=dict(container_runs=4,group_seconds=300,seconds=900) or origin['target_task_nature']!='maintenance_followup_not_independent_bug' or len(origin['prior_runs'])!=2):raise ValueError('invalid AST mapping origin/caps')
        caps=origin['caps']
        for ref in origin['prior_runs']:
            record=checked(ref,bindings)
            if record['status']!='ERROR' or type(record['container_runs']) is not int or record['container_runs']<0:raise ValueError('prior qualification identity differs')
            prior.append(dict(receipt=ref,container_runs=record['container_runs'],seconds=record['seconds']))
        if sum(x['container_runs'] for x in prior)!=4:raise ValueError('historical container ledger differs')
        snapshot=checked(origin['prior_code_snapshot'],bindings)
        for item in snapshot['files']:
            file=safe(item['snapshot']['path'])
            if sha(file)!=item['snapshot']['sha256']:raise ValueError('pre-mapping source snapshot changed')
            bindings[str(file)]=item['snapshot']['sha256']
    if [x['instance_id'] for x in c['cases']]!=list(MPL_CASES):raise ValueError('duplicate/unknown/misordered Matplotlib pair')
    h,d=helpers();dataset=checked(c['dataset_manifest'],bindings)
    if Path(c['dataset_manifest']['path']).parent!=h.DATA:raise ValueError('dataset helper root differs')
    for item in dataset['files']:
        if Path(item['name']).name!=item['name']:raise ValueError('unsafe dataset basename')
        path=safe(h.DATA/item['name'])
        if sha(path)!=item['sha256']:raise ValueError('dataset changed')
        bindings[str(path)]=item['sha256']
    selection=checked(c['selection'],bindings);ancestry=checked(c['ancestry'],bindings)
    chosen=[p for p in selection['pairs'] if p['source']['instance_id']==list(MPL_CASES)[0] and p['target']['instance_id']==list(MPL_CASES)[1]]
    ancestors=[p for p in ancestry['results'] if p.get('repo')=='matplotlib/matplotlib' and p.get('source')==list(MPL_CASES)[0] and p.get('target')==list(MPL_CASES)[1]]
    if (ancestry.get('schema')!='code_source_second_wave_ancestry_v1' or ancestry.get('selection_sha256')!=c['selection']['sha256'] or len(chosen)!=1 or len(ancestors)!=1 or ancestors[0]['status']!='ANCESTRY_PASS_METADATA_ONLY' or ancestors[0]['target_base']!=MPL_CASES[list(MPL_CASES)[1]][0]):raise ValueError('Matplotlib ancestry differs')
    assets=matplotlib_assets(c['runtime'],bindings);cases=[]
    for spec in c['cases']:
        if set(spec)!=({'instance_id','repo','base_commit','dataset_file','role','archive','dependency_slot','problem_sha256','label_map'}|({'node_source'} if ast_mode else set())):raise ValueError('invalid Matplotlib case spec')
        revision,role,data,f2p,ptp,module=MPL_CASES[spec['instance_id']]
        if spec['repo']!='matplotlib/matplotlib' or (spec['base_commit'],spec['role'],spec['dataset_file'])!=(revision,role,data) or spec['dependency_slot'] not in ('source','target'):raise ValueError('Matplotlib source/target identity differs')
        if any(chosen[0][role][k]!=spec[k] for k in ('instance_id','repo','base_commit')):raise ValueError('selected Matplotlib identity differs')
        if spec['dataset_file'] not in [x['name'] for x in dataset['files']]:raise ValueError('Matplotlib dataset absent')
        row=h.dataset_row(dict(id=spec['instance_id'],rev=revision,data=data))
        if hashlib.sha256(row['problem_statement'].encode()).hexdigest()!=spec['problem_sha256']:raise ValueError('raw public problem hash differs')
        mapping=spec['label_map'];labels={};resolved={}
        if ast_mode:
            ref=spec['node_source'];file=safe(ref['path'])
            if set(ref)!={'path','sha256'} or sha(file)!=ref['sha256']:raise ValueError('public AST source changed')
            bindings[str(file)]=ref['sha256'];published=json.loads(row['FAIL_TO_PASS'])+json.loads(row['PASS_TO_PASS']);nodes=resolve_matplotlib_nodes(module,file.read_text(),published)
            resolved=dict(zip(published,nodes));mapping_counts[spec['instance_id']]=sum(a!=b for a,b in zip(published,nodes))
        if type(mapping) is not dict or set(mapping)!={'f2p','ptp'} or module not in {x[6:] for x in row['test_patch'].splitlines() if x.startswith('+++ b/')}:raise ValueError('Matplotlib published test module differs')
        for suite,field in [('f2p','FAIL_TO_PASS'),('ptp','PASS_TO_PASS')]:
            published=json.loads(row[field]);entries=mapping[suite]
            if type(entries) is not list or any(type(e) is not dict or set(e)!={'published','node'} for e in entries) or [e['published'] for e in entries]!=published or any(e['node']!=(resolved[e['published']] if ast_mode else e['published']) or e['node'].split('::')[0]!=module for e in entries):raise ValueError('Matplotlib node map must be exact, ordered and complete')
            labels[suite]=mapped_labels('matplotlib/matplotlib',[e['node'] for e in entries])
        if (len(labels['f2p']),len(labels['ptp']))!=(f2p,ptp) or len(set(labels['f2p']+labels['ptp']))!=f2p+ptp:raise ValueError('Matplotlib published counts/aliases differ')
        ref=spec['archive'];path=safe(ref['path'])
        if set(ref)!={'path','sha256'} or sha(path)!=ref['sha256']:raise ValueError('Matplotlib archive changed')
        bindings[str(path)]=ref['sha256'];matplotlib_archive(path,revision);cases.append(dict(spec=spec,row=row,labels=labels))
    bindings[str(Path(__file__).resolve())]=sha(__file__)
    bindings.update({str(HERE/(name+'.py')):digest for name,digest in PINS.items()})
    return dict(mode='matplotlib_pair',contract=c,bindings=bindings,cases=cases,helpers=(h,d),assets=assets,caps=caps,mapping_counts=mapping_counts,prior_controls=prior,limits='Frozen Python3.10 projected runtime/deps; project Python from exact archives only. Original released-wheel native extensions plus absent generated _version.py are explicitly overlaid; not a native build of either base commit.',output=output)


def exact_coverage(labels,record):
    value=record.get('result') or {};tests=value.get('tests') or {}
    return dict(labels={n:tests.get(n,'missing') for n in labels},reported_tests=len(tests),extra_ids=sorted(set(tests)-set(labels)),complete=not value.get('fatal') and set(tests)==set(labels) and all(x in ('passed','failed') for x in tests.values()) and record.get('exit') in (0,1))


def matplotlib_qualification(base,gold,labels):
    flat=labels['f2p']+labels['ptp'];coverage=[exact_coverage(flat,x) for x in (base,gold)];checks={}
    for index,(name,arm,suite,state) in enumerate([('base_all_f2p_reproduced',0,'f2p','failed'),('gold_all_f2p_pass',1,'f2p','passed'),('base_all_ptp_pass',0,'ptp','passed'),('gold_all_ptp_pass',1,'ptp','passed')]):
        checks[name]=coverage[arm]['complete'] and all(coverage[arm]['labels'][n]==state for n in labels[suite])
    return dict(qualified=all(checks.values()) and base.get('exit')==1 and gold.get('exit')==0,**checks)


def matplotlib_command(work,labels,runner,name,cidfile,assets,slot):
    cmd=['docker','run','--name',name,'--cidfile',str(cidfile),'--rm','--pull','never','--network','none','--read-only','--cpus','1','--memory','4g','--pids-limit','256','--cap-drop','ALL','--security-opt','no-new-privileges','--user',str(os.getuid())+':'+str(os.getgid()),'--tmpfs','/tmp:rw,nosuid,size=512m','-e','HOME=/tmp','-e','MPLBACKEND=Agg','-e','MPLCONFIGDIR=/tmp/mpl','-e','PYTHONPATH=/workspace/lib:/deps','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1','--workdir','/tmp']
    for src,dst in ((work,'/workspace'),(assets['sites'][slot],'/deps'),(assets['runtime'],'/extra'),(runner,'/qualifier.py')):cmd+=['--mount','type=bind,src='+str(src)+',dst='+dst+',readonly']
    options=matplotlib_warning_options(assets.get('warning_rules',[]))
    policy=['--warning-options='+json.dumps(options)] if options else []
    return cmd+['--entrypoint','/extra/bin/python',IMAGE,'/qualifier.py','matplotlib',*policy,*labels]


def matplotlib_cleanup(cidfile,name):
    cid=Path(cidfile).read_text().strip()
    if not re.fullmatch('[0-9a-f]{64}',cid):raise ValueError('unknown owned Matplotlib CID')
    inspected=subprocess.run(['docker','inspect','--format','{{json .Name}}',cid],capture_output=True,timeout=15)
    if inspected.returncode:
        if any(x in inspected.stderr.lower() for x in (b'no such object',b'no such container')):return dict(cid=cid,status='ALREADY_REMOVED')
        raise ValueError('Matplotlib CID ownership not proven')
    if json.loads(inspected.stdout)!='/'+name:raise ValueError('Matplotlib CID ownership differs')
    removed=subprocess.run(['docker','rm','-f',cid],capture_output=True,timeout=15)
    if removed.returncode:raise RuntimeError('owned Matplotlib cleanup failed')
    return dict(cid=cid,status='REMOVED_OWNED',exit=removed.returncode)


def run_matplotlib_group(work,labels,runner,log,assets,slot,timeout):
    available=mem_available()
    if available<4*1024**3:return dict(status='DEFERRED',MemAvailable=available)
    name='cb-mpl-'+str(os.getpid())+'-'+str(time.monotonic_ns());cid=log.with_suffix('.cid');cmd=matplotlib_command(work,labels,runner,name,cid,assets,slot);started=time.monotonic();record=dict(exit=None,MemAvailable=available,container_started=False);proc=None
    new(log.with_suffix('.command.json'),dict(argv=cmd,container=name,cidfile=str(cid),timeout_seconds=timeout))
    with log.open('xb') as out:
        try:
            proc=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT);record['container_started']=True;record['exit']=proc.wait(timeout=timeout)
        except BaseException as exc:record['error']=dict(type=type(exc).__name__,message=str(exc))
        finally:
            if proc is not None:
                try:record['cleanup']=matplotlib_cleanup(cid,name)
                except BaseException as exc:record.update(status='CLEANUP_FAILED',cleanup_error=dict(type=type(exc).__name__,message=str(exc)))
                if proc.poll() is None:
                    try:proc.wait(timeout=15)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=15)
    raw=log.read_bytes();markers=[line[len(MARKER):] for line in raw.decode(errors='replace').splitlines() if line.startswith(MARKER)]
    try:record['result']=json.loads(markers[0]) if len(markers)==1 else dict(fatal=['missing/duplicate machine result'])
    except ValueError:record['result']=dict(fatal=['invalid machine result'])
    record.update(seconds=time.monotonic()-started,log_sha256=sha(log));record['coverage']=exact_coverage(labels,record);return record


def execute_matplotlib_pair(c):
    out=c['output'];out.mkdir();h,_=c['helpers'];assets=c['assets'];runner=out/'qualifier.py';runner.write_text(RUNNER);started=time.monotonic();caps=c.get('caps',dict(container_runs=4,group_seconds=600,seconds=1800));deadline=started+caps['seconds']
    result=dict(status='STARTED',schema='matplotlib_pair_qualification_result_v1',input_sha256=c['bindings'],runner_sha256=sha(runner),dependency_limits=c['limits'],model_calls=0,training=0,container_runs=0,cases={},target_reference_use='EVAL_ONLY gold controls; no actor/writer/experience input')
    result['caps']=caps;result['mapping_counts']=c.get('mapping_counts',{});result['prior_controls']=c.get('prior_controls',[]);result['target_task_nature']=c['contract'].get('mapping_origin',{}).get('target_task_nature')
    result['warning_compatibility']=c['contract']['runtime'].get('warning_compatibility')
    result['prior_environment_control']=assets.get('prior_environment_control')
    try:
        for case in c['cases']:
            if mem_available()<4*1024**3:result['status']='DEFERRED';break
            spec,row,labels=case['spec'],case['row'],case['labels'];root=out/spec['instance_id'];root.mkdir();base=root/'clean_base'
            extraction=assets['helper'].extract(Path(spec['archive']['path']),base,spec['base_commit']);raw_tree=tree(base);overlay=assets['helper'].overlay(base,Path(assets['native_sites'][spec['dependency_slot']]))
            if overlay!=assets['overlays'][spec['dependency_slot']]:raise ValueError('applied native overlay differs')
            clean=tree(base)
            for name,field in [('task.txt','problem_statement'),('test.patch','test_patch'),('reference.patch','patch')]:
                with (root/name).open('xb') as f:f.write(row[field].encode())
            record=dict(spec=spec,extraction=extraction,archive_tree_sha256=raw_tree,native_overlay=overlay,clean_base_sha256=clean,input_sha256={n:sha(root/n) for n in ('task.txt','test.patch','reference.patch')},labels=labels,arms={});result['cases'][spec['instance_id']]=record
            for arm in ('base_with_tests','gold_with_tests'):
                if result['container_runs']>=caps['container_runs']:raise RuntimeError('qualification container cap')
                if any(sha(p)!=digest for p,digest in c['bindings'].items()):raise ValueError('frozen Matplotlib input changed')
                timeout=min(caps['group_seconds'],deadline-time.monotonic()-60)
                if timeout<=0:raise TimeoutError('qualification wall deadline')
                work=root/arm;shutil.copytree(base,work);a=dict(test_patch=patched(h,work,row['test_patch'],root/'test.patch'));record['arms'][arm]=a
                if a['test_patch']['apply_exit']!=0:raise ValueError('published test patch did not apply')
                if arm=='gold_with_tests':
                    a['reference_patch']=patched(h,work,row['patch'],root/'reference.patch')
                    if a['reference_patch']['apply_exit']!=0:raise ValueError('EVAL_ONLY reference patch did not apply')
                if 'node_source' in spec:
                    module=MPL_CASES[spec['instance_id']][-1]
                    if sha(work/module)!=spec['node_source']['sha256']:raise ValueError('actual base/gold public test module differs from AST-bound source')
                a['tree_sha256']=tree(work);a['group']=run_matplotlib_group(work,labels['f2p']+labels['ptp'],runner,root/(arm+'.log'),assets,spec['dependency_slot'],timeout)
                result['container_runs']+=int(a['group'].get('container_started',False))
                for suite in ('f2p','ptp'):
                    tests=(a['group'].get('result') or {}).get('tests') or {};a[suite]=dict(group_exit=a['group'].get('exit'),tests={n:tests.get(n,'missing') for n in labels[suite]})
                if a['group'].get('status')=='DEFERRED':result['status']='DEFERRED';break
                if a['group'].get('error') or a['group'].get('cleanup_error') or not a['group'].get('coverage',exact_coverage(labels['f2p']+labels['ptp'],a['group']))['complete']:raise RuntimeError('incomplete/invalid Matplotlib group; preserve raw and stop')
            if tree(base)!=clean:raise ValueError('clean source/base changed')
            record['qualification']=matplotlib_qualification(record['arms'].get('base_with_tests',{}).get('group',{}),record['arms'].get('gold_with_tests',{}).get('group',{}),labels)
            if result['status']=='DEFERRED':break
        if result['status']!='DEFERRED':result['status']='QUALIFIED' if len(result['cases'])==2 and all(v['qualification']['qualified'] for v in result['cases'].values()) else 'NOT_QUALIFIED'
    except BaseException as exc:result.update(status='ERROR',error=dict(type=type(exc).__name__,message=str(exc)))
    finally:
        result['unrun_groups']=[dict(case=x['spec']['instance_id'],arm=arm) for x in c['cases'] for arm in ('base_with_tests','gold_with_tests') if not result['cases'].get(x['spec']['instance_id'],{}).get('arms',{}).get(arm,{}).get('group',{}).get('container_started',False)]
        result['total_container_runs_all_attempts']=result['container_runs']+sum(x['container_runs'] for x in c.get('prior_controls',[]))
        result['prior_controls_seconds']=sum(x['seconds'] for x in c.get('prior_controls',[]))
        result['total_container_runs_including_prior_environment_control']=result['container_runs']+(assets.get('prior_environment_control') or {}).get('container_runs',0)
        result['seconds']=time.monotonic()-started;result['total_seconds_including_prior_environment_control']=result['seconds']+(assets.get('prior_environment_control') or {}).get('seconds',0);result['unrun_cases']=[x['spec']['instance_id'] for x in c['cases'] if x['spec']['instance_id'] not in result['cases']];new(out/'receipt.json',result)
    return result





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
        elif (repo=='sympy/sympy' and parts[0].startswith('sympy/')) or (repo=='matplotlib/matplotlib' and parts[0].startswith('lib/matplotlib/tests/')):mapped.append(label)
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
    if c.get('schema') in ('contextbench_pool_qualification_matplotlib_pair_v1','contextbench_pool_qualification_matplotlib_pair_v2'):return load_matplotlib_pair(c,bindings,output)
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
kind=sys.argv[1];labels=sys.argv[2:];result={'tests':{},'fatal':[]};warning_options=[]
if kind=='matplotlib' and labels and labels[0].startswith('--warning-options='):warning_options=json.loads(labels.pop(0).split('=',1)[1])
def status(test,value):result['tests'][test]=value
def error_kind(test,err):
 return 'error' if issubclass(err[0],(ImportError,SyntaxError)) or test.__class__.__name__.startswith('_') else 'failed'
try:
 assert sys.version_info[:2]==((3,10) if kind=='matplotlib' else (3,8)), 'wrong historical Python runtime'
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
  if kind=='matplotlib':
   import matplotlib,numpy
   from pathlib import Path
   assert Path(matplotlib.__file__).resolve().is_relative_to(Path('/workspace/lib')), 'project Python escaped clean source tree'
   result['runtime']={'python':sys.version,'matplotlib':matplotlib.__version__,'matplotlib_file':matplotlib.__file__,'numpy':numpy.__version__,'backend':matplotlib.get_backend()}
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
  args=warning_options+['--rootdir=/workspace']+['/workspace/'+n for n in labels] if kind=='matplotlib' else labels
  code=pytest.main(['-q','-p','no:cacheprovider']+args,plugins=[Plugin()])
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
    if c.get('mode')=='matplotlib_pair':return execute_matplotlib_pair(c)
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
