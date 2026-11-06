"""Frozen CPU training plan and explicit owned-window Qwen3-8B LoRA training.

Import/prepare never load model weights or call CUDA. No generation, service
management, downloads, parent adapters, retries, or automatic model fallback.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
import gc
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import re
import time

ST=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106/context_study_v1')
TOKENS=Path(__file__).with_name('alfworld_supervision_tokens.py')
CONFIG={'seed':17,'max_optimizer_updates':192,'batch_size':1,'learning_rate':0.0002,'adam_betas':[0.9,0.999],'adam_eps':1e-8,'weight_decay':0.01,'lora_r':8,'lora_alpha':16,'lora_dropout':0.0,'target_modules':['q_proj','v_proj'],'dtype':'bfloat16','gradient_checkpointing':True,'use_reentrant':False,'use_cache':False,'parent_adapter':None,'attention':'sdpa','init_lora_weights':True}

class IntegrityError(ValueError):pass

def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024**2),b''):digest.update(chunk)
    return digest.hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf8'))
def packed(value):return json.dumps(value,sort_keys=True,separators=(',',':'))
def value_sha(value):return hashlib.sha256(packed(value).encode()).hexdigest()
def write_new(path,value):
    with Path(path).open('x',encoding='utf8',newline='\n') as out:json.dump(value,out,indent=2);out.write('\n')
def canonical(path):
    path=Path(path)
    if not path.is_absolute() or path.resolve()!=path or any(p.is_symlink() for p in [path,*path.parents]):raise IntegrityError('canonical unaliased absolute path required')
    return path
def checked(path,digest):
    path=canonical(path)
    if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest) or sha(path)!=digest:raise IntegrityError('hash mismatch: '+str(path))
    return path

def module(path):
    spec=importlib.util.spec_from_file_location('learning_'+Path(path).stem,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def validate_row(row,eos,max_length,vocab_size):
    ids,mask,labels=(row[key] for key in ('input_ids','attention_mask','labels'))
    if not ids or type(ids) is not list or not (len(ids)==len(mask)==len(labels)) or len(ids)>max_length:raise IntegrityError('unequal/empty/overlength arrays; no truncation')
    if any(type(t) is not int or not 0<=t<vocab_size for t in ids) or any(type(t) is not int or t!=1 for t in mask) or any(type(t) is not int for t in labels):raise IntegrityError('invalid token IDs/attention/labels')
    n,end=row['prompt_token_count'],row['assistant_end_index']
    if type(n) is not int or type(end) is not int or not 0<n<end<len(ids):raise IntegrityError('invalid current completion boundary')
    positions=list(range(n,end+1))
    if any(label!=-100 for label in labels[:n]+labels[end+1:]) or any(labels[i]!=ids[i] for i in positions):raise IntegrityError('prefix/history/trailing template has loss or target was changed')
    if type(row['supervised_tokens']) is not int or type(row['sequence_length']) is not int or labels[end]!=eos or sum(labels[i]==eos for i in positions)!=1 or row['supervised_tokens']!=len(positions) or row['sequence_length']!=len(ids):raise IntegrityError('current completion EOS/count mismatch')
    if row.get('prefix_token_alignment_verified') is not True or row.get('source_role')!='teacher' or type(row.get('source_group')) is not str or not row['source_group'] or type(row.get('row_id')) is not str or not row['row_id']:raise IntegrityError('unqualified teacher completion/source')
    return positions


def load_data(manifest_path,digest,study_root=ST):
    path=checked(manifest_path,digest);data=read(path)
    if data.get('schema')!='alfworld_current_assistant_token_candidates_v1' or data.get('qualification_mode')!='LOCAL_HF_TOKENIZER_CPU' or data.get('long_rows_truncated') is not False or data.get('compiler_sha256')!=sha(TOKENS):raise IntegrityError('not pinned actual HF untruncated compiled data')
    for name in ['rows.jsonl','exclusions.json','formation_ledger.json']:checked(path.parent/name,data['output_sha256'][name])
    compiler=module(TOKENS);assets=data['tokenizer'];model=canonical(assets['model_path'])
    if (model/'adapter_config.json').exists():raise IntegrityError('parent adapter is forbidden in base model directory')
    for name,d in assets['files_sha256'].items():
        if name not in ['config.json','tokenizer_config.json','tokenizer.json']:raise IntegrityError('unexpected tokenizer binding file')
        checked(model/name,d)
    cfg=read(model/'config.json')
    if (cfg.get('model_type')!='qwen3' or cfg.get('architectures')!=['Qwen3ForCausalLM'] or cfg.get('hidden_size')!=4096 or cfg.get('num_hidden_layers')!=36 or cfg.get('vocab_size')!=151936 or assets.get('enable_thinking') is not False):raise IntegrityError('requires bound local HF Qwen3-8B configuration')
    # Recompile from the actual provider prefix/native target with the pinned
    # tokenizer, so labels cannot be rebound to a different valid-looking span.
    rebuilt=compiler.compile_export(Path(data['source_export']['path']),data['source_export']['sha256'],model,max_length=data['max_length'],study_root=study_root)
    rows=[json.loads(line) for line in (path.parent/'rows.jsonl').read_text(encoding='utf8').splitlines()]
    if rows!=rebuilt['rows'] or read(path.parent/'exclusions.json')!=rebuilt['exclusions'] or read(path.parent/'formation_ledger.json')!=rebuilt['formation_ledger']:raise IntegrityError('compiled rows/masks/formation costs differ from actual evidence')
    if len(rows)!=data['compiled_rows'] or len({r['row_id'] for r in rows})!=len(rows):raise IntegrityError('row count/duplicate identity')
    for row in rows:validate_row(row,assets['eos_token_id'],data['max_length'],cfg['vocab_size'])
    return data,rows


def schedule_rows(rows,groups,updates=192,seed=17):
    if type(groups) is not list or not groups or any(type(g) is not str or not g for g in groups) or len(set(groups))!=len(groups):raise IntegrityError('explicit distinct source_group list required')
    if type(updates) is not int or not 1<=updates<=192 or type(seed) is not int or seed!=17:raise IntegrityError('fixed seed17 and1..192 optimizer updates required')
    by_group=defaultdict(list)
    for row in rows:by_group[row['source_group']].append(row)
    if set(groups)-set(by_group):raise IntegrityError('requested source group has no rows')
    if len({r['row_id'] for r in rows})!=len(rows):raise IntegrityError('duplicate row identity')
    groups=sorted(groups);rng={g:random.Random(seed+int(hashlib.sha256(g.encode()).hexdigest()[:16],16)) for g in groups};queues={};cursor=Counter();epochs=Counter();result=[]
    for step in range(updates):
        group=groups[step%len(groups)]
        if group not in queues or cursor[group]>=len(queues[group]):
            queues[group]=sorted(by_group[group],key=lambda r:r['row_id']);rng[group].shuffle(queues[group]);cursor[group]=0;epochs[group]+=1
        row=queues[group][cursor[group]];cursor[group]+=1
        result.append({'update':step+1,'row_id':row['row_id'],'source_group':group,'group_permutation_epoch':epochs[group],'input_tokens':len(row['input_ids']),'supervised_tokens':row['supervised_tokens']})
    return result


def plan_data(data_path,data_sha,data,rows,groups,updates,wall_seconds,model_reference=None):
    if type(wall_seconds) is not int or not 1<=wall_seconds<=86400:raise IntegrityError('wall_seconds must be explicit positive integer <=86400')
    if model_reference is not None:
        binding=read(checked(model_reference['path'],model_reference['sha256']))
        named={Path(r['path']).name:r['sha256'] for r in binding['files']}
        if binding['model_dir']!=data['tokenizer']['model_path'] or any(named.get(n)!=d for n,d in data['tokenizer']['files_sha256'].items()):raise IntegrityError('CPU model-binding reference differs from tokenizer/base')
    schedule=schedule_rows(rows,groups,updates)
    versions={name:importlib.metadata.version(name) for name in ['torch','transformers','peft','tokenizers']}
    return {'schema':'alfworld_assistant_action_lora_plan_v1','config':CONFIG,'data_manifest':{'path':str(data_path),'sha256':data_sha},'model_path':data['tokenizer']['model_path'],'model_binding_reference':model_reference,'full_weight_hashes_checked_during_CPU_plan':False,'tokenizer_binding':data['tokenizer'],'source_groups':sorted(groups),'max_length':data['max_length'],'optimizer_updates':updates,'wall_limit_seconds':wall_seconds,'schedule':schedule,'schedule_sha256':value_sha(schedule),'scheduled_input_tokens':sum(r['input_tokens'] for r in schedule),'scheduled_supervised_tokens':sum(r['supervised_tokens'] for r in schedule),'unique_rows_scheduled':len({r['row_id'] for r in schedule}),'group_update_counts':dict(Counter(r['source_group'] for r in schedule)),'components':{str(p):sha(p) for p in [Path(__file__).resolve(),TOKENS]},'versions':versions,'initialization':'fresh bound HF BF16 base; seed17 new q/v LoRA r8 alpha16 dropout0; no parent adapter','formation_ledger_reference':str(Path(data_path).parent/'formation_ledger.json'),'different_stages_or_rows_are_not_independent_tasks':True,'matched_claim':'same selected groups, seed, initialization procedure and successful update count only; input/supervised tokens reported separately','future_scope':'training/reload receipt is not a world episode, GGUF serving compatibility, or heldout learning gain','development_only':True}


def check_root(root,study_root=ST):
    root=canonical(root)
    legacy=Path(study_root)/'supervision_learning_v1' in root.parents and re.fullmatch('attempt_v[1-9][0-9]*',root.name)
    comparison=root.parent==Path(study_root)/'learning_comparison_v1/plans' and re.fullmatch('(ordinary|recovery)_v[1-9][0-9]*',root.name)
    if not (legacy or comparison):raise IntegrityError('use fresh private learning plan root')
    return root


def prepare(root,data_manifest,data_sha,source_groups,*,updates=192,wall_seconds=7200,model_binding=None,model_binding_sha=None,study_root=ST):
    if (model_binding is None)!=(model_binding_sha is None):raise IntegrityError('pair model binding path and SHA')
    reference={'path':str(canonical(model_binding)),'sha256':model_binding_sha} if model_binding else None
    root=check_root(root,study_root)
    if root.exists():raise FileExistsError('fresh plan directory required')
    data_path=checked(data_manifest,data_sha);data,rows=load_data(data_path,data_sha,study_root);plan=plan_data(data_path,data_sha,data,rows,source_groups,updates,wall_seconds,reference)
    root.mkdir(parents=True,exist_ok=False);write_new(root/'manifest.json',plan)
    return {'root':str(root),'manifest_sha256':sha(root/'manifest.json'),'optimizer_updates':updates,'unique_rows_scheduled':plan['unique_rows_scheduled'],'group_update_counts':plan['group_update_counts'],'input_tokens':plan['scheduled_input_tokens'],'supervised_tokens':plan['scheduled_supervised_tokens']}


def verify_plan(root,digest,study_root=ST):
    root=check_root(root,study_root);plan=read(checked(root/'manifest.json',digest));data_path=Path(plan['data_manifest']['path']);data,rows=load_data(data_path,plan['data_manifest']['sha256'],study_root)
    expected=plan_data(data_path,plan['data_manifest']['sha256'],data,rows,plan['source_groups'],plan['optimizer_updates'],plan['wall_limit_seconds'],plan.get('model_binding_reference'))
    if plan!=expected:raise IntegrityError('frozen training plan/config/schedule/components changed')
    return root,plan,{r['row_id']:r for r in rows}


def validate_model_binding(path,digest,plan):
    reference=plan.get('model_binding_reference')
    if reference is not None and reference!={'path':str(canonical(path)),'sha256':digest}:raise IntegrityError('full model binding differs from frozen CPU reference')
    binding=read(checked(path,digest));model=canonical(binding['model_dir'])
    if str(model)!=plan['model_path'] or (model/'adapter_config.json').exists():raise IntegrityError('wrong model or parent adapter')
    files=binding['files']
    if type(files) is not list or not files:raise IntegrityError('empty full model binding')
    names={}
    for row in files:
        p=canonical(row['path'])
        if p.parent!=model or p.name in names or type(row.get('bytes')) is not int or row['bytes']<0 or p.stat().st_size!=row['bytes'] or p.name.startswith('adapter_'):raise IntegrityError('invalid/duplicate/base-adapter binding file')
        checked(p,row['sha256']);names[p.name]=row['sha256']
    if 'model.safetensors.index.json' not in names:raise IntegrityError('full8B binding requires safetensor index')
    index=read(model/'model.safetensors.index.json');shards=set(index['weight_map'].values())
    if not shards or any(type(n) is not str or Path(n).name!=n or not n.endswith('.safetensors') for n in shards) or not shards<=names.keys():raise IntegrityError('missing/unsafe bound weight shards')
    actual_shards={p.name for p in model.iterdir() if p.is_file() and p.name.endswith('.safetensors')}
    if actual_shards!=shards:raise IntegrityError('unbound or missing effective safetensor files')
    for name,d in plan['tokenizer_binding']['files_sha256'].items():
        if names.get(name)!=d:raise IntegrityError('training base differs from tokenizer/model config')
    return binding


def validate_window(path,digest,plan_sha,model_path):
    receipt=read(checked(path,digest));allowed=receipt.get('allowed_plan_sha256',[])
    if type(allowed) is not list or any(not isinstance(s,str) or not re.fullmatch('[0-9a-f]{64}',s) for s in allowed):raise IntegrityError('invalid window allowed plan list')
    if receipt.get('plan_sha256'):allowed=allowed+[receipt['plan_sha256']]
    if (receipt.get('status')!='OWNED_RESEARCH_WINDOW_GRANTED' or receipt.get('exclusive_research_job') is not True or receipt.get('gpu_exclusive') is not False or receipt.get('lease_scope')!='context_study_v1_and_owned_18104' or type(receipt.get('cuda_device')) is not int or receipt['cuda_device']!=0 or plan_sha not in allowed or receipt.get('model_dir',model_path)!=model_path):raise IntegrityError('D owned research-window grant does not bind this plan')
    return receipt


def sparse_causal(model,row,device,*,eos,max_length,vocab_size):
    import torch
    import torch.nn.functional as F
    positions=validate_row(row,eos,max_length,vocab_size);ids=torch.tensor([row['input_ids']],device=device);attention=torch.tensor([row['attention_mask']],device=device);predictors=torch.tensor([p-1 for p in positions],device=device);targets=torch.tensor([row['labels'][p] for p in positions],device=device)
    output=model(input_ids=ids,attention_mask=attention,logits_to_keep=predictors,use_cache=False)
    logits=output.logits[0]
    if logits.shape[0]!=len(positions):raise IntegrityError('model sparse logits selector not honored')
    return F.cross_entropy(logits.float(),targets),logits


def adapter_hashes(model,adapter_name='default'):
    import torch
    from peft import get_peft_model_state_dict
    state=get_peft_model_state_dict(model,adapter_name=adapter_name);result={}
    for name,tensor in sorted(state.items()):
        if 'lora_' not in name:raise IntegrityError('unexpected non-LoRA adapter tensor')
        cpu=tensor.detach().cpu().contiguous();result[name]={'shape':list(cpu.shape),'dtype':str(cpu.dtype),'sha256':hashlib.sha256(cpu.view(torch.uint8).numpy().tobytes()).hexdigest()}
    if not result:raise IntegrityError('empty adapter state')
    return result


def classify_oom(exc,torch_module):
    typed=isinstance(exc,getattr(torch_module,'OutOfMemoryError',())) if torch_module is not None else False
    message=bool(re.search(r'\bcuda(?:\s+error)?\s*:\s*out of memory\b|\bcuda out of memory\b',str(exc),re.IGNORECASE))
    return {'typed_torch_out_of_memory':typed,'cuda_out_of_memory_message':message,'classification':'torch_oom_type' if typed else 'cuda_oom_message_only' if message else 'unclassified_no_oom_evidence','oom':True if typed or message else None}


def run(root,plan_sha,model_binding,model_binding_sha,resource_window,resource_window_sha,*,study_root=ST):
    root=check_root(root,study_root)
    if (root/'reservation.json').exists():raise FileExistsError('attempt already reserved; never rerun')
    root,plan,rows=verify_plan(root,plan_sha,study_root);window=validate_window(resource_window,resource_window_sha,plan_sha,plan['model_path']);binding=validate_model_binding(model_binding,model_binding_sha,plan)
    reservation={'plan_sha256':plan_sha,'model_binding_path':str(model_binding),'model_binding_sha256':model_binding_sha,'resource_window_path':str(resource_window),'resource_window_sha256':resource_window_sha,'resource_scope':'D research queue/owned18104 only; not a global GPU or cross-host lock','mode':'EXPLICIT_LORA_TRAIN_NO_GENERATION'}
    write_new(root/'reservation.json',reservation)
    started=time.monotonic();model=optimizer=torch=loss=logits=gradients=trainable=None;completed_rows=Counter();completed_groups=Counter()
    receipt={'status':'FAILED','reservation':reservation,'optimizer_updates_attempted':0,'optimizer_updates_completed':0,'forward_calls_started':0,'forward_calls_completed':0,'completed_forward_sequence_tokens':0,'completed_forward_supervised_tokens':0,'attempted_sequence_tokens_upper_bound':0,'attempted_supervised_tokens_upper_bound':0,'completed_update_sequence_tokens':0,'completed_update_supervised_tokens':0,'model_weight_loads_started':0,'model_weight_loads_completed':0,'http_generation_inference_calls':0,'source_groups':plan['source_groups'],'development_only':True,'shared_models_managed':False,'gpu_exclusive':False,'formation_ledger_reference':plan['formation_ledger_reference']}
    try:
        import torch
        from peft import LoraConfig,get_peft_model
        from transformers import AutoModelForCausalLM,set_seed
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false');set_seed(CONFIG['seed']);torch.cuda.reset_peak_memory_stats(0);receipt['cuda_memory_before']=dict(zip(['free','total'],torch.cuda.mem_get_info(0)))
        receipt['model_weight_loads_started']+=1
        model=AutoModelForCausalLM.from_pretrained(plan['model_path'],dtype=torch.bfloat16,device_map={'':0},attn_implementation='sdpa',local_files_only=True,trust_remote_code=False,use_safetensors=True)
        receipt['model_weight_loads_completed']+=1;model.config.use_cache=False
        model=get_peft_model(model,LoraConfig(r=8,lora_alpha=16,lora_dropout=0.0,bias='none',task_type='CAUSAL_LM',target_modules=['q_proj','v_proj'],init_lora_weights=True))
        trainable={n:p for n,p in model.named_parameters() if p.requires_grad}
        if not trainable or any('lora_' not in n or not any('.'+m+'.' in n for m in CONFIG['target_modules']) for n in trainable):raise IntegrityError('only fresh q/v LoRA parameters may train')
        receipt['trainable_parameters']=sum(p.numel() for p in trainable.values());receipt['initial_adapter_tensor_hashes']=adapter_hashes(model)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.enable_input_require_grads();model.train()
        optimizer=torch.optim.AdamW(list(trainable.values()),lr=CONFIG['learning_rate'],betas=tuple(CONFIG['adam_betas']),eps=CONFIG['adam_eps'],weight_decay=CONFIG['weight_decay'])
        if {id(p) for g in optimizer.param_groups for p in g['params']}!={id(p) for p in trainable.values()}:raise IntegrityError('optimizer includes non-LoRA parameters')
        with (root/'steps.jsonl').open('x',encoding='utf8') as log:
            for scheduled in plan['schedule']:
                if time.monotonic()-started>=plan['wall_limit_seconds']:raise TimeoutError('frozen wall budget reached; no retry')
                row=rows[scheduled['row_id']];receipt['optimizer_updates_attempted']+=1;receipt['attempted_sequence_tokens_upper_bound']+=len(row['input_ids']);receipt['attempted_supervised_tokens_upper_bound']+=row['supervised_tokens'];log.write(json.dumps({'event':'attempt',**scheduled})+'\n');log.flush();optimizer.zero_grad(set_to_none=True);receipt['forward_calls_started']+=1
                loss,logits=sparse_causal(model,row,model.device,eos=plan['tokenizer_binding']['eos_token_id'],max_length=plan['max_length'],vocab_size=model.config.vocab_size);receipt['forward_calls_completed']+=1;receipt['completed_forward_sequence_tokens']+=len(row['input_ids']);receipt['completed_forward_supervised_tokens']+=row['supervised_tokens']
                if not torch.isfinite(loss):raise FloatingPointError('non-finite masked loss')
                loss.backward();gradients=[p.grad for p in trainable.values() if p.grad is not None]
                if not gradients or not all(torch.isfinite(g).all() for g in gradients) or any(p.grad is not None for n,p in model.named_parameters() if n not in trainable):raise FloatingPointError('missing/non-finite LoRA or unexpected base gradients')
                norm=math.sqrt(sum(float(g.float().square().sum()) for g in gradients))
                if not math.isfinite(norm) or norm==0:raise FloatingPointError('zero/non-finite LoRA gradient norm')
                optimizer.step();completed_rows[row['row_id']]+=1;completed_groups[row['source_group']]+=1;receipt['optimizer_updates_completed']+=1;receipt['completed_update_sequence_tokens']+=len(row['input_ids']);receipt['completed_update_supervised_tokens']+=row['supervised_tokens'];log.write(json.dumps({'event':'optimizer_update',**scheduled,'loss':float(loss.detach()),'gradient_norm':norm,'wall_seconds':time.monotonic()-started})+'\n');log.flush();loss=logits=None
        model.eval();model.gradient_checkpointing_disable();receipt['trained_adapter_tensor_hashes']=adapter_hashes(model);adapter=root/'adapter';model.save_pretrained(adapter,safe_serialization=True);receipt['adapter_files_sha256']={p.name:sha(p) for p in adapter.iterdir() if p.is_file()}
        model.load_adapter(str(adapter),adapter_name='reload_check',is_trainable=False,local_files_only=True);model.set_adapter('reload_check');model.eval();receipt['reload_active_adapters']=model.active_adapters;receipt['saved_adapter_config']=read(adapter/'adapter_config.json')
        cfg=receipt['saved_adapter_config']
        if (set(cfg['target_modules'])!={'q_proj','v_proj'} or cfg['r']!=8 or cfg['lora_alpha']!=16 or cfg['lora_dropout']!=0.0 or cfg['bias']!='none' or cfg['base_model_name_or_path']!=plan['model_path'] or receipt['reload_active_adapters']!=['reload_check']):raise IntegrityError('saved/reloaded adapter configuration/active identity differs')
        receipt['reloaded_adapter_tensor_hashes']=adapter_hashes(model,'reload_check');receipt['adapter_reload_tensor_identity_verified']=receipt['trained_adapter_tensor_hashes']==receipt['reloaded_adapter_tensor_hashes']
        if not receipt['adapter_reload_tensor_identity_verified']:raise IntegrityError('adapter save/reload tensors differ')
        if receipt['optimizer_updates_completed']!=plan['optimizer_updates']:raise IntegrityError('completed update count differs from frozen schedule')
        receipt['status']='TRAINED_SAVED_RELOADED_NO_WORLD_EVALUATION'
    except Exception as exc:
        receipt['error']={'type':type(exc).__name__,'message':str(exc)};receipt['oom_evidence']=classify_oom(exc,torch);receipt['oom']=receipt['oom_evidence']['oom'];receipt['retry_performed']=False
    finally:
        receipt['work_wall_seconds']=time.monotonic()-started;cleanup_started=time.monotonic();receipt['completed_group_update_counts']=dict(completed_groups);receipt['completed_row_visit_counts']=dict(completed_rows)
        try:
            if torch is not None and torch.cuda.is_initialized():receipt['cuda_peak_allocated_bytes']=torch.cuda.max_memory_allocated(0);receipt['cuda_peak_reserved_bytes']=torch.cuda.max_memory_reserved(0)
            del optimizer,model,loss,logits,gradients,trainable;gc.collect()
            if torch is not None and torch.cuda.is_initialized():torch.cuda.empty_cache()
        except Exception as cleanup_error:receipt['cleanup_error']={'type':type(cleanup_error).__name__,'message':str(cleanup_error)}
        receipt['cleanup_wall_seconds']=time.monotonic()-cleanup_started;receipt['wall_seconds']=time.monotonic()-started
        write_new(root/'receipt.json',receipt)
    return receipt


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True);parser.add_argument('--run',action='store_true');parser.add_argument('--manifest-sha');parser.add_argument('--data-manifest',type=Path);parser.add_argument('--data-manifest-sha');parser.add_argument('--source-group',action='append');parser.add_argument('--updates',type=int,default=192);parser.add_argument('--wall-seconds',type=int,default=7200);parser.add_argument('--model-binding',type=Path);parser.add_argument('--model-binding-sha');parser.add_argument('--resource-window',type=Path);parser.add_argument('--resource-window-sha');a=parser.parse_args(argv)
    if a.run:
        if not all([a.manifest_sha,a.model_binding,a.model_binding_sha,a.resource_window,a.resource_window_sha]):parser.error('run requires frozen plan, full model binding and D owned research-window hashes')
        result=run(a.root,a.manifest_sha,a.model_binding,a.model_binding_sha,a.resource_window,a.resource_window_sha)
    else:
        if not all([a.data_manifest,a.data_manifest_sha,a.source_group]):parser.error('CPU plan requires compiled manifest SHA and explicit source groups')
        result=prepare(a.root,a.data_manifest,a.data_manifest_sha,a.source_group,updates=a.updates,wall_seconds=a.wall_seconds,model_binding=a.model_binding,model_binding_sha=a.model_binding_sha)
    print(json.dumps(result))
    return 0 if result.get('status','TRAINED_SAVED_RELOADED_NO_WORLD_EVALUATION')=='TRAINED_SAVED_RELOADED_NO_WORLD_EVALUATION' else 1

if __name__=='__main__':raise SystemExit(main())
