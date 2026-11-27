from io import BytesIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.request import Request


PILOT = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
sys.path.insert(0, str(PILOT))
try:
    import compact_consensus as compact
finally:
    sys.path.remove(str(PILOT))


ROW = {
    'id': 'private-id', 'dataset': 'finqa', 'report': 'private-report',
    'question': 'What are sales?', 'table': [['Metric', '2020'], ['Sales', '12']],
    'pre_text': [], 'post_text': [],
}


def choice(index, number, *, scale='none', finish='stop'):
    return {'index': index, 'finish_reason': finish,
            'message': {'role': 'assistant', 'content': f'Final program: add({number}, const_0)\nFinal scale: {scale}'},
            'logprobs': {'content': [{'logprob': -0.2}, {'logprob': -0.5}]}}


def metric_sample(prompt, generation, *, cache=0, finished=0):
    return f'''# TYPE vllm:prompt_tokens_by_source_total counter
vllm:prompt_tokens_by_source_total{{model_name="student",source="local_compute"}} {prompt}
vllm:prompt_tokens_by_source_total{{model_name="student",source="local_cache_hit"}} {cache}
vllm:generation_tokens_total{{model_name="student"}} {generation}
vllm:request_success_total{{finished_reason="stop",model_name="student"}} {finished}
vllm:num_requests_running{{model_name="student"}} 0
vllm:num_requests_waiting{{model_name="student"}} 0
'''


class CompactConsensusTest(unittest.TestCase):
    def test_input_and_scale_instructions_are_shared(self):
        other = {**ROW, 'dataset': 'tatqa', 'gold': {'answer': 'private-reference'}}
        self.assertEqual(compact.compact_prompt(ROW), compact.compact_prompt(other))
        prompt = compact.compact_prompt(other)
        self.assertNotIn('private-', prompt)
        self.assertIn('Final scale:', prompt)
        self.assertIn('Plan:', compact.compact_prompt(other, planned=True))

    def test_native_execution_changes_the_choice_by_majority(self):
        result = compact.evaluate_choices(ROW, {'choices': [choice(3, 12), choice(0, 9), choice(2, 12), choice(1, 12)]}, 4)
        self.assertEqual(result['selected_index'], 1)
        self.assertEqual(result['first_executable_index'], 0)
        self.assertEqual(result['vote_share'], 0.75)
        self.assertEqual(result['selected_min_token_logprob'], -0.5)
        self.assertEqual(compact.grade_choices(ROW, result, {'exe_ans': 12}, None),
                         {'strict_executable': True, 'first_sample_strict_executable': False,
                          'correct_by_index': [False, True, True, True]})

    def test_scale_and_incomplete_samples_do_not_create_spurious_consensus(self):
        row = {**ROW, 'dataset': 'tatqa'}
        choices = [choice(0, 9), choice(1, 12, scale='percent'), choice(2, '0.12'), choice(3, 12, scale='percent', finish='length')]
        result = compact.evaluate_choices(row, {'choices': choices}, 4)
        self.assertEqual(result['executed_n'], 3)
        self.assertEqual(result['vote_share'], 0.25)
        self.assertEqual(result['selected_index'], 0)
        self.assertIsNone(result['majority_index'])
        self.assertEqual(result['samples'][3]['status'], 'not_delivered')
        self.assertEqual(result['samples'][1]['vote_key'][0], result['samples'][2]['vote_key'][0])
        self.assertNotEqual(result['samples'][1]['vote_key'][1], result['samples'][2]['vote_key'][1])

    def test_missing_or_duplicate_choice_index_raises(self):
        with self.assertRaisesRegex(ValueError, 'index'):
            compact.evaluate_choices(ROW, {'choices': [choice(0, 12), choice(0, 12), choice(1, 12), choice(2, 12)]}, 4)

    def test_one_native_post_reports_logical_and_measured_engine_tokens(self):
        before = metric_sample(100, 32, cache=124, finished=2)
        after = metric_sample(205, 84, cache=424, finished=6)
        usage = {'prompt_tokens': 108, 'completion_tokens': 52, 'total_tokens': 160}
        response = {'model': 'student', 'choices': [choice(i, 12) for i in range(4)], 'usage': usage}
        with patch.object(compact, 'urlopen', side_effect=[BytesIO(before.encode()), BytesIO(json.dumps(response).encode()),
                                                           BytesIO(after.encode())]) as request:
            result = compact.call_compact(ROW, base='http://127.0.0.1:8000/v1', model='student', n=4,
                                          max_tokens=80, temperature=0.6, seed=17, cache_salt='isolated',
                                          measure_engine=True)
        self.assertEqual(request.call_count, 3)
        for call in (request.call_args_list[0], request.call_args_list[2]):
            self.assertEqual(call.args[0], 'http://127.0.0.1:8000/metrics')
        (post,) = request.call_args_list[1].args
        self.assertIsInstance(post, Request)
        self.assertEqual(post.method, 'POST')
        self.assertEqual(json.loads(post.data)['n'], 4)
        self.assertEqual(json.loads(post.data)['cache_salt'], 'isolated')
        self.assertEqual(result['usage']['prompt_tokens'], 108)
        self.assertEqual(result['engine_work']['locally_computed_prefill_tokens'], 105)
        self.assertEqual(result['engine_work']['locally_computed_tokens'], 157)
        self.assertEqual(result['engine_work']['counter_deltas']['prompt_local_cache_hit_tokens'], 300)

    def test_contaminated_engine_delta_is_preserved_without_a_prefill_estimate(self):
        before = compact.metrics_snapshot(metric_sample(100, 32))
        after = compact.metrics_snapshot(metric_sample(205, 84))
        result = compact.engine_work(before, after, {'completion_tokens': 50})
        self.assertEqual(result['counter_deltas']['prompt_local_compute_tokens'], 105)
        self.assertIsNone(result['locally_computed_prefill_tokens'])
        self.assertFalse(result['completion_tokens_reconcile'])
