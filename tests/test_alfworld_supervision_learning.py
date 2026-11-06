"""CPU-only plan/integrity and small tensor causal-shift controls. No real training."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];PATH=ROOT/'research/agent_frontier_portfolio_20261029/alfworld_supervision_learning.py'
spec=importlib.util.spec_from_file_location('learning_tested',PATH);x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value),encoding='utf8')

def row(identity,group,eos=151645):return {'input_ids':[1,2,3,4,eos,10],'attention_mask':[1]*6,'labels':[-100,-100,3,4,eos,-100],'prompt_token_count':2,'assistant_end_index':4,'supervised_tokens':3,'sequence_length':6,'prefix_token_alignment_verified':True,'source_role':'teacher','source_group':group,'row_id':identity}

class PlanTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name).resolve();self.model=self.base/'model';self.model.mkdir();write(self.model/'config.json',dict(model_type='qwen3',architectures=['Qwen3ForCausalLM'],hidden_size=4096,num_hidden_layers=36,vocab_size=151936));write(self.model/'tokenizer_config.json',{'chat_template':'MOCK'});write(self.model/'tokenizer.json',{'MOCK':True});self.assets={'model_path':str(self.model),'files_sha256':{name:x.sha(self.model/name) for name in ['config.json','tokenizer_config.json','tokenizer.json']},'enable_thinking':False,'eos_token_id':151645};self.rows=[row('a1','gA'),row('a2','gA'),row('b1','gB'),row('b2','gB'),row('b3','gB')];self.source=self.base/'tokens';self.source.mkdir();self.rowfile=self.source/'rows.jsonl';self.rowfile.write_bytes(b''.join(json.dumps(r).encode()+b'\n' for r in self.rows));write(self.source/'exclusions.json',[]);write(self.source/'formation_ledger.json',{'source_fee_once':True});self.data={'schema':'alfworld_current_assistant_token_candidates_v1','qualification_mode':'LOCAL_HF_TOKENIZER_CPU','long_rows_truncated':False,'compiler_sha256':x.sha(x.TOKENS),'tokenizer':self.assets,'max_length':32768,'compiled_rows':len(self.rows),'output_sha256':{n:x.sha(self.source/n) for n in ['rows.jsonl','exclusions.json','formation_ledger.json']},'source_export':{'path':str(self.base/'unused_source.json'),'sha256':'a'*64}};self.manifest=self.source/'data_manifest.json';write(self.manifest,self.data);self.attempt=self.base/'supervision_learning_v1/recovery/attempt_v1'
        rebuilt={'rows':copy.deepcopy(self.rows),'exclusions':[],'formation_ledger':{'source_fee_once':True}};self.fake=types.SimpleNamespace(compile_export=lambda *a,**kw:copy.deepcopy(rebuilt));self.mock=patch.object(x,'module',return_value=self.fake);self.mock.start();self.addCleanup(self.mock.stop);self.version=patch.object(x.importlib.metadata,'version',return_value='MOCK_VERSION');self.version.start();self.addCleanup(self.version.stop)
    def prepare(self,**kw):return x.prepare(self.attempt,self.manifest,x.sha(self.manifest),['gA','gB'],updates=kw.pop('updates',12),study_root=self.base,**kw)
    def rebound_rows(self,rows):
        self.rowfile.write_bytes(b''.join(json.dumps(r).encode()+b'\n' for r in rows));self.data['output_sha256']['rows.jsonl']=x.sha(self.rowfile);write(self.manifest,self.data)
    def model_binding(self):
        shard=self.model/'model-00001-of-00001.safetensors';shard.write_bytes(b'MOCK_NOT_MODEL_WEIGHTS');write(self.model/'model.safetensors.index.json',{'weight_map':{'fake.parameter':shard.name}});paths=list(self.model.iterdir());binding={'model_dir':str(self.model),'files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':x.sha(p)} for p in paths]};path=self.base/'binding.json';write(path,binding);return path
    def test_plan_balances_groups_and_covers_every_row_before_repeat(self):
        a=x.schedule_rows(self.rows,['gB','gA'],12);b=x.schedule_rows(self.rows,['gA','gB'],12);self.assertEqual(a,b);self.assertEqual({r['row_id'] for r in a},{r['row_id'] for r in self.rows});self.assertEqual(sum(r['source_group']=='gA' for r in a),6);self.assertEqual(sum(r['source_group']=='gB' for r in a),6)
        for group,count in [('gA',2),('gB',3)]:self.assertEqual(len({r['row_id'] for r in a if r['source_group']==group and r['group_permutation_epoch']==1}),count)
    def test_prepare_and_verify_without_weight_binding_or_resource_probe(self):
        r=self.prepare();root,plan,rows=x.verify_plan(self.attempt,r['manifest_sha256'],study_root=self.base);self.assertEqual(plan['scheduled_input_tokens'],72);self.assertEqual(plan['scheduled_supervised_tokens'],36);self.assertEqual(plan['unique_rows_scheduled'],5);self.assertEqual(len(rows),5);self.assertFalse((self.attempt/'reservation.json').exists());self.assertFalse((self.model/'model.safetensors.index.json').exists());self.assertEqual(plan['config']['lora_dropout'],0.0);self.assertIsNone(plan['config']['parent_adapter'])
    def test_duplicate_unknown_group_and_invalid_updates_rejected(self):
        for groups,updates in [([],12),(['gA','gA'],12),(['missing'],12),(['gA'],193),(['gA'],True)]:
            with self.subTest(groups=groups,updates=updates),self.assertRaises(x.IntegrityError):x.schedule_rows(self.rows,groups,updates)
    def test_rows_hash_tampering_rejected(self):
        self.rowfile.write_bytes(self.rowfile.read_bytes()+b' ')
        with self.assertRaisesRegex(x.IntegrityError,'hash'):self.prepare()
    def test_rebound_target_mask_still_rejected_by_actual_recompiler(self):
        rows=copy.deepcopy(self.rows);rows[0]['labels'][1]=2;self.rebound_rows(rows)
        with self.assertRaisesRegex(x.IntegrityError,'actual evidence'):self.prepare()
    def test_training_plan_schedule_tamper_rejected(self):
        r=self.prepare();plan=x.read(self.attempt/'manifest.json');plan['schedule'][0]['row_id']='b1';write(self.attempt/'manifest.json',plan)
        with self.assertRaisesRegex(x.IntegrityError,'plan/config'):x.verify_plan(self.attempt,x.sha(self.attempt/'manifest.json'),study_root=self.base)
    def test_parent_adapter_rejected_before_any_weights(self):
        write(self.model/'adapter_config.json',{'peft_type':'LORA'})
        with self.assertRaisesRegex(x.IntegrityError,'parent adapter'):self.prepare()
    def test_full_model_binding_hashes_and_shards(self):
        self.prepare();plan=x.read(self.attempt/'manifest.json');path=self.model_binding();x.validate_model_binding(path,x.sha(path),plan);binding=x.read(path);binding['files']=[r for r in binding['files'] if not r['path'].endswith('.safetensors')];write(path,binding)
        with self.assertRaisesRegex(x.IntegrityError,'weight shards'):x.validate_model_binding(path,x.sha(path),plan)
    def test_unbound_effective_weight_file_rejected(self):
        self.prepare();plan=x.read(self.attempt/'manifest.json');path=self.model_binding();(self.model/'model.safetensors').write_bytes(b'UNBOUND')
        with self.assertRaisesRegex(x.IntegrityError,'effective'):x.validate_model_binding(path,x.sha(path),plan)
    def test_binding_weight_tampering_rejected(self):
        self.prepare();path=self.model_binding();(self.model/'model-00001-of-00001.safetensors').write_bytes(b'ALTERED')
        with self.assertRaises(x.IntegrityError):x.validate_model_binding(path,x.sha(path),x.read(self.attempt/'manifest.json'))
    def test_owned_window_is_not_global_GPU_exclusivity(self):
        grant={'status':'OWNED_RESEARCH_WINDOW_GRANTED','exclusive_research_job':True,'gpu_exclusive':False,'lease_scope':'context_study_v1_and_owned_18104','cuda_device':0,'allowed_plan_sha256':['a'*64,'b'*64]};p=self.base/'window.json';write(p,grant);self.assertFalse(x.validate_window(p,x.sha(p),'b'*64,str(self.model))['gpu_exclusive']);grant['gpu_exclusive']=True;write(p,grant)
        with self.assertRaisesRegex(x.IntegrityError,'window grant'):x.validate_window(p,x.sha(p),'b'*64,str(self.model))
    def test_window_must_bind_plan(self):
        p=self.base/'window.json';write(p,{'status':'OWNED_RESEARCH_WINDOW_GRANTED','exclusive_research_job':True,'gpu_exclusive':False,'lease_scope':'context_study_v1_and_owned_18104','cuda_device':0,'plan_sha256':'a'*64})
        with self.assertRaises(x.IntegrityError):x.validate_window(p,x.sha(p),'b'*64,str(self.model))
    def test_frozen_rows_EOS_shift_and_trailing_template_masks(self):
        good=row('r','g');self.assertEqual(x.validate_row(good,151645,100,151936),[2,3,4])
        for position in [0,1,5]:
            bad=copy.deepcopy(good);bad['labels'][position]=bad['input_ids'][position]
            with self.subTest(position=position),self.assertRaises(x.IntegrityError):x.validate_row(bad,151645,100,151936)
        bad=copy.deepcopy(good);bad['input_ids'][4]=8;bad['labels'][4]=8
        with self.assertRaisesRegex(x.IntegrityError,'EOS'):x.validate_row(bad,151645,100,151936)
    def test_comparison_plan_namespace_and_optional_binding_reference(self):
        binding=self.model_binding();self.attempt=self.base/'learning_comparison_v1/plans/recovery_v1';r=x.prepare(self.attempt,self.manifest,x.sha(self.manifest),['gA','gB'],updates=12,model_binding=binding,model_binding_sha=x.sha(binding),study_root=self.base);_,plan,_=x.verify_plan(self.attempt,r['manifest_sha256'],study_root=self.base);self.assertEqual(plan['model_binding_reference']['sha256'],x.sha(binding));self.assertFalse(plan['full_weight_hashes_checked_during_CPU_plan'])
    def test_simulated_OOM_one_attempt_failed_receipt_and_no_retry(self):
        self.prepare();plan=x.read(self.attempt/'manifest.json');calls=[]
        class FakeOOM(RuntimeError):pass
        def fail_load(*args,**kwargs):calls.append(kwargs);raise FakeOOM('MOCK OOM; no real GPU/model')
        cuda=types.SimpleNamespace(reset_peak_memory_stats=lambda *a:None,mem_get_info=lambda *a:(0,0),is_initialized=lambda:False)
        torch=types.SimpleNamespace(cuda=cuda,bfloat16='MOCK_BF16',OutOfMemoryError=FakeOOM);peft=types.SimpleNamespace(LoraConfig=lambda **k:None,get_peft_model=lambda *a:None);transformers=types.SimpleNamespace(AutoModelForCausalLM=types.SimpleNamespace(from_pretrained=fail_load),set_seed=lambda seed:None)
        with patch.object(x,'verify_plan',return_value=(self.attempt,plan,{})),patch.object(x,'validate_window',return_value={}),patch.object(x,'validate_model_binding',return_value={}),patch.dict(sys.modules,{'torch':torch,'peft':peft,'transformers':transformers}):
            receipt=x.run(self.attempt,'a'*64,self.base/'binding','b'*64,self.base/'window','c'*64,study_root=self.base)
        self.assertEqual(len(calls),1);self.assertEqual(receipt['status'],'FAILED');self.assertTrue(receipt['oom']);self.assertFalse(receipt['retry_performed']);self.assertEqual(receipt['optimizer_updates_completed'],0);self.assertTrue((self.attempt/'receipt.json').exists());self.assertTrue((self.attempt/'reservation.json').exists())
        with self.assertRaisesRegex(FileExistsError,'never rerun'):x.run(self.attempt,'a'*64,self.base/'binding','b'*64,self.base/'window','c'*64,study_root=self.base)
    def test_AcceleratorError_CUDA_oom_message_is_not_false_non_OOM(self):
        self.prepare();plan=x.read(self.attempt/'manifest.json');calls=[]
        class AcceleratorError(RuntimeError):pass
        class TypedOOM(RuntimeError):pass
        def fail_mem(*args):raise AcceleratorError('CUDA error: out of memory')
        def must_not_load(*args,**kwargs):calls.append(kwargs);raise AssertionError('weight load should not start')
        cuda=types.SimpleNamespace(reset_peak_memory_stats=lambda *a:None,mem_get_info=fail_mem,is_initialized=lambda:False);torch=types.SimpleNamespace(cuda=cuda,bfloat16='MOCK',OutOfMemoryError=TypedOOM);peft=types.SimpleNamespace(LoraConfig=lambda **k:None,get_peft_model=lambda *a:None);transformers=types.SimpleNamespace(AutoModelForCausalLM=types.SimpleNamespace(from_pretrained=must_not_load),set_seed=lambda seed:None)
        with patch.object(x,'verify_plan',return_value=(self.attempt,plan,{})),patch.object(x,'validate_window',return_value={}),patch.object(x,'validate_model_binding',return_value={}),patch.dict(sys.modules,{'torch':torch,'peft':peft,'transformers':transformers}):
            receipt=x.run(self.attempt,'a'*64,self.base/'binding','b'*64,self.base/'window','c'*64,study_root=self.base)
        self.assertEqual(receipt['status'],'FAILED');self.assertEqual(receipt['error'],{'type':'AcceleratorError','message':'CUDA error: out of memory'});self.assertTrue(receipt['oom']);self.assertFalse(receipt['oom_evidence']['typed_torch_out_of_memory']);self.assertTrue(receipt['oom_evidence']['cuda_out_of_memory_message']);self.assertEqual(receipt['oom_evidence']['classification'],'cuda_oom_message_only');self.assertEqual(receipt['model_weight_loads_started'],0);self.assertEqual(calls,[]);self.assertFalse(receipt['retry_performed'])
    def test_no_OOM_evidence_is_unclassified_not_definitive_false(self):
        result=x.classify_oom(ValueError('MOCK unrelated failure'),types.SimpleNamespace(OutOfMemoryError=MemoryError));self.assertIsNone(result['oom']);self.assertEqual(result['classification'],'unclassified_no_oom_evidence')
    def test_import_has_no_torch_HF_CUDA_or_model_start(self):
        code="import importlib.util,sys;s=importlib.util.spec_from_file_location('m',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(any(x in sys.modules for x in ['torch','transformers','peft']))";done=subprocess.run([sys.executable,'-B','-c',code,str(PATH)],capture_output=True,text=True,check=True);self.assertEqual(done.stdout.strip(),'False')
    def test_prepare_refuses_existing_attempt(self):
        self.prepare()
        with self.assertRaises(FileExistsError):self.prepare()


class SparseTensorTests(unittest.TestCase):
    def test_actual_CPU_sparse_CE_equals_dense_value_and_every_gradient(self):
        try:import torch
        except ImportError:self.skipTest('local torch absent; GB10 CPU tensor control required')
        from torch.nn import functional as F
        class Tiny(torch.nn.Module):
            def __init__(self):super().__init__();self.logits=torch.nn.Parameter(torch.arange(6*17,dtype=torch.float32).reshape(1,6,17)/100);self.selector=None
            def forward(self,input_ids,attention_mask,logits_to_keep=None,use_cache=False):
                self.selector=logits_to_keep
                return types.SimpleNamespace(logits=self.logits if logits_to_keep is None else self.logits[:,logits_to_keep,:])
        sparse=Tiny();dense=Tiny();r=row('small','g',eos=9);loss,_=x.sparse_causal(sparse,r,'cpu',eos=9,max_length=100,vocab_size=17);labels=torch.tensor([r['labels']]);out=dense(torch.tensor([r['input_ids']]),torch.tensor([r['attention_mask']]));reference=F.cross_entropy(out.logits[:,:-1,:].reshape(-1,17),labels[:,1:].reshape(-1),ignore_index=-100);torch.testing.assert_close(loss,reference,rtol=1e-7,atol=1e-7);loss.backward();reference.backward();torch.testing.assert_close(sparse.logits.grad,dense.logits.grad,rtol=1e-7,atol=1e-7);self.assertEqual(sparse.selector.tolist(),[1,2,3]);self.assertEqual(float(sparse.logits.grad[:,[0,4,5],:].abs().sum()),0.0);self.assertGreater(float(sparse.logits.grad[:,[1,2,3],:].abs().sum()),0.0)

if __name__=='__main__':unittest.main()
