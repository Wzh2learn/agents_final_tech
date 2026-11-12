"""Execution/patch boundaries; these checks do not establish learned utility."""
import ast
import importlib.util
from pathlib import Path

import pytest

PATH=Path(__file__).resolve().parents[1]/'research/agent_frontier_portfolio_20261029/continuation_program.py'
SPEC=importlib.util.spec_from_file_location('continuation_program',PATH)
CP=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(CP)
SOURCE='''def node_start(o,m):
    m['node']='wait'
    return {'kind':'act','name':'say','arguments':{'message':'Please check the signal.'},'memory':m}
def step(o,m):
    return node_start(o,m)
'''


def test_program_receives_copies_and_emits_a_public_operation():
    memory={'phone':'555-0100'}; observation={'turn':3,'done':False}
    result=CP.public_step(CP.load_program(SOURCE),observation,memory,[])
    assert memory=={'phone':'555-0100'} and observation=={'turn':3,'done':False}
    assert result['memory']['node']=='wait' and result['name']=='say'


def test_already_bound_standard_imports_and_reverse_iteration_do_not_need_io():
    source="import json, re\ndef step(o,m):\n    m['last']=list(reversed(o['values']))[0]\n    return {'kind':'yield','memory':m}\n"
    result=CP.public_step(CP.load_program(source),{'values':[1,2]},{},[])
    assert result['memory']['last']==2


@pytest.mark.parametrize('decision',[
    {'kind':'act','name':'user_device_toggle','arguments':{},'memory':{}},
    {'kind':'stop','memory':{}},
    {'kind':'act','name':'say','arguments':{'message':42},'memory':{}},
    {'kind':'yield','memory':{'x':float('nan')}},
])
def test_rejects_illegal_role_completion_and_invalid_data(decision):
    with pytest.raises(ValueError):CP.public_step(lambda o,m:decision,{'done':False},{},['get_line'])


def test_local_refinement_preserves_other_handlers_and_adds_a_new_state():
    replacement="def node_start(o,m):\n    return node_probe(o,m)\n"
    addition="def node_probe(o,m):\n    return {'kind':'yield','reason':'need new public evidence','memory':m}\n"
    revised,meta=CP.refine_state(SOURCE,'node_start',replacement,[addition])
    old=ast.parse(SOURCE);new=ast.parse(revised)
    old_router=next(n for n in old.body if n.name=='step')
    new_router=next(n for n in new.body if n.name=='step')
    assert [ast.dump(n) for n in old_router.body]==[ast.dump(n) for n in new_router.body[-len(old_router.body):]]
    assert meta['added_states']==['node_probe'] and CP.load_program(revised)({}, {})['kind']=='yield'


def test_added_control_state_is_reachable_on_the_following_decision():
    replacement="def node_start(o,m):\n    m['node']='probe'\n    return {'kind':'act','name':'say','arguments':{'message':'Check the signal'},'memory':m}\n"
    addition="def node_probe(o,m):\n    return {'kind':'yield','reason':'received new feedback','memory':m}\n"
    revised,_=CP.refine_state(SOURCE,'node_start',replacement,[addition])
    program=CP.load_program(revised)
    first=CP.public_step(program,{'done':False},{},[])
    second=CP.public_step(program,{'done':False},first['memory'],[])
    assert second['reason']=='received new feedback'


def test_edited_state_overrides_original_inline_yield_but_keeps_terminal_guard():
    source="def node_done(o,m):\n return {'kind':'yield','memory':m}\ndef step(o,m):\n if o.get('done'): return {'kind':'stop','memory':m}\n node=m.get('node','start')\n if node=='done': return {'kind':'yield','memory':m}\n return {'kind':'yield','memory':m}\n"
    replacement="def node_done(o,m):\n return {'kind':'act','name':'say','arguments':{'message':'Continue correcting'},'memory':m}\n"
    revised,_=CP.refine_state(source,'node_done',replacement)
    p=CP.load_program(revised)
    assert CP.public_step(p,{'done':False},{'node':'done'},[])['kind']=='act'
    assert CP.public_step(p,{'done':True},{'node':'done'},[])['kind']=='stop'


def test_packed_new_helpers_are_preserved_without_becoming_control_states():
    addition="def is_good(x):\n return x==1\ndef node_probe(o,m):\n return {'kind':'yield','memory':m}\n"
    revised,meta=CP.refine_state(SOURCE,'node_start',"def node_start(o,m):\n return node_probe(o,m)\n",[addition])
    assert meta['added_states']==['node_probe'] and 'is_good' in meta['added_functions']
    assert CP.load_program(revised)({}, {})['kind']=='yield'


@pytest.mark.parametrize('source',[
    'import os\ndef step(o,m): return {}',
    "x=sum(range(100))\ndef step(o,m): return {}",
    "def step(o,m): return o.__class__",
    "def step(o=open('x'),m=None): return {}",
])
def test_rejects_non_controller_top_level_execution(source):
    with pytest.raises((ValueError,SyntaxError)):CP.check_source(source)


def test_patch_cannot_replace_multiple_or_existing_state_functions():
    with pytest.raises(ValueError):CP.refine_state(SOURCE,'node_start','def node_start(o,m):return {}\ndef step(o,m):return {}')
    with pytest.raises(ValueError):CP.refine_state(SOURCE,'node_start','def node_start(o,m):return {}',['def step(o,m):return {}'])


def test_effect_counterexample_locates_an_unread_committed_field():
    source="def node_quota(o,m):\n d=json.loads(o['messages'][-1]['content'])\n return d.get('used',0)>d.get('limit',0)\ndef step(o,m):return {}\n"
    def entry(node,data,decision):
        import json
        return {'memory_before':{'node':node},'observation':{'messages':[{'role':'tool','requestor':'assistant','error':False,'content':json.dumps(data)}]},'decision':decision}
    offer={'kind':'act','name':'say','arguments':{'message':'Buy more?'},'memory':{}}
    trace=[entry('quota',{'used':11,'limit':10,'credit':0},offer),
           entry('committed',{'new_credit':2},{'kind':'act','name':'say','arguments':{'message':'Check again'},'memory':{}}),
           entry('quota',{'used':11,'limit':10,'credit':2},offer)]
    cases=CP.effect_counterexamples(source,trace)
    assert len(cases)==1 and cases[0]['target']=='node_quota'
    assert cases[0]['unread_effect_fields']==['credit']
    assert cases[0]['before_index']==0 and cases[0]['after_index']==2
    assert cases[0]['effect_receipt_indices']==[1]


def test_metadata_change_without_a_matching_effect_witness_is_not_a_counterexample():
    source="def node_quota(o,m):return o.get('used',0)\ndef step(o,m):return {}\n"
    trace=[]
    for label in ['old','new']:
        import json
        trace.append({'memory_before':{'node':'quota'},'observation':{'messages':[{'role':'tool','content':json.dumps({'used':1,'description':label})}]},'decision':{'kind':'yield','memory':{}}})
    assert CP.effect_counterexamples(source,trace)==[]
    with pytest.raises(ValueError,match='abstain'):
        CP.feedback_update_request({'program':source,'failure_trace':trace},localized=True,model='test-model')


def test_feedback_writer_uses_only_the_supplied_public_material_and_declared_cap():
    material={'program':SOURCE,'failure_trace':[],'public_success':{'outcome':1}}
    request,selected=CP.feedback_update_request(material,localized=False,model='test-model')
    import json
    assert json.loads(request['messages'][1]['content'])==material
    assert request['model']=='test-model' and request['max_tokens']==32768
    assert request['tool_choice']['function']['name']=='emit_revision' and selected is None
