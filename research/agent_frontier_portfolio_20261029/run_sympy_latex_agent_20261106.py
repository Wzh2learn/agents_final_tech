#!/usr/bin/env python3
"""Source-only SymPy 14774 acquisition; preflight never calls a model.

The adapter passes a private protocol to the existing harness builder. It never
changes shared module globals, old pair qualification, or live Django files.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.graph import research_actor_dependencies as dependencies
from scripts.graph import research_auto_record as auto_record
from scripts.graph import research_teacher_backend as teacher
from scripts.graph.research_tool_runtime import ripgrep_binding
import run_django_aggregation_agent_20261106 as primitives

core, requests_runner = primitives.core, primitives.requests_runner
PRIVATE = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
QUAL = PRIVATE / 'sympy_latex_qualification_20261106'
QUAL_SHA = '941e2cc1f44ddb77059d6feb6a51669b7e5cab39cb8456a832231b998ba974e7'
PARENT = PRIVATE / 'sympy_latex_agent_20261106'
SEED_RUNTIME = PRIVATE / 'django_aggregation_agent_20261106/actor_source_v2'
SEED_RUNTIME_SHA = 'f76dc69ba650e61c49a81611392dabf15b65c5d67b7c8fc0ae03bac10c10c16c'
SITE_ENV = PRIVATE / 'swe_contextbench_sympy_python38_env_20261104'
SITE_CONTROL_SHA = '1c6ebb9f156a60076a30ef3a17aa0373bd41ae58abfa6b4e510d8daf00dce9a6'
PROFILE = PRIVATE / 'django_aggregation_agent_20261106/qwen38_27b_model_profile_v1.json'
PROFILE_SHA = '9cbb51bb6dc64583cb376f81e8f8c1c28400cb494fce2793f1fa2ce60e39a279'
SOURCE_BASE = '8fc63c2d71752389a44367b8ef4aba8a91af6a45'
FOCUS = 'sympy/printing/tests/test_latex.py::test_latex_functions'
ROW_HASHES = {'patch':'442fce72a3eb4d34f5c2ed917a11c34e91976af7bd3c56b3e7317139c1c318ed',
              'test_patch':'fa04b744bfa51c3ee5dc865d777bcf0c156317de8d3286e7560c0880f9a96bfd',
              'problem_statement':'0dbbe7a36ff54be79355909d4d0ad9dbb6083b282520cb66562e68198a1c3f1c',
              'PASS_TO_PASS':'035ea3a7ea11f77eb26efa423c381dc35fecd3a2655875babbe36a5f17cec173'}
EID = 'source__none__seed7201'
MAX_POSTS, MAX_SECONDS, MAX_BYTES = 48, 1200, 6_000_000
ENVIRONMENT = ('\n\nThe instructions.txt file is read-only task information. Edit the SymPy source '
               'under /root/ instead. Complete the implementation and run relevant tests without '
               'asking for permission to continue. Python and dependencies are available offline; '
               'python resolves to the isolated Python 3.8 runtime.\n')
sha = primitives.sha


def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding='utf8'))
    if not isinstance(value, dict): raise ValueError('expected object')
    return value


def write_new(path: Path, value) -> None:
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')


def checked_qualification() -> tuple[dict, dict]:
    if sha(QUAL/'FINAL_QUALIFICATION.json') != QUAL_SHA: raise ValueError('qualification changed')
    qualification = read(QUAL/'FINAL_QUALIFICATION.json')
    for name, digest in qualification['artifacts'].items():
        if Path(name).name != name or sha(QUAL/name) != digest: raise ValueError('qualification artifact changed')
    row = read(QUAL/'source_row.json')
    if (row.get('instance_id'), row.get('base_commit')) != ('sympy__sympy-14774', SOURCE_BASE):
        raise ValueError('wrong source row')
    if any(hashlib.sha256(row[key].encode()).hexdigest() != digest for key,digest in ROW_HASHES.items()):
        raise ValueError('source row text or reference changed')
    return qualification, row


def tree(root: Path) -> dict:
    if root.is_symlink() or not root.is_dir(): raise ValueError('unsafe source tree')
    result = {}
    for path in root.rglob('*'):
        if path.is_symlink(): raise ValueError('source symlink')
        if '.git' in path.relative_to(root).parts: raise ValueError('Git history exposed')
        if path.is_file(): result[path.relative_to(root).as_posix()] = sha(path)
    return result


def verify_clean(clean: Path, archive: Path) -> dict:
    expected = {}
    with tarfile.open(archive, 'r:gz') as stream:
        for member in stream:
            parts = PurePosixPath(member.name)
            if (parts.is_absolute() or '..' in parts.parts or not parts.parts
                    or parts.parts[0] != 'sympy-'+SOURCE_BASE or not (member.isfile() or member.isdir())):
                raise ValueError('unsafe source archive')
            if member.isfile():
                name = PurePosixPath(*parts.parts[1:]).as_posix()
                if name in expected: raise ValueError('duplicate archive path')
                with stream.extractfile(member) as content: expected[name] = hashlib.sha256(content.read()).hexdigest()
    if tree(clean) != expected: raise ValueError('source baseline differs from archive')
    return expected


def regression_nodes(row: dict, clean: Path) -> list[str]:
    nodes = []
    for raw in json.loads(row['PASS_TO_PASS']):
        node = raw if '::' in raw else 'sympy/printing/tests/test_latex.py::'+raw
        if node == FOCUS: continue
        file, function = node.split('::')
        relative = PurePosixPath(file)
        if relative.is_absolute() or '..' in relative.parts or not re.fullmatch(r'test_\w+',function):
            raise ValueError('invalid regression node')
        names = {entry.name for entry in ast.parse((clean/file).read_text()).body if isinstance(entry,ast.FunctionDef)}
        if function not in names: raise ValueError('unmapped regression node')
        nodes.append(node)
    if len(nodes) != 114 or len(set(nodes)) != 114: raise ValueError('expected exact 114 regression nodes')
    return nodes


def prepare_projection() -> dict:
    destination = PARENT/'actor_python38'
    if not destination.exists():
        dependencies.verify_projection(SEED_RUNTIME, SEED_RUNTIME_SHA)
        controls = SITE_ENV/'controls/receipt.json'; manifest = SITE_ENV/'controls/environment_manifest.json'
        if sha(controls) != SITE_CONTROL_SHA or sha(manifest) != read(controls)['environment_manifest_sha256']:
            raise ValueError('SymPy dependency controls changed')
        expected = read(manifest)['site_files']
        if tree(SITE_ENV/'site') != expected: raise ValueError('SymPy dependency files changed')
        dependencies.prepare_projection(destination, SEED_RUNTIME/'runtime', {'default':SITE_ENV/'site'},
                                        ['sympy'], python_version='3.8')
    actor = dependencies.verify_projection(destination, sha(destination/'manifest.json'))
    manifest = read(destination/'manifest.json')
    if manifest['python'] != '3.8' or manifest['blocked_packages'] != ['sympy'] or set(actor['sites']) != {'default'}:
        raise ValueError('wrong SymPy projection policy')
    return actor


def derive(root: Path, actor: dict, profile: dict) -> str:
    protocol = SimpleNamespace(OUT=root/'inputs', SITE=Path(actor['sites']['default']), LEGACY=Path(actor['runtime']))
    code = requests_runner.derive(root, 'source', 'none', None, protocol=protocol, seed=7201)
    code = primitives.rebind_model(code, profile)
    code = primitives.set_model_limits(code, profile, 'teacher27b')
    code = core.replace_once(code, "before_temperature,before_seed=payload.get('temperature'),payload.get('seed')",
        "before_temperature,before_seed=payload.get('temperature'),payload.get('seed')\n payload['model']="+repr(profile['model_id']))
    code = core.replace_once(code, "'--entrypoint','python3'", "'--entrypoint','/extra/bin/python'")
    code = core.replace_once(code, 'calls=[]; payload_bytes=[]; sampling=[];',
                             'calls=[]; payload_bytes=[]; sampling=[]; post_lock=threading.Lock(); post_count=[0];')
    line = "  line=first.split(b'\\r\\n',1)[0].rsplit(b' ',1)[0]"
    guard = line+f"\n  if line.startswith(b'POST'):\n   with post_lock:\n    if post_count[0]>={MAX_POSTS}:\n     calls.append('DENIED_POST_LIMIT');self.request.sendall(b'HTTP/1.1 403 Forbidden\\r\\nContent-Length: 0\\r\\nConnection: close\\r\\n\\r\\n');return\n    post_count[0]+=1\n    request_index=post_count[0]"
    code = core.replace_once(code, line, guard)
    code = core.replace_once(code, 'line not in allowed or len(calls)>=24 or ', 'line not in allowed or ')
    code = core.replace_once(code, 'timeout=900)', f'timeout={MAX_SECONDS})')
    code = core.replace_once(code, 'sum(payload_bytes)+length>6000000', f'sum(payload_bytes)+length>{MAX_BYTES}')
    # Reserve and reconcile each body independently: another handler may finish
    # capture first, so payload_bytes[-1] cannot identify this request's bytes.
    code = core.replace_once(code, '   payload_bytes.append(length)',
        '   with post_lock:\n'
        f'    if sum(payload_bytes)+length>{MAX_BYTES}:\n'
        "     calls.append('DENIED:post_byte_reservation');self.request.sendall(b'HTTP/1.1 403 Forbidden\\r\\nContent-Length: 0\\r\\nConnection: close\\r\\n\\r\\n');return\n"
        '    payload_index=len(payload_bytes);payload_bytes.append(length)')
    code = core.replace_once(code, '   payload_bytes[-1]=forwarded\n   if sum(payload_bytes)>6000000:',
        '   with post_lock:\n    payload_bytes[payload_index]=forwarded\n'
        f'    over_byte_budget=sum(payload_bytes)>{MAX_BYTES}\n   if over_byte_budget:')
    extra = ripgrep_binding()+['--mount',f'type=bind,src={root/EID}/work/instructions.txt,dst=/root/instructions.txt,readonly']
    code = core.replace_once(code, 'cmd[_at:_at]=[', 'cmd[_at:_at]='+repr(extra)+'+[')
    code = primitives.bind_per_request_transport(code)
    compile(code, '<sympy-source-harness>', 'exec')
    return code


def components() -> dict[str, Path]:
    result = {'outer_runner.py':Path(__file__), 'django_primitives.py':Path(primitives.__file__),
              'core.py':Path(core.__file__), 'requests_runner.py':Path(requests_runner.__file__),
              'base_harness.py':core.BASE, 'research_actor_dependencies.py':Path(dependencies.__file__),
              'research_teacher_backend.py':Path(teacher.__file__), 'research_auto_record.py':Path(auto_record.__file__)}
    for module in ('scripts.graph.research_evidence_graph','scripts.graph.research_tool_runtime',
                   'qualify_swe_contextbench_sympy_20261104','qualify_swe_contextbench_requests_20261105',
                   'run_swe_contextbench_sphinx_20261105'):
        result[module.replace('.','_')+'.py'] = Path(sys.modules[module].__file__)
    return result


def freeze_inputs(root: Path, actor: dict, profile: dict, row: dict) -> dict:
    final = root/'inputs_manifest.json'
    if final.exists():
        result = read(final); verify_inputs(root,result); return result
    if root.exists(): raise FileExistsError('partial attempt exists; inspect it, never overwrite')
    if sha(core.BASE) != core.BASE_SHA: raise ValueError('base harness changed')
    verify_clean(QUAL/'source/clean', QUAL/'source.tar.gz')
    root.mkdir(parents=True)
    source = root/'inputs/source'; source.mkdir(parents=True)
    shutil.copytree(QUAL/'source/clean',source/'clean_base')
    (source/'task.txt').write_text(row['problem_statement']+ENVIRONMENT,encoding='utf8')
    shutil.copyfile(PROFILE,root/'model_profile.json')
    snapshot = root/(EID+'.components'); snapshot.mkdir()
    paths = components()
    for name,path in paths.items(): shutil.copyfile(path,snapshot/name)
    frozen_components = {name:sha(snapshot/name) for name in paths}
    if any(sha(path) != frozen_components[name] for name,path in paths.items()): raise ValueError('components raced')
    primitives.prepare_actor_runtime(root)
    harness = root/'frozen_source_harness.py'; harness.write_text(derive(root,actor,profile),encoding='utf8')
    result = {'version':1,'qualification_sha256':QUAL_SHA,'source_base':SOURCE_BASE,
              'baseline_archive_sha256':sha(QUAL/'source.tar.gz'),'baseline_tree':tree(source/'clean_base'),
              'task_sha256':sha(source/'task.txt'),'model_profile_sha256':PROFILE_SHA,
              'projection_sha256':actor['manifest_sha256'],'component_sha256':frozen_components,
              'harness_sha256':sha(harness),'protocol_binding':{'OUT':str(root/'inputs'),
                 'SITE':actor['sites']['default'],'LEGACY':actor['runtime'],'shared_globals_modified':False},
              'limits':{'posts':MAX_POSTS,'seconds':MAX_SECONDS,'payload_bytes':MAX_BYTES},
              'boundary':'source only; task/base/projected deps/bridge; evaluator references are never actor mounts'}
    write_new(final,result)
    verify_inputs(root,result)
    return result


def verify_inputs(root: Path, manifest: dict) -> None:
    actor = dependencies.verify_projection(PARENT/'actor_python38',manifest['projection_sha256'])
    source = root/'inputs/source'
    if (tree(source/'clean_base') != manifest['baseline_tree'] or sha(source/'task.txt') != manifest['task_sha256']
            or sha(root/'model_profile.json') != manifest['model_profile_sha256']
            or sha(root/'frozen_source_harness.py') != manifest['harness_sha256']
            or manifest['qualification_sha256'] != QUAL_SHA): raise ValueError('frozen inputs changed')
    snapshot = root/(EID+'.components')
    paths = components()
    if set(paths) != set(manifest['component_sha256']) or any(
            sha(paths[name]) != digest or sha(snapshot/name) != digest for name,digest in manifest['component_sha256'].items()):
        raise ValueError('frozen or loaded runner components changed')
    expected = {'OUT':str(root/'inputs'),'SITE':actor['sites']['default'],'LEGACY':actor['runtime'],
                'shared_globals_modified':False}
    if manifest['protocol_binding'] != expected: raise ValueError('adapter binding changed')


def execution_integrity(case: Path, receipt: dict) -> dict:
    result = primitives.execution_integrity(case,receipt)
    posts, steps = result['counted_posts'], result['completed_usage_steps']
    if steps < posts:
        result['failures'] = [f for f in result['failures'] if f != 'model_usage_steps_disagree_with_counted_posts']
    names = [entry.get('request_body_file') for entry in receipt['sampling_metadata']]
    if len(set(names)) != len(names): result['failures'].append('request_body_identity_reused')
    result.update({'passed':not result['failures'],'requests_without_public_step_finish':max(0,posts-steps),
                   'usage_completeness':'LOWER_BOUND_PUBLIC_STEP_FINISH',
                   'scope':'all physical POSTs counted/captured; compaction or unfinished calls may lack public step_finish'})
    return result


def apply_patch(work: Path, patch: str, output: Path) -> None:
    output.write_text(patch,encoding='utf8')
    subprocess.run(['git','apply','--check',str(output)],cwd=work,capture_output=True,check=True,timeout=30)
    subprocess.run(['git','apply',str(output)],cwd=work,capture_output=True,check=True,timeout=30)


def evaluate(work: Path, output: Path, actor: dict, row: dict, clean: Path) -> dict:
    """Restore tests in an isolated evaluator copy, preserving the actor's work."""
    if any(path.is_symlink() for path in work.rglob('*')): raise ValueError('candidate symlink')
    output.mkdir(parents=True,exist_ok=False); candidate = output/'candidate'
    shutil.copytree(work,candidate,ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache',
                        'tests','instructions.txt','opencode.json','source_experience.md'))
    for tests in clean.rglob('tests'):
        if tests.is_dir(): shutil.copytree(tests,candidate/tests.relative_to(clean),dirs_exist_ok=True)
    apply_patch(candidate,row['test_patch'],output/'hidden_test.patch')
    nodes = regression_nodes(row,clean)
    result = {'status':'EVALUATED','test_source':'FROZEN_BASE_PLUS_QUALIFIED_HIDDEN_PATCH'}
    for name,args,count in (('focus',['-m','pytest','-q','-p','no:cacheprovider',FOCUS],1),
                            ('regression',['-m','pytest','-q','-p','no:cacheprovider',*nodes],114),
                            ('issue_probe',['/probe.py'],1)):
        cmd = ['docker','run','--rm','--pull','never','--network','none','--read-only','--cpus','2','--memory','3g',
               '--pids-limit','256','--cap-drop','ALL','--security-opt','no-new-privileges',
               '--tmpfs','/tmp:rw,nosuid,size=512m','-e','HOME=/tmp','-e','PYTHONPATH=/workspace:/deps',
               '-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
               '-e','HYPOTHESIS_STORAGE_DIRECTORY=/tmp/hypothesis',
               '--mount',f'type=bind,src={candidate},dst=/workspace,readonly',
               '--mount',f"type=bind,src={actor['sites']['default']},dst=/deps,readonly",
               '--mount',f"type=bind,src={actor['runtime']},dst=/extra,readonly",
               '--mount',f'type=bind,src={QUAL}/probe_source.py,dst=/probe.py,readonly',
               '--workdir','/workspace','--entrypoint','/extra/bin/python',primitives.SOURCE_IMAGE,*args]
        proc = subprocess.run(cmd,capture_output=True,timeout=300)
        log = output/(name+'.log');log.write_bytes(proc.stdout+proc.stderr)
        text = log.read_text(encoding='utf8',errors='replace')
        if name == 'issue_probe':
            observed = [json.loads(line[7:]) for line in text.splitlines() if line.startswith('RESULT ')]
            passed = proc.returncode == 0 and len(observed) == 1 and observed[0].get('pass') is True
            passed = passed and observed[0].get('module') == '/workspace/sympy/__init__.py'
        else:
            observed = sum(int(n) for n in re.findall(r'(\d+) passed',text))
            passed = proc.returncode == 0 and observed == count
        result[name] = {'exit':proc.returncode,'expected_count':count,'observed':observed,'passed':passed,'log_sha256':sha(log)}
    result['passed'] = all(result[name]['passed'] for name in ('focus','regression','issue_probe'))
    write_new(output/'receipt.json',result)
    return result


def preflight(root: Path, actor: dict, row: dict) -> dict:
    receipt = root/'preflight/receipt.json'
    if receipt.exists(): return read(receipt)
    parent = root/'preflight';parent.mkdir(exist_ok=False)
    clean = root/'inputs/source/clean_base'
    gold = parent/'gold_input';shutil.copytree(clean,gold)
    apply_patch(gold,row['patch'],parent/'source_gold.patch')
    base_result = evaluate(clean,parent/'base',actor,row,clean)
    gold_result = evaluate(gold,parent/'gold',actor,row,clean)
    passed = (not base_result['focus']['passed'] and base_result['focus']['observed'] == 0
              and base_result['focus']['exit'] == 1 and base_result['regression']['passed']
              and not base_result['issue_probe']['passed'] and base_result['issue_probe']['exit'] == 1
              and gold_result['passed'])
    result = {'status':'PREFLIGHT_PASS' if passed else 'PREFLIGHT_FAILED','model_calls':0,
              'base':base_result,'gold':gold_result,'projection_sha256':actor['manifest_sha256']}
    write_new(receipt,result)
    if not passed: raise ValueError('source base/gold/projection preflight failed')
    return result


def execute_source(root: Path, manifest: dict, actor: dict, row: dict, profile: dict,
                   expected_manifest_sha256: str) -> dict:
    if sha(root/'inputs_manifest.json') != expected_manifest_sha256 or manifest != read(root/'inputs_manifest.json'):
        raise ValueError('reviewed inputs manifest changed')
    verify_inputs(root,manifest)
    if read(root/'preflight/receipt.json')['status'] != 'PREFLIGHT_PASS': raise ValueError('preflight required')
    live = teacher.verify_vllm_backend(profile)
    @auto_record.recorded_episode(root,7201)
    def run(task: str, condition: str) -> None:
        shutil.copyfile(root/'frozen_source_harness.py',root/(EID+'.harness.py'))
        shutil.copyfile(root/'inputs/source/task.txt',root/(EID+'.task.txt'))
        plan = {'status':'STARTED','task':task,'condition':condition,'seed':7201,'backend_kind':'teacher27b',
                'model_profile_sha256':PROFILE_SHA,'projection_sha256':manifest['projection_sha256'],
                'component_sha256':manifest['component_sha256'],'runner_sha256':manifest['component_sha256']['outer_runner.py'],
                'inputs_manifest_sha256':sha(root/'inputs_manifest.json'),'live_backend':live,
                'task_sha256':manifest['task_sha256'],'harness_sha256':manifest['harness_sha256']}
        start = root/(EID+'.started.json');write_new(start,plan)
        proc = subprocess.run([sys.executable,str(root/(EID+'.harness.py')),'source','no_skill'],
                              capture_output=True,stdin=subprocess.DEVNULL,timeout=MAX_SECONDS+120)
        (root/(EID+'.runner.stdout')).write_bytes(proc.stdout);(root/(EID+'.runner.stderr')).write_bytes(proc.stderr)
        plan.update({'started_sha256':sha(start),'runner_exit':proc.returncode})
        case = root/EID
        if proc.returncode == 0 and (case/'receipt.json').is_file():
            receipt = read(case/'receipt.json')
            if sha(case/'raw.jsonl') != receipt['raw_sha256']: raise ValueError('raw hash mismatch')
            metadata = [json.loads(line) for line in (case/'sampling_metadata.jsonl').read_text().splitlines()]
            if Counter(map(lambda x:json.dumps(x,sort_keys=True),metadata)) != Counter(
                    map(lambda x:json.dumps(x,sort_keys=True),receipt['sampling_metadata'])): raise ValueError('sampling log mismatch')
            integrity = execution_integrity(case,receipt)
            if not metadata or any((m['model'],m['seed'],m['temperature']) != (profile['model_id'],7201,0.2) for m in metadata):
                raise ValueError('forwarded model/sampling changed')
            steps = receipt['step_finish_tokens']
            raw_steps = [event['part']['tokens'] for event in map(json.loads,(case/'raw.jsonl').read_text().splitlines())
                         if event.get('type') == 'step_finish']
            if raw_steps != steps: raise ValueError('raw token receipt mismatch')
            verify_inputs(root,manifest); checked_qualification()
            plan.update({'status':'COMPLETED','agent_exit':receipt['agent_exit'],'raw_sha256':receipt['raw_sha256'],
                'posts':integrity['counted_posts'],'execution_integrity':integrity,
                'reported_tokens':sum(step.get('total',0) for step in steps),
                'cache_read_included':sum(step.get('cache',{}).get('read',0) for step in steps),
                'usage_completeness':'LOWER_BOUND_PUBLIC_STEP_FINISH',
                'provider_usage':primitives.provider_usage(case,receipt)})
            try:
                plan['post_run_evaluation'] = evaluate(case/'work',case/'post_run_evaluation',actor,row,
                                                      root/'inputs/source/clean_base')
            except Exception as exc:
                plan['post_run_evaluation'] = {'status':'EVALUATION_FAILED','passed':False,'error_type':type(exc).__name__}
            plan['source_artifact_qualification'] = {'passed':integrity['passed'] and plan['post_run_evaluation']['passed']}
        else: plan['status'] = 'RUNNER_ERROR_REVIEW_RAW_AND_PROXY_LOG'
        write_new(root/(EID+'.completed.json'),plan)
    run('source','none')
    return read(root/(EID+'.completed.json'))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt-id',required=True)
    parser.add_argument('--inputs-manifest-sha256',help='required for execution; use the reviewed preflight digest')
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--preflight-only',action='store_true')
    modes.add_argument('--execute-source',action='store_true')
    args = parser.parse_args()
    if args.execute_source and not args.inputs_manifest_sha256:parser.error('execution requires --inputs-manifest-sha256')
    root = primitives.attempt_root(PARENT,args.attempt_id)
    if root.is_symlink() or PARENT.is_symlink() or (PARENT/'attempts').is_symlink(): raise ValueError('unsafe output root')
    _, row = checked_qualification()
    profile = teacher.validate_vllm_model_profile(PROFILE,PROFILE_SHA,full=False)
    actor = prepare_projection()
    manifest = freeze_inputs(root,actor,profile,row)
    if args.preflight_only:
        result = preflight(root,actor,row)
        print(json.dumps({'status':result['status'],'model_calls':0,'root':str(root),
                          'inputs_manifest_sha256':sha(root/'inputs_manifest.json'),
                          'projection_sha256':actor['manifest_sha256']}))
    else: print(json.dumps(execute_source(root,manifest,actor,row,profile,args.inputs_manifest_sha256)))


if __name__ == '__main__': main()
