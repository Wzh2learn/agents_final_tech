"""Signed adapter arithmetic must preserve the effective dense maps."""
import copy
from pathlib import Path
import sys
import unittest

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'))
from feedback_residual import compose


class ExactAdapterTests(unittest.TestCase):
    def setUp(self):
        self.config = dict(peft_type='LORA', bias='none', r=2, lora_alpha=6)
        self.ordinary = {'q.lora_A.weight': torch.tensor([[1., 2., 0.], [0., 1., 3.]]),
                         'q.lora_B.weight': torch.tensor([[2., 0.], [1., 4.]])}
        self.recovery = {'q.lora_A.weight': torch.tensor([[2., 0., 1.], [3., 2., 0.]]),
                         'q.lora_B.weight': torch.tensor([[1., 3.], [0., 2.]])}

    def test_signed_residual_is_difference_of_products_not_factors(self):
        before = {k: v.clone() for k, v in self.ordinary.items()}
        result, cfg = compose(self.ordinary, self.recovery, self.config, self.config, (-1., 1.))
        actual = cfg['lora_alpha'] / cfg['r'] * result['q.lora_B.weight'] @ result['q.lora_A.weight']
        expected = 3 * (self.recovery['q.lora_B.weight'] @ self.recovery['q.lora_A.weight']
                        - self.ordinary['q.lora_B.weight'] @ self.ordinary['q.lora_A.weight'])
        self.assertTrue(torch.equal(actual, expected))
        wrong = 3 * (self.recovery['q.lora_B.weight'] - self.ordinary['q.lora_B.weight']) @ (
            self.recovery['q.lora_A.weight'] - self.ordinary['q.lora_A.weight'])
        self.assertFalse(torch.equal(wrong, expected))
        self.assertTrue(all(torch.equal(before[k], v) for k, v in self.ordinary.items()))

    def test_average_supports_different_original_scales(self):
        other = dict(self.config, lora_alpha=2)
        result, cfg = compose(self.ordinary, self.recovery, self.config, other, (.5, .5))
        expected = 1.5 * self.ordinary['q.lora_B.weight'] @ self.ordinary['q.lora_A.weight'] + .5 * self.recovery['q.lora_B.weight'] @ self.recovery['q.lora_A.weight']
        self.assertTrue(torch.equal(result['q.lora_B.weight'] @ result['q.lora_A.weight'], expected))
        self.assertEqual(cfg['r'], cfg['lora_alpha'])

    def test_mismatch_and_nonfinite_cannot_silently_create_weights(self):
        cases = [dict(self.config, use_dora=True), dict(self.config, alpha_pattern={'q': 4}),
                 dict(self.config, r=3)]
        for cfg in cases:
            with self.assertRaises(ValueError):
                compose(self.ordinary, self.recovery, self.config, cfg, (-1., 1.))
        broken = copy.deepcopy(self.recovery)
        broken['q.lora_A.weight'][0, 0] = float('nan')
        with self.assertRaises(ValueError):
            compose(self.ordinary, broken, self.config, self.config, (-1., 1.))


if __name__ == '__main__':
    unittest.main()
