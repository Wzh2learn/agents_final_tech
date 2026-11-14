"""Finite source-isolated development evaluation using the existing OpenCode runner."""
from pathlib import Path
from types import SimpleNamespace
import argparse,fcntl,hashlib,http.client,importlib,json,os,shutil,socket,socketserver,subprocess,sys,tempfile,threading,time

BASE=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
PHASE=BASE/'fccl_condition_learning_v1'
TRAIN=PHASE/'policy_v1'
OUT=TRAIN/'native_v1'
REPO=Path('/home/testuser/wzh/projects/agents_final_tech')
CODE=REPO/'research/agent_frontier_portfolio_20261029'
ST=BASE/'alfworld_text_qualification_20261106/context_study_v1'
LC=ST/'learning_comparison_v1'
PY=REPO/'venv/bin/python'
sys.path[:0]=[str(CODE),str(REPO)]
import run_contextbench_source as source
import run_swe_contextbench_astropy_20261105 as astro
import run_swe_contextbench_matplotlib_20261106 as mpl

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()

def new(path,value):
 with Path(path).open('x') as f:json.dump(value,f,indent=2);f.write('\n')

def state():
 return json.loads((TRAIN/'RESULT.json').read_text())

def prepare():
 if OUT.exists():raise ValueError('native attempt exists')
 OUT.mkdir()
 if shutil.disk_usage(OUT).free<4*1024**3:raise RuntimeError('insufficient private disk space')
 h=source.helpers()
 roots={'astropy':astro.qual.OUT/'source','matplotlib':mpl.qual.OUT/'source'}
 specs={}
 for name,runner in [('astropy',astro),('matplotlib',mpl)]:
  row=runner.row_for('source');root=roots[name]
  problem=(root/'task.txt').read_text()
  assert problem==row['problem_statement'].replace('\r\n','\n').rstrip()+'\n'
  specs[name]={'task':row['instance_id'],'base_commit':row['base_commit'],
               'task_file':str(root/'task.txt'),'task_sha256':sha(root/'task.txt')}
 assert {v['task'] for v in specs.values()}=={'astropy__astropy-14995','matplotlib__matplotlib-23562'}
 data=json.loads((TRAIN/'DATA.json').read_text())
 history=[]
 for i,request in enumerate(data['requests']):
  history.append({'public_source_context':request['messages'][-1]['content'],
    'candidate_edits':[r['assistant']['tool_calls'][0]['function'] for r in data['rows'] if r['cell'][0]==i],
    'native_contract_success':data['utilities'][i]})
 history_text=json.dumps(history,ensure_ascii=False,separators=(',',':'))
 episodes=[]
 for a,arm in enumerate(['frozen','history','bc','row','coupled','dpo']):
  for name in (['astropy','matplotlib'] if a%2==0 else ['matplotlib','astropy']):
   runner=astro if name=='astropy' else mpl
   folder=OUT/arm/name;folder.mkdir(parents=True)
   work=folder/'work';shutil.copytree(roots[name]/'clean_base',work)
   if name=='astropy':
    runner.qual.overlay(work);p=runner.actor_protocol()
    actor={'runtime':str(p.LEGACY),'sites':{'default':str(p.SITE)}}
   else:
    runner.qual.overlay(work,runner.site_for('source'));p=runner.protocol('source')
    actor={'runtime':str(p.LEGACY),'sites':{'default':str(p.SITE)}}
   for parent,dirs,files in os.walk(work):
    os.chmod(parent,0o755)
    for f in files:
     q=Path(parent)/f
     if q.is_symlink():raise ValueError('unexpected linked source')
     os.chmod(q,0o755 if q.stat().st_mode&0o111 else 0o644)
   inputs=folder/'inputs';inputs.mkdir()
   prompt=('Implement the requested change in the current /workspace repository. Use the only bash tool '
           'to read or edit source and run relevant tests. The environment is offline. '
           'Use python -m pytest -o addopts= when appropriate. Finish after implementing and checking the change.\n\n'
           + (('Earlier native-graded source experience (different issue; check applicability):\n'+history_text+'\n\n') if arm=='history' else '')
           + specs[name]['task']+'\n'+Path(specs[name]['task_file']).read_text())
   (inputs/'task.txt').write_text(prompt)
   (inputs/'guest.py').write_text(source.GUEST)
   profile={'model_id':'qwen3-8b-qual','context':32768,'output':8192}
   (inputs/'opencode.json').write_text(json.dumps(h.actor.config(profile,17)))
   episodes.append(dict(arm=arm,domain=name,folder=str(folder),actor=actor,
     inputs=source.tree(inputs),initial_work=source.tree(work)))
 server=Path('/home/testuser/.lmstudio/extensions/backends/llama.cpp-linux-arm64-nvidia-cuda13-2.16.0/llama-server')
 assert sha(server)=='037e02419e78256ed4227af31fc0b2602ff04c670fb7ad4fa2429fafb03bd55d'
 parent=LC/'gguf_conversion_v1/hf_parent_bf16_v1/Qwen3-8B-HF-BOUND-BF16.gguf'
 converter=BASE/'tools/llama_cpp/954de248ac6907dd05dc19f0f511ab18f2807a54/convert_lora_to_gguf.py'
 assert sha(converter)=='ecfe41c32d788a58de9da64ba988b2c97d4131880ff838b1e4e5f641bd415d2e'
 plan=dict(schema='native_policy_development_transfer_v1',scope='Two existing exposed development tasks, distinct from training Astropy15082; not independent confirmation.',
  tasks=specs,arms=['frozen','history','bc','row','coupled','dpo'],episodes=episodes,
  training_plan={'path':str(TRAIN/'PLAN.json'),'sha256':sha(TRAIN/'PLAN.json')},
  caps=dict(posts=16,seconds=600,combined_wire_bytes=64*1024**2),max_model_posts=192,
  sampling=dict(seed=17,temperature=.2,context=32768,output=8192,native_thinking=False),
  server=str(server),server_sha256=sha(server),parent=str(parent),parent_sha256='505618debb4e6ff112a8724f22853f09d4a6dd7ba0e32123d404fe9a4da8f5e3',
  converter=str(converter),converter_sha256=sha(converter),
  base_config=str(LC/'gguf_conversion_v1/recovery_v4/BASE_CONFIG_ONLY'),
  script_sha256=sha(__file__),components=source.components(),
  strong_controls='frozen current-code/feedback agent and untrained same-source full-history agent; source traceback/complete repair controls remain in source experiment.',
  next='Native success/regressions and full training plus execution costs; source loss or source selection accuracy is not the end state.')
 new(OUT/'PLAN.json',plan)
 print(json.dumps({'status':'PREPARED_CPU_ONLY','plan_sha256':sha(OUT/'PLAN.json'),'episodes':len(episodes),'tasks':specs}))

def convert(plan,arm):
 root=TRAIN/arm
 info=json.loads((root/'TRAINING.json').read_text())
 for n,d in info['adapter_files'].items():assert sha(root/'adapter'/n)==d
 dst=root/(arm+'.gguf')
 converter=Path(plan['converter']);src=converter.parent
 assert sha(converter)==plan['converter_sha256']
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',
          PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(src/'gguf-py')+':'+str(src))
 cmd=[str(PY),'-B',str(converter),'--outtype','f32','--base',plan['base_config'],
      '--outfile',str(dst),str(root/'adapter')]
 started=time.monotonic()
 p=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
 (root/'conversion.stdout').write_bytes(p.stdout);(root/'conversion.stderr').write_bytes(p.stderr)
 new(root/'CONVERSION.json',dict(argv=cmd,exit=p.returncode,seconds=time.monotonic()-started,
      gguf_sha256=sha(dst) if dst.exists() else None,training_receipt_sha256=sha(root/'TRAINING.json')))
 if p.returncode:raise RuntimeError('CPU conversion failed: '+arm)
 return dst

def server_start(plan,arm,lora):
 server=Path(plan['server']);assert sha(server)==plan['server_sha256']
 with socket.socket() as test:
  test.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
  test.bind(('127.0.0.1',18104))
 log=(OUT/arm/'server.log').open('wb')
 argv=[str(server),'-m',plan['parent'],'--host','127.0.0.1','--port','18104','--alias','qwen3-8b-qual',
       '-c','32768','-n','8192','-np','1','--no-context-shift','--jinja','-ngl','999']
 if lora is not None:argv+=['--lora',str(lora)]
 process=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
 proof=dict(pid=process.pid,argv=argv,health_gets=0)
 try:
  for _ in range(120):
   if process.poll() is not None:raise RuntimeError('owned model exited during startup')
   try:
    connection=http.client.HTTPConnection('127.0.0.1',18104,timeout=2)
    proof['health_gets']+=1;connection.request('GET','/health')
    response=connection.getresponse();body=response.read();connection.close()
    if response.status==200:
     new(OUT/arm/'SERVER.json',proof);return process,log
   except OSError:pass
   time.sleep(1)
  raise TimeoutError('owned server readiness cap')
 except BaseException:
  new(OUT/arm/'SERVER_START_FAILURE.json',proof)
  process.terminate()
  try:process.wait(timeout=20)
  except subprocess.TimeoutExpired:process.kill();process.wait()
  log.close();raise

def episode(plan,ep,h,profile,*,relay_factory=None):
 folder=Path(ep['folder'])
 assert source.tree(folder/'inputs')==ep['inputs']
 assert source.tree(folder/'work')==ep['initial_work']
 new(folder/'STARTED.json',dict(pid=os.getpid(),unix=time.time(),plan_sha256=sha(OUT/'PLAN.json')))
 bridge=Path(tempfile.mkdtemp(prefix='fccl-policy-',dir='/tmp'));bridge.chmod(0o700)
 relay=(source.Relay if relay_factory is None else relay_factory)(folder,profile,h,deadline=time.monotonic()+plan['caps']['seconds'],caps=plan['caps'])
 class Server(socketserver.ThreadingUnixStreamServer):daemon_threads=False;block_on_close=True
 class Handler(socketserver.BaseRequestHandler):
  def handle(self):relay.handle(self.request)
 server=Server(str(bridge/'s'),Handler);os.chmod(bridge/'s',0o600)
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 name='fccl-policy-'+str(os.getpid())+'-'+str(time.monotonic_ns())
 command=source.docker_command(folder,ep['actor'],bridge,profile,h,name,source_runtime=source.MPL_SOURCE_RUNTIME)
 if ep['domain']=='astropy':
  i=command.index('PYTHONPATH=/workspace/lib:/deps');command[i]='PYTHONPATH=/workspace:/deps'
 new(folder/'ACTOR_COMMAND.json',command)
 try:result=source.run_owned(command,name,folder/'container.cid',folder/'raw.jsonl',folder/'actor.stderr',plan['caps']['seconds'])
 finally:
  relay.close();server.shutdown();server.server_close();(bridge/'s').unlink();bridge.rmdir()
 accounting=relay.accounting()
 runner=astro if ep['domain']=='astropy' else mpl
 grade=runner.evaluate('source',folder)
 result=dict(arm=ep['arm'],domain=ep['domain'],actor=result,accounting=accounting,grade=grade,
  native_success=grade.get('focus',{}).get('exit')==0 and grade.get('regression',{}).get('exit')==0,
  raw_sha256=sha(folder/'raw.jsonl'))
 new(folder/'RESULT.json',result)
 return result

def prepare_resume():
 old=json.loads((OUT/'RESULT.json').read_text())
 assert old['status']=='FAILED' and 'Address already in use' in old['error']
 assert {(x['arm'],x['domain']) for x in old['episodes']}=={('frozen','astropy'),('frozen','matplotlib')}
 plan=json.loads((OUT/'PLAN.json').read_text())
 assert sha(OUT/'EXECUTED_DRIVER_V1.py')==plan['script_sha256']
 completed=[]
 for ep in plan['episodes']:
  p=Path(ep['folder'])/'RESULT.json'
  if ep['arm']=='frozen':
   assert p.exists()
   completed.append(dict(path=str(p),sha256=sha(p)))
  else:
   assert not p.exists() and not (Path(ep['folder'])/'STARTED.json').exists()
 resume=dict(original_plan_sha256=sha(OUT/'PLAN.json'),failed_batch_sha256=sha(OUT/'RESULT.json'),
  inherited_episodes=completed,remaining_episodes=10,driver_sha256=sha(__file__),
  correction='SO_REUSEADDR for port availability check; ephemeral socket reproducer retained. No task, prompt, model, cap or scoring change.',
  reuse='2 completed native baselines and 4 converted adapters reused; no retraining or baseline rerun')
 (OUT/'resume_v2').mkdir()
 new(OUT/'RESUME_PLAN_V2.json',resume)
 print(json.dumps({'resume_sha256':sha(OUT/'RESUME_PLAN_V2.json'),'inherited':2,'remaining':10}))

def run(plan_sha,resume=False):
 result_root=OUT/'resume_v2' if resume else OUT
 inherited=[]
 if resume:
  assert sha(OUT/'RESUME_PLAN_V2.json')==plan_sha
  correction=json.loads((OUT/'RESUME_PLAN_V2.json').read_text())
  assert sha(__file__)==correction['driver_sha256']
  assert sha(OUT/'PLAN.json')==correction['original_plan_sha256']
  assert sha(OUT/'RESULT.json')==correction['failed_batch_sha256']
  for ref in correction['inherited_episodes']:
   assert sha(ref['path'])==ref['sha256']
   inherited.append(json.loads(Path(ref['path']).read_text()))
 else:
  assert sha(OUT/'PLAN.json')==plan_sha
 assert not (result_root/'LIVE.json').exists() and not (result_root/'RESULT.json').exists()
 plan=json.loads((OUT/'PLAN.json').read_text())
 if not resume:assert sha(__file__)==plan['script_sha256']
 assert state()['status']=='ALL_FOUR_ADAPTERS_TRAINED'
 assert sha(TRAIN/'PLAN.json')==plan['training_plan']['sha256']
 assert sha(plan['parent'])==plan['parent_sha256']
 for p,d in plan['components'].items():assert sha(p)==d
 result=dict(status='RUNNING',plan_sha256=sha(OUT/'PLAN.json'),resume_sha256=plan_sha if resume else None,
   episodes=inherited,training_updates=state()['optimizer_updates'])
 def publish():
  temp=result_root/'LIVE.tmp';temp.write_text(json.dumps(result,indent=2));temp.replace(result_root/'LIVE.json')
 h=source.helpers()
 try:
  with source.resource_lock():
   loras={}
   for arm in ['bc','row','coupled','dpo']:
    if resume:
     p=TRAIN/arm/'CONVERSION.json';j=json.loads(p.read_text());dst=TRAIN/arm/(arm+'.gguf')
     assert j['exit']==0 and sha(dst)==j['gguf_sha256']
     loras[arm]=dst
    else:loras[arm]=convert(plan,arm)
   publish()
   for arm in plan['arms']:
    pending=[x for x in plan['episodes'] if x['arm']==arm and not any(
      old['arm']==arm and old['domain']==x['domain'] for old in inherited)]
    if not pending:continue
    process=log=None
    try:
     process,log=server_start(plan,arm,loras.get(arm))
     profile=dict(host='127.0.0.1',port=18104,model_id='qwen3-8b-qual',context=32768,output=8192)
     for ep in pending:
      value=episode(plan,ep,h,profile);result['episodes'].append(value);publish()
      print(json.dumps(dict(event='native_episode_returned',arm=arm,domain=ep['domain'],native_success=value['native_success'],accounting=value['accounting'])),flush=True)
    finally:
     if process is not None:
      process.terminate()
      try:process.wait(timeout=20)
      except subprocess.TimeoutExpired:process.kill();process.wait()
     if log is not None:log.close()
   result['status']='ALL12_NATIVE_EPISODES_RETURNED'
 except BaseException as exc:
  import traceback
  result.update(status='FAILED',error=traceback.format_exc());raise
 finally:
  probes=list(OUT.glob('*/SERVER*.json'))
  result['owned_model_health_gets']=sum(json.loads(p.read_text())['health_gets'] for p in probes)
  publish();new(result_root/'RESULT.json',result)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','run','resume-prepare','resume']);parser.add_argument('--plan-sha')
 args=parser.parse_args()
 if args.mode=='prepare':prepare()
 elif args.mode=='resume-prepare':prepare_resume()
 else:run(args.plan_sha,resume=args.mode=='resume')
