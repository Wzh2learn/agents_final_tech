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
import subprocess
import time

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


# Separate vLLM/Hugging Face contract.  The 35B GGUF schema above is unchanged.
VLLM_MODEL_ROOT=Path('/home/testuser/wzh/models/hf/Qwen3.8-27B-FP8')
VLLM_TEMPLATE=Path('/home/testuser/wzh/vllm_cache/qwen38_think_off_default.jinja')
VLLM_PRIVATE_ROOT=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030/django_aggregation_agent_20261106')
VLLM_CONTAINER_ID='4b7c8b76fd42c474f76c9ee53b13c90980dc9ddae7e62cd8201dc58cc79eadf3'
VLLM_IMAGE_ID='sha256:734134467dc5b567845fdfc1cbe5b16e9761e3b6a059b35dc8de6d8147ac997f'
VLLM_CONFIG_SHA='74227dd615bf1ea975aa676bdf355a0379858c12f394b5365cd9dfa5fc2c70bc'
VLLM_INDEX_SHA='f0838c766951bdfe76d6afbdb2771a8f67aaa2231dedb3d33cebd817729843a2'
VLLM_TEMPLATE_SHA='48e031fa478ebc48f06e5b0f0efba328a274030961f41a8a9b26877be6500f76'
VLLM_METADATA_FILES=('config.json','model.safetensors.index.json','generation_config.json','tokenizer.json',
    'tokenizer_config.json','vocab.json','merges.txt','chat_template.jinja',
    'preprocessor_config.json','video_preprocessor_config.json')
VLLM_PROFILE_FIELDS={'version','kind','host','port','model_id','model_root','weights_manifest_path',
    'weights_manifest_sha256','context','output','container_id','container_name','image_id','template_path',
    'template_sha256','pid','started_at','process_start_ticks','ownership'}


def _vllm_file(root: Path, name: str) -> Path:
    if not isinstance(name,str) or not name or Path(name).name!=name or '/' in name or '\\' in name or name in ('.','..'):
        raise ValueError('unsafe indexed file path')
    root=Path(root)
    if root.is_symlink() or not root.is_dir():raise ValueError('model root must be a real directory')
    path=root/name
    if path.is_symlink() or not path.is_file() or path.resolve().parent!=root.resolve():
        raise ValueError('model file is missing, linked, or escapes its root')
    return path


def _vllm_hash_regular(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():raise ValueError('linked or missing file')
    before=path.stat();digest=hashlib.sha256()
    flags=os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)
    fd=os.open(str(path),flags)
    with os.fdopen(fd,'rb') as f:
        opened=os.fstat(f.fileno())
        if (before.st_dev,before.st_ino)!=(opened.st_dev,opened.st_ino):raise ValueError('file changed before hashing')
        for chunk in iter(lambda:f.read(1024*1024),b''):digest.update(chunk)
        after=os.fstat(f.fileno())
    if (opened.st_size,opened.st_mtime_ns,opened.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
        raise ValueError('file changed while hashing')
    return {'sha256':digest.hexdigest(),'bytes':after.st_size}


def _vllm_index(root: Path) -> list[str]:
    index=_vllm_file(root,'model.safetensors.index.json')
    if sha(index)!=VLLM_INDEX_SHA:raise ValueError('vLLM weight index changed')
    mapping=json.loads(index.read_text(encoding='utf8')).get('weight_map')
    if not isinstance(mapping,dict) or not mapping or not all(isinstance(x,str) and x.endswith('.safetensors') for x in mapping.values()):
        raise ValueError('invalid safetensors index')
    names=sorted(set(mapping.values()))
    for name in names:_vllm_file(root,name)
    if {p.name for p in root.glob('*.safetensors')}!=set(names):
        raise ValueError('unindexed or missing safetensors file')
    return names


def _vllm_manifest_fields(manifest: dict) -> None:
    expected={'version','kind','model_root','index_sha256','config_sha256','template_path','template_sha256',
              'weight_files','files','hashed_bytes','hash_seconds'}
    if not isinstance(manifest,dict) or set(manifest)!=expected or (manifest['version'],manifest['kind'],manifest['model_root'],
            manifest['index_sha256'],manifest['config_sha256'],manifest['template_path'],manifest['template_sha256'])!=(
            1,'vllm_hf_weights',str(VLLM_MODEL_ROOT),VLLM_INDEX_SHA,VLLM_CONFIG_SHA,str(VLLM_TEMPLATE),VLLM_TEMPLATE_SHA):
        raise ValueError('unexpected vLLM weight manifest')
    names=_vllm_index(VLLM_MODEL_ROOT)
    if manifest['weight_files']!=names or set(manifest['files'])!=set(names)|set(VLLM_METADATA_FILES):
        raise ValueError('vLLM manifest file set changed')
    if manifest['files']['config.json']['sha256']!=VLLM_CONFIG_SHA or manifest['files']['model.safetensors.index.json']['sha256']!=VLLM_INDEX_SHA:
        raise ValueError('vLLM config/index digest changed')
    if sum(v['bytes'] for v in manifest['files'].values())!=manifest['hashed_bytes']:
        raise ValueError('vLLM manifest byte count changed')


def build_vllm_weights_manifest(model_root: Path, output: Path) -> dict:
    """Stream-hash every indexed shard and required metadata exactly once."""
    root,output=Path(model_root),Path(output)
    if root!=VLLM_MODEL_ROOT or output.parent.resolve()!=VLLM_PRIVATE_ROOT.resolve() or output.exists() or output.is_symlink():
        raise ValueError('unexpected model root or manifest output')
    started=time.monotonic(); names=_vllm_index(root)
    files={name:_vllm_hash_regular(_vllm_file(root,name)) for name in sorted(set(names)|set(VLLM_METADATA_FILES))}
    if VLLM_TEMPLATE.is_symlink() or _vllm_hash_regular(VLLM_TEMPLATE)['sha256']!=VLLM_TEMPLATE_SHA:
        raise ValueError('vLLM template changed')
    manifest={'version':1,'kind':'vllm_hf_weights','model_root':str(root),'index_sha256':VLLM_INDEX_SHA,
        'config_sha256':VLLM_CONFIG_SHA,'template_path':str(VLLM_TEMPLATE),'template_sha256':VLLM_TEMPLATE_SHA,
        'weight_files':names,'files':files,'hashed_bytes':sum(v['bytes'] for v in files.values()),
        'hash_seconds':round(time.monotonic()-started,3)}
    _vllm_manifest_fields(manifest)
    with output.open('x',encoding='utf8') as f:json.dump(manifest,f,indent=2);f.write('\n')
    return manifest


def inspect_vllm_container() -> dict:
    """Read only explicitly selected docker fields; Config.Env is never requested."""
    fmt=('{{json .Id}}\n{{json .Name}}\n{{json .Image}}\n{{json .State.Pid}}\n'
         '{{json .State.StartedAt}}\n{{json .State.Running}}\n{{json .HostConfig.PortBindings}}\n'
         '{{json .Config.Cmd}}\n'
         '{{range .Mounts}}{{if eq .Destination "/models/model"}}{{json .}}{{end}}{{end}}\n'
         '{{range .Mounts}}{{if eq .Destination "/models/chat_template_custom.jinja"}}{{json .}}{{end}}{{end}}')
    proc=subprocess.run(['docker','inspect','--format',fmt,VLLM_CONTAINER_ID],capture_output=True,check=True,timeout=30)
    lines=proc.stdout.decode('utf8').splitlines()
    if len(lines)!=10:raise ValueError('unexpected docker inspection result')
    vals=[json.loads(x) for x in lines]
    return {'container_id':vals[0],'container_name':vals[1].lstrip('/'),'image_id':vals[2],
            'pid':vals[3],'started_at':vals[4],'running':vals[5],'port_bindings':vals[6],
            'argv':vals[7],'model_mount':vals[8],'template_mount':vals[9],
            # Docker's PID is in the daemon's namespace, which can differ from
            # the caller's /proc; StartedAt is container start, not OS ticks.
            'process_start_ticks':None}


def _validate_vllm_live(live: dict, profile: dict | None = None) -> None:
    if (live['container_id']!=VLLM_CONTAINER_ID or live['container_name']!='vllm-probe' or
            live['image_id']!=VLLM_IMAGE_ID or live['running'] is not True or
            type(live['pid']) is not int or live['pid']<=0 or
            (live['process_start_ticks'] is not None and (type(live['process_start_ticks']) is not int or live['process_start_ticks']<=0)) or
            live['port_bindings']!={'8000/tcp':[{'HostIp':'','HostPort':'8006'}]}):
        raise ValueError('vLLM container identity, status or published port changed')
    for key,src,dst in [('model_mount',VLLM_MODEL_ROOT,'/models/model'),
                        ('template_mount',VLLM_TEMPLATE,'/models/chat_template_custom.jinja')]:
        mount=live[key]
        if (mount.get('Type'),mount.get('Source'),mount.get('Destination'),mount.get('RW'))!=('bind',str(src),dst,False):
            raise ValueError('vLLM read-only mount changed')
    argv=live['argv']
    if not isinstance(argv,list) or argv[:3]!=['vllm','serve','/models/model']:
        raise ValueError('unexpected vLLM command')
    flags={'--served-model-name':'qwen38-27b-fp8','--max-model-len':'32768','--max-num-seqs':'32',
           '--reasoning-parser':'qwen3','--tool-call-parser':'qwen3_xml','--chat-template':'/models/chat_template_custom.jinja'}
    for flag,value in flags.items():
        if argv.count(flag)!=1 or argv.index(flag)+1>=len(argv) or argv[argv.index(flag)+1]!=value:
            raise ValueError('vLLM command option changed: '+flag)
    if argv.count('--enable-prefix-caching')!=1:raise ValueError('vLLM prefix caching changed')
    if profile and any(live[k]!=profile[k] for k in ('pid','started_at','process_start_ticks')):
        raise ValueError('vLLM container/process restarted after profile creation')


def create_vllm_model_profile(profile_path: Path, manifest_path: Path, manifest_sha256: str) -> dict:
    """Bind the freshly hashed weights to the observed shared server; no HTTP."""
    profile_path,manifest_path=Path(profile_path),Path(manifest_path)
    if (profile_path.parent.resolve()!=VLLM_PRIVATE_ROOT.resolve() or manifest_path.parent.resolve()!=VLLM_PRIVATE_ROOT.resolve()
            or profile_path.exists() or profile_path.is_symlink() or manifest_path.is_symlink() or sha(manifest_path)!=manifest_sha256):
        raise ValueError('invalid profile output or manifest identity')
    _vllm_manifest_fields(json.loads(manifest_path.read_text(encoding='utf8')))
    live=inspect_vllm_container();_validate_vllm_live(live)
    profile={'version':1,'kind':'vllm_hf','host':'127.0.0.1','port':8006,'model_id':'qwen38-27b-fp8',
             'model_root':str(VLLM_MODEL_ROOT),'weights_manifest_path':str(manifest_path),
             'weights_manifest_sha256':manifest_sha256,'context':32768,'output':8192,
             'container_id':VLLM_CONTAINER_ID,'container_name':'vllm-probe','image_id':VLLM_IMAGE_ID,
             'template_path':str(VLLM_TEMPLATE),'template_sha256':VLLM_TEMPLATE_SHA,
             'pid':live['pid'],'started_at':live['started_at'],'process_start_ticks':live['process_start_ticks'],
             'ownership':'shared_research_teacher_readonly_27b'}
    with profile_path.open('x',encoding='utf8') as f:json.dump(profile,f,indent=2);f.write('\n')
    return profile


def validate_vllm_model_profile(path: Path, digest: str, *, full: bool = True) -> dict:
    """Validate profile and manifest; full=True also rehashes all indexed weights.

    `context` is the shared prompt-plus-generation limit, not an independent
    input allocation in addition to `output`.
    """
    path=Path(path)
    if path.is_symlink() or not re.fullmatch(r'[0-9a-f]{64}',digest) or sha(path)!=digest:
        raise ValueError('vLLM profile missing or hash mismatch')
    profile=json.loads(path.read_text(encoding='utf8'))
    _vllm_profile_fields(profile)
    manifest_path=Path(profile['weights_manifest_path'])
    if manifest_path.is_symlink() or manifest_path.parent.resolve()!=VLLM_PRIVATE_ROOT.resolve() or sha(manifest_path)!=profile['weights_manifest_sha256']:
        raise ValueError('vLLM weights manifest changed')
    manifest=json.loads(manifest_path.read_text(encoding='utf8'));_vllm_manifest_fields(manifest)
    if _vllm_hash_regular(VLLM_TEMPLATE)['sha256']!=VLLM_TEMPLATE_SHA:raise ValueError('vLLM template changed')
    if full:
        for name,expected in manifest['files'].items():
            if _vllm_hash_regular(_vllm_file(VLLM_MODEL_ROOT,name))!=expected:
                raise ValueError('vLLM model file changed: '+name)
    return profile


def _vllm_profile_fields(p: dict) -> None:
    if not isinstance(p,dict) or set(p)!=VLLM_PROFILE_FIELDS:raise ValueError('unexpected vLLM profile schema')
    fixed={'version':1,'kind':'vllm_hf','host':'127.0.0.1','port':8006,'model_id':'qwen38-27b-fp8',
           'model_root':str(VLLM_MODEL_ROOT),'context':32768,'output':8192,'container_id':VLLM_CONTAINER_ID,
           'container_name':'vllm-probe','image_id':VLLM_IMAGE_ID,'template_path':str(VLLM_TEMPLATE),
           'template_sha256':VLLM_TEMPLATE_SHA,'ownership':'shared_research_teacher_readonly_27b'}
    if any(type(p[k]) is not type(v) or p[k]!=v for k,v in fixed.items()):raise ValueError('unexpected vLLM endpoint or profile')
    if (type(p['pid']) is not int or p['pid']<=0 or
            (p['process_start_ticks'] is not None and (type(p['process_start_ticks']) is not int or p['process_start_ticks']<=0))
            or not isinstance(p['started_at'],str) or not p['started_at'] or
            not isinstance(p['weights_manifest_sha256'],str) or not re.fullmatch(r'[0-9a-f]{64}',p['weights_manifest_sha256'])):
        raise ValueError('invalid vLLM process or manifest identity')


def verify_vllm_backend(profile: dict) -> dict:
    """Check the same running container and its bounded command, without HTTP."""
    _vllm_profile_fields(profile)
    live=inspect_vllm_container();_validate_vllm_live(live,profile)
    if _vllm_hash_regular(VLLM_TEMPLATE)['sha256']!=VLLM_TEMPLATE_SHA:raise ValueError('vLLM template changed')
    result={k:live[k] for k in ('container_id','container_name','image_id','pid','started_at','process_start_ticks','running')}
    result.update({'caller_host':'127.0.0.1','published_host_ip':'docker_all_interfaces','context_shared_with_output':True,
                   'process_start_scope':'docker container StartedAt; host process start ticks UNKNOWN'})
    return result
