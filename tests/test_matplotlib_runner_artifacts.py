"""Deterministic protections for generated Matplotlib evaluation artifacts."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'))
import run_swe_contextbench_matplotlib_20261106 as runner


class CandidateArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.clean = self.root / 'clean'
        self.work = self.root / 'work'
        self.clean.mkdir()
        self.work.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def make_symlink(self, path, target):
        try:
            path.symlink_to(target)
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows has no symlink privilege; exercised by the GB10 suite')
            raise

    def test_generated_image_link_recorded_and_other_link_rejected(self):
        image = self.work / 'result_images/test/plot-expected.png'
        image.parent.mkdir(parents=True)
        self.make_symlink(image, '/root/lib/mpl_toolkits/tests/baseline_images/test/plot.png')
        report = runner.inspect_candidate_artifacts(self.work, self.clean)
        self.assertEqual(report['excluded_root'], 'result_images')
        self.assertEqual(report['excluded_symlinks'], [{'path': 'result_images/test/plot-expected.png', 'target': '/root/lib/mpl_toolkits/tests/baseline_images/test/plot.png'}])
        self.assertEqual(report['unresolved_symlinks'], [])
        self.assertEqual(runner.candidate_manifest(self.work)['result_images/test/plot-expected.png']['target'], '/root/lib/mpl_toolkits/tests/baseline_images/test/plot.png')
        nested_code = self.work / 'result_images/test/research.py'
        nested_code.write_text('real code edit')
        artifacts = runner.inspect_candidate_artifacts(self.work, self.clean)
        self.assertNotIn('result_images/test/research.py', artifacts['excluded_files'])
        cache = set(artifacts['excluded_files']) | {x['path'] for x in artifacts['excluded_symlinks']}
        self.assertIn('result_images/test/research.py', runner.source_tree(self.work, set(), cache))
        self.make_symlink(self.work / 'code.py', '/root/code.py')
        report = runner.inspect_candidate_artifacts(self.work, self.clean)
        self.assertEqual(report['unresolved_symlinks'][0]['path'], 'code.py')

    def test_frozen_or_symlinked_cache_is_not_excluded(self):
        (self.clean / 'result_images').mkdir()
        image = self.work / 'result_images/test.png'
        image.parent.mkdir()
        self.make_symlink(image, '/root/baseline.png')
        report = runner.inspect_candidate_artifacts(self.work, self.clean)
        self.assertIsNone(report['excluded_root'])
        self.assertEqual(report['unresolved_symlinks'][0]['path'], 'result_images/test.png')
        image.unlink()
        image.parent.rmdir()
        (self.clean / 'result_images').rmdir()
        self.make_symlink(self.work / 'result_images', '/root/not-a-cache')
        report = runner.inspect_candidate_artifacts(self.work, self.clean)
        self.assertIsNone(report['excluded_root'])
        self.assertEqual(report['unresolved_symlinks'][0]['path'], 'result_images')

    def test_source_revision_is_bound_to_frozen_raw_and_manifest(self):
        case = self.root / 'source__none__seed7'
        case.mkdir()
        work = case / 'work'
        work.mkdir()
        (work / 'candidate.py').write_text('candidate')
        raw = case / 'raw.jsonl'
        raw.write_text('original raw')
        completed = self.root / 'source__none__seed7.completed.json'
        completed.write_text(json.dumps({'post_run_evaluation': {'status': 'UNRESOLVED_SYMLINK'}}))
        out = case / runner.POSTHOC_NAME
        out.mkdir()
        manifest = json.dumps(runner.candidate_manifest(work), sort_keys=True,
                              separators=(',', ':'), ensure_ascii=False).encode('utf8') + b'\n'
        for name in ('candidate_manifest_before.json', 'candidate_manifest_after.json'):
            (out / name).write_bytes(manifest)
        metrics = {}
        for name in ('focus', 'regression', 'issue_probe'):
            log = out / (name + '.log')
            log.write_text(name)
            metrics[name] = {'log_sha256': runner.sha(log)}
        revision = {'scope': 'POSTHOC_GENERATED_IMAGE_ARTIFACT_RECHECK',
                    'original_completed_sha256': runner.sha(completed),
                    'original_raw_sha256': runner.sha(raw), 'candidate_unchanged': True,
                    'original_completed_unchanged': True, 'original_raw_unchanged': True,
                    'candidate_manifest_before_sha256': hashlib.sha256(manifest).hexdigest(),
                    'candidate_manifest_after_sha256': hashlib.sha256(manifest).hexdigest(),
                    'model_calls': 0, 'result': {'status': 'EVALUATED', **metrics}}
        (out / 'receipt.json').write_text(json.dumps(revision))
        self.assertEqual(runner.source_revision(self.root, 7)[0], revision)
        raw.write_text('tampered raw')
        with self.assertRaises(ValueError):
            runner.source_revision(self.root, 7)

    def test_source_episode_requires_frozen_actor_projection_and_mounts(self):
        eid = 'source__none__seed7'
        harness = self.root / (eid + '.harness.py')
        harness.write_text(f'type=bind,src={runner.ACTOR_DEPS}/deps/source,dst=/deps,readonly\n'
                           f'type=bind,src={runner.ACTOR_DEPS}/runtime,dst=/extra,readonly\n')
        started = self.root / (eid + '.started.json')
        started.write_text(json.dumps({'harness_sha256': runner.sha(harness),
                                       'actor_projection_sha256': runner.ACTOR_DEPS_SHA}))
        completed = self.root / (eid + '.completed.json')
        record = {'status': 'COMPLETED', 'started_sha256': runner.sha(started),
                  'harness_sha256': runner.sha(harness)}
        for value in (None, 'wrong'):
            record['actor_projection_sha256'] = value
            completed.write_text(json.dumps(record))
            with self.assertRaises(ValueError):
                runner.verify_source_actor_projection(self.root, 7)
        record['actor_projection_sha256'] = runner.ACTOR_DEPS_SHA
        completed.write_text(json.dumps(record))
        self.assertEqual(runner.verify_source_actor_projection(self.root, 7)['status'], 'COMPLETED')

    def test_evaluation_directory_never_overwrites(self):
        out = runner.new_evaluation_dir(self.root, 'recheck')
        sentinel = out / 'receipt.json'
        sentinel.write_text('preserve')
        with self.assertRaises(FileExistsError):
            runner.new_evaluation_dir(self.root, 'recheck')
        self.assertEqual(sentinel.read_text(), 'preserve')


if __name__ == '__main__':
    unittest.main()
