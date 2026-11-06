#!/usr/bin/env python3
"""Freeze source-only Django experience; no model calls except explicit generation.

The source episode remains immutable. Each output is bound to its own saved
runner components and to rechecked raw, feedback, baseline and complete diff.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import time
import urllib.request

EID = 'source__none__seed7201'
ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
QUAL = ROOT / 'django_aggregation_qualification_20261106'
BASELINE = QUAL / 'sqlite_source/clean'
QUAL_SHA = '46f67e61c87e2e3d118189fbce9ce45a9cbf105eb8440ff2eee6d43d67dd16cc'
COMPONENTS = {'outer_runner.py', 'core.py', 'requests_runner.py', 'research_actor_dependencies.py',
              'research_auto_record.py', 'base_harness.py'}
MARKERS = ('django__django-34176', '/pull/34176', '/issues/34176', '#34176')
BACKENDS = {'student8b': {'model_id': 'qwen3-8b-qual', 'host': '127.0.0.1', 'port': 18104},
            'teacher35b': {'model_id': 'Qwen3.6-35B-A3B-Q4_K_M.gguf', 'host': '127.0.0.1', 'port': 8004},
            'teacher27b': {'model_id': 'qwen38-27b-fp8', 'host': '127.0.0.1', 'port': 8006}}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()


def read(path: Path) -> dict:
    value=json.loads(path.read_text(encoding='utf8'))
    if not isinstance(value,dict): raise ValueError('expected JSON object')
    return value


def verify_baseline(baseline: Path) -> dict:
    if baseline.resolve() != BASELINE.resolve() or sha(QUAL/'sqlite_receipt.json') != QUAL_SHA:
        raise ValueError('unrecognized source baseline or qualification')
    case=read(QUAL/'sqlite_receipt.json')['cases']['source'];archive=QUAL/'source.tar.gz'
    if sha(archive)!=case['archive_sha256']: raise ValueError('source archive changed')
    expected={}; omitted=[]
    with tarfile.open(archive,'r:gz') as tf:
        for item in tf:
            name=PurePosixPath(item.name)
            if not name.parts or name.parts[0]!='django-'+case['base'] or name.is_absolute() or '..' in name.parts:
                raise ValueError('unsafe baseline archive')
            if item.issym(): omitted.append(item.name);continue
            if item.isdir():continue
            if not item.isfile():raise ValueError('non-file baseline')
            with tf.extractfile(item) as f:expected[PurePosixPath(*name.parts[1:]).as_posix()]=hashlib.sha256(f.read()).hexdigest()
    if tree(baseline)!=expected or sorted(omitted)!=sorted(case['omitted_symlinks']):
        raise ValueError('baseline differs from source archive')
    return {'qualification_sha256':QUAL_SHA,'archive_sha256':case['archive_sha256'],'base':case['base']}


def tree(root: Path, *, actor: bool = False) -> dict:
    if root.is_symlink() or not root.is_dir(): raise ValueError('tree missing or symlink')
    result={}
    for p in root.rglob('*'):
        if p.is_symlink(): raise ValueError('symlink requires separate review')
        if not p.is_file():continue
        rel=p.relative_to(root)
        if any(v in ('.git','__pycache__','.pytest_cache') for v in rel.parts): continue
        if actor and len(rel.parts)==1 and rel.name in ('instructions.txt','opencode.json','source_experience.md'):continue
        result[rel.as_posix()]=sha(p)
    return result


def make_diff(base: Path, work: Path) -> tuple[bytes,list,dict]:
    before,after=tree(base),tree(work,actor=True)
    changed=sorted(name for name in before.keys()|after.keys() if before.get(name)!=after.get(name))
    parts=[]
    for name in changed:
        left,right=base/name,work/name
        old=left.read_bytes().splitlines(keepends=True) if left.is_file() else []
        new=right.read_bytes().splitlines(keepends=True) if right.is_file() else []
        parts.extend(difflib.diff_bytes(difflib.unified_diff,old,new,
                    fromfile=('source-base/'+name).encode(),tofile=('source-agent/'+name).encode()))
    return b''.join(parts),changed,{name:{'before':before.get(name),'after':after.get(name)} for name in changed}


def render_field(name: str, data: bytes) -> str:
    # JSON records use bounded chunks; concatenating text then UTF-8/surrogateescape
    # recovers even a giant unterminated line or a non-UTF8 byte, without truncation.
    text=data.decode('utf8',errors='surrogateescape')
    chunks=[text[i:i+160] for i in range(0,len(text),160)] or ['']
    return 'BEGIN_'+name+'\n'+''.join(json.dumps({'part':i,'text':chunk},ensure_ascii=True)+'\n'
                                         for i,chunk in enumerate(chunks))+'END_'+name+'\n'


def decode_field(document: str, name: str) -> bytes:
    body=document.split('BEGIN_'+name+'\n',1)[1].split('END_'+name+'\n',1)[0]
    rows=[json.loads(s) for s in body.splitlines()]
    if [r['part'] for r in rows]!=list(range(len(rows))): raise ValueError('field chunks not ordered')
    return ''.join(r['text'] for r in rows).encode('utf8',errors='surrogateescape')


def decode_patch(document: str) -> bytes:
    return decode_field(document,'COMPLETE_SOURCE_DIFF')


def source_evidence(source: Path, baseline: Path, *, verify_baseline=verify_baseline) -> dict:
    completed=source/(EID+'.completed.json')
    if not completed.is_file(): raise ValueError('source has not completed; do not read live raw')
    record=read(completed); start=source/(EID+'.started.json'); started=read(start)
    if (record.get('status')!='COMPLETED' or type(record.get('posts')) is not int or record['posts']<1
            or record.get('started_sha256')!=sha(start)
            or (started.get('task'),started.get('condition'),started.get('seed'))!=('source','none',7201)):
        raise ValueError('source did not deliver a completed physical model episode')
    components=started.get('component_sha256',{});snap=source/(EID+'.components')
    if not COMPONENTS.issubset(components) or started.get('runner_sha256')!=components['outer_runner.py']:
        raise ValueError('source component snapshot incomplete')
    kind=started.get('backend_kind','student8b')
    if kind not in BACKENDS or (kind.startswith('teacher') and 'research_teacher_backend.py' not in components):
        raise ValueError('source backend or teacher snapshot missing')
    if any(sha(snap/name)!=digest for name,digest in components.items()): raise ValueError('source component snapshot changed')
    task_file=source/(EID+'.task.txt')
    if sha(task_file)!=started.get('task_sha256'):raise ValueError('source task changed')
    case=source/EID; raw=case/'raw.jsonl';detail=read(case/'receipt.json')
    if (sha(raw)!=record.get('raw_sha256') or detail.get('raw_sha256')!=sha(raw)
            or sum(x.startswith('POST ') for x in detail.get('model_http_requests',[]))!=record['posts']):
        raise ValueError('raw/request accounting changed')
    feedback=record.get('post_run_evaluation',{})
    if feedback.get('status')!='EVALUATED':raise ValueError('source feedback incomplete')
    logs={}
    for key in ('focus','regression','issue_probe',*(['broader_regression'] if 'broader_regression' in feedback else [])):
        item=feedback.get(key,{})
        path=case/'post_run_evaluation_restored_tests'/(key+'.log')
        if sha(path)!=item.get('log_sha256'):raise ValueError('source feedback log changed')
        logs[key]=sha(path)
    actions=[]
    for line in raw.read_text(encoding='utf8').splitlines():
        ev=json.loads(line)
        if ev.get('type')=='tool_use':
            part=ev.get('part',{});state=part.get('state',{})
            inp=json.dumps(state.get('input',{}),ensure_ascii=False);out=str(state.get('output',''))
            actions.append({'tool':part.get('tool'),'status':state.get('status'),'input_prefix':inp[:600],
                            'input_chars':len(inp),'input_sha256':hashlib.sha256(inp.encode()).hexdigest(),
                            'output_tail':out[-800:],'output_chars':len(out),'output_sha256':hashlib.sha256(out.encode()).hexdigest()})
    if not actions:raise ValueError('source has no recorded tool actions')
    diff,changed,files=make_diff(baseline,case/'work')
    if any(marker.casefold() in (raw.read_text(encoding='utf8')+diff.decode('utf8',errors='replace')).casefold() for marker in MARKERS):
        raise ValueError('source contains explicit target identity')
    provenance={'source_attempt':str(source.resolve()),'completion_sha256':sha(completed),'started_sha256':sha(start),
                'raw_sha256':sha(raw),'case_receipt_sha256':sha(case/'receipt.json'),'task_sha256':sha(task_file),'component_sha256':components,
                'model_profile_sha256':started.get('model_profile_sha256'),'projection_sha256':started.get('projection_sha256'),
                'baseline':verify_baseline(baseline),'feedback_log_sha256':logs,'diff_sha256':hashlib.sha256(diff).hexdigest(),
                'changed_artifacts':files}
    outcome={'agent_exit':record.get('agent_exit'),'physical_posts':record['posts'],
             'reported_tokens':record.get('reported_tokens'),'focus':feedback['focus'],
             'regression':feedback['regression'],'issue_probe':feedback['issue_probe']}
    if 'broader_regression' in feedback:
        outcome['broader_regression']=feedback['broader_regression']
        outcome['source_artifact_qualification']=feedback.get('source_artifact_qualification')
    return {'provenance':provenance,'outcome':outcome,'actions':actions,'diff':diff,'changed_paths':changed,'task':task_file.read_bytes()}


def body(label: str, evidence: dict, *, history: bool) -> str:
    result=label+'\nSource outcome:\n'+json.dumps(evidence['outcome'],ensure_ascii=True,indent=2)+'\n'
    result+='Changed paths:\n'+json.dumps(evidence['changed_paths'],ensure_ascii=True,indent=2)+'\n'
    if history:
        result+='Source task (ordered JSON parts):\n'+render_field('SOURCE_TASK',evidence['task'])
        result+='Tool actions (input prefix 600 characters, output tail 800 characters; hashes retain identity):\n'
        result+=render_field('ACTION_JSON',json.dumps(evidence['actions'],ensure_ascii=True,indent=2).encode())
    result+='Complete observed source unified diff; concatenate ordered JSON part text exactly:\n'
    result+=render_field('COMPLETE_SOURCE_DIFF',evidence['diff'])
    if decode_patch(result)!=evidence['diff'] or max(map(len,result.splitlines()),default=0)>1800:
        raise ValueError('diff rendering failed or exceeds read-tool line limit')
    return result


def build_draft(source: Path, baseline: Path, output: Path, *, verify_baseline=verify_baseline) -> dict:
    if output.exists() or output.is_symlink():raise FileExistsError('preserve existing experience directory')
    ev=source_evidence(source,baseline,verify_baseline=verify_baseline)
    output.mkdir(parents=True)
    for name,text in [('source_history.md',body('Source-only ordinary history.',ev,history=True)),
                      ('feedback_card.md',body('Observed source edit and source outcome.',ev,history=False))]:
        (output/name).write_text(text,encoding='utf8')
    manifest={'status':'DRAFT','source':ev['provenance'], 'action_count':len(ev['actions']),
              'artifacts':{n:sha(output/n) for n in ('source_history.md','feedback_card.md')},
              'scope':'source-only; explicit identity screen does not prove pretraining independence'}
    (output/'draft_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
    return manifest


def validate_draft(source: Path, baseline: Path, output: Path, *, verify_baseline=verify_baseline) -> dict:
    draft=read(output/'draft_manifest.json');ev=source_evidence(source,baseline,verify_baseline=verify_baseline)
    if (draft.get('status')!='DRAFT' or draft['source']!=ev['provenance'] or
        any(sha(output/name)!=digest for name,digest in draft['artifacts'].items()) or
        (output/'source_history.md').read_text(encoding='utf8')!=body('Source-only ordinary history.',ev,history=True) or
        (output/'feedback_card.md').read_text(encoding='utf8')!=body('Observed source edit and source outcome.',ev,history=False)):
        raise ValueError('source or draft artifacts changed')
    return draft


def source_backend(draft: dict) -> tuple[str, dict]:
    source=Path(draft['source']['source_attempt']);started_file=source/(EID+'.started.json')
    if sha(started_file)!=draft['source']['started_sha256']:raise ValueError('source start changed')
    started=read(started_file);kind=started.get('backend_kind','student8b')
    if kind not in BACKENDS:raise ValueError('unknown source backend')
    if kind.startswith('teacher'):
        name='research_teacher_backend.py';components=started.get('component_sha256',{})
        if name not in components or sha(source/(EID+'.components')/name)!=components[name]:
            raise ValueError('teacher source helper snapshot missing or changed')
    return kind,started


def generate_skill(source: Path, baseline: Path, output: Path, model_profile: Path, digest: str) -> dict:
    """Explicitly generate one ordinary skill; reserve before the sole POST."""
    draft=validate_draft(source,baseline,output)
    if digest!=draft['source']['model_profile_sha256']:raise ValueError('skill model differs from source model profile')
    kind,started=source_backend(draft)
    if kind.startswith('teacher'):
        from scripts.graph import research_teacher_backend as backend_helper
    else:
        import run_django_aggregation_agent_20261106 as backend_helper
    if kind=='teacher27b':
        profile=backend_helper.validate_vllm_model_profile(model_profile,digest)
        live=backend_helper.verify_vllm_backend(profile)
    else:
        profile=backend_helper.validate_model_profile(model_profile,digest);live=backend_helper.verify_live_backend(profile)
    expected=BACKENDS[kind]
    if any(profile.get(k)!=v for k,v in expected.items()):raise ValueError('source backend profile does not match whitelist')
    endpoint=f"http://{profile['host']}:{profile['port']}/v1/chat/completions"
    paths={name:output/name for name in ('skill_generation_request.json','skill_generation_response.json',
                                         'skill_generation_ledger.json','generated_skill.md')}
    if any(p.exists() or p.is_symlink() for p in paths.values()): raise FileExistsError('generation already attempted')
    payload={'model':profile['model_id'],'temperature':0.2,'seed':7201,'max_tokens':2500,
        'messages':[{'role':'system','content':'Create concise reusable instructions from this source-only agent execution '
                     'and measured feedback. Distinguish successful actions, observed failures and uncertainty; '
                     'do not invent results or assume a future task. Return only the skill text.'},
                    {'role':'user','content':(output/'source_history.md').read_text(encoding='utf8')}]}
    data=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf8')
    if len(data)>6_000_000:raise ValueError('source history exceeds generation request cap')
    with paths['skill_generation_request.json'].open('xb') as f:f.write(data)
    ledger={'status':'ATTEMPT_STARTED','physical_http_attempts':1,'model_profile_sha256':digest,'backend':live,
            'backend_kind':kind,'model_id':profile['model_id'],'endpoint':endpoint,
            'backend_helper_sha256':sha(Path(backend_helper.__file__)),'experience_helper_sha256':sha(Path(__file__)),
            'source_backend_helper_sha256':started.get('component_sha256',{}).get('research_teacher_backend.py') if kind.startswith('teacher') else None,
            'request_timeout_seconds':900 if kind.startswith('teacher') else 300,
            'source_history_sha256':sha(output/'source_history.md'),'request_sha256':sha(paths['skill_generation_request.json']),
            'usage':None,'finish_reason':None}
    ledger_path=paths['skill_generation_ledger.json']
    with ledger_path.open('x',encoding='utf8') as f:json.dump(ledger,f,indent=2)
    begin=time.monotonic()
    try:
        req=urllib.request.Request(endpoint,data=data,
                                   headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=ledger['request_timeout_seconds']) as response:raw=response.read()
        with paths['skill_generation_response.json'].open('xb') as f:f.write(raw)
        parsed=json.loads(raw);choice=parsed['choices'][0];text=choice['message']['content']
        ledger.update({'response_sha256':sha(paths['skill_generation_response.json']),
                       'usage':parsed.get('usage'),'finish_reason':choice.get('finish_reason')})
        if not isinstance(text,str) or not text.strip() or choice.get('finish_reason')!='stop':
            raise ValueError('skill output empty or truncated')
        if any(marker.casefold() in text.casefold() for marker in MARKERS):
            raise ValueError('generated skill contains explicit target identity')
        with paths['generated_skill.md'].open('x',encoding='utf8') as f:f.write(text.strip()+'\n')
        ledger.update({'status':'RECEIVED','skill_sha256':sha(paths['generated_skill.md'])})
    except Exception as exc:
        ledger.update({'status':'FAILED_UNKNOWN_USAGE' if not paths['skill_generation_response.json'].exists() else 'FAILED_RECORDED_RESPONSE',
                       'error_type':type(exc).__name__})
        raise
    finally:
        ledger['seconds']=round(time.monotonic()-begin,3)
        ledger_path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8')
    return ledger


def validate_skill(output: Path, draft: dict) -> dict:
    ledger=read(output/'skill_generation_ledger.json')
    kind,started=source_backend(draft); expected=BACKENDS[kind]
    if (ledger.get('status')!='RECEIVED' or ledger.get('physical_http_attempts')!=1 or ledger.get('finish_reason')!='stop'
            or ledger.get('model_profile_sha256')!=draft['source']['model_profile_sha256']
            or ledger.get('source_history_sha256')!=sha(output/'source_history.md')):
        raise ValueError('skill ledger or source binding invalid')
    new_fields={'backend_kind','model_id','endpoint','backend_helper_sha256','experience_helper_sha256','source_backend_helper_sha256'}
    if kind.startswith('teacher') or any(field in ledger for field in new_fields):
        endpoint=f"http://{expected['host']}:{expected['port']}/v1/chat/completions"
        source_helper=started['component_sha256'].get('research_teacher_backend.py') if kind.startswith('teacher') else None
        if (not new_fields.issubset(ledger) or ledger['backend_kind']!=kind or ledger['model_id']!=expected['model_id']
                or ledger['endpoint']!=endpoint or ledger['source_backend_helper_sha256']!=source_helper
                or any(not isinstance(ledger[key],str) or not re.fullmatch(r'[0-9a-f]{64}',ledger[key])
                       for key in ('backend_helper_sha256','experience_helper_sha256'))):
            raise ValueError('skill backend metadata does not match its source')
    for key,name in [('request_sha256','skill_generation_request.json'),('response_sha256','skill_generation_response.json'),
                     ('skill_sha256','generated_skill.md')]:
        if ledger.get(key)!=sha(output/name):raise ValueError('skill evidence changed')
    request=read(output/'skill_generation_request.json');response=read(output/'skill_generation_response.json')
    if (request.get('model')!=expected['model_id'] or request.get('seed')!=7201 or request.get('temperature')!=0.2
            or request.get('max_tokens')!=2500 or request.get('messages',[])[-1].get('content')!=(output/'source_history.md').read_text(encoding='utf8')):
        raise ValueError('skill request is not source-bound')
    choice=response['choices'][0]
    if choice.get('finish_reason')!='stop' or choice['message']['content'].strip()+'\n'!=(output/'generated_skill.md').read_text(encoding='utf8'):
        raise ValueError('skill does not match the recorded response')
    if any(marker.casefold() in choice['message']['content'].casefold() for marker in MARKERS):
        raise ValueError('generated skill contains explicit target identity')
    return ledger


def freeze(source: Path, baseline: Path, output: Path, *, verify_baseline=verify_baseline) -> dict:
    target_records=list(source.parent.glob('*/target__*.started.json'))+list(source.parent.glob('*/target__*.completed.json'))
    if target_records:raise ValueError('target has started in this experiment family; pre-target freeze forbidden')
    final=output/'input_profile_manifest.json'
    if final.exists() or final.is_symlink():raise FileExistsError('profile already frozen')
    draft=validate_draft(source,baseline,output,verify_baseline=verify_baseline)
    validate_skill(output,draft)
    names=('source_history.md','feedback_card.md','generated_skill.md','skill_generation_request.json',
           'skill_generation_response.json','skill_generation_ledger.json','draft_manifest.json')
    manifest={'status':'FROZEN_BEFORE_TARGET','source':draft['source'],
              'artifacts':{n:sha(output/n) for n in names},
              'scope':'development only; no target episode was visible in the source attempt family at freeze'}
    if list(source.parent.glob('*/target__*.started.json')) or list(source.parent.glob('*/target__*.completed.json')):
        raise ValueError('target started during freeze')
    with final.open('x',encoding='utf8') as f:json.dump(manifest,f,ensure_ascii=False,indent=2);f.write('\n')
    return manifest


def validate_frozen(source: Path, baseline: Path, output: Path, expected_sha256: str, *, verify_baseline=verify_baseline) -> dict:
    """Validate an immutable pre-target freeze for consumption after target starts.

    Historical source snapshots are checked directly; today's runner need not be
    byte-identical to the earlier version that performed the source episode.
    """
    manifest_path=output/'input_profile_manifest.json'
    if sha(manifest_path)!=expected_sha256:raise ValueError('frozen manifest changed')
    manifest=read(manifest_path);draft=validate_draft(source,baseline,output,verify_baseline=verify_baseline)
    validate_skill(output,draft)
    names={'source_history.md','feedback_card.md','generated_skill.md','skill_generation_request.json',
           'skill_generation_response.json','skill_generation_ledger.json','draft_manifest.json'}
    if (manifest.get('status')!='FROZEN_BEFORE_TARGET' or manifest.get('source')!=draft['source']
            or set(manifest.get('artifacts',{}))!=names
            or any(sha(output/name)!=digest for name,digest in manifest['artifacts'].items())):
        raise ValueError('frozen source profile changed')
    return manifest


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-attempt',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    actions=parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--build-draft',action='store_true')
    actions.add_argument('--generate-skill',action='store_true')
    actions.add_argument('--freeze-before-target',action='store_true')
    parser.add_argument('--model-profile',type=Path)
    parser.add_argument('--model-profile-sha256')
    args=parser.parse_args()
    if args.source_attempt.resolve().parent != (ROOT/'django_aggregation_agent_20261106/attempts').resolve():
        parser.error('source attempt must belong to this private experiment')
    if args.output.resolve().parent != args.source_attempt.resolve():parser.error('output must be inside source attempt')
    if args.generate_skill:
        if not args.model_profile or not args.model_profile_sha256:parser.error('explicit model profile and hash required')
        result=generate_skill(args.source_attempt,BASELINE,args.output,args.model_profile,args.model_profile_sha256)
    else:
        if args.model_profile or args.model_profile_sha256:parser.error('model profile allowed only for skill generation')
        result=(build_draft if args.build_draft else freeze)(args.source_attempt,BASELINE,args.output)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
