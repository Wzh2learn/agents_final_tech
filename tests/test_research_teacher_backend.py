"""Read-only teacher profile and process contracts; no service is contacted."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.graph import research_teacher_backend as teacher


class TeacherTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.gguf=self.root/'Qwen3.6-35B-A3B-Q4_K_M.gguf';self.gguf.write_bytes(b'weight')
        self.profile={'version':1,'host':'127.0.0.1','port':8004,'model_id':self.gguf.name,
                      'gguf_path':str(self.gguf),'gguf_sha256':hashlib.sha256(b'weight').hexdigest(),
                      'context':65536,'output':16384,'pid':2642808,'server_executable_sha256':'a'*64,
                      'thinking':'default_template','ownership':'shared_research_teacher_readonly_35b'}
        self.path=self.root/'profile.json';self.path.write_text(json.dumps(self.profile))

    def test_profile_rejects_changed_hash_endpoint_and_weights(self):
        with mock.patch.object(teacher,'WEIGHTS_PATH',self.gguf),mock.patch.object(teacher,'WEIGHTS_SHA',self.profile['gguf_sha256']),mock.patch.object(teacher,'EXECUTABLE_SHA','a'*64):
            self.assertEqual(teacher.validate_model_profile(self.path,teacher.sha(self.path)),self.profile)
            with self.assertRaises(ValueError):teacher.validate_model_profile(self.path,'0'*64)
            p=dict(self.profile,port=8005);self.path.write_text(json.dumps(p))
            with self.assertRaises(ValueError):teacher.validate_model_profile(self.path,teacher.sha(self.path))
            with self.assertRaises(ValueError):teacher.verify_live_backend(p)
            self.path.write_text(json.dumps(self.profile));self.gguf.write_bytes(b'other')
            with self.assertRaises(ValueError):teacher.validate_model_profile(self.path,teacher.sha(self.path))

    def test_argv_accepts_implicit_file_name_alias_not_conflicting_alias(self):
        argv=['server','-m',str(self.gguf),'--host','127.0.0.1','--port','8004','-c','65536']
        result=teacher.validate_argv(argv,self.profile)
        self.assertEqual(result['alias_source'],'model_file_basename_unverified_by_http')
        with self.assertRaises(ValueError):teacher.validate_argv(argv+['--alias','other'],self.profile)
        with self.assertRaises(ValueError):teacher.validate_argv(argv+['-c','4096'],self.profile)

    def test_listener_must_belong_to_profile_pid(self):
        tcp=('  sl local_address rem_address st tx_queue rx_queue tr tm->when retrnsmt uid timeout inode\n'
             '  0: 0100007F:1F44 00000000:0000 0A 00000000:00000000 00:00000000 00000000 1000 0 12345\n')
        self.assertTrue(teacher.has_owned_listener(tcp,{'12345'},8004))
        self.assertFalse(teacher.has_owned_listener(tcp,{'99999'},8004))
        self.assertFalse(teacher.has_owned_listener(tcp,{'12345'},8005))

    def test_process_mismatch_rejects_without_exposing_command_line(self):
        proc=self.root/'proc'/'2642808';(proc/'net').mkdir(parents=True);(proc/'fd').mkdir()
        executable=proc/'exe';executable.write_bytes(b'server')
        self.profile['server_executable_sha256']=hashlib.sha256(b'server').hexdigest()
        argv=['server','-m',str(self.gguf),'--host','127.0.0.1','--port','8004','-c','65536']
        (proc/'cmdline').write_bytes(('\0'.join(argv)+'\0').encode());(proc/'fd'/'7').touch()
        (proc/'net'/'tcp').write_text('header\n 0: 0100007F:1F44 00000000:0000 0A 0 0 0 1000 0 12345\n')
        with mock.patch.object(teacher.os,'readlink',return_value='socket:[99999]'):
            with self.assertRaises(ValueError):teacher._verify_live_backend(self.profile,self.root/'proc')
        with mock.patch.object(teacher.os,'readlink',return_value='socket:[12345]'):
            result=teacher._verify_live_backend(self.profile,self.root/'proc')
        self.assertTrue(result['owns_loopback_listener']);self.assertNotIn('argv',result)
        self.assertEqual(result['context_shift'],'UNKNOWN')


class VllmTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.model=self.root/'model';self.model.mkdir()
        self.template=self.root/'template.jinja';self.template.write_text('template')
        for name in teacher.VLLM_METADATA_FILES:
            if name!='model.safetensors.index.json':(self.model/name).write_text(name)
        (self.model/'layer.safetensors').write_bytes(b'weights')
        (self.model/'model.safetensors.index.json').write_text(json.dumps({'weight_map':{'x':'layer.safetensors','y':'layer.safetensors'}}))
        self.patches=[mock.patch.object(teacher,'VLLM_MODEL_ROOT',self.model),
            mock.patch.object(teacher,'VLLM_TEMPLATE',self.template),
            mock.patch.object(teacher,'VLLM_CONFIG_SHA',teacher.sha(self.model/'config.json')),
            mock.patch.object(teacher,'VLLM_INDEX_SHA',teacher.sha(self.model/'model.safetensors.index.json')),
            mock.patch.object(teacher,'VLLM_TEMPLATE_SHA',teacher.sha(self.template)),
            mock.patch.object(teacher,'VLLM_PRIVATE_ROOT',self.root)]
        for patch in self.patches:patch.start();self.addCleanup(patch.stop)
        self.manifest=self.root/'manifest.json';self.profile=self.root/'profile.json'
        self.live={'container_id':teacher.VLLM_CONTAINER_ID,'container_name':'vllm-probe','image_id':teacher.VLLM_IMAGE_ID,
            'pid':42,'started_at':'2026-08-21T15:41:38.036347742Z','process_start_ticks':987,
            'running':True,'port_bindings':{'8000/tcp':[{'HostIp':'','HostPort':'8006'}]},
            'model_mount':{'Source':str(self.model),'Destination':'/models/model','RW':False,'Type':'bind'},
            'template_mount':{'Source':str(self.template),'Destination':'/models/chat_template_custom.jinja','RW':False,'Type':'bind'},
            'argv':['vllm','serve','/models/model','--served-model-name','qwen38-27b-fp8','--max-num-seqs','32',
                 '--max-model-len','32768','--enable-prefix-caching','--reasoning-parser','qwen3',
                 '--tool-call-parser','qwen3_xml','--chat-template','/models/chat_template_custom.jinja']}

    def build(self):
        manifest=teacher.build_vllm_weights_manifest(self.model,self.manifest)
        self.assertEqual(manifest['weight_files'],['layer.safetensors'])
        with mock.patch.object(teacher,'inspect_vllm_container',return_value=self.live):
            profile=teacher.create_vllm_model_profile(self.profile,self.manifest,teacher.sha(self.manifest))
        return profile

    def test_manifest_and_profile_detect_wrong_inputs_or_file_tamper(self):
        profile=self.build();self.assertEqual(profile['context'],32768)
        self.assertEqual(teacher.validate_vllm_model_profile(self.profile,teacher.sha(self.profile),full=True),profile)
        with self.assertRaises(ValueError):teacher.validate_vllm_model_profile(self.profile,'0'*64,full=True)
        p=dict(profile,port=8007);self.profile.write_text(json.dumps(p))
        with self.assertRaises(ValueError):teacher.validate_vllm_model_profile(self.profile,teacher.sha(self.profile),full=True)
        for field,value in [('model_id','other'),('model_root',str(self.root/'other')),('context',65536)]:
            self.profile.write_text(json.dumps(dict(profile,**{field:value})))
            with self.assertRaises(ValueError):teacher.validate_vllm_model_profile(self.profile,teacher.sha(self.profile),full=True)
        self.profile.write_text(json.dumps(profile));(self.model/'layer.safetensors').write_bytes(b'tampered')
        with self.assertRaises(ValueError):teacher.validate_vllm_model_profile(self.profile,teacher.sha(self.profile),full=True)

    def test_live_contract_rejects_mapping_identity_and_context_changes(self):
        profile=self.build()
        with mock.patch.object(teacher,'inspect_vllm_container',return_value=self.live):
            self.assertTrue(teacher.verify_vllm_backend(profile)['running'])
        for field,value in [('port_bindings',{'8000/tcp':[{'HostIp':'','HostPort':'9999'}]}),
                            ('container_id','f'*64),('image_id','sha256:'+'0'*64),('pid',43),
                            ('started_at','2026-08-22T15:41:38Z'),('process_start_ticks',988)]:
            broken=dict(self.live,**{field:value})
            with mock.patch.object(teacher,'inspect_vllm_container',return_value=broken):
                with self.assertRaises(ValueError):teacher.verify_vllm_backend(profile)
        broken=dict(self.live,argv=[x if x!='32768' else '65536' for x in self.live['argv']])
        with mock.patch.object(teacher,'inspect_vllm_container',return_value=broken):
            with self.assertRaises(ValueError):teacher.verify_vllm_backend(profile)
        broken=dict(self.live,model_mount=dict(self.live['model_mount'],RW=True))
        with mock.patch.object(teacher,'inspect_vllm_container',return_value=broken):
            with self.assertRaises(ValueError):teacher.verify_vllm_backend(profile)

    def test_index_cannot_escape_or_duplicate_untracked_weight(self):
        index=self.model/'model.safetensors.index.json'
        index.write_text(json.dumps({'weight_map':{'x':'../secret.safetensors'}}))
        with mock.patch.object(teacher,'VLLM_INDEX_SHA',teacher.sha(index)):
            with self.assertRaises(ValueError):teacher.build_vllm_weights_manifest(self.model,self.manifest)

    def test_manifest_tamper_is_rejected(self):
        self.build();profile_digest=teacher.sha(self.profile)
        self.manifest.write_text(self.manifest.read_text()+' ')
        with self.assertRaises(ValueError):teacher.validate_vllm_model_profile(self.profile,profile_digest,full=True)


if __name__=='__main__':unittest.main()
