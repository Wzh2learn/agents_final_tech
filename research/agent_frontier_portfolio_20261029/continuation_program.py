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
