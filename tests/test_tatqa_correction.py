import json
import os
from contextlib import ExitStack, nullcontext
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

CODE = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'
sys.path.insert(0, str(CODE))
import tatqa_correction as task


def fixture():
    record = dict(table=dict(uid='table-1', table=[['year', 'value'], ['2020', '22.12']]),
                  paragraphs=[dict(text='Public financial context', order=1)])
    question = dict(uid='question-1', question='What is the rate?', answer='HIDDEN_ANSWER',
                    scale='HIDDEN_SCALE', derivation='HIDDEN_DERIVATION', rel_paragraphs=[1])
    return task.public_record(record, question)


def actor_text(text, message='final', part='text-1'):
    return dict(type='text', part=dict(type='text', messageID=message, id=part, text=text))


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

    def test_terminal_cli_submits_declared_program_and_scale_through_real_executor(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp);public = folder / 'public.json';public.write_text(json.dumps(fixture()))
            events = [actor_text('Final program: add(999, 1)', 'old'),
                      actor_text('The report supplies the two quantities.\nFinal program: add(10, 12.12)\nFinal scale: percent')]
            output = folder / 'actor.jsonl';output.write_text('\n'.join(json.dumps(e) for e in events))
            returned = subprocess.run([sys.executable, str(CODE / 'tatqa_correction.py'),
                '--final-jsonl', str(output), '--public', str(public), '--work', str(folder),
                '--executor', str(task.arithmetic.executor().__file__)], capture_output=True, text=True)
            self.assertEqual(returned.returncode, 0, returned.stderr)
            response = json.loads(returned.stdout)
            self.assertEqual(response['status'], 'submitted')
            self.assertEqual(response['execution']['status'], 'executed')
            self.assertAlmostEqual(response['execution']['terminal_execution_answer'], 22.12)
            self.assertEqual(json.loads((folder / 'candidate.json').read_text()),
                             dict(program='add(10, 12.12)', scale='percent'))
            log = [json.loads(line) for line in (folder / 'executions.jsonl').read_text().splitlines()]
            self.assertEqual(len(log), 1)
            self.assertEqual(log[0]['origin'], 'terminal_declaration')
            self.assertNotIn('execution_correct', response['execution'])

    def test_terminal_rejects_absent_or_ambiguous_declarations_without_guessing(self):
        reasoning = dict(type='reasoning', part=dict(type='reasoning', messageID='new', id='r',
                                                    text='Final program: add(1, 2)'))
        cases = [
            [actor_text('Final program: add(2, 2)', 'old'), reasoning],
            [actor_text('Final program: add(1, 2)\nFinal program: add(2, 2)')],
            [actor_text('Final program: add(1, 2)\nFinal scale: percent\nFinal scale: million')],
        ]
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp);before = json.dumps(dict(program='add(3, 3)', scale='percent'))
            (folder / 'candidate.json').write_text(before)
            for events in cases:
                with self.subTest(events=events):
                    result = task.submit_terminal_response(events, fixture(), folder)
                    self.assertEqual(result['status'], 'not_submitted')
                    self.assertEqual((folder / 'candidate.json').read_text(), before)
                    self.assertFalse((folder / 'executions.jsonl').exists())

    def test_terminal_omitted_scale_retains_public_scale_and_explicit_none_clears_it(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / 'candidate.json').write_text(json.dumps(dict(program='add(1, 2)', scale='percent')))
            result = task.submit_terminal_response([actor_text('Final program: add(10, 12.12)')], fixture(), folder)
            self.assertEqual(result['scale'], 'percent')
            self.assertTrue(result['changed'])
            result = task.submit_terminal_response([actor_text(
                'Final program: divide(22.12, const_100)\nFinal scale: none')], fixture(), folder)
            self.assertEqual(result['scale'], '')
            self.assertEqual(json.loads((folder / 'candidate.json').read_text())['scale'], '')
            self.assertAlmostEqual(result['execution']['terminal_execution_answer'], .2212)

    def test_terminal_invalid_predicted_scale_remains_a_failed_submission(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            result = task.submit_terminal_response([actor_text(
                'Final program: add(10, 12.12)\nFinal scale: trillion')], fixture(), folder)
            self.assertEqual(result['execution']['code'], 'UNSUPPORTED_PREDICTED_SCALE')
            saved = json.loads((folder / 'candidate.json').read_text())
            self.assertEqual(saved['scale'], 'trillion')
            grade = task.grade(saved, fixture(), dict(answer_type='arithmetic', answer=22.12, scale='percent'),
                               metric_dir=folder / 'not-mounted')
            self.assertFalse(grade['execution_correct'])
            self.assertFalse(grade['program_valid'])


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

    def test_terminal_submissions_use_the_unchanged_official_scale_scoring(self):
        gold = dict(answer_type='arithmetic', answer=22.12, scale='percent')
        for program, scale in [('add(10, 12.12)', 'percent'), ('divide(22.12, const_100)', 'none')]:
            with self.subTest(program=program, scale=scale), tempfile.TemporaryDirectory() as temp:
                folder = Path(temp)
                task.submit_terminal_response([actor_text(
                    f'Final program: {program}\nFinal scale: {scale}')], fixture(), folder)
                saved = json.loads((folder / 'candidate.json').read_text())
                result = task.grade(saved, fixture(), gold, metric_dir=self.metric_dir)
                self.assertEqual(result['official_em'], 1.)
                self.assertEqual(result['official_f1'], 1.)

    def native_result(self, submission, *, use_tatqa=False, batch=False, exit_code=0):
        """Exercise real host grading with offline actor I/O, never a model score."""
        import run_finqa_correction as study
        import run_finqa_learning_native as native
        public = fixture();order = []
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp);folder = root / 'case'
            for name in ('inputs', 'work', 'dependencies'):
                (folder / name).mkdir(parents=True)
            (folder / 'inputs/public.json').write_text(json.dumps(public))
            (folder / 'inputs/task.txt').write_text('Public test task')
            gold = (dict(answer_type='arithmetic', answer=22.12, scale='percent')
                    if use_tatqa else dict(exe_ans=22.12))
            labels = root / 'LABELS_PRIVATE.json';labels.write_text(json.dumps([gold]))

            class Relay:
                def __init__(self, *args, **kwargs):pass
                def close(self):pass
                def accounting(self):return dict(integrity_passed=True, actual_forwarded_posts=0)

            def actor(*args, **kwargs):
                order.append('actor')
                if set(submission) == {'program', 'scale'}:
                    task.submit_program(submission['program'], submission['scale'], public, folder / 'work')
                else:
                    task.arithmetic.submit_program(submission['program'], public, folder / 'work')
                return dict(exit=exit_code, seconds=0.)

            def grade(candidate, observed, private):
                order.append('grade')
                self.assertEqual(observed, public)
                self.assertEqual(private, gold)
                return task.grade(candidate, observed, private, metric_dir=self.metric_dir)

            h = SimpleNamespace(
                actor=SimpleNamespace(config=lambda *a: {'agent': {'build': {}}},
                                      RUNTIME_ROOT='unused', RUNTIME_SHA='unused'),
                deps=SimpleNamespace(verify_projection=lambda *a: {'runtime': 'offline-runtime'}))
            ep = dict(index=0, id=public['id'], report=public['report'], folder=str(folder),
                      arm='fixed', public_sha256=study.sha(folder / 'inputs/public.json'),
                      task_sha256=study.sha(folder / 'inputs/task.txt'))
            options = dict(submission_grader=grade) if use_tatqa else {}
            with ExitStack() as stack:
                stack.enter_context(patch.object(study.core, 'docker_command', return_value=['offline-actor']))
                stack.enter_context(patch.object(study.core, 'run_owned', side_effect=actor))
                stack.enter_context(patch.object(study.core, 'Relay', Relay))
                if batch:
                    training = root / 'training';training.mkdir()
                    (training / 'RESULT.json').write_text('{}')
                    bound = root / 'bound';bound.write_text('offline resource binding')
                    plan = dict(episodes=[ep], arm_order=['fixed'], training_root=str(training),
                                components={}, terminal_status='OFFLINE_HOST_TEST_RETURNED')
                    for key in ('parent', 'server', 'converter'):
                        plan[key] = str(bound);plan[key + '_sha256'] = study.sha(bound)
                    (root / 'PLAN.json').write_text(json.dumps(plan))
                    stack.enter_context(patch.object(study.core, 'resource_lock', nullcontext))
                    stack.enter_context(patch.object(study.core, 'helpers', return_value=h))
                    stack.enter_context(patch.object(native, 'convert', return_value=None))
                    stack.enter_context(patch.object(native, 'start_server', return_value=(object(), None)))
                    stack.enter_context(patch.object(native, 'stop_server'))
                    native.run(study.sha(root / 'PLAN.json'), root, **options)
                    result = json.loads((root / 'RESULT.json').read_text())['episodes'][0]
                else:
                    result = study.episode(ep, h, {'runtime': 'offline-runtime'}, {},
                                           private_labels=labels, **options)
            for path in (folder / 'inputs').iterdir():
                self.assertNotIn('"official_em"', path.read_text())
                self.assertNotIn('"answer_type"', path.read_text())
            self.assertNotIn('execution_correct', (folder / 'work/executions.jsonl').read_text())
            return result, order

    @unittest.skipUnless(os.name == 'posix', 'native host uses Unix relay sockets')
    def test_native_episode_accepts_scale_only_through_the_explicit_host_grader(self):
        submission = dict(program='add(10, 12.12)', scale='percent')
        legacy, _ = self.native_result(submission)
        self.assertFalse(legacy['native_success'])
        self.assertIsNone(legacy['submitted_program'])
        result, order = self.native_result(submission, use_tatqa=True)
        self.assertEqual(order, ['actor', 'grade'])
        self.assertEqual(result['submitted_program'], submission['program'])
        self.assertTrue(result['native_success'])
        self.assertEqual(result['official_em'], 1.)
        plain, _ = self.native_result(dict(program='add(10, 12.12)'))
        self.assertTrue(plain['native_success'])

    @unittest.skipUnless(os.name == 'posix', 'native host uses Unix relay sockets')
    def test_native_grading_retains_invalid_units_and_failed_completion(self):
        invalid, _ = self.native_result(dict(program='add(10, 12.12)', scale='trillion'), use_tatqa=True)
        self.assertFalse(invalid['native_success'])
        self.assertFalse(invalid['program_valid'])
        failed, _ = self.native_result(dict(program='add(10, 12.12)', scale='percent'),
                                      use_tatqa=True, exit_code=1)
        self.assertEqual(failed['official_em'], 1.)
        self.assertFalse(failed['native_success'])

    @unittest.skipUnless(os.name == 'posix', 'native host uses Unix relay sockets')
    def test_native_batch_passes_the_host_grader_to_every_episode(self):
        result, order = self.native_result(dict(program='divide(22.12, const_100)', scale=''),
                                          use_tatqa=True, batch=True)
        self.assertEqual(order, ['actor', 'grade'])
        self.assertTrue(result['native_success'])
        self.assertEqual(result['official_em'], 1.)


if __name__ == '__main__':
    unittest.main()
