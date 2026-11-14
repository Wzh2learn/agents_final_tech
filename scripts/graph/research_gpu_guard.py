"""One weight-loading owner; stop the owned research service under RAM pressure.

Uses the existing GPU hook's lock. RPC-only actors keep their separate task lock.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import subprocess
import time

LOCK=Path.home()/'wzh/.gpu_lock'
RUNTIME=Path.home()/'wzh/research_evidence/agent_learning_20261030/research_services'


class GPUResourceBusy(RuntimeError):pass


def available_gib():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):return int(line.split()[1])/1024**2
    raise RuntimeError('MemAvailable cannot be verified')


def acquire_gpu_lease(min_available_gib=48, lock_path=None):
    import fcntl
    path=LOCK if lock_path is None else Path(lock_path)
    path.parent.mkdir(parents=True,exist_ok=True)
    handle=path.open('a+')
    try:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise GPUResourceBusy('GPU weights already leased; unload the resident model before loading another model or training') from exc
        free=available_gib()
        if free<min_available_gib:
            raise GPUResourceBusy(f'Only {free:.1f} GiB available; need {min_available_gib:.1f} GiB before loading weights')
        return handle
    except BaseException:
        handle.close();raise


@contextmanager
def gpu_lease(min_available_gib=48,lock_path=None):
    handle=acquire_gpu_lease(min_available_gib,lock_path)
    try:yield handle
    finally:handle.close()  # Never unlink the shared lock inode.


def container_info(identity):
    try:
        result=subprocess.run(['docker','inspect','--format','{{.Id}}\n{{.Image}}\n{{.State.Running}}',identity],
                              capture_output=True,text=True,timeout=8)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('Docker state timed out; keep the GPU lease held') from exc
    if result.returncode:
        if 'No such object' in result.stderr or 'No such container' in result.stderr:return None
        raise RuntimeError('Docker state unavailable; keep the GPU lease held')
    cid,image,running=result.stdout.strip().splitlines()
    return dict(id=cid,image=image,running=running=='true')


def publish(path,value):
    tmp=Path(path).with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)


def stop_owned(identity,state,output,interval):
    """Hold the caller's lease until the original model has actually stopped."""
    reason=state['status']
    while True:
        try:
            result=subprocess.run(['docker','stop','--time','10',identity],
                                  capture_output=True,text=True,timeout=20)
            if result.returncode==0:
                state.update(status=reason,stopped_unix=time.time(),stop_exit=0)
                publish(output,state);return
            current=container_info(identity)
            if not current or not current['running']:
                state.update(status=reason,stopped_unix=time.time(),stop_exit=result.returncode)
                publish(output,state);return
        except (subprocess.TimeoutExpired,RuntimeError,OSError):
            pass
        state.update(status='STOP_RETRY_LEASE_HELD',checked_unix=time.time())
        publish(output,state);time.sleep(interval)


def watch(metadata,reserve_gib=32,interval=5):
    metadata=Path(metadata).resolve()
    metadata.relative_to(RUNTIME.resolve())
    service=json.loads(metadata.read_text())
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if service.get('boot_id')!=boot or service.get('container_name')!='research-qwen27b-current':
        raise ValueError('Only this boot\'s owned research model may be guarded')
    info=container_info(service['container_name'])
    if not info or not info['running'] or info['image']!=service['settings']['VLLM_IMAGE']:
        raise ValueError('Owned container identity does not match')
    identity=info['id'];requested_stop=False
    def stop_request(*_):
        nonlocal requested_stop
        requested_stop=True
    for sig in [signal.SIGTERM,signal.SIGINT]:signal.signal(sig,stop_request)
    state=dict(status='STARTING',pid=os.getpid(),boot_id=boot,container_id=identity,
               reserve_gib=reserve_gib,lock_path=str(LOCK),interval_seconds=interval,
               service_metadata=str(metadata),started_unix=time.time())
    output=RUNTIME/'gpu_guard_current.json'
    with gpu_lease(min_available_gib=reserve_gib):
        try:
            while True:
                if requested_stop:
                    state['status']='STOPPED_BY_REQUEST';break
                try:current=container_info(identity)
                except RuntimeError:
                    state.update(status='UNKNOWN_CONTAINER_STATE',checked_unix=time.time())
                    publish(output,state);time.sleep(interval);continue
                if not current or not current['running']:
                    state['status']='OWNED_MODEL_EXITED';break
                free=available_gib()
                state.update(status='GUARDING',available_gib=free,checked_unix=time.time())
                publish(output,state)
                if requested_stop or free<reserve_gib:
                    state['status']='STOPPED_BY_REQUEST' if requested_stop else 'STOPPED_LOW_MEMORY'
                    break
                time.sleep(interval)
        finally:
            # The original immutable container ID prevents stopping a replacement.
            stop_owned(identity,state,output,interval)
    return state


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--metadata',type=Path,required=True)
    parser.add_argument('--reserve-gib',type=float,default=32);parser.add_argument('--interval',type=float,default=5)
    args=parser.parse_args()
    if args.reserve_gib<16 or args.interval<=0:parser.error('reserve >=16 GiB and positive interval required')
    print(json.dumps(watch(args.metadata,args.reserve_gib,args.interval)))
