"""Paired fresh-session continuations using the existing native checkpoint API.

This is a bounded diagnostic, not a learned method. Both arms retain the same
world/public prefix; only a public-policy reminder differs. No writer runs.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import continuation_program as CP

REPO = Path(__file__).resolve().parents[2]
COMMON = ('Use /runtime/bin/python -B /workspace/continuation_client.py for every observe/act, '
          'beginning with {"op":"observe"}; do not call world_client directly. '
          'Continue the customer task from its current public history. Account and device changes '
          'recorded there remain applied. Preserve completed progress and use the official workflow '
          'to finish the remaining goal. No training-history pack is loaded; the initial observation '
          'contains the full public prefix. Final prose alone does not send a message to the customer.')
REMINDER = (' A completed data refuel does not establish that connectivity is restored. '
            'Before escalation, use public feedback to check unresolved prerequisites in the workflow. '
            'Keep confirmed completed steps and do not repeat changes with successful receipts.')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def carrier():
    sys.path.insert(0, str(REPO))
    spec = importlib.util.spec_from_file_location('native_carrier', Path(__file__).with_name('tau2_execution.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def continuation_cut(messages):
    """Bind a successful assistant write receipt, then a real public reply."""
    for index, message in enumerate(messages):
        if message.get('role') != 'assistant':
            continue
        for call in message.get('tool_calls') or []:
            if call.get('name') != 'refuel_data':
                continue
            for receipt_index in range(index + 1, len(messages)):
                receipt = messages[receipt_index]
                if (receipt.get('role') != 'tool' or receipt.get('requestor') != 'assistant'
                        or receipt.get('id') != call.get('id') or receipt.get('error')):
                    continue
                try:
                    result = json.loads(receipt.get('content', ''))
                except (TypeError, ValueError):
                    continue
                if not isinstance(result, dict) or float(result.get('new_data_refueling_gb', 0)) <= 0:
                    continue
                for stop in range(receipt_index + 1, len(messages)):
                    last = messages[stop]
                    if (last.get('role') == 'user' and not last.get('tool_calls')
                            and last.get('content') and not last['content'].strip().startswith('###')):
                        return dict(action_index=index, receipt_index=receipt_index, prefix_length=stop + 1)
    raise ValueError('no successful refuel followed by a nonterminal public user reply')


def prepare(args):
    C = carrier()
    api = C.tau()
    from tau2.agent.base_agent import is_valid_agent_history_message
    original_plan, closed = read(args.source / 'PLAN.json'), read(args.source / 'CLOSEOUT.json')
    assert len(closed['episodes']) == 8 and closed['unstarted'] == 0
    args.root.mkdir(parents=True, exist_ok=False)
    caps = dict(actor_post_cap=16, total_post_cap=48, token_cap=1000000, seconds=600,
        native_steps=120, continue_unfinished_once=True, request_interval_seconds=3, initial_cooldown_seconds=61)
    task_file = Path(original_plan['frozen']['task_file']['path'])
    assert sha(task_file) == original_plan['frozen']['task_file']['sha256']
    tasks = read(task_file)
    tasks = tasks['tasks'] if isinstance(tasks, dict) else tasks
    cases, frozen = [], {}
    for index in range(2):
        parent = args.source / ('dev' + str(index)) / 'simple_protocol'
        raw = read(parent / 'simulation.json')
        cut = continuation_cut(raw['messages'])
        original = api['Task'].model_validate(next(t for t in tasks if t['id'] == raw['task_id']))
        assert not original.evaluation_criteria.nl_assertions
        sim = api['SimulationRun'].model_validate(raw)
        prefix = copy.deepcopy(sim.messages[:cut['prefix_length']])
        runtime = original.model_copy(deep=True)
        runtime.initial_state.message_history = prefix
        folder = args.root / ('case' + str(index)); folder.mkdir()
        write(folder / 'original_task.json', original.model_dump(mode='json'))
        write(folder / 'runtime_task.json', runtime.model_dump(mode='json'))
        public = [C.project_message(m) for m in prefix if is_valid_agent_history_message(m)]
        write(folder / 'public_prefix.json', public)
        direct = api['get_environment'](policy_type='workflow')
        init = runtime.initial_state
        direct.set_state(initialization_data=init.initialization_data,
                         initialization_actions=init.initialization_actions, message_history=prefix)
        probe = folder / 'zero_model_replay'; probe.mkdir()
        class Offline:
            deadline = time.monotonic() + 20
            def call(self, *a, **kw):
                raise AssertionError('no model during checkpoint reconstruction')
        env, agent, world, thread = C.make_world(api, runtime, Offline(), probe, caps, evaluation_task=original)
        observation = agent.observations.get(timeout=10)
        expected = dict(agent_db=direct.get_db_hash(), user_db=direct.get_user_db_hash(),
            public_sha256=hashlib.sha256(json.dumps(public, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest())
        actual = dict(agent_db=env.get_db_hash(), user_db=env.get_user_db_hash(),
            public_sha256=hashlib.sha256(json.dumps(observation['messages'], ensure_ascii=False, separators=(',', ':')).encode()).hexdigest())
        agent.actions.put(None); thread.join(5)
        assert expected == actual and not thread.is_alive()
        write(folder / 'checkpoint.json', actual)
        cases.append(dict(index=index, task_id=original.id, parent=str(parent),
            parent_sha256=sha(parent / 'simulation.json'), **cut, public_messages=len(public),
            excluded_private_user_messages=len(prefix) - len(public)))
        for name in ['original_task.json', 'runtime_task.json', 'public_prefix.json', 'checkpoint.json']:
            p = folder / name
            frozen['case' + str(index) + '_' + p.stem] = dict(path=str(p), sha256=sha(p))
    noop = CP.compile_history_policy("def step(o,m):\n return {'kind':'yield','memory':{}}\n")
    for condition in ['neutral', 'reminder']:
        (args.root / (condition + '.py')).write_text(noop, encoding='utf-8')
    write(args.root / 'POLICY_FREEZE.json', {c:sha(args.root / (c + '.py')) for c in ['neutral','reminder']})
    code = args.root / 'executed_code'; code.mkdir()
    for label, p in dict(driver=Path(__file__), carrier=Path(C.__file__), compiler=Path(CP.__file__),
            client=Path(__file__).with_name('reactive_skill_client.py'),
            gateway=REPO / 'scripts/graph/research_school_gateway.py', task_file=task_file).items():
        frozen[label] = dict(path=str(p), sha256=sha(p))
        if label != 'task_file': shutil.copy2(p, code / (label + '_' + p.name))
    plan = dict(cases=cases, targets=[c['task_id'] for c in cases], conditions=['neutral','reminder'],
        notes=dict(neutral=COMMON, reminder=COMMON + REMINDER), caps=caps, frozen=frozen,
        order={'0':['neutral','reminder'], '1':['reminder','neutral']},
        all_post_cap=192, all_token_cap=4000000, formation_calls=0,
        prior_project_posts=closed['cumulative_posts'], prior_project_known=closed['cumulative_known'],
        prior_unknown_posts=closed['old_unknown_posts'], prior_reserved_tokens=closed['old_unknown_reserve'],
        hypothesis='A valid local effect may leave unresolved work. Test a fixed public-policy reminder at the same replayed state, not a learned method.',
        equivalence='Agent/user database hashes and complete public prefix match within each case. New Actor and User samples remain stochastic; no claim of identical hidden model states.',
        selection='First successful refuel receipt then first nonterminal public user reply, from each frozen simple_protocol source. No suffix, final reward, private user tools or gold added to Actor input.',
        cost='Historical prefix acquisition remains in project ledger, not counted as new physical requests. All continuation roles/failures counted. No historical training pack in either hot context.',
        decision='Both neutral arms succeed or a fixed reminder suffices: do not build a complex selector. Single draws are developmental clues, not confirmation.',
        git_commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip())
    write(args.root / 'PLAN.json', plan)
    print(json.dumps(dict(prepared=True, cases=cases, plan_sha256=sha(args.root / 'PLAN.json'), model_calls=0)), flush=True)


def check(root):
    plan = read(root / 'PLAN.json')
    for item in plan['frozen'].values():
        assert sha(item['path']) == item['sha256'], item['path']
    return plan


def run(args):
    plan = check(args.root)
    assert args.condition in plan['conditions'] and args.index in [0,1]
    folder = args.root / ('case' + str(args.index))
    C = carrier(); api = C.tau()
    original = api['Task'].model_validate_json((folder / 'original_task.json').read_text())
    runtime = api['Task'].model_validate_json((folder / 'runtime_task.json').read_text())
    files = {'program.py':(args.root / (args.condition + '.py')).read_bytes(),
        'continuation_program.py':Path(plan['frozen']['compiler']['path']).read_bytes(),
        'continuation_client.py':Path(plan['frozen']['client']['path']).read_bytes(),
        'program_memory.json':json.dumps(dict(mode=0,memory={})).encode(),
        'experience.txt':b'No training-history pack in either continuation arm.'}
    C.run_one(args.index, prepared=(api,plan['caps'],runtime),
        root_override=args.root / ('dev' + str(args.index)) / args.condition,
        plan_path=args.root / 'PLAN.json', extra_files=files, extra_instruction=plan['notes'][args.condition],
        condition='checkpoint_pair_' + args.condition, evaluation_task=original,
        checkpoint=read(folder / 'checkpoint.json'))


def batch(args):
    plan = check(args.root)
    handle = dict(pid=os.getpid(), start_ticks=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(), started=time.time(),
        argv=sys.argv, plan_sha256=sha(args.root / 'PLAN.json'))
    with (args.root / 'RUN_HANDLE.json').open('x',encoding='utf-8') as f:
        json.dump(handle,f,indent=2)
    key = sys.stdin.readline().strip(); assert key
    results, stopped = [], False
    for index in range(2):
        for condition in plan['order'][str(index)]:
            if (args.root / 'STOP_DISPATCH').exists(): stopped=True; break
            check(args.root)
            charged = [r for p in args.root.rglob('gateway_ledger.json') for r in read(p) if r['state']!='not_sent']
            assert all(r['state']=='complete' and r.get('http_status')==200 and r.get('usage') for r in charged)
            assert len(charged)+48 <= plan['all_post_cap']
            assert sum(r['usage']['total_tokens'] for r in charged)+1000000 <= plan['all_token_cap']
            write(args.root / 'BATCH_LIVE.json',dict(index=index,condition=condition,completed=results,pid=os.getpid()))
            process = subprocess.run([sys.executable,str(Path(__file__)),'run','--root',str(args.root),
                '--index',str(index),'--condition',condition],input=key+'\n',text=True)
            folder=args.root/('dev'+str(index))/condition
            if process.returncode or not (folder/'RESULT.json').exists():
                results.append(dict(index=index,condition=condition,exit=process.returncode));stopped=True;break
            result=read(folder/'RESULT.json')
            native=folder/'native_reward.json'
            record=dict(index=index,condition=condition,result=result,reward=read(native)['reward'] if native.exists() else None)
            results.append(record);print(json.dumps(record),flush=True)
            if result['unknown'] or result['world_thread_alive'] or not native.exists():stopped=True;break
        if stopped:break
    key=None
    write(args.root/'BATCH_RESULT.json',dict(results=results,stopped_early=stopped,finished=time.time()))
    print(json.dumps(dict(batch_terminal=True,episodes=len(results),stopped_early=stopped)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','run','batch'])
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--source',type=Path)
    parser.add_argument('--index',type=int,default=0)
    parser.add_argument('--condition')
    args=parser.parse_args()
    {'prepare':prepare,'run':run,'batch':batch}[args.mode](args)
