"""Offline source authorization/replay contracts, with no world or model calls."""
import copy
from contextlib import ExitStack
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('recovery_source_tests', REPO/'research/agent_frontier_portfolio_20261029/alfworld_recovery_source.py')
m = importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding='utf8')


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve();self.case = 'CPU_CASE'
        self.root = self.base/'cases'/self.case/'ordinary_reset/student8b/attempt_v2'
        self.root.mkdir(parents=True)
        self.state = lambda n: dict(observation='public',score=0.0,done=False,won=False,action_count=n,admissible_commands=['look'])
        self.runtime = {'process':{'pid':12,'start_ticks':'123','argv':['CPU_FAKE'],'cwd':'/cpu','exe':'/cpu'},'active_lora':None}
        self.manifest = dict(case_id=self.case,stage='ordinary_reset',backend='student8b',model_seed=17,world_seed=17,
            protocol_sha256='',protocol_path=str(self.base/'old.json'),pool_binding={'sha256':m.POOL_SHA},
            caps=dict(posts=128,seconds=1800,world_actions=100,model_payload_bytes_combined=64000000),world_step_cap=100,game={'sha256_game':'game'},
            inputs_sha256={'initial_reset.json':''},runtime_profile_override={'profile':{'variant':'frozen','gguf_sha256':m.PARENT_SHA},'runtime_admission':self.runtime})
        self.receipt = dict(status='RETURNED',label='MULTITASK_CONTEXT_DEVELOPMENT',manifest_sha256='',real_model_calls=128,
            forwarded_model_posts=128,model_posts=128,unknown_usage_model_posts=0,won=False,errors=[],
            model_request_payload_bytes=123,model_response_wire_bytes=456,elapsed_seconds=500,
            final_world_state=self.state(2),world_actions=2,total_world_action_count=2)
        self.events = [dict(event='episode',game_id=self.case,seed=17,step_cap=100,asset_sha256='game',pool_manifest_sha256=m.POOL_SHA,bridge_sha256=m.BRIDGE_SHA),
                       dict(event='reset',state=self.state(0)),dict(event='step',action='look',state=self.state(1)),dict(event='step',action='look',state=self.state(2))]
        self.old = self.base/'old.json';self.cohort = self.base/'cohort.json';self.new = self.base/'new.json'
        write(self.old,{'case_ids':[self.case]+['CPU_%d'%i for i in range(15)],'pool_sha256':m.POOL_SHA,'total_caps':self.manifest['caps']})
        self.protocol = dict(schema='ALFWORLD_ADDITIONAL_RECOVERY_V1',allow_frozen_ordinary_reset_sources=True,
            source_protocol={'path':str(self.old),'sha256':m.sha(self.old)},source_cohort={'path':str(self.cohort),'sha256':''},
            source_bindings={},additional_caps=m.ADDITIONAL_CAPS.copy(),world_step_cap=100)
        self.stack = self.enterContext(ExitStack())
        self.stack.enter_context(patch.object(m,'ROOT',self.base))
        self.stack.enter_context(patch.object(m,'SOURCE_PROTOCOL_SHA',m.sha(self.old)))
        self.stack.enter_context(patch.object(m,'SOURCE_COHORT_SHA',m.SOURCE_COHORT_SHA))
        self.stack.enter_context(patch('socket.create_connection',side_effect=AssertionError('offline only')))
        self.save()

    def save(self):
        write(self.root/'initial_reset.json',self.state(0))
        self.manifest['protocol_sha256']=m.SOURCE_PROTOCOL_SHA
        self.manifest['inputs_sha256']['initial_reset.json']=m.sha(self.root/'initial_reset.json')
        write(self.root/'manifest.json',self.manifest)
        self.receipt['manifest_sha256']=m.sha(self.root/'manifest.json');write(self.root/'receipt.json',self.receipt)
        write(self.root/'reservation.json',{'mode':'REAL_DEVELOPMENT','manifest_sha256':m.sha(self.root/'manifest.json'),'runtime_identity':self.runtime['process']})
        (self.root/'execute_world.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in self.events),encoding='utf8')
        rows=[dict(case=c,arm='frozen',status='RECORDED',root=str(self.root),won=False,receipt_sha256=m.sha(self.root/'receipt.json')) for c in json.loads(self.old.read_text())['case_ids']]
        write(self.cohort,{'cases':rows});m.SOURCE_COHORT_SHA=m.sha(self.cohort)
        self.protocol['source_cohort']['sha256']=m.SOURCE_COHORT_SHA
        self.protocol['source_bindings'][self.case]=dict(root=str(self.root),**{key:m.sha(self.root/name) for key,name in (
            ('manifest_sha256','manifest.json'),('receipt_sha256','receipt.json'),('execute_world_sha256','execute_world.jsonl'),('reservation_sha256','reservation.json'))})
        write(self.new,self.protocol)

    def load(self):return m.load_source(self.new,m.sha(self.new),self.case)

    def test_full_old_budget_is_unchanged_and_new_phase_is_additional(self):
        source=self.load()
        self.assertEqual(source['receipt']['model_posts'],128)
        self.assertEqual(source['manifest']['stage'],'ordinary_reset')
        self.assertEqual(source['additional_caps'],dict(m.ADDITIONAL_CAPS,world_actions=98))
        self.assertEqual(source['world_step_cap'],100)
        self.assertIn('NOT_OLD_REMAINING',source['budget_semantics'])
        expected=hashlib.sha256(json.dumps([source['reset'],source['steps']],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        self.assertEqual(source['public_prefix_sha256'],expected)

    def test_tampering_or_missing_allow_is_rejected(self):
        (self.root/'execute_world.jsonl').write_text('changed')
        with self.assertRaises(ValueError):self.load()
        self.save();self.protocol['allow_frozen_ordinary_reset_sources']=False;write(self.new,self.protocol)
        with self.assertRaises(ValueError):self.load()
        self.protocol['allow_frozen_ordinary_reset_sources']=True;self.protocol['additional_caps']['posts']=96;write(self.new,self.protocol)
        with self.assertRaises(ValueError):self.load()

    def test_zero_actions_terminal_duplicate_and_budget_exhausted_world_rejected(self):
        original=copy.deepcopy(self.events)
        variants=[original[:2],original+[copy.deepcopy(original[-1])],original[:2]+[dict(event='step',action='look',state=dict(self.state(1),won=True,done=True)),original[-1]]]
        for events in variants:
            self.events=events;self.save()
            with self.subTest(events=events),self.assertRaises(ValueError):self.load()
        self.events=original;self.receipt['model_request_payload_bytes']=-1;self.save()
        with self.assertRaises(ValueError):self.load()
        self.receipt['model_request_payload_bytes']=123;self.receipt['model_posts']=129;self.save()
        with self.assertRaisesRegex(ValueError,'historical formation cost'):self.load()
        self.receipt['model_posts']=128;self.events=original[:2]+[dict(event='step',action='look',state=self.state(i)) for i in range(1,101)]
        self.receipt.update(final_world_state=self.state(100),world_actions=100,total_world_action_count=100);self.save()
        with self.assertRaises(ValueError):self.load()

    def test_fake_teacher_or_adapter_source_rejected(self):
        self.manifest['backend']='teacher27b';self.save()
        with self.assertRaises(ValueError):self.load()
        self.manifest['backend']='student8b';self.manifest['runtime_profile_override']['profile']['variant']='ordinary';self.save()
        with self.assertRaises(ValueError):self.load()
        self.manifest['runtime_profile_override']['profile']['variant']='frozen';self.receipt['real_model_calls']=0;self.save()
        with self.assertRaises(ValueError):self.load()
        self.receipt['real_model_calls']=128;self.receipt['status']='FAILED';self.save()
        with self.assertRaises(ValueError):self.load()


@unittest.skipUnless((m.ROOT/'alfworld_text_qualification_20261106/context_study_v1/learning_comparison_v1/hf_evaluation_v1/RUN_v2/RESULT.json').is_file(),'GB10 closed-source fixture')
class ActualClosedSourceTests(unittest.TestCase):
    def test_actual_frozen_failure_is_replay_compatible_without_running_world(self):
        base=m.ROOT/'alfworld_text_qualification_20261106/context_study_v1/learning_comparison_v1/hf_evaluation_v1'
        rows=json.loads((base/'RUN_v2/RESULT.json').read_text(encoding='utf8'))['cases']
        eligible={'heldout1_clean_02', 'heldout1_look_04', 'heldout1_clean_03', 'heldout1_clean_04',
                  'heldout1_heat_01', 'heldout1_heat_03', 'heldout1_heat_04', 'heldout1_cool_04'}
        with tempfile.TemporaryDirectory(prefix='offline_source_test_',dir=m.ROOT) as tmp:
            path=Path(tmp)/'CPU_PROTOCOL.json'
            bindings={}
            for row in rows:
                root=Path(row['root'])
                bindings[row['case']]=dict(root=str(root),**{
                    key:m.sha(root/name) for key,name in [('manifest_sha256','manifest.json'),
                    ('receipt_sha256','receipt.json'),('execute_world_sha256','execute_world.jsonl'),
                    ('reservation_sha256','reservation.json')]})
            q=dict(schema='ALFWORLD_ADDITIONAL_RECOVERY_V1',allow_frozen_ordinary_reset_sources=True,
                source_protocol={'path':str(base/'PROTOCOL.json'),'sha256':m.SOURCE_PROTOCOL_SHA},
                source_cohort={'path':str(base/'RUN_v2/RESULT.json'),'sha256':m.SOURCE_COHORT_SHA},
                additional_caps=m.ADDITIONAL_CAPS,world_step_cap=100,source_bindings=bindings)
            write(path,q)
            for row in rows:
                with self.subTest(case=row['case']):
                    if row['case'] not in eligible:
                        with self.assertRaises(ValueError):m.load_source(path,m.sha(path),row['case'])
                        continue
                    prefix=m.load_source(path,m.sha(path),row['case'])
                    original=json.loads((Path(row['root'])/'receipt.json').read_text(encoding='utf8'))
                    self.assertEqual(prefix['receipt'],original)
                    self.assertEqual(len(prefix['steps']),original['world_actions'])
                    self.assertEqual(prefix['additional_caps']['world_actions']+len(prefix['steps']),100)
                    self.assertEqual(prefix['additional_caps']['posts'],32)
                    self.assertEqual(prefix['steps'][-1]['state'],original['final_world_state'])


if __name__=='__main__':unittest.main()
