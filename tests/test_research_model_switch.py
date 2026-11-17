"""Regression checks for stopping a starting or orphaned research model."""
import json
from contextlib import nullcontext
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest

pytestmark=pytest.mark.skipif(sys.platform!='linux',reason='Linux process ownership contract')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/agent_frontier_portfolio_20261029'))
import finqa_patch_learning as switch
from scripts.graph import research_gpu_guard as guard


def sandbox(tmp_path,monkeypatch):
    root=tmp_path/'research_services';root.mkdir()
    boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    (root/'qwen27b_current.json').write_text(json.dumps(dict(boot_id=boot,
        container_name='research-qwen27b-current',settings=dict(VLLM_IMAGE='test-image'))))
    monkeypatch.setattr(switch.m.study,'PRIVATE',tmp_path)
    monkeypatch.setattr(guard,'gpu_lease',lambda **kwargs:nullcontext())
    running=root/'running'
    monkeypatch.setattr(guard,'container_info',lambda name:dict(id='test-id',image='test-image',running=True) if running.exists() else None)
    monkeypatch.setattr(guard,'stop_owned',lambda identity,*args:running.unlink())
    return root,boot


def test_startup_guard_registers_container_before_stop(tmp_path,monkeypatch):
    root,boot=sandbox(tmp_path,monkeypatch)
    child='''import json,os,signal,sys,time
from pathlib import Path
p=Path(sys.argv[1]);registered=False
state=dict(status='WAITING_CONTAINER',pid=os.getpid(),boot_id=sys.argv[2],start_ticks=Path('/proc/self/stat').read_text().split()[21])
def save():
 q=p/'next.json';q.write_text(json.dumps(state));q.replace(p/'gpu_guard_current.json')
def stop(*args):
 (p/'stopped.json').write_text(json.dumps(dict(registered=registered)))
 if registered:(p/'running').unlink()
 sys.exit(0)
signal.signal(signal.SIGTERM,stop)
(p/'running').touch();save()
while not (p/'register').exists():time.sleep(.01)
registered=True;state['container_id']='test-id';save()
while True:time.sleep(.1)
'''
    process=subprocess.Popen([sys.executable,'-c',child,str(root),boot])
    try:
        deadline=time.monotonic()+5
        while not (root/'gpu_guard_current.json').exists():
            assert time.monotonic()<deadline;time.sleep(.01)
        def release_registration(_):
            (root/'register').touch();time.sleep(.05)
        monkeypatch.setattr(switch,'time',SimpleNamespace(monotonic=time.monotonic,sleep=release_registration))
        assert switch.stop27()
        assert json.loads((root/'stopped.json').read_text())['registered']
        assert not (root/'running').exists()
    finally:
        if process.poll() is None:process.kill()
        process.wait(timeout=5)


def test_dead_guard_does_not_hide_owned_resident(tmp_path,monkeypatch):
    root,boot=sandbox(tmp_path,monkeypatch)
    (root/'gpu_guard_current.json').write_text(json.dumps(dict(pid=999999999,boot_id=boot,start_ticks='0')))
    (root/'running').touch()
    assert switch.stop27()
    assert not (root/'running').exists()
