"""Public-evidence compilation contracts; no model or world is executed."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'research/agent_frontier_portfolio_20261029')]
spec=importlib.util.spec_from_file_location('alf_experience_test',ROOT/'research/agent_frontier_portfolio_20261029/prepare_alfworld_experience_20261106.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)


class ExperienceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.pilot=self.root/'pilot';self.pilot.mkdir();self.source=self.root/'source';self.source.mkdir()
        (self.source/'responses').mkdir();self.output=self.pilot/'experiences/clean_1/v1'
        self.initial={'observation':'Your task is to: clean soap and put it on cart.','score':0.,'done':False,
                      'won':False,'action_count':0,'admissible_commands':['move soap 1 to cart 1']}
        self.final=dict(self.initial,observation='You move soap 1 to cart 1.',score=1.,done=True,won=True,action_count=1)
        self.action='move soap 1 to cart 1';self.tokens={'total':9,'input':8,'output':1,'cache':{'read':0}}
        self.contract={'pairs':[{'source':'clean_1','target':'clean_2'},{'source':'heat_1','target':'heat_2'}],
                       'pool_sha256':'b'*64,'source_model':'qwen38-27b-fp8','world_and_model_seed':17}
        self.save(self.pilot/'CONTRACT.json',self.contract)
        self.save(self.source/'initial_reset.json',self.initial);self.save(self.source/'opencode_config.json',{'public':'config'})
        (self.source/'task.txt').write_text('Source task. '+self.initial['observation'])
        self.manifest={'game_id':'clean_1','backend':'teacher27b','profile_sha256':e.PROFILE_SHA,
            'model_id':'qwen38-27b-fp8','seed':17,
            'game_sha256':'a'*64,'pool_binding':{'sha256':'b'*64},
            'components':{'/archived/not-current/run_alfworld_actor_20261106.py':'c'*64},
            'prompt_sha256':e.sha(self.source/'task.txt'),'initial_sha256':e.sha(self.source/'initial_reset.json'),
            'config_sha256':e.sha(self.source/'opencode_config.json')}
        self.trajectory=[{'event':'episode','game_id':'clean_1','asset_sha256':'a'*64,'pool_manifest_sha256':'b'*64,'seed':17},
                         {'event':'reset','state':self.initial},{'event':'step','action':self.action,'state':self.final}]
        self.raw=[{'type':'tool_use','part':{'tool':'bash','state':{'status':'completed',
            'input':{'command':"python /world/client.py step --action '"+self.action+"'"},'output':json.dumps(self.final)+'\n'}}},
            {'type':'step_finish','part':{'tokens':self.tokens}},
            {'type':'text','part':{'text':'Observed terminal won=true.'}}]
        body=self.source/'responses/00001.body';body.write_bytes(b'data: public recorded response\n\n')
        self.response={'status':200,'complete':True,'body_sha256':e.sha(body),'body_bytes':body.stat().st_size,
                       'usage':{'total_tokens':9}}
        self.save(self.source/'responses/00001.body.receipt.json',self.response)
        self.receipt={'manifest_sha256':'','status':'RETURNED','docker_exit':0,'final_world_state':self.final,
                      'won':True,'world_actions':1,'forwarded_model_posts':1,'response_receipts':[self.response],
                      'raw_step_tokens_separate_not_added':[self.tokens]}
        self.receipts={};self.resync()
        self.patch('PILOT',self.pilot);self.patch('CONTRACT_SHA',e.sha(self.pilot/'CONTRACT.json'))
        self.patch('SOURCES_SHA',e.sha(self.pilot/'SOURCES.json'));self.patch('RECEIPTS',self.receipts)
        self.budget={'context_tokens':32768,'writer_prompt_tokens':100,'max_output_tokens':2500,
                     'safety_margin_tokens':512,'remaining_tokens':29656,'artifact_tokens':{e.HISTORY:90,e.SUMMARY:20}}
        self.patch('token_budget',mock.Mock(return_value=self.budget))

    def save(self,path,obj):path.write_text(json.dumps(obj),encoding='utf8')
    def patch(self,name,value):
        p=mock.patch.object(e,name,value);p.start();self.addCleanup(p.stop)
    def resync(self):
        self.save(self.source/'manifest.json',self.manifest)
        self.receipt['manifest_sha256']=e.sha(self.source/'manifest.json')
        self.save(self.source/'receipt.json',self.receipt);self.receipts['clean_1']=e.sha(self.source/'receipt.json')
        for name,rows in [('execute_world.jsonl',self.trajectory),('raw.jsonl',self.raw)]:
            (self.source/name).write_text(''.join(json.dumps(r)+'\n' for r in rows))
        self.save(self.pilot/'SOURCES.json',{'contract_sha256':e.sha(self.pilot/'CONTRACT.json'),
            'source_roles_fixed_before_generation':True,'sources':[{'game_id':'clean_1','root':str(self.source),
            'manifest_sha256':e.sha(self.source/'manifest.json')}]})
        if hasattr(self,'budget'):e.SOURCES_SHA=e.sha(self.pilot/'SOURCES.json')

    def generate(self,content='Match the current goal and verify real feedback.',usage=None,finish='stop'):
        response={'choices':[{'finish_reason':finish,'message':{'content':content,'reasoning':'not final'}}],'usage':usage}
        chunks=iter([json.dumps(response).encode(),b'']);connection=mock.Mock()
        connection.getresponse.return_value=SimpleNamespace(status=200,length=None,read=lambda n:next(chunks))
        with mock.patch.object(e.teacher,'validate_vllm_model_profile',return_value={'host':'127.0.0.1','port':8006}), \
             mock.patch.object(e.teacher,'verify_vllm_backend',return_value={}), \
             mock.patch.object(e.http.client,'HTTPConnection',return_value=connection):
            if content and finish=='stop':e.generate_skill(self.output)
            else:
                with self.assertRaises(ValueError):e.generate_skill(self.output)
        return connection

    def test_history_keeps_public_text_tool_error_and_actual_world_binding(self):
        self.raw.insert(0,{'type':'tool_use','part':{'tool':'bash','state':{'status':'error','input':{'command':'invalid'},
                            'output':'partial diagnostic','error':'PermissionDenied: actual error'}}})
        self.resync();manifest=e.draft('clean_1',self.output)
        text=(self.output/(e.HISTORY+'.md')).read_text();rows=json.loads(e.decode_field(text,'PUBLIC_EVENTS'))
        self.assertEqual(rows[0]['status'],'error');self.assertEqual(rows[0]['error'],'PermissionDenied: actual error')
        self.assertEqual(rows[0]['output'],'partial diagnostic');self.assertEqual(rows[-1]['text'],'Observed terminal won=true.')
        self.assertEqual(manifest['source']['trajectory_sha256'],e.sha(self.source/'execute_world.jsonl'))
        self.assertIn(self.action,(self.output/(e.SUMMARY+'.md')).read_text());self.assertIn(e.GUARD,(self.output/(e.SUMMARY+'.md')).read_text())
        self.assertEqual(manifest['source']['archived_component_sha256'],self.manifest['components'])

    def test_source_failure_and_unknown_provider_usage_are_not_promoted_or_zeroed(self):
        self.final.update(won=False,score=0.);self.receipt['won']=False
        self.raw[0]['part']['state']['output']=json.dumps(self.final)+'\n'
        self.response['usage']=None;self.save(self.source/'responses/00001.body.receipt.json',self.response)
        self.resync();manifest=e.draft('clean_1',self.output)
        evidence=e.load_source('clean_1')
        self.assertIs(manifest['source']['won'],False)
        self.assertIsNone(evidence['outcome']['cost']['provider_tokens_known'])
        self.assertEqual(evidence['outcome']['cost']['unknown_usage_model_posts'],1)
        self.assertFalse(evidence['outcome']['cost']['usage_complete'])
        self.assertIn('won=false',(self.output/(e.SUMMARY+'.md')).read_text())

    def test_target_or_wrong_archived_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'source must'):e.load_source('clean_2')
        self.manifest['game_id']='heat_1';self.resync()
        with self.assertRaisesRegex(ValueError,'wrong archived source'):e.load_source('clean_1')

    def test_writer_input_contains_only_source_public_evidence(self):
        e.draft('clean_1',self.output);text=(self.output/(e.HISTORY+'.md')).read_text();payload=e.skill_payload(text)
        encoded=json.dumps(payload)
        self.assertNotIn(str(self.source),encoded);self.assertNotIn('pool_binding',encoded)
        self.assertNotIn('clean_2',encoded);self.assertNotIn('pddl_problem',encoded)
        self.assertEqual(payload['chat_template_kwargs'],{'enable_thinking':False});self.assertEqual(payload['max_tokens'],2500)
        self.assertFalse(payload['stream'])
        with self.assertRaises(ValueError):e.public_screen(text+' pddl_problem: hidden',self.contract)
        with self.assertRaises(ValueError):e.public_screen(text+' heat_2',self.contract)

    def test_one_reserved_writer_call_retains_usage_none_and_never_retries(self):
        e.draft('clean_1',self.output);connection=self.generate(usage=None)
        self.assertEqual(connection.request.call_count,1)
        self.assertEqual(connection.request.call_args.args,('POST','/v1/chat/completions'))
        self.assertIsNone(e.read(self.output/'skill_ledger.json')['usage'])
        with self.assertRaises(FileExistsError):e.generate_skill(self.output)
        self.assertTrue((self.output/'skill_response.json').exists())

    def test_reasoning_only_output_retains_failure_and_cannot_freeze(self):
        e.draft('clean_1',self.output);connection=self.generate(content='',usage={'total_tokens':20})
        self.assertEqual(connection.request.call_count,1)
        ledger=e.read(self.output/'skill_ledger.json');self.assertEqual(ledger['physical_http_attempts'],1)
        self.assertEqual(ledger['usage'],{'total_tokens':20});self.assertIn('FAILED',ledger['status'])
        self.assertFalse((self.output/(e.SKILL+'.md')).exists());self.assertTrue((self.output/'skill_response.json').exists())
        with self.assertRaises((ValueError,FileNotFoundError)):e.freeze(self.output)

    def test_frozen_interface_validates_after_target_start_and_rejects_tampering(self):
        e.draft('clean_1',self.output);self.generate();manifest=e.freeze(self.output);path=self.output/'frozen_manifest.json';digest=e.sha(path)
        loaded=e.validate_frozen(path,digest);self.assertEqual(set(loaded),{'manifest','texts','binding'})
        self.assertEqual(set(loaded['texts']),set(e.CONDITIONS));self.assertEqual(loaded['binding']['source_game_id'],'clean_1')
        target=self.pilot/'target_attempts/clean_2/student8b/none/attempt_v1';target.mkdir(parents=True)
        (target/'reservation.json').write_text('{}')
        self.assertEqual(e.validate_frozen(path,digest)['manifest'],manifest)
        with self.assertRaisesRegex(ValueError,'compilation is closed'):e.freeze(self.output)
        carrier=self.output/(e.HISTORY+'.md');original=carrier.read_bytes();carrier.write_bytes(original+b'changed')
        with self.assertRaises(ValueError):e.validate_frozen(path,digest)
        carrier.write_bytes(original);raw=self.source/'raw.jsonl';raw.write_text(raw.read_text()+'{"type":"text","part":{"text":"changed"}}\n')
        with self.assertRaises(ValueError):e.validate_frozen(path,digest)

    def test_native_token_limit_is_checked_before_any_draft_or_request_write(self):
        # Tiny bytes can be many native tokens: a byte-only gate would miss this.
        tokenizer=SimpleNamespace(apply_chat_template=lambda *a,**k:'native prompt',encode=lambda text,**k:list(range(30000)))
        identity={'context_tokens':32768}
        with mock.patch.object(e,'token_budget',side_effect=original_token_budget), \
             mock.patch.object(e,'local_tokenizer',return_value=(tokenizer,'template',identity)), \
             mock.patch.object(e.http.client,'HTTPConnection') as http:
            with self.assertRaisesRegex(ValueError,'token count exceeds'):e.draft('clean_1',self.output)
            self.assertFalse(self.output.exists());http.assert_not_called()

    def test_raw_world_state_mismatch_and_response_bytes_tamper_are_rejected(self):
        self.raw[0]['part']['state']['output']=json.dumps(dict(self.final,won=False))+'\n';self.resync()
        with self.assertRaisesRegex(ValueError,'raw tool returns'):e.load_source('clean_1')
        self.raw[0]['part']['state']['output']=json.dumps(self.final)+'\n';self.resync()
        (self.source/'responses/00001.body').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'response archive'):e.load_source('clean_1')


original_token_budget=e.token_budget
if __name__=='__main__':unittest.main()
