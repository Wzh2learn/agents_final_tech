import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

CODE=Path(__file__).resolve().parents[1]/'scripts/graph/research_gpu_guard.py'
spec=importlib.util.spec_from_file_location('research_gpu_guard',CODE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


@unittest.skipUnless(sys.platform=='linux','actual flock semantics are tested on GB10')
class GPUWeightsLeaseTests(unittest.TestCase):
    def test_resident_lease_excludes_another_loader_until_release(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(m,'available_gib',return_value=80):
            lock=Path(folder)/'gpu.lock'
            with m.gpu_lease(48,lock):
                with self.assertRaises(m.GPUResourceBusy):m.acquire_gpu_lease(48,lock)
            with m.gpu_lease(48,lock):self.assertTrue(lock.is_file())

    def test_headroom_rejection_does_not_leak_the_lease(self):
        with tempfile.TemporaryDirectory() as folder:
            lock=Path(folder)/'gpu.lock'
            with patch.object(m,'available_gib',return_value=10):
                with self.assertRaises(m.GPUResourceBusy):m.acquire_gpu_lease(48,lock)
            with patch.object(m,'available_gib',return_value=80):
                with m.gpu_lease(48,lock):pass

    def test_low_memory_stops_the_immutable_owned_container_id(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);metadata=root/'model.json'
            metadata.write_text(json.dumps(dict(
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                container_name='research-qwen27b-current',settings={'VLLM_IMAGE':'owned-image'})))
            info=dict(id='original-container-id',image='owned-image',running=True)
            with patch.object(m,'RUNTIME',root),patch.object(m,'LOCK',root/'gpu.lock'), \
                 patch.object(m,'available_gib',side_effect=[80,10]), \
                 patch.object(m,'container_info',return_value=info), \
                 patch.object(m.signal,'signal'), \
                 patch.object(m.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as stop:
                result=m.watch(metadata,reserve_gib=32,interval=.01)
            self.assertEqual(result['status'],'STOPPED_LOW_MEMORY')
            self.assertEqual(stop.call_args.args[0],['docker','stop','--time','10','original-container-id'])
            self.assertEqual(json.loads((root/'gpu_guard_current.json').read_text())['status'],'STOPPED_LOW_MEMORY')

    def test_docker_inspection_timeout_is_retriable(self):
        with patch.object(m.subprocess,'run',side_effect=subprocess.TimeoutExpired('docker',8)):
            with self.assertRaisesRegex(RuntimeError,'lease held'):m.container_info('original-id')

    def test_stop_timeout_keeps_lease_until_stop_succeeds(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(m,'available_gib',return_value=80):
            root=Path(folder);lock=root/'gpu.lock';output=root/'state.json'
            state={'status':'STOPPED_LOW_MEMORY'}
            def during_retry(_):
                self.assertEqual(json.loads(output.read_text())['status'],'STOP_RETRY_LEASE_HELD')
                with self.assertRaises(m.GPUResourceBusy):m.acquire_gpu_lease(0,lock)
            with m.gpu_lease(48,lock), \
                 patch.object(m.subprocess,'run',side_effect=[subprocess.TimeoutExpired('docker',20),SimpleNamespace(returncode=0)]) as stop, \
                 patch.object(m.time,'sleep',side_effect=during_retry):
                m.stop_owned('original-id',state,output,.01)
            self.assertEqual(state['status'],'STOPPED_LOW_MEMORY')
            self.assertEqual(stop.call_count,2)
            with m.gpu_lease(48,lock):pass


if __name__=='__main__':unittest.main()
