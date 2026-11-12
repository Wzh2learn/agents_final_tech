"""Restricted Getafix-style structural reference, not a novel induction method.

Infer one guarded False -> NotImplemented equality edit from an actual before/
after pair, then bind it at every statically admitted position. The normalization
grammar is researcher supplied. It supports equivalent if/else/early-return and
leading short-circuit type guards; it does not synthesize arbitrary Python.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def methods(text):
    for cls in ast.walk(ast.parse(text)):
        if isinstance(cls, ast.ClassDef):
            for fn in cls.body:
                if isinstance(fn, ast.FunctionDef) and fn.name == '__eq__':
                    yield cls, fn


def learn(before, after):
    candidates = []
    before_methods = {(c.name, f.name): f for c, f in methods(before)}
    for cls, fn in methods(after):
        old = before_methods.get((cls.name, fn.name))
        if old is None or len(fn.args.args) != 2:
            continue
        restored = copy.deepcopy(fn)
        changes = [n for n in ast.walk(restored) if isinstance(n, ast.Return)
                   and isinstance(n.value, ast.Name) and n.value.id == 'NotImplemented']
        if len(changes) != 1:
            continue
        changes[0].value = ast.Constant(value=False, kind=None)
        if ast.dump(old) == ast.dump(restored):
            parameter = fn.args.args[1].arg
            guards = [n.test for n in ast.walk(old) if isinstance(n, ast.If)
                      and isinstance(n.test, ast.UnaryOp) and isinstance(n.test.op, ast.Not)
                      and isinstance(n.test.operand, ast.Call)
                      and isinstance(n.test.operand.func, ast.Name)
                      and n.test.operand.func.id == 'isinstance'
                      and len(n.test.operand.args) == 2
                      and isinstance(n.test.operand.args[0], ast.Name)
                      and n.test.operand.args[0].id == parameter
                      and isinstance(n.test.operand.args[1], ast.Name)
                      and n.test.operand.args[1].id == cls.name]
            if guards:
                candidates.append(dict(method=fn.name, other_argument=1,
                                       type_role='receiver class', old=False,
                                       new='NotImplemented', source_class=cls.name))
    assert len(candidates) == 1, 'one exact, source-observed guarded edit required'
    return candidates[0]


def bind(text, schema):
    edits = {}
    lines = text.encode().splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))

    def span(node):
        return (starts[node.lineno - 1] + node.col_offset,
                starts[node.end_lineno - 1] + node.end_col_offset)

    for cls, fn in methods(text):
        if fn.name != schema['method'] or len(fn.args.args) != 2:
            continue
        self_name, other = [a.arg for a in fn.args.args]
        if any(isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id == other
               for n in ast.walk(fn)):
            continue

        def type_guard(node):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == 'isinstance' and len(node.args) == 2
                    and isinstance(node.args[0], ast.Name) and node.args[0].id == other):
                return False
            kind = node.args[1]
            return ((isinstance(kind, ast.Name) and kind.id == cls.name)
                    or (isinstance(kind, ast.Attribute) and kind.attr == '__class__'
                        and isinstance(kind.value, ast.Name) and kind.value.id == self_name)
                    or (isinstance(kind, ast.Call) and isinstance(kind.func, ast.Name)
                        and kind.func.id == 'type' and len(kind.args) == 1
                        and isinstance(kind.args[0], ast.Name) and kind.args[0].id == self_name))

        guards = {ast.dump(n) for n in ast.walk(fn) if type_guard(n)}
        if len(guards) > 1:
            continue  # Do not conflate distinct runtime type tests.
        facts = {}
        returns = {}

        def block(statements, states):
            states = set(states)
            for node in statements:
                if not states:
                    break
                if isinstance(node, ast.Return):
                    value = node.value
                    if isinstance(value, ast.Constant) and value.value is False:
                        key = span(value)
                        facts.setdefault(key, set()).update(states)
                        returns[key] = (value, cls.name, fn.name)
                    elif (isinstance(value, ast.BoolOp) and isinstance(value.op, ast.And)
                          and len(value.values) > 1 and type_guard(value.values[0])):
                        guard = ast.get_source_segment(text, value.values[0])
                        rest = ' and '.join('(' + ast.get_source_segment(text, n) + ')'
                                            for n in value.values[1:])
                        edits[span(value)] = dict(replacement='((' + rest + ') if (' + guard + ') else NotImplemented)',
                                                 class_name=cls.name, method=fn.name,
                                                 normal_form='leading type-guard conjunction')
                    states = set()
                elif isinstance(node, ast.Raise):
                    states = set()
                elif isinstance(node, ast.If):
                    guard, positive = node.test, True
                    if isinstance(guard, ast.UnaryOp) and isinstance(guard.op, ast.Not):
                        guard, positive = guard.operand, False
                    if type_guard(guard):
                        yes = {positive} if any(s is None or s == positive for s in states) else set()
                        no = {not positive} if any(s is None or s != positive for s in states) else set()
                    else:
                        yes, no = states, states
                    states = block(node.body, yes) | block(node.orelse, no)
                elif isinstance(node, (ast.Try, ast.For, ast.While, ast.With)):
                    states = {None}  # Unsupported control structure: lose proof, don't guess.
            return states

        block(fn.body, {None})
        for key, states in facts.items():
            if states == {False}:
                edits[key] = dict(replacement='NotImplemented', class_name=cls.name,
                                  method=fn.name, normal_form='unsupported-type return path')
    result = text.encode()
    for (start, end), record in sorted(edits.items(), reverse=True):
        result = result[:start] + record['replacement'].encode() + result[end:]
    ast.parse(result.decode())
    return result, [dict(start=start, end=end, **record) for (start, end), record in sorted(edits.items())]


def main():
    root = Path('/workspace').resolve()
    inputs = root / '.research-inputs'
    before = inputs / 'source_before.py'
    after = inputs / 'source_after.py'
    schema = learn(before.read_text(), after.read_text())
    applied = []
    for path in sorted((root / 'django').rglob('*.py')):
        assert root in path.resolve().parents and not path.is_symlink()
        original = path.read_text()
        updated, bindings = bind(original, schema)
        if bindings:
            old_hash = digest(path)
            path.write_bytes(updated)
            applied.append(dict(file=path.relative_to(root).as_posix(), before_sha256=old_hash,
                                after_sha256=digest(path), bindings=bindings))
    record = dict(scope='Post-hoc source completion and static baseline only', schema=schema,
                  grammar='Researcher-supplied restricted type-guard control-flow normalization',
                  source_before_sha256=digest(before), source_after_sha256=digest(after),
                  files=applied, model_calls=0)
    with (root / '.compiled_binding.json').open('x') as f:
        json.dump(record, f, indent=2)
        f.write('\n')
    print('COMPILED_BINDINGS=' + json.dumps(record))


if __name__ == '__main__':
    main()
