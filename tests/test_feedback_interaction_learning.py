"""Check gradient semantics before a candidate objective reaches a real actor."""
import importlib.util
from pathlib import Path
import unittest

import torch

PATH = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029/feedback_interaction_learning.py'
SPEC = importlib.util.spec_from_file_location('feedback_interaction_learning', PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
update = MODULE.interaction_update


class InteractionLearningTests(unittest.TestCase):
    def inputs(self, utility=None):
        policy = torch.zeros((1, 2, 2), dtype=torch.float64, requires_grad=True)
        reference = torch.zeros_like(policy, requires_grad=True)
        utility = torch.tensor([[[1., 0.], [0., 1.]]] if utility is None else utility, dtype=torch.float64)
        observed = torch.ones_like(policy, dtype=torch.bool)
        return policy, reference, utility, observed

    def test_native_crossover_moves_both_rows_and_keeps_reference_frozen(self):
        p, r, u, o = self.inputs()
        result = update(p, r, u, o, behavior_clone=0.)
        result['total'].backward()
        self.assertEqual((result['eligible_rows'], result['eligible_pairs']), (2, 1))
        self.assertIsNone(r.grad)
        self.assertTrue(torch.equal(p.grad.sign(), torch.tensor([[[-1., 1.], [1., -1.]]])))

    def test_interaction_cancels_shared_context_and_action_offsets(self):
        p, r, u, o = self.inputs()
        first = update(p, r, u, o, behavior_clone=0.)
        offsets = torch.tensor([[[3., 8.], [5., 10.]]], dtype=torch.float64)
        second = update(p + offsets, r, u, o, behavior_clone=0.)
        self.assertEqual(float(first['interaction'].detach()), float(second['interaction'].detach()))
        self.assertNotEqual(float(first['row'].detach()), float(second['row'].detach()))

    def test_common_failure_does_not_acquire_an_invented_preference(self):
        p, r, u, o = self.inputs([[[1., 0.], [0., 0.]]])
        result = update(p, r, u, o, behavior_clone=0.)
        result['total'].backward()
        self.assertEqual(result['eligible_pairs'], 0)
        self.assertEqual(float(result['interaction'].detach()), 0.)
        self.assertTrue(torch.equal(p.grad[:, 1], torch.zeros_like(p.grad[:, 1])))

    def test_unknown_cell_is_not_a_zero_failure_label(self):
        p, r, u, o = self.inputs()
        o[0, 1, 0] = False
        with self.assertRaisesRegex(ValueError, 'explicit NaN'):
            update(p, r, u, o, behavior_clone=0.)
        u[0, 1, 0] = float('nan')
        result = update(p, r, u, o, behavior_clone=0.)
        result['total'].backward()
        self.assertEqual(result['eligible_pairs'], 0)
        self.assertTrue(torch.isfinite(p.grad).all())
        self.assertTrue(torch.equal(p.grad[:, 1], torch.zeros_like(p.grad[:, 1])))

    def test_coupling_is_nonseparable_in_context_score_coordinates(self):
        p, r, u, o = self.inputs()
        def objective(flat):
            return update(flat.reshape(1, 2, 2), r, u, o, behavior_clone=0.)['total']
        hessian = torch.autograd.functional.hessian(objective, p.detach().flatten())
        self.assertEqual(float(hessian[0, 2]), -2.)
        row_hessian = torch.autograd.functional.hessian(lambda flat: update(
            flat.reshape(1, 2, 2), r, u, o, behavior_clone=0., interaction_weight=0.)['total'], p.detach().flatten())
        self.assertEqual(float(row_hessian[0, 2]), 0.)

    def test_bc_gradient_and_scales_are_explicit(self):
        p, r, u, o = self.inputs()
        bc = torch.tensor(2., requires_grad=True)
        result = update(p, r, u, o, behavior_clone=bc, beta=2.)
        result['total'].backward()
        self.assertEqual(float(bc.grad), 1.)
        for kwargs in ({'beta': 0.}, {'row_weight': -1.}, {'interaction_weight': float('nan')}):
            with self.assertRaises(ValueError):
                update(p, r, u, o, behavior_clone=0., **kwargs)

    def test_boltzmann_relative_reward_target_has_zero_residual(self):
        _, _, u, o = self.inputs()
        reference = torch.log_softmax(torch.zeros_like(u), dim=-1)
        policy = torch.log_softmax(u / 2., dim=-1).requires_grad_()
        result = update(policy, reference, u, o, behavior_clone=0., beta=2.)
        self.assertAlmostEqual(float(result['total'].detach()), 0., places=12)

    def test_all_unknown_outcomes_keep_only_bc(self):
        p, r, u, o = self.inputs()
        u[:] = float('nan')
        o[:] = False
        result = update(p, r, u, o, behavior_clone=3.)
        result['total'].backward()
        self.assertEqual(float(result['total'].detach()), 3.)
        self.assertEqual(result['eligible_rows'], 0)
        self.assertTrue(torch.equal(p.grad, torch.zeros_like(p.grad)))


if __name__ == '__main__':
    unittest.main()
