"""Synthetic token boundaries plus frozen-evidence controls. No HF download/model."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
x=load('tokens_tested',ROOT/'research/agent_frontier_portfolio_20261029/alfworld_supervision_tokens.py')
fixtures=load('existing_supervision_fixture',ROOT/'tests/test_alfworld_recovery_supervision.py')

class FakeTokenizer:
    chat_template='INJECTED TEST TOKENIZER NOT HF';eos_token_id=999999;pad_token_id=0
    def __init__(self,mode=None):self.mode=mode;self.seen=[]
    def convert_tokens_to_ids(self,text):return self.eos_token_id if text=='<|im_end|>' else -1
    def decode(self,ids):return ''.join('<|im_end|>' if i==self.eos_token_id else chr(i) for i in ids)
    def apply_chat_template(self,messages,*,tools,tokenize,add_generation_prompt,**options):
        assert options==dict(enable_thinking=False,truncation=False,return_dict=False)
        self.seen.append(copy.deepcopy(messages))
        history=messages if add_generation_prompt else messages[:-1]
        prefix=json.dumps({'messages':history,'tools':tools},ensure_ascii=False)+x.QWEN_HEADER
        text=prefix
        if not add_generation_prompt:
            target=messages[-1];text+=target['content']+json.dumps(target['tool_calls'],ensure_ascii=False)
            if self.mode!='no_eos':text+='<|im_end|>'
            if self.mode=='double_eos':text+='<|im_end|>'
            text+='x' if self.mode=='after_eos' else '\n'
        if not tokenize:return text
        ids=[]
        while text:
            if text.startswith('<|im_end|>'):ids.append(self.eos_token_id);text=text[len('<|im_end|>'):]
            else:ids.append(ord(text[0]));text=text[1:]
        if not add_generation_prompt and self.mode=='boundary':ids[len(prefix)-1]+=1
        return ids


class TokenTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name).resolve();self.f=fixtures.Fixture(self.base);self.model=self.base/'model';self.model.mkdir();fixtures.write(self.model/'config.json',{'model_type':'qwen3','architectures':['Qwen3ForCausalLM']});fixtures.write(self.model/'tokenizer_config.json',{'chat_template':FakeTokenizer.chat_template});fixtures.write(self.model/'tokenizer.json',{'mock':True});self.out=self.base/'source_export';self.bundle=self.f.build();fixtures.x.export_supervision(self.bundle,self.out);self.manifest=self.out/'data_manifest.json';self.expected=x.sha(self.manifest)
    def compile(self,**kwargs):return x.compile_export(self.manifest,self.expected,self.model,tokenizer=kwargs.pop('tokenizer',FakeTokenizer()),study_root=self.base,**kwargs)
    def request_target(self):
        request=x.read(self.f.root/'requests/00001.json')['forwarded'];assistant,metadata=fixtures.x.native_assistant((self.f.root/'responses/00001.body').read_bytes());return request,assistant
    def rebind_rows(self,rows):
        (self.out/'trajectories.jsonl').write_bytes(b''.join(json.dumps(r).encode()+b'\n' for r in rows));m=x.read(self.manifest);m['output_sha256']['trajectories.jsonl']=x.sha(self.out/'trajectories.jsonl');fixtures.write(self.manifest,m);self.expected=x.sha(self.manifest)
    def test_actual_request_prefix_only_current_whole_completion_and_EOS(self):
        tok=FakeTokenizer();bundle=self.compile(tokenizer=tok);self.assertEqual(len(bundle['rows']),2);self.assertFalse(bundle['exclusions']);self.assertEqual(bundle['manifest']['qualification_mode'],'INJECTED_TEST_TOKENIZER')
        for row in bundle['rows']:
            n=row['prompt_token_count'];end=row['assistant_end_index'];self.assertEqual(row['labels'][:n],[-100]*n);self.assertEqual(row['labels'][n:end+1],row['input_ids'][n:end+1]);self.assertEqual(row['labels'][end],tok.eos_token_id);self.assertTrue(all(i==-100 for i in row['labels'][end+1:]));self.assertEqual(row['supervised_tokens'],end+1-n);decoded=tok.decode(row['labels'][n:end+1]);self.assertIn('Public plan before action.',decoded);self.assertIn('bash',decoded);self.assertEqual(decoded.count('<|im_end|>'),1)
        self.assertEqual(tok.seen[0],x.read(self.f.root/'requests/00001.json')['forwarded']['messages']);self.assertEqual(bundle['formation_ledger']['selected_recovery_real_calls'],4);self.assertEqual(bundle['manifest']['source_groups'],1);self.assertEqual(len(bundle['formation_ledger']['collector_sources_once']),1)
    def test_hash_tampering_export_manifest_rejected(self):
        with self.assertRaisesRegex(x.IntegrityError,'hash'):x.compile_export(self.manifest,'0'*64,self.model,tokenizer=FakeTokenizer(),study_root=self.base)
    def test_request_hash_tampering_rejected_before_tokenization(self):
        p=self.f.root/'requests/00001.json';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(ValueError):self.compile()
    def test_native_SSE_tampering_rejected(self):
        p=self.f.root/'responses/00001.body';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(ValueError):self.compile()
    def test_wrong_action_mask_cannot_be_promoted_even_after_export_rehash(self):
        rows=copy.deepcopy(self.bundle['trajectories']);bad=next(t for t in rows[0]['assistant_turn_metadata'] if t.get('client_error'));bad['supervised']=True;bad['fields']=['content','tool_calls'];rows[0]['supervised_assistant_turn_indices'].append(bad['message_index']);self.rebind_rows(rows)
        with self.assertRaisesRegex(x.IntegrityError,'masks/actions'):self.compile()
    def test_duplicate_turn_rejected_even_after_export_rehash(self):
        rows=copy.deepcopy(self.bundle['trajectories']);rows[0]['assistant_turn_metadata'].append(copy.deepcopy(rows[0]['assistant_turn_metadata'][0]));self.rebind_rows(rows)
        with self.assertRaisesRegex(x.IntegrityError,'rows/masks'):self.compile()
    def test_changed_exporter_hash_rejected(self):
        m=x.read(self.manifest);m['exporter_sha256']='0'*64;fixtures.write(self.manifest,m);self.expected=x.sha(self.manifest)
        with self.assertRaisesRegex(x.IntegrityError,'code hash'):self.compile()
    def test_long_context_explicit_exclusion_without_truncation(self):
        bundle=self.compile(max_length=10);self.assertEqual(bundle['rows'],[]);self.assertEqual(len(bundle['exclusions']),2);self.assertTrue(all(e['reason']=='length_exceeds_cap_no_truncation' for e in bundle['exclusions']));self.assertEqual(bundle['manifest']['action_candidates'],2);self.assertEqual(bundle['formation_ledger']['selected_recovery_real_calls'],4)
    def test_BPE_prefix_mismatch_explicit_diagnosis_no_silent_slice(self):
        req,target=self.request_target()
        with self.assertRaises(x.TokenExclusion) as caught:x.encode_completion(req,target,FakeTokenizer('boundary'),100000)
        self.assertEqual(caught.exception.reason,'generation_full_token_prefix_mismatch');self.assertTrue(caught.exception.details['rendered_text_prefix_equal']);self.assertIn('not applied automatically',caught.exception.details['possible_explicit_construction'])
    def test_EOS_missing_double_and_trailing_text_rejected(self):
        req,target=self.request_target()
        for mode in ['no_eos','double_eos','after_eos']:
            with self.subTest(mode=mode),self.assertRaises(x.TokenExclusion):x.encode_completion(req,target,FakeTokenizer(mode),100000)
    def test_reasoning_or_non_action_target_rejected(self):
        req,target=self.request_target()
        for bad in [{**target,'reasoning_content':'private'},{'role':'assistant','content':'done'}]:
            with self.subTest(target=bad),self.assertRaises(x.IntegrityError):x.encode_completion(req,bad,FakeTokenizer(),100000)
    def test_tool_not_exposed_rejected(self):
        req,target=self.request_target();req['tools']=[]
        with self.assertRaisesRegex(x.IntegrityError,'not exposed'):x.encode_completion(req,target,FakeTokenizer(),100000)
    def test_rows_not_direct_old_runner_input_and_output_refuses_overwrite(self):
        b=self.compile();out=self.base/'tokens';r=x.export_tokens(b,out);self.assertEqual(r['rows'],2);self.assertFalse(b['manifest']['old_single_completion_trainrunner_adapted']);self.assertEqual(len(x.read(out/'formation_ledger.json')['collector_sources_once']),1)
        with self.assertRaises(FileExistsError):x.export_tokens(b,out)
    def test_tokenizer_template_hash_and_model_type_bound(self):
        fixtures.write(self.model/'tokenizer_config.json',{'chat_template':'changed'})
        with self.assertRaisesRegex(x.IntegrityError,'Qwen3'):self.compile()
    def test_invalid_length_not_bool_or_zero(self):
        for value in [True,0,-1,1.0]:
            with self.subTest(value=value),self.assertRaises(x.IntegrityError):self.compile(max_length=value)
    def test_import_is_standard_library_and_no_tokenizer_model_startup(self):
        code="import importlib.util,sys; s=importlib.util.spec_from_file_location('offline',sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(any(x in sys.modules for x in ['torch','transformers','tokenizers']))"
        result=subprocess.run([sys.executable,'-B','-c',code,str(ROOT/'research/agent_frontier_portfolio_20261029/alfworld_supervision_tokens.py')],capture_output=True,text=True,check=True);self.assertEqual(result.stdout.strip(),'False')
    def test_ledger_tampering_even_rehashed_rejected(self):
        p=self.out/'ledger.json';ledger=x.read(p);ledger['selected_recovery_real_calls']=999;fixtures.write(p,ledger);m=x.read(self.manifest);m['output_sha256']['ledger.json']=x.sha(p);fixtures.write(self.manifest,m);self.expected=x.sha(self.manifest)
        with self.assertRaisesRegex(x.IntegrityError,'ledger'):self.compile()

if __name__=='__main__':unittest.main()
