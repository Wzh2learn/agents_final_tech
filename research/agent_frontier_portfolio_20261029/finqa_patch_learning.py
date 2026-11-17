"""One four-operator candidate: TRAIN patch supervision, replay, native DEV."""
from pathlib import Path
import argparse,copy,json,os,random,re,shutil,signal,subprocess,sys,time,traceback
repo=Path('/home/testuser/wzh/projects/agents_final_tech')
sys.path[:0]=[str(repo),str(repo/'research/agent_frontier_portfolio_20261029')]
import finqa_state_learning as m
import run_finqa_learning_native as native
step1=m.PAIRED_STATES.parent/'structural_patch_step1_v1'
root=step1.parent/'structural_patch_candidate_v1'
replay=m.PAIRED_STATES.parent/'teacher_expansion_clean_v3'
def literal_matches(public,snapshot):
 # Reuse the earlier public probe's literal alignment; candidates are not labels.
 def numbers(text):
  return [float(v.replace(',','')) for v in re.findall(r'[-+]?\d[\d,]*(?:\.\d+)?',str(text))]
 operands=list(dict.fromkeys(re.findall(r'(?<![\w#])[-+]?\d[\d,]*(?:\.\d+)?%?',snapshot['current_program'] or '')))
 hints=[]
 for operand in operands[:20]:
  values=numbers(operand)
  if not values:continue
  value=values[0];cells=[];texts=[]
  def matches(text):
   return any(abs(value-v)<=1e-7*max(1,abs(value),abs(v)) for v in numbers(text))
  for r,row in enumerate(public['table']):
   for c,cell in enumerate(row):
    if matches(cell):cells.append(dict(row=r,col=c,row_label=row[0],column_header=public['table'][0][c] if c<len(public['table'][0]) else '',cell=cell))
  for field in ['pre_text','post_text']:
   for i,text in enumerate(public.get(field,[])):
    if matches(text):texts.append(dict(field=field,index=i,text=str(text)[:450]))
  hints.append(dict(operand=operand,literal_table_candidates=cells[:8],literal_text_candidates=texts[:2]))
 return hints
def prompt(public,snapshot):
 return ('Task: bounded financial program patch review. Compare the program with the supplied report and actual execution. '
 'Execution reports a computed value, never answer correctness. Check quantities, periods, units and dependencies. '
 'Retain consistent calculations; a patch is not mandatory. '
 'Finish with exactly one JSON object and no code fences or Final program line. '
 'Keys: diagnosis (brief), evidence (short list of report anchors), patches (list). '
 'The execution layer applies the patches and executes the resulting program. '
 'Use only: '
 '{"op":"KEEP"} alone preserves the original; '
 '{"op":"rebind_operand","from":"10","to":"20"} simultaneously replaces matching ORIGINAL operands across steps, '
 'with optional positions [[original_step_index,1_or_2]]; indices are zero-based BEFORE insertion. '
 '{"op":"scale_output","mode":"divide","factor":1000000} appends a power-of-ten conversion; mode divide or multiply. '
 '{"op":"prepend_step","step":"subtract(10, 2)"} adds one flat calculation before the original. '
 'Prefix steps use #i for earlier prefix steps. Bind to prefix step i with to="@i"; all prefix indices start at zero. '
 'Original #i operands automatically shift after insertion. '
 'At most eight operations and six prefix steps. Use supported FinQA operators and two arguments per flat step. '
 'If useful, validate with /extra/bin/python /inputs/finqa_tool.py --patches followed by one quoted JSON list. '
 'Return the complete patch list as your final JSON even after validation. Do not replace the whole program in prose. '
 'No reference answer is available. Literal matches are candidates, not correctness labels.\n'+json.dumps(dict(public_task=public,observed_state=snapshot,literal_operand_matches=literal_matches(public,snapshot)),ensure_ascii=False))
TOOL=r"""from pathlib import Path
import argparse,json,sys
import finqa_correction as task
task.executor(Path('/inputs/executor.py'))
from finqa_minimal_patches import apply_patches
def commit(patches,origin):
 public=json.loads(Path('/inputs/public.json').read_text())
 state=json.loads(Path('/inputs/initial_state.json').read_text())
 program=apply_patches(state['current_program'],patches)
 execution=task.submit_program(program,public,Path('/workspace'),origin=origin)
 return dict(program=program,execution=execution)
def final(events):
 latest=None;parts={}
 for event in events:
  part=event.get('part',{})
  if not isinstance(part,dict) or not isinstance(part.get('messageID'),str):continue
  if part['messageID']!=latest:latest=part['messageID'];parts={}
  if event.get('type')=='text' and part.get('type')=='text' and isinstance(part.get('text'),str):
   parts[part['id']]=part['text']
 text='\n'.join(parts.values()).strip()
 proposal=json.loads(text)
 return commit(proposal['patches'],'terminal_structured_patch')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--patches');p.add_argument('--final-jsonl');a=p.parse_args()
 try:
  if a.patches is not None:out=commit(json.loads(a.patches),'tool_structured_patch')
  elif a.final_jsonl is not None:
   events=[json.loads(s) for s in Path(a.final_jsonl).read_text().splitlines() if s.strip()]
   try:out=final(events)
   except (ValueError,KeyError,TypeError,IndexError) as e:
    # Public schema failure retains the original; no hidden label is consulted.
    out=commit([dict(op='KEEP')],'invalid_patch_retains_original');out['patch_error']=str(e)
  else:raise ValueError('use --patches or final patch JSON')
  print(json.dumps(out,ensure_ascii=False))
 except (ValueError,KeyError,TypeError,IndexError) as e:
  print(json.dumps(dict(status='patch_error',error=str(e))));raise SystemExit(2)
"""
def prepare():
 formation=step1/'formation_v2'
 assert m.read(formation/'teacher_result.json')['status']=='RETURNED'
 assert not root.exists()
 data=m.read(replay/'DATA.json');prior=m.read(replay/'PLAN.json')
 tokenizer=m.tokens.load_tokenizer(m.learning.MODEL)
 examples=m.read_lines(formation/'COMBINED_PATCH_SAMPLES.jsonl')
 # Keep all recovered source pairs; use first sixteen independent normal KEEP states.
 normals=[x for x in examples if x['phase']=='source_KEEP'][:16]
 examples=[x for x in examples if x['phase']!='source_KEEP']+normals
 template=m.read(step1/'formation/000/wire/00001.request.json')
 before=(step1/'formation/000/inputs/task.txt').read_text()
 rows=[];groups=[];by_source={}
 for example in examples:by_source.setdefault(example['source_index'],[]).append(example)
 for index,items in sorted(by_source.items()):
  group=[]
  for example in items:
   proposal=example['target']
   target=dict(diagnosis=proposal.get('diagnosis','No patch required.'),evidence=proposal.get('evidence',[]),patches=proposal['patches'])
   request=m.fresh_request(template,before,prompt(example['public'],example['state']))
   row=m.tokens.encode_completion(request,dict(role='assistant',content=json.dumps(target,ensure_ascii=False)),
                                   tokenizer,16384,completion_kind='text')
   row.update(source_index=index,phase=example['phase'])
   group.append(row);rows.append(row)
  groups.append(group)
 anchors=[[data['rows'][i] for i in group] for group in prior['paired_rows']]
 schedule=[dict(kind='replay',index=i) for i in range(len(anchors))]+[dict(kind='patch',index=i) for i in range(len(groups))]
 random.Random(17).shuffle(schedule);schedule=schedule*3
 root.mkdir()
 m.study.new(root/'DATA.json',dict(anchor_groups=anchors,patch_groups=groups))
 m.study.new(root/'PLAN.json',dict(model=prior['model_path'],warm_start=str(replay/'aligned_sft'),seed=17,
  learning_rate=2e-4,epochs=3,schedule=schedule,wall_seconds=14400,
  replay_groups=len(anchors),patch_groups=len(groups),patch_targets=len(rows),
  repair_targets=sum(x['phase']=='repair' for x in examples),normal_keep_targets=len(normals),
  runtime=m.read(step1/'PLAN.json')['runtime'],caps=m.read(replay/'native_v1/PLAN.json')['caps'],
  data_sources='121 TRAIN replay groups + actual new TRAIN repairs and KEEP; no DEV teacher targets',
  former_prompt_run_excluded=True))
 print(json.dumps(dict(prepared=True,replay_groups=len(anchors),patch_groups=len(groups),patch_targets=len(rows),updates=len(schedule))),flush=True)
def stop27():
 from scripts.graph import research_gpu_guard as guard
 services=m.study.PRIVATE/'research_services';owner=m.read(services/'gpu_guard_current.json')
 boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 stat=Path('/proc',str(owner['pid']),'stat')
 def live():return stat.exists() and stat.read_text().split()[2] not in ['Z','X']
 changed=live()
 if changed:
  assert owner['boot_id']==boot and stat.read_text().split()[21]==owner['start_ticks']
  deadline=time.monotonic()+90
  # A startup guard must know the container ID before a stop request. Otherwise
  # terminating its launcher can leave a detached model outside the GPU lease.
  while live() and not owner.get('container_id'):
   if time.monotonic()>deadline:raise TimeoutError('model guard has not registered its container; refusing another model')
   time.sleep(1);latest=m.read(services/'gpu_guard_current.json')
   assert latest['pid']==owner['pid'] and latest['boot_id']==boot
   owner=latest
  if live():os.kill(owner['pid'],signal.SIGTERM)
  deadline=time.monotonic()+120
  while live():
   if time.monotonic()>deadline:raise TimeoutError('prior model service did not stop')
   time.sleep(2)
 # Reconcile a previously orphaned owned container before allowing new weights.
 # The lease prevents a replacement owner racing this final container check.
 with guard.gpu_lease(min_available_gib=0):
  info=guard.container_info('research-qwen27b-current')
  if info and info['running']:
   service=m.read(services/'qwen27b_current.json')
   assert service['boot_id']==boot and service['container_name']=='research-qwen27b-current'
   assert info['image']==service['settings']['VLLM_IMAGE']
   state=dict(owner,status='STOPPED_UNGUARDED_RESIDENT',container_id=info['id'])
   guard.stop_owned(info['id'],state,services/'gpu_guard_current.json',3);changed=True
 return changed
def restore27():
 services=m.study.PRIVATE/'research_services';folder=services/('restore_patch_candidate_'+str(int(time.time())));folder.mkdir()
 shutil.copyfile(services/'restore_1794836679/restore.py',folder/'restore.py')
 with (folder/'supervisor.log').open('xb') as log:
  p=subprocess.Popen([str(repo/'venv/bin/python'),'-u','-B',str(folder/'restore.py')],cwd=repo,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 return dict(pid=p.pid,folder=str(folder))
def train():
 import torch
 from peft import PeftModel
 from transformers import AutoModelForCausalLM
 from scripts.graph.research_gpu_guard import gpu_lease
 plan=m.read(root/'PLAN.json');data=m.read(root/'DATA.json')
 assert not (root/'TRAIN_LIVE.json').exists()
 state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],
  optimizer_updates=0,forward_calls=0,supervised_tokens=0,training_sequence_tokens=0,http_posts=0)
 started=time.monotonic();m.study.publish(root/'TRAIN_LIVE.json',state)
 try:
  with m.study.core.resource_lock(),gpu_lease():
   torch.manual_seed(plan['seed'])
   base=AutoModelForCausalLM.from_pretrained(plan['model'],dtype=torch.bfloat16,device_map={'':0},attn_implementation='sdpa',local_files_only=True,trust_remote_code=False)
   model=PeftModel.from_pretrained(base,plan['warm_start'],is_trainable=True)
   model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False});model.enable_input_require_grads();model.train()
   parameters=[p for p in model.parameters() if p.requires_grad]
   optimizer=torch.optim.AdamW(parameters,lr=plan['learning_rate'])
   for item in plan['schedule']:
    if time.monotonic()-started>plan['wall_seconds']:raise TimeoutError('candidate training wall cap')
    free=next(int(x.split()[1])/1024**2 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
    if free<32:raise RuntimeError('32GiB memory reserve')
    optimizer.zero_grad(set_to_none=True)
    batch=data['anchor_groups' if item['kind']=='replay' else 'patch_groups'][item['index']]
    coefficients=(m.learning.group_coefficients([r['supervised_tokens'] for r in batch],'token_mean') if item['kind']=='replay' else [1/len(batch)]*len(batch))
    loss_value=0.
    for row,coefficient in zip(batch,coefficients,strict=True):
     offset,kept=m.learning.completion_logit_window(row)
     inputs=torch.tensor([row['input_ids']],device='cuda');labels=torch.tensor([row['labels'][offset:]],device='cuda')
     logits=model(input_ids=inputs,use_cache=False,logits_to_keep=kept).logits
     value=coefficient*m.learning.weighted_loss(logits,labels,(labels!=-100).float())
     if not bool(torch.isfinite(value)):raise ValueError('nonfinite candidate loss')
     loss_value+=float(value.detach());value.backward()
     state['forward_calls']+=1;state['supervised_tokens']+=row['supervised_tokens'];state['training_sequence_tokens']+=row['sequence_length']
     del inputs,labels,logits,value
    gradient=torch.nn.utils.clip_grad_norm_(parameters,1.,error_if_nonfinite=True);optimizer.step()
    state.update(optimizer_updates=state['optimizer_updates']+1,last_kind=item['kind'],last_loss=loss_value,gradient_norm=float(gradient.detach()))
    m.study.publish(root/'TRAIN_LIVE.json',state)
   output=root/plan.get('adapter_folder','patch_policy');model.save_pretrained(output);state['status']='TRAINED'
 except BaseException:state.update(status='FAILED',error=traceback.format_exc());raise
 finally:
  state['seconds']=time.monotonic()-started;m.study.publish(root/'TRAIN_LIVE.json',state);m.study.new(root/'TRAIN_RESULT.json',state)
def prepare_dev():
 plan=m.read(root/'PLAN.json');common=m.read(replay/'native_v1/PLAN.json')
 sources=common['source_episodes'];assert len(sources)==64
 labels=m.read(Path(sources[0]['folder']).parent.parent/'LABELS_PRIVATE.json')
 m.study.new(root/'DEV_LABELS_PRIVATE.json',labels)
 episodes=[]
 for ep in sources:
  source=Path(ep['folder']);folder=root/'dev'/f"{ep['index']:03d}";inputs=folder/'inputs';inputs.mkdir(parents=True)
  for name in ['work','dependencies']:shutil.copytree(source/name,folder/name)
  public=m.read(source/'inputs/public.json');snapshot=m.state_from_folder(source)
  (inputs/'public.json').write_text(json.dumps(public,ensure_ascii=False))
  (inputs/'initial_state.json').write_text(json.dumps(snapshot,ensure_ascii=False))
  (inputs/'task.txt').write_text(prompt(public,snapshot))
  (inputs/'finqa_correction.py').write_text(Path(m.task.__file__).read_text())
  (inputs/'finqa_minimal_patches.py').write_text((repo/'research/agent_frontier_portfolio_20261029/finqa_minimal_patches.py').read_text())
  (inputs/'finqa_tool.py').write_text(TOOL)
  (inputs/'executor.py').write_text(Path(m.task.executor().__file__).read_text())
  (inputs/'guest.py').write_text(m.study.guest_source(terminal_program=True))
  episodes.append(dict(index=ep['index'],id=ep['id'],report=ep['report'],folder=str(folder)))
 m.study.new(root/'DEV_PLAN.json',dict(episodes=episodes,caps=plan['caps'],source='identical cached first-pass states as ordinary33/paired37',teacher_calls=0))
def evaluate():
 plan=m.read(root/'PLAN.json');runtime=plan['runtime'];output=root/'patch_policy';target=output/'adapter.gguf'
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',
          PYTHONPATH=str(Path(runtime['converter']).parent/'gguf-py')+':'+str(Path(runtime['converter']).parent))
 argv=[str(repo/'venv/bin/python'),'-B',runtime['converter'],'--outtype','f32','--base',runtime['base_config'],'--outfile',str(target),str(output)]
 converted=subprocess.run(argv,capture_output=True,timeout=180,env=env)
 (output/'conversion.stdout').write_bytes(converted.stdout);(output/'conversion.stderr').write_bytes(converted.stderr)
 if converted.returncode:raise RuntimeError('candidate adapter conversion failed')
 dev=m.read(root/'DEV_PLAN.json');state=dict(status='RUNNING',pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],episodes=[])
 m.study.publish(root/'DEV_LIVE.json',state);process=log=None;started=time.monotonic()
 try:
  with m.study.core.resource_lock():
   h=m.study.core.helpers();checked=h.deps.verify_projection(h.actor.RUNTIME_ROOT,h.actor.RUNTIME_SHA)
   m.study.CAPS.clear();m.study.CAPS.update(plan['caps'])
   process,log=native.start_server(runtime,'patch_policy',target,root)
   for ep in dev['episodes']:
    result=m.study.episode(ep,h,checked,m.study.MODEL,private_labels=root/'DEV_LABELS_PRIVATE.json')
    row=dict(index=ep['index'],success=result['native_success'],program=result['submitted_program'],
     posts=result['accounting']['actual_forwarded_posts'],tokens=result['accounting']['provider_total_tokens_known'],
     unknown=len(result['accounting']['unknown_usage_requests']),seconds=result['actor']['seconds'])
    state['episodes'].append(row);m.study.publish(root/'DEV_LIVE.json',state);print(json.dumps(row),flush=True)
  state['status']='RETURNED'
 except BaseException:state.update(status='FAILED',error=traceback.format_exc());raise
 finally:
  if process is not None:native.stop_server(process,log)
  state['seconds']=time.monotonic()-started;m.study.publish(root/'DEV_LIVE.json',state);m.study.new(root/'DEV_RESULT.json',state)
def run():
 if not (root/'PLAN.json').exists():prepare()
 unloaded=stop27();state=dict(status='RUNNING')
 try:
  with (root/'training.log').open('xb') as log:
   result=subprocess.run([str(repo/'venv/bin/python'),'-u','-B',__file__,'train'],cwd=repo,stdout=log,stderr=subprocess.STDOUT,timeout=15000)
  if result.returncode:raise RuntimeError('candidate training failed; see TRAIN_RESULT')
  prepare_dev();evaluate();state['status']='RETURNED'
 except BaseException:state.update(status='FAILED',error=traceback.format_exc());raise
 finally:
  if unloaded:state['restoration']=restore27()
  m.study.publish(root/'RUN_RESULT.json',state)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('mode',choices=['prepare','train','prepare-dev','evaluate','run']);args=a.parse_args()
 {'prepare':prepare,'train':train,'prepare-dev':prepare_dev,'evaluate':evaluate,'run':run}[args.mode]()
