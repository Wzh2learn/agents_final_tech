#!/usr/bin/env python3
"""Frozen, source-only experience formation and matched SymPy transfer arms.

Existing runners remain untouched. Small private function adapters bind their
explicit source literals to the qualified target; every adaptation is recorded.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
import hashlib
import http.client
import inspect
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import run_sympy_latex_agent_20261106 as source
import prepare_django_aggregation_experience_20261106 as rendering
from run_swe_contextbench_sphinx_20261105 import inspect_experience_reads

PARENT = source.PARENT
SOURCE = PARENT/'attempts/teacher27_source_v1'
SOURCE_SHA = '9d3d0e74502346202ab76bf4bef859eeb2bc8a06940ddf80a8038555e5e72a7e'
EXPERIENCE = PARENT/'source_experience_v1'
TARGETS = PARENT/'transfer_attempts'
TARGET_BASE = '226b942f0748819d5d2d723b91591fed4975961c'
STUDENT_PROFILE = source.PRIVATE/'django_aggregation_agent_20261106/model_profile.json'
STUDENT_SHA = 'acce24743e43c205b605b8bceddd4f5eb756d93fdba5f58e28bc32ba772ab6d0'
TARGET_HASHES = {'patch':'29f89ebf3661c4f2ac79f78ebfd261496a97c571474eb362add78de40155b0b6',
 'test_patch':'cbfe6c47680a45a2b532ccaa50b35e6c54f262297c0fbc20e6fa56998beb26a8',
 'problem_statement':'daee201cddfd6c378587e897a5104d7104a1b71a790a529190b3220cf3f8219d'}
NODES_SHA = '66cf54285fe4099dbbbd3adf8b703f92849c4e7e155ec01f14f95d453f247ac9'
EXCLUDED = ['sympy/printing/tests/test_latex.py::test_issue_13559',
            'sympy/printing/tests/test_latex.py::test_issue_8470']
MARKERS = ('sympy__sympy-19235','/pull/19235','/issues/19235','#19235','gh-19235')
CONDITIONS = ('none','source_history','feedback_card','generated_skill')
EXPERIENCE_NAMES = {'source_history.md','feedback_card.md','generated_skill.md','draft_manifest.json',
                   'skill_generation_request.json','skill_generation_response.json','skill_generation_ledger.json'}
sha, read, write_new = source.sha, source.read, source.write_new


def adapt(function, replacements=(), **bindings):
    """Bind an independent namespace and checked literal changes, never globals."""
    tree = ast.parse(inspect.getsource(function)); counts = [0]*len(replacements)
    class Literals(ast.NodeTransformer):
        def visit_Constant(self,node):
            for i,(old,new,count) in enumerate(replacements):
                if type(node.value) is type(old) and node.value == old:
                    counts[i]+=1;return ast.copy_location(ast.Constant(new),node)
            return node
    tree = Literals().visit(tree);ast.fix_missing_locations(tree)
    if counts != [count for _,_,count in replacements]: raise ValueError('adapter literal contract changed')
    namespace = dict(function.__globals__);namespace.update(bindings)
    exec(compile(tree,'<private-sympy-adapter>','exec'),namespace)
    return namespace[function.__name__]


def no_target_started():
    if TARGETS.exists() and any(TARGETS.iterdir()):
        raise ValueError('target preparation already exists; source formation is closed')


def source_evidence():
    completed = SOURCE/(source.EID+'.completed.json')
    if sha(completed) != SOURCE_SHA: raise ValueError('source completion changed')
    record = read(completed);started = read(SOURCE/(source.EID+'.started.json'))
    manifest = read(SOURCE/'inputs_manifest.json')
    if sha(SOURCE/'inputs_manifest.json') != record['inputs_manifest_sha256']:
        raise ValueError('archived source input manifest changed')
    if (manifest['component_sha256'] != started['component_sha256'] or
            sha(SOURCE/'inputs/source/task.txt') != record['task_sha256'] or
            sha(SOURCE/'frozen_source_harness.py') != record['harness_sha256'] or
            sha(SOURCE/(source.EID+'.harness.py')) != record['harness_sha256'] or
            sha(SOURCE/'model_profile.json') != record['model_profile_sha256']):
        raise ValueError('archived source bindings changed')
    clean = SOURCE/'inputs/source/clean_base'
    source.checked_qualification()
    source.verify_clean(clean,source.QUAL/'source.tar.gz')
    if source.tree(clean) != manifest['baseline_tree']: raise ValueError('archived baseline changed')
    def baseline(_):return {'archive_sha256':manifest['baseline_archive_sha256'],'base':source.SOURCE_BASE}
    evidence_fn = adapt(rendering.source_evidence,
        [('post_run_evaluation_restored_tests','post_run_evaluation',1)], MARKERS=MARKERS)
    evidence = evidence_fn(SOURCE,clean,verify_baseline=baseline)
    case = SOURCE/source.EID;detail = read(case/'receipt.json')
    sampling=[json.loads(line) for line in (case/'sampling_metadata.jsonl').read_text().splitlines()]
    if Counter(json.dumps(m,sort_keys=True) for m in sampling)!=Counter(json.dumps(m,sort_keys=True) for m in detail['sampling_metadata']):
        raise ValueError('source sampling log changed')
    for entry in sampling:
        payload=read(case/'model_request_bodies'/entry['request_body_file'])
        if (payload.get('model'),payload.get('seed'),payload.get('temperature'))!=('qwen38-27b-fp8',7201,.2):
            raise ValueError('source model/sampling payload changed')
    if read(case/'post_run_evaluation/receipt.json')!=record['post_run_evaluation']:
        raise ValueError('source independent evaluation receipt changed')
    integrity = source.execution_integrity(case,detail)
    usage = source.primitives.provider_usage(case,detail)
    if (not integrity['passed'] or integrity['counted_posts'] != record['posts']
            or usage != record['provider_usage'] or not record['source_artifact_qualification']['passed']):
        raise ValueError('source integrity, provider usage or independent outcome changed')
    raw_steps = [event['part']['tokens'] for event in map(json.loads,(case/'raw.jsonl').read_text().splitlines())
                 if event.get('type') == 'step_finish']
    if raw_steps != detail['step_finish_tokens']: raise ValueError('source raw usage changed')
    source.dependencies.verify_projection(PARENT/'actor_python38',record['projection_sha256'])
    evidence['outcome'].update(provider_usage=usage,execution_integrity=integrity,
                               source_artifact_qualification=record['source_artifact_qualification'])
    return evidence


def prepare_source():
    no_target_started();ev = source_evidence()
    if EXPERIENCE.exists(): raise FileExistsError('preserve existing source artifacts')
    EXPERIENCE.mkdir()
    for name,label,history in [('source_history.md','Source-only ordinary history.',True),
                               ('feedback_card.md','Observed source edit and source outcome.',False)]:
        (EXPERIENCE/name).write_text(rendering.body(label,ev,history=history),encoding='utf8')
    manifest = {'status':'DRAFT','source':ev['provenance'],'history_rendering_version':2,
                'artifacts':{name:sha(EXPERIENCE/name) for name in ('source_history.md','feedback_card.md')},
                'scope':'exposed development; source issue supplies a fix hint; no target or gold input'}
    write_new(EXPERIENCE/'draft_manifest.json',manifest)
    return manifest


def validate_draft():
    draft=read(EXPERIENCE/'draft_manifest.json');ev=source_evidence()
    if draft['source'] != ev['provenance'] or draft['history_rendering_version'] != 2:
        raise ValueError('source draft binding changed')
    for name,label,history in [('source_history.md','Source-only ordinary history.',True),
                               ('feedback_card.md','Observed source edit and source outcome.',False)]:
        if (sha(EXPERIENCE/name) != draft['artifacts'][name] or
                (EXPERIENCE/name).read_text(encoding='utf8') != rendering.body(label,ev,history=history)):
            raise ValueError('source draft rendering changed')
    return draft


def skill_payload():
    return {'model':'qwen38-27b-fp8','temperature':.2,'seed':7201,'max_tokens':2500,'stream':False,
        'messages':[{'role':'system','content':'Create concise reusable instructions from this source-only execution and '
          'measured feedback. Distinguish successes, actual failures and uncertainty. Do not invent a future task. Return only skill text.'},
          {'role':'user','content':(EXPERIENCE/'source_history.md').read_text(encoding='utf8')}]}


def retain_response(response,path):
    with path.open('xb') as stream:
        while True:
            try:block=response.read(65536)
            except http.client.IncompleteRead as exc:
                stream.write(exc.partial);raise
            if not block:break
            stream.write(block);stream.flush()
    if getattr(response,'length',0) not in (None,0):raise http.client.IncompleteRead(b'',response.length)
    return path.read_bytes()


def generate_skill():
    no_target_started();draft=validate_draft()
    ledger_path=EXPERIENCE/'skill_generation_ledger.json'
    if any((EXPERIENCE/name).exists() for name in ('skill_generation_request.json','skill_generation_response.json',
                                                  'skill_generation_ledger.json','generated_skill.md')):
        raise FileExistsError('skill generation already attempted; never retry automatically')
    profile=source.teacher.validate_vllm_model_profile(source.PROFILE,source.PROFILE_SHA,full=False)
    backend=source.teacher.verify_vllm_backend(profile)
    payload=skill_payload()
    request=EXPERIENCE/'skill_generation_request.json';request.write_bytes(json.dumps(payload,ensure_ascii=False).encode())
    ledger={'status':'ATTEMPT_STARTED','physical_http_attempts':1,'model_profile_sha256':source.PROFILE_SHA,
            'source_history_sha256':sha(EXPERIENCE/'source_history.md'),'request_sha256':sha(request),'backend':backend}
    write_new(ledger_path,ledger)
    connection=http.client.HTTPConnection(profile['host'],profile['port'],timeout=900)
    try:
        connection.request('POST','/v1/chat/completions',body=request.read_bytes(),headers={'Content-Type':'application/json'})
        response=connection.getresponse();ledger['http_status']=response.status
        path=EXPERIENCE/'skill_generation_response.json';raw=retain_response(response,path)
        ledger['response_sha256']=sha(path)
        parsed=json.loads(raw);ledger['provider_usage']=parsed.get('usage')
        if response.status != 200:raise ValueError('skill generation HTTP failure')
        choice=parsed['choices'][0];text=choice['message']['content']
        if choice.get('finish_reason') != 'stop' or not isinstance(text,str) or not text.strip():
            raise ValueError('skill output empty or truncated')
        if any(marker.casefold() in text.casefold() for marker in MARKERS):raise ValueError('skill contains future target identity')
        with (EXPERIENCE/'generated_skill.md').open('x',encoding='utf8') as stream:stream.write(text.strip()+'\n')
        ledger.update(status='RECEIVED',skill_sha256=sha(EXPERIENCE/'generated_skill.md'))
    except Exception as exc:
        ledger.update(status='FAILED_RETAINED_RAW_OR_UNKNOWN_USAGE',error_type=type(exc).__name__);raise
    finally:
        if (EXPERIENCE/'skill_generation_response.json').exists():
            ledger['response_sha256']=sha(EXPERIENCE/'skill_generation_response.json')
        connection.close();ledger_path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8')
    return ledger


def validate_skill():
    ledger=read(EXPERIENCE/'skill_generation_ledger.json')
    for field,name in [('request_sha256','skill_generation_request.json'),('response_sha256','skill_generation_response.json'),
                        ('skill_sha256','generated_skill.md')]:
        if ledger.get(field) != sha(EXPERIENCE/name):raise ValueError('skill evidence changed')
    request=read(EXPERIENCE/'skill_generation_request.json');response=read(EXPERIENCE/'skill_generation_response.json')
    choice=response['choices'][0];text=choice['message']['content']
    if (ledger.get('status')!='RECEIVED' or ledger.get('physical_http_attempts')!=1 or ledger.get('http_status')!=200
            or ledger.get('model_profile_sha256')!=source.PROFILE_SHA or request.get('model')!='qwen38-27b-fp8'
            or request!=skill_payload()
            or request['messages'][-1]['content']!=(EXPERIENCE/'source_history.md').read_text(encoding='utf8')
            or ledger.get('source_history_sha256')!=sha(EXPERIENCE/'source_history.md')
            or choice.get('finish_reason')!='stop' or text.strip()+'\n'!=(EXPERIENCE/'generated_skill.md').read_text(encoding='utf8')
            or ledger.get('provider_usage')!=response.get('usage') or any(m.casefold() in text.casefold() for m in MARKERS)):
        raise ValueError('skill is not the recorded source-only 27B output')
    return ledger


def freeze_source():
    no_target_started();draft=validate_draft();validate_skill()
    manifest={'status':'FROZEN_BEFORE_TARGET','source':draft['source'],
              'artifacts':{name:sha(EXPERIENCE/name) for name in sorted(EXPERIENCE_NAMES)},'scope':draft['scope']}
    write_new(EXPERIENCE/'frozen_manifest.json',manifest);return manifest


def frozen_source(digest):
    if sha(EXPERIENCE/'frozen_manifest.json')!=digest:raise ValueError('frozen source manifest changed')
    frozen=read(EXPERIENCE/'frozen_manifest.json');draft=validate_draft();validate_skill()
    if (frozen['status']!='FROZEN_BEFORE_TARGET' or frozen['source']!=draft['source'] or
            set(frozen['artifacts'])!=EXPERIENCE_NAMES or
            any(sha(EXPERIENCE/name)!=value for name,value in frozen['artifacts'].items())):
        raise ValueError('frozen source artifacts changed')
    return frozen


def target_row():
    source.checked_qualification();row=read(source.QUAL/'target_row.json')
    if (row['instance_id'],row['base_commit'])!=('sympy__sympy-19235',TARGET_BASE) or any(
        hashlib.sha256(row[key].encode()).hexdigest()!=value for key,value in TARGET_HASHES.items()):
        raise ValueError('target qualification row changed')
    path=source.QUAL/'target/regression_nodes_qualified.json'
    if sha(path)!=NODES_SHA:raise ValueError('target regression subset changed')
    nodes=json.loads(path.read_text())
    if len(nodes)!=142 or len(set(nodes))!=142 or set(nodes)&set(EXCLUDED):raise ValueError('wrong target regression scope')
    return row,nodes


def target_evaluator():
    _,nodes=target_row()
    evaluate=adapt(source.evaluate,[(114,142,1),('/probe_source.py,dst=/probe.py,readonly','/probe_target.py,dst=/probe.py,readonly',1)],
                   regression_nodes=lambda row,clean:nodes)
    def independent(work,output,actor,row,clean):
        configs={'conftest.py','pytest.ini','setup.cfg','tox.ini','pyproject.toml'}
        if any(path.is_symlink() for path in work.rglob('*')):raise ValueError('candidate symlink')
        with tempfile.TemporaryDirectory(prefix='sympy-eval-') as temporary:
            staged=Path(temporary)/'candidate';shutil.copytree(work,staged,
                ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache'))
            for path in staged.rglob('*'):
                if path.is_file() and path.name in configs:path.unlink()
            for path in clean.rglob('*'):
                if path.is_file() and path.name in configs:
                    target=staged/path.relative_to(clean);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
            return evaluate(staged,output,actor,row,clean)
    return independent


def target_id(condition):return f'target__{condition}__seed7202'


def derive_target(root,condition,actor,profile,experience):
    def bind_requests(_root,_task,_condition,_experience,*,protocol,seed):
        return source.requests_runner.derive(root,'target',condition,experience,protocol=protocol,seed=7202)
    proxy=SimpleNamespace(rebind_model=source.primitives.rebind_model,
        set_model_limits=lambda code,p,backend:source.primitives.set_model_limits(code,p,'student8b'),
        bind_per_request_transport=source.primitives.bind_per_request_transport)
    return adapt(source.derive,requests_runner=SimpleNamespace(derive=bind_requests),primitives=proxy,EID=target_id(condition))(root,actor,profile)


def target_components():
    paths=source.components();paths['source_adapter.py']=paths.pop('outer_runner.py')
    paths.update({'outer_runner.py':Path(__file__),'experience_renderer.py':Path(rendering.__file__)})
    return paths


def verify_target_inputs(root,manifest):
    frozen_source(manifest['source_manifest_sha256'])
    source.dependencies.verify_projection(PARENT/'actor_python38',manifest['projection_sha256'])
    if (source.tree(root/'inputs/target/clean_base')!=manifest['baseline_tree']
            or sha(root/'inputs/target/task.txt')!=manifest['task_sha256']
            or sha(root/'frozen_source_harness.py')!=manifest['harness_sha256']
            or sha(root/'model_profile.json')!=STUDENT_SHA):raise ValueError('target inputs changed')
    paths=target_components();snapshot=root/(target_id(manifest['condition'])+'.components')
    if set(paths)!=set(manifest['component_sha256']) or any(sha(paths[n])!=h or sha(snapshot/n)!=h for n,h in manifest['component_sha256'].items()):
        raise ValueError('target components changed')
    if manifest['condition']!='none' and sha(root/'source_experience.md')!=manifest['experience_sha256']:
        raise ValueError('actor experience changed')


def prepare_target(attempt,condition,source_digest):
    if condition not in CONDITIONS:raise ValueError('unsupported target condition')
    frozen_source(source_digest);row,_=target_row()
    root=TARGETS/source.primitives.attempt_root(PARENT,attempt).name
    if TARGETS.is_symlink() or root.exists() or root.is_symlink():raise FileExistsError('preserve existing transfer attempt')
    actor=source.prepare_projection();profile=source.primitives.validate_model_profile(STUDENT_PROFILE,STUDENT_SHA)
    verify_clean=adapt(source.verify_clean,SOURCE_BASE=TARGET_BASE)
    verify_clean(source.QUAL/'target/clean',source.QUAL/'target.tar.gz')
    root.mkdir(parents=True);inputs=root/'inputs/target';inputs.mkdir(parents=True)
    shutil.copytree(source.QUAL/'target/clean',inputs/'clean_base')
    (inputs/'task.txt').write_text(row['problem_statement']+source.ENVIRONMENT,encoding='utf8')
    shutil.copyfile(STUDENT_PROFILE,root/'model_profile.json');source.primitives.prepare_actor_runtime(root)
    experience=None
    if condition!='none':
        experience=root/'source_experience.md';shutil.copyfile(EXPERIENCE/(condition+'.md'),experience)
    paths=target_components();snapshot=root/(target_id(condition)+'.components');snapshot.mkdir()
    for name,path in paths.items():shutil.copyfile(path,snapshot/name)
    harness=root/'frozen_source_harness.py';harness.write_text(derive_target(root,condition,actor,profile,experience),encoding='utf8')
    manifest={'status':'PREPARED','condition':condition,'source_manifest_sha256':source_digest,
        'source_completion_sha256':SOURCE_SHA,'projection_sha256':actor['manifest_sha256'],
        'model_profile_sha256':STUDENT_SHA,'task_sha256':sha(inputs/'task.txt'),'harness_sha256':sha(harness),
        'component_sha256':{name:sha(snapshot/name) for name in paths},'baseline_tree':source.tree(inputs/'clean_base'),
        'experience_sha256':sha(experience) if experience else None,'target_base':TARGET_BASE,
        'target_regression_nodes_sha256':NODES_SHA,'known_exclusions':EXCLUDED,
        'adapter_bindings':{'role':'target','seed':7202,'backend':'student8b','evaluation_count':142,
                            'source_evaluation_count':114,'shared_globals_modified':False}}
    write_new(root/'inputs_manifest.json',manifest);verify_target_inputs(root,manifest)
    control=adapt(source.preflight,[('inputs/source/clean_base','inputs/target/clean_base',1),('source_gold.patch','target_gold.patch',1)],
                  evaluate=target_evaluator())(root,actor,row)
    return {'root':str(root),'status':control['status'],'model_calls':0,'inputs_manifest_sha256':sha(root/'inputs_manifest.json')}


def execute_target(attempt,source_digest,input_digest):
    root=TARGETS/source.primitives.attempt_root(PARENT,attempt).name;manifest=read(root/'inputs_manifest.json')
    if manifest['source_manifest_sha256']!=source_digest:raise ValueError('target bound to different source')
    condition=manifest['condition'];eid=target_id(condition);actor=source.prepare_projection()
    row,_=target_row();profile=source.primitives.validate_model_profile(STUDENT_PROFILE,STUDENT_SHA)
    def observed_write(path,value):
        if path.name in (eid+'.started.json',eid+'.completed.json'):
            value=dict(value,source_manifest_sha256=source_digest)
            if path.name.endswith('.completed.json'):
                raw=root/eid/'raw.jsonl'
                value['experience_read']=(inspect_experience_reads(raw,root/'source_experience.md') if raw.is_file()
                                          else {'status':'RAW_UNAVAILABLE'}) if condition!='none' else None
        write_new(path,value)
    run=adapt(source.execute_source,[(7201,7202,3),('source','target',2),('none',condition,1),('teacher27b','student8b',1),
        ('inputs/source/task.txt','inputs/target/task.txt',1),('inputs/source/clean_base','inputs/target/clean_base',1),
        ('source_artifact_qualification','target_artifact_qualification',1)],
        EID=eid,PROFILE_SHA=STUDENT_SHA,verify_inputs=verify_target_inputs,checked_qualification=target_row,
        teacher=SimpleNamespace(verify_vllm_backend=source.primitives.verify_live_backend),
        evaluate=target_evaluator(),write_new=observed_write)
    return run(root,manifest,actor,row,profile,input_digest)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare-source','generate-skill','freeze-source','prepare-target','execute-target'))
    parser.add_argument('--attempt-id');parser.add_argument('--condition',choices=CONDITIONS,default='none')
    parser.add_argument('--source-manifest-sha256');parser.add_argument('--inputs-manifest-sha256')
    args=parser.parse_args()
    if args.mode.endswith('target') and (not args.attempt_id or not args.source_manifest_sha256):
        parser.error('target modes require --attempt-id and --source-manifest-sha256')
    if args.mode=='execute-target' and not args.inputs_manifest_sha256:parser.error('execution requires reviewed --inputs-manifest-sha256')
    if args.mode=='prepare-source':result=prepare_source()
    elif args.mode=='generate-skill':result=generate_skill()
    elif args.mode=='freeze-source':result=freeze_source()
    elif args.mode=='prepare-target':result=prepare_target(args.attempt_id,args.condition,args.source_manifest_sha256)
    else:result=execute_target(args.attempt_id,args.source_manifest_sha256,args.inputs_manifest_sha256)
    response={'mode':args.mode,'result':result}
    if args.mode=='freeze-source':response['source_manifest_sha256']=sha(EXPERIENCE/'frozen_manifest.json')
    print(json.dumps(response))


if __name__=='__main__':main()
