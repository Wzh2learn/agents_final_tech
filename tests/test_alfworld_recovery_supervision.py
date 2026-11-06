"""Offline integrity/semantic boundary controls; no endpoint/model imports."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

MODULE=Path(__file__).resolve().parents[1]/'research/agent_frontier_portfolio_20261029/alfworld_recovery_supervision.py'
spec=importlib.util.spec_from_file_location('recovery_supervision_tested',MODULE)
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)


def write(path,value,lines=False):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(json.dumps(row)+'\n' for row in value) if lines else json.dumps(value))


def state(i,won=False):return dict(observation=f'public state {i}',score=int(won),done=won,won=won,action_count=i,admissible_commands=['look'])

def command(action):return "/runtime/bin/python -B /world/client.py step --socket /world/s --action '"+action+"'"

def assistant(cid,action):return {'role':'assistant','content':'Public plan before action.','tool_calls':[{'id':cid,'type':'function','function':{'name':'bash','arguments':json.dumps({'command':command(action)})}}]}


def sse(message,usage,reasoning='private reasoning excluded'):
    chunks=[]
    if message.get('tool_calls'):
        call=message['tool_calls'][0];args=call['function']['arguments'];mid=len(args)//2
        chunks=[{'choices':[{'index':0,'delta':{'role':'assistant','content':message['content'],'reasoning_content':reasoning,'tool_calls':[{'index':0,'id':call['id'],'type':'function','function':{'name':'bash','arguments':args[:mid]}}]},'finish_reason':None}]},
                {'choices':[{'index':0,'delta':{'tool_calls':[{'index':0,'function':{'arguments':args[mid:]}}]},'finish_reason':'tool_calls'}],'usage':usage}]
    else:chunks=[{'choices':[{'index':0,'delta':{'role':'assistant','content':message['content'],'reasoning_content':reasoning},'finish_reason':'stop'}],'usage':usage}]
    return ''.join('data: '+json.dumps(chunk)+'\n\n' for chunk in chunks)+'data: [DONE]\n\n'


class Fixture:
    def __init__(self,base):
        self.base=base;self.root=base/'cases/c1/drop_recent/teacher27b/attempt_v1';self.source=base/'cases/c1/collect/student8b/attempt_v1';self.batch=base/'batch/RESULT.json'
        self.pool_row=dict(id='c1',task_uid='task1',family='pick_heat',layout=21,layout_group='FloorPlan21',game_sha256='1'*64,traj_sha256='2'*64,game_member='a/game.tw-pddl',traj_member='a/traj_data.json')
        write(base/'pool/POOL.json',{'games':[self.pool_row]});write(base/'PROTOCOL.json',{'development_only':True,'total_caps':{'posts':128,'seconds':1800,'world_actions':100,'model_payload_bytes_combined':64000000}})
        source_world=[{'event':'reset','state':state(0)},{'event':'step','action':'go to table 1','state':state(1)}]
        write(self.source/'execute_world.jsonl',source_world,True)
        write(self.source/'manifest.json',{'pool_binding':self.pool_row})
        write(self.source/'receipt.json',dict(won=False,manifest_sha256=x.sha(self.source/'manifest.json'),provider_usage=dict(prompt_tokens=30,completion_tokens=5,total_tokens=35),real_model_calls=2))
        self.source_binding={str(self.source/name):x.sha(self.source/name) for name in ['manifest.json','receipt.json','execute_world.jsonl']}
        self.root.mkdir(parents=True)
        (self.root/'task.txt').write_bytes(b'Do the actual "goal".\n`public` previous history.');write(self.root/'opencode_config.json',{'tools':{'bash':True}})
        write(self.root/'initial_reset.json',state(0));write(self.root/'handoff_public.json',state(1))
        self.world=[{'event':'episode','game_id':'c1','asset_sha256':'1'*64,'seed':17},*source_world,{'event':'step','action':'look','state':state(2)},{'event':'step','action':'put item 1','state':state(3,True)}]
        write(self.root/'execute_world.jsonl',self.world,True);write(self.root/'execute_replay.jsonl',[{'equal':True,'actual':state(0)},{'equal':True,'actual':state(1)}],True)
        task=(self.root/'task.txt').read_text();self.messages=[{'role':'system','content':'Preserve actual system.'},{'role':'user','content':'"'+task.replace('"','\\"')+'"'}];self.tools=[{'type':'function','function':{'name':'bash','parameters':{'type':'object','properties':{'command':{'type':'string'}}}}}]
        self.raw=[];responses=[]
        completion=[assistant('a','look'),assistant('bad','take unknown'),assistant('b','put item 1'),{'role':'assistant','content':'The goal has succeeded.'}]
        for i,msg in enumerate(completion,1):
            request={'model':'teacher-model','temperature':0.6,'chat_template_kwargs':{'enable_thinking':False},'messages':copy.deepcopy(self.messages),'tools':self.tools}
            write(self.root/f'requests/{i:05}.json',{'incoming':request,'forwarded':request});write(self.root/f'template_checks/{i:05}.json',{'request_payload_sha256':x.object_sha(request)})
            usage=dict(prompt_tokens=10+i,completion_tokens=2,total_tokens=12+i);body=self.root/f'responses/{i:05}.body';body.parent.mkdir(exist_ok=True);body.write_text(sse(msg,usage))
            response=dict(status=200,complete=True,body_bytes=body.stat().st_size,body_sha256=x.sha(body),usage=usage);responses.append(response);write(Path(str(body)+'.receipt.json'),response)
            self.messages.append(msg)
            if msg.get('tool_calls'):
                call=msg['tool_calls'][0];cid=call['id'];result={'error':'invalid_action'} if cid=='bad' else state(2 if cid=='a' else 3,cid=='b');output='public client warning\n'+json.dumps(result)+'\n';exit_code=2 if cid=='bad' else 0
                part={'tool':'bash','callID':cid,'state':{'status':'completed','input':json.loads(call['function']['arguments']),'output':output,'metadata':{'exit':exit_code}}};self.raw.append({'type':'tool_use','part':part});self.messages.append({'role':'tool','tool_call_id':cid,'content':output})
        write(self.root/'raw_1.jsonl',self.raw,True)
        self.m=dict(case_id='c1',backend='teacher27b',stage='drop_recent',model_id='teacher-model',world_seed=17,protocol_path=str(base/'PROTOCOL.json'),protocol_sha256=x.sha(base/'PROTOCOL.json'),pool_binding={'path':str(base/'pool/POOL.json'),'sha256':x.sha(base/'pool/POOL.json'),**{k:v for k,v in self.pool_row.items() if k not in ['id','family']}},source_root=str(self.source),source_binding=self.source_binding,sampling={'temperature':0.6,'chat_template_kwargs':{'enable_thinking':False}},experience_assignment={'source_id':'heat_1','carrier':'ordinary_public_history','manifest_sha256':'3'*64})
        totals={k:sum(r['usage'][k] for r in responses) for k in ['prompt_tokens','completion_tokens','total_tokens']}
        self.r=dict(status='RETURNED',case_id='c1',backend='teacher27b',stage='drop_recent',won=True,world_actions=2,total_world_action_count=3,real_model_calls=4,forwarded_model_posts=4,response_receipts=responses,unknown_usage_model_posts=0,provider_usage=totals,errors=[],model_relay_errors=[],rounds=[{'round':1,'exit':0,'raw_sha256':x.sha(self.root/'raw_1.jsonl')}],source_binding_charge_once=self.source_binding,elapsed_seconds=5.,replay_control_cost={'control_world_actions':1,'all_public_states_equal':True},final_world_state=state(3,True))
        first=x.read_json(self.root/'requests/00001.json')['forwarded'];digest=x.sha(self.root/'task.txt');proof=dict(expected_task_sha256=digest,normalized_task_sha256=digest,whole_task_raw_equal=False,whole_task_lossless_quoted_equal=True,first_forwarded_request_sha256=x.object_sha(first));self.r['experience_delivery']=proof;write(self.root/'actual_task_delivery.json',{**proof,'stage':'drop_recent'})
        self.refresh()
    def refresh(self):
        self.m['inputs_sha256']={name:x.sha(self.root/name) for name in ['task.txt','opencode_config.json','initial_reset.json','handoff_public.json']};write(self.root/'manifest.json',self.m);self.r['manifest_sha256']=x.sha(self.root/'manifest.json');write(self.root/'receipt.json',self.r)
        self.entry=dict(root=str(self.root),receipt_sha256=x.sha(self.root/'receipt.json'),case='c1',backend=self.r['backend'],stage=self.r['stage'],status=self.r['status'],won=self.r['won'],new_world_actions=self.r['world_actions'],provider_usage=self.r['provider_usage'],real_model_calls=self.r['real_model_calls']);self.result=dict(status='ALL_TEACHER_DIAGNOSTICS_RETURNED',error=None,completed_count=1,results=[self.entry]);write(self.batch,self.result)
    def build(self):return x.build_supervision([(self.batch,x.sha(self.batch))],study_root=self.base)
    def body_change(self,index,text):
        body=self.root/f'responses/{index:05}.body';body.write_text(text);r=self.r['response_receipts'][index-1];r.update(body_sha256=x.sha(body),body_bytes=body.stat().st_size);write(Path(str(body)+'.receipt.json'),r);self.refresh()

    def sync_requests(self):
        for p in sorted((self.root/'requests').glob('*.json')):
            request=x.read_json(p)['forwarded'];write(self.root/'template_checks'/p.name,{'request_payload_sha256':x.object_sha(request)})
        first=x.read_json(self.root/'requests/00001.json')['forwarded'];digest=x.sha(self.root/'task.txt');proof=dict(expected_task_sha256=digest,normalized_task_sha256=digest,whole_task_raw_equal=False,whole_task_lossless_quoted_equal=True,first_forwarded_request_sha256=x.object_sha(first));self.r['experience_delivery']=proof;write(self.root/'actual_task_delivery.json',{**proof,'stage':self.m['stage']})
        self.r['rounds'][0]['raw_sha256']=x.sha(self.root/'raw_1.jsonl');self.refresh()
    def ordinary(self):
        destination=self.base/'cases/c1/ordinary_reset/teacher27b/attempt_v1';destination.parent.mkdir(parents=True);self.root.rename(destination);self.root=destination
        self.m.update(stage='ordinary_reset',source_root=None,source_binding=None,cohort_binding=None,caps=x.read_json(self.base/'PROTOCOL.json')['total_caps'],world_step_cap=100);self.r.update(stage='ordinary_reset',source_binding_charge_once=None,replay_control_cost=None,total_world_action_count=2,final_world_state=state(2,True))
        write(self.root/'handoff_public.json',state(0));(self.root/'execute_replay.jsonl').unlink();self.world=[self.world[0],{'event':'reset','state':state(0)},{'event':'step','action':'look','state':state(1)},{'event':'step','action':'put item 1','state':state(2,True)}];write(self.root/'execute_world.jsonl',self.world,True)
        outputs={}
        for event in self.raw:
            part=event['part'];cid=part['callID']
            if cid!='bad':part['state']['output']='public client warning\n'+json.dumps(state(1 if cid=='a' else 2,cid=='b'))+'\n'
            outputs[cid]=part['state']['output']
        write(self.root/'raw_1.jsonl',self.raw,True);task=x.ordinary_reset_prompt(state(0));(self.root/'task.txt').write_bytes(task.encode())
        for path in (self.root/'requests').glob('*.json'):
            obj=x.read_json(path)
            for msg in obj['forwarded']['messages']:
                if msg['role']=='user':msg['content']='"'+task.replace('"','\\"')+'"'
                if msg['role']=='tool':msg['content']=outputs[msg['tool_call_id']]
            write(path,obj)
        self.sync_requests();return self
    def two_rounds(self):
        sid='ses_fixture1';rawparts={e['part']['callID']:copy.deepcopy(e['part']) for e in self.raw}
        for part in rawparts.values():part['sessionID']=sid
        self.raw=[{'type':'tool_use','part':rawparts['a']},{'type':'text','sessionID':sid,'part':{'text':'I stopped early.'}}];write(self.root/'raw_1.jsonl',self.raw,True)
        raw2=[{'type':'tool_use','part':rawparts['bad']},{'type':'tool_use','part':rawparts['b']},{'type':'text','sessionID':sid,'part':{'text':'Done.'}}];write(self.root/'raw_2.jsonl',raw2,True)
        initial=x.read_json(self.root/'requests/00001.json')['forwarded'];messages=copy.deepcopy(initial['messages']);responses=[]
        completion=[assistant('a','look'),{'role':'assistant','content':'I stopped early.'},assistant('bad','take unknown'),assistant('b','put item 1'),{'role':'assistant','content':'Done.'}]
        for i,msg in enumerate(completion,1):
            if i==3:messages.append({'role':'user','content':'"'+x.CONTINUE+'"'})
            request={**initial,'messages':copy.deepcopy(messages)};write(self.root/f'requests/{i:05}.json',{'incoming':request,'forwarded':request});usage=dict(prompt_tokens=10+i,completion_tokens=2,total_tokens=12+i);body=self.root/f'responses/{i:05}.body';body.write_text(sse(msg,usage));response=dict(status=200,complete=True,body_bytes=body.stat().st_size,body_sha256=x.sha(body),usage=usage);responses.append(response);write(Path(str(body)+'.receipt.json'),response);messages.append(msg)
            if msg.get('tool_calls'):
                cid=msg['tool_calls'][0]['id'];messages.append({'role':'tool','tool_call_id':cid,'content':rawparts[cid]['state']['output']})
        self.messages=messages;self.r.update(response_receipts=responses,real_model_calls=5,forwarded_model_posts=5,provider_usage={key:sum(row['usage'][key] for row in responses) for key in ['prompt_tokens','completion_tokens','total_tokens']},ordinary_continuations=1,rounds=[{'round':1,'exit':0,'raw_sha256':x.sha(self.root/'raw_1.jsonl'),'state':state(2),'model_posts_cumulative':2},{'round':2,'exit':0,'raw_sha256':x.sha(self.root/'raw_2.jsonl'),'state':state(3,True),'model_posts_cumulative':5}]);self.m['ordinary_continuations']=1
        write(self.root/'ordinary_continuation.json',dict(session_id=sid,prompt=x.CONTINUE,after_round=1,world_state_before=state(2),world_reset=False,new_method=False));self.sync_requests();return self


class SupervisionTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name).resolve();self.f=Fixture(self.base)
    def test_success_masks_full_accepted_completion_and_keeps_failed_tool_context(self):
        b=self.f.build();r=b['trajectories'][0];positive=r['supervised_assistant_turn_indices'];self.assertEqual(len(positive),2);self.assertEqual(r['messages'],self.f.messages)
        self.assertTrue(all(r['messages'][i]['content']=='Public plan before action.' for i in positive));self.assertTrue(all(t['fields']==['content','tool_calls'] for t in r['assistant_turn_metadata'] if t['supervised']))
        bad=next(t for t in r['assistant_turn_metadata'] if t.get('call_id')=='bad');self.assertFalse(bad['supervised']);self.assertEqual(bad['client_error'],'invalid_action');self.assertFalse(r['role_mask_metadata'][-1]['supervised']);self.assertNotIn('private reasoning excluded',json.dumps(r['messages']));self.assertTrue(any('invalid_action' in msg.get('content','') for msg in r['messages']));self.assertFalse(b['manifest']['old_single_completion_training_runner_compatible'])
    def test_failed_native_not_promoted_and_cost_preserved(self):
        self.f.r['won']=False;self.f.r['final_world_state']=state(3);self.f.world[-1]['state']=state(3);write(self.f.root/'execute_world.jsonl',self.f.world,True);self.f.refresh();b=self.f.build();self.assertFalse(b['trajectories']);self.assertEqual(b['exclusions'][0]['reason'],'native_not_won');self.assertEqual(b['ledger']['selected_recovery_real_calls'],4)
    def test_claimed_success_without_native_win_rejected(self):
        self.f.r['final_world_state']=state(3);self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'native state'):self.f.build()
    def test_inflight_batch_rejected(self):
        self.f.result['status']='RUNNING';write(self.f.batch,self.f.result)
        with self.assertRaisesRegex(x.IntegrityError,'terminal'):self.f.build()
    def test_pinned_hash_tampering_rejected(self):
        for filename in ['task.txt','raw_1.jsonl']:
            with self.subTest(filename=filename):
                p=self.f.root/filename;old=p.read_bytes();p.write_bytes(old+b' ')
                with self.assertRaisesRegex(x.IntegrityError,'hash mismatch'):self.f.build()
                p.write_bytes(old)
    def test_sse_body_tampering_rejected(self):
        p=self.f.root/'responses/00001.body';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(x.IntegrityError,'hash mismatch'):self.f.build()
    def test_unknown_usage_rejected(self):
        self.f.r['unknown_usage_model_posts']=1;self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'usage'):self.f.build()
    def test_wrong_actual_sampling_rejected(self):
        self.f.m['sampling']['temperature']=1.;self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'sampling'):self.f.build()
    def test_missing_tool_mapping_explicit_exclusion(self):
        self.f.raw[0]['part']['callID']='unknown';write(self.f.root/'raw_1.jsonl',self.f.raw,True);self.f.r['rounds'][0]['raw_sha256']=x.sha(self.f.root/'raw_1.jsonl');self.f.refresh();b=self.f.build();self.assertEqual(b['exclusions'][0]['reason'],'supervision_mapping_rejected');self.assertIn('mapping',b['exclusions'][0]['details']);self.assertEqual(b['ledger']['selected_recovery_real_calls'],4)
    def test_malformed_native_arguments_explicit_exclusion(self):
        msg=assistant('a','look');msg['tool_calls'][0]['function']['arguments']='{bad';self.f.body_change(1,sse(msg,self.f.r['response_receipts'][0]['usage']));b=self.f.build();self.assertIn('SSE target',b['exclusions'][0]['details'])
    def test_reasoning_only_not_promoted(self):
        self.f.body_change(4,sse({'role':'assistant','content':''},self.f.r['response_receipts'][3]['usage']));row=self.f.build()['trajectories'][0];self.assertFalse(row['assistant_turn_metadata'][-1]['supervised']);self.assertEqual(row['messages'][-1]['content'],'');self.assertGreater(row['assistant_turn_metadata'][-1]['ignored_reasoning_utf8_bytes'],0)
    def test_complex_command_explicitly_rejected(self):
        msg=assistant('a','look');msg['tool_calls'][0]['function']['arguments']=json.dumps({'command':command('look')+'; '+command('look')});self.f.raw[0]['part']['state']['input']=json.loads(msg['tool_calls'][0]['function']['arguments']);write(self.f.root/'raw_1.jsonl',self.f.raw,True);self.f.r['rounds'][0]['raw_sha256']=x.sha(self.f.root/'raw_1.jsonl');self.f.body_change(1,sse(msg,self.f.r['response_receipts'][0]['usage']));b=self.f.build();self.assertIn('complex',b['exclusions'][0]['details'])
    def test_tool_exit_zero_with_error_not_positive(self):
        self.f.raw[1]['part']['state']['metadata']['exit']=0;write(self.f.root/'raw_1.jsonl',self.f.raw,True);self.f.r['rounds'][0]['raw_sha256']=x.sha(self.f.root/'raw_1.jsonl');self.f.refresh();self.assertIn('ambiguous error',self.f.build()['exclusions'][0]['details'])
    def test_whole_task_not_just_reminder_required(self):
        self.f.r['experience_delivery']['normalized_task_sha256']='0'*64;self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'whole-task'):self.f.build()
    def test_context_mutation_rejected(self):
        p=self.f.root/'requests/00002.json';obj=x.read_json(p);obj['forwarded']['messages'][0]['content']='changed';write(p,obj);write(self.f.root/'template_checks/00002.json',{'request_payload_sha256':x.object_sha(obj['forwarded'])})
        with self.assertRaisesRegex(x.IntegrityError,'conversation'):self.f.build()
    def test_duplicate_episode_no_double_cost(self):
        write(self.f.batch,{**self.f.result,'completed_count':2,'results':[self.f.entry,self.f.entry]});b=self.f.build();self.assertEqual(len(b['trajectories']),1);self.assertEqual(b['ledger']['selected_recovery_real_calls'],4);self.assertEqual(len(b['ledger']['collector_sources_once']),1)
    def test_same_source_task_not_independent_and_source_fee_once(self):
        other=self.f.root.with_name('attempt_v2');shutil.copytree(self.f.root,other);entry={**self.f.entry,'root':str(other)};write(self.f.batch,{**self.f.result,'completed_count':2,'results':[self.f.entry,entry]});b=self.f.build();self.assertEqual(len(b['trajectories']),1);self.assertEqual(b['exclusions'][0]['reason'],'duplicate_source_task_layout');self.assertEqual(b['ledger']['selected_recovery_real_calls'],8);self.assertEqual(len(b['ledger']['collector_sources_once']),1)
    def test_output_order_preserved_fresh_directory_required(self):
        b=self.f.build();root=self.base/'out';r=x.export_supervision(b,root);row=json.loads((root/'trajectories.jsonl').read_text(encoding='utf8'));self.assertEqual(row['messages'],self.f.messages);self.assertEqual(list(row['tools'][0]['function']),list(self.f.tools[0]['function']));self.assertEqual(r['supervised_assistant_turns'],2)
        with self.assertRaises(FileExistsError):x.export_supervision(b,root)
    def test_source_binding_tamper(self):
        (self.f.source/'execute_world.jsonl').write_text('[]')
        with self.assertRaisesRegex(x.IntegrityError,'hash mismatch'):self.f.build()
    def test_pool_identity_does_not_trust_case_alias(self):
        self.f.m['pool_binding']['task_uid']='fake';self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'POOL'):self.f.build()
    def test_unselected_entries_explicit_summary_not_read(self):
        entry={**self.f.entry,'backend':'student8b','root':str(self.base/'absent')};write(self.f.batch,{**self.f.result,'completed_count':2,'results':[self.f.entry,entry]});b=self.f.build();self.assertEqual(b['exclusions'][0]['reason'],'unselected_backend_or_stage');self.assertTrue(b['exclusions'][0]['batch_summary_only'])
    def test_failure_still_checks_actual_sse_and_task_delivery(self):
        self.f.r['won']=False;self.f.r['final_world_state']=state(3);self.f.world[-1]['state']=state(3);write(self.f.root/'execute_world.jsonl',self.f.world,True);self.f.refresh()
        p=self.f.root/'responses/00001.body';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(x.IntegrityError,'hash mismatch'):self.f.build()
    def test_missing_provider_template_digest_rejected(self):
        (self.f.root/'template_checks/00001.json').unlink()
        with self.assertRaisesRegex(x.IntegrityError,'digest'):self.f.build()
    def test_wrong_world_action_not_inferred_from_shell_success(self):
        self.f.world[-1]['action']='other action';write(self.f.root/'execute_world.jsonl',self.f.world,True);b=self.f.build();self.assertIn('no matching accepted',b['exclusions'][0]['details'])
    def test_source_replay_state_divergence_rejected(self):
        p=self.f.root/'execute_replay.jsonl';rows=x.jsonl(p);rows[-1]['actual']['observation']='different';write(p,rows,True)
        with self.assertRaisesRegex(x.IntegrityError,'replay'):self.f.build()
    def test_final_text_is_not_a_success_reference(self):
        self.f.r['final_world_state']['done']=False;self.f.world[-1]['state']['done']=False;write(self.f.root/'execute_world.jsonl',self.f.world,True);self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'terminal reward'):self.f.build()
    def test_native_argument_text_preserved_across_real_sdk_json_reserialization(self):
        for i in range(2,5):
            p=self.f.root/f'requests/{i:05}.json';obj=x.read_json(p)
            for msg in obj['forwarded']['messages']:
                for call in msg.get('tool_calls',[]):call['function']['arguments']=json.dumps(json.loads(call['function']['arguments']),separators=(',',':'))
            write(p,obj);write(self.f.root/f'template_checks/{i:05}.json',{'request_payload_sha256':x.object_sha(obj['forwarded'])})
        b=self.f.build();row=b['trajectories'][0];self.assertEqual(row['messages'],self.f.messages);self.assertFalse(row['conversation_prefix_checks'][1]['exact_prefix_equal']);self.assertTrue(row['conversation_prefix_checks'][1]['tool_argument_JSON_equivalence_verified'])
    def test_ordinary_reset_no_failure_source_fee_same_task_group(self):
        recovery=self.f.build()['trajectories'][0];self.f.ordinary();ordinary=x.build_supervision([(self.f.batch,x.sha(self.f.batch))],stage='ordinary_reset',study_root=self.base);row=ordinary['trajectories'][0];self.assertEqual(row['source_group'],recovery['source_group']);self.assertEqual(len(row['supervised_assistant_turn_indices']),2);self.assertEqual(ordinary['ledger']['collector_sources_once'],[]);self.assertEqual(ordinary['ledger']['original_experience_references_once'],[])
    def test_ordinary_reset_forbids_fake_source(self):
        self.f.ordinary();self.f.m['source_root']=str(self.f.source);self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'cannot carry'):x.build_supervision([(self.f.batch,x.sha(self.f.batch))],stage='ordinary_reset',study_root=self.base)
    def test_ordinary_caps_and_empty_history_prompt_strict(self):
        self.f.ordinary();self.f.m['caps']['posts']=32;self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'total caps'):x.build_supervision([(self.f.batch,x.sha(self.f.batch))],stage='ordinary_reset',study_root=self.base)
        self.f.m['caps']['posts']=128;(self.f.root/'task.txt').write_bytes(b'a substituted goal');self.f.sync_requests()
        with self.assertRaisesRegex(x.IntegrityError,'prompt differs'):x.build_supervision([(self.f.batch,x.sha(self.f.batch))],stage='ordinary_reset',study_root=self.base)
    def test_ordinary_reset_handoff_must_be_actual_reset(self):
        self.f.ordinary();write(self.f.root/'handoff_public.json',state(1));self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'non-reset'):x.build_supervision([(self.f.batch,x.sha(self.f.batch))],stage='ordinary_reset',study_root=self.base)
    def test_two_round_same_session_fixed_continue_retained_unsupervised(self):
        self.f.two_rounds();row=self.f.build()['trajectories'][0];self.assertEqual(row['messages'],self.f.messages);self.assertEqual(len(row['supervised_assistant_turn_indices']),2);self.assertEqual(len(row['ordinary_continuation_checks']),1);self.assertEqual(sum(msg['role']=='user' for msg in row['messages']),2);self.assertFalse(next(t for t in row['assistant_turn_metadata'] if t['post_index']==2)['supervised'])
    def test_two_round_different_session_rejected(self):
        self.f.two_rounds();p=self.f.root/'raw_2.jsonl';rows=x.jsonl(p)
        for row in rows:
            if 'sessionID' in row:row['sessionID']='ses_other'
            if 'sessionID' in row.get('part',{}):row['part']['sessionID']='ses_other'
        write(p,rows,True);self.f.r['rounds'][1]['raw_sha256']=x.sha(p);self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'same unfinished session'):self.f.build()
    def test_two_round_arbitrary_goal_rejected(self):
        self.f.two_rounds();p=self.f.root/'requests/00003.json';req=x.read_json(p);req['forwarded']['messages'][-1]['content']='Do a different task';write(p,req);self.f.sync_requests()
        with self.assertRaisesRegex(x.IntegrityError,'arbitrary'):self.f.build()
    def test_two_round_claimed_reset_or_wrong_state_rejected(self):
        self.f.two_rounds();p=self.f.root/'ordinary_continuation.json';obj=x.read_json(p);obj['world_reset']=True;write(p,obj)
        with self.assertRaisesRegex(x.IntegrityError,'proof differs'):self.f.build()
    def test_two_round_missing_or_tampered_raw_rejected(self):
        self.f.two_rounds();p=self.f.root/'raw_2.jsonl';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(x.IntegrityError,'hash mismatch'):self.f.build()
    def test_three_controller_rounds_rejected(self):
        self.f.two_rounds();self.f.r['rounds'].append({**self.f.r['rounds'][1],'round':3});write(self.f.root/'raw_3.jsonl',[],True);self.f.r['rounds'][-1]['raw_sha256']=x.sha(self.f.root/'raw_3.jsonl');self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'round count'):self.f.build()
    def test_unapproved_continuation_cannot_be_enabled_by_file_only(self):
        self.f.two_rounds();self.f.m['ordinary_continuations']=0;self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'continuation budget'):self.f.build()
    def test_two_round_cannot_change_old_context_with_fixed_last_user(self):
        self.f.two_rounds();p=self.f.root/'requests/00003.json';obj=x.read_json(p);obj['forwarded']['messages'][0]['content']='another system';write(p,obj);self.f.sync_requests()
        with self.assertRaisesRegex(x.IntegrityError,'conversation'):self.f.build()
    def test_positive_helper_rejects_failed_receipt(self):
        self.f.r['won']=False
        with self.assertRaisesRegex(x.IntegrityError,'native won'):x.align_observed_chat(self.f.root,self.f.m,self.f.r,[],0,{})
    def test_zero_label_failed_round_control_never_promoted(self):
        self.f.two_rounds();view=x.align_observed_chat(self.f.root,self.f.m,self.f.r,[e for e in self.f.world if e.get('event')=='step'],1,{},supervise=False);self.assertEqual(view['supervised_assistant_turn_indices'],[]);self.assertTrue(all(not meta['supervised'] for meta in view['role_mask_metadata']))
    def test_boolean_round_id_rejected(self):
        self.f.two_rounds();self.f.r['rounds'][0]['round']=True;self.f.refresh();write(self.f.root/'raw_True.jsonl',self.f.raw,True);self.f.r['rounds'][0]['raw_sha256']=x.sha(self.f.root/'raw_True.jsonl');self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'round count'):self.f.build()
    def test_ordinary_no_fabricated_replay_fee(self):
        self.f.ordinary();self.f.r['replay_control_cost']={'control_world_actions':3};self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'fabricated replay'):x.build_supervision([(self.f.batch,x.sha(self.f.batch))],stage='ordinary_reset',study_root=self.base)
    def test_float_ordinary_caps_are_not_byte_equivalent_budget(self):
        self.f.ordinary();self.f.m['caps']['seconds']=1800.0;self.f.refresh()
        with self.assertRaisesRegex(x.IntegrityError,'total caps'):x.build_supervision([(self.f.batch,x.sha(self.f.batch))],stage='ordinary_reset',study_root=self.base)
    def test_single_action_parser_rejects_shell_forms(self):
        for cmd in ['cat /hidden',command('look')+' && echo done',command('look')+'\n'+command('look')]:
            with self.subTest(command=cmd),self.assertRaises(x.UnsupportedTrajectory):x.parse_command(cmd)

if __name__=='__main__':unittest.main()
