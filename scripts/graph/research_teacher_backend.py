"""Validate the existing local research teacher without managing or probing it.

Import is side-effect free. Validation reads the supplied profile, model file,
and Linux process metadata; it never sends an HTTP request or changes a server.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re

WEIGHTS_PATH = Path('/home/testuser/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-GGUF/Qwen3.6-35B-A3B-Q4_K_M.gguf')
WEIGHTS_SHA = '4ac6a06bce551257267f49ad2226f8671a22519ccc1a4dde9d5b433d1f2a410d'
EXECUTABLE_SHA = '037e02419e78256ed4227af31fc0b2602ff04c670fb7ad4fa2429fafb03bd55d'
MODEL_ID = 'Qwen3.6-35B-A3B-Q4_K_M.gguf'
OWNER = 'shared_research_teacher_readonly_35b'
FIELDS = {'version','host','port','model_id','gguf_path','gguf_sha256','context','output',
          'pid','server_executable_sha256','thinking','ownership'}


def sha(path: Path) -> str:
    digest=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def validate_fields(p: dict) -> None:
    if not isinstance(p,dict) or set(p)!=FIELDS:
        raise ValueError('unexpected teacher profile schema')
    fixed={'version':1,'host':'127.0.0.1','port':8004,'model_id':MODEL_ID,
           'gguf_path':str(WEIGHTS_PATH),'gguf_sha256':WEIGHTS_SHA,'context':65536,'output':16384,
           'pid':2642808,'server_executable_sha256':EXECUTABLE_SHA,
           'thinking':'default_template','ownership':OWNER}
    if any(type(p[k]) is not type(v) or p[k]!=v for k,v in fixed.items()):
        raise ValueError('unexpected teacher endpoint, model, process or configuration')


def validate_model_profile(path: Path, digest: str) -> dict:
    path=Path(path)
    if not re.fullmatch(r'[0-9a-f]{64}',digest) or path.is_symlink() or not path.is_file() or sha(path)!=digest:
        raise ValueError('teacher profile missing or hash mismatch')
    p=json.loads(path.read_text(encoding='utf8'))
    validate_fields(p)
    if WEIGHTS_PATH.is_symlink() or not WEIGHTS_PATH.is_file() or sha(WEIGHTS_PATH)!=WEIGHTS_SHA:
        raise ValueError('teacher model weights unavailable or changed')
    return p


def validate_argv(argv: list[str], profile: dict) -> dict:
    values={'-m':profile['gguf_path'],'--host':profile['host'],'--port':str(profile['port']),'-c':str(profile['context'])}
    for flag,value in values.items():
        if argv.count(flag)!=1 or argv.index(flag)+1>=len(argv) or argv[argv.index(flag)+1]!=value:
            raise ValueError('teacher process command does not match expected '+flag)
    if any(x in argv for x in ('--model','--ctx-size')):
        raise ValueError('duplicate long-form teacher model/context options')
    if '--alias' in argv:
        if argv.count('--alias')!=1 or argv.index('--alias')+1>=len(argv) or argv[argv.index('--alias')+1]!=profile['model_id']:
            raise ValueError('teacher alias conflicts with profile')
        alias='explicit_command_line'
    else:
        if Path(profile['gguf_path']).name!=profile['model_id']:
            raise ValueError('implicit model filename differs from requested identifier')
        alias='model_file_basename_unverified_by_http'
    return {'alias_source':alias,'context_shift':'explicitly_disabled' if '--no-context-shift' in argv else 'UNKNOWN',
            'parallel_slots':'UNKNOWN','output_limit':'request_cap_not_confirmed_from_server'}


def has_owned_listener(tcp: str, owned: set[str], port: int) -> bool:
    wanted='0100007F:'+f'{port:04X}'
    for line in tcp.splitlines()[1:]:
        columns=line.split()
        if len(columns)>=10 and columns[1]==wanted and columns[3]=='0A' and columns[9] in owned:return True
    return False


def _verify_live_backend(profile: dict, proc_root: Path) -> dict:
    proc=Path(proc_root)/str(profile['pid'])
    raw=(proc/'cmdline').read_bytes()
    if not raw:raise ValueError('teacher process is not running')
    options=validate_argv(raw.decode('utf8').rstrip('\0').split('\0'),profile)
    exe=sha(proc/'exe')
    if exe!=profile['server_executable_sha256']:raise ValueError('teacher executable hash changed')
    owned=set()
    for fd in (proc/'fd').iterdir():
        try:
            match=re.fullmatch(r'socket:\[([0-9]+)\]',os.readlink(fd))
            if match:owned.add(match.group(1))
        except FileNotFoundError:pass
    if not has_owned_listener((proc/'net/tcp').read_text(),owned,profile['port']):
        raise ValueError('teacher process does not own expected loopback listener')
    return {'pid':profile['pid'],'executable_sha256':exe,'cmdline_sha256':hashlib.sha256(raw).hexdigest(),
            'owns_loopback_listener':True,'model_id':profile['model_id'],'host':profile['host'],
            'port':profile['port'],'context':profile['context'],'requested_output_cap':profile['output'],**options}


def verify_live_backend(profile: dict) -> dict:
    validate_fields(profile)
    return _verify_live_backend(profile,Path('/proc'))
