"""Synthetic CPU metadata/process controls; never a real model qualification."""
import copy
from contextlib import ExitStack
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029/alfworld_context_study.py'
spec = importlib.util.spec_from_file_location('alfworld_runtime_profile_tests', SCRIPT)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def gguf(path, *, layers=32, tokens=None, merges=None):
    def string(value):
        data = value.encode()
        return struct.pack('<Q', len(data)) + data
    metadata = {'general.architecture': 'qwen3', 'qwen3.block_count': layers, 'qwen3.embedding_length':4096,
        'qwen3.feed_forward_length':12288, 'qwen3.attention.head_count':32, 'qwen3.attention.head_count_kv':8,
        'tokenizer.chat_template':'ACTUAL_NEW_GGUF_TEMPLATE', 'tokenizer.ggml.pre':'qwen2',
        'tokenizer.ggml.tokens':tokens or ['A','B','<eos>'], 'tokenizer.ggml.merges':merges or ['A B']}
    body = b''
    for key, value in metadata.items():
        body += string(key)
        if type(value) is int:
            body += struct.pack('<II', 4, value)
        elif isinstance(value, str):
            body += struct.pack('<I', 8) + string(value)
        else:
            body += struct.pack('<IIQ', 9, 8, len(value)) + b''.join(string(s) for s in value)
    path.write_bytes(b'GGUF' + struct.pack('<IQQ', 3, 0, len(metadata)) + body)


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf8')


class RuntimeProfileTests(unittest.TestCase):
    def setUp(self):
        r._GGUF_DIGEST_CACHE.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.private = self.root/'private'
        self.private.mkdir()
        self.hf = self.root/'trusted_hf/Qwen3-8B'
        self.hf.mkdir(parents=True)
        self.exe = self.root/'trusted_llama_server'
        self.exe.write_bytes(b'CPU_SYNTHETIC_EXECUTABLE_NOT_A_SERVER')
        config = {'architectures':['Qwen3ForCausalLM'], 'model_type':'qwen3', 'num_hidden_layers':32,
                  'hidden_size':4096, 'intermediate_size':12288, 'num_attention_heads':32, 'num_key_value_heads':8}
        dump(self.hf/'config.json', config)
        dump(self.hf/'tokenizer.json', {'model':{'vocab':{'A':0,'B':1},'merges':['A B']},
                                     'added_tokens':[{'content':'<eos>','id':2}]})
        dump(self.hf/'tokenizer_config.json', {'chat_template':'HF_TEMPLATE_MUST_NOT_REPLACE_GGUF'})
        dump(self.hf/'model.safetensors.index.json', {'weight_map':{'fake.weight':'model-1.safetensors'}})
        (self.hf/'model-1.safetensors').write_bytes(b'CPU_ONLY_NOT_MODEL_WEIGHTS')
        self.parent_path = self.private/'parent.json'
        dump(self.parent_path, {'model_dir':str(self.hf), 'files':[
            {'path':str(p), 'sha256':r.sha(p), 'bytes':p.stat().st_size} for p in sorted(self.hf.iterdir())]})
        self.gguf = self.private/'new_parent.gguf'
        gguf(self.gguf)
        self.admission_path = self.private/'admission.json'
        self.profile_path = self.private/'profile.json'
        self.profile = {'schema':'alfworld_owned_8b_runtime_profile_v1', 'variant':'frozen',
            'host':'127.0.0.1','port':18104,'model_id':'qwen3-8b-qual','context':32768,'output':8192,
            'enable_thinking':False,'gguf_path':str(self.gguf),'gguf_sha256':r.sha(self.gguf),
            'server_executable':str(self.exe),'server_executable_sha256':r.sha(self.exe),
            'parent_hf_binding':{'path':str(self.parent_path),'sha256':r.sha(self.parent_path)},
            'runtime_admission':{'path':str(self.admission_path),'sha256':''}}
        self.admission = {'schema':'owned_8b_runtime_admission_v1','status':'OWNED_RESEARCH_RUNTIME_READY',
            'process':{'pid':777,'start_ticks':'12345','cwd':str(self.root),'exe':str(self.exe),
                'argv':[str(self.exe),'-m',str(self.gguf),'--host','127.0.0.1','--port','18104',
                    '--alias','qwen3-8b-qual','-c','32768','-n','8192','-np','1','--no-context-shift']},
            'gguf':{'path':str(self.gguf),'sha256':r.sha(self.gguf)},'model_alias':'qwen3-8b-qual',
            'active_lora':None,'parent_hf_binding':self.profile['parent_hf_binding']}
        self.save()
        self.real_rec = r.recovery()
        self.real_core = self.real_rec.actor()
        self.legacy = {'model_id':'legacy-unchanged','server_executable_sha256':r.sha(self.exe)}
        self.core = SimpleNamespace(load_profile=mock.Mock(return_value=self.legacy))
        self.rec = SimpleNamespace(actor=lambda:self.core)
        stack = self.enterContext(ExitStack())
        for obj, name, value in ((r,'QUAL',self.private/'qual'), (r,'HF8B',self.hf),
                                 (r,'OWNED8B_EXE',self.exe), (r,'recovery',lambda:self.rec)):
            stack.enter_context(mock.patch.object(obj,name,value))
        stack.enter_context(mock.patch('socket.create_connection', side_effect=AssertionError('CPU tests never request an endpoint')))

    def save(self):
        dump(self.admission_path,self.admission)
        self.profile['runtime_admission']['sha256'] = r.sha(self.admission_path)
        dump(self.profile_path,self.profile)
        self.digest = r.sha(self.profile_path)

    def load(self):
        return r.load_study_profile('student8b', self.profile_path, self.digest)

    def readonly_gguf(self):
        self.gguf.chmod(0o444)
        self.addCleanup(lambda:self.gguf.chmod(0o644) if self.gguf.exists() else None)

    @unittest.skipUnless(os.name=='posix','ctime-based reuse requires POSIX semantics')
    def test_readonly_gguf_reuses_only_its_hash_with_stable_manifest_scope(self):
        self.readonly_gguf()
        for path in (self.profile_path,self.parent_path,self.admission_path):path.chmod(0o444)
        with mock.patch.object(r,'runtime_digest',wraps=r.runtime_digest) as digest:
            first=self.load()[1];second=self.load()[1]
            paths=[Path(call.args[0]) for call in digest.call_args_list]
            self.assertEqual(paths.count(self.gguf),1)
            for path in (self.profile_path,self.parent_path,self.admission_path,self.exe,self.hf/'tokenizer.json'):
                self.assertEqual(paths.count(path),2)
        self.assertEqual(first,second)
        proof=first['gguf_verification']
        self.assertEqual(set(proof),{'path','sha256','file_identity','scope'})
        self.assertEqual(set(proof['file_identity']),set(r._GGUF_IDENTITY_FIELDS))
        self.assertIn('same_process',proof['scope'])

    def test_writable_gguf_is_always_hashed_and_never_chmodded(self):
        mode=self.gguf.stat().st_mode
        with mock.patch.object(r,'runtime_digest',wraps=r.runtime_digest) as digest:
            first=r.verified_gguf(self.gguf,self.profile['gguf_sha256'])[1]
            second=r.verified_gguf(self.gguf,self.profile['gguf_sha256'])[1]
        self.assertEqual(digest.call_count,2)
        self.assertEqual(first,second)
        self.assertEqual(first['scope'],'stream_sha256_every_load')
        self.assertEqual(self.gguf.stat().st_mode,mode)

    @unittest.skipUnless(os.name=='posix','ctime-based reuse requires POSIX semantics')
    def test_wrong_digest_or_new_process_never_reuses_a_prior_proof(self):
        self.readonly_gguf()
        expected=self.profile['gguf_sha256']
        with mock.patch.object(r,'runtime_digest',wraps=r.runtime_digest) as digest:
            r.verified_gguf(self.gguf,expected)
            for _ in range(2):
                with self.assertRaisesRegex(ValueError,'hash changed'):r.verified_gguf(self.gguf,'0'*64)
            r.verified_gguf(self.gguf,expected)
            self.assertEqual(digest.call_count,3)
            with mock.patch.object(r.os,'getpid',return_value=r._GGUF_DIGEST_PID+1):
                r.verified_gguf(self.gguf,expected)
            self.assertEqual(digest.call_count,4)

    @unittest.skipUnless(os.name=='posix','ctime-based reuse requires POSIX semantics')
    def test_inplace_write_with_restored_mtime_cannot_hit_the_readonly_cache(self):
        self.readonly_gguf()
        expected=self.profile['gguf_sha256']
        r.verified_gguf(self.gguf,expected)
        before=self.gguf.stat()
        self.gguf.chmod(0o644)
        gguf(self.gguf,layers=16)
        os.utime(self.gguf,ns=(before.st_atime_ns,before.st_mtime_ns))
        self.gguf.chmod(0o444)
        self.assertEqual(self.gguf.stat().st_mtime_ns,before.st_mtime_ns)
        self.assertNotEqual(self.gguf.stat().st_ctime_ns,before.st_ctime_ns)
        with mock.patch.object(r,'runtime_digest',wraps=r.runtime_digest) as digest:
            with self.assertRaisesRegex(ValueError,'hash changed'):r.verified_gguf(self.gguf,expected)
        self.assertEqual(digest.call_count,1)

    @unittest.skipUnless(os.name=='posix','readonly replacement uses POSIX semantics')
    def test_inode_replacement_and_hardlinks_cannot_reuse_a_prior_hash(self):
        self.readonly_gguf()
        expected=self.profile['gguf_sha256']
        with mock.patch.object(r,'runtime_digest',wraps=r.runtime_digest) as digest:
            first=r.verified_gguf(self.gguf,expected)[1]
            old=self.gguf.stat()
            replacement=self.private/'replacement.gguf';replacement.write_bytes(self.gguf.read_bytes())
            os.utime(replacement,ns=(old.st_atime_ns,old.st_mtime_ns));replacement.chmod(0o444)
            os.replace(replacement,self.gguf)
            self.assertNotEqual(self.gguf.stat().st_ino,old.st_ino)
            second=r.verified_gguf(self.gguf,expected)[1]
            self.assertEqual(digest.call_count,2)
            self.assertNotEqual(first['file_identity'],second['file_identity'])
            os.link(self.gguf,self.private/'second_link.gguf')
            linked=r.verified_gguf(self.gguf,expected)[1]
            r.verified_gguf(self.gguf,expected)
            self.assertEqual(digest.call_count,4)
            self.assertEqual(linked['scope'],'stream_sha256_every_load')

    @unittest.skipUnless(os.name=='posix','ctime race detection requires POSIX semantics')
    def test_hash_time_mutation_is_rejected_without_caching(self):
        self.readonly_gguf()
        before=self.gguf.stat()
        original=r.runtime_digest
        def mutate_after_read(path):
            value=original(path)
            self.gguf.chmod(0o644);gguf(self.gguf,layers=16)
            os.utime(self.gguf,ns=(before.st_atime_ns,before.st_mtime_ns));self.gguf.chmod(0o444)
            return value
        with mock.patch.object(r,'runtime_digest',side_effect=mutate_after_read):
            with self.assertRaisesRegex(ValueError,'identity changed during full hash'):
                r.verified_gguf(self.gguf,self.profile['gguf_sha256'])
        self.assertEqual(len(r._GGUF_DIGEST_CACHE),0)

    def test_reference_context_requires_pair_and_only_reset_student(self):
        path=self.private/'bank.txt';path.write_bytes(b'PUBLIC_HISTORY_ONLY')
        digest=r.sha(path)
        self.assertEqual(r.load_reference_context('ordinary_reset','student8b'),(None,None))
        for p,d in ((path,None),(None,digest)):
            with self.subTest(path=p,digest=d),self.assertRaises(ValueError):
                r.load_reference_context('ordinary_reset','student8b',p,d)
        for stage,backend in [(s,'student8b') for s in r.STAGES if s!='ordinary_reset']+[('ordinary_reset','teacher27b')]:
            with self.subTest(stage=stage,backend=backend),self.assertRaises(ValueError):
                r.load_reference_context(stage,backend,path,digest)

    def test_reference_context_rereads_utf8_and_rejects_mutation_or_escape(self):
        path=self.private/'bank.txt';text='Historical public feedback\n经验 remains task-dependent.\n'
        path.write_bytes(text.encode('utf8'));digest=r.sha(path)
        proof,actual=r.load_reference_context('ordinary_reset','student8b',path,digest)
        self.assertEqual(actual,text)
        self.assertEqual(proof['text_sha256'],digest)
        path.write_bytes(b'CHANGED')
        with self.assertRaisesRegex(ValueError,'hash changed'):
            r.load_reference_context('ordinary_reset','student8b',path,digest)
        for raw in (b' \n\t',b'\xff'):
            path.write_bytes(raw)
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                r.load_reference_context('ordinary_reset','student8b',path,r.sha(path))
        outside=self.root/'outside_bank.txt';outside.write_bytes(b'PUBLIC_BUT_OUTSIDE_ROOT')
        with self.assertRaisesRegex(ValueError,'unsafe runtime'):
            r.load_reference_context('ordinary_reset','student8b',outside,r.sha(outside))

    def test_default_remains_exact_legacy_and_partial_pair_or_teacher_fails(self):
        self.assertEqual(r.load_study_profile('student8b'), (self.legacy,None))
        self.core.load_profile.assert_called_once_with('student8b')
        for path,digest in ((self.profile_path,None),(None,self.digest)):
            with self.subTest(path=path,digest=digest), self.assertRaises(ValueError):
                r.load_study_profile('student8b',path,digest)
        with self.assertRaisesRegex(ValueError,'student8b only'):
            r.load_study_profile('teacher27b',self.profile_path,self.digest)

    def test_profile_rejects_digest_ports_escape_symlink_and_mutation(self):
        with self.assertRaisesRegex(ValueError,'hash changed'):
            r.load_study_profile('student8b',self.profile_path,'0'*64)
        for port in (8004,5050):
            with self.subTest(port=port):
                self.profile['port']=port;self.save()
                with self.assertRaises(ValueError):self.load()
        self.profile['port']=18104;self.save()
        outside=self.root/'outside.json';outside.write_bytes(self.profile_path.read_bytes())
        with self.assertRaisesRegex(ValueError,'unsafe runtime'):
            r.load_study_profile('student8b',outside,r.sha(outside))
        with self.assertRaises(ValueError):
            r.load_study_profile('student8b',self.private/'../outside.json',r.sha(outside))
        if sys.platform != 'win32':
            link=self.private/'link.json';link.symlink_to(self.profile_path)
            with self.assertRaises(ValueError):r.load_study_profile('student8b',link,self.digest)
        self.profile_path.write_text('{}',encoding='utf8')
        with self.assertRaises(ValueError):self.load()

    def test_new_gguf_architecture_and_parent_tokenizer_are_checked(self):
        profile,binding=self.load()
        self.assertEqual(profile['gguf_path'],str(self.gguf))
        self.assertEqual(binding['profile'],self.profile)
        self.assertFalse(binding['parent_weights_rehashed_here'])
        gguf(self.gguf,layers=16)
        self.profile['gguf_sha256']=r.sha(self.gguf)
        self.admission['gguf']['sha256']=r.sha(self.gguf);self.save()
        with self.assertRaisesRegex(ValueError,'architecture'):
            self.load()
        gguf(self.gguf)
        self.profile['gguf_sha256']=r.sha(self.gguf);self.admission['gguf']['sha256']=r.sha(self.gguf);self.save()
        (self.hf/'tokenizer.json').write_text('{}',encoding='utf8')
        with self.assertRaisesRegex(ValueError,'hash changed'):
            self.load()

    def test_fresh_per_arm_adapter_references_are_bound_without_activation(self):
        adapter=self.private/'ordinary.gguf';adapter.write_bytes(b'CPU_ONLY_ADAPTER_REFERENCE')
        self.profile['variant']='ordinary'
        self.admission['active_lora']={'path':str(adapter),'sha256':r.sha(adapter),'scale':1}
        self.admission['process']['argv']+=['--lora',str(adapter)];self.save()
        self.assertEqual(self.load()[1]['runtime_admission']['active_lora']['sha256'],r.sha(adapter))
        self.admission['active_lora']['scale']=0.5;self.save()
        with self.assertRaises(ValueError):self.load()
        self.admission['active_lora']['scale']=1;self.profile['variant']='frozen';self.save()
        with self.assertRaises(ValueError):self.load()

    def test_actual_process_pid_reuse_argv_executable_and_listener_are_checked(self):
        binding=self.load()[1]
        process=self.admission['process']
        proc_root=self.private/'fake_proc';proc=proc_root/str(process['pid'])
        (proc/'net').mkdir(parents=True);(proc/'fd').mkdir()
        raw=b'\0'.join(a.encode() for a in process['argv'])+b'\0'
        (proc/'cmdline').write_bytes(raw);(proc/'exe').write_bytes(self.exe.read_bytes())
        stat=lambda ticks:f"777 (CPU fake process) S {'0 '*18}{ticks}\n"
        (proc/'stat').write_text(stat('12345'))
        (proc/'fd/5').write_bytes(b'CPU_FAKE_SOCKET')
        net='header\n0: 0100007F:46B8 00000000:0000 0A 0:0 00:0 0 1000 0 123 1\n'
        (proc/'net/tcp').write_text(net)
        real_path=Path
        def redirect(value):return proc_root if str(value)=='/proc' else real_path(value)
        links={str(proc/'cwd'):process['cwd'],str(proc/'exe'):process['exe'],str(proc/'fd/5'):'socket:[123]'}
        with mock.patch.object(r,'Path',side_effect=redirect),mock.patch.object(r.os,'readlink',side_effect=lambda p:links[str(p)]):
            self.assertTrue(r.verify_runtime_identity(binding)['owns_loopback_listener'])
            (proc/'stat').write_text(stat('99999'))
            with self.assertRaisesRegex(ValueError,'process changed'):r.verify_runtime_identity(binding)
            (proc/'stat').write_text(stat('12345'));(proc/'exe').write_bytes(b'wrong actual binary')
            with self.assertRaisesRegex(ValueError,'running executable'):r.verify_runtime_identity(binding)
            (proc/'exe').write_bytes(self.exe.read_bytes());links[str(proc/'fd/5')]='socket:[999]'
            with self.assertRaisesRegex(ValueError,'does not own'):r.verify_runtime_identity(binding)

    def test_duplicate_inline_model_flags_cannot_hide_a_different_gguf(self):
        for extra in (['--model','old.gguf'],['--model=old.gguf'],['--port=8004']):
            with self.subTest(extra=extra):
                changed=copy.deepcopy(self.admission);changed['process']['argv']+=extra
                with self.assertRaises(ValueError):r.runtime_argv(self.profile,changed)

    def test_actual_legacy_token_qualifier_reads_new_template_and_rejects_ids_merges(self):
        rec=self.real_rec
        real_path=Path
        def redirect(value):
            return self.hf.parent if str(value)=='/home/testuser/wzh/models/hf' else real_path(value)
        tokenizer=SimpleNamespace(apply_chat_template=mock.Mock(return_value=[0,1,2]))
        loader=mock.Mock(return_value=tokenizer)
        fake_transformers=SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=loader))
        with mock.patch.object(rec,'Path',side_effect=redirect), \
             mock.patch.object(rec.importlib.metadata,'version',return_value='CPU_MOCK'), \
             mock.patch.dict(sys.modules,{'transformers':fake_transformers}):
            binding,qualify=rec.token_qualifier('student8b',self.profile)
            self.assertEqual(binding['template_sha256'],r.hashlib.sha256(b'ACTUAL_NEW_GGUF_TEMPLATE').hexdigest())
            self.assertTrue(binding['vocab_mapping_all_equal'])
            self.assertTrue(binding['BPE_merges_all_equal'])
            self.assertTrue(qualify({'messages':[{'role':'user','content':'public'}]})['fits'])
            self.assertEqual(tokenizer.apply_chat_template.call_args.kwargs['chat_template'],'ACTUAL_NEW_GGUF_TEMPLATE')
            for arguments in ({'tokens':['B','A','<eos>']},{'merges':['B A']}):
                gguf(self.gguf,**arguments);loader.reset_mock()
                with self.subTest(arguments=arguments),self.assertRaises(ValueError):
                    rec.token_qualifier('student8b',self.profile)
                loader.assert_not_called()

    def test_prepare_verify_freezes_complete_override_and_rejects_rehashed_metadata(self):
        self.readonly_gguf()
        def ascii_write(path,value):
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('x',encoding='utf8') as out:json.dump(value,out,ensure_ascii=True)
        self.core=SimpleNamespace(**vars(self.core), write_new=ascii_write,
            config=self.real_core.config, model_payload=self.real_core.model_payload,
            PROFILE_PINS={'student8b':('old','old-profile-sha')}, stop_world=mock.Mock(),
            dependencies=SimpleNamespace(verify_projection=mock.Mock()), RUNTIME_ROOT=self.private/'runtime',
            RUNTIME_SHA='runtime-sha', BINARY=self.exe, BINARY_SHA=r.sha(self.exe), IMAGE='CPU_MOCK')
        reset={'observation':'Your task is to: public goal.','score':0.0,'done':False,'won':False,
               'action_count':0,'admissible_commands':['look']}
        files={p.name:r.sha(p) for p in (self.hf/'tokenizer.json',self.hf/'tokenizer_config.json')}
        self.rec.bridge=lambda:SimpleNamespace(validate_response=lambda value:value)
        self.rec.token_qualifier=mock.Mock(return_value=({'model_dir':str(self.hf),'files_sha256':files,
            'template_origin':'actual_GGUF_metadata','vocab_mapping_all_equal':True,'BPE_merges_all_equal':True},mock.Mock()))
        parent=self.private/'qual/context_study_v1/cases/clean_99/ordinary_reset/student8b'
        reference=self.private/'bank.txt';reference_text='Frozen public history\n经验, without a host filename.\n'
        reference.write_bytes(reference_text.encode('utf8'))
        caps={'posts':128,'seconds':1800,'world_actions':100,'model_payload_bytes_combined':64000000}
        study={'total_caps':caps,'collection_caps':dict(caps,posts=32,seconds=600),'world_seed':17,
               'pool_path':'CPU_ONLY_NO_GOLD','pool_sha256':'pool'}
        game,pool,assignment={'game_path':'CPU_ONLY'},{'sha256':'pool'},{'carrier':'ordinary_public_history','source_id':'CPU_ONLY'}
        with mock.patch.object(r,'protocol',return_value=study), \
             mock.patch.object(r,'read_case',return_value=(game,pool,assignment,'CPU_ONLY_EXPERIENCE')), \
             mock.patch.object(r,'components',return_value={'CPU_CONTROL':'fixed'}), \
             mock.patch.object(r,'task_pool',return_value=SimpleNamespace(start_world=mock.Mock(return_value=((None,None),reset,None)))), \
             mock.patch.object(r.subprocess,'check_output',return_value='CPU_IMAGE\n'), \
             mock.patch.object(r.os,'getuid',return_value=1000,create=True), \
             mock.patch.object(r.os,'getgid',return_value=1000,create=True):
            for index,ref in enumerate((None,reference),1):
                root=parent/('attempt_v'+str(index))
                manifest=r.prepare(root,self.private/'protocol.json','f'*64,runtime_profile=self.profile_path,
                    runtime_profile_sha=self.digest,reference_context=ref,reference_context_sha=r.sha(ref) if ref else None)
                actual=r.verify(root,r.sha(root/'manifest.json'))
                self.assertEqual(manifest['runtime_profile_override']['profile'],self.profile)
                self.assertEqual(actual[2]['gguf_path'],str(self.gguf))
                self.assertFalse(manifest['sampling']['chat_template_kwargs']['enable_thinking'])
                self.assertEqual(manifest['caps'],caps)
                self.assertEqual(self.rec.token_qualifier.call_args.args[1]['gguf_path'],str(self.gguf))
                expected=r.render_prompt(reset,[],reset,reference_text if ref else '',ref is not None,'recent')
                self.assertEqual((root/'task.txt').read_bytes(),expected.encode('utf8'))
                self.assertNotIn(str(reference).encode('utf8'),(root/'task.txt').read_bytes())
                if ref:
                    original_digest=r.sha(root/'manifest.json')
                    reference.write_bytes(b'CHANGED_AFTER_FREEZE')
                    with self.assertRaisesRegex(ValueError,'hash changed'):r.verify(root,original_digest)
                    reference.write_bytes(reference_text.encode('utf8'))
                    changed=copy.deepcopy(manifest);changed['reference_context']['text_sha256']='0'*64
                    (root/'manifest.json').write_text(json.dumps(changed,ensure_ascii=True),encoding='utf8')
                    with self.assertRaisesRegex(ValueError,'frozen reference context'):r.verify(root,r.sha(root/'manifest.json'))
                else:
                    self.assertNotIn('reference_context',manifest)
            manifest['runtime_profile_override']['profile']['variant']='ordinary'
            (root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=True),encoding='utf8')
            with self.assertRaisesRegex(ValueError,'frozen runtime profile metadata'):
                r.verify(root,r.sha(root/'manifest.json'))

    def test_cli_requires_pair_and_propagates_only_to_prepare(self):
        base=['--preflight-only','--run-root',str(self.private/'unused'),'--protocol','protocol','--protocol-sha','f'*64]
        with mock.patch.object(r,'prepare',return_value={'mode':'CPU_ONLY'}) as prepare,mock.patch('sys.stderr',new_callable=io.StringIO):
            for extra in (['--runtime-profile',str(self.profile_path)],['--runtime-profile-sha',self.digest],
                          ['--reference-context',str(self.private/'bank.txt')],['--reference-context-sha','f'*64]):
                with self.subTest(extra=extra),self.assertRaises(SystemExit):r.main(base+extra)
            prepare.assert_not_called()
            with mock.patch('builtins.print'):
                r.main(base+['--runtime-profile',str(self.profile_path),'--runtime-profile-sha',self.digest])
            self.assertEqual(prepare.call_args.kwargs['runtime_profile'],self.profile_path)
            self.assertEqual(prepare.call_args.kwargs['runtime_profile_sha'],self.digest)
            self.assertIsNone(prepare.call_args.kwargs['reference_context'])
            with mock.patch('builtins.print'):
                r.main(base+['--runtime-profile',str(self.profile_path),'--runtime-profile-sha',self.digest,
                             '--reference-context',str(self.private/'bank.txt'),'--reference-context-sha','e'*64])
            self.assertEqual(prepare.call_args.kwargs['reference_context'],self.private/'bank.txt')
            self.assertEqual(prepare.call_args.kwargs['reference_context_sha'],'e'*64)
            with mock.patch.object(r,'run_episode') as execute,self.assertRaises(SystemExit):
                r.main(['--execute','--run-root',str(self.private/'unused'),'--manifest-sha','f'*64,
                        '--runtime-profile',str(self.profile_path),'--runtime-profile-sha',self.digest])
            execute.assert_not_called()
            with mock.patch.object(r,'run_episode') as execute,self.assertRaises(SystemExit):
                r.main(['--execute','--run-root',str(self.private/'unused'),'--manifest-sha','f'*64,
                        '--reference-context',str(self.private/'bank.txt'),'--reference-context-sha','e'*64])
            execute.assert_not_called()


if __name__=='__main__':
    unittest.main()
