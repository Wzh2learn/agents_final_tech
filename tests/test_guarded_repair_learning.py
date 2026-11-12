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


class FragmentLearningTest(unittest.TestCase):
    # Deliberately different API names: the learner must recover the field,
    # computation and binding from AST and execution aliases, not task IDs.
    SOURCE = '''class Packet:
    def __init__(self, key, extents=None):
        self.key, self.extents = key, extents

class Factory:
    def build(self, declared, used):
        remembered = {}
        for item in used:
            carrier = item
            sizes = []
            for axis in carrier.axes:
                sizes.append((0, axis - 1))
            metadata = {"extents": sizes}
            remembered[item] = Packet(item, **metadata)
        normalized = []
        for original in declared:
            if isinstance(original, Wrapped):
                normalized.append(original.key)
            else:
                normalized.append(original)
        declared = normalized
        output = []
        for item in declared:
            try:
                output.append(remembered[item])
            except KeyError:
                output.append(Packet(item))
        return output
'''

    def candidates(self, source=None, **options):
        import ast
        from guarded_repair_learning import learn_execution_fragments
        source = source or self.SOURCE
        calls = [n for n in ast.walk(ast.parse(source))
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == 'Packet']
        donor, recipient = sorted(calls, key=lambda n:n.lineno)
        common = dict(runtime_class='Packet', caller_owner='Factory', caller_function='build')
        good = dict(common, caller_line=donor.lineno,
                    arguments={'key': {'type':'Array'}, 'extents': {'type':'list'}},
                    argument_aliases={'key':['item','carrier'], 'extents':['sizes']})
        bad = dict(common, caller_line=recipient.lineno,
                   arguments={'key': {'type':'Array'}, 'extents': {'type':'NoneType'}},
                   argument_aliases={'key':['item']})
        return learn_execution_fragments(source, good, bad, relative_path='api.py', **options)

    def execute(self, candidate):
        from guarded_repair_learning import apply_fragment_edits
        class Array:
            def __init__(self, *axes): self.axes = axes
        class Wrapped:
            def __init__(self, key, *axes): self.key, self.axes = key, axes
        ns={'Wrapped': Wrapped}
        exec(apply_fragment_edits(self.SOURCE, candidate['edits']), ns)
        return ns['Factory'](), Array, Wrapped

    def test_extracts_real_loop_and_preserves_current_scalar_and_used_paths(self):
        candidates=self.candidates()
        self.assertEqual([c['binding'] for c in candidates], ['current','origin'])
        factory,Array,_=self.execute(candidates[0]); arr=Array(4,7); scalar=object()
        values=factory.build([arr,scalar], [])
        self.assertEqual(values[0].extents, [(0,3),(0,6)])
        self.assertIsNone(values[1].extents)
        self.assertEqual(factory.build([arr],[arr])[0].extents, [(0,3),(0,6)])
        self.assertEqual(candidates[0]['field'], 'extents')
        self.assertNotIn('dimensions', candidates[0]['fragment'])

    def test_counterexample_rejects_current_binding_but_origin_handles_each_input(self):
        from guarded_repair_learning import update_fragment_candidates
        candidates=self.candidates()
        outcomes=[]
        for c in candidates:
            factory,Array,Wrapped=self.execute(c)
            a,b=Wrapped('first',2,3),Wrapped('second',5,8)
            result=factory.build((x for x in [a,b]), [])
            passed=[r.extents for r in result]==[[(0,1),(0,2)],[(0,4),(0,7)]]
            outcomes.append({'candidate':c['id'],'case':'two_original_objects','passed':passed})
        state=update_fragment_candidates(candidates, outcomes, required_cases=['two_original_objects'])
        self.assertEqual(state['eligible'], [candidates[1]['id']])
        self.assertEqual(state['rejected'], [candidates[0]['id']])

    def test_origin_collision_abstains_instead_of_using_last_object(self):
        factory,_,Wrapped=self.execute(self.candidates()[1])
        output=factory.build([Wrapped('same',2),Wrapped('same',7)], [])
        self.assertTrue(all(v.extents is None for v in output))

    def test_completed_iteration_counterexample_adds_a_non_null_guard(self):
        factory,_,Wrapped=self.execute(self.candidates()[1])
        unspecified=Wrapped('unspecified');unspecified.axes=None
        with self.assertRaises(TypeError):factory.build([unspecified],[])
        feedback={'completed':True,'operation':'iterate','role_attribute':'axes',
                  'observed_type':'NoneType','exception_type':'TypeError'}
        candidates=self.candidates(execution_feedback=[feedback])
        self.assertEqual(len(candidates),4)
        selected=next(c for c in candidates if c['binding']=='origin' and c['guard_kind']=='not_none')
        factory,_,Wrapped=self.execute(selected)
        unspecified=Wrapped('unspecified');unspecified.axes=None
        self.assertIsNone(factory.build([unspecified],[])[0].extents)
        self.assertEqual(factory.build([Wrapped('array',3,6)],[])[0].extents,[(0,2),(0,5)])
        # Uncompleted or unrelated feedback does not silently create a repair.
        self.assertEqual(len(self.candidates(execution_feedback=[dict(feedback,completed=False)])),2)
        self.assertEqual(len(self.candidates(execution_feedback=[dict(feedback,role_attribute='missing')])),2)

    def test_unknown_and_untested_candidates_are_not_confirmation(self):
        from guarded_repair_learning import update_fragment_candidates
        candidates=self.candidates()
        state=update_fragment_candidates(candidates,[{'candidate':candidates[0]['id'],
                    'case':'source','passed':None}],required_cases=['source','control'])
        self.assertFalse(state['eligible'])
        self.assertEqual(len(state['pending']), 2)
        with self.assertRaisesRegex(ValueError, 'Boolean'):
            update_fragment_candidates(candidates,[{'candidate':candidates[0]['id'],
                'case':'source','passed':1}],required_cases=['source'])

    def test_syntax_scope_and_stale_source_fail_before_editing(self):
        from guarded_repair_learning import apply_fragment_edits, render_fragment_cli
        import tempfile, subprocess
        candidates=self.candidates()
        self.assertEqual(len(candidates),2)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); target=root/'api.py'; target.write_text(self.SOURCE+'\n# changed\n')
            program=root/'skill.py'; program.write_text(render_fragment_cli(candidates[1]),encoding='utf-8')
            before=target.read_bytes()
            run=subprocess.run([sys.executable,str(program),'--root',str(root)],capture_output=True)
            self.assertNotEqual(run.returncode,0)
            self.assertEqual(target.read_bytes(),before)
            target.write_text(self.SOURCE,encoding='utf-8',newline='\n')
            run=subprocess.run([sys.executable,str(program),'--root',str(root)],capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(target.read_text(),apply_fragment_edits(self.SOURCE,candidates[1]['edits']))
            repeated=subprocess.run([sys.executable,str(program),'--root',str(root)],capture_output=True)
            self.assertEqual(repeated.returncode,0,repeated.stderr)
            self.assertIn(b'ALREADY_APPLIED',repeated.stdout)


if __name__=='__main__':unittest.main()
