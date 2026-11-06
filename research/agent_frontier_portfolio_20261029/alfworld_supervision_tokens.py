"""CPU tokenizer compilation of hash-verified real ALF assistant action turns.

The actual forwarded request supplies every prefix, not the trajectory view.
No model weights, inference, training, truncation, or shared service operations.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys

ST=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106/context_study_v1')
EXPORTER=Path(__file__).with_name('alfworld_recovery_supervision.py')
NATIVE=Path(__file__).with_name('alfworld_correction_data_20261106.py')
QWEN_HEADER='<|im_start|>assistant\n<think>\n\n</think>\n\n'

class IntegrityError(ValueError):pass
class TokenExclusion(ValueError):
    def __init__(self,reason,**details):super().__init__(reason);self.reason=reason;self.details=details

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def text_sha(value):return hashlib.sha256(value.encode()).hexdigest()
def object_sha(value):return text_sha(json.dumps(value,separators=(',',':')))
def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def module(path):
    spec=importlib.util.spec_from_file_location('qualified_'+Path(path).stem,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def load_export(path,expected_sha,study_root=ST):
    """Revalidate exporter, native parser, every selected episode, masks and costs."""
    path=Path(path)
    if path.resolve()!=path or path.is_symlink() or sha(path)!=expected_sha:raise IntegrityError('export manifest hash/path mismatch')
    frozen=read(path)
    if frozen.get('exporter_sha256')!=sha(EXPORTER) or frozen.get('native_SSE_helper_sha256')!=sha(NATIVE):raise IntegrityError('frozen exporter/native parser code hash differs')
    exporter=module(EXPORTER)
    exporter.within(path,study_root)
    if frozen.get('schema')!='alfworld_recovery_openai_supervision_candidates_v2' or frozen.get('backend')!='teacher27b':raise IntegrityError('unsupported supervision export schema/backend')
    for name in ['trajectories.jsonl','exclusions.json','ledger.json']:
        exporter.checked(path.parent/name,frozen['output_sha256'][name],study_root,{})
    rows=[json.loads(line) for line in (path.parent/'trajectories.jsonl').read_text(encoding='utf8').splitlines()]
    rebuilt=exporter.build_supervision([(Path(r['path']),r['sha256']) for r in frozen['batch_results']],stage=frozen['stage'],study_root=study_root)
    if rows!=rebuilt['trajectories'] or read(path.parent/'exclusions.json')!=rebuilt['exclusions'] or read(path.parent/'ledger.json')!=rebuilt['ledger'] or frozen['input_artifact_sha256']!=rebuilt['manifest']['input_artifact_sha256']:
        raise IntegrityError('export rows/masks/actions/source ledger differ from frozen actual evidence')
    if frozen['trajectory_count']!=len(rows) or frozen['source_task_layout_groups']!=len({r['source_group'] for r in rows}):raise IntegrityError('export count/group mismatch')
    return exporter,frozen,rows,rebuilt['ledger']


def load_tokenizer(model_path):
    # Process-local offline flags; no model class, device operation, or weight load.
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(str(model_path),local_files_only=True,trust_remote_code=False,use_fast=True)


def installed_version(name):
    try:return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:return None


def tokenizer_binding(model_path,tokenizer):
    path=Path(model_path)
    if not path.is_absolute() or path.resolve()!=path:raise IntegrityError('tokenizer path must be canonical and local')
    cfg=read(path/'config.json');meta=read(path/'tokenizer_config.json')
    if cfg.get('model_type')!='qwen3' or cfg.get('architectures')!=['Qwen3ForCausalLM'] or tokenizer.chat_template!=meta.get('chat_template'):raise IntegrityError('not the pinned local Qwen3 chat template')
    if tokenizer.eos_token_id!=tokenizer.convert_tokens_to_ids('<|im_end|>'):raise IntegrityError('Qwen assistant end token differs')
    return {'model_path':str(path),'files_sha256':{name:sha(path/name) for name in ['config.json','tokenizer_config.json','tokenizer.json']},'chat_template_sha256':text_sha(tokenizer.chat_template),'enable_thinking':False,'eos_token_id':tokenizer.eos_token_id,'pad_token_id':tokenizer.pad_token_id,'weights_loaded':False,'tokenizer_class':type(tokenizer).__module__+'.'+type(tokenizer).__name__,'transformers_version':installed_version('transformers'),'tokenizers_version':installed_version('tokenizers')}


def token_ids(value):
    if hasattr(value,'keys'):value=value['input_ids']
    if type(value) is not list or any(type(t) is not int for t in value):raise IntegrityError('unexpected tokenizer batch/type')
    return value


def encode_completion(request,assistant,tokenizer,max_length):
    if type(max_length) is not int or max_length<=0:raise IntegrityError('max_length must be a positive integer')
    if assistant.get('role')!='assistant' or len(assistant.get('tool_calls') or [])!=1 or any(key in assistant for key in ['reasoning_content','reasoning','analysis']):raise IntegrityError('target is not one public assistant action completion')
    # The frozen Qwen template directly accepts JSON argument strings. Validate,
    # but retain those strings and all actual context/tool schema dictionary order.
    name=assistant['tool_calls'][0]['function']['name']
    if name not in {tool['function']['name'] for tool in request.get('tools',[])}:raise IntegrityError('target tool was not exposed')
    for message in request['messages']+[assistant]:
        for call in message.get('tool_calls') or []:
            arg=call['function']['arguments']
            if type(arg) is str:
                parsed=json.loads(arg)
                if type(parsed) is not dict:raise IntegrityError('tool arguments not JSON object')
            elif type(arg) is not dict:raise IntegrityError('unsupported native tool arguments')
    messages=copy.deepcopy(request['messages']);tools=copy.deepcopy(request.get('tools'));options=dict(tools=tools,enable_thinking=False,truncation=False,return_dict=False)
    prefix_text=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,**options)
    full_text=tokenizer.apply_chat_template(messages+[copy.deepcopy(assistant)],tokenize=False,add_generation_prompt=False,**options)
    if not prefix_text.endswith(QWEN_HEADER):raise TokenExclusion('unexpected_Qwen_generation_header',rendered_prefix_tail=prefix_text[-100:])
    prefix=token_ids(tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,**options))
    full=token_ids(tokenizer.apply_chat_template(messages+[copy.deepcopy(assistant)],tokenize=True,add_generation_prompt=False,**options))
    if len(full)>max_length:raise TokenExclusion('length_exceeds_cap_no_truncation',prompt_tokens=len(prefix),full_tokens=len(full),max_length=max_length)
    if len(full)<=len(prefix) or full[:len(prefix)]!=prefix:
        mismatch=next((i for i,(a,b) in enumerate(zip(prefix,full)) if a!=b),min(len(prefix),len(full)))
        raise TokenExclusion('generation_full_token_prefix_mismatch',first_mismatch=mismatch,prompt_tokens=len(prefix),full_tokens=len(full),rendered_text_prefix_equal=full_text.startswith(prefix_text),prefix_tail_ids=prefix[max(0,mismatch-4):mismatch+5],full_boundary_ids=full[max(0,mismatch-4):mismatch+5],diagnosis='Qwen generation/full template or BPE boundary differs; no token slice accepted',possible_explicit_construction='Use unchanged rendered generation prefix plus the public Qwen completion after the identical empty-think header and im_end, then retokenize together and recheck exact prefix; not applied automatically')
    ends=[i for i in range(len(prefix),len(full)) if full[i]==tokenizer.eos_token_id]
    if len(ends)!=1 or ends[0]<=len(prefix):raise TokenExclusion('missing_ambiguous_or_zero_target_EOS',end_token_positions=ends,prompt_tokens=len(prefix))
    end=ends[0]+1
    if tokenizer.decode(full[end:]).strip():raise TokenExclusion('non_whitespace_after_assistant_EOS')
    labels=[-100]*len(full);labels[len(prefix):end]=full[len(prefix):end]
    if not any(x!=-100 for x in labels):raise TokenExclusion('zero_supervised_target')
    return {'input_ids':full,'attention_mask':[1]*len(full),'labels':labels,'prompt_token_count':len(prefix),'sequence_length':len(full),'supervised_tokens':end-len(prefix),'assistant_end_index':end-1,'prefix_token_alignment_verified':True,'rendered_prefix_sha256':text_sha(prefix_text),'rendered_full_sha256':text_sha(full_text),'template_adaptations':{'arguments':'unchanged native JSON strings or objects supported by frozen Qwen template','content_leading_newlines_trimmed_by_Qwen_template':len(assistant.get('content',''))-len(assistant.get('content','').lstrip('\n'))},'loss_scope':'only current public assistant content and tool_call plus im_end; template trailing whitespace masked'}


def compile_export(export_manifest,expected_sha,model_path,*,max_length=32768,tokenizer=None,study_root=ST):
    if type(max_length) is not int or max_length<=0:raise IntegrityError('max_length must be a positive integer')
    exporter,frozen,trajectories,ledger=load_export(export_manifest,expected_sha,study_root)
    injected=tokenizer is not None
    tokenizer=tokenizer if tokenizer is not None else load_tokenizer(model_path);assets=tokenizer_binding(model_path,tokenizer);rows=[];exclusions=[];seen=set();attempts=0
    for trajectory in trajectories:
        positives=set(trajectory['supervised_assistant_turn_indices']);aligned={a['post_index']:a for a in trajectory['action_alignment']}
        for turn in trajectory['assistant_turn_metadata']:
            if not turn['supervised']:continue
            if turn['message_index'] not in positives or turn['fields']!=['content','tool_calls'] or turn.get('exit_code')!=0 or turn.get('client_error') is not None:raise IntegrityError('action/mask is not accepted whole current assistant completion')
            at=turn['post_index'];alignment=aligned[at];key=(trajectory['trajectory_id'],at,alignment['call_id'])
            if key in seen:raise IntegrityError('duplicate supervised native turn')
            seen.add(key);attempts+=1;root=Path(trajectory['root']);req_path=root/f'requests/{at:05}.json';sse_path=root/f'responses/{at:05}.body'
            if sha(req_path)!=alignment['request_sha256'] or sha(sse_path)!=alignment['SSE_sha256']:raise IntegrityError('actual request/native SSE hash differs')
            request=read(req_path)['forwarded'];assistant,metadata=exporter.native_assistant(sse_path.read_bytes())
            if len(assistant.get('tool_calls') or [])!=1 or assistant['tool_calls'][0]['id']!=turn['call_id'] or alignment['call_id']!=turn['call_id']:raise IntegrityError('native target call identity differs')
            action=exporter.parse_command(json.loads(assistant['tool_calls'][0]['function']['arguments'])['command'])
            if action!=turn['world_action']:raise IntegrityError('native target action differs from accepted world action')
            provenance={'row_id':text_sha(json.dumps(key)),'trajectory_id':trajectory['trajectory_id'],'source_group':trajectory['source_group'],'source_role':'teacher','backend':trajectory['backend'],'provider_model_id':request['model'],'stage':trajectory['stage'],'task_uid':trajectory['group_identity']['task_uid'],'layout_group':trajectory['group_identity']['layout_group'],'post_index':at,'call_id':turn['call_id'],'world_action':action,'actual_request_path':str(req_path),'actual_request_sha256':alignment['request_sha256'],'actual_forwarded_payload_sha256':object_sha(request),'native_SSE_path':str(sse_path),'native_SSE_sha256':alignment['SSE_sha256'],'formation_ledger_key':trajectory['receipt_sha256'],'ignored_reasoning_utf8_bytes':metadata['ignored_reasoning_utf8_bytes'],'development_only':True,'prefix_source':'actual forwarded request, not reconstructed trajectory view'}
            try:encoded=encode_completion(request,assistant,tokenizer,max_length)
            except TokenExclusion as exc:exclusions.append({**provenance,'reason':exc.reason,'details':exc.details});continue
            rows.append({**provenance,**encoded})
    return {'rows':rows,'exclusions':exclusions,'formation_ledger':ledger,'manifest':{'schema':'alfworld_current_assistant_token_candidates_v1','source_export':{'path':str(export_manifest),'sha256':expected_sha,'exporter_sha256':frozen['exporter_sha256'],'native_SSE_helper_sha256':frozen['native_SSE_helper_sha256']},'compiler_sha256':sha(__file__),'qualification_mode':'INJECTED_TEST_TOKENIZER' if injected else 'LOCAL_HF_TOKENIZER_CPU','tokenizer':assets,'max_length':max_length,'action_candidates':attempts,'compiled_rows':len(rows),'excluded_turns':len(exclusions),'source_groups':len({r['source_group'] for r in trajectories}),'compiled_source_groups':len({r['source_group'] for r in rows}),'max_sequence_length':max((r['sequence_length'] for r in rows),default=0),'supervised_tokens':sum(r['supervised_tokens'] for r in rows),'source_costs_charged_once_not_per_training_turn':True,'different_stages_or_turns_are_not_independent_tasks':True,'long_rows_truncated':False,'old_single_completion_trainrunner_adapted':False,'model_weight_generation_training_GPU_calls':0,'torch_package_imported_by_dependencies':'torch' in sys.modules}}


def export_tokens(bundle,output_root):
    root=Path(output_root)
    if not root.is_absolute() or root.resolve()!=root or any(p.is_symlink() for p in [root,*root.parents]):raise IntegrityError('output requires fresh unaliased absolute directory')
    root.mkdir(parents=True,exist_ok=False)
    with (root/'rows.jsonl').open('xb') as out:
        for row in bundle['rows']:out.write(json.dumps(row,ensure_ascii=False,separators=(',',':')).encode()+b'\n')
    for name,key in [('exclusions.json','exclusions'),('formation_ledger.json','formation_ledger')]:
        with (root/name).open('x',encoding='utf8',newline='\n') as out:json.dump(bundle[key],out,ensure_ascii=False,indent=2);out.write('\n')
    manifest={**bundle['manifest'],'output_sha256':{name:sha(root/name) for name in ['rows.jsonl','exclusions.json','formation_ledger.json']}}
    with (root/'data_manifest.json').open('x',encoding='utf8',newline='\n') as out:json.dump(manifest,out,indent=2);out.write('\n')
    return {'output_root':str(root),'manifest_sha256':sha(root/'data_manifest.json'),'rows':len(bundle['rows']),'excluded':len(bundle['exclusions'])}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--export-manifest',type=Path,required=True);p.add_argument('--export-manifest-sha',required=True);p.add_argument('--model-path',type=Path,required=True);p.add_argument('--max-length',type=int,default=32768);p.add_argument('--output-root',type=Path,required=True);a=p.parse_args(argv)
    print(json.dumps(export_tokens(compile_export(a.export_manifest,a.export_manifest_sha,a.model_path,max_length=a.max_length),a.output_root)))

if __name__=='__main__':main()
