"""Analytical learner controls, not Agent performance or method evidence."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'))
from corrective_skill_policy import Context, Segment, Outcome, ConditionalRepairPolicy, preference


def context(arity, *, source='train'):
    return Context('snapshot-' + arity, source, (('feedback_kind','return_mismatch'),('call_arity',arity)))


def outcome(ctx, success, *, tokens=100, regression=True):
    return Outcome(ctx.snapshot,'same-model','same-continuation','same-budget',True,success,regression,tokens)


A=Segment('binding','call-binding',(('python repair_call.py','/workspace'),),'public check passes or return to ordinary correction')
B=Segment('adapter','result-adapter',(('python repair_return.py','/workspace'),),'public check passes or return to ordinary correction')


class PolicyTest(unittest.TestCase):
    def test_cheap_failure_and_target_only_repair_do_not_beat_full_success(self):
        c=context('2'); good=outcome(c,True,tokens=100)
        self.assertEqual(preference(c,good,outcome(c,False,tokens=1)),1)
        self.assertEqual(preference(c,good,outcome(c,True,tokens=1,regression=False)),1)
        self.assertIsNone(preference(c,outcome(c,False,tokens=1),outcome(c,False,tokens=500)))
        self.assertIsNone(preference(c,good,outcome(c,True,tokens=None)))

    def test_invalid_pairing_and_hidden_feature_names_are_rejected(self):
        c=context('2'); r=outcome(c,True)
        with self.assertRaisesRegex(ValueError,'same admitted'):
            preference(c,r,replace(r,snapshot='different-world'))
        with self.assertRaisesRegex(ValueError,'share model'):
            preference(c,r,replace(r,continuation='different-controller'))
        with self.assertRaisesRegex(ValueError,'observable'):
            Context('s','g',(('hidden_target_success','yes'),))
        self.assertIsNone(preference(c,r,replace(r,execution_valid=False)))

    def test_same_feedback_can_learn_opposite_executable_segments(self):
        p=ConditionalRepairPolicy(); one,two=context('1'),context('2')
        self.assertIsNone(p.choose(one,[A,B]))
        for _ in range(30):
            p.update(one,A,B,outcome(one,True),outcome(one,False))
            p.update(two,A,B,outcome(two,False),outcome(two,True))
        self.assertEqual(p.choose(one,[A,B]),A)
        self.assertEqual(p.choose(two,[A,B]),B)
        with self.assertRaisesRegex(ValueError,'source group'):
            p.choose(two,[A,B],heldout=True)
        heldout=replace(two,source_group='new-task')
        before=dict(p.weights)
        self.assertEqual(p.choose(heldout,[A,B],heldout=True),B)
        self.assertEqual(p.weights,before)
        self.assertIsNone(p.choose(context('3',source='unseen-condition'),[A,B]))

    def test_unidentifiable_same_family_pair_does_not_claim_an_update(self):
        c=context('2');p=ConditionalRepairPolicy()
        another=replace(A,identifier='different-executable',commands=(('python another_repair.py','/workspace'),))
        self.assertFalse(p.update(c,A,another,outcome(c,True),outcome(c,False)))
        self.assertEqual(p.updates,0)

    def test_feedback_ablation_does_not_leak_feedback_through_support_gate(self):
        c=context('2');p=ConditionalRepairPolicy(use_feedback=False)
        p.update(c,A,B,outcome(c,True),outcome(c,False))
        changed=replace(c,conditions=(('feedback_kind','different-feedback'),('call_arity','2')))
        self.assertEqual(p.choose(c,[A,B]),p.choose(changed,[A,B]))
        self.assertIsNotNone(p.choose(changed,[A,B]))


if __name__=='__main__': unittest.main()
