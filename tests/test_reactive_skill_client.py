"""Real operation/state contracts, not evidence of learned-policy effectiveness."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location('reactive_skill_client', ROOT / 'reactive_skill_client.py')
C = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(C)


@pytest.mark.skipif(os.name == 'nt', reason='Owned Linux guest uses fcntl file locks')
def test_parallel_cli_cannot_overwrite_a_completed_world_operation(tmp_path):
    """Reproduce a delayed stale writer, with no network or real model."""
    (tmp_path/'program_memory.json').write_text(json.dumps(dict(mode=0, memory={})))
    (tmp_path/'program.py').write_text("def step(o,m):return {'kind':'yield','memory':m}\n")
    (tmp_path/'tools.json').write_text(json.dumps([dict(function=dict(name='query'))]))
    (tmp_path/'world.json').write_text(json.dumps(dict(done=False, turn=1,
        messages=[dict(role='user', content='initial')], accepted=[])))
    child = r'''
import fcntl, importlib.util, json, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1]); root=Path(sys.argv[2]); who=sys.argv[3]
import reactive_skill_client as c
def rpc(request):
    with (root/'world.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        value=json.loads((root/'world.json').read_text())
        if request['op']=='act':
            if request['turn']!=value['turn']:return {'error':'stale_native_operation'}
            value['accepted'].append(request['arguments']['worker']);value['turn']+=1
            value['messages']=[dict(role='tool',content='accepted',requestor='assistant',error=False)]
            (root/'world.json').write_text(json.dumps(value))
    if request['op']=='observe' and who=='A':
        (root/'a_observed').write_text('ready')
        until=time.monotonic()+1
        while not (root/'b_finished').exists() and time.monotonic()<until:time.sleep(.01)
    return value
c.rpc=rpc
sys.argv=['client',json.dumps(dict(op='act',turn=1,name='query',arguments=dict(worker=who))),'--root',str(root)]
c.main()
if who=='B':(root/'b_finished').write_text('done')
'''
    args=[sys.executable,'-c',child,str(ROOT),str(tmp_path)]
    a=subprocess.Popen(args+['A'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    b=None
    try:
        until=time.monotonic()+5
        while not (tmp_path/'a_observed').exists() and time.monotonic()<until:time.sleep(.01)
        assert (tmp_path/'a_observed').exists()
        b=subprocess.Popen(args+['B'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        aout,aerr=a.communicate(timeout=5);bout,berr=b.communicate(timeout=5)
        assert a.returncode==b.returncode==0,(aout,aerr,bout,berr)
        state=json.loads((tmp_path/'program_memory.json').read_text())
        world=json.loads((tmp_path/'world.json').read_text())
        accepted=[m for m in state['history'] if m['role']=='assistant']
        assert len(world['accepted'])==len(accepted)==1
        assert state['last_turn']==world['turn']==2
        assert accepted[0]['tool_calls'][0]['arguments']['worker']==world['accepted'][0]
    finally:
        for p in [a,b]:
            if p is not None and p.poll() is None:p.kill();p.wait()


class World:
    def __init__(self, terminal_after=20):
        self.turn = 1; self.acts = []; self.terminal_after = terminal_after
    def observation(self):
        if len(self.acts) >= self.terminal_after:
            return {'done': True}
        return dict(done=False, turn=self.turn, messages=[dict(role='user', content='observation ' + str(self.turn))])
    def __call__(self, request):
        if request['op'] == 'observe':
            return self.observation()
        assert request['turn'] == self.turn
        if request['name'] == 'reject':
            return {'error': 'not accepted'}
        self.acts.append(copy.deepcopy(request)); self.turn += 1
        return self.observation()


def policy(observation, memory):
    memory['issued'] = memory.get('issued', 0) + 1
    return dict(kind='act', name='repair', arguments={}, memory=memory)


def test_none_mode_never_calls_policy_and_retains_actual_actor_operation():
    world = World(); state = {'mode': 0}
    def forbidden(*args): raise AssertionError('disabled policy invoked')
    result, state = C.execute(dict(op='act', turn=1, name='actor', arguments={}), world, forbidden, state, ['actor'], lambda x: None)
    assert [x['name'] for x in world.acts] == ['actor']
    assert result['skill']['requested_operation_executed'] is True
    assert [m['role'] for m in state['history']] == ['user', 'assistant', 'user']


@pytest.mark.parametrize('mode', [1, 4])
def test_fragment_displaces_pending_actor_action_and_respects_bound(mode):
    world = World(); rows = []
    result, state = C.execute(dict(op='act', turn=1, name='stale_proposal', arguments={}), world, policy, {'mode': mode}, ['repair'], rows.append)
    assert len(world.acts) == mode == len(rows)
    assert all(x['name'] == 'repair' for x in world.acts)
    assert not result['skill']['requested_operation_executed']
    assert state['memory']['issued'] == mode
    assert len(state['history']) == 1 + 2 * mode


def test_latest_observations_and_own_actual_actions_form_public_history():
    world = World(); seen = []
    def p(o, m):
        seen.append(o['messages'])
        return policy(o, m)
    _, state = C.execute({'op': 'observe'}, world, p, {'mode': 4}, ['repair'], lambda x: None)
    assert [len(x) for x in seen] == [1, 3, 5, 7]
    assert state['history'][1]['tool_calls'][0]['id'] == 'actor-1'


def test_fragment_can_start_after_an_actual_actor_action_returns_feedback():
    def p(o, m):
        if o['turn'] == 1:
            return dict(kind='yield', memory=m)
        return policy(o, m)
    world = World(); rows = []
    result, state = C.execute(dict(op='act', turn=1, name='actor', arguments={}), world, p, {'mode': 4}, ['actor', 'repair'], rows.append)
    assert [x['name'] for x in world.acts] == ['actor'] + ['repair'] * 4
    assert result['skill']['requested_operation_executed'] and len(rows) == 4
    assert state['history_complete'] and len(state['history']) == 11


def test_repeated_observe_does_not_duplicate_history_and_gap_disables_auto():
    state = {'mode': 1}
    o = dict(done=False, turn=1, messages=[dict(role='user', content='start')])
    C.remember(state, o); C.remember(state, o)
    assert len(state['history']) == 1
    world = World(); world.turn = 3
    result, state = C.execute({'op': 'observe'}, world, policy, state, ['repair'], lambda x: None)
    assert not state['history_complete'] and not world.acts
    assert not result['skill']['history_complete']


def test_world_rejection_does_not_commit_planned_memory_or_fabricate_action_history():
    def p(o, m):
        return dict(kind='act', name='reject', arguments={}, memory={'completed': True})
    world = World()
    result, state = C.execute({'op': 'observe'}, world, p, {'mode': 4, 'memory': {}}, ['reject'], lambda x: None)
    assert state['memory'] == {} and len(state['history']) == 1
    assert not result['skill']['actions'][0]['accepted']


def test_native_terminal_stops_fragment_and_say_is_recorded_as_content():
    def p(o, m): return dict(kind='act', name='say', arguments={'message': 'repair'}, memory=m)
    world = World(terminal_after=1)
    result, state = C.execute({'op': 'observe'}, world, p, {'mode': 4}, [], lambda x: None)
    assert result['done'] and len(world.acts) == 1
    assert state['history'][-1] == {'role': 'assistant', 'content': 'repair'}


def test_stale_command_does_not_trigger_policy_or_actor_action():
    world = World()
    result, state = C.execute(dict(op='act', turn=0, name='actor', arguments={}), world, policy, {'mode': 4}, ['repair'], lambda x: None)
    assert result['error'] == 'stale_actor_operation' and not world.acts


def test_nonterminal_stop_and_non_agent_tool_disable_policy_without_fake_success():
    world = World()
    def p(o, m): return dict(kind='stop', memory=m)
    result, state = C.execute({'op': 'observe'}, world, p, {'mode': 4}, [], lambda x: None)
    assert not result['done'] and not world.acts and state['disabled_reason'].startswith('policy_error:')


def test_observation_recording_cannot_mutate_rpc_or_caller_objects():
    state = {}; observation = dict(turn=1, done=False, messages=[dict(role='user', content='x')])
    C.remember(state, observation); state['history'][0]['content'] = 'changed'
    assert observation['messages'][0]['content'] == 'x'
