"""Offline OpenAI tool-chat supervision candidates from terminal ALF batches.

Standard library only; no tokenization/training/inference. Assistant turn masks
must later be compiled per current completion. They are not old single-row
input_ids/labels. Successful execution does not establish stepwise optimality.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shlex

ST = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106/context_study_v1')
LEGACY = Path(__file__).with_name('alfworld_correction_data_20261106.py')
STATE_KEYS = ('observation','score','done','won','action_count','admissible_commands')
_NATIVE = None
CONTINUE = 'Continue the unfinished task.'
STAGES = ('drop_recent','ordinary_reset')

class IntegrityError(ValueError): pass
class UnsupportedTrajectory(ValueError): pass

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def object_sha(value):return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()
def read_json(path):return read_json_text(Path(path).read_text(encoding='utf8'))
def jsonl(path):return [read_json_text(line) for line in Path(path).read_text(encoding='utf8').splitlines()]

def native_assistant(body):
    global _NATIVE
    if _NATIVE is None:
        spec=importlib.util.spec_from_file_location('supervision_native_sse',LEGACY);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);_NATIVE=module.native_assistant
    try:return _NATIVE(body)
    except (ValueError,KeyError,TypeError) as exc:raise UnsupportedTrajectory('native SSE target not qualified: '+str(exc)) from exc


def observed_assistant(body):
    """Reasoning-only empty public turns can be context, never positive targets."""
    try:return native_assistant(body)
    except UnsupportedTrajectory as exc:
        if 'reasoning-only/empty native target' not in str(exc):raise
        chunks=[read_json_text(line[5:].strip()) for line in body.decode().splitlines() if line.startswith('data:') and line[5:].strip()!='[DONE]']
        deltas=[choice.get('delta',{}) for chunk in chunks for choice in chunk.get('choices',[])]
        text=''.join(delta.get('content') or '' for delta in deltas)
        return {'role':'assistant','content':text},{'finish_reason':'stop','usage':next(chunk['usage'] for chunk in reversed(chunks) if chunk.get('usage')),'ignored_reasoning_utf8_bytes':sum(len((delta.get(key) or '').encode()) for delta in deltas for key in ('reasoning_content','reasoning','analysis'))}


def within(path,base):
    path=Path(path)
    if not path.is_absolute() or '..' in path.parts or path.resolve()!=path or any(p.is_symlink() for p in [path,*path.parents]) or Path(base).resolve() not in path.parents:
        raise IntegrityError('artifact outside explicit study root or symlink: '+str(path))
    return path


def checked(path,expected,base,bindings):
    path=within(path,base)
    if not re.fullmatch('[0-9a-f]{64}',expected) or sha(path)!=expected:raise IntegrityError('hash mismatch: '+str(path))
    bindings[str(path)]=expected
    return path


def public(state):
    if type(state) is not dict or not set(STATE_KEYS)<=set(state):raise IntegrityError('missing public state')
    value={key:state[key] for key in STATE_KEYS}
    if type(value['won']) is not bool or type(value['done']) is not bool or type(value['action_count']) is not int or type(value['observation']) is not str or value['action_count']<0 or type(value['score']) not in (int,float) or type(value['admissible_commands']) is not list or any(type(x) is not str for x in value['admissible_commands']):
        raise IntegrityError('invalid native state types')
    return value


def usage_sum(receipt):
    totals={key:0 for key in ('prompt_tokens','completion_tokens','total_tokens')}
    for response in receipt['response_receipts']:
        usage=response.get('usage')
        if (response.get('complete') is not True or response.get('status')!=200 or type(usage) is not dict or
                any(type(usage.get(key)) is not int or usage[key]<0 for key in totals) or usage['total_tokens']!=usage['prompt_tokens']+usage['completion_tokens']):
            raise IntegrityError('incomplete provider response/usage')
        for key in totals:totals[key]+=usage[key]
    if totals!=receipt['provider_usage'] or receipt.get('unknown_usage_model_posts')!=0:raise IntegrityError('provider cost ledger mismatch/unknown usage')
    return totals


def parse_command(command):
    if not isinstance(command,str) or any(token in command for token in [';','&&','||','|','\n','\r','`','$(']):
        raise UnsupportedTrajectory('complex/multiple-action Bash command')
    try:tokens=shlex.split(command,posix=True)
    except ValueError as exc:raise UnsupportedTrajectory('unparseable Bash command') from exc
    prefix=['/runtime/bin/python','-B','/world/client.py','step','--socket','/world/s','--action']
    if len(tokens)!=8 or tokens[:7]!=prefix or not tokens[7].strip():raise UnsupportedTrajectory('unmatched single-world-action command')
    return tokens[7]


def tool_output(part):
    state=part.get('state',{});metadata=state.get('metadata',{})
    if part.get('tool')!='bash' or state.get('status')!='completed' or type(metadata.get('exit')) is not int or not isinstance(state.get('output'),str):
        raise UnsupportedTrajectory('tool result lacks completed status/output/integer exit')
    lines=[line for line in state['output'].splitlines() if line.strip()]
    try:value=read_json_text(lines[-1])
    except (ValueError,IndexError) as exc:raise UnsupportedTrajectory('tool output lacks one final client JSON response') from exc
    if type(value) is not dict:raise UnsupportedTrajectory('client response is not an object')
    return state['input'],state['output'],metadata['exit'],value


def read_json_text(text):
    def pairs(rows):
        value={}
        for key,item in rows:
            if key in value:raise ValueError('duplicate JSON key')
            value[key]=item
        return value
    return json.loads(text,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))


def semantic_messages(messages):
    value=copy.deepcopy(messages)
    for message in value:
        for call in message.get('tool_calls') or []:
            args=call['function'].get('arguments')
            if isinstance(args,str):call['function']['arguments']=read_json_text(args)
    return value


def task_delivery(root,manifest,receipt,first,bindings):
    task=(root/'task.txt').read_bytes().decode();users=[m.get('content') for m in first['messages'] if m.get('role')=='user'];quoted='"'+task.replace('"',chr(92)+'"')+'"'
    raw=task in users;encoded=quoted in users;proof=receipt['experience_delivery'];actual=read_json(root/'actual_task_delivery.json')
    if not (raw or encoded) or proof.get('expected_task_sha256')!=sha(root/'task.txt') or proof.get('normalized_task_sha256')!=sha(root/'task.txt') or proof.get('first_forwarded_request_sha256')!=object_sha(first):
        raise IntegrityError('actual whole-task delivery is not proven')
    if proof.get('whole_task_raw_equal')!=raw or proof.get('whole_task_lossless_quoted_equal')!=encoded or actual.get('expected_task_sha256')!=sha(root/'task.txt') or actual.get('whole_task_raw_equal')!=raw or actual.get('whole_task_lossless_quoted_equal')!=encoded or actual.get('stage')!=manifest['stage']:
        raise IntegrityError('whole-task delivery receipt mismatch')
    bindings[str(root/'actual_task_delivery.json')]=sha(root/'actual_task_delivery.json')


def provider_records(root,m,r,bindings):
    """Verify even excluded failed runs; hashing at export is recorded, not a new external anchor."""
    records=[]
    for index,response in enumerate(r['response_receipts'],1):
        ident=f'{index:05}';path=root/'requests'/(ident+'.json');body=root/'responses'/(ident+'.body');native_receipt=root/'responses'/(ident+'.body.receipt.json')
        within(path,root);within(native_receipt,root);request=read_json(path)['forwarded'];bindings[str(path)]=sha(path)
        checked(body,response['body_sha256'],root,bindings)
        if body.stat().st_size!=response['body_bytes'] or read_json(native_receipt)!=response:raise IntegrityError('SSE receipt mismatch')
        bindings[str(native_receipt)]=sha(native_receipt)
        if request.get('model')!=m['model_id'] or any(request.get(k)!=v for k,v in m['sampling'].items()):raise IntegrityError('actual provider sampling/model differs')
        data=[line[5:].strip() for line in body.read_text(encoding='utf8').splitlines() if line.startswith('data:')]
        if not data or data[-1]!='[DONE]':raise IntegrityError('SSE has no terminal DONE')
        try:chunks=[read_json_text(line) for line in data[:-1]]
        except ValueError as exc:raise IntegrityError('malformed native SSE JSON') from exc
        usages=[chunk['usage'] for chunk in chunks if chunk.get('usage')]
        if not usages or usages[-1]!=response['usage']:raise IntegrityError('native SSE usage mismatch')
        check=root/'template_checks'/(ident+'.json');within(check,root)
        if not check.is_file() or read_json(check).get('request_payload_sha256')!=object_sha(request):raise IntegrityError('saved forwarded request digest mismatch/missing')
        bindings[str(check)]=sha(check)
        if index==1:task_delivery(root,m,r,request,bindings)
        records.append((request,body))
    if not records:raise IntegrityError('no actual provider request')
    return records


def ordinary_reset_prompt(reset):
    """Exact existing render_prompt(reset, [], reset, '', False, 'recent') contract."""
    return ('Complete this unfinished household task using the actual environment.\n'
        'Original public goal and reset observation (historical):\n' + public(reset)['observation'] +
        '\nPrior experience, historical and not the current state:\n<prior_experience>\n' +
        '\n</prior_experience>\n'
        'Accepted target actions and public observations (historical):\n[]' +
        '\nCurrent public observation and admissible actions:\n' + json.dumps(public(reset),ensure_ascii=False) +
        '\nUse only Bash, one environment action per tool call:\n'
        "/runtime/bin/python -B /world/client.py step --socket /world/s --action '<one exact action>'\n"
        'Read every returned observation and use current admissible_commands. Historical observations are cached, '
        'not fresh evidence. Follow the current goal rather than an old object or procedure. Every accepted action '
        'including look consumes a real step. Continue autonomously. Stop when done is true, and claim success only '
        'after an actual response has won=true. There is no reset, game selection or administrative operation.\n')


def world_records(root,m,r,pool_row,source,bindings):
    events=jsonl(root/'execute_world.jsonl');headers=[e for e in events if e.get('event')=='episode'];states=[public(e['state']) for e in events if e.get('event') in {'reset','step'}];steps=[e for e in events if e.get('event')=='step']
    if source is None:
        n=0;source_states=[read_json(root/'initial_reset.json')]
        if m['stage']!='ordinary_reset' or read_json(root/'handoff_public.json')!=source_states[0] or source_states[0]['action_count']!=0 or (root/'execute_replay.jsonl').exists():raise IntegrityError('ordinary reset has replay or non-reset handoff')
    else:
        source_events=jsonl(source/'execute_world.jsonl');source_states=[public(e['state']) for e in source_events if e.get('event') in {'reset','step'}];n=len(source_states)-1
        replays=jsonl(root/'execute_replay.jsonl')
        if len(replays)!=len(source_states) or any(e.get('equal') is not True or public(e['actual'])!=state for e,state in zip(replays,source_states)):raise IntegrityError('actual source replay comparisons differ')
        within(root/'execute_replay.jsonl',root);bindings[str(root/'execute_replay.jsonl')]=sha(root/'execute_replay.jsonl')
    if (not source_states or not states or len(headers)!=1 or headers[0]['game_id']!=m['case_id'] or headers[0]['asset_sha256']!=pool_row['game_sha256'] or headers[0]['seed']!=m['world_seed'] or source_states[-1]['done'] or source_states[-1]['won'] or states[:len(source_states)]!=source_states or
            states[0]!=read_json(root/'initial_reset.json') or states[n]!=read_json(root/'handoff_public.json') or states[-1]!=public(r['final_world_state']) or states[-1]['won'] is not r['won'] or
            [state['action_count'] for state in states]!=list(range(len(states))) or len(steps)-n!=r['world_actions'] or r['total_world_action_count']!=states[-1]['action_count'] or len(states)!=len(steps)+1):
        raise IntegrityError('native state/replay trajectory is not proven')
    if r['won'] and (states[-1]['done'] is not True or states[-1]['score']!=1.):raise IntegrityError('won flag without native terminal reward')
    within(root/'execute_world.jsonl',root);bindings[str(root/'execute_world.jsonl')]=sha(root/'execute_world.jsonl')
    return steps,n


def round_structure(root,m,r,records,states,bindings):
    """One/two controller rounds only; never accept arbitrary new user instructions."""
    rounds=r['rounds']
    if [state['action_count'] for state in states]!=list(range(len(states))):raise IntegrityError('world reset or discontinuity between rounds')
    if type(rounds) is not list or any(type(row.get('round')) is not int for row in rounds) or type(r.get('ordinary_continuations',0)) is not int or [row.get('round') for row in rounds] not in ([1],[1,2]) or r.get('ordinary_continuations',0)!=len(rounds)-1:raise IntegrityError('unqualified controller round count')
    raw=[];sessions=[];cumulative=[]
    def visit(value,found):
        if isinstance(value,dict):
            for key,item in value.items():
                if key in {'sessionID','session_id'} and isinstance(item,str) and re.fullmatch(r'ses_[A-Za-z0-9]+',item):found.add(item)
                else:visit(item,found)
        elif isinstance(value,list):
            for item in value:visit(item,found)
    for row in rounds:
        path=checked(root/('raw_'+str(row['round'])+'.jsonl'),row['raw_sha256'],root,bindings);events=jsonl(path);raw.extend(events);found=set();visit(events,found);sessions.append(found)
        posts=row.get('model_posts_cumulative')
        if posts is not None:
            if type(posts) is not int or posts<1 or cumulative and posts<=cumulative[-1]:raise IntegrityError('invalid round POST boundary')
            cumulative.append(posts)
        if row.get('state') is not None and public(row['state']) not in states:raise IntegrityError('round state absent from continuous world')
    if len(rounds)==1:
        if (root/'ordinary_continuation.json').exists():raise IntegrityError('orphan controller continuation')
        return raw,{},[]
    if type(m.get('ordinary_continuations')) is not int or m.get('ordinary_continuations')!=1 or len(cumulative)!=2 or not (1<=cumulative[0]<len(records)<=cumulative[1]) or rounds[0]['exit']!=0:raise IntegrityError('unqualified controller continuation budget/boundary')
    before=public(rounds[0]['state'])
    if before['won'] or before['done'] or len(sessions[0])!=1 or sessions[0]!=sessions[1]:raise IntegrityError('continuation does not preserve the same unfinished session')
    path=within(root/'ordinary_continuation.json',root);proof=read_json(path);bindings[str(path)]=sha(path)
    if (proof.get('session_id')!=next(iter(sessions[0])) or proof.get('prompt')!=CONTINUE or type(proof.get('after_round')) is not int or proof.get('after_round')!=1 or proof.get('world_reset') is not False or proof.get('new_method') is not False or public(proof['world_state_before'])!=before):raise IntegrityError('controller continuation proof differs')
    boundary=cumulative[0]+1;request=records[boundary-1][0];message=request['messages'][-1]
    if set(message)!={'role','content'} or message['role']!='user' or message['content'] not in (CONTINUE,'"'+CONTINUE+'"'):raise IntegrityError('continuation has arbitrary additional user instruction')
    # Round1 post boundary must finish at this world state without any reset.
    first_events=jsonl(root/'raw_1.jsonl');first_counts=[]
    for event in first_events:
        if event.get('type')=='tool_use':
            try:_,_,exit_code,result=tool_output(event['part'])
            except UnsupportedTrajectory:continue
            if exit_code==0 and 'error' not in result:first_counts.append(public(result)['action_count'])
    if first_counts and first_counts[-1]!=before['action_count']:raise IntegrityError('round boundary world state changed')
    return raw,{boundary:copy.deepcopy(message)},[{'boundary_post':boundary,'session_id':proof['session_id'],'world_reset':False,'continuation_sha256':sha(path),'prompt':CONTINUE}]


def episode_inputs(entry,base,bindings):
    root=within(entry['root'],base);receipt=read_json(checked(root/'receipt.json',entry['receipt_sha256'],base,bindings))
    if receipt.get('status') not in {'RETURNED','EPISODE_TIMEOUT','FAILED','CLEANUP_INCOMPLETE'} or entry.get('status')!=receipt['status'] or receipt.get('case_id')!=entry['case'] or receipt.get('backend')!=entry['backend'] or receipt.get('stage')!=entry['stage'] or entry.get('won') is not receipt.get('won'):
        raise IntegrityError('not a matching terminal episode')
    manifest=read_json(checked(root/'manifest.json',receipt['manifest_sha256'],base,bindings))
    if any(manifest.get(key)!=receipt.get(key) for key in ('case_id','backend','stage')):raise IntegrityError('manifest episode identity mismatch')
    allowed={'task.txt','opencode_config.json','initial_reset.json','handoff_public.json'}
    if set(manifest['inputs_sha256'])!=allowed:raise IntegrityError('unexpected/missing frozen input names')
    for name,digest in manifest['inputs_sha256'].items():checked(root/name,digest,base,bindings)
    protocol=checked(manifest['protocol_path'],manifest['protocol_sha256'],base,bindings)
    pool_binding=manifest['pool_binding'];pool=read_json(checked(pool_binding['path'],pool_binding['sha256'],base,bindings));row=next((row for row in pool['games'] if row['id']==manifest['case_id']),None)
    if not row or any(row[key]!=pool_binding[key] for key in ('task_uid','layout','layout_group','game_sha256','traj_sha256','game_member','traj_member')):raise IntegrityError('POOL task/layout identity mismatch')
    source=None;source_fee=None
    if manifest['stage']=='ordinary_reset':
        if any(manifest.get(key) is not None for key in ('source_root','source_binding','cohort_binding')) or receipt.get('source_binding_charge_once') is not None:raise IntegrityError('ordinary reset cannot carry a collector source/cohort')
        total=read_json(protocol)['total_caps']
        if manifest.get('caps')!=total or any(type(v) is not int for v in total.values()) or any(type(v) is not int for v in manifest['caps'].values()) or total.get('posts')!=128 or total.get('seconds')!=1800 or total.get('world_actions')!=100 or manifest.get('world_step_cap')!=100:raise IntegrityError('ordinary reset must use protocol total caps and100 world steps')
        reset=read_json(root/'initial_reset.json')
        if (root/'task.txt').read_bytes()!=ordinary_reset_prompt(reset).encode():raise IntegrityError('ordinary reset prompt differs from empty-history renderer')
        replay=receipt.get('replay_control_cost')
        if replay is not None and (type(replay) is not dict or replay.get('control_world_actions')!=0):raise IntegrityError('ordinary reset fabricated replay cost')
    else:
        if manifest.get('cohort_binding'):
            cohort=manifest['cohort_binding'];checked(cohort['path'],cohort['sha256'],base,bindings)
        source=within(manifest['source_root'],base);expected_names={'manifest.json','receipt.json','execute_world.jsonl'}
        if {Path(path).name for path in manifest['source_binding']}!=expected_names or any(Path(path).parent!=source for path in manifest['source_binding']):raise IntegrityError('unexpected collector-source reference paths')
        for path,digest in manifest['source_binding'].items():checked(path,digest,base,bindings)
        if receipt['source_binding_charge_once']!=manifest['source_binding']:raise IntegrityError('source cost reference mismatch')
        source_receipt=read_json(source/'receipt.json');source_manifest=read_json(source/'manifest.json')
        if source_receipt['manifest_sha256']!=manifest['source_binding'][str(source/'manifest.json')] or source_manifest['pool_binding']['task_uid']!=row['task_uid'] or source_receipt['won'] is not False:raise IntegrityError('source is not this task failure')
        source_fee={'source_root':str(source),'source_receipt_sha256':manifest['source_binding'][str(source/'receipt.json')],'provider_usage':source_receipt.get('provider_usage'),'real_model_calls':source_receipt.get('real_model_calls'),'charge_once':True}
    for round in receipt['rounds']:
        raw=root/('raw_'+str(round['round'])+'.jsonl');checked(raw,round['raw_sha256'],base,bindings)
        if type(round['exit']) is not int:raise IntegrityError('invalid actor exit metadata')
    totals=usage_sum(receipt)
    if totals!=entry['provider_usage'] or receipt['real_model_calls']!=entry['real_model_calls'] or receipt['forwarded_model_posts']!=len(receipt['response_receipts']):raise IntegrityError('batch/provider count mismatch')
    if receipt['real_model_calls']!=receipt['forwarded_model_posts'] or receipt['world_actions']!=entry['new_world_actions'] or type(receipt['won']) is not bool:raise IntegrityError('batch/world count mismatch')
    records=provider_records(root,manifest,receipt,bindings);world_records(root,manifest,receipt,row,source,bindings)
    states=[public(e['state']) for e in jsonl(root/'execute_world.jsonl') if e.get('event') in {'reset','step'}]
    round_structure(root,manifest,receipt,records,states,bindings)
    cost={'root':str(root),'receipt_sha256':entry['receipt_sha256'],'real_model_calls':receipt['real_model_calls'],'model_posts':receipt.get('model_posts'),'provider_usage':totals,'provider_cached_input_tokens':receipt.get('provider_cached_input_tokens'),'elapsed_seconds':receipt['elapsed_seconds'],'replay_control_cost':receipt.get('replay_control_cost'),'native_won':receipt['won'],'status':receipt['status'],'cache_is_input_subset':True}
    return root,manifest,receipt,row,source,source_fee,cost


def align_trajectory(root,m,r,pool_row,source,bindings):
    if r['errors'] or r['model_relay_errors'] or any(round['exit']!=0 for round in r['rounds']):raise UnsupportedTrajectory('successful flag with execution/relay/actor error')
    steps,n=world_records(root,m,r,pool_row,source,bindings)
    return align_observed_chat(root,m,r,steps,n,bindings)


def align_observed_chat(root,m,r,steps,n,bindings,*,supervise=True):
    if supervise and r.get('won') is not True:raise IntegrityError('positive supervision requires native won')
    records=provider_records(root,m,r,bindings)
    states=[public(e['state']) for e in jsonl(root/'execute_world.jsonl') if e.get('event') in {'reset','step'}]
    raw,boundaries,continuations=round_structure(root,m,r,records,states,bindings)
    raw_tools=[e['part'] for e in raw if e.get('type')=='tool_use'];by_id={p['callID']:p for p in raw_tools}
    if len(by_id)!=len(raw_tools):raise IntegrityError('duplicate raw tool call id')
    messages=None;tools=None;turns=[];used=set();position=n;request_bindings=[];prefix_checks=[]
    records=provider_records(root,m,r,bindings)
    for index,response in enumerate(r['response_receipts'],1):
        request,body=records[index-1];path=root/'requests'/(f'{index:05}'+'.json')
        if index in boundaries:
            messages.append(copy.deepcopy(boundaries[index]))
        if messages is None:
            task_delivery(root,m,r,request,bindings);messages=copy.deepcopy(request['messages']);tools=copy.deepcopy(request.get('tools'))
        else:
            if semantic_messages(request['messages'])!=semantic_messages(messages) or request.get('tools')!=tools:raise IntegrityError('provider conversation lost/changed observed context')
            # Keep native SSE completion strings; only JSON tool-argument serialization may differ in a later SDK request.
        prefix_checks.append({'post_index':index,'forwarded_request_sha256':object_sha(request),'exact_prefix_equal':request['messages']==messages,'tool_argument_JSON_equivalence_verified':True})
        assistant,metadata=observed_assistant(body.read_bytes())
        if metadata['usage']!=response['usage']:raise IntegrityError('native SSE usage mismatch')
        at=len(messages);messages.append(assistant);calls=assistant.get('tool_calls') or []
        if len(calls)>1:raise UnsupportedTrajectory('multiple actions in one assistant completion')
        if not calls:
            turns.append({'message_index':at,'post_index':index,'supervised':False,'fields':[],'reason':'final_or_non_action_text','ignored_reasoning_utf8_bytes':metadata['ignored_reasoning_utf8_bytes']});continue
        call=calls[0];cid=call['id']
        if cid not in by_id or cid in used:raise UnsupportedTrajectory('missing/duplicate native assistant to raw tool mapping')
        part=by_id[cid];args=read_json_text(call['function']['arguments']);raw_args,output,exit_code,result=tool_output(part)
        if call['function']['name']!='bash' or args!=raw_args:raise IntegrityError('native tool arguments differ from raw execution')
        action=parse_command(args.get('command'));used.add(cid);success=False;reason='failed_tool_context'
        if 'error' in result:
            if set(result)!={'error'} or exit_code==0:raise UnsupportedTrajectory('ambiguous error tool result')
        else:
            if exit_code!=0:raise UnsupportedTrajectory('nonzero exit with native state')
            if set(result)!=set(STATE_KEYS):raise UnsupportedTrajectory('client output contains fields outside the public state schema')
            native=public(result)
            if position>=len(steps) or steps[position]['action']!=action or public(steps[position]['state'])!=native:raise UnsupportedTrajectory('tool response has no matching accepted native world action')
            position+=1;success=True;reason='accepted_native_action_not_optimality_claim'
        messages.append({'role':'tool','tool_call_id':cid,'content':output})
        turns.append({'message_index':at,'post_index':index,'supervised':success and supervise,'fields':['content','tool_calls'] if success and supervise else [],'reason':reason,'call_id':cid,'world_action':action,'exit_code':exit_code,'client_error':result.get('error'),'ignored_reasoning_utf8_bytes':metadata['ignored_reasoning_utf8_bytes']})
        request_bindings.append({'post_index':index,'call_id':cid,'request_sha256':bindings[str(path)],'SSE_sha256':response['body_sha256']})
    if used!=set(by_id) or position!=len(steps):raise UnsupportedTrajectory('unmapped raw tool or unaccounted native world actions')
    positive=[t['message_index'] for t in turns if t['supervised']]
    if not positive and supervise:raise UnsupportedTrajectory('no qualified assistant action completion')
    bindings[str(root/'execute_world.jsonl')]=sha(root/'execute_world.jsonl')
    return {'messages':messages,'tools':tools,'supervised_assistant_turn_indices':positive,'assistant_turn_metadata':turns,
            'role_mask_metadata':[{'message_index':i,'role':message['role'],'supervised':i in positive,'fields':['content','tool_calls'] if i in positive else []} for i,message in enumerate(messages)],'action_alignment':request_bindings,'conversation_prefix_checks':prefix_checks,'ordinary_continuation_checks':continuations,'serialization_policy':'original first-request context, native SSE assistant completions and raw executed tool outputs; later SDK tool-argument JSON reserialization only checked for equivalence','final_text_supervised':False,'loss_scope':'accepted-action current assistant public content plus tool_calls; compile completion/EOS later','not_stepwise_optimality':True}


def build_supervision(batch_results,*,backend='teacher27b',stage='drop_recent',study_root=ST):
    if backend!='teacher27b' or stage not in STAGES:raise IntegrityError('this exporter selects teacher27b and one explicit eligible stage only')
    bindings={};trajectories=[];exclusions=[];episodes={};sources={};experience={};groups=set();seen=set();batch_refs=[]
    for batch_path,expected_sha in batch_results:
        path=checked(batch_path,expected_sha,study_root,bindings);batch=read_json(path);status=str(batch.get('status','')).upper()
        if (type(batch.get('completed_count')) is not int or batch['completed_count']!=len(batch.get('results',[])) or batch.get('error') is not None or
                'RUNNING' in status or not (status.startswith('ALL') or status.startswith('COMPLETED') or status.startswith('TERMINAL')) or not any(word in status for word in ['RETURNED','COMPLETE','TERMINAL'])):
            raise IntegrityError('batch RESULT is not explicitly fully terminal')
        batch_refs.append({'path':str(path),'sha256':expected_sha})
        for entry in batch['results']:
            key=(entry['root'],entry['receipt_sha256'])
            if key in seen:
                exclusions.append({'root':entry['root'],'reason':'duplicate_episode_reference','receipt_sha256':entry['receipt_sha256'],'cost_already_counted':True});continue
            seen.add(key)
            if entry.get('backend')!=backend or entry.get('stage')!=stage:
                exclusions.append({'root':entry['root'],'reason':'unselected_backend_or_stage','batch_summary_only':True,'reported_real_calls':entry.get('real_model_calls'),'reported_provider_usage':entry.get('provider_usage')});continue
            root,m,r,pool_row,source,source_fee,cost=episode_inputs(entry,study_root,bindings);episodes[key]=cost
            if source_fee:sources[source_fee['source_receipt_sha256']]=source_fee
            assignment=m.get('experience_assignment')
            if stage!='ordinary_reset' and assignment is not None:experience[digest_key(assignment)]=assignment
            identity={'task_uid':pool_row['task_uid'],'task_family':pool_row['family'],'layout':pool_row['layout'],'layout_group':pool_row['layout_group'],'collector_source_receipt_sha256':source_fee['source_receipt_sha256'] if source_fee else None}
            group=digest_key({key:value for key,value in identity.items() if key!='collector_source_receipt_sha256'})
            if r['won'] is not True:
                cost['supervision_disposition']='native_not_won'
                exclusions.append({'root':str(root),'reason':'native_not_won','group':identity,'cost_reference':entry['receipt_sha256'],'errors':r['errors'],'relay_errors':r['model_relay_errors']});continue
            if group in groups:
                cost['supervision_disposition']='duplicate_source_task_layout'
                exclusions.append({'root':str(root),'reason':'duplicate_source_task_layout','group':identity,'cost_reference':entry['receipt_sha256']});continue
            try:row=align_trajectory(root,m,r,pool_row,source,bindings)
            except UnsupportedTrajectory as exc:
                cost['supervision_disposition']='supervision_mapping_rejected'
                exclusions.append({'root':str(root),'reason':'supervision_mapping_rejected','details':str(exc),'group':identity,'cost_reference':entry['receipt_sha256']});continue
            cost['supervision_disposition']='accepted_development_candidate'
            groups.add(group);trajectories.append({'trajectory_id':entry['receipt_sha256'],'root':str(root),'backend':backend,'stage':stage,'source_group':group,'group_identity':identity,'pool_binding':m['pool_binding'],'receipt_sha256':entry['receipt_sha256'],'manifest_sha256':r['manifest_sha256'],'development_status':'exposed_development_supervision_candidate_not_confirmation','requires_per_turn_token_compilation':True,**row})
    totals={key:sum(e['provider_usage'][key] for e in episodes.values()) for key in ('prompt_tokens','completion_tokens','total_tokens')}
    return {'trajectories':trajectories,'exclusions':exclusions,'ledger':{'recovery_episodes_once':list(episodes.values()),'selected_recovery_real_calls':sum(e['real_model_calls'] for e in episodes.values()),'selected_recovery_provider_usage':totals,'collector_sources_once':list(sources.values()),'original_experience_references_once':list(experience.values()),'source_fees_not_repeated_per_turn':True},'manifest':{'schema':'alfworld_recovery_openai_supervision_candidates_v2','batch_results':batch_refs,'backend':backend,'stage':stage,'trajectory_count':len(trajectories),'source_task_layout_groups':len(groups),'group_key_fields':['task_uid','task_family','layout','layout_group'],'different_stage_exports_are_not_independent_tasks':True,'input_artifact_sha256':bindings,'exporter_sha256':sha(__file__),'native_SSE_helper_sha256':sha(LEGACY),'standard_library_only':True,'model_training_tokenization_calls':0,'development_only':True,'old_single_completion_training_runner_compatible':False,'limits':['at most two controller rounds; only frozen same-session fixed Continue accepted','strict one canonical world client action per Bash command','accepted execution is not stepwise optimality','multi-turn assistant masks require subsequent per-turn tokenizer compilation']}}


def digest_key(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def export_supervision(bundle,output_root):
    root=Path(output_root)
    if not root.is_absolute() or root.resolve()!=root or any(p.is_symlink() for p in [root,*root.parents]):raise IntegrityError('output must be a fresh unaliased absolute directory')
    root.mkdir(parents=True,exist_ok=False)
    payload=b''.join(json.dumps(row,ensure_ascii=False,separators=(',',':')).encode()+b'\n' for row in bundle['trajectories'])
    with (root/'trajectories.jsonl').open('xb') as out:out.write(payload)
    for name,key in [('exclusions.json','exclusions'),('ledger.json','ledger')]:
        with (root/name).open('x',encoding='utf8',newline='\n') as out:json.dump(bundle[key],out,ensure_ascii=False,indent=2);out.write('\n')
    manifest={**bundle['manifest'],'output_sha256':{name:sha(root/name) for name in ['trajectories.jsonl','exclusions.json','ledger.json']}}
    with (root/'data_manifest.json').open('x',encoding='utf8',newline='\n') as out:json.dump(manifest,out,indent=2);out.write('\n')
    return {'output_root':str(root),'manifest_sha256':sha(root/'data_manifest.json'),'trajectory_count':len(bundle['trajectories']),'supervised_assistant_turns':sum(len(row['supervised_assistant_turn_indices']) for row in bundle['trajectories']),'excluded_entries':len(bundle['exclusions'])}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--batch',type=Path,action='append',required=True);parser.add_argument('--batch-sha',action='append',required=True);parser.add_argument('--stage',choices=STAGES,default='drop_recent');parser.add_argument('--output-root',type=Path,required=True);args=parser.parse_args(argv)
    if len(args.batch)!=len(args.batch_sha):parser.error('pair each explicit batch path with its SHA')
    print(json.dumps(export_supervision(build_supervision(list(zip(args.batch,args.batch_sha)),stage=args.stage),args.output_root)))

if __name__=='__main__':main()
