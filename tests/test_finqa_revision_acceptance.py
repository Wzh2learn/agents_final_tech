"""Public execution gates and reference-relative correction evidence."""
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/agent_frontier_portfolio_20261029'))
import finqa_revision_acceptance as m


class RevisionAcceptanceTests(unittest.TestCase):
    def test_public_gate_never_uses_hidden_correctness(self):
        old={'status':'executed','terminal_execution_answer':1,'correct':False}
        new={'status':'executed','terminal_execution_answer':2,'correct':True}
        self.assertEqual(m.public_gate(old,new),'score')
        old['correct'],new['correct']=True,False
        self.assertEqual(m.public_gate(old,new),'score')
        self.assertEqual(m.public_gate(old,dict(status='error')),'retain')
        self.assertEqual(m.public_gate(dict(status='error'),new),'accept')
        self.assertEqual(m.public_gate(dict(status='error'),dict(status='error')),'retain')
        new['terminal_execution_answer']=1
        self.assertEqual(m.public_gate(old,new),'retain')
        with self.assertRaises(ValueError):m.public_gate(dict(status='unknown'),new)

    def test_reference_cancels_shared_proposal_preference(self):
        negative=dict(first_margin=2.,old_sum=-8.,new_sum=-7.,old_mean=-2.,new_mean=-1.)
        reference=dict(first_margin=3.,old_sum=-4.,new_sum=-2.,old_mean=-1.,new_mean=-.5)
        scores=m.advantages(negative,reference)
        self.assertEqual(scores['negative_first'],2.)
        self.assertEqual(scores['relative_first'],-1.)
        self.assertEqual(scores['relative_sequence_sum'],-1.)
        self.assertEqual(scores['relative_sequence_mean'],.5)
        self.assertFalse(m.accept('score',scores['relative_first']))
        self.assertFalse(m.accept('score',0.))
        self.assertTrue(m.accept('score',.01))
        self.assertTrue(m.accept('accept',None))
        self.assertFalse(m.accept('retain',None))
        for bad in (math.nan,math.inf,-math.inf):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):m.accept('score',bad)

    def test_canonical_tool_target_preserves_the_program(self):
        import finqa_learning_controls as c
        program='subtract(10, 2), divide(#0, 2)'
        target=m.tool_target(program)
        self.assertEqual(c.program_of(target),program)
        self.assertEqual(target['content'],'')
        self.assertNotIn('reference',str(target))


if __name__=='__main__':unittest.main()
