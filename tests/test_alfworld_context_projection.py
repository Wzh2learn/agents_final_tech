"""CPU-only pure projection controls; never starts an actor/relay/world."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/'research/agent_frontier_portfolio_20261029/alfworld_context_projection.py'
spec=importlib.util.spec_from_file_location('projection_tested',PATH)
x=importlib.util.module_from_spec(spec);spec.loader.exec_module(x)


def text(role,value):return {'role':role,'content':value}
def batch(*ids):return {'role':'assistant','content':'actual public plan','tool_calls':[{'id':i,'type':'function','function':{'name':'bash','arguments':'{  "command": "look" }'}} for i in ids]}
def reply(i,value='actual observation'):return {'role':'tool','tool_call_id':i,'content':value}
def wire(value):return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()


class ProjectionTests(unittest.TestCase):
    def packet(self,messages):return {'tools':[{'type':'function','function':{'name':'bash','parameters':{'properties':{'command':{'type':'string'}},'type':'object'}}}],'messages':messages,'seed':17,'temperature':0.2,'chat_template_kwargs':{'enable_thinking':False},'extra':{'preserve':'\"quotes\"\n`backticks` 中文'}}
    def test_at_most_k_rounds_is_byte_identical_JSON(self):
        for k in [1,3,20]:
            payload=self.packet([text('system','rules'),text('assistant','before'),text('user','goal'),batch('a','b'),reply('b'),reply('a'),text('assistant','after')]);projected,proof=x.project_last_tool_rounds(payload,k);self.assertEqual(wire(payload),wire(projected));self.assertEqual(proof['original_sha256'],proof['projected_sha256']);self.assertEqual(proof['removed_indices'],[])
    def test_multi_tool_batch_kept_whole_and_reply_order_is_local(self):
        payload=self.packet([text('system','s'),batch('a'),reply('a'),batch('b','c'),reply('c'),reply('b')]);projected,proof=x.project_last_tool_rounds(payload,1);self.assertEqual(projected['messages'],[payload['messages'][i] for i in [0,3,4,5]]);self.assertEqual(proof['kept_round_count'],1);self.assertEqual(proof['removed_indices'],[1,2])
    def test_all_user_system_developer_original_messages_survive(self):
        messages=[text('system','exact system'),text('developer','exact developer'),text('user','actual current goal'),batch('a'),reply('a'),text('assistant','old stop'),text('user','Continue the unfinished task.'),batch('b'),reply('b'),text('system','later system'),text('developer','later developer'),text('user','another current instruction')];payload=self.packet(messages);projected,proof=x.project_last_tool_rounds(payload,1);self.assertEqual(projected['messages'],[m for i,m in enumerate(messages) if i not in [3,4,5]]);self.assertEqual(proof['original_round_count'],2)
    def test_only_plain_assistant_at_or_after_cutoff_stays(self):
        messages=[text('assistant','old intro'),batch('a'),reply('a'),text('assistant','old reflection'),batch('b'),reply('b'),text('assistant','new reflection'),text('user','Continue'),text('assistant','new final')];projected,_=x.project_last_tool_rounds(self.packet(messages),1);self.assertEqual(projected['messages'],messages[4:])
    def test_ID_reuse_in_different_rounds_is_legal(self):
        messages=[text('user','goal'),batch('same'),reply('same','old'),text('user','Continue'),batch('same'),reply('same','current')];projected,proof=x.project_last_tool_rounds(self.packet(messages),1);self.assertEqual(projected['messages'],[messages[i] for i in [0,3,4,5]]);self.assertEqual(proof['original_round_count'],2)
    def test_input_nested_dict_and_original_order_are_immutable(self):
        payload=self.packet([text('system','s'),batch('a'),reply('a'),batch('b'),reply('b')]);before=copy.deepcopy(payload);raw=wire(payload);projected,_=x.project_last_tool_rounds(payload,1);self.assertEqual(payload,before);self.assertEqual(wire(payload),raw);self.assertEqual(list(projected),list(payload));self.assertEqual(projected['tools'],payload['tools']);self.assertEqual(projected['seed'],17);projected['tools'][0]['function']['name']='mutated copy';projected['messages'][-1]['content']='changed';self.assertEqual(payload,before)
    def test_default_k_is_three_complete_rounds(self):
        messages=[text('user','goal')]
        for n in range(5):messages.extend([batch(str(n)),reply(str(n))])
        projected,proof=x.project_last_tool_rounds(self.packet(messages));self.assertEqual(projected['messages'],messages[:1]+messages[5:]);self.assertEqual((proof['original_round_count'],proof['kept_round_count'],proof['removed_round_count']),(5,3,2))
    def test_zero_k_keeps_anchors_and_trailing_plain_assistant(self):
        messages=[text('assistant','old'),text('user','goal'),batch('a'),reply('a'),text('user','Continue'),text('assistant','current plain content')];projected,proof=x.project_last_tool_rounds(self.packet(messages),0);self.assertEqual(projected['messages'],[messages[i] for i in [1,4,5]]);self.assertEqual(proof['kept_round_count'],0)
    def test_no_tool_rounds_does_not_drop_plain_assistant(self):
        payload=self.packet([text('user','goal'),text('assistant','plain'),text('user','Continue')]);projected,proof=x.project_last_tool_rounds(payload,0);self.assertEqual(wire(payload),wire(projected));self.assertEqual(proof['original_round_count'],0)
    def test_proof_contains_only_hashes_indices_counts(self):
        _,proof=x.project_last_tool_rounds(self.packet([batch('a'),reply('a'),batch('b'),reply('b')]),1);self.assertEqual(set(proof),{'original_sha256','projected_sha256','kept_indices','removed_indices','original_round_count','kept_round_count','removed_round_count'});self.assertEqual(sorted(proof['kept_indices']+proof['removed_indices']),list(range(4)));self.assertNotEqual(proof['original_sha256'],proof['projected_sha256'])
    def test_malformed_pairings_rejected_even_if_before_cutoff(self):
        malformed=[[reply('a')],[batch('a')],[batch('a'),text('user','interrupt'),reply('a')],[batch('a'),reply('other')],[batch('a'),reply('a'),reply('a')],[batch('a','a'),reply('a')],[batch('a','b'),reply('a'),reply('a')],[batch('a'),batch('b'),reply('b')],[{'role':'assistant','tool_calls':{'id':'a'}}],[{'role':'assistant','tool_calls':[{}]}],[{'role':'assistant','tool_calls':[{'id':' ' }]}],[text('function','unsupported')],[{'role':[],'content':'invalid role'}],[{'role':'user','content':'goal','tool_calls':[]}]]
        for messages in malformed:
            with self.subTest(messages=messages),self.assertRaises(ValueError):x.project_last_tool_rounds(self.packet(messages+[batch('z'),reply('z')]),1)
    def test_invalid_k_payload_or_nonfinite_JSON_rejected(self):
        for k in [-1,True,1.0,'3']:
            with self.subTest(k=k),self.assertRaises(ValueError):x.project_last_tool_rounds(self.packet([]),k)
        for payload in [None,[],{}, {'messages':{}},{'messages':[None]},{'messages':[],'temperature':float('nan')}]:
            with self.subTest(payload=payload),self.assertRaises(ValueError):x.project_last_tool_rounds(payload)

if __name__=='__main__':unittest.main()
