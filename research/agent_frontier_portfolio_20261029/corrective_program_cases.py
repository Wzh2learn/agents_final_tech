"""Source-representation probes for executable corrective programs.

These views are correlated representations of exposed sources, not independent
benchmark tasks. Run ``probe`` only inside the owned offline container when the
file under test was written by a model. Native project tests remain separate.
"""
from __future__ import annotations

import argparse
import ast
from collections import namedtuple
import copy
import json
from pathlib import Path


VIEWS = {
    'canonical': ('SourceCarrier', '_path2d', '_original_path', None),
    'train_alias': ('ContourCarrier', '_cached_projection', '_saved_outline', '_active'),
    'check_alias': ('SceneGlyph', '_display_shape', '_source_shape', '_receiver'),
}


def source_view(source, kind, view):
    """Change local representation, keeping public method signatures intact."""
    class_name, projected, original, alias = VIEWS[view]
    if kind == 'plot':
        tree = ast.parse(source['before_class'])
        cls = tree.body[0]
    elif kind == 'iterable':
        fn = ast.parse(source['before_function']).body[0]
        cls = ast.ClassDef(name='SourceCarrier', bases=[], keywords=[], body=[fn],
                           decorator_list=[])
        tree = ast.Module(body=[cls], type_ignores=[])
    else:
        raise ValueError('unknown source kind')
    cls.name = class_name
    attributes = {'_path2d': projected, '_original_path': original}

    class Representation(ast.NodeTransformer):
        def visit_Attribute(self, node):
            self.generic_visit(node)
            node.attr = attributes.get(node.attr, node.attr)
            return node

        def visit_Constant(self, node):
            if isinstance(node.value, str) and node.value in attributes:
                node.value = attributes[node.value]
            return node

    tree = Representation().visit(tree)
    if alias:
        fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
                  and n.name == ('get_path' if kind == 'plot' else 'resolve_lookup_value'))
        occupied = {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}
        occupied.update(a.arg for a in fn.args.args)
        if alias in occupied:
            raise ValueError('alias would capture an existing name')
        receiver = fn.args.args[0].arg

        class Alias(ast.NodeTransformer):
            def visit_Name(self, node):
                if node.id == receiver and isinstance(node.ctx, ast.Load):
                    return ast.copy_location(ast.Name(id=alias, ctx=ast.Load()), node)
                return node

        fn.body = [Alias().visit(n) for n in fn.body]
        fn.body.insert(0, ast.Assign(targets=[ast.Name(id=alias, ctx=ast.Store())],
                                   value=ast.Name(id=receiver, ctx=ast.Load())))
    ast.fix_missing_locations(tree)
    code = ast.unparse(tree) + '\n'
    return code, dict(kind=kind, class_name=class_name, projected=projected,
                      original=original,
                      method='get_path' if kind == 'plot' else 'resolve_lookup_value')


def probe(path, metadata):
    """Execute the declared public function witnesses, without importing a repo."""
    tree = ast.parse(Path(path).read_text())
    # Parsing alone permits constructs such as a return in a class body. Check
    # the whole module without executing its imports or class definitions.
    compile(tree, str(path), 'exec')
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == metadata['class_name'])
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef)
              and n.name == metadata['method'])
    if fn.decorator_list:
        raise ValueError('probe does not execute decorators')
    module = ast.Module(body=[copy.deepcopy(fn)], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {}
    exec(compile(module, '<public-source-function>', 'exec'), namespace)
    method = namespace[metadata['method']]
    receiver_type = type(metadata['class_name'], (), {metadata['method']: method})
    rows = []

    def check(name, operation):
        try:
            passed = bool(operation())
            rows.append(dict(name=name, passed=passed, error=None))
        except Exception as exc:
            rows.append(dict(name=name, passed=False, error=type(exc).__name__,
                             message=str(exc)))

    if metadata['kind'] == 'plot':
        a, b = metadata['projected'], metadata['original']
        for name, present, expected in [
            ('undrawn', (b,), b), ('drawn', (a, b), a),
            ('legacy_drawn_posthoc', (a,), a),
        ]:
            obj = receiver_type()
            objects = {key: object() for key in present}
            for key, value in objects.items():
                setattr(obj, key, value)
            check(name, lambda obj=obj, objects=objects, expected=expected:
                  method(obj) is objects[expected])
    else:
        class Expression:
            def __init__(self, value):
                self.value = value

            def resolve_expression(self, *args, **kwargs):
                return self.value

        obj = receiver_type()
        pair = namedtuple('Pair', 'a b')
        for name, value, expected in [
            ('ordinary_tuple', (Expression(2), Expression(3)), (2, 3)),
            ('namedtuple', pair(Expression(2), Expression(3)), (2, 3)),
            ('list', [Expression(2), Expression(3)], [2, 3]),
            ('scalar', 7, 7),
        ]:
            # Source-native tests accept both flatten and guarded construction;
            # do not invent a requirement to preserve the namedtuple subtype.
            check(name, lambda value=value, expected=expected:
                  method(obj, value, None, True) == expected)
    return dict(rows=rows, passed=all(r['passed'] for r in rows),
                scope='Source-function witnesses only; not native project grading.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=Path)
    parser.add_argument('metadata', type=Path)
    args = parser.parse_args()
    result = probe(args.file, json.loads(args.metadata.read_text()))
    print('SOURCE_PROBE=' + json.dumps(result))


if __name__ == '__main__':
    main()
