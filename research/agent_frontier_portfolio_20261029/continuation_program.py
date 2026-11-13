"""Executable feedback-conditioned controllers and local state refinements.

The controller sees public observations and its own JSON memory. It returns
one real tool/customer operation, yields, or acknowledges a terminal world.
This module neither calls a model nor certifies a program's task success.
It is not a Python security sandbox: execution belongs in the owned actor
container, with the host enforcing role/turn limits on every world operation.
"""
from __future__ import annotations
import ast
import copy
import hashlib
import json
import math
import re


SAFE_BUILTINS = {
    'str': str, 'int': int, 'float': float, 'bool': bool, 'dict': dict,
    'list': list, 'tuple': tuple, 'set': set, 'len': len, 'range': range,
    'enumerate': enumerate, 'zip': zip, 'min': min, 'max': max, 'sum': sum,
    'any': any, 'all': all, 'sorted': sorted, 'isinstance': isinstance,
    'reversed': reversed, 'next': next, 'abs': abs, 'round': round,
    'Exception': Exception, 'ValueError': ValueError, 'TypeError': TypeError,
}
FORBIDDEN = (ast.ImportFrom, ast.ClassDef, ast.Global, ast.Nonlocal,
             ast.AsyncFunctionDef, ast.Await, ast.Yield, ast.YieldFrom)


def check_source(source):
    if not isinstance(source, str) or len(source.encode('utf-8')) > 48000:
        raise ValueError('invalid controller source length')
    tree = ast.parse(source)
    if not any(isinstance(n, ast.FunctionDef) and n.name == 'step' for n in tree.body):
        raise ValueError('controller must define step(observation, memory)')
    for n in ast.walk(tree):
        if isinstance(n,ast.Import) and any(a.name not in {'json','re','math'} or a.asname for a in n.names):
            raise ValueError('only the already-bound pure standard modules are available')
        if isinstance(n, FORBIDDEN):
            raise ValueError('unsupported controller construct: ' + type(n).__name__)
        if isinstance(n, ast.Name) and n.id.startswith('__'):
            raise ValueError('private runtime names are not controller inputs')
        if isinstance(n, ast.Attribute) and n.attr.startswith('_'):
            raise ValueError('private attributes are not controller inputs')
    for n in tree.body:
        # Top-level execution would precede the runtime's step bound.
        if isinstance(n, ast.Import):
            continue
        elif isinstance(n, ast.FunctionDef):
            if n.decorator_list or n.args.defaults or any(n.args.kw_defaults):
                raise ValueError('controller definitions cannot execute decorators/defaults')
        elif isinstance(n, ast.Assign):
            ast.literal_eval(n.value)
        elif not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                  and isinstance(n.value.value, str)):
            raise ValueError('only pure definitions and literal constants are allowed')
    return tree


def load_program(source):
    tree = check_source(source)
    class ExistingModules(ast.NodeTransformer):
        def visit_Import(self,node):
            return ast.copy_location(ast.Pass(),node)
    tree=ast.fix_missing_locations(ExistingModules().visit(tree))
    scope = {'__builtins__': SAFE_BUILTINS, 'json': json, 're': re, 'math': math}
    exec(compile(tree, '<corrective-controller>', 'exec'), scope)
    return scope['step']


def public_step(program, observation, memory, tool_names):
    """Validate an operation; the host world still enforces tool roles/turns."""
    value = program(copy.deepcopy(observation), copy.deepcopy(memory))
    if type(value) is not dict or set(value) - {'kind','name','arguments','memory','reason'}:
        raise ValueError('invalid controller decision')
    kind = value.get('kind')
    if kind not in {'act','yield','stop'} or type(value.get('memory')) is not dict:
        raise ValueError('invalid controller decision kind/memory')
    json.dumps(value, allow_nan=False)
    if kind == 'act':
        if observation.get('done'):
            raise ValueError('controller cannot act after terminal observation')
        name = value.get('name')
        if type(name) is not str or name not in set(tool_names) | {'say'}:
            raise ValueError('controller requested a non-agent tool')
        if type(value.get('arguments')) is not dict:
            raise ValueError('tool arguments must be an object')
        if name == 'say' and (set(value['arguments']) != {'message'}
                or type(value['arguments']['message']) is not str):
            raise ValueError('invalid customer message')
    elif kind == 'stop' and not observation.get('done'):
        raise ValueError('controller cannot declare a nonterminal world complete')
    return value


def weave_corrective_option(source, option_source):
    """Attach a learned corrective option while preserving the base policy.

    option_step(public_observation, prior_memory, proposed_decision) returns
    None to retain the base decision, or a complete act/yield decision. A
    multi-step option stores its phase in ordinary JSON memory. It can return
    control when its observed scope ends instead of finishing the whole task.
    Native outcome/cost evidence, not this compiler, decides learned utility.
    """
    parent = check_source(source)
    if not isinstance(option_source, str) or len(option_source.encode('utf-8')) > 16000:
        raise ValueError('invalid corrective option source length')
    # Reuse exactly the existing pure-definition checks; this is not a sandbox.
    check_source(option_source + "\ndef step(o,m):\n    return {'kind':'yield','memory':m}\n")
    option = ast.parse(option_source)
    functions = [n.name for n in option.body if isinstance(n, ast.FunctionDef)]
    if functions.count('option_step') != 1 or any(not n.startswith('option_') for n in functions):
        raise ValueError('option functions require an option_ namespace and option_step')
    entry = next(n for n in option.body if isinstance(n, ast.FunctionDef) and n.name == 'option_step')
    if (len(entry.args.posonlyargs + entry.args.args) != 3 or entry.args.vararg
            or entry.args.kwarg or entry.args.kwonlyargs):
        raise ValueError('option_step requires exactly three positional inputs')
    for node in option.body:
        if isinstance(node, ast.Assign):
            if any(not isinstance(t, ast.Name) or not t.id.startswith('OPTION_') for t in node.targets):
                raise ValueError('option constants require an OPTION_ namespace')
    names = {n.name for n in parent.body if isinstance(n, ast.FunctionDef)}
    names.update(n.id for a in parent.body if isinstance(a, ast.Assign)
                 for target in a.targets for n in ast.walk(target) if isinstance(n, ast.Name))
    option_names = set(functions)
    option_names.update(t.id for n in option.body if isinstance(n, ast.Assign) for t in n.targets)
    if names.intersection(option_names) or 'base_controller_step' in names:
        raise ValueError('corrective option collides with the base controller')
    if any(isinstance(n, ast.Name) and n.id == 'step' for n in ast.walk(parent)):
        raise ValueError('a referenced source step cannot be renamed safely')
    base_step = next(n for n in parent.body if isinstance(n, ast.FunctionDef) and n.name == 'step')
    base_step.name = 'base_controller_step'
    wrapper = ast.parse('''
def step(observation, memory):
    before = json.loads(json.dumps(memory))
    proposal = base_controller_step(observation, memory)
    if observation.get('done'):
        return proposal
    correction = option_step(
        json.loads(json.dumps(observation)),
        before,
        json.loads(json.dumps(proposal)))
    if correction is None:
        return proposal
    return correction
''')
    combined = ast.Module(body=parent.body + option.body + wrapper.body, type_ignores=[])
    revised = ast.unparse(ast.fix_missing_locations(combined)) + '\n'
    check_source(revised)
    return revised, dict(parent_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),
        option_sha256=hashlib.sha256(option_source.encode('utf-8')).hexdigest(),
        option_functions=functions, base_bodies_preserved=True)


def partial_effect_frontier(records):
    """Retain observed complementary effects, including globally failed runs.

    This is an empirical multi-objective admission rule, not causal credit for
    individual actions. Unknown effects cannot dominate or be dominated. Costs
    do not make an unsuccessful but shorter trajectory a better skill.
    """
    groups, ids = {}, set()
    for record in records:
        identity, group = record['id'], record['group']
        components, reward = record['components'], record['native_reward']
        if (not isinstance(identity, str) or not identity or identity in ids
                or not isinstance(group, str) or not group
                or type(components) is not dict or not components
                or any(not isinstance(k, str) or not k for k in components)
                or any(v is not None and type(v) is not bool for v in components.values())
                or type(reward) not in (int, float) or not math.isfinite(reward)
                or not 0 <= reward <= 1):
            raise ValueError('invalid or duplicate partial-effect record')
        ids.add(identity)
        peers = groups.setdefault(group, [])
        for peer in peers:
            if (peer['model'] != record['model'] or peer['caps'] != record['caps']
                    or set(peer['components']) != set(components)):
                raise ValueError('incomparable measurements inside one source group')
        peers.append(record)

    def dominates(a, b):
        if any(v is None for r in (a, b) for v in r['components'].values()):
            return False
        keys = sorted(a['components'])
        av = [a['native_reward']] + [int(a['components'][k]) for k in keys]
        bv = [b['native_reward']] + [int(b['components'][k]) for k in keys]
        return all(x >= y for x, y in zip(av, bv)) and any(x > y for x, y in zip(av, bv))

    dominated = {r['id'] for peers in groups.values() for r in peers
                 if any(dominates(p, r) for p in peers if p is not r)}
    return dict(retained_ids=[r['id'] for r in records if r['id'] not in dominated],
                dominated_ids=[r['id'] for r in records if r['id'] in dominated],
                scope='Observed whole-run component feedback; not independent action credit')


def compile_history_policy(source):
    """Match offline and deployed state: generated policy uses public history.

    Both update arms use this same wrapper. Public history carries past actions
    and receipts; old controller node memory is neither replayed nor invented.
    """
    tree = check_source(source)
    if len(source.encode('utf-8')) > 16000:
        raise ValueError('history-conditioned policy exceeds proposal bound')
    if any(isinstance(n, ast.Name) and n.id in {'step', 'history_candidate_step'}
           for n in ast.walk(tree)) or any(isinstance(n, ast.FunctionDef)
           and n.name == 'history_candidate_step' for n in tree.body):
        raise ValueError('history entry namespace collision or referenced entry')
    next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'step').name = 'history_candidate_step'
    wrapper = ast.parse('''
def step(observation, memory):
    for message in observation.get('messages', []):
        if message.get('content') is None:
            message.pop('content', None)
    decision = history_candidate_step(observation, {})
    decision['memory'] = {}
    return decision
''')
    result = ast.unparse(ast.fix_missing_locations(ast.Module(
        body=tree.body + wrapper.body, type_ignores=[]))) + '\n'
    check_source(result)
    return result


def score_effect_witnesses(source, examples, tool_names, *, positive_weight=1.0,
                           negative_weight=1.0, unsupported_weight=0.05,
                           size_weight=0.01):
    """Score conditional actions using signed, observed macro-effect witnesses.

    Native labels and executor identity are host-side supervision only. A
    policy receives a public prefix and fresh memory, never the old program's
    private control state. Preserving an observed positive action and avoiding
    a known harmful replay are separate objectives, including globally failed
    source runs. Neutral transitions carry no effect label; deviations on them
    incur only the explicitly weighted intervention prior.

    This is an offline compatibility objective, not counterfactual environment
    evaluation. Exact tool arguments and whitespace-normalized Say text are
    used; paraphrases are not silently certified as semantically equivalent.
    """
    weights = dict(positive=positive_weight, negative=negative_weight,
                   unsupported=unsupported_weight, size=size_weight)
    if (type(examples) is not list or any(type(v) not in (int, float)
            or not math.isfinite(v) or v < 0 for v in weights.values())):
        raise ValueError('finite nonnegative weights and explicit witnesses required')
    identities = set()
    for row in examples:
        observation = row['observation']
        if (not isinstance(row['id'], str) or row['id'] in identities
                or row.get('executor') not in {'actor', 'program'}
                or type(observation) is not dict
                or set(observation) - {'messages', 'turn', 'done', 'proposed_operation', 'error'}
                or type(observation.get('messages')) is not list
                or type(row['command']) is not dict
                or set(row['command']) != {'name', 'arguments'}
                or type(row['command']['arguments']) is not dict
                or any(type(row[k]) is not list or any(not isinstance(x, str) for x in row[k])
                       for k in ['gained', 'lost'])):
            raise ValueError('invalid witness or non-public policy observation')
        for message in observation['messages']:
            if (type(message) is not dict or message.get('role') not in {'user', 'assistant', 'tool'}
                    or set(message) - {'role', 'content', 'tool_calls', 'id', 'requestor', 'error'}
                    or (message.get('content') is not None and type(message['content']) is not str)
                    or (message['role'] == 'user' and message.get('tool_calls'))
                    or (message['role'] == 'tool' and message.get('requestor') != 'assistant')):
                raise ValueError('message is not the public agent projection')
            for call in message.get('tool_calls') or []:
                if (type(call) is not dict or set(call) - {'id', 'name', 'arguments'}
                        or not isinstance(call.get('name'), str) or type(call.get('arguments')) is not dict):
                    raise ValueError('invalid public tool call')
        proposal = observation.get('proposed_operation')
        if proposal is not None and (type(proposal) is not dict
                or set(proposal) - {'op', 'turn', 'name', 'arguments'}
                or proposal.get('op') != 'act'
                or proposal.get('turn') != observation.get('turn')
                or proposal.get('name') not in set(tool_names) | {'say'}
                or type(proposal.get('arguments')) is not dict):
            raise ValueError('pending operation is not a recorded legal Actor command')
        identities.add(row['id'])

    report = dict(eligible=False, objective=None, positive_misses=0, negative_repeats=0,
                  positive_examples=sum(bool(r['gained']) for r in examples),
                  negative_examples=sum(bool(r['lost']) for r in examples),
                  neutral_examples=sum(not r['gained'] and not r['lost'] for r in examples),
                  observed_effects=sum(bool(r['gained'] or r['lost']) for r in examples),
                  unsupported_dispatches=0, retained_actor_positives=0,
                  positive_interventions=0, unknown_continuations=0,
                  rows=[], weights=weights, errors=[])
    try:
        program = load_program(source)
    except Exception as exc:
        report['errors'].append(dict(kind=type(exc).__name__, message=str(exc)[:200]))
        return report

    for row in examples:
        try:
            decision = public_step(program, row['observation'], {}, tool_names)
            actual = row['command']
            intervention = decision['kind'] == 'act'
            effective = decision if intervention else row['observation'].get('proposed_operation')
            same = bool(effective and effective['name'] == actual['name']
                        and effective['arguments'] == actual['arguments'])
            if effective and effective['name'] == actual['name'] == 'say':
                same = (' '.join(effective['arguments']['message'].split())
                        == ' '.join(actual['arguments']['message'].split()))
            missed = bool(row['gained']) and not same
            repeated = bool(row['lost']) and same
            unsupported = (not row['gained'] and not row['lost']
                           and intervention and not same)
            report['positive_misses'] += missed
            report['negative_repeats'] += repeated
            report['unsupported_dispatches'] += unsupported
            report['retained_actor_positives'] += bool(row['gained']) and same and not intervention
            report['positive_interventions'] += bool(row['gained']) and same and intervention
            report['unknown_continuations'] += effective is None
            report['rows'].append(dict(id=row['id'], source=row.get('source'),
                executor=row['executor'], matched_observed_action=same,
                missed_positive=missed, repeated_negative=repeated,
                effective_executor='program' if intervention else 'actor' if effective else 'unknown',
                abstention_is_not_verified_correction=effective is None,
                action={k: decision[k] for k in ['kind', 'name', 'arguments'] if k in decision}))
        except Exception as exc:
            report['errors'].append(dict(id=row['id'], kind=type(exc).__name__, message=str(exc)[:200]))
    if report['errors']:
        return report
    report['eligible'] = True
    report['source_sha256'] = hashlib.sha256(source.encode('utf-8')).hexdigest()
    if not report['observed_effects']:
        return report
    report['objective'] = (
        positive_weight * report['positive_misses'] / max(1, report['positive_examples'])
        + negative_weight * report['negative_repeats'] / max(1, report['negative_examples'])
        + unsupported_weight * report['unsupported_dispatches'] / max(1, report['neutral_examples'])
        + size_weight * len(source.encode('utf-8')) / 16000)
    return report


def select_witness_update(incumbent_source, candidate_sources, examples, tool_names, **weights):
    """Bounded signed-witness revision; retain the incumbent on a loss tie.

    Candidate formation and real task execution are accounted elsewhere. This
    selector cannot establish a native gain, and it does not discard a failed
    source merely because its terminal reward is zero.
    """
    sources = [incumbent_source] + list(candidate_sources)
    scores = [score_effect_witnesses(s, examples, tool_names, **weights) for s in sources]
    if not any(s['observed_effects'] for s in scores):
        return dict(source=incumbent_source, selected_index=0, scores=scores, reason='no_observed_effects')
    eligible = [i for i, s in enumerate(scores) if s['eligible'] and s['objective'] is not None]
    if not eligible:
        return dict(source=incumbent_source, selected_index=0, scores=scores, reason='no_valid_update')
    selected = min(eligible, key=lambda i: (scores[i]['objective'], i))
    return dict(source=sources[selected], selected_index=selected, scores=scores,
                reason='signed_observed_effects_and_intervention_prior')


def witness_learning_request(materials, diagnostics, *, constrained, model):
    """Matched bounded proposals; only the update/retention instruction differs."""
    instruction = '''Learn a compact reusable local corrective skill from the supplied real public histories and observed macro-effect feedback, including failed whole tasks and actions actually executed by the Actor. Return emit_policy with source, rationale and evidence. Define pure step(observation,memory) with optional pure helpers/literal constants, at most 16000 UTF-8 bytes. observation is a dictionary: messages contains complete public history, proposed_operation is a pending Actor command or None, turn/done are public keys. Each decision is {kind:'act',name:assistant_tool_or_say,arguments:object,memory:object} or {kind:'yield',memory:object,reason:string}. say has exactly {message:string}. Stop only after done=true. json/re/math and basic builtins are bound; no imports/IO/private fields.
Use runtime entity IDs, current requested quantities, public receipts and actual feedback; never hardcode source IDs, quantities, task IDs or native labels. Check consent, prior successful writes, available resources, current rather than obsolete feedback and remaining obligations. Both arms are wrapped as history-only policies: each call receives empty own memory, and returned memory is reset; derive progress from complete public history and actual receipts. Automate only a supported local correction, then yield to the Actor for remaining diagnosis. Do not greet, reset, declare whole-task success, or transfer the entire conversation. Retain an already-correct recorded Actor proposal by yielding; copying it is no additional skill contribution. Distinguish requested from observed results. A candidate can change conditions, action bodies and return behavior; no donor body is immutable.
Labels describe observed macro spans containing intervening customer/environment actions, not independent causal credit. The host evaluates exact tool arguments and whitespace-normalized Say text; wording matches are only a conservative offline proxy. Neutral spans are unlabelled for effects. Full native success and formation-plus-use cost on new tasks decide usefulness. All supplied feedback and diagnostics are available to both update rules.'''
    if constrained:
        instruction += '''\nUpdate rule: minimize missed positive-action witnesses plus harmful-action replays in negative contexts, with a small unsupported-intervention prior and source-size penalty. Diagnose the supplied executable counterexamples, keep supported conditional behavior softly, revise conflicting guards/parameters/continuations, and yield outside learned support. The host retains the lowest observed compatibility objective within the same bounded proposal budget; this is not proof of task utility.'''
    else:
        instruction += '''\nOrdinary feedback revision: freely write the best local policy from all the same histories, effect labels, code and diagnostics. Revise your preceding proposal using the supplied feedback; no particular repair location or edit restriction is imposed. As in the constrained arm, the host returns the lowest observed compatibility objective among the same number of candidates, not automatically the last revision. This is an adaptation baseline, not a reproduction of a published method.'''
    tool = dict(type='function', function=dict(name='emit_policy',
        description='Return an executable public-feedback corrective skill.',
        parameters=dict(type='object', properties={k: dict(type='string')
            for k in ['source', 'rationale', 'evidence']}, required=['source', 'rationale', 'evidence'])))
    data = dict(materials=materials, candidate_diagnostics=diagnostics)
    return dict(model=model, messages=[dict(role='system', content=instruction),
        dict(role='user', content=json.dumps(data, ensure_ascii=False))], tools=[tool],
        tool_choice=dict(type='function', function=dict(name='emit_policy')),
        temperature=0, max_tokens=32768, stream=True, stream_options=dict(include_usage=True))


def partial_effect_learning_request(materials, *, compose, model):
    """Build the exact two-writer preservation-v1 training inputs.

    Both writers see identical past executions and have the same model budget.
    The experimental requests are archived privately; this pure builder makes
    their update rule reviewable without executing any generated code.
    """
    instruction = (
        'Form a reusable corrective policy from the supplied actual public executions. Use only public '
        'history, feedback and runtime memory. observation is a DICTIONARY: '
        "observation.get('messages',[]) is the full actual public history; proposed_operation is a "
        'pending Actor command or None; done/turn are dictionary keys. The Actor handles the task '
        'outside your supported local scope. Preserve consent and parameter bindings from current '
        'history; never call customer-only tools or hardcode source line IDs, quantities, task IDs or '
        'expected outcomes. Do not mistake a normal Say receipt for a repeated write, stale '
        'observations for current status, or any positive refuel for sufficient quota.\nReturn '
        'emit_policy with source, rationale, evidence. Define pure step(observation,memory), optional '
        'pure helpers/literal constants. Return '
        "{kind:'act',name:assistant_tool_or_say,arguments:object,memory:object} or "
        "{kind:'yield',memory:object,reason:string}. say arguments exactly {message:string}. Stop only "
        'if done is already true. No imports/IO/private attributes. json/re/math and basic builtins are '
        'bound. No greeting/reset/whole-task declaration. Common client can execute up to four local '
        'actions per Actor operation and then replans any displaced proposal. Learn concrete '
        'feedback-conditioned corrections, not merely warnings. Empty scope yields to Actor.\nPast '
        'component feedback is training evidence only. Full native success, regressions and total '
        'formation-plus-use costs matter; failed task suffix cost alone is not benefit.\n'
    )
    if compose:
        instruction += (
            'Learning rule: retain both nondominated partially successful donors selected below. Emit a '
            '<=4000 UTF-8 byte routing bridge defining step. Their pure bodies remain frozen under d0_/d1_ '
            'namespaces. Prefer reusing a supported concrete action node with '
            "call_fragment('d0.node_name',observation,child_memory), or d1 analog, rather than replaying a "
            'whole stopped controller. The complete source and callable names are supplied. call_fragment '
            "returns the original node's act/yield and records actual dispatch in returned memory. "
            'Preserve/extend that memory when keeping the decision; use your own phase to continue locally '
            'and yield when support ends. Learn the runtime conditions and node/memory bindings from public '
            'trajectories and complementary effects. Do not follow a node whose stale control state blocks '
            'the needed correction. Direct new corrective actions are allowed when necessary, but explain '
            'unsupported reuse. Do not overwrite frozen donor/dispatcher definitions.\nObserved component '
            'frontier: '
            + json.dumps(partial_effect_frontier(materials['donor_records'])))
    else:
        instruction += (
            'Ordinary feedback-update comparator: write the best <=16000 UTF-8 byte complete local policy '
            'from the same supplied code, full histories and outcomes. You may rewrite guards, actions, '
            'memory and continuation freely; there is no donor-preservation or Pareto constraint. Supplied '
            'donor programs are evidence, not runtime globals. This is a same-information rewrite baseline '
            'inspired by execution-anchored revision, not a reproduction claim.'
        )
    request = {'tools': [{'type': 'function',
                'function': {'name': 'emit_policy',
                             'description': 'Return an executable public-feedback corrective '
                                            'policy.',
                             'parameters': {'type': 'object',
                                            'properties': {'source': {'type': 'string'},
                                                           'rationale': {'type': 'string'},
                                                           'evidence': {'type': 'string'}},
                                            'required': ['source', 'rationale', 'evidence']}}}],
     'tool_choice': {'type': 'function', 'function': {'name': 'emit_policy'}},
     'temperature': 0,
     'max_tokens': 65536,
     'stream': True,
     'stream_options': {'include_usage': True}}
    request['model'] = model
    request['messages'] = [dict(role='system', content=instruction),
                           dict(role='user', content=json.dumps(materials, ensure_ascii=False))]
    return request


def compose_fragment_library(sources, bridge_source):
    """Namespace frozen donor bodies and learn their public-state routing.

    The bridge may add actions or yield to the Actor. call_fragment executes
    an existing two-input node or step with copied public data, recording the
    actual dispatch in returned memory. Generated code runs in the guest only.
    """
    if not sources or len(sources) > 8:
        raise ValueError('expected a small nonempty donor library')
    bodies, entries, reserved, hashes = [], [], {'call_fragment'}, []
    for index, source in enumerate(sources):
        tree = check_source(source)
        names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                if any(not isinstance(t, ast.Name) for t in node.targets):
                    raise ValueError('donor globals must have simple names')
                names.update(t.id for t in node.targets)
        # Refuse ambiguous shadowing rather than silently changing its meaning.
        for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
            local = {a.arg for a in fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs}
            local.update(n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store))
            local.update(n.name for n in ast.walk(fn) if isinstance(n, ast.FunctionDef) and n is not fn)
            if local.intersection(names):
                raise ValueError('donor local/global shadowing needs a scoped adapter')
        mapping = {name: 'd' + str(index) + '_' + name for name in names}
        for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
            if ((fn.name == 'step' or fn.name.startswith('node_'))
                    and len(fn.args.posonlyargs + fn.args.args) == 2
                    and not fn.args.vararg and not fn.args.kwarg and not fn.args.kwonlyargs):
                entries.append(('d' + str(index) + '.' + fn.name, mapping[fn.name]))

        class Namespace(ast.NodeTransformer):
            def visit_Name(self, node):
                if node.id in mapping:
                    node.id = mapping[node.id]
                return node

            def visit_FunctionDef(self, node):
                if node.name in mapping:
                    node.name = mapping[node.name]
                return self.generic_visit(node)

        bodies.extend(Namespace().visit(tree).body)
        reserved.update(mapping.values())
        hashes.append(hashlib.sha256(source.encode('utf-8')).hexdigest())
    bridge = check_source(bridge_source)
    declared = {n.name for n in bridge.body if isinstance(n, ast.FunctionDef)}
    declared.update(t.id for n in bridge.body if isinstance(n, ast.Assign)
                    for t in n.targets if isinstance(t, ast.Name))
    if declared.intersection(reserved):
        raise ValueError('bridge cannot replace frozen donor definitions')
    dispatch = "def call_fragment(name, observation, memory):\n"
    dispatch += "    child = json.loads(json.dumps(memory))\n"
    for i, (public, internal) in enumerate(entries):
        dispatch += "    " + ('if' if i == 0 else 'elif') + " name == " + repr(public) + ":\n"
        dispatch += "        decision = " + internal + "(json.loads(json.dumps(observation)), child)\n"
    dispatch += "    else:\n        raise ValueError('unknown corrective fragment')\n"
    dispatch += "    decision['memory']['fccl_fragment_calls'] = memory.get('fccl_fragment_calls', [])[-15:] + [name]\n"
    dispatch += "    return decision\n"
    combined = ast.Module(body=bodies + ast.parse(dispatch).body + bridge.body, type_ignores=[])
    output = ast.unparse(ast.fix_missing_locations(combined)) + '\n'
    check_source(output)
    return output, dict(donor_sha256=hashes, donor_bodies_preserved=True,
                        preservation_scope='AST bodies under namespace renaming; common dispatch adds call evidence',
                        fragment_names=[name for name, _ in entries],
                        bridge_sha256=hashlib.sha256(bridge_source.encode('utf-8')).hexdigest())


def matched_continuation_preference(continuation, correction, cost_margin=0.15):
    """An empirical *whole-suffix* training target, never a single-action label.

    Native success takes priority. Cost comparisons require two successful
    suffixes and completely known use. Failed/failed pairs stay unresolved;
    cheaper failure does not manufacture a positive corrective example.
    """
    if type(cost_margin) not in (int, float) or not 0 <= cost_margin < 1:
        raise ValueError('invalid cost margin')
    for key in ('checkpoint', 'model', 'caps', 'public_files'):
        if key not in continuation or key not in correction:
            raise ValueError('missing matched context: ' + key)
        if json.dumps(continuation[key], sort_keys=True, allow_nan=False) != json.dumps(correction[key], sort_keys=True, allow_nan=False):
            raise ValueError('unmatched continuation context: ' + key)
    scores = [x.get('native_reward') for x in (continuation, correction)]
    if any(type(x) not in (int, float) or x not in (0, 1) for x in scores):
        raise ValueError('complete binary native outcomes are required')
    if scores == [0, 1]:
        return 'CORRECTION'
    if scores == [1, 0]:
        return 'CONTINUE'
    if scores == [0, 0]:
        return 'UNRESOLVED'
    uses = [x.get('known_tokens') for x in (continuation, correction)]
    if any(x.get('unknown', 0) for x in (continuation, correction)) or any(type(x) is not int or x < 0 for x in uses):
        return 'UNRESOLVED'
    if uses[1] < uses[0] * (1 - cost_margin):
        return 'CORRECTION'
    if uses[0] < uses[1] * (1 - cost_margin):
        return 'CONTINUE'
    return 'TIE'


def corrective_frontier(continuation, correction):
    """Select a complete empirically preferred suffix at a matched frontier.

    Do not align through already-divergent user feedback. In that case the
    apparent next-action difference is not at a common observed state.
    """
    preference = matched_continuation_preference(continuation, correction)
    if preference not in {'CORRECTION', 'CONTINUE'}:
        return None
    left = continuation.get('public_continuation')
    right = correction.get('public_continuation')
    if type(left) is not list or type(right) is not list:
        raise ValueError('complete public continuations are required')
    def observed(message):
        if type(message) is not dict or message.get('role') not in {'assistant','user','tool'}:
            raise ValueError('invalid public continuation message')
        if ((message['role'] == 'user' and message.get('tool_calls'))
                or (message['role'] == 'tool' and message.get('requestor') != 'assistant')):
            raise ValueError('private user-tool history is not a learning input')
        value = copy.deepcopy(message)
        if value['role'] == 'tool':
            value.pop('id', None)
        for call in value.get('tool_calls') or []:
            call.pop('id', None)
        return value
    normalized_left = [observed(x) for x in left]
    normalized_right = [observed(x) for x in right]
    common = []
    for index, (old, new) in enumerate(zip(left, right)):
        if normalized_left[index] == normalized_right[index]:
            common.append(copy.deepcopy(old))
            continue
        if old.get('role') != 'assistant' or new.get('role') != 'assistant':
            return None
        preferred = correction if preference == 'CORRECTION' else continuation
        rejected = continuation if preference == 'CORRECTION' else correction
        return dict(preference=preference, common_public_suffix=common,
            preferred_first_decision=copy.deepcopy(new if preference == 'CORRECTION' else old),
            rejected_first_decision=copy.deepcopy(old if preference == 'CORRECTION' else new),
            preferred_public_continuation=copy.deepcopy(preferred['public_continuation']),
            rejected_public_continuation=copy.deepcopy(rejected['public_continuation']),
            evidence='One matched whole-suffix comparison, not isolated action credit')
    return None


def option_learning_request(materials, model):
    """Induce a bounded corrective option from real matched suffix outcomes.

    Frontier selection abstains before generation if outcomes or the observed
    decision state do not justify a preference. This request is a candidate
    learning rule; source replay and new-task native utility must still test it.
    """
    pair = materials.get('matched_pair')
    if type(pair) is not dict:
        raise ValueError('matched corrective evidence is required')
    selected = corrective_frontier(pair['continuation'], pair['correction'])
    if selected is None:
        raise ValueError('no matched preferred frontier; abstain before generation')
    instruction = '''Learn a reusable, bounded corrective option from the supplied real executions. The selected comparison supervises an entire corrective continuation; it does not prove that one action caused success. All evidence is past development data. The ordinary whole-controller updater receives exactly the same underlying material.
Output emit_corrective_option with source defining option_step(observation, memory, proposed_decision), optional pure option_* helpers and OPTION_* literal constants, rationale and evidence. At most 16000 UTF-8 source bytes. json/re/math and basic builtins are already bound. No imports other than these, IO, hidden state, source IDs, fixed source quantities, oracle labels, or future task information.
The compiler leaves the original controller bodies intact. At each actual public step, option_step receives the public observation, memory BEFORE the proposed base step, and the proposed decision. Return None to retain the proposal; or return a complete {kind: act|yield, name/arguments where needed, memory: object, reason: optional}. Legal assistant tools and say only. Never execute customer-only tools. Use memory for an actual multi-step corrective fragment when justified. End the fragment by yielding when its local scope is complete or unsupported; terminal stop is allowed only for a terminal world.
Learning rule: use the matched preferred continuation to identify a corrective fragment and its observable entry conditions. Preserve effects already established in that prefix. Bind entity/tool parameters from current public values. Use the supplied successful preservation contexts to constrain over-broad correction, and return control on observations not justified by the learned fragment. Learn concrete corrective actions, not only a new failure explanation. Do not simply prohibit all transfers, assume positive quota is sufficient, or declare a task complete from one positive word. A single-step intervention is an explicit strong comparator, not automatically an innovation. Native new-task success, regressions and full formation-plus-use cost will decide acceptance.'''
    tool = dict(type='function', function=dict(name='emit_corrective_option',
        description='Propose an executable feedback-conditioned corrective option.',
        parameters=dict(type='object', properties={k:dict(type='string') for k in ('source','rationale','evidence')},
                        required=['source','rationale','evidence'])))
    payload = dict(materials=materials, selected_frontier=selected)
    request = dict(model=model, messages=[dict(role='system',content=instruction),
        dict(role='user',content=json.dumps(payload,ensure_ascii=False))],
        tools=[tool],tool_choice=dict(type='function',function=dict(name='emit_corrective_option')),
        temperature=0,max_tokens=32768,stream=True,stream_options=dict(include_usage=True))
    return request, selected


def effect_counterexamples(source, trace):
    """Find repeated decisions ignoring a changed, publicly witnessed effect.

    This is a bounded localization heuristic for learning an edit, not proof
    of causal responsibility. It recognizes JSON `new_<field>` receipts and
    direct/subscript reads in the handler and its non-state helpers. An empty
    result means abstain; it must not default to the last controller state.
    """
    functions={n.name:n for n in check_source(source).body if isinstance(n,ast.FunctionDef)}
    def reads(name,visited=None):
        visited=set() if visited is None else visited
        if name in visited or name not in functions:return set()
        visited.add(name);fields=set()
        for n in ast.walk(functions[name]):
            if isinstance(n,ast.Call):
                if isinstance(n.func,ast.Attribute) and n.func.attr=='get' and n.args:
                    if isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str):fields.add(n.args[0].value)
                if isinstance(n.func,ast.Name) and not n.func.id.startswith('node_'):
                    fields.update(reads(n.func.id,visited))
            if isinstance(n,ast.Subscript) and isinstance(n.slice,ast.Constant) and isinstance(n.slice.value,str):
                fields.add(n.slice.value)
        return fields
    payloads=[];previous={};cases=[]
    for i,item in enumerate(trace):
        messages=item.get('observation',{}).get('messages') or []
        message=messages[-1] if messages else {}
        data=None
        if message.get('role')=='tool' and message.get('requestor','assistant')=='assistant' and not message.get('error'):
            try:data=json.loads(message.get('content',''))
            except (TypeError,ValueError):pass
        payloads.append(data if type(data) is dict else {})
        target='node_'+str(item.get('memory_before',{}).get('node',''))
        if target not in functions or type(data) is not dict:continue
        decision=item.get('decision',{})
        operation={k:decision.get(k) for k in ['kind','name','arguments']}
        key=(target,json.dumps(operation,sort_keys=True,allow_nan=False))
        if key in previous:
            before_index,before=previous[key]
            changed={k for k in data.keys() & before.keys() if data[k]!=before[k]}
            unread=changed-reads(target);witnesses={}
            for j in range(before_index+1,i):
                for field in unread:
                    if 'new_'+field in payloads[j] and payloads[j]['new_'+field]==data[field]:
                        witnesses.setdefault(field,[]).append(j)
            if witnesses:
                cases.append(dict(target=target,before_index=before_index,after_index=i,
                    unread_effect_fields=sorted(witnesses),effect_receipt_indices=sorted({j for indexes in witnesses.values() for j in indexes}),
                    before=copy.deepcopy(before),after=copy.deepcopy(data),repeated_operation=copy.deepcopy(operation)))
        previous[key]=(i,copy.deepcopy(data))
    return cases


def feedback_update_request(materials, *, localized, model):
    """Same public evidence/model/cap; optionally select an effect counterexample.

    The derived location adds no observation or oracle label. It constrains
    a proposed edit; actual continuation and transfer must decide utility.
    """
    if type(localized) is not bool:raise ValueError('explicit update rule required')
    instruction='''Revise the supplied executable corrective controller using the complete real public failure and success continuations. Their outcome labels supervise whole continuations, not an isolated action. The current original controller, tools, policy and all public evidence are supplied equally to both update rules. Do not invent hidden state or a reference solution.
Return emit_revision with edits=[{target:existing_function_name,replacement:complete_Python_def}], additions=[complete definitions of fresh pure helpers or node_<state> handlers], rationale and evidence. At most eight existing functions may be edited. Empty edits/additions are permitted if the feedback does not justify an update. Use compact edits, not a full rewrite. Preserve entity/parameter bindings, legal assistant versus customer actions, consent and completed progress. No hardcoded source IDs, quantities or outcomes; use runtime observations. The functions see observation and JSON memory. json/re/math and ordinary basic builtins are already bound; no IO, private names or other imports. Full task success and formation plus execution cost will decide acceptance, not syntax or wording. Explain which observed continuation supports any replacement and when it should abstain.'''
    selected=None
    if localized:
        cases=effect_counterexamples(materials['program'],materials['failure_trace'])
        if not cases:raise ValueError('no effect counterexample: abstain before a model request')
        selected=cases[0]
        instruction+='\nEffect-conditioned refinement rule: the deterministic public-trace/read-footprint analysis below located a repeated decision that ignores a changed witnessed effect. If you propose any edit, it must include '+selected['target']+'. Learn an appropriate condition and remaining continuation from the supplied real success/failure evidence, rather than merely blocking all later use or editing the final yield. Other justified edits remain allowed within the same eight-function cap. The proposed location is a heuristic, not a causal fact.\nDerived location: '+json.dumps(selected,ensure_ascii=False)
    else:
        instruction+='\nOrdinary feedback-edit rule: choose the most effective repairs anywhere in the controller from the same complete public traces; no location restriction is imposed. You may revise guards, continuation logic or stopping behavior.'
    props=dict(edits=dict(type='array',items=dict(type='object',properties=dict(target=dict(type='string'),replacement=dict(type='string')),required=['target','replacement'])),additions=dict(type='array',items=dict(type='string')),rationale=dict(type='string'),evidence=dict(type='string'))
    tool=dict(type='function',function=dict(name='emit_revision',description='Propose an executable feedback update.',parameters=dict(type='object',properties=props,required=list(props))))
    request=dict(model=model,messages=[dict(role='system',content=instruction),dict(role='user',content=json.dumps(materials,ensure_ascii=False))],tools=[tool],tool_choice=dict(type='function',function=dict(name='emit_revision')),temperature=0,max_tokens=32768,stream=True,stream_options=dict(include_usage=True))
    return request,selected


def refine_state(source, target, replacement, additions=()):
    """Replace one named decision handler and add new handlers, leaving others intact.

    A split creates a new controller state in code, not an inferred world fact.
    Calling this function alone is not evidence that the edit improves execution.
    """
    old = check_source(source)
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', target or ''):
        raise ValueError('refinement must name one decision handler')
    selected = [n for n in old.body if isinstance(n, ast.FunctionDef) and n.name == target]
    if len(selected) != 1:
        raise ValueError('target handler is absent or duplicated')
    new = ast.parse(replacement)
    if len(new.body) != 1 or not isinstance(new.body[0], ast.FunctionDef) or new.body[0].name != target:
        raise ValueError('replacement must define exactly the targeted handler')
    existing = {n.name for n in old.body if isinstance(n, ast.FunctionDef)}
    extra = []
    for text in additions:
        parsed = ast.parse(text)
        if not parsed.body or not all(isinstance(n,ast.FunctionDef) for n in parsed.body):
            raise ValueError('additions must contain only function definitions')
        for n in parsed.body:
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',n.name) or n.name in existing:
                raise ValueError('new helper/handler must have a fresh name')
            existing.add(n.name); extra.append(n)
    for i,n in enumerate(old.body):
        if n is selected[0]:old.body[i] = new.body[0]
    old.body.extend(extra)
    # An edited state may have been implemented by an inline yield in step.
    # Bind that state to its edited handler; do not leave a dormant replacement.
    state_handlers=([new.body[0]] if target.startswith('node_') else [])
    state_handlers += [n for n in extra if n.name.startswith('node_')]
    if state_handlers:
        router=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='step')
        if len(router.args.args)!=2:
            raise ValueError('step requires observation and memory parameters')
        obs_name,mem_name=[a.arg for a in router.args.args]
        # Locate the original router's node variable, keeping preceding guards.
        node_vars=set()
        for statement in router.body:
            if isinstance(statement,ast.Assign) and isinstance(statement.value,ast.Call):
                call=statement.value
                if (isinstance(call.func,ast.Attribute) and call.func.attr=='get'
                        and isinstance(call.func.value,ast.Name) and call.func.value.id==mem_name
                        and call.args and isinstance(call.args[0],ast.Constant) and call.args[0].value=='node'):
                    node_vars.update(t.id for t in statement.targets if isinstance(t,ast.Name))
        routes=[]
        for n in state_handlers:
            state=n.name[len('node_'):]
            route=ast.parse("if "+mem_name+".get('node') == "+repr(state)+":\n    return "+n.name+"("+obs_name+", "+mem_name+")\n").body[0]
            found=False
            for statement in router.body:
                test=statement.test if isinstance(statement,ast.If) else None
                if (isinstance(test,ast.Compare) and len(test.ops)==1 and isinstance(test.ops[0],ast.Eq)
                        and len(test.comparators)==1 and isinstance(test.comparators[0],ast.Constant)
                        and test.comparators[0].value==state and isinstance(test.left,ast.Name)
                        and test.left.id in node_vars):
                    statement.body=route.body;found=True;break
            if not found:routes.append(route)
        at=len(router.body)-1 if router.body and isinstance(router.body[-1],ast.Return) else len(router.body)
        router.body[at:at]=routes
        terminal=ast.parse("if "+obs_name+".get('done'):\n    return {'kind':'stop','memory':"+mem_name+"}\n").body[0]
        router.body.insert(0,terminal)
    old=ast.fix_missing_locations(old)
    result = ast.unparse(old) + '\n'
    check_source(result)
    return result, {'parent_sha256': hashlib.sha256(source.encode()).hexdigest(),
                    'target': target, 'added_functions': [n.name for n in extra],
                    'added_states': [n.name for n in extra if n.name.startswith('node_')],
                    'wired_states': [n.name[len('node_'):] for n in state_handlers],
                    'candidate_sha256': hashlib.sha256(result.encode()).hexdigest()}
