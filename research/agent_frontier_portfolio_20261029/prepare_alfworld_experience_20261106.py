#!/usr/bin/env python3
"""Compile public ALFWorld source experience; only --generate-skill calls a model."""
from __future__ import annotations
import argparse
from functools import lru_cache
import hashlib
import http.client
import json
from pathlib import Path
import re
import shlex
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.graph import research_teacher_backend as teacher
from prepare_django_aggregation_experience_20261106 import render_field, decode_field

Q=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106')
PILOT=Q/'experience_transfer_pilot_v1'
CONTRACT_SHA='088fcc1b43f71f6c09f63168456b9c200ee1bb7352f55afd2db5443c6f36625e'
SOURCES_SHA='aedfc39c8aad7cc718425194de692015aa0ebb49027c5002067f72ecbba0d124'
RECEIPTS={'clean_1':'554da1ae3ae4ebcd78845ec3d9164ba49665999caa742af2c9a864e424cca3cf',
          'heat_1':'0d0d5f6d28ac848d03b59079269eacd87650327c8284b54cc140c9a7527b3749'}
PROFILE=Q.parent/'django_aggregation_agent_20261106/qwen38_27b_model_profile_v1.json'
PROFILE_SHA='9cbb51bb6dc64583cb376f81e8f8c1c28400cb494fce2793f1fa2ce60e39a279'
HISTORY='ordinary_public_history'
SKILL='ordinary_generated_skill'
SUMMARY='transparent_goal_conditioned_source_summary'
CONDITIONS=(HISTORY,SKILL,SUMMARY)
STATE_KEYS={'observation','score','done','won','action_count','admissible_commands'}
GUARD=('Match the procedure to the current goal. Re-check source entities and locations against current observations. '
       'Do not assume the source route applies; use the current episode\'s real feedback.')
SYSTEM=('Write concise reusable instructions from this real source task, public actions/observations, failures and terminal feedback. '
        'Distinguish observed success, failure and uncertainty. Do not invent results or a future task. '
        'Return only the skill as final content.')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    value=json.loads(Path(path).read_text(encoding='utf8'))
    if not isinstance(value,dict):raise ValueError('expected JSON object')
    return value
def write_new(path,value):
    with Path(path).open('x',encoding='utf8',newline='\n') as stream:
        if isinstance(value,str):stream.write(value)
        else:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
def jsonl(path):return [json.loads(line) for line in Path(path).read_text(encoding='utf8').splitlines()]


def registry():
    if sha(PILOT/'CONTRACT.json')!=CONTRACT_SHA or sha(PILOT/'SOURCES.json')!=SOURCES_SHA:
        raise ValueError('fixed contract/source registry changed')
    contract,sources=read(PILOT/'CONTRACT.json'),read(PILOT/'SOURCES.json')
    if sources.get('contract_sha256')!=CONTRACT_SHA or sources.get('source_roles_fixed_before_generation') is not True:
        raise ValueError('source roles were not fixed')
    allowed={p['source'] for p in contract['pairs']}
    rows={r['game_id']:r for r in sources['sources']}
    if len(rows)!=len(sources['sources']) or not set(rows)<=allowed or set(rows)!=set(RECEIPTS):
        raise ValueError('unregistered or target source')
    return contract,rows


def public_screen(text,contract):
    forbidden=['extra.expert_plan','pddl_problem','pddl_domain','private_game_assets','walkthrough','(:init','(:goal']
    forbidden += [p['target'] for p in contract['pairs']]
    if any(word.casefold() in text.casefold() for word in forbidden):raise ValueError('privileged or future target input')


def public_events(events):
    result=[]
    for event in events:
        part=event.get('part',{})
        if event.get('type')=='tool_use':
            state=part.get('state',{})
            result.append({'type':'tool','tool':part.get('tool'),'status':state.get('status'),
                'input':state.get('input',{}),'output':state.get('output',''),'error':state.get('error')})
        elif event.get('type')=='text':result.append({'type':'text','text':part.get('text','')})
        elif event.get('type')=='error':result.append({'type':'error','error':event.get('error',part)})
    return result


def load_source(game_id):
    contract,rows=registry()
    if game_id not in rows:raise ValueError('source must be registered _1, never a target _2')
    row=rows[game_id];root=Path(row['root'])
    if root.is_symlink() or not root.is_absolute():raise ValueError('unsafe source archive root')
    if sha(root/'manifest.json')!=row['manifest_sha256'] or sha(root/'receipt.json')!=RECEIPTS[game_id]:
        raise ValueError('archived source manifest/receipt changed')
    manifest,receipt=read(root/'manifest.json'),read(root/'receipt.json')
    if (manifest.get('game_id')!=game_id or receipt.get('manifest_sha256')!=row['manifest_sha256']
            or manifest.get('backend')!='teacher27b' or manifest.get('profile_sha256')!=PROFILE_SHA
            or manifest.get('model_id')!=contract['source_model'] or manifest.get('seed')!=contract['world_and_model_seed']
            or manifest['pool_binding']['sha256']!=contract['pool_sha256']):
        raise ValueError('wrong archived source binding')
    for name,key in [('task.txt','prompt_sha256'),('initial_reset.json','initial_sha256'),('opencode_config.json','config_sha256')]:
        if sha(root/name)!=manifest[key]:raise ValueError('archived source input changed')
    trajectory=jsonl(root/'execute_world.jsonl');events=jsonl(root/'raw.jsonl')
    if not trajectory or trajectory[0].get('event')!='episode':raise ValueError('missing actual episode trace')
    episode=trajectory[0]
    if (episode.get('game_id')!=game_id or episode.get('asset_sha256')!=manifest['game_sha256']
            or episode.get('pool_manifest_sha256')!=manifest['pool_binding']['sha256'] or episode.get('seed')!=17):
        raise ValueError('world trace source changed')
    resets=[r['state'] for r in trajectory if r.get('event')=='reset']
    initial=read(root/'initial_reset.json')
    if resets!=[initial] or initial.get('won') is not False:raise ValueError('native reset evidence changed')
    steps=[r for r in trajectory if r.get('event')=='step']
    if [r['state']['action_count'] for r in steps]!=list(range(1,len(steps)+1)):
        raise ValueError('world actions are not ordered')
    final=steps[-1]['state'] if steps else initial
    if (final!=receipt.get('final_world_state') or receipt.get('won') is not final.get('won')
            or receipt.get('world_actions')!=len(steps) or any(not set(s)<=STATE_KEYS for s in [initial,*[r['state'] for r in steps]])):
        raise ValueError('world terminal/public state evidence changed')
    observed={}
    for event in public_events(events):
        if event['type']!='tool' or event['tool']!='bash':continue
        command=event['input'].get('command','');states=[]
        for line in str(event['output']).splitlines():
            try:value=json.loads(line)
            except json.JSONDecodeError:continue
            if isinstance(value,dict) and set(value)==STATE_KEYS:states.append(value)
        if states:
            arguments=shlex.split(command)
            if arguments.count('--action')!=1:raise ValueError('public action attribution ambiguous')
            action=arguments[arguments.index('--action')+1];state=states[-1];number=state['action_count']
            if number in observed:raise ValueError('duplicate public world action')
            observed[number]={'action':action,'state':state}
    if observed!={r['state']['action_count']:{'action':r['action'],'state':r['state']} for r in steps}:
        raise ValueError('raw tool returns disagree with actual world trace')
    raw_tokens=[r['part']['tokens'] for r in events if r.get('type')=='step_finish']
    if raw_tokens!=receipt.get('raw_step_tokens_separate_not_added'):raise ValueError('raw token receipt changed')
    response_bindings={};known=[];unknown=0
    responses=receipt.get('response_receipts',[])
    for i,saved in enumerate(responses,1):
        body=root/'responses'/f'{i:05}.body';meta=body.with_suffix('.body.receipt.json')
        if read(meta)!=saved or sha(body)!=saved['body_sha256']:raise ValueError('provider response archive changed')
        response_bindings[body.name]=sha(body);response_bindings[meta.name]=sha(meta)
        usage=saved.get('usage')
        if isinstance(usage,dict) and type(usage.get('total_tokens')) is int:known.append(usage['total_tokens'])
        else:unknown+=1
    posts=receipt.get('forwarded_model_posts')
    if type(posts) is not int or posts<len(responses) or posts<len(raw_tokens):raise ValueError('physical request accounting changed')
    unknown+=posts-len(responses)
    cost={'provider_tokens_known':sum(known) if known else None,'known_usage_responses':len(known),
          'unknown_usage_model_posts':unknown,'usage_complete':unknown==0 and len(known)==posts,
          'physical_model_posts':posts,'raw_step_tokens_are_separate_not_added':True}
    task=(root/'task.txt').read_text(encoding='utf8')
    outcome={'receipt_status':receipt.get('status'),'docker_exit':receipt.get('docker_exit'),'world_actions':len(steps),
             'won':final['won'],'done':final['done'],'final_world_state':final,'cost':cost}
    source={'root':str(root),'manifest_sha256':row['manifest_sha256'],'receipt_sha256':RECEIPTS[game_id],
            'trajectory_sha256':sha(root/'execute_world.jsonl'),'raw_sha256':sha(root/'raw.jsonl'),'won':final['won'],
            'task_sha256':manifest['prompt_sha256'],'initial_sha256':manifest['initial_sha256'],
            'response_file_sha256':response_bindings,'archived_component_sha256':manifest['components'],
            'pool_manifest_sha256':manifest['pool_binding']['sha256']}
    return {'source_game_id':game_id,'source':source,'task':task,'initial':initial,'steps':steps,
            'public_events':public_events(events),'outcome':outcome,'contract':contract}


def carrier_texts(evidence):
    outcome=json.dumps(evidence['outcome'],ensure_ascii=False,indent=2)
    history='Ordinary public source execution. These records describe the past source episode.\n'
    history+=render_field('SOURCE_TASK',evidence['task'].encode())
    history+=render_field('PUBLIC_EVENTS',json.dumps(evidence['public_events'],ensure_ascii=False).encode())
    history+='Actual world terminal feedback:\n'+outcome+'\n'
    observation=evidence['initial']['observation'].replace('\\n','\n')
    goal=re.search(r'Your task is to:\s*([^\n]+)',observation)
    if not goal:raise ValueError('public source goal missing')
    summary='Public source goal: '+goal.group(1)+'\nObserved source actions:\n'
    summary+=''.join(f"{i}. {r['action']} -> {r['state']['observation']}\n" for i,r in enumerate(evidence['steps'],1))
    summary+=f"Observed source terminal: won={json.dumps(evidence['outcome']['won'])}; actions={len(evidence['steps'])}.\n"
    summary+='Fixed goal guard: '+GUARD+'\n'
    result={HISTORY:history,SUMMARY:summary}
    for text in result.values():public_screen(text,evidence['contract'])
    return result


def skill_payload(history):
    return {'model':'qwen38-27b-fp8','seed':17,'temperature':.2,'max_tokens':2500,'stream':False,
            'chat_template_kwargs':{'enable_thinking':False},
            'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':history}]}


@lru_cache(maxsize=1)
def local_tokenizer():
    from transformers import AutoTokenizer
    profile=teacher.validate_vllm_model_profile(PROFILE,PROFILE_SHA,full=False)
    tokenizer=AutoTokenizer.from_pretrained(profile['model_root'],local_files_only=True,trust_remote_code=False)
    template=Path(profile['template_path']).read_text(encoding='utf8')
    files={name:sha(Path(profile['model_root'])/name) for name in ('tokenizer.json','tokenizer_config.json','vocab.json','merges.txt')}
    return tokenizer,template,{'model_profile_sha256':PROFILE_SHA,'tokenizer_file_sha256':files,
                                'template_sha256':profile['template_sha256'],'context_tokens':profile['context']}


def token_budget(texts):
    tokenizer,template,identity=local_tokenizer()
    payload=skill_payload(texts[HISTORY])
    rendered=tokenizer.apply_chat_template(payload['messages'],chat_template=template,tokenize=False,
                                         add_generation_prompt=True,enable_thinking=False)
    count=len(tokenizer.encode(rendered,add_special_tokens=False));margin=512
    result=dict(identity,method='local tokenizer plus actual native chat template; no model call',
                artifact_tokens={name:len(tokenizer.encode(text,add_special_tokens=False)) for name,text in texts.items()},
                writer_prompt_tokens=count,max_output_tokens=2500,safety_margin_tokens=margin,
                remaining_tokens=identity['context_tokens']-count-2500-margin)
    if result['remaining_tokens']<0:raise ValueError('local token count exceeds writer context/output reserve')
    return result


def pre_target():
    root=PILOT/'target_attempts'
    if root.exists() and any(root.rglob('reservation.json')):
        raise ValueError('target preparation exists; source compilation is closed')


def draft(game_id,output):
    pre_target();evidence=load_source(game_id);texts=carrier_texts(evidence);budget=token_budget(texts)
    if output.exists() or output.is_symlink():raise FileExistsError('preserve existing compilation directory')
    output.mkdir(parents=True)
    for name,text in texts.items():write_new(output/(name+'.md'),text)
    manifest={'version':1,'status':'DRAFT','source_game_id':game_id,'source':evidence['source'],
              'artifact_sha256':{n:sha(output/(n+'.md')) for n in texts},'contract_sha256':CONTRACT_SHA,
              'compiler':{'script_sha256':sha(Path(__file__)),'renderer_sha256':sha(Path(sys.modules[render_field.__module__].__file__)),
                          'sources_registry_sha256':SOURCES_SHA,'token_budget':budget,'model_calls':0}}
    write_new(output/'draft_manifest.json',manifest);return manifest


def validate_draft(output):
    manifest=read(output/'draft_manifest.json');evidence=load_source(manifest['source_game_id']);texts=carrier_texts(evidence)
    if manifest.get('version')!=1 or manifest.get('status')!='DRAFT' or manifest.get('contract_sha256')!=CONTRACT_SHA or manifest['source']!=evidence['source']:
        raise ValueError('draft source binding changed')
    for name,text in texts.items():
        if (sha(output/(name+'.md'))!=manifest['artifact_sha256'][name]
                or (output/(name+'.md')).read_bytes()!=text.encode()):raise ValueError('public draft changed')
    return manifest,texts,evidence


def generate_skill(output):
    pre_target();manifest,texts,evidence=validate_draft(output);budget=token_budget(texts)
    names=('skill_request.json','skill_response.json','skill_ledger.json',SKILL+'.md')
    if any((output/name).exists() for name in names):raise FileExistsError('writer already attempted; never retry or fall back')
    payload=skill_payload(texts[HISTORY]);public_screen(json.dumps(payload),evidence['contract'])
    profile=teacher.validate_vllm_model_profile(PROFILE,PROFILE_SHA,full=False)
    backend=teacher.verify_vllm_backend(profile)
    ledger={'status':'RESERVED','physical_http_attempts':1,'model_profile_sha256':PROFILE_SHA,'token_budget':budget,
            'source_game_id':manifest['source_game_id'],'draft_sha256':sha(output/'draft_manifest.json'),'usage':None,'backend':backend}
    write_new(output/'skill_ledger.json',ledger);write_new(output/'skill_request.json',payload)
    ledger['request_sha256']=sha(output/'skill_request.json')
    connection=http.client.HTTPConnection(profile['host'],profile['port'],timeout=900)
    response_path=output/'skill_response.json'
    try:
        connection.request('POST','/v1/chat/completions',body=(output/'skill_request.json').read_bytes(),headers={'Content-Type':'application/json'})
        response=connection.getresponse();ledger['http_status']=response.status
        with response_path.open('xb') as stream:
            while True:
                try:block=response.read(65536)
                except http.client.IncompleteRead as exc:stream.write(exc.partial);raise
                if not block:break
                stream.write(block);stream.flush()
        if getattr(response,'length',0) not in (0,None):raise http.client.IncompleteRead(b'',response.length)
        parsed=read(response_path);ledger['usage']=parsed.get('usage')
        if response.status!=200:raise ValueError('writer HTTP error')
        choice=parsed['choices'][0];text=choice['message'].get('content')
        if choice.get('finish_reason')!='stop' or not isinstance(text,str) or not text.strip():raise ValueError('writer final content missing/incomplete; reasoning is not final')
        public_screen(text,evidence['contract']);write_new(output/(SKILL+'.md'),text.strip()+'\n')
        ledger.update(status='RECEIVED',skill_sha256=sha(output/(SKILL+'.md')))
    except Exception as exc:
        ledger.update(status='FAILED_RAW_RETAINED_OR_USAGE_UNKNOWN',error_type=type(exc).__name__);raise
    finally:
        connection.close()
        if response_path.exists():ledger['response_sha256']=sha(response_path)
        (output/'skill_ledger.json').write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8')
    return ledger


def validate_generation(output,texts):
    ledger=read(output/'skill_ledger.json');request=read(output/'skill_request.json');response=read(output/'skill_response.json')
    text=(output/(SKILL+'.md')).read_text(encoding='utf8');choice=response['choices'][0]
    if (ledger.get('status')!='RECEIVED' or ledger.get('physical_http_attempts')!=1 or ledger.get('http_status')!=200
        or ledger.get('model_profile_sha256')!=PROFILE_SHA or ledger.get('draft_sha256')!=sha(output/'draft_manifest.json')
        or ledger.get('request_sha256')!=sha(output/'skill_request.json') or ledger.get('response_sha256')!=sha(output/'skill_response.json')
        or ledger.get('skill_sha256')!=sha(output/(SKILL+'.md')) or ledger.get('usage')!=response.get('usage')
        or json.dumps(request,sort_keys=True)!=json.dumps(skill_payload(texts[HISTORY]),sort_keys=True)
        or choice.get('finish_reason')!='stop' or not isinstance(choice['message'].get('content'),str)
        or choice['message']['content'].strip()+'\n'!=text):raise ValueError('writer evidence/payload changed')
    return ledger


def freeze(output):
    pre_target();draft_manifest,texts,evidence=validate_draft(output);validate_generation(output,texts)
    for name in CONDITIONS:public_screen((output/(name+'.md')).read_text(encoding='utf8'),evidence['contract'])
    compiler=dict(draft_manifest['compiler'],writer_file_sha256={n:sha(output/n) for n in
                  ('draft_manifest.json','skill_request.json','skill_response.json','skill_ledger.json')})
    manifest={'version':1,'source_game_id':draft_manifest['source_game_id'],'source':evidence['source'],
              'artifact_sha256':{n:sha(output/(n+'.md')) for n in CONDITIONS},'compiler':compiler,
              'contract_sha256':CONTRACT_SHA}
    write_new(output/'frozen_manifest.json',manifest);return manifest


def validate_frozen(path:Path,expected_sha256:str)->dict:
    path=Path(path)
    if path.is_symlink() or sha(path)!=expected_sha256:raise ValueError('frozen manifest changed')
    manifest=read(path);output=path.parent
    if manifest.get('version')!=1 or manifest.get('contract_sha256')!=CONTRACT_SHA or set(manifest['artifact_sha256'])!=set(CONDITIONS):
        raise ValueError('unknown frozen contract')
    draft_manifest,expected,evidence=validate_draft(output)
    if manifest['source_game_id']!=draft_manifest['source_game_id'] or manifest['source']!=evidence['source']:
        raise ValueError('frozen source mismatch')
    for name,digest in manifest['compiler']['writer_file_sha256'].items():
        if name not in ('draft_manifest.json','skill_request.json','skill_response.json','skill_ledger.json') or sha(output/name)!=digest:
            raise ValueError('frozen compiler evidence changed')
    validate_generation(output,expected)
    texts={n:(output/(n+'.md')).read_bytes().decode('utf8') for n in CONDITIONS}
    for name,text in texts.items():
        if hashlib.sha256(text.encode()).hexdigest()!=manifest['artifact_sha256'][name]:raise ValueError('frozen carrier changed')
        public_screen(text,evidence['contract'])
    binding={'source_game_id':manifest['source_game_id'],'source_manifest_sha256':evidence['source']['manifest_sha256'],
        'source_receipt_sha256':evidence['source']['receipt_sha256'],'source_trajectory_sha256':evidence['source']['trajectory_sha256'],
        'source_raw_sha256':evidence['source']['raw_sha256'],'source_won':evidence['source']['won'],
        'source_pool_manifest_sha256':evidence['source']['pool_manifest_sha256'],
        'contract_sha256':CONTRACT_SHA,'frozen_manifest_sha256':expected_sha256}
    return {'manifest':manifest,'texts':texts,'binding':binding}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-game-id',required=True);parser.add_argument('--experience-id',default='v1')
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--build-draft',action='store_true');modes.add_argument('--generate-skill',action='store_true');modes.add_argument('--freeze',action='store_true')
    args=parser.parse_args()
    if not re.fullmatch(r'v[1-9][0-9]*',args.experience_id):parser.error('invalid version identifier')
    registry_rows=registry()[1]
    if args.source_game_id not in registry_rows:parser.error('only registered source _1 IDs are allowed')
    output=PILOT/'experiences'/args.source_game_id/args.experience_id
    if any(p.is_symlink() for p in (PILOT/'experiences',output.parent,output)):raise ValueError('unsafe output path')
    result=draft(args.source_game_id,output) if args.build_draft else generate_skill(output) if args.generate_skill else freeze(output)
    print(json.dumps({'output':str(output),'result':result}))


if __name__=='__main__':main()
