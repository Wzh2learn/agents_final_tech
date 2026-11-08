"""CPU-only first-response channel diagnosis; never sends or executes tools."""
from pathlib import Path
import copy, hashlib, json

try:
    from jsonschema import Draft202012Validator
except ImportError:
    Draft202012Validator=None

RESULT_SHA='82ff3d887d6e4014c7f0bbc002e0b976d682e9c84750a7b9ad7659715041e93d'
CASES=('nexttrain_look_01','nexttrain_look_03','nexttrain_look_05')
SCOPE='FIRST_RESPONSE_CHANNEL_ONLY; NO_TOOL_EXECUTION_OR_TASK_OUTCOME'


def require(ok,reason):
    if not ok:raise ValueError(reason)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def _non_json(value):raise ValueError('non-JSON constant: '+value)


def _json(value):return json.loads(value,parse_constant=_non_json)


def declared_tools(payload):
    result={}
    def refs(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key in ('$ref','$dynamicRef'):require(isinstance(item,str) and item.startswith('#'),'external schema retrieval forbidden')
                refs(item)
        elif isinstance(value,list):
            for item in value:refs(item)
    require(isinstance(payload.get('tools'),list) and payload['tools'],'function tools required')
    for tool in payload['tools']:
        require(isinstance(tool,dict) and tool.get('type')=='function','only declared function tools supported')
        f=tool.get('function',{});name=f.get('name');schema=f.get('parameters')
        require(isinstance(name,str) and name and name not in result and isinstance(schema,dict),'malformed/duplicate tool declaration')
        refs(schema)
        result[name]=schema
    return result


def parse_sse(rawbytes,payload):
    schemas=declared_tools(payload);events=[]
    for line in rawbytes.decode('utf-8').splitlines():
        if not line or line.startswith(':'):continue
        require(line.startswith('data:'),'unexpected SSE field');events.append(line[5:].strip())
    require(events and events.count('[DONE]')==1 and events[-1]=='[DONE]','unique final DONE required')
    chunks=[_json(e) for e in events[:-1]];usages=[];finishes=[];calls={};content=[];reasoning=[];channel_errors=[]
    for chunk in chunks:
        require(isinstance(chunk,dict) and not chunk.get('error'),'SSE error/malformed chunk')
        if chunk.get('usage'):usages.append(chunk['usage'])
        for choice in chunk.get('choices',[]):
            require(choice.get('index',0)==0,'only one response choice supported')
            if choice.get('finish_reason') is not None:finishes.append(choice['finish_reason'])
            delta=choice.get('delta',{})
            for key,target in (('content',content),('reasoning_content',reasoning)):
                if delta.get(key) is not None:require(isinstance(delta[key],str),'non-text delta');target.append(delta[key])
            for part in delta.get('tool_calls',[]):
                index=part.get('index');require(type(index) is int and index>=0,'tool-call index required')
                call=calls.setdefault(index,dict(id=None,name='',arguments_raw=''))
                require(part.get('type','function')=='function','non-function response call')
                if part.get('id'):
                    if call['id'] not in (None,part['id']):call['id_conflict']=True
                    else:call['id']=part['id']
                f=part.get('function',{});name=f.get('name','');argument=f.get('arguments','')
                require(isinstance(name,str) and isinstance(argument,str),'non-string function delta')
                call['name']+=name
                call['arguments_raw']+=argument
    require(len(finishes)==1 and finishes[0] in ('stop','tool_calls','length'),'one supported finish_reason required')
    usage=usages[-1] if usages else None;cache=None
    if usage is not None:
        require(isinstance(usage,dict) and all(type(usage.get(k)) is int and usage[k]>=0 for k in ('prompt_tokens','completion_tokens','total_tokens')) and
            usage['total_tokens']==usage['prompt_tokens']+usage['completion_tokens'],'invalid final usage')
        cache=(usage.get('prompt_tokens_details') or {}).get('cached_tokens')
        require(cache is None or type(cache) is int and 0<=cache<=usage['prompt_tokens'],'cache must be input subset')
    ids=[call['id'] for call in calls.values()]
    for index,call in sorted(calls.items()):
        call.update(index=index,arguments=None,schema_validated=False,schema_status='UNVERIFIED')
        try:
            require(isinstance(call['id'],str) and bool(call['id'].strip()) and ids.count(call['id'])==1 and not call.get('id_conflict'),'missing/duplicate/conflicting call id')
            require(call['name'] in schemas,'undeclared tool name');call['arguments']=_json(call['arguments_raw'])
            schema=schemas[call['name']];supported=Draft202012Validator is not None and schema.get('$schema','https://json-schema.org/draft/2020-12/schema') in ('https://json-schema.org/draft/2020-12/schema','https://json-schema.org/draft/2020-12/schema#')
            if supported:
                try:Draft202012Validator.check_schema(schema)
                except Exception:supported=False
            if supported:Draft202012Validator(schema).validate(call['arguments']);call.update(schema_validated=True,schema_status='VALID')
            call['validation']='JSONSCHEMA_VALID' if call['schema_validated'] else 'JSON_SYNTAX_AND_DECLARED_NAME_ONLY'
        except Exception as exc:
            call.update(validation='INVALID',schema_status='INVALID',error=type(exc).__name__+': '+str(exc));channel_errors.append(call['error'])
    channel='NO_TOOL_CALL' if not calls else 'INVALID_TOOL_CALL' if channel_errors else 'TOOL_CALL_SCHEMA_VALID' if all(c['schema_validated'] for c in calls.values()) else 'TOOL_CALL_SCHEMA_UNVERIFIED'
    return dict(scope=SCOPE,done_count=1,usage=usage,usage_known=usage is not None,usage_updates=len(usages),cached_input_tokens=cache,
        finish_reason=finishes[0],truncated=finishes[0]=='length',content=''.join(content),reasoning_content=''.join(reasoning),
        tool_calls=[calls[i] for i in sorted(calls)],errors=[] if usage is not None else ['USAGE_UNKNOWN'],channel_errors=channel_errors,
        channel_status=channel,schema_library_available=Draft202012Validator is not None)


def validate_mutation(original,changed):
    restored=copy.deepcopy(changed);restored['tool_choice']=original.get('tool_choice')
    require(original.get('tool_choice')=='auto' and changed.get('tool_choice')=='required' and restored==original and
        json.dumps(restored,separators=(',',':'))==json.dumps(original,separators=(',',':')),'only auto to required may change, preserving order')


def required_payload(original):
    declared_tools(original);changed=copy.deepcopy(original);changed['tool_choice']='required'
    validate_mutation(original,changed);return changed


def _bound(path,digest):
    path=Path(path);require(path.is_absolute() and path.resolve()==path and not any(p.is_symlink() for p in (path,*path.parents)),'unsafe source path')
    raw=path.read_bytes();require(sha(raw)==digest,'source binding changed: '+str(path));return raw


def prepare_probe(result_path,result_sha=RESULT_SHA):
    require(result_sha==RESULT_SHA,'only the closed B6 cohort is accepted')
    result_path=Path(result_path);result=_json(_bound(result_path,result_sha))
    require(result['status']=='ALL6_REFERENCE_COMPONENT_RETURNED' and result['completed_receipts']==6 and result['unknown_usage_model_posts']==0 and
        all(result.get(k) is True for k in ('restored_healthy','shared35_unchanged','shared27_unchanged')) and
        not any(result.get(k) for k in ('error','aggregation_errors','aggregation_error','unrun','unclosed_attempts','restoration_error')),'source batch not closed')
    prepared=[]
    for case in CASES:
        rows=[r for r in result['cases'] if r['case']==case];require(len(rows)==1 and rows[0]['status']=='CLOSED_AUDITED','source slot not unique/closed')
        row=rows[0];root=Path(row['root']);require(root.parts[-4:]==(case,'ordinary_reset','student8b','attempt_v6'),'wrong source namespace')
        refs={str(result_path):result_sha};files={}
        for name in ('receipt.json','manifest.json','requests/00001.body','requests/00001.json','responses/00001.body','responses/00001.body.receipt.json','raw_1.jsonl','execute_world.jsonl'):
            path=root/name;digest=row['raw_bindings'].get(str(path));require(isinstance(digest,str),'source raw binding missing')
            files[name]=_bound(path,digest);refs[str(path)]=digest
        receipt=_json(files['receipt.json']);manifest=_json(files['manifest.json']);response=_json(files['responses/00001.body.receipt.json'])
        require(sha(files['receipt.json'])==row['receipt_sha256'] and sha(files['manifest.json'])==row['manifest_sha256'] and
            receipt['manifest_sha256']==row['manifest_sha256'] and receipt['case_id']==case and not receipt['errors'] and not receipt['model_relay_errors'] and
            receipt['unknown_usage_model_posts']==0 and receipt['status']=='RETURNED','source episode not closed')
        states=[r['state'] for r in map(_json,files['execute_world.jsonl'].splitlines()) if r.get('event') in ('reset','step')]
        require(states and states[-1]==receipt['final_world_state'] and receipt['won']==states[-1]['won'],'source native outcome differs')
        original=_json(files['requests/00001.body']);record=_json(files['requests/00001.json']);declared_tools(original)
        require(original==record['forwarded'] and files['requests/00001.body']==json.dumps(original,separators=(',',':')).encode() and
            original.get('stream') is True and original['max_tokens']==8192 and manifest['runtime_profile_override']['profile']['context']==32768,'source forwarded bytes/config differ')
        parsed=parse_sse(files['responses/00001.body'],original)
        require(response==receipt['response_receipts'][0] and response['status']==200 and response['complete'] is True and response['body_sha256']==sha(files['responses/00001.body']) and
            response['body_bytes']==len(files['responses/00001.body']) and parsed['usage_known'] and parsed['usage']==response['usage'] and
            parsed['finish_reason']=='stop' and not parsed['tool_calls'] and not parsed['errors'],'source first response is not plain stop')
        payload=required_payload(original)
        body=json.dumps(payload,separators=(',',':')).encode();require(len(body)<8*1024**2,'independent wire bound exceeded')
        prepared.append(dict(case=case,source_refs=refs,source_body_sha256=sha(files['requests/00001.body']),payload=payload,body=body,
            body_sha256=sha(body),first_source_response=parsed,limits=dict(physical_posts=1,total_tokens_upper_bound=32768,max_output_tokens=8192,combined_wire_bytes=8*1024**2)))
    return dict(scope=SCOPE,module_sha256=sha(Path(__file__).read_bytes()),execution_authorized=False,cases=prepared,
        limits=dict(physical_posts=3,total_tokens_upper_bound=98304,combined_wire_bytes=3*8*1024**2))
