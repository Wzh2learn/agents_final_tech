import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

CODE = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'
sys.path.insert(0, str(CODE))
import tatqa_correction as task


def fixture():
    record = dict(table=dict(uid='table-1', table=[['year', 'value'], ['2020', '22.12']]),
                  paragraphs=[dict(text='Public financial context', order=1)])
    question = dict(uid='question-1', question='What is the rate?', answer='HIDDEN_ANSWER',
                    scale='HIDDEN_SCALE', derivation='HIDDEN_DERIVATION', rel_paragraphs=[1])
    return task.public_record(record, question)


class TATQAExecutionTests(unittest.TestCase):
    def test_projection_keeps_full_evidence_without_gold_or_relevance_annotations(self):
        public = fixture();text = json.dumps(public)
        self.assertEqual(public['pre_text'], ['Public financial context'])
        self.assertEqual(public['table'][1], ['2020', '22.12'])
        self.assertNotIn('HIDDEN_', text)
        self.assertNotIn('rel_paragraphs', text)
        self.assertEqual(set(public), task.arithmetic.PUBLIC_KEYS)

    def test_public_execution_never_returns_correctness_and_rejects_unknown_scale(self):
        value = task.execute_public('divide(1, const_100)', fixture(), 'percent')
        self.assertEqual(value['status'], 'executed')
        self.assertAlmostEqual(value['terminal_execution_answer'], .01)
        self.assertEqual(value['predicted_scale'], 'percent')
        self.assertNotIn('execution_correct', value)
        self.assertEqual(task.execute_public('add(1, 2)', fixture(), 'trillion')['code'], 'UNSUPPORTED_PREDICTED_SCALE')

    def test_cli_persists_actual_program_and_scale_including_invalid_submissions(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp);public = folder / 'public.json';public.write_text(json.dumps(fixture()))
            argv = [sys.executable, str(CODE / 'tatqa_correction.py'), '--public', str(public), '--work', str(folder),
                    '--executor', str(task.arithmetic.executor().__file__)]
            for program in ['add(10, 12.12)', 'not-a-program']:
                returned = subprocess.run(argv + ['--program', program, '--scale', 'percent'], capture_output=True, text=True, check=True)
                response = json.loads(returned.stdout)
                self.assertNotIn('execution_correct', response)
                self.assertEqual(json.loads((folder / 'candidate.json').read_text()), dict(program=program, scale='percent'))
            entries = [json.loads(x) for x in (folder / 'executions.jsonl').read_text().splitlines()]
            self.assertEqual([x['execution']['status'] for x in entries], ['executed', 'error'])


class TATQAOfficialScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value = os.environ.get('TATQA_METRIC_DIR')
        if not value:
            raise unittest.SkipTest('pinned official TAT-QA scorer not configured')
        cls.metric_dir = Path(value)

    def test_official_scale_equivalence_mismatch_zero_and_sign(self):
        cases = [
            ('add(10, 12.12)', 'percent', 22.12, 'percent', True, True),
            ('divide(22.12, const_100)', '', 22.12, 'percent', True, False),
            ('add(22.12%, 0)', '', 22.12, 'percent', True, False),
            ('add(22.12%, 0)', 'percent', 22.12, 'percent', False, True),
            ('add(10, 12.12)', '', 22.12, 'percent', False, False),
            ('multiply(123.2, 1000000)', '', 123.2, 'million', True, False),
            ('add(123.2, 0)', 'thousand', 123.2, 'million', False, False),
            ('subtract(2, 2)', '', 0, '', True, True),
            ('subtract(0, 22.12)', 'percent', 22.12, 'percent', False, True),
        ]
        for program, scale, answer, gold_scale, correct, scale_exact in cases:
            with self.subTest(program=program, scale=scale, gold_scale=gold_scale):
                gold = dict(answer_type='arithmetic', answer=answer, scale=gold_scale)
                result = task.grade(dict(program=program, scale=scale), fixture(), gold, metric_dir=self.metric_dir)
                self.assertEqual(result['execution_correct'], correct)
                self.assertEqual(result['official_f1'], float(correct))
                self.assertEqual(result['scale_exact'], scale_exact)

    def test_invalid_submission_and_modified_upstream_cannot_be_scored_as_valid(self):
        gold = dict(answer_type='arithmetic', answer=0, scale='')
        self.assertFalse(task.grade(dict(answer=0), fixture(), gold, metric_dir=self.metric_dir)['program_valid'])
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            for name in task.OFFICIAL_FILES:
                shutil.copyfile(self.metric_dir / name, folder / name)
            with (folder / 'tatqa_metric.py').open('a') as stream:
                stream.write('\n# changed\n')
            with self.assertRaisesRegex(ValueError, 'source changed'):
                task.official_metric_type(folder)


if __name__ == '__main__':
    unittest.main()
