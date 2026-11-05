#!/usr/bin/env python3
"""Local-only original Requests #3481 stream20 probe; no model or external network."""
from __future__ import annotations
import hashlib, json, os, subprocess, sys, time
from pathlib import Path

ROOT=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
OUT=ROOT/'requests_streaming_probe_20261105'
QUAL=ROOT/'requests_qualification_20261105_v3/target'
AGENT=ROOT/'requests_agent_20261105/attempts/pilot1'
LEGACY=Path('/home/testuser/miniconda3/envs/haiguan')
SITE=ROOT/'requests_qualification_20261105/env/lib/python3.8/site-packages'
IMAGE='sha256:648a1999badfe683239ec49e05b2a508e37f762213478122c58fa713f6c00f58'
ARMS={'base':QUAL/'base','gold':QUAL/'gold', 'no_history':AGENT/'target__none__seed7201/work', 'source_history':AGENT/'target__source_history__seed7201/work'}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def worker():
    import contextlib, socket, threading, traceback
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from httpbin import app
    import requests
    # Serve actual httpbin route body, with explicitly chunked transport as in
    # the issue stack trace. All requests are confined to container loopback.
    class Handler(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'
        def log_message(self,*args): pass
        def do_GET(self):
            if self.path != '/stream/20': self.send_error(404); return
            r=app.test_client().get(self.path)
            self.send_response(r.status_code)
            self.send_header('Content-Type',r.headers['Content-Type'])
            self.send_header('Transfer-Encoding','chunked')
            self.send_header('Connection','close')
            self.end_headers()
            try:
                for chunk in r.response:
                    self.wfile.write(('%x\r\n' % len(chunk)).encode('ascii')+chunk+b'\r\n')
                    self.wfile.flush()
                self.wfile.write(b'0\r\n\r\n');self.wfile.flush()
            except (BrokenPipeError,ConnectionResetError): pass
    server=HTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    socket.setdefaulttimeout(10)
    url='http://127.0.0.1:%s/stream/20' % server.server_port
    trials={}
    for case in ('as_issue','explicit_utf8_control'):
        result={'url':url,'stream':True,'chunk_size':30,'decode_unicode':True,
                'manual_encoding':'utf-8' if case=='explicit_utf8_control' else None,'lines':[]}
        try:
            # Original issue code: closing(get(..., stream=True)) and
            # iter_lines(chunk_size=30, decode_unicode=True). Only URL is local.
            with contextlib.closing(requests.get(url,stream=True)) as response:
                result.update({'status_code':response.status_code,'content_type':response.headers.get('Content-Type'),
                               'transfer_encoding':response.headers.get('Transfer-Encoding'),
                               'initial_encoding':response.encoding})
                if case=='explicit_utf8_control': response.encoding='utf-8'
                for line in response.iter_lines(chunk_size=30,decode_unicode=True):
                    result['lines'].append({'type':type(line).__name__,
                       'value':line.decode('utf8',errors='replace') if isinstance(line,bytes) else line})
            result['exception']=None
        except Exception as exc:
            result['exception']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
        ids=[]
        for line in result['lines']:
            try: ids.append(json.loads(line['value'])['id'])
            except (ValueError,KeyError,TypeError): ids.append(None)
        result['line_count']=len(result['lines']); result['ids']=ids
        result['all_twenty']=ids==list(range(20)) and result['exception'] is None
        trials[case]=result
    server.shutdown();server.server_close()
    print(json.dumps({'requests_version':requests.__version__,'requests_file':requests.__file__,
                      'network':'container --network none; loopback server only',
                      'server':'local python httpbin /stream/20 response, HTTP/1.1 chunked',
                      'trials':trials},ensure_ascii=False))

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    snapshot={'script_sha256':sha(Path(__file__)),'image':IMAGE,'arms':{},'model_calls':0,'training':0}
    for name,work in ARMS.items():
        if not work.is_dir(): raise FileNotFoundError(work)
        interesting=['requests/models.py','requests/utils.py','requests/packages/urllib3/response.py']
        versions={p:sha(work/p) if (work/p).is_file() else None for p in interesting}
        cmd=['docker','run','--rm','--pull','never','--network','none','--read-only',
             '--cpus','2','--memory','3g','--pids-limit','256','--cap-drop','ALL','--security-opt','no-new-privileges',
             '--tmpfs','/tmp:rw,nosuid,size=128m','-e','HOME=/tmp','-e','PYTHONPATH=/workspace:/deps',
             '-e','PYTHONDONTWRITEBYTECODE=1',
             '--mount',f'type=bind,src={work},dst=/workspace,readonly',
             '--mount',f'type=bind,src={LEGACY},dst=/opt/legacy,readonly',
             '--mount',f'type=bind,src={SITE},dst=/deps,readonly',
             '--mount',f'type=bind,src={Path(__file__).resolve()},dst=/probe.py,readonly',
             '--workdir','/workspace','--entrypoint','/opt/legacy/bin/python',IMAGE,'/probe.py','--worker']
        start=time.monotonic()
        try:
            p=subprocess.run(cmd,capture_output=True,timeout=90)
            code,stdout,stderr=p.returncode,p.stdout,p.stderr
        except subprocess.TimeoutExpired as e:
            code,stdout,stderr=124,e.stdout or b'',e.stderr or b''
        (OUT/(name+'.stdout')).write_bytes(stdout); (OUT/(name+'.stderr')).write_bytes(stderr)
        entry={'work':str(work),'file_sha256':versions,'exit':code,
               'stdout_sha256':sha(OUT/(name+'.stdout')),'stderr_sha256':sha(OUT/(name+'.stderr')),
               'seconds':round(time.monotonic()-start,3)}
        try: entry['result']=json.loads(stdout)
        except (ValueError,UnicodeDecodeError): entry['result']=None
        snapshot['arms'][name]=entry
        (OUT/'receipt.json').write_text(json.dumps(snapshot,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(json.dumps(snapshot,indent=2,ensure_ascii=False))

if __name__=='__main__':
    if '--worker' in sys.argv: worker()
    else: main()
