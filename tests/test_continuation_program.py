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


def test_corrective_option_uses_prior_memory_and_can_execute_a_complete_fragment():
    base="def step(o,m):\n m['node']='transferred'\n return {'kind':'act','name':'transfer','arguments':{},'memory':m}\n"
    option='''def option_step(o,m,p):
    if m.get('option_phase')=='verify':
        return {'kind':'yield','reason':'scope complete; inspect remaining task','memory':m}
    if o.get('blocked'):
        m['option_phase']='verify'
        return {'kind':'act','name':'repair','arguments':{},'memory':m}
    return None
'''
    revised,meta=CP.weave_corrective_option(base,option)
    p=CP.load_program(revised)
    first=CP.public_step(p,{'blocked':True,'done':False},{'node':'before'},['repair','transfer'])
    assert first['name']=='repair' and first['memory']['node']=='before'
    second=CP.public_step(p,{'blocked':False,'done':False},first['memory'],['repair','transfer'])
    assert second['kind']=='yield' and second['memory']['node']=='before'
    assert meta['base_bodies_preserved']


def test_noop_option_cannot_mutate_the_retained_decision_or_nested_memory():
    base="def step(o,m):\n return {'kind':'act','name':'query','arguments':{'n':1},'memory':m}\n"
    option="def option_step(o,m,p):\n o['bad']=True\n m['nested']['x']=9\n p['arguments']['n']=99\n return None\n"
    revised,_=CP.weave_corrective_option(base,option)
    memory={'nested':{'x':1}}
    decision=CP.public_step(CP.load_program(revised),{'done':False},memory,['query'])
    assert decision['arguments']=={'n':1} and decision['memory']==memory


def test_option_constants_cannot_change_existing_base_globals():
    base="OPTION_MODE='query'\ndef step(o,m):\n return {'kind':'act','name':OPTION_MODE,'arguments':{},'memory':m}\n"
    option="OPTION_MODE='transfer'\ndef option_step(o,m,p):\n return None\n"
    with pytest.raises(ValueError):CP.weave_corrective_option(base,option)


def test_terminal_world_never_enters_option_and_illegal_corrections_are_rejected():
    base="def step(o,m):\n return {'kind':'stop','memory':m} if o.get('done') else {'kind':'yield','memory':m}\n"
    option="def option_step(o,m,p):\n return {'kind':'act','name':'private_user_tool','arguments':{},'memory':m}\n"
    revised,_=CP.weave_corrective_option(base,option);p=CP.load_program(revised)
    assert CP.public_step(p,{'done':True},{},[])['kind']=='stop'
    with pytest.raises(ValueError):CP.public_step(p,{'done':False},{},[])


@pytest.mark.parametrize('option',[
    'import os\ndef option_step(o,m,p):return None',
    'def node_start(o,m,p):return None',
    'def option_step(o,m,p):return None\nx=1',
    'def option_step(o,m,p):return None\ndef step(o,m):return None',
    'def option_step(o,m):return None',
])
def test_option_cannot_add_io_collisions_or_unscoped_globals(option):
    with pytest.raises(ValueError):CP.weave_corrective_option(SOURCE,option)


def test_matched_preferences_preserve_failure_ties_and_do_not_fake_unknown_costs():
    common=dict(checkpoint={'public':'same'},model='fixed',caps={'posts':12},public_files={'experience':'same'})
    a=dict(common,native_reward=0,known_tokens=100,unknown=0)
    b=dict(common,native_reward=0,known_tokens=1,unknown=0)
    assert CP.matched_continuation_preference(a,b)=='UNRESOLVED'
    b['native_reward']=1
    assert CP.matched_continuation_preference(a,b)=='CORRECTION'
    a['native_reward']=1;b['unknown']=1
    assert CP.matched_continuation_preference(a,b)=='UNRESOLVED'
    b.update(unknown=0,known_tokens=90)
    assert CP.matched_continuation_preference(a,b)=='TIE'
    b['known_tokens']=70
    assert CP.matched_continuation_preference(a,b)=='CORRECTION'
    b['caps']={'posts':13}
    with pytest.raises(ValueError):CP.matched_continuation_preference(a,b)


def test_frontier_selection_abstains_when_user_feedback_diverged_before_action():
    common=dict(checkpoint={'public':'same'},model='fixed',caps={'posts':12},public_files={})
    a=dict(common,native_reward=0,known_tokens=10,unknown=0,
        public_continuation=[{'role':'user','content':'first state'},{'role':'assistant','content':'retry'}])
    b=dict(common,native_reward=1,known_tokens=10,unknown=0,
        public_continuation=[{'role':'user','content':'different state'},{'role':'assistant','content':'repair'}])
    assert CP.corrective_frontier(a,b) is None
    b['public_continuation'][0]={'role':'user','content':'first state'}
    selected=CP.corrective_frontier(a,b)
    assert selected['preference']=='CORRECTION' and selected['preferred_first_decision']['content']=='repair'
    assert len(selected['common_public_suffix'])==1


def test_option_request_retains_both_complete_suffixes_and_abstains_on_failed_pair():
    common=dict(checkpoint={'public':'same'},model='fixed',caps={'posts':12},public_files={})
    a=dict(common,native_reward=0,known_tokens=10,unknown=0,
        public_continuation=[{'role':'assistant','content':'give up'}])
    b=dict(common,native_reward=1,known_tokens=10,unknown=0,
        public_continuation=[{'role':'assistant','content':'repair'},{'role':'user','content':'resolved'}])
    materials=dict(matched_pair={'continuation':a,'correction':b},program=SOURCE)
    request,selected=CP.option_learning_request(materials,'fixed')
    assert request['tool_choice']['function']['name']=='emit_corrective_option'
    assert 'resolved' in request['messages'][1]['content'] and 'give up' in request['messages'][1]['content']
    b['native_reward']=0
    with pytest.raises(ValueError):CP.option_learning_request(materials,'fixed')


def test_frontier_ignores_wire_ids_but_never_learns_from_private_user_tools():
    common=dict(checkpoint={'public':'same'},model='fixed',caps={'posts':12},public_files={})
    a=dict(common,native_reward=0,known_tokens=10,unknown=0,public_continuation=[
        {'role':'assistant','tool_calls':[{'id':'a','name':'query','arguments':{}}]},
        {'role':'tool','id':'a','requestor':'assistant','content':'same'},
        {'role':'assistant','content':'give up'}])
    b=dict(common,native_reward=1,known_tokens=10,unknown=0,public_continuation=[
        {'role':'assistant','tool_calls':[{'id':'different','name':'query','arguments':{}}]},
        {'role':'tool','id':'different','requestor':'assistant','content':'same'},
        {'role':'assistant','content':'repair'}])
    selected=CP.corrective_frontier(a,b)
    assert len(selected['common_public_suffix'])==2
    assert selected['preferred_first_decision']['content']=='repair'
    b['public_continuation'][1]['requestor']='user'
    with pytest.raises(ValueError):CP.corrective_frontier(a,b)


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
