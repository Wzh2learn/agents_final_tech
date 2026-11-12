"""Source-stage control: induce a guarded program from executed partial repairs.

The finite grammar is classical decision-stump induction, not a novelty claim.
Unlike whole-episode preference ranking, complementary failed repairs can supply
program-level success constraints. Independent task grading remains separate.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
import hashlib
import json
import textwrap


@dataclass(frozen=True)
class GuardedChoice:
    predicate: str | None
    when_true: str
    when_false: str
    unresolved_cases: tuple[str, ...]
    equivalent_solutions: int


def learn_guard(rows):
    """Prefer a single globally valid fragment; otherwise fit one Boolean split.

    Rows contain pre-execution public Boolean features and the measured outcome
    of each complete candidate program on that case. A case all programs fail is
    reported unresolved, never converted into an arbitrary preference label.
    """
    rows = list(rows)
    if not rows:
        return None
    ids = [r['case'] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate execution case')
    candidates = sorted(rows[0]['success'])
    keys = sorted(rows[0]['features'])
    if not candidates:
        raise ValueError('missing executable candidates')
    for row in rows:
        if sorted(row['success']) != candidates or sorted(row['features']) != keys:
            raise ValueError('inconsistent candidate or observable-feature schema')
        if any(type(v) is not bool for v in [*row['features'].values(), *row['success'].values()]):
            raise ValueError('unknown observations cannot be silently labelled false')
    unresolved = tuple(r['case'] for r in rows if not any(r['success'].values()))
    useful = [r for r in rows if any(r['success'].values())]
    if not useful:
        return None
    global_choices = [c for c in candidates if all(r['success'][c] for r in useful)]
    if global_choices:
        winner = global_choices[0]
        return GuardedChoice(None, winner, winner, unresolved, len(global_choices))
    solutions = []
    for key in keys:
        partitions = [[r for r in useful if r['features'][key] is v] for v in (True,False)]
        if not all(partitions):
            continue
        good = [[c for c in candidates if all(r['success'][c] for r in part)] for part in partitions]
        for a in good[0]:
            for b in good[1]:
                solutions.append((key,a,b))
    if not solutions:
        return None
    key,a,b = sorted(solutions)[0]  # Fixed pre-result tie rule, not identifiability.
    return GuardedChoice(key,a,b,unresolved,len(solutions))


def compile_guarded_block(source, *, function_name, anchor_test, candidate_blocks, predicate_bindings, choice):
    """Replace only the admitted statement block; source-specific names are bindings.

    No generated code is executed here. Outputs must be checked in an isolated
    source environment and then scored by the independent native task grader.
    """
    tree = ast.parse(source)
    functions = [n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==function_name]
    if len(functions)!=1:
        raise ValueError('ambiguous or missing source function')
    expected = ast.dump(ast.parse(anchor_test,mode='eval').body,include_attributes=False)
    anchors = [n for n in ast.walk(functions[0]) if isinstance(n,ast.If) and ast.dump(n.test,include_attributes=False)==expected]
    if len(anchors)!=1:
        raise ValueError('ambiguous or missing source anchor')
    anchor = anchors[0]
    def block(name):
        value = textwrap.dedent(candidate_blocks[name]).strip()+'\n'
        if not ast.parse(value).body:
            raise ValueError('empty executable fragment')
        return value
    if choice.predicate is None:
        generated = block(choice.when_true)
    else:
        condition = predicate_bindings[choice.predicate]
        ast.parse(condition,mode='eval')
        generated = ('if '+condition+':\n'+textwrap.indent(block(choice.when_true),'    ')
                     +'else:\n'+textwrap.indent(block(choice.when_false),'    '))
    first,last = anchor.body[0],anchor.body[-1]
    lines = source.splitlines(keepends=True)
    replacement = textwrap.indent(generated,' '*first.col_offset)+'\n'
    result = ''.join(lines[:first.lineno-1])+replacement+''.join(lines[last.end_lineno:])
    ast.parse(result)
    return result


def compile_guarded_predicate(source, *, function_name, anchor_test, predicate_bindings, choice,
                              then_candidate='then', rest_candidate='rest'):
    """Learn when to take an existing branch, preserving both branch procedures."""
    functions=[n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name==function_name]
    if len(functions)!=1:
        raise ValueError('ambiguous or missing source function')
    expected=ast.dump(ast.parse(anchor_test,mode='eval').body,include_attributes=False)
    anchors=[n for n in ast.walk(functions[0]) if isinstance(n,ast.If) and ast.dump(n.test,include_attributes=False)==expected]
    if len(anchors)!=1:
        raise ValueError('ambiguous or missing source anchor')
    if not {choice.when_true,choice.when_false}<={then_candidate,rest_candidate}:
        raise ValueError('choice does not refer to the admitted branch procedures')
    if choice.predicate is None:
        condition='True' if choice.when_true==then_candidate else 'False'
    else:
        value=predicate_bindings[choice.predicate]
        condition=value if choice.when_true==then_candidate else 'not ('+value+')'
    ast.parse(condition,mode='eval')
    node=anchors[0].test
    # AST columns are UTF-8 byte offsets, not Unicode character offsets.
    lines=source.encode('utf-8').splitlines(keepends=True)
    begin=sum(map(len,lines[:node.lineno-1]))+node.col_offset
    end=sum(map(len,lines[:node.end_lineno-1]))+node.end_col_offset
    raw=b''.join(lines)
    output=(raw[:begin]+condition.encode('utf-8')+raw[end:]).decode('utf-8')
    ast.parse(output)
    return output


def apply_fragment_edits(source, edits):
    """Apply non-overlapping, whole-statement edits to an admitted snapshot."""
    lines = source.splitlines(keepends=True)
    boundary = len(lines)
    for start, end, replacement in sorted(edits, key=lambda e:e[0], reverse=True):
        if not (0 <= start <= end <= boundary):
            raise ValueError('overlapping or invalid fragment edits')
        lines[start:end] = [replacement]
        boundary = start
    result = ''.join(lines)
    compile(result, '<generated-correction>', 'exec')
    return result


def _replace_names(node, bindings):
    class Rename(ast.NodeTransformer):
        def visit_Name(self, value):
            if value.id not in bindings:
                return value
            replacement = copy.deepcopy(bindings[value.id])
            if isinstance(replacement, ast.Name):
                replacement.ctx = value.ctx
            elif not isinstance(value.ctx, ast.Load):
                raise ValueError('cannot assign into a rebound role')
            return ast.copy_location(replacement, value)
    return Rename().visit(copy.deepcopy(node))


def _located_call(tree, event):
    scopes = tree.body
    if event['caller_owner'] is not None:
        classes = [n for n in scopes if isinstance(n, ast.ClassDef)
                   and n.name == event['caller_owner']]
        if len(classes) != 1:
            raise ValueError('ambiguous caller owner')
        scopes = classes[0].body
    functions = [n for n in scopes if isinstance(n, ast.FunctionDef)
                 and n.name == event['caller_function']]
    if len(functions) != 1:
        raise ValueError('ambiguous caller function')
    scope = functions[0]
    calls = [n for n in ast.walk(scope) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == event['runtime_class']
             and n.lineno <= event['caller_line'] <= n.end_lineno]
    if len(calls) != 1:
        raise ValueError('ambiguous constructor call at executed location')
    return scope, calls[0]


def _enclosing_statement(node, parents):
    while not isinstance(node, ast.stmt):
        node = parents[node]
    return node


def _field_expression(scope, call, field, parents, covered):
    for keyword in call.keywords:
        if keyword.arg == field:
            return keyword.value, _enclosing_statement(call, parents)
        if keyword.arg is None and isinstance(keyword.value, ast.Name):
            choices = []
            for n in ast.walk(scope):
                if not (isinstance(n, ast.Assign) and n.lineno < call.lineno
                        and any(isinstance(t, ast.Name) and t.id == keyword.value.id
                                for t in n.targets) and isinstance(n.value, ast.Dict)):
                    continue
                if covered and n.lineno not in covered:
                    continue
                for key, value in zip(n.value.keys, n.value.values):
                    if isinstance(key, ast.Constant) and key.value == field:
                        choices.append((value, n))
            if len(choices) != 1:
                raise ValueError('ambiguous executed keyword-field producer')
            return choices[0]
    raise ValueError('observed field is not supplied by a supported donor expression')


def _backward_slice(value, anchor, parents, role_aliases, scope):
    if not isinstance(value, ast.Name):
        raise ValueError('fragment grammar requires a named computed field')
    block = next((items for _, items in ast.iter_fields(parents[anchor])
                  if isinstance(items, list) and anchor in items), None)
    if block is None:
        raise ValueError('missing donor statement block')
    wanted = {value.id}
    chosen = []
    # Supported mutations are explicit list/set/dict updates. Other side
    # effects are outside this restricted slice grammar, not assumed pure.
    mutators = {'append','extend','insert','add','update','setdefault'}
    for statement in reversed(block[:block.index(anchor)]):
        writes = {n.id for n in ast.walk(statement)
                  if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        mutations = {n.func.value.id for n in ast.walk(statement)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and isinstance(n.func.value, ast.Name) and n.func.attr in mutators}
        if not (wanted - role_aliases) & (writes | mutations):
            continue
        chosen.append(statement)
        reads = {n.id for n in ast.walk(statement)
                 if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        wanted = (wanted - writes) | (reads - writes)
    if not chosen:
        raise ValueError('no executable donor computation was extracted')
    locals_ = {n.id for n in ast.walk(scope)
               if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    if (wanted - role_aliases) & locals_:
        raise ValueError('slice has unresolved local dependencies')
    return list(reversed(chosen))


def _sequence_projection(block, output):
    if len(block) != 1:
        raise ValueError('unsupported sequence projection body')
    n = block[0]
    if isinstance(n, ast.If):
        return ast.IfExp(test=copy.deepcopy(n.test),
                         body=_sequence_projection(n.body, output),
                         orelse=_sequence_projection(n.orelse, output))
    if (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Attribute)
            and isinstance(n.value.func.value, ast.Name)
            and n.value.func.value.id == output and n.value.func.attr == 'append'
            and len(n.value.args) == 1 and not n.value.keywords):
        return copy.deepcopy(n.value.args[0])
    raise ValueError('unsupported sequence projection operation')


def _origin_binding(scope, target_call, parents, fresh):
    """Recover a preceding sequence projection without hardcoding API types."""
    target_loop = parents[target_call]
    while target_loop is not scope and not isinstance(target_loop, ast.For):
        target_loop = parents[target_loop]
    if not (isinstance(target_loop, ast.For) and isinstance(target_loop.iter, ast.Name)):
        return None
    sequence = target_loop.iter.id
    assignments = [n for n in ast.walk(scope) if isinstance(n, ast.Assign)
                   and n.lineno < target_loop.lineno and isinstance(n.value, ast.Name)
                   and any(isinstance(t, ast.Name) and t.id == sequence for t in n.targets)]
    if len(assignments) != 1:
        return None
    assignment = assignments[0]
    output = assignment.value.id
    producers = [n for n in ast.walk(scope) if isinstance(n, ast.For)
                 and n.lineno < assignment.lineno and isinstance(n.iter, ast.Name)
                 and n.iter.id == sequence and isinstance(n.target, ast.Name)]
    if len(producers) != 1:
        return None
    producer = producers[0]
    projection = _sequence_projection(producer.body, output)
    original, key, mapping, saved = [fresh(n) for n in ('original','key','origins','sequence')]
    expression = ast.unparse(_replace_names(projection, {producer.target.id:ast.Name(id=original,ctx=ast.Load())}))
    # Save a one-shot iterator once; preserve the original normalization loop.
    prefix = (f'{saved} = tuple({sequence})\n{mapping} = {{}}\n'
              f'for {original} in {saved}:\n'
              f'    {key} = {expression}\n'
              f'    {mapping}.setdefault({key}, []).append({original})\n')
    loop = copy.deepcopy(producer)
    loop.iter = ast.Name(id=saved, ctx=ast.Load())
    prefix += ast.unparse(ast.fix_missing_locations(loop)) + '\n'
    edit = [producer.lineno-1, producer.end_lineno,
            textwrap.indent(prefix, ' '*producer.col_offset)]
    argument = ast.unparse(target_call.args[0])
    return (f'{mapping}[{argument}][0]',
            f'len({mapping}.get({argument}, ())) == 1', edit)


def learn_execution_fragments(source, donor, recipient, *, relative_path, covered_lines=(),
                              execution_feedback=()):
    """Generate complete candidate programs from one witnessed field contrast.

    The declared search grammar is local backward slicing plus two role
    bindings: the current argument, and its original object before a witnessed
    sequence normalization. This is a classical source-stage component, not
    independently demonstrated Agent learning or a new program-synthesis claim.
    Trace repr strings, task IDs, dimensions and object addresses are never code.
    """
    from pathlib import PurePosixPath
    path = PurePosixPath(relative_path)
    if path.is_absolute() or '..' in path.parts or '\\' in relative_path or ':' in relative_path:
        raise ValueError('expected a workspace-relative source path')
    tree = ast.parse(source)
    parents = {child:parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    scope, good_call = _located_call(tree, donor)
    other, bad_call = _located_call(tree, recipient)
    if other is not scope or not good_call.args or not bad_call.args:
        raise ValueError('constructor contrast must share a caller scope')
    if not isinstance(good_call.args[0], ast.Name):
        raise ValueError('first constructor argument must be a witnessed name')
    parameters = [key for key,aliases in donor['argument_aliases'].items()
                  if good_call.args[0].id in aliases]
    if len(parameters) != 1:
        raise ValueError('ambiguous constructor object role')
    role_aliases = set(donor['argument_aliases'][parameters[0]])
    changed = [key for key,value in donor['arguments'].items()
               if value['type'] != 'NoneType'
               and recipient['arguments'].get(key,{}).get('type') == 'NoneType']
    if len(changed) != 1:
        raise ValueError('expected one witnessed missing field')
    field = changed[0]
    value, anchor = _field_expression(scope, good_call, field, parents, set(covered_lines))
    if not (isinstance(value, ast.Name)
            and value.id in donor['argument_aliases'].get(field,[])):
        raise ValueError('field expression lacks an executed identity alias')
    fragment = _backward_slice(value, anchor, parents, role_aliases, scope)
    attributes = sorted({n.attr for stmt in fragment for n in ast.walk(stmt)
                         if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                         and n.value.id in role_aliases})
    if not attributes:
        raise ValueError('donor fragment has no observable role requirement')
    iterated = {n.iter.attr for stmt in fragment for n in ast.walk(stmt)
                if isinstance(n,ast.For) and isinstance(n.iter,ast.Attribute)
                and isinstance(n.iter.value,ast.Name) and n.iter.value.id in role_aliases}
    # A completed None-iteration counterexample adds a predicate to the
    # declared grammar. It does not retroactively relabel old executions.
    nullable = sorted({row.get('role_attribute') for row in execution_feedback
                       if row.get('completed') is True and row.get('operation') == 'iterate'
                       and row.get('exception_type') == 'TypeError'
                       and row.get('observed_type') == 'NoneType'} & iterated)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    def fresh(label):
        name = '_fccl_' + label
        while name in names:
            name += '_'
        names.add(name)
        return name
    renames = {name:ast.Name(id=fresh(name),ctx=ast.Load())
               for name in sorted({n.id for stmt in fragment for n in ast.walk(stmt)
                                    if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Store)})}
    current = ast.unparse(bad_call.args[0])
    bindings = [('current', current, None, None)]
    origin = _origin_binding(scope, bad_call, parents, fresh)
    if origin is not None:
        bindings.append(('origin', *origin))
    statement = _enclosing_statement(bad_call, parents)
    if source.splitlines()[statement.lineno-1][:statement.col_offset].strip():
        raise ValueError('inline compound statements are outside the edit grammar')
    candidates = []
    for mode, binding, precondition, extra in bindings:
        mapping = dict(renames, **{alias:ast.parse(binding,mode='eval').body for alias in role_aliases})
        body = [_replace_names(stmt, mapping) for stmt in fragment]
        field_value = _replace_names(value, mapping)
        class SupplyField(ast.NodeTransformer):
            def visit_Call(self, n):
                if (n.lineno,n.col_offset) == (bad_call.lineno,bad_call.col_offset):
                    if any(k.arg == field or k.arg is None for k in n.keywords):
                        raise ValueError('recipient has an unresolved keyword supplier')
                    n.keywords.append(ast.keyword(arg=field,value=copy.deepcopy(field_value)))
                return self.generic_visit(n)
        body.append(SupplyField().visit(copy.deepcopy(statement)))
        guard = ' and '.join(f'hasattr({binding}, {attribute!r})' for attribute in attributes)
        if precondition:
            guard = precondition + ' and ' + guard
        predicates=[('exists',guard)]
        if nullable:
            predicates.append(('not_none', guard+' and '+' and '.join(
                f'getattr({binding}, {attribute!r}) is not None' for attribute in nullable)))
        for kind,predicate in predicates:
            replacement = ast.If(test=ast.parse(predicate,mode='eval').body, body=copy.deepcopy(body),
                                 orelse=[copy.deepcopy(statement)])
            rendered = ast.unparse(ast.fix_missing_locations(replacement)) + '\n'
            edits = [[statement.lineno-1,statement.end_lineno,
                      textwrap.indent(rendered,' '*statement.col_offset)]]
            if extra:
                edits.append(extra)
            after = apply_fragment_edits(source, edits)
            after_hash = hashlib.sha256(after.encode('utf-8')).hexdigest()
            candidates.append(dict(id=after_hash[:16],binding=mode,field=field,guard_kind=kind,
                guard=predicate,fragment=ast.unparse(ast.Module(body=body[:-1],type_ignores=[])),
                relative_path=path.as_posix(),before_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),
                after_sha256=after_hash,edits=edits))
    return candidates


def update_fragment_candidates(candidates, outcomes, *, required_cases):
    """Only completed full-program counterexamples eliminate a candidate."""
    ids = [c['id'] for c in candidates]
    if len(set(ids)) != len(ids) or not required_cases or len(set(required_cases)) != len(required_cases):
        raise ValueError('unique candidates and nonempty required cases needed')
    values = {}
    for row in outcomes:
        key = row['candidate'],row['case']
        if row['candidate'] not in ids or key in values:
            raise ValueError('unknown candidate or duplicate execution outcome')
        if row['passed'] is not None and type(row['passed']) is not bool:
            raise ValueError('execution outcomes must be Boolean or unknown')
        values[key] = row['passed']
    rejected = [c for c in ids if any(v is False for (k,_),v in values.items() if k == c)]
    eligible = [c for c in ids if c not in rejected
                and all(values.get((c,k)) is True for k in required_cases)]
    return dict(eligible=eligible,rejected=rejected,
                pending=[c for c in ids if c not in rejected and c not in eligible])


def render_fragment_cli(candidate):
    """Render a dependency-free Python 3.8 CLI; generation does not execute it."""
    return '''import argparse, ast, hashlib, json, os
from pathlib import Path
PLAN = ''' + repr(candidate) + '''
p = argparse.ArgumentParser()
p.add_argument('--root', required=True)
args = p.parse_args()
root = Path(args.root).resolve()
path = (root / PLAN['relative_path']).resolve()
if root not in path.parents:
    raise ValueError('source path escaped workspace')
raw = path.read_bytes()
before = hashlib.sha256(raw).hexdigest()
if before == PLAN['after_sha256']:
    print(json.dumps({'status':'ALREADY_APPLIED','candidate':PLAN['id']}))
    raise SystemExit(0)
if before != PLAN['before_sha256']:
    raise ValueError('source snapshot changed; return to ordinary correction')
lines = raw.decode('utf-8').splitlines(keepends=True)
boundary = len(lines)
for start, end, replacement in sorted(PLAN['edits'], key=lambda e:e[0], reverse=True):
    if not 0 <= start <= end <= boundary:
        raise ValueError('overlapping edits')
    lines[start:end] = [replacement]
    boundary = start
result = ''.join(lines).encode('utf-8')
if hashlib.sha256(result).hexdigest() != PLAN['after_sha256']:
    raise ValueError('generated output hash mismatch')
compile(result, str(path), 'exec')
temporary = path.with_name(path.name + '.fccl-tmp')
with temporary.open('xb') as handle:
    handle.write(result)
os.replace(str(temporary), str(path))
print(json.dumps({'status':'APPLIED_NOT_TEST_VERIFIED','candidate':PLAN['id']}))
'''


def main():
    import argparse
    import hashlib
    import json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-file',required=True)
    parser.add_argument('--evidence',required=True)
    parser.add_argument('--bindings',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    source=Path(args.source_file).read_bytes()
    bindings=json.loads(Path(args.bindings).read_text())
    if hashlib.sha256(source).hexdigest()!=bindings['expected_source_sha256']:
        raise ValueError('current source differs from the admitted binding')
    rows=json.loads(Path(args.evidence).read_text())
    if not rows or any(set(r['features'])!=set(bindings['predicate_bindings']) for r in rows):
        raise ValueError('execution features differ from the admitted predicate grammar')
    choice=learn_guard(rows)
    if choice is None or choice.unresolved_cases:
        print(json.dumps(dict(status='NO_COMPLETE_CONSISTENT_PROGRAM')))
        return 2
    common=dict(function_name=bindings['function_name'],anchor_test=bindings['anchor_test'],
                predicate_bindings=bindings['predicate_bindings'],choice=choice)
    if bindings.get('mode','block')=='predicate':
        program=compile_guarded_predicate(source.decode('utf-8'),**common)
    else:
        program=compile_guarded_block(source.decode('utf-8'),candidate_blocks=bindings['candidate_blocks'],**common)
    with Path(args.output).open('x',encoding='utf-8',newline='\n') as out:
        out.write(program)
    print(json.dumps(dict(status='COMPILED_NOT_EXECUTION_VERIFIED',choice=choice.__dict__,
        program_sha256=hashlib.sha256(Path(args.output).read_bytes()).hexdigest())))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
