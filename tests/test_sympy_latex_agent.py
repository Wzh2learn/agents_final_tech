"""Source adapter boundary checks; synthetic requests never reach a model."""
import ast
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import shutil
import socket
import sys
import tarfile
import tempfile
import threading
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT),str(ROOT/'research/agent_frontier_portfolio_20261029')]
spec = importlib.util.spec_from_file_location('sympy_latex_test',ROOT/'research/agent_frontier_portfolio_20261029/run_sympy_latex_agent_20261106.py')
runner = importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class SympySourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.clean = self.root/'clean';self.clean.mkdir()
        self.test = self.clean/'sympy/printing/tests/test_latex.py';self.test.parent.mkdir(parents=True)
        self.test.write_text('def test_latex_functions():\n    assert True\n'+''.join(
            f'def test_case_{i}():\n    assert True\n' for i in range(114)))
        (self.clean/'module.py').write_text('source=1\n')
        self.row = {'PASS_TO_PASS':json.dumps([f'test_case_{i}' for i in range(114)]),
                    'problem_statement':'source issue only','test_patch':
                    'diff --git a/sympy/printing/tests/test_latex.py b/sympy/printing/tests/test_latex.py\n'
                    '--- a/sympy/printing/tests/test_latex.py\n+++ b/sympy/printing/tests/test_latex.py\n'
                    '@@ -1,4 +1,4 @@\n def test_latex_functions():\n-    assert True\n+    assert "hidden-check"\n'
                    ' def test_case_0():\n     assert True\n'}
        self.actor = {'runtime':str(self.root/'projection/runtime'),
                      'sites':{'default':str(self.root/'projection/deps/default')},'manifest_sha256':'a'*64}
        self.profile = {'model_id':'qwen38-27b-fp8','host':'127.0.0.1','port':8006,'context':32768,'output':8192}

    def generated_setup(self, port=8006):
        if not runner.core.BASE.exists():self.skipTest('authoritative frozen harness is on GB10')
        attempt = self.root/'attempt';source = attempt/'inputs/source';source.mkdir(parents=True)
        shutil.copytree(self.clean,source/'clean_base');(source/'task.txt').write_text('source issue only')
        runner.primitives.prepare_actor_runtime(attempt)
        with mock.patch.object(runner,'ripgrep_binding',return_value=[]):
            code = runner.derive(attempt,self.actor,dict(self.profile,port=port))
        parsed = ast.parse(code);prefix=[]
        for statement in parsed.body:
            if isinstance(statement,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='server' for t in statement.targets):break
            prefix.append(statement)
        else:self.fail('generated harness no longer exposes the server boundary')
        argv = ['harness.py','source','no_skill']
        with mock.patch.object(sys,'argv',argv):
            namespace={};exec(compile(ast.Module(body=prefix,type_ignores=[]),'<setup>','exec'),namespace)
        self.addCleanup(shutil.rmtree,namespace['bridge'],True)
        return namespace,attempt

    def test_generated_actor_command_has_only_selected_inputs_and_isolated_python(self):
        shared_root,shared_out = runner.core.ROOT,runner.primitives.shared.OUT
        namespace,attempt = self.generated_setup()
        cmd=namespace['cmd'];bindings=[cmd[i+1] for i,value in enumerate(cmd) if value=='--mount']
        self.assertIn('/extra/bin/python',cmd)
        self.assertIn('PATH=/extra/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',cmd)
        self.assertTrue(any(self.actor['sites']['default'] in value and 'readonly' in value for value in bindings))
        self.assertTrue(any('instructions.txt,dst=/root/instructions.txt,readonly' in value for value in bindings))
        self.assertFalse(any(any(part in value for part in ('qualification','_row.json','gold','probe_source','post_run_evaluation')) for value in bindings))
        task=(attempt/runner.EID/'work/instructions.txt').read_text()
        self.assertIn('source issue only',task);self.assertNotIn('hidden-check',task)
        self.assertEqual((runner.core.ROOT,runner.primitives.shared.OUT),(shared_root,shared_out))
        self.assertEqual(list((attempt/'runtime').iterdir()),[])
        (namespace['bridge']).rmdir()

    @unittest.skipUnless(hasattr(socket,'AF_UNIX') and sys.platform!='win32','Unix harness bridge')
    def test_generated_post_gate_captures_concurrent_requests_once(self):
        class FakeModel(BaseHTTPRequestHandler):
            protocol_version='HTTP/1.1'
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200);self.send_header('Content-Length','2');self.end_headers();self.wfile.write(b'{}')
            def log_message(self,*args):pass
        model=ThreadingHTTPServer(('127.0.0.1',0),FakeModel)
        threading.Thread(target=model.serve_forever,daemon=True).start()
        self.addCleanup(model.server_close);self.addCleanup(model.shutdown)
        with mock.patch.object(runner,'MAX_POSTS',3),mock.patch.object(runner,'MAX_BYTES',512):
            ns,attempt=self.generated_setup(model.server_port)
        server=ns['Server'](str(ns['sockpath']),ns['Handler'])
        threading.Thread(target=server.serve_forever,daemon=True).start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        first=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);first.settimeout(3);first.connect(str(ns['sockpath']))
        self.addCleanup(first.close)
        payload=json.dumps({'model':'placeholder','messages':[{'role':'user','content':'first'}]}).encode()
        first.sendall(b'POST /v1/chat/completions HTTP/1.1\r\nContent-Length: '+str(len(payload)).encode()+b'\r\n\r\n'+payload[:3])
        deadline=time.monotonic()+2
        while ns['post_count'][0]!=1 and time.monotonic()<deadline:time.sleep(.005)
        self.assertEqual(ns['post_count'][0],1)
        class UnixConnection(http.client.HTTPConnection):
            def connect(connection):
                connection.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);connection.sock.settimeout(3)
                connection.sock.connect(str(ns['sockpath']))
        client=UnixConnection('localhost');self.addCleanup(client.close)
        second='second'+'y'*200
        client.request('POST','/v1/chat/completions',body=json.dumps({'messages':[{'role':'user','content':second}]}))
        response=client.getresponse();self.assertEqual(response.status,200);self.assertEqual(response.getheader('Connection'),'close');response.read()
        first.sendall(payload[3:]);response=http.client.HTTPResponse(first);response.begin();self.assertEqual(response.status,200);response.read()
        client.request('POST','/v1/chat/completions',body=json.dumps({'messages':[{'role':'user','content':'z'*100}]}))
        response=client.getresponse();self.assertEqual(response.status,403);response.read()
        client.request('POST','/v1/chat/completions',body='{}');response=client.getresponse()
        self.assertEqual(response.status,403);response.read()
        captures=sorted((attempt/runner.EID/'model_request_bodies').glob('*.json'))
        self.assertEqual([p.name for p in captures],['00001.json','00002.json'])
        bodies=[json.loads(path.read_text()) for path in captures]
        self.assertEqual({b['messages'][0]['content'] for b in bodies},{'first',second})
        self.assertEqual(ns['payload_bytes'],[len(path.read_bytes()) for path in captures])
        self.assertTrue(all((b['model'],b['temperature'],b['seed'])==('qwen38-27b-fp8',.2,7201) for b in bodies))

    def test_compaction_gap_is_lower_bound_and_more_steps_than_posts_is_invalid(self):
        case=self.root/'case';directory=case/'model_request_bodies';directory.mkdir(parents=True)
        metadata=[]
        for i in (1,2):
            path=directory/f'{i:05}.json';path.write_text('{}')
            metadata.append({'request_body_file':path.name,'request_body_sha256':runner.sha(path)})
        receipt={'model_http_requests':['POST /v1/chat/completions']*2,'sampling_metadata':metadata,'step_finish_tokens':[{}]}
        result=runner.execution_integrity(case,receipt)
        self.assertTrue(result['passed']);self.assertEqual(result['requests_without_public_step_finish'],1)
        self.assertEqual(result['usage_completeness'],'LOWER_BOUND_PUBLIC_STEP_FINISH')
        receipt['step_finish_tokens']=[{}]*3;self.assertFalse(runner.execution_integrity(case,receipt)['passed'])
        receipt['step_finish_tokens']=[{}];metadata[1]=metadata[0]
        self.assertFalse(runner.execution_integrity(case,receipt)['passed'])

    def test_exact_regression_mapping_rejects_missing_duplicate_and_unsafe_nodes(self):
        self.assertEqual(len(runner.regression_nodes(self.row,self.clean)),114)
        for bad in ('test_not_present','test_case_0','../escape.py::test_x'):
            row=dict(self.row);nodes=json.loads(row['PASS_TO_PASS']);nodes[-1]=bad;row['PASS_TO_PASS']=json.dumps(nodes)
            with self.subTest(bad=bad),self.assertRaises(ValueError):runner.regression_nodes(row,self.clean)

    def fake_evaluator(self,cmd,**kwargs):
        if cmd[0]!='docker':return self.actual_run(cmd,**kwargs)
        for arg in cmd:
            if arg.startswith('type=bind,src=') and ',dst=/workspace,' in arg:
                candidate=Path(arg.split('src=',1)[1].split(',dst=',1)[0])
                self.assertIn('hidden-check',(candidate/'sympy/printing/tests/test_latex.py').read_text())
        if cmd[-1]=='/probe.py':
            stdout=b'RESULT {"pass":true,"module":"/workspace/sympy/__init__.py"}\n'
        else:stdout=f'{114 if "test_case_113" in cmd[-1] else 1} passed in 0.1s\n'.encode()
        return subprocess_result(0,stdout)

    def test_independent_evaluation_restores_nested_tests_without_changing_actor(self):
        work=self.root/'work';shutil.copytree(self.clean,work)
        changed=work/'sympy/printing/tests/test_latex.py';changed.write_text('def test_latex_functions():\n    assert False\n')
        self.actual_run=runner.subprocess.run
        with mock.patch.object(runner.subprocess,'run',side_effect=self.fake_evaluator):
            result=runner.evaluate(work,self.root/'evaluation',self.actor,self.row,self.clean)
        self.assertTrue(result['passed']);self.assertEqual(result['regression']['observed'],114)
        self.assertNotIn('hidden-check',changed.read_text());self.assertIn('assert False',changed.read_text())

    def test_success_exit_with_zero_tests_cannot_qualify(self):
        self.actual_run=runner.subprocess.run
        def empty(cmd,**kwargs):
            if cmd[0]!='docker':return self.actual_run(cmd,**kwargs)
            return subprocess_result(0,b'no tests ran\n')
        with mock.patch.object(runner.subprocess,'run',side_effect=empty):
            result=runner.evaluate(self.clean,self.root/'evaluation',self.actor,self.row,self.clean)
        self.assertFalse(result['passed']);self.assertEqual(result['focus']['observed'],0)

    def test_source_archive_and_row_identity_cannot_drift(self):
        archive=self.root/'source.tar.gz'
        with tarfile.open(archive,'w:gz') as stream:stream.add(self.clean,arcname='sympy-'+runner.SOURCE_BASE)
        self.assertEqual(runner.verify_clean(self.clean,archive),runner.tree(self.clean))
        (self.clean/'module.py').write_text('tampered\n')
        with self.assertRaises(ValueError):runner.verify_clean(self.clean,archive)
        q=self.root/'qualification';q.mkdir();(q/'artifact').write_text('expected')
        manifest=q/'FINAL_QUALIFICATION.json';manifest.write_text(json.dumps({'artifacts':{'artifact':runner.sha(q/'artifact')}}))
        (q/'source_row.json').write_text(json.dumps({'instance_id':'sympy__sympy-19487','base_commit':runner.SOURCE_BASE}))
        with mock.patch.object(runner,'QUAL',q),mock.patch.object(runner,'QUAL_SHA',runner.sha(manifest)):
            with self.assertRaisesRegex(ValueError,'wrong source row'):runner.checked_qualification()
            (q/'artifact').write_text('changed')
            with self.assertRaisesRegex(ValueError,'artifact changed'):runner.checked_qualification()

    def test_frozen_inputs_detect_tamper_and_auto_record_allows_only_one_launch(self):
        if not runner.core.BASE.exists():self.skipTest('authoritative frozen harness is on GB10')
        q=self.root/'qualification';(q/'source').mkdir(parents=True)
        shutil.copytree(self.clean,q/'source/clean')
        with tarfile.open(q/'source.tar.gz','w:gz') as stream:stream.add(q/'source/clean',arcname='sympy-'+runner.SOURCE_BASE)
        profile=self.root/'profile.json';profile.write_text(json.dumps(self.profile))
        attempt=self.root/'attempt'
        with mock.patch.object(runner,'QUAL',q),mock.patch.object(runner,'PROFILE',profile), \
             mock.patch.object(runner,'PROFILE_SHA',runner.sha(profile)), \
             mock.patch.object(runner.dependencies,'verify_projection',return_value=self.actor), \
             mock.patch.object(runner,'ripgrep_binding',return_value=[]):
            manifest=runner.freeze_inputs(attempt,self.actor,self.profile,self.row)
            digest=runner.sha(attempt/'inputs_manifest.json')
            task=attempt/'inputs/source/task.txt';original=task.read_bytes();task.write_text('changed')
            with self.assertRaisesRegex(ValueError,'frozen inputs changed'):runner.verify_inputs(attempt,manifest)
            task.write_bytes(original)
            path=attempt/'inputs_manifest.json';original_manifest=path.read_bytes()
            modified=dict(manifest,task_sha256='f'*64);path.write_text(json.dumps(modified))
            with self.assertRaisesRegex(ValueError,'reviewed inputs manifest changed'):
                runner.execute_source(attempt,modified,self.actor,self.row,self.profile,digest)
            path.write_bytes(original_manifest)
            (attempt/'preflight').mkdir();(attempt/'preflight/receipt.json').write_text('{"status":"PREFLIGHT_PASS"}')
            with mock.patch.object(runner.teacher,'verify_vllm_backend',return_value={}), \
                 mock.patch.object(runner.subprocess,'run',return_value=subprocess_result(1,b'')) as launch:
                result=runner.execute_source(attempt,manifest,self.actor,self.row,self.profile,digest)
                self.assertEqual(result['status'],'RUNNER_ERROR_REVIEW_RAW_AND_PROXY_LOG')
                self.assertEqual(launch.call_count,1)
                with self.assertRaises(FileExistsError):runner.execute_source(attempt,manifest,self.actor,self.row,self.profile,digest)
                self.assertEqual(launch.call_count,1)

    def test_projection_excludes_installed_sympy_source_and_metadata(self):
        prefix=self.root/'prefix';(prefix/'bin').mkdir(parents=True)
        (prefix/'bin/python3.8').write_bytes(b'python');(prefix/'lib/python3.8').mkdir(parents=True)
        (prefix/'lib/python3.8/os.py').write_text('stdlib')
        site=self.root/'site';site.mkdir();(site/'mpmath').mkdir();(site/'mpmath/__init__.py').write_text('dependency')
        (site/'sympy').mkdir();(site/'sympy/__init__.py').write_text('future project source')
        (site/'sympy-1.14.dist-info').mkdir();(site/'sympy-1.14.dist-info/METADATA').write_text('future metadata')
        destination=self.root/'projection'
        manifest=runner.dependencies.prepare_projection(destination,prefix,{'default':site},['sympy'],python_version='3.8')
        result=runner.dependencies.verify_projection(destination,runner.sha(manifest))
        visible=Path(result['sites']['default'])
        self.assertTrue((visible/'mpmath/__init__.py').is_file())
        self.assertFalse(any('sympy' in p.name for p in visible.iterdir()))
        self.assertFalse((Path(result['runtime'])/'lib/python3.8/site-packages').exists())

    def test_evaluator_failure_retains_known_cost_and_marks_source_unqualified(self):
        root=self.root/'attempt';(root/'inputs/source').mkdir(parents=True)
        (root/'inputs/source/task.txt').write_text('task');(root/'frozen_source_harness.py').write_text('frozen harness')
        (root/'preflight').mkdir();(root/'preflight/receipt.json').write_text('{"status":"PREFLIGHT_PASS"}')
        manifest={'projection_sha256':'a'*64,'component_sha256':{'outer_runner.py':'b'*64},
                  'task_sha256':runner.sha(root/'inputs/source/task.txt'),
                  'harness_sha256':runner.sha(root/'frozen_source_harness.py')}
        (root/'inputs_manifest.json').write_text(json.dumps(manifest));digest=runner.sha(root/'inputs_manifest.json')
        def launch(cmd,**kwargs):
            case=root/runner.EID;(case/'work').mkdir(parents=True)
            directory=case/'model_request_bodies';directory.mkdir();path=directory/'00001.json';path.write_text('{}')
            tokens={'total':7,'cache':{'read':0},'input':4,'output':3,'reasoning':0}
            raw=case/'raw.jsonl';raw.write_text(json.dumps({'type':'step_finish','part':{'tokens':tokens}})+'\n')
            metadata=[{'request_body_file':path.name,'request_body_sha256':runner.sha(path),
                       'model':'qwen38-27b-fp8','seed':7201,'temperature':.2}]
            (case/'sampling_metadata.jsonl').write_text(json.dumps(metadata[0])+'\n')
            (case/'receipt.json').write_text(json.dumps({'raw_sha256':runner.sha(raw),'agent_exit':0,
                'model_http_requests':['POST /v1/chat/completions'],'sampling_metadata':metadata,'step_finish_tokens':[tokens]}))
            return subprocess_result(0,b'')
        with mock.patch.object(runner,'verify_inputs'),mock.patch.object(runner,'checked_qualification'), \
             mock.patch.object(runner.teacher,'verify_vllm_backend',return_value={}), \
             mock.patch.object(runner.subprocess,'run',side_effect=launch), \
             mock.patch.object(runner,'evaluate',side_effect=TimeoutError):
            result=runner.execute_source(root,manifest,self.actor,self.row,self.profile,digest)
        self.assertEqual(result['posts'],1);self.assertEqual(result['reported_tokens'],7)
        self.assertTrue(result['execution_integrity']['passed'])
        self.assertEqual(result['post_run_evaluation']['status'],'EVALUATION_FAILED')
        self.assertFalse(result['source_artifact_qualification']['passed'])
        self.assertTrue((root/(runner.EID+'.completed.json')).is_file())


def subprocess_result(code,stdout):
    return runner.subprocess.CompletedProcess([],code,stdout,b'')


if __name__=='__main__':unittest.main()
