"""Offline contracts for representation-aware repair, not task results."""
import copy
import json
from pathlib import Path
import sys
import unittest

BASE = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'
sys.path.insert(0, str(BASE))
import continuation_program as CP
import binding_update as B
import binding_experiment as E


SOURCE = '''def extract_phone(text):
    return text
def tool_results(o):
    return [json.loads(x['content']) for x in o['messages'] if x['role']=='tool']
def step(o,m):
    target=[x['content'] for x in o['messages'] if x['role']=='user'][-1]
    matches=[r for r in tool_results(o) if r.get('phone_number')==target and 'data_used_gb' in r and 'data_limit_gb' in r]
    if matches:
        r=matches[-1]
        if r['data_used_gb']>r['data_limit_gb']:
            return {'kind':'act','name':'credit','arguments':{'line_id':r['line_id'],'amount':r['data_used_gb']-r['data_limit_gb']},'memory':m}
    return {'kind':'yield','memory':m}
'''


def observation(records):
    return dict(messages=[dict(role='user', content='target')] + [
        dict(role='tool', requestor='assistant', id='event-' + str(i), content=json.dumps(record))
        for i, record in enumerate(records)], turn=7, done=False,
        proposed_operation=None)


def combined():
    return dict(line_id='line-B', plan_id='plan-B', phone_number='target',
                data_used_gb=12, data_limit_gb=10, data_refueling_gb=0)


class BindingUpdateTests(unittest.TestCase):
    def test_partition_preserves_facts_entity_role_order_and_original_input(self):
        source = observation([combined()])
        original = copy.deepcopy(source)
        views = B.receipt_views(source)
        self.assertTrue(views)
        self.assertEqual(source, original)
        for view in views:
            changed = view['observation']
            self.assertEqual(changed['turn'], source['turn'])
            self.assertEqual(changed['messages'][0], source['messages'][0])
            self.assertEqual(len(changed['messages']), len(source['messages']))
            for i in view['changed_messages']:
                before, after = source['messages'][i], changed['messages'][i]
                self.assertEqual({k: v for k, v in before.items() if k != 'content'},
                                 {k: v for k, v in after.items() if k != 'content'})
                rebuilt = {}
                for part in json.loads(after['content']):
                    self.assertEqual(part['line_id'], 'line-B')
                    self.assertEqual(part['plan_id'], 'plan-B')
                    rebuilt.update(part)
                self.assertEqual(rebuilt, json.loads(before['content']))

    def test_view_failure_does_not_remove_valid_ordinary_candidate(self):
        row = dict(id='one', source='handwritten', executor='actor',
            observation=observation([combined()]), command=dict(name='credit',
                arguments=dict(line_id='line-B', amount=2)), gained=['quota'], lost=[])
        score = B.score_binding_update(SOURCE, SOURCE, [row], ['credit'])
        self.assertIsNotNone(score['ordinary'])
        self.assertIsNone(score['consistency'])
        self.assertIn('view_errors', score)

    def test_same_pool_controls_do_not_claim_consistency_unique_when_augmented_erm_matches(self):
        row = dict(id='one', source='handwritten', executor='actor',
            observation=observation([combined()]), command=dict(name='credit',
                arguments=dict(line_id='line-B', amount=2)), gained=['quota'], lost=[])
        fixed = B.normalized_baseline(SOURCE)
        report = B.select_binding_update(SOURCE, [fixed], [row], ['credit'])
        self.assertEqual(report['selected']['ordinary'], 0)
        self.assertEqual(report['selected']['augmented_erm'], 1)
        self.assertEqual(report['selected']['consistency'], 1)
        self.assertEqual(report['source_units'], 1)
        self.assertEqual(report['independent_native_executions'], 0)

    def test_normalization_uses_target_entity_and_latest_line_values(self):
        records = [dict(line_id='line-A', plan_id='plan-A', phone_number='other', data_used_gb=99),
            dict(line_id='line-B', plan_id='plan-B', phone_number='target', data_used_gb=12),
            dict(plan_id='plan-B', data_limit_gb=10), dict(plan_id='plan-A', data_limit_gb=100)]
        program = CP.load_program(B.normalized_baseline(SOURCE))
        actual = CP.public_step(program, observation(records), {}, ['credit'])
        self.assertEqual(actual['arguments'], dict(line_id='line-B', amount=2))
        records.append(dict(line_id='line-B', data_used_gb=7))
        self.assertEqual(CP.public_step(program, observation(records), {}, ['credit'])['kind'], 'yield')
        for view in B.receipt_views(observation(records)):
            self.assertEqual(CP.public_step(program, view['observation'], {}, ['credit'])['kind'], 'yield')

    def test_request_preserves_materials_and_uses_supported_structured_delivery(self):
        material = dict(program=SOURCE, source_feedback=['actual failure'], view_note='derived')
        request = B.binding_edit_request(material, model='test-model')
        self.assertEqual(json.loads(request['messages'][1]['content']), material)
        self.assertEqual(request['tool_choice']['function']['name'], 'emit_edit')
        self.assertEqual(request['max_tokens'], 32768)
        self.assertNotIn('thinking', request)
        self.assertNotIn('reasoning_effort', request)
        self.assertIn('exactly one complete function definition', request['messages'][0]['content'])
        self.assertIn('helper in its own separate edits item', request['messages'][0]['content'])

    def test_stream_parser_reassembles_tool_fragments_without_delivering_reasoning(self):
        events = [dict(choices=[dict(delta=dict(reasoning_content='private analysis'))]),
            dict(choices=[dict(delta=dict(tool_calls=[dict(index=0,
                function=dict(name='emit_edit', arguments='{"edits":'))]))]),
            dict(choices=[dict(delta=dict(tool_calls=[dict(index=0,
                function=dict(arguments='[]}'))]), finish_reason='tool_calls')]),
            dict(choices=[], usage=dict(prompt_tokens=2, completion_tokens=3, total_tokens=5))]
        raw = ('\n'.join('data: ' + json.dumps(event) for event in events) + '\ndata: [DONE]\n').encode()
        finish, calls = E.parse_calls(raw)
        self.assertEqual(finish, 'tool_calls')
        self.assertEqual(calls, {0:dict(name='emit_edit', arguments='{"edits":[]}')})
        self.assertNotIn('private analysis', str(calls))


if __name__ == '__main__':
    unittest.main()
