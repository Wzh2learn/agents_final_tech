"""Bounded source formation and isolated replay for binding_update.

No native Agent episodes are launched here. Source labels are extracted with
the existing native evaluator; generated policies run only inside Docker.
Paths are explicit arguments, and credentials enter through stdin only.
"""
import argparse
import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import binding_update as B
import continuation_program as CP

IMAGE = 'sha256:364db321fcc720859537bc04fab5c06a3be6ad0c87686a380b015a0d36c232ca'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(args):
    """Freeze exposed source feedback; do not open any future target body."""
    sys.path.insert(0, str(args.repo))
    C = load('native_carrier', Path(__file__).with_name('tau2_execution.py'))
    api = C.tau()
    from tau2.agent.llm_agent import is_valid_agent_history_message
    source, timing, root = args.source, args.timing, args.root
    root.mkdir(parents=True, exist_ok=False)
    examples = read(source / 'examples.json')
    old = read(source / 'materials.json')
    sources = old['sources']
    provenance = []
    task_file = C.ROOT / 'upstream/data/tau2/domains/telecom/tasks.json'
    tasks = read(task_file)
    if isinstance(tasks, dict):
        tasks = tasks['tasks']
    for relative in ['dev0/both_r0', 'dev0/pre_r1']:
        episode = timing / relative
        sim = api['SimulationRun'].model_validate_json((episode / 'simulation.json').read_text())
        task = api['Task'].model_validate(next(t for t in tasks if t['id'] == sim.task_id))
        assert not task.evaluation_criteria.nl_assertions
        positions = [i for i, m in enumerate(sim.messages) if m.role == 'assistant']
        hits = [i for i in positions if any(c.name == 'refuel_data' for c in (sim.messages[i].tool_calls or []))]
        assert len(hits) == 1
        start = hits[0]
        stop = next((i for i in positions if i > start), len(sim.messages))
        def effects(cut):
            partial = sim.model_copy(deep=True, update={'messages': sim.messages[:cut]})
            value = api['evaluate_simulation'](partial, task, api['EvaluationType'].ENV,
                                             False, 'telecom-workflow')
            return {r.env_assertion.func_name: r.met for r in value.env_assertions}
        before, after = effects(start), effects(stop)
        message = sim.messages[start]
        assert len(message.tool_calls) == 1
        call = message.tool_calls[0]
        public = [C.project_message(m) for m in sim.messages[:start]
                  if is_valid_agent_history_message(m)]
        observation = dict(messages=public, turn=positions.index(start), done=False,
                           proposed_operation=None)
        identity = 'timing:' + relative
        example = dict(id=identity, source=identity, executor='actor', observation=observation,
            command=dict(name=call.name, arguments=call.arguments),
            gained=[k for k in before if after[k] and not before[k]],
            lost=[k for k in before if before[k] and not after[k]])
        assert example['gained'] and not example['lost']
        examples.append(example)
        sources.append(dict(source=identity, public_messages=public,
            witnesses=[dict(id=identity, public_prefix_count=len(public), command=example['command'],
                gained=example['gained'], lost=example['lost'], executor='actor', recorded_pending=None,
                before=before, after=after)],
            provenance='Recorded Actor action; native macro transition until next assistant decision.'))
        provenance.append(dict(id=identity, native_span=[start, stop], before=before, after=after,
            simulation=dict(path=str(episode / 'simulation.json'), sha256=sha(episode / 'simulation.json'))))
    incumbent = source / 'witness_update.py'
    (root / 'incumbent.py').write_bytes(incumbent.read_bytes())
    write(root / 'examples.json', examples)
    views = []
    for example in examples[-2:]:
        for view in B.receipt_views(example['observation']):
            views.append(dict(witness_id=example['id'], transform=view['transform'],
                replacements=[dict(message_index=i, content=view['observation']['messages'][i]['content'])
                              for i in view['changed_messages']]))
    materials = dict(program=incumbent.read_text(), sources=sources, tools=old['tools'], policy=old['policy'],
        derived_view_examples=views,
        interface='step(public_observation, memory); memory resets; yield forwards a pending operation unchanged.',
        scope='Exposed development sources only. Native macro feedback is training supervision, not policy input. '
              'All selectors share every source, view, candidate and formation cost. No new-task results supplied.')
    write(root / 'materials.json', materials)
    write(root / 'NEW_SOURCE_EFFECTS.json', dict(sources=provenance, new_model_calls=0, new_native_episodes=0))
    files = dict(driver=Path(__file__), binding=Path(B.__file__), compiler=Path(CP.__file__),
        carrier=Path(C.__file__), gateway=args.repo / 'scripts/graph/research_school_gateway.py',
        incumbent=root / 'incumbent.py', examples=root / 'examples.json', materials=root / 'materials.json')
    executed = root / 'executed_code'
    executed.mkdir()
    for label, path in files.items():
        shutil.copy2(path, executed / (label + '_' + path.name))
    plan = dict(frozen={k:dict(path=str(p), sha256=sha(p)) for k,p in files.items()},
        source_units=len(examples), source_trajectories=len(sources),
        model='deepseek-v4-flash', formation_posts=2, formation_tokens=600000, output_cap=32768,
        seconds_per_request=900, unknown_reservation=262144,
        equiv_weight=1.0, edit_weight=0.01, image=IMAGE,
        pool='incumbent plus at most two shared automatic edits; handwritten normalization is a separate baseline',
        stop='No blind retries; stop on provider/unknown usage failure. Stop extra proposals once no useful search remains.',
        prior_project_posts=4556, prior_project_known=46384634,
        prior_unknown_posts=10, prior_reserved_tokens=2621440,
        execution='AST construction on host; generated functions only in networkless resource-limited Docker.',
        independence='Four exposed source trajectories; 64 witnesses/views are not independent tasks.',
        git_commit=subprocess.check_output(['git','-C',str(args.repo),'rev-parse','HEAD'], text=True).strip())
    write(root / 'PLAN.json', plan)
    print(json.dumps(dict(prepared=True, source_units=len(examples), source_trajectories=len(sources),
                         source_effects=provenance, plan_sha256=sha(root / 'PLAN.json'))), flush=True)


def check(root):
    plan = read(root / 'PLAN.json')
    for record in plan['frozen'].values():
        if sha(record['path']) != record['sha256']:
            raise ValueError('frozen source changed: ' + record['path'])
    return plan


def parse_calls(raw):
    calls, finish = {}, None
    for line in raw.decode('utf-8').splitlines():
        if not line.startswith('data:') or line[5:].strip() == '[DONE]':
            continue
        for choice in json.loads(line[5:].strip()).get('choices', []):
            finish = choice.get('finish_reason') or finish
            for call in choice.get('delta', {}).get('tool_calls') or []:
                row = calls.setdefault(call.get('index', 0), dict(name='', arguments=''))
                row['name'] += call.get('function', {}).get('name', '')
                row['arguments'] += call.get('function', {}).get('arguments', '')
    return finish, calls


def form(args):
    plan = check(args.root)
    sys.path.insert(0, str(args.repo))
    from scripts.graph.research_school_gateway import BatchBudget, SchoolGateway, usage_from_body
    budget = BatchBudget(args.root / 'budget', posts=plan['formation_posts'], tokens=plan['formation_tokens'])
    key = sys.stdin.readline().strip()
    if not key:
        budget.close()
        raise ValueError('credential required through stdin')
    gateway = SchoolGateway(key, budget, output_ceiling=plan['output_cap'])
    key = None
    for index in range(plan['formation_posts']):
        out = args.root / 'formation' / str(index)
        if out.exists():
            continue
        if index and any(r['state'] != 'complete' or r.get('http_status') != 200 for r in budget.rows):
            break
        out.mkdir(parents=True, exist_ok=False)
        material = read(args.root / 'materials.json')
        if index:
            prior = args.root / 'formation' / '0'
            material['previous_shared_attempt'] = read(prior / 'RESULT.json')
            if (prior / 'proposal.json').exists():
                material['previous_shared_proposal'] = read(prior / 'proposal.json')
            material['search_instruction'] = 'Offer one compact alternative repair using the same sources; no extra task information.'
        builder = (B.fragment_edit_request if plan.get('learning_mode') == 'prerequisite_fragment'
                   else B.binding_edit_request)
        request = builder(material, model=plan['model'], output_cap=plan['output_cap'])
        body = json.dumps(request, ensure_ascii=False, separators=(',', ':')).encode()
        if len(body) + plan['output_cap'] + 8192 > 262144:
            raise ValueError('conservative input byte ceiling exceeded')
        (out / 'request.json').write_bytes(body)
        parts, status, connection, result = [], None, None, {}
        try:
            _, connection = gateway.open(body, timeout=60)
            response = http.client.HTTPResponse(connection)
            response.begin()
            status = response.status
            deadline = time.monotonic() + plan['seconds_per_request']
            with (out / 'response.sse').open('xb') as handle:
                while True:
                    if time.monotonic() >= deadline:
                        raise TimeoutError('formation deadline')
                    connection.settimeout(min(60, max(.01, deadline - time.monotonic())))
                    block = response.read1(65536)
                    if not block:
                        break
                    handle.write(block); handle.flush(); parts.append(block)
                    if sum(map(len, parts)) > 16 * 1024**2:
                        raise ValueError('response byte cap')
            raw = b''.join(parts)
            budget.finish(status=status, body=raw)
            finish, calls = parse_calls(raw)
            result.update(status=status, finish_reason=finish, usage=usage_from_body(raw))
            if status != 200 or finish != 'tool_calls' or len(calls) != 1 or calls[0]['name'] != 'emit_edit':
                raise ValueError('no complete emit_edit delivery')
            proposal = json.loads(calls[0]['arguments'])
            write(out / 'proposal.json', proposal)
            source, metadata = CP.apply_function_edits(material['program'], proposal['edits'])
            (out / 'program.py').write_text(source, encoding='utf-8')
            result.update(structure='PASS', program_sha256=sha(out / 'program.py'), edits=metadata)
        except Exception as error:
            result['error'] = type(error).__name__ + ': ' + str(error)
        finally:
            if budget.pending is not None:
                budget.finish(status=status, body=b''.join(parts))
            if connection:
                connection.close()
            result.setdefault('usage', usage_from_body(b''.join(parts)))
            write(out / 'RESULT.json', result)
        print(json.dumps(dict(formation=index, **result)), flush=True)
        if result.get('error') or not result.get('usage'):
            break
    budget.close()


GUEST = '''import json, pathlib, sys
sys.path.insert(0, '/modules')
import binding_update as B
root=pathlib.Path('/evidence')
inc=(root/'incumbent.py').read_text()
examples=json.loads((root/'examples.json').read_text())
tools=[t['function']['name'] for t in json.loads((root/'materials.json').read_text())['tools']]
paths=sorted(root.glob('formation/*/program.py'))
candidates=[p.read_text() for p in paths]
result=B.select_binding_update(inc,candidates,examples,tools)
result['candidate_paths']=['incumbent.py']+[str(p.relative_to(root)) for p in paths]
result['simple_baseline']=B.score_binding_update(B.normalized_baseline(inc),inc,examples,tools)
print(json.dumps(result))
'''


def probe(args):
    plan = check(args.root)
    name = 'fccl-binding-probe-' + str(time.time_ns())
    command = ['docker','run','--rm','--name',name,'--network','none','--read-only',
        '--pids-limit','64','--memory','768m','--cpus','1',
        '--tmpfs','/tmp:rw,noexec,nosuid,size=64m',
        '--mount','type=bind,src='+str(args.root)+',dst=/evidence,readonly',
        '--mount','type=bind,src='+str(Path(__file__).parent)+',dst=/modules,readonly',
        plan['image'],'python','-B','-c',GUEST]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=75)
    except subprocess.TimeoutExpired:
        subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=15)
        raise
    if completed.returncode:
        raise RuntimeError(completed.stderr[-2000:])
    result = json.loads(completed.stdout)
    result.update(new_model_calls=0, new_native_episodes=0, plan_sha256=sha(args.root / 'PLAN.json'))
    write(args.root / 'SOURCE_SELECTION.json', result)
    print(json.dumps(dict(selected=result['selected'], candidate_paths=result['candidate_paths'],
        source_units=result['source_units'], scores=[dict(ordinary=s['ordinary'],
            augmented_erm=s['augmented_erm'],consistency=s['consistency'],
            positive_misses=s['raw']['positive_misses'],negative_repeats=s['raw']['negative_repeats'],
            errors=s.get('view_errors',s['raw']['errors'])) for s in result['scores']],
        baseline={k:result['simple_baseline'][k] for k in ['ordinary','augmented_erm','consistency']})),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare','form','probe'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--source', type=Path)
    parser.add_argument('--timing', type=Path)
    arguments = parser.parse_args()
    {'prepare':prepare,'form':form,'probe':probe}[arguments.mode](arguments)
