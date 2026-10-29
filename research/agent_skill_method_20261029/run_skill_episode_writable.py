#!/usr/bin/env python3
"""Isolated, bounded OpenCode/Qwen skill pilot; no official-harness claim."""
import json, os, select, shutil, socket, socketserver, subprocess, sys, threading, time, hashlib, tarfile
from pathlib import Path

ROOT=Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029')
UP=Path('/home/testuser/wzh/research_evidence/agent_frontier_20261029/skillsbench_v1_1/tasks')
DEPS=Path('/home/testuser/wzh/projects/agents_final_tech/venv/lib/python3.12/site-packages')
task, arm=sys.argv[1:3]
if task not in ('llm-prefix-cache-replay','dialogue-parser','tictoc-unnecessary-abort-detection') or arm not in ('no_skill','all_skill','select_skill'): raise SystemExit('unsupported')
case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))
case.mkdir(parents=True, exist_ok=False)
work=case/'work'; work.mkdir(); work.chmod(0o777); bridge=Path('/tmp')/('skill_bridge_'+str(os.getpid())); bridge.mkdir(exist_ok=False)
src=UP/task
body=(src/'task.md').read_text(encoding='utf8').split('---',2)[2].strip()
target='/app' if task=='dialogue-parser' else '/root'
for name in (('trace.jsonl','config.json') if task=='llm-prefix-cache-replay' else (('script.txt',) if task=='dialogue-parser' else ())):
    shutil.copy2(src/'environment'/name,work/name)
if task=='tictoc-unnecessary-abort-detection':
    (work/'traces').mkdir()
    with tarfile.open(src/'environment'/'tictoc-unnecessary-abort-detection-traces.tar.gz') as tar:
        tar.extractall(work/'traces',filter='data')
(work/'instructions.txt').write_text(body,encoding='utf8')
allskills=src/'environment'/'skills'
skills=[]
if arm!='no_skill':
    shutil.copytree(allskills,work/'skills')
    names={'llm-prefix-cache-replay':['prefix-cache-replay','cache-policy-comparison'], 'dialogue-parser':['dialogue-graph'], 'tictoc-unnecessary-abort-detection':['transaction-trace-analysis','transaction-protocol-reasoning','transaction-concurrency-control-foundations']}[task]
    if arm=='select_skill': names=names[:1]  # deterministic task metadata rule, no adaptive model
    skills=[f'{target}/skills/{n}/SKILL.md' for n in names]
prompt=(f'Read {target}/instructions.txt with the read tool. Complete the stated task using local files. '
        f'Work only inside {target}. Generate the required output files. Do not ask for user input. '
        + ('Before solving, read these instructions: '+', '.join(skills)+'. ' if skills else '')
        + 'Use available tools to implement and execute your solution. Do not access network. Never read an entire large trace into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified file.')
cfg={'provider':{'gb10':{'npm':'@ai-sdk/openai-compatible','name':'local',
 'options':{'baseURL':'http://127.0.0.1:18004/v1','timeout':120000},
 'models':{'qwen3.6-35b-a3b':{'name':'Qwen3.6-35B-A3B','limit':{'context':32768,'output':4096}}}}},
 'model':'gb10/qwen3.6-35b-a3b','permission':{'*':'deny','read':'allow','write':'allow','edit':'allow','bash':'allow','glob':'allow','grep':'allow','list':'allow'}}
(work/'opencode.json').write_text(json.dumps(cfg),encoding='utf8')
sockpath=bridge/'model.sock'; calls=[]; payload_bytes=[]; allowed={b'POST /v1/chat/completions',b'GET /v1/models'}
def relay(a,b):
 try:
  while True:
   rr,_,_=select.select([a,b],[],[],120)
   if not rr:return
   for x in rr:
    data=x.recv(65536)
    if not data:return
    (b if x is a else a).sendall(data)
 except (OSError,TimeoutError):return
class Handler(socketserver.BaseRequestHandler):
 def handle(self):
  first=b'';self.request.settimeout(30)
  while b'\r\n\r\n' not in first and len(first)<65536:
   b=self.request.recv(4096)
   if not b:return
   first+=b
  line=first.split(b'\r\n',1)[0].rsplit(b' ',1)[0]
  headers=first.split(b'\r\n\r\n',1)[0].split(b'\r\n')[1:]
  lengths=[x.split(b':',1)[1].strip() for x in headers if x.lower().startswith(b'content-length:')]
  length=int(lengths[0]) if lengths and lengths[0].isdigit() else None
  if line not in allowed or len(calls)>=8 or (line.startswith(b'POST') and (length is None or sum(payload_bytes)+length>450000)):
   calls.append('DENIED_OR_LIMIT');self.request.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n');return
  if line.startswith(b'POST'):payload_bytes.append(length)
  calls.append(line.decode()); upstream=socket.create_connection(('127.0.0.1',8004),timeout=30)
  try:upstream.sendall(first);relay(self.request,upstream)
  finally:upstream.close()
class Server(socketserver.ThreadingUnixStreamServer): daemon_threads=True
entry='''import select,socket,threading,subprocess,os,sys\ndef proxy(c):\n s=socket.socket(socket.AF_UNIX);s.connect('/bridge/model.sock')\n try:\n  while 1:\n   ready,_,_=select.select([c,s],[],[],120)\n   if not ready:break\n   for x in ready:\n    b=x.recv(65536)\n    if not b:return\n    (s if x is c else c).sendall(b)\n finally:c.close();s.close()\nl=socket.socket();l.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);l.bind(('127.0.0.1',18004));l.listen(8)\ndef serve():\n while 1:\n  c,_=l.accept();threading.Thread(target=proxy,args=(c,),daemon=True).start()\nthreading.Thread(target=serve,daemon=True).start()\np=subprocess.run(['/opt/opencode','run','--pure','--format','json','-m','gb10/qwen3.6-35b-a3b','--title','skill-pilot',sys.argv[1]],stdin=subprocess.DEVNULL);raise SystemExit(p.returncode)'''
name='agent-skill-'+str(os.getpid())
cmd=['docker','run','--name',name,'--rm','--pull','never','--network','none','--read-only','--cpus','1','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','128','--memory','2g','--tmpfs','/tmp:rw,nosuid,size=128m','--tmpfs','/home/agent:rw,nosuid,size=256m','--env','HOME=/home/agent','--env','OPENCODE_DISABLE_MODELS_FETCH=1','--mount',f'type=bind,src={work},dst={target}','--mount',f'type=bind,src={bridge},dst=/bridge,readonly','--mount','type=bind,src=/home/testuser/.opencode/bin/opencode,dst=/opt/opencode,readonly','--workdir',target,'--entrypoint','python3','python:3.12-slim','-c',entry,prompt]
server=Server(str(sockpath),Handler);os.chmod(sockpath,0o666);threading.Thread(target=server.serve_forever,daemon=True).start();start=time.time()
try:
 try:
  run=subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300);rc=run.returncode;out=run.stdout;err=run.stderr
 except subprocess.TimeoutExpired as e:
  subprocess.run(['docker','kill',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10);rc=124;out=e.stdout or b'';err=e.stderr or b''
 (case/'raw.jsonl').write_bytes(out);(case/'stderr.txt').write_bytes(err)
finally:
 server.shutdown();server.server_close();sockpath.unlink(missing_ok=True)
events=[]
for line in out.splitlines():
 try:events.append(json.loads(line))
 except json.JSONDecodeError:pass
tokens=[]
for e in events:
 if isinstance(e,dict) and e.get('type')=='step_finish':tokens.append(e.get('part',{}).get('tokens',{}))
# A completely separate non-agent container mounts verifier after the episode;
# it has no endpoint or oracle. Never feed its test output back to the agent.
verifier_command='python -m pytest -q -p no:cacheprovider /verifier/test_outputs.py'
if task=='tictoc-unnecessary-abort-detection': verifier_command+=' && REWARD_PATH=/tmp/reward.txt python /verifier/score_outputs.py && cat /tmp/reward.txt'
verify=['docker','run','--rm','--network','none','--cpus','1','--memory','768m','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','-e','PYTHONPATH=/deps','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1','--mount',f'type=bind,src={work},dst={target}', '--mount',f'type=bind,src={src / "verifier"},dst=/verifier,readonly','--mount',f'type=bind,src={DEPS},dst=/deps,readonly','--workdir',target,'python:3.12-slim','/bin/sh','-c',verifier_command]
try:
 v=subprocess.run(verify,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);vrc=v.returncode;vout=v.stdout
except subprocess.TimeoutExpired as e:vrc=124;vout=e.stdout or b''
(case/'verifier.txt').write_bytes(vout)
receipt={'task':task,'arm':arm,'status':'DEVELOPMENT_ONLY','agent_exit':rc,'verifier_exit':vrc,'elapsed_seconds':round(time.time()-start,3),'model_http_requests':calls,'post_content_lengths':payload_bytes,'step_finish_tokens':tokens,'raw_bytes':len(out),'stderr_bytes':len(err),'output_files':sorted(p.name for p in work.iterdir()),'skills_prompted':skills,'sandbox':'docker network none; verifier absent during agent; limited UDS proxy','raw_sha256':hashlib.sha256(out).hexdigest()}
(case/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
