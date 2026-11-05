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


if __name__=='__main__':unittest.main()
