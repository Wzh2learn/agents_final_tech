"""Source-stage control: induce a guarded program from executed partial repairs.

The finite grammar is classical decision-stump induction, not a novelty claim.
Unlike whole-episode preference ranking, complementary failed repairs can supply
program-level success constraints. Independent task grading remains separate.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
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
