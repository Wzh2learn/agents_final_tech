"""Four bounded repair operators over the existing flat FinQA executor."""
from __future__ import annotations

import math
import re
from finqa_correction import executor


def same_operand(left, right, module):
    if left == right:
        return True
    if left.startswith(('#', '@')) or right.startswith(('#', '@')):
        return False
    try:
        a, b = module.parse_numeric_argument(left), module.parse_numeric_argument(right)
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
    except Exception:
        return False


def apply_patches(program, patches):
    """@i denotes prepended step i; #i in bindings denotes original step i.

    Bindings are simultaneous and affect operands only. Prefix insertion shifts
    original references automatically. No semantic graph or new parser is built.
    """
    if not isinstance(patches, list) or not 1 <= len(patches) <= 8:
        raise ValueError('one to eight patch operations required')
    if any(not isinstance(p, dict) for p in patches):
        raise ValueError('patch operations must be objects')
    if any(p.get('op') == 'KEEP' for p in patches):
        if len(patches) != 1:
            raise ValueError('KEEP must stand alone')
        return program
    module = executor()
    prefix, bindings, scales = [], [], []
    for patch in patches:
        kind = patch.get('op')
        if kind == 'prepend_step':
            try:
                step = module.parse_program(patch['step'])
            except ValueError:
                # The existing parser requires comma-space delimiters.
                match = re.fullmatch(r'\s*(\w+)\(\s*([^(),]+),\s*([^(),]+)\s*\)\s*', patch['step'])
                if match is None:
                    raise
                step = module.parse_program(f'{match[1]}({match[2].strip()}, {match[3].strip()})')
            if len(step) != 1 or len(prefix) >= 6:
                raise ValueError('prepend_step adds one flat step; at most six')
            item = step[0]
            if any(re.fullmatch(r'#\d+', arg) and int(arg[1:]) >= len(prefix)
                   for arg in (item.arg1, item.arg2)):
                raise ValueError('prefix reference must point to an earlier prefix step')
            prefix.append(item)
        elif kind == 'rebind_operand':
            if not all(isinstance(patch.get(k), str) for k in ('from', 'to')):
                raise ValueError('binding requires string from/to operands')
            bindings.append(patch)
        elif kind == 'scale_output':
            factor = float(patch['factor'])
            if (not math.isfinite(factor) or factor <= 0
                    or not math.isclose(math.log10(factor), round(math.log10(factor)), abs_tol=1e-10)
                    or not 1 <= factor <= 1e9
                    or patch.get('mode', 'divide') not in ('multiply', 'divide')):
                raise ValueError('output scale must be an integer power of ten, 1..1e9')
            scales.append((patch.get('mode', 'divide'), str(int(factor))))
        else:
            raise ValueError('unsupported patch operator')
    try:
        original = list(module.parse_program(program))
    except Exception:
        if not prefix or bindings:
            raise ValueError('invalid original requires a prefix-only reconstruction')
        original = []
    touched = [0]*len(bindings)
    result = [module.ProgramStep(i, s.op, s.arg1, s.arg2) for i, s in enumerate(prefix)]
    for i, step in enumerate(original):
        arguments = []
        for slot, token in enumerate((step.arg1, step.arg2), 1):
            replacements = []
            for j, patch in enumerate(bindings):
                scope = patch.get('positions')
                if scope is not None and [i, slot] not in scope:
                    continue
                if same_operand(token, patch['from'], module):
                    replacements.append(patch['to']); touched[j] += 1
            if len(set(replacements)) > 1:
                raise ValueError('conflicting simultaneous bindings')
            chosen = replacements[0] if replacements else token
            if re.fullmatch(r'@\d+', chosen):
                position = int(chosen[1:])
                if position >= len(prefix):
                    raise ValueError('missing prepended step')
                chosen = '#'+str(position)
            elif re.fullmatch(r'#\d+', chosen):
                chosen = '#'+str(int(chosen[1:])+len(prefix))
            arguments.append(chosen)
        result.append(module.ProgramStep(len(result), step.op, *arguments))
    if any(count == 0 for count in touched):
        raise ValueError('a requested binding matched no operand')
    for op, factor in scales:
        if not result:
            raise ValueError('cannot scale a missing output')
        result.append(module.ProgramStep(len(result), op, '#'+str(len(result)-1), factor))
    if not result or len(result) > 24:
        raise ValueError('empty or excessive patched program')
    return module.render_program(result)
