"""Guest-only local correction around a persistent Actor's world operations.

The same client serves the no-intervention and bounded-fragment conditions.
Generated policies run only inside the owned container; the native world still
checks roles, arguments, turn nonces, task progress and termination.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import socket

from continuation_program import load_program, public_step


def remember(state, observation):
    """Accumulate actual public deltas, detecting a bypassed/missing interval."""
    if observation.get('done') or observation.get('error'):
        return
    turn = observation.get('turn')
    if type(turn) is not int or type(observation.get('messages')) is not list:
        raise ValueError('invalid public observation')
    last = state.get('last_turn')
    if last == turn:
        return
    if last is None:
        state['history'] = copy.deepcopy(observation['messages'])
        state['history_complete'] = turn == 1
    elif turn == last + 1:
        state['history'].extend(copy.deepcopy(observation['messages']))
    else:
        state['history_complete'] = False
        state['history'].extend(copy.deepcopy(observation['messages']))
    state['last_turn'] = turn


def record_action(state, command):
    """The observation delta excludes our own actual assistant operation."""
    if command['name'] == 'say':
        message = dict(role='assistant', content=command['arguments']['message'])
    else:
        message = dict(role='assistant', content=None, tool_calls=[dict(
            id='actor-' + str(command['turn']), name=command['name'],
            arguments=copy.deepcopy(command['arguments']))])
    state['history'].append(message)


def execute(request, rpc, program, state, tool_names, emit_trace):
    """Return truthful state if a correction displaced the Actor's proposal.

    A stale Actor command is never executed after an automatic fragment.
    Planned policy memory is committed only after the world accepted its act.
    ``mode`` is an experimental bound, not a success or exit-utility label.
    """
    if type(request) is not dict or request.get('op') not in {'observe', 'act'}:
        raise ValueError('expected an explicit observe/act request')
    mode = state.get('mode')
    if type(mode) is not int or mode not in (0, 1, 4, 16):
        raise ValueError('unknown frozen intervention bound')
    current = rpc({'op': 'observe'})
    remember(state, current)
    if request['op'] == 'act' and (type(request.get('turn')) is not int
            or request['turn'] != current.get('turn')):
        return dict(error='stale_actor_operation', observation=current), state
    interventions = []
    stop_reason = 'disabled' if mode == 0 else 'not_applicable'

    def act(command, proposed_memory=None):
        nonlocal current
        before = copy.deepcopy(current)
        following = rpc(command)
        accepted = not following.get('error')
        if accepted:
            record_action(state, command)
            if proposed_memory is not None:
                state['memory'] = copy.deepcopy(proposed_memory)
            remember(state, following)
        current = following
        return before, accepted

    def drain(proposal):
        nonlocal stop_reason
        if mode == 0 or state.get('disabled_reason') or not state.get('history_complete'):
            stop_reason = 'disabled_or_incomplete_history'
            return
        while len(interventions) < mode and not current.get('done') and not current.get('error'):
            observation = dict(current, messages=copy.deepcopy(state['history']),
                               proposed_operation=copy.deepcopy(proposal))
            memory = copy.deepcopy(state.get('memory', {}))
            try:
                decision = public_step(program, observation, memory, tool_names)
            except Exception as exc:
                state['disabled_reason'] = 'policy_error: ' + type(exc).__name__ + ': ' + str(exc)
                stop_reason = state['disabled_reason']
                return
            if decision['kind'] != 'act':
                state['memory'] = decision['memory']
                stop_reason = decision.get('reason', decision['kind'])
                return
            command = dict(op='act', turn=current['turn'], name=decision['name'],
                           arguments=decision['arguments'])
            before, accepted = act(command, decision['memory'])
            row = dict(observation=observation, memory_before=memory,
                       decision=decision, command=command, accepted=accepted,
                       following=copy.deepcopy(current))
            emit_trace(row)
            interventions.append(row)
            if not accepted:
                stop_reason = 'world_rejected_skill_operation'
                return
        if current.get('done'):
            stop_reason = 'native_world_terminal'
        elif len(interventions) >= mode:
            stop_reason = 'frozen_fragment_bound'

    # An intervention replaces the stale pending act; it is never followed by it.
    drain(request if request['op'] == 'act' else None)
    executed = request['op'] == 'observe'
    if request['op'] == 'act' and not interventions and not current.get('done') and not current.get('error'):
        _, executed = act(request)
        if executed:
            drain(None)
    reply = dict(current)
    reply['skill'] = dict(mode=mode, actions=[dict(name=x['command']['name'],
        arguments=x['command']['arguments'], accepted=x['accepted']) for x in interventions],
        requested_operation_executed=executed, history_complete=state.get('history_complete', False),
        stop_reason=stop_reason)
    return reply, state


def rpc(request):
    connection = socket.socket(socket.AF_UNIX)
    connection.settimeout(850)
    try:
        connection.connect('/world/s')
        connection.sendall(json.dumps(request, allow_nan=False).encode() + b'\n')
        chunks = []; size = 0
        while True:
            block = connection.recv(65536)
            if not block:
                break
            chunks.append(block); size += len(block)
            if size > 2 * 1024**2:
                raise ValueError('world response exceeds bound')
            if b'\n' in block:
                break
        return json.loads(b''.join(chunks))
    finally:
        connection.close()


def main():
    # OpenCode may launch concurrent Bash tools. The world serializes turns;
    # its public-history cache must serialize the complete read/act/write too.
    import fcntl
    parser = argparse.ArgumentParser()
    parser.add_argument('request', help='Same public JSON operation as world_client.py')
    parser.add_argument('--root', type=Path, default=Path('/workspace'))
    args = parser.parse_args(); root = args.root
    with (root / 'program_memory.lock').open('a') as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        try:
            state_path = root / 'program_memory.json'
            state = json.loads(state_path.read_text())
            program = load_program((root / 'program.py').read_text())
            names = [x['function']['name'] for x in json.loads((root / 'tools.json').read_text())]
            def trace(value):
                with (root / 'reactive_skill.trace.jsonl').open('a') as handle:
                    handle.write(json.dumps(value, allow_nan=False) + '\n')
            result, state = execute(json.loads(args.request), rpc, program, state, names, trace)
            temporary = state_path.with_suffix('.tmp')
            temporary.write_text(json.dumps(state, allow_nan=False))
            temporary.replace(state_path)
            print(json.dumps(result, allow_nan=False))
        finally:
            fcntl.flock(guard, fcntl.LOCK_UN)


if __name__ == '__main__':
    main()
