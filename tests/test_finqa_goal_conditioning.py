"""Check goal attribution, decision-only scoring, and real gradient directions."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       'research/agent_frontier_portfolio_20261029'))
import finqa_goal_conditioning as goal


class GoalConditioningTests(unittest.TestCase):
    def test_only_question_changes_in_a_matched_pair(self):
        a = dict(id='same', question='growth 2012 to 2013?', table=[['2013', 10]])
        b = dict(a, question='growth 2013 to 2014?')
        goal.validate_goal_pair(a, b)
        for bad in (a, dict(b, id='different'), dict(b, table=[]), dict(b, question='')):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                goal.validate_goal_pair(a, bad)

    def test_program_first_preserves_financial_explanation(self):
        original = dict(role='assistant', content='2013 cost was 6,175 million.\nThe decline is 11.4%.', tool_calls=[])
        before = copy.deepcopy(original)
        program = 'subtract(5469, 6175), divide(#0, 6175)'
        target = goal.program_first_target(original, program)
        self.assertEqual(original, before)
        self.assertEqual(target['content'], 'Final program: '+program+'\n\n'+original['content'])
        self.assertEqual(goal.program_first_target(target, program), target)

    def test_mask_excludes_same_expression_in_prompt_and_later_reasoning(self):
        program = 'add(1, 2)'
        content = 'Final program: '+program+'\n\nExplanation also contains '+program+'.'
        rendered = 'user: old '+program+'\nassistant: '+content+'\nEOS'
        start = rendered.index(content)
        row = dict(input_ids=list(range(len(rendered))),
                   labels=[-100]*start+list(range(start, len(rendered))),
                   prompt_token_count=start)
        offsets = [(i, i+1) for i in range(len(rendered))]
        selected = goal.program_positions(rendered, {'content': content}, row, offsets, program)
        self.assertEqual(''.join(rendered[i] for i in selected), program)
        self.assertLess(max(selected), rendered.index('\n\n', start))
        with self.assertRaises(ValueError):
            goal.program_positions(rendered, {'content': content}, row, offsets[:-1], program)
        row['labels'][selected[0]] = -100
        with self.assertRaises(ValueError):
            goal.program_positions(rendered, {'content': content}, row, offsets, program)

    def test_coupled_loss_cancels_goal_independent_program_bias(self):
        import torch
        scores = torch.tensor([[0.6, -0.4], [-0.2, 0.7]], dtype=torch.float64)
        bias = torch.tensor([[3.0, -2.0]], dtype=torch.float64, requires_grad=True)
        base = goal.contrast_loss(scores, mode='coupled')
        changed = goal.contrast_loss(scores+bias, mode='coupled')
        self.assertTrue(torch.allclose(base, changed, atol=1e-12))
        changed.backward()
        self.assertTrue(torch.equal(bias.grad, torch.zeros_like(bias)))
        self.assertFalse(torch.allclose(goal.contrast_loss(scores, mode='independent'),
                                        goal.contrast_loss(scores+bias, mode='independent')))

    def test_both_modes_send_gradients_to_all_four_choices(self):
        import torch
        for mode in ('coupled', 'independent'):
            scores = torch.zeros((2, 2), requires_grad=True)
            goal.contrast_loss(scores, mode=mode).backward()
            self.assertLess(float(scores.grad[0, 0]), 0)
            self.assertLess(float(scores.grad[1, 1]), 0)
            self.assertGreater(float(scores.grad[0, 1]), 0)
            self.assertGreater(float(scores.grad[1, 0]), 0)
        with self.assertRaises(ValueError):
            goal.contrast_loss(torch.zeros((2, 3)), mode='coupled')
        with self.assertRaises(ValueError):
            goal.contrast_loss(torch.zeros((2, 2)), mode='invalid')

    def test_causal_program_score_has_no_prompt_or_explanation_gradient(self):
        import torch
        logits = torch.zeros((1, 6, 4), requires_grad=True)
        row = dict(input_ids=[0, 1, 2, 3, 1, 0], labels=[-100, -100, 2, 3, 1, 0],
                   program_positions=[2, 3])
        score = goal.program_score(logits, row)
        self.assertAlmostEqual(float(score.detach()), -1.38629436, places=6)
        score.backward()
        active = [i for i in range(6) if bool(logits.grad[0, i].any())]
        self.assertEqual(active, [1, 2])
        self.assertGreater(float(logits.grad[0, 1, 2]), 0)
        for bad in ([0], [1], [2, 2], [], [7]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                goal.program_score(logits, dict(row, program_positions=bad))


if __name__ == '__main__':
    unittest.main()
