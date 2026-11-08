"""Pure synthetic channel controls; no tool execution or scientific outcomes."""
from pathlib import Path
import copy, json
import importlib.util, unittest
from unittest import mock

PATH=Path(__file__).resolve().parents[1]/'research/agent_frontier_portfolio_20261029/action_channel_probe.py'
spec=importlib.util.spec_from_file_location('action_channel_cpu',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def payload():
    return dict(tool_choice='auto',stream=True,seed=17,temperature=.2,max_tokens=8192,messages=[{'role':'user','content':'FAKE'}],
        tools=[{'type':'function','function':{'name':'bash','parameters':{'type':'object','properties':{'command':{'type':'string'}},'required':['command']}}}])


def sse(parts=(),finish='stop',usage=True):
    chunks=[{'choices':[{'index':0,'delta':part,'finish_reason':None}]} for part in parts]
    final={'choices':[{'index':0,'delta':{},'finish_reason':finish}]}
    if usage:final['usage']={'prompt_tokens':10,'completion_tokens':3,'total_tokens':13,'prompt_tokens_details':{'cached_tokens':4}}
    chunks.append(final)
    return ''.join('data: '+json.dumps(c)+'\n\n' for c in chunks).encode()+b'data: [DONE]\n\n'


def calls(arguments='{"command":"look"}',name='bash'):
    return [{'tool_calls':[{'index':0,'id':'call1','type':'function','function':{'name':name,'arguments':arguments}}]}]


class ActionChannelTests(unittest.TestCase):
    def test_copy_changes_only_tool_choice(self):
        original=payload();snapshot=copy.deepcopy(original);new=m.required_payload(original)
        self.assertEqual(original,snapshot);self.assertEqual(new['tool_choice'],'required');m.validate_mutation(original,new)
        new['messages'][0]['content']='changed';self.assertEqual(original,snapshot)
        with self.assertRaises(ValueError):m.validate_mutation(original,new)

    def test_no_stream_seed_or_temperature_change(self):
        for key,value in [('stream',False),('seed',29),('temperature',1),('max_tokens',8)]:
            new=m.required_payload(payload());new[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate_mutation(payload(),new)
        new=m.required_payload(payload());schema=new['tools'][0]['function']['parameters']
        new['tools'][0]['function']['parameters']=dict(reversed(list(schema.items())))
        with self.assertRaises(ValueError):m.validate_mutation(payload(),new)

    def test_unique_final_done(self):
        raw=sse()
        for bad in (raw.replace(b'data: [DONE]\n\n',b''),raw+b'data: [DONE]\n\n',raw+b'data: {}\n\n'):
            with self.subTest(body=bad[-40:]),self.assertRaises(ValueError):m.parse_sse(bad,payload())
        with self.assertRaises(ValueError):m.parse_sse(sse(finish='unknown'),payload())

    def test_plain_stop_and_unknown_usage_not_zero(self):
        result=m.parse_sse(sse([{'content':'go to desk 1'}],usage=False),payload())
        self.assertEqual(result['tool_calls'],[]);self.assertEqual(result['finish_reason'],'stop')
        self.assertIsNone(result['usage']);self.assertIsNone(result['cached_input_tokens']);self.assertFalse(result['usage_known'])

    def test_usage_cache_subset_and_last_usage(self):
        result=m.parse_sse(sse(),payload());self.assertEqual(result['usage']['total_tokens'],13);self.assertEqual(result['cached_input_tokens'],4)
        raw=sse().replace(b'"cached_tokens": 4',b'"cached_tokens": 11')
        with self.assertRaises(ValueError):m.parse_sse(raw,payload())
        prior=b'data: {"usage":{"prompt_tokens":1,"completion_tokens":0,"total_tokens":1}}\n\n'
        result=m.parse_sse(prior+sse(),payload());self.assertEqual(result['usage_updates'],2);self.assertEqual(result['usage']['total_tokens'],13)

    def test_partial_arguments_merge_and_stop_tool_finish(self):
        parts=calls('{"com');parts.append({'tool_calls':[{'index':0,'function':{'arguments':'mand":"look"}'}}]})
        result=m.parse_sse(sse(parts),payload());self.assertFalse(result['errors']);self.assertEqual(result['tool_calls'][0]['arguments'],{'command':'look'})
        self.assertEqual(result['finish_reason'],'stop')
        p=payload();p['tools'][0]['function']['name']='bashbash';parts=calls('',name='bash')
        parts.append({'tool_calls':[{'index':0,'function':{'name':'bash','arguments':'{"command":"look"}'}}]})
        self.assertEqual(m.parse_sse(sse(parts),p)['tool_calls'][0]['name'],'bashbash')

    def test_invalid_or_truncated_arguments_preserve_usage(self):
        for args in ('{"command":','not-json','{"command":NaN}'):
            result=m.parse_sse(sse(calls(args),finish='length'),payload())
            self.assertTrue(result['channel_errors']);self.assertFalse(result['errors']);self.assertTrue(result['truncated']);self.assertEqual(result['usage']['total_tokens'],13)

    def test_unknown_name_and_bad_parameters(self):
        self.assertTrue(m.parse_sse(sse(calls(name='not_declared')),payload())['channel_errors'])
        if m.Draft202012Validator is not None:self.assertTrue(m.parse_sse(sse(calls('{"command":7}')),payload())['channel_errors'])
        for duplicate in (False,True):
            parts=calls();item=copy.deepcopy(parts[0]['tool_calls'][0]);item['index']=1
            if duplicate:parts[0]['tool_calls'].append(item)
            else:parts[0]['tool_calls'][0].pop('id')
            result=m.parse_sse(sse(parts),payload());self.assertTrue(result['channel_errors']);self.assertFalse(result['errors'])

    def test_schema_absence_is_explicitly_unverified(self):
        with mock.patch.object(m,'Draft202012Validator',None):result=m.parse_sse(sse(calls('{"command":7}')),payload())
        self.assertFalse(result['tool_calls'][0]['schema_validated']);self.assertEqual(result['tool_calls'][0]['validation'],'JSON_SYNTAX_AND_DECLARED_NAME_ONLY')
        p=payload();p['tools'][0]['function']['parameters']['$schema']='https://unsupported.invalid/dialect'
        result=m.parse_sse(sse(calls()),p);self.assertEqual(result['channel_status'],'TOOL_CALL_SCHEMA_UNVERIFIED');self.assertFalse(result['errors'])

    def test_tool_declaration_types_and_external_refs_rejected(self):
        for kind in ('custom',None):
            p=payload();p['tools'][0]['type']=kind
            with self.subTest(kind=kind),self.assertRaises(ValueError):m.declared_tools(p)
        p=payload();p['tools']+=copy.deepcopy(p['tools'])
        with self.assertRaises(ValueError):m.declared_tools(p)
        p=payload();p['tools'][0]['function']['parameters']={'$ref':'https://invalid.example/schema'}
        with self.assertRaises(ValueError):m.declared_tools(p)

    def test_wrong_result_hash_refused_before_read(self):
        with self.assertRaises(ValueError):m.prepare_probe(Path('/FAKE/result'),'0'*64)
