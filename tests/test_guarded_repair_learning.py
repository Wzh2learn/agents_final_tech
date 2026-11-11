"""Analytical controls only; real source/target performance is reported separately."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/agent_frontier_portfolio_20261029'))
from guarded_repair_learning import learn_guard,compile_guarded_block,compile_guarded_predicate,GuardedChoice


class GuardTest(unittest.TestCase):
    def test_predicate_compilation_preserves_unrelated_unicode_and_branch_bodies(self):
        source='def f(对象):\n    if not 对象:\n        return "replace"\n    return "join"\n'
        g=GuardedChoice('empty_columns','then','rest',(),1)
        output=compile_guarded_predicate(source,function_name='f',anchor_test='not 对象',
            predicate_bindings={'empty_columns':'对象.cols == 0'},choice=g)
        self.assertEqual(output,source.replace('not 对象','对象.cols == 0'))
    def test_complementary_failures_can_produce_a_guard(self):
        rows=[dict(case='unary',features={'operand_none':True},success={'original':False,'partial':True}),
              dict(case='binary',features={'operand_none':False},success={'original':True,'partial':False})]
        g=learn_guard(rows)
        self.assertEqual((g.predicate,g.when_true,g.when_false),('operand_none','partial','original'))
        source='def f(x, operand=None):\n    if x is not None:\n        return x + operand\n    return None\n'
        output=compile_guarded_block(source,function_name='f',anchor_test='x is not None',
            candidate_blocks={'original':'return x + operand','partial':'return x * 2'},
            predicate_bindings={'operand_none':'operand is None'},choice=g)
        ns={};exec(output,ns)
        self.assertEqual(ns['f'](3),6)
        self.assertEqual(ns['f'](3,4),7)
        self.assertIsNone(ns['f'](None))

    def test_globally_good_fragment_does_not_invent_conditional_gain(self):
        rows=[dict(case='a',features={'p':True},success={'safe':True,'other':False}),
              dict(case='b',features={'p':False},success={'safe':True,'other':True})]
        self.assertIsNone(learn_guard(rows).predicate)

    def test_common_failure_and_unseparable_conditions_are_not_forced(self):
        rows=[dict(case='a',features={'p':True},success={'a':False,'b':False})]
        self.assertIsNone(learn_guard(rows))
        rows=[dict(case='a',features={'p':True},success={'a':True,'b':False}),
              dict(case='b',features={'p':True},success={'a':False,'b':True})]
        self.assertIsNone(learn_guard(rows))
        rows[1]['features']['p']=None
        with self.assertRaisesRegex(ValueError,'unknown'):
            learn_guard(rows)


if __name__=='__main__':unittest.main()
