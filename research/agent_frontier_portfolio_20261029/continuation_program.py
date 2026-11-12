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
