"""Offline timing controls; handwritten policies, no models or services."""
import ast
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'research/agent_frontier_portfolio_20261029'


def module(name):
    spec = importlib.util.spec_from_file_location(name, BASE / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


CP = module('continuation_program')
PHASE = module('policy_deployment')


class DeploymentControls(unittest.TestCase):
    def test_memory_and_pending_operation_semantics(self):
        source = "def step(o,m):\n m['called']=True\n return {'kind':'act','name':'inspect','arguments':{},'memory':m}\n"
        for phase, pending, kind in [('both', None, 'act'), ('both', {}, 'act'),
                ('pre', None, 'act'), ('pre', {}, 'yield'),
                ('post', None, 'yield'), ('post', {}, 'act')]:
            with self.subTest(phase=phase, pending=pending):
                revised, _ = PHASE.gate_deployment(source, phase)
                decision = CP.public_step(CP.load_program(revised),
                    {'done': False, 'proposed_operation': pending}, {}, ['inspect'])
                self.assertEqual(decision['kind'], kind)
                self.assertEqual(decision['memory'], {'called': True} if kind == 'act' else {})

    def test_only_one_equal_length_literal_changes_and_terminal_is_preserved(self):
        source = "def step(o,m):\n return {'kind':'stop' if o.get('done') else 'yield','memory':m}\n"
        normalized, sizes = [], []
        for phase in ['both', 'pre', 'post']:
            revised, meta = PHASE.gate_deployment(source, phase)
            tree = ast.parse(revised)
            sizes.append(len(revised.encode()))
            constant = next(n for n in tree.body if isinstance(n, ast.Assign)
                and n.targets[0].id == 'DEPLOYMENT_PHASE')
            constant.value = ast.Constant(0)
            normalized.append(ast.dump(tree))
            self.assertTrue(meta['policy_body_preserved'])
            self.assertEqual(CP.public_step(CP.load_program(revised), {'done': True}, {}, [])['kind'], 'stop')
        self.assertEqual(len(set(sizes)), 1)
        self.assertEqual(len(set(normalized)), 1)

    def test_ambiguous_entries_and_unknown_phase_are_rejected(self):
        for source, phase in [
            ('def step(o,m): return step(o,m)', 'pre'),
            ('DEPLOYMENT_PHASE=1\ndef step(o,m): return {}', 'post'),
            ('def step(o,m): return {}\ndef step(o,m): return {}', 'both'),
            ('def step(o,m): return {}', 'invalid')]:
            with self.subTest(phase=phase, source=source), self.assertRaises(ValueError):
                PHASE.gate_deployment(source, phase)


if __name__ == '__main__':
    unittest.main()
