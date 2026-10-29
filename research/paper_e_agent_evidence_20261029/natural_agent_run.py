#!/usr/bin/env python3
"""One frozen natural-source development case, isolated OpenCode, no remote network."""
import json, os, select, socket, socketserver, subprocess, sys, threading, time
from pathlib import Path

ROOT=Path('/home/testuser/wzh/research_evidence/paper_e_natural_agent_20261029')
case=sys.argv[1]
if case not in ('migration_base','migration_prose','scifact_1','scifact_2'): raise SystemExit('Unknown case')
prompt=json.loads((ROOT/'task_prompts.json').read_text())[case]
PUBLIC=ROOT/('docker_public_'+case); BRIDGE=ROOT/'docker_bridge'
PUBLIC.mkdir(exist_ok=True); BRIDGE.mkdir(exist_ok=True)
sockpath=BRIDGE/'model.sock'
if sockpath.exists(): raise SystemExit('Refusing to overwrite existing socket')
if not any(PUBLIC.iterdir()): raise SystemExit('Prepared files missing')
if (ROOT/f'raw_agent_container_{case}.jsonl').exists(): raise SystemExit('Refusing to overwrite raw')
config={'provider':{'gb10':{'npm':'@ai-sdk/openai-compatible','name':'isolated-local','options':{'baseURL':'http://127.0.0.1:18004/v1','timeout':120000},'models':{'qwen3.6-35b-a3b':{'name':'Qwen3.6-35B-A3B'}}}},'model':'gb10/qwen3.6-35b-a3b','permission':{'*':'deny','read':'allow'}}
(PUBLIC/'opencode.json').write_text(json.dumps(config,indent=2))
allowed={b'POST /v1/chat/completions', b'GET /v1/models'}; calls=[]

def relay(a,b):
    try:
        while True:
            ready,_,_=select.select([a,b],[],[],120)
            if not ready: break
            for s in ready:
                d=s.recv(65536)
                if not d: return
                (b if s is a else a).sendall(d)
    except (OSError,TimeoutError): pass

class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(30); first=b''
        while b'\r\n\r\n' not in first and len(first)<65536:
            d=self.request.recv(4096)
            if not d:return
            first+=d
        line=first.split(b'\r\n',1)[0].rsplit(b' ',1)[0]
        if line not in allowed:
            calls.append('DENIED'); self.request.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n'); return
        calls.append(line.decode()); upstream=socket.create_connection(('127.0.0.1',8004),timeout=30)
        try: upstream.sendall(first); relay(self.request,upstream)
        finally: upstream.close()

class UnixServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads=True

entry='''import select,socket,threading,subprocess,os\ndef proxy(c):\n s=socket.socket(socket.AF_UNIX);s.connect('/bridge/model.sock')\n try:\n  while 1:\n   ready,_,_=select.select([c,s],[],[],120)\n   if not ready:break\n   for x in ready:\n    b=x.recv(65536)\n    if not b:return\n    (s if x is c else c).sendall(b)\n finally:c.close();s.close()\nl=socket.socket();l.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);l.bind(('127.0.0.1',18004));l.listen(8)\ndef serve():\n while 1:\n  c,_=l.accept();threading.Thread(target=proxy,args=(c,),daemon=True).start()\nthreading.Thread(target=serve,daemon=True).start()\np=subprocess.run(['/opt/opencode','run','--pure','--format','json','-m','gb10/qwen3.6-35b-a3b','--title','paper-e-container-qualification','Read /task/report.txt using the read tool. What was North revenue in 2025 Q4? State the answer and filename. Do not use other tools.'],stdin=subprocess.DEVNULL);raise SystemExit(p.returncode)'''
name=f'paper-e-qualification-{os.getpid()}-{int(time.time())}'
entry=entry.replace('Read /task/report.txt using the read tool. What was North revenue in 2025 Q4? State the answer and filename. Do not use other tools.',prompt.replace("'", "\\'"))
cmd=['docker','run','--name',name,'--rm','--pull','never','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','128','--memory','2g','--tmpfs','/tmp:rw,nosuid,size=128m','--tmpfs','/home/agent:rw,nosuid,size=256m','--env','HOME=/home/agent','--env','OPENCODE_DISABLE_MODELS_FETCH=1','--mount',f'type=bind,src={PUBLIC},dst=/task,readonly','--mount',f'type=bind,src={BRIDGE},dst=/bridge,readonly','--mount','type=bind,src=/home/testuser/.opencode/bin/opencode,dst=/opt/opencode,readonly','--workdir','/task','--entrypoint','python3','python:3.12-slim','-c',entry]
started=time.time(); server=UnixServer(str(sockpath),Handler);os.chmod(sockpath,0o666);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    try:
        r=subprocess.run(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=150); rc=r.returncode; out=r.stdout; err=r.stderr
    except subprocess.TimeoutExpired as e:
        subprocess.run(['docker','kill',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
        rc=124;out=e.stdout or b'';err=e.stderr or b''
    (ROOT/f'raw_agent_container_{case}.jsonl').write_bytes(out);(ROOT/f'stderr_container_{case}.txt').write_bytes(err)
    report={'status':'natural_source_development','fixture_case':case,'exit_code':rc,'elapsed_seconds':time.time()-started,'allowed_model_http_requests':calls,'docker_network':'none','task_mount':'read-only','host_home_mounted':False,'raw_bytes':len(out),'stderr_bytes':len(err)}
    (ROOT/f'container_{case}_receipt.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
finally:
    server.shutdown();server.server_close();sockpath.unlink(missing_ok=True)
