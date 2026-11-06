import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029/run_alfworld_correction_learning_20261106.py'
spec = importlib.util.spec_from_file_location('alf_correction_learning', SCRIPT)
learning = importlib.util.module_from_spec(spec)
spec.loader.exec_module(learning)


def row():
    return {'input_ids': [1, 2, 3, 4, 5, 6], 'attention_mask': [1] * 6,
            'labels': [-100, -100, -100, 4, 5, -100], 'source_role': 'teacher',
            'row_id': 'teacher-one', 'source_group': 'same-exposed-task'}


class CorrectionQualificationTests(unittest.TestCase):
    def test_masks_are_exact_and_training_never_truncates(self):
        self.assertEqual(learning.validate_row(row()), [3, 4])
        changes = [{'labels': [-100] * 6}, {'labels': [1, -100, -100, 4, 5, -100]},
                   {'labels': [-100, -100, 3, -100, 5, -100]}, {'labels': [-100, -100, -100, 9, 5, -100]},
                   {'attention_mask': [1, 1]}, {'source_role': 'student'}, {'source_group': ''}]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                learning.validate_row(dict(row(), **change))
        with mock.patch.dict(learning.CONFIG, {'max_length': 5}), self.assertRaises(ValueError):
            learning.validate_row(row())

    def test_rows_hash_duplicate_ids_and_reservation_are_binding(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'rows.jsonl'
            one, two = row(), dict(row(), row_id='teacher-two')
            path.write_text(json.dumps(one) + '\n' + json.dumps(two) + '\n')
            self.assertEqual(len(learning.load_rows(path, learning.sha(path))), 2)
            with self.assertRaises(ValueError):
                learning.load_rows(path, '0' * 64)
            path.write_text(json.dumps(one) + '\n' + json.dumps(one) + '\n')
            with self.assertRaises(ValueError):
                learning.load_rows(path, learning.sha(path))
            root = Path(folder) / 'attempt_v1'
            root.mkdir()
            (root / 'reservation.json').write_text('{}')
            with mock.patch.object(learning, 'verify', return_value=(root, {}, [])), self.assertRaises(FileExistsError):
                learning.execute(root, 'any')

    def test_execute_cli_cannot_override_training_source(self):
        for extra in [[], ['--manifest-sha', 'a' * 64, '--rows-sha', 'b' * 64]]:
            with self.subTest(extra=extra), mock.patch('sys.stderr'), self.assertRaises(SystemExit):
                learning.main(['--execute', '--run-root', 'unused', *extra])

    def test_export_metadata_cannot_switch_model_rows_source_or_eos(self):
        example = dict(row(), target_token_ids=[4, 5])
        model_files = {'files': [{'path': str(learning.MODEL / 'tokenizer.json'), 'sha256': 'tokenizer-pinned'}]}
        with tempfile.TemporaryDirectory() as folder:
            manifest = Path(folder) / 'data_manifest.json'
            rows = Path(folder) / 'rows.jsonl'
            expected = {'rows_file': 'rows.jsonl', 'rows_sha256': 'rows-pinned', 'row_count': 1,
                        'source_roles': ['teacher'], 'source_groups': ['same-exposed-task'], 'source_group_count': 1,
                        'model_assets': {'model_path': str(learning.MODEL), 'enable_thinking': False,
                                         'files_sha256': {'tokenizer.json': 'tokenizer-pinned'}, 'eos_token_id': 5},
                        'frozen_manifest_sha256': learning.CORRECTIONS_SHA,
                        'provider_manifest_sha256': learning.PROVIDER_MANIFEST_SHA, 'exporter_sha256': 'exporter-pinned'}
            component = str(SCRIPT.with_name('alfworld_correction_data_20261106.py'))
            with mock.patch.object(learning, 'components', return_value={component: 'exporter-pinned'}):
                manifest.write_text(json.dumps(expected))
                learning.validate_export(manifest, learning.sha(manifest), rows, 'rows-pinned', [example], model_files)
                changes = [{'rows_sha256': 'changed'}, {'source_roles': ['teacher', 'student']},
                           {'source_group_count': 2}, {'frozen_manifest_sha256': 'changed'},
                           {'model_assets': dict(expected['model_assets'], model_path='/wrong/model')},
                           {'model_assets': dict(expected['model_assets'], eos_token_id=7)},
                           {'model_assets': dict(expected['model_assets'], files_sha256={'tokenizer.json': 'changed'})}]
                for change in changes:
                    with self.subTest(change=change), self.assertRaises(ValueError):
                        manifest.write_text(json.dumps(dict(expected, **change)))
                        learning.validate_export(manifest, learning.sha(manifest), rows, 'rows-pinned', [example], model_files)

    def test_sparse_masked_causal_loss_and_gradients_match_full_reference(self):
        import torch
        from transformers import Qwen3Config, Qwen3ForCausalLM
        torch.manual_seed(17)
        config = Qwen3Config(vocab_size=32, hidden_size=32, intermediate_size=48,
                    num_hidden_layers=1, num_attention_heads=2, num_key_value_heads=2,
                    head_dim=16, max_position_embeddings=32, attention_dropout=0.0)
        model = Qwen3ForCausalLM(config).float().eval()
        reference = copy.deepcopy(model)
        example = row()
        sparse, logits = learning.sparse_causal(model, example, 'cpu')
        full = reference(input_ids=torch.tensor([example['input_ids']]),
                         attention_mask=torch.ones(1, 6, dtype=torch.long),
                         labels=torch.tensor([example['labels']]), use_cache=False).loss
        self.assertEqual(tuple(logits.shape), (2, 32))
        torch.testing.assert_close(sparse, full, rtol=1e-6, atol=1e-6)
        sparse.backward()
        full.backward()
        for (name, parameter), (other_name, other) in zip(model.named_parameters(), reference.named_parameters()):
            self.assertEqual(name, other_name)
            if parameter.grad is not None:
                torch.testing.assert_close(parameter.grad, other.grad, rtol=2e-5, atol=2e-6)


if __name__ == '__main__':
    unittest.main()
