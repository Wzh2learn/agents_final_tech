#!/usr/bin/env python3
"""Qualify two SWE-Skills-Bench SymPy tasks on GB10 without a model."""
from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess

from qualify_swe_aiohttp_20261104 import BENCH, BENCH_REV, DEPS, ROOT, commit, run, sha

SYMPY = ROOT / 'sympy_swe_skills_20261104'
SYMPY_REV = 'ba8647df9546cfb1ab15d7d2fcb573ae60203be7'
OUT = ROOT / 'swe_sympy_qualification_20261104'
IMAGE = 'sha256:648a1999badfe683239ec49e05b2a508e37f762213478122c58fa713f6c00f58'

TAYLOR = '''
from sympy.core.singleton import S
from sympy.functions.combinatorial.factorials import factorial

def taylor_coefficient(expr, x, x0, k):
    if not isinstance(k, int) or k < 0:
        raise ValueError("k must be a non-negative integer")
    return S(expr).diff(x, k).subs(x, x0) / factorial(k)

def taylor_polynomial(expr, x, x0, n):
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non-negative integer")
    return sum(taylor_coefficient(expr, x, x0, k) * (x - x0)**k for k in range(n + 1))
'''
TAYLOR_TEST = '''
from sympy import symbols, exp, Rational, expand
from sympy.calculus import taylor_polynomial, taylor_coefficient

def test_taylor_polynomial_exact():
    x = symbols('x')
    assert expand(taylor_polynomial(exp(x), x, 0, 2) - (1+x+x**2/2)) == 0
    assert taylor_coefficient(exp(x), x, 0, 2) == Rational(1, 2)
'''
CHARUTIL = '''
from sympy.core.symbol import Symbol
from sympy.core.function import expand
from sympy.matrices.dense import eye
from sympy.matrices.exceptions import NonSquareMatrixError

def characteristic_data(M, lam=None):
    if M.rows != M.cols:
        raise NonSquareMatrixError()
    if lam is None:
        lam = Symbol('lambda')
    return {'char_poly': expand((M-lam*eye(M.rows)).det()), 'trace': M.trace(),
            'determinant': M.det(), 'eigenvalues': M.eigenvals()}
'''
CHAR_TEST = '''
from sympy import Matrix
from sympy.matrices import characteristic_data

def test_characteristic_data_diagonal():
    result = characteristic_data(Matrix([[2, 0], [0, 3]]))
    assert result['trace'] == 5
    assert result['determinant'] == 6
    assert result['eigenvalues'] == {2: 1, 3: 1}
'''


def main() -> None:
    if OUT.exists():
        raise FileExistsError('refusing to overwrite previous qualification')
    if commit(BENCH) != BENCH_REV or commit(SYMPY) != SYMPY_REV:
        raise ValueError('upstream revision changed')
    if subprocess.check_output(['git', '-C', str(SYMPY), 'status', '--porcelain'], text=True).strip():
        raise ValueError('SymPy source checkout is not clean')
    subprocess.check_output(['docker', 'image', 'inspect', IMAGE])
    OUT.mkdir(parents=True)
    result = {'benchmark_revision': BENCH_REV, 'repository_revision': SYMPY_REV, 'image_id': IMAGE,
              'script_sha256': sha(Path(__file__)), 'cases': {},
              'scope': 'Researcher-authored controls; synthetic benchmark requirements on a fixed public repo.'}
    for batch in (1, 2):
        hidden = BENCH / f'tests/batch{batch}/test_sympy_symbolic_math.py'
        task = BENCH / f'tasks/batch{batch}/sympy-symbolic-math.md'
        for condition in ('empty', 'positive'):
            case = OUT / f'batch{batch}_{condition}'
            workspace = case / 'sympy'
            case.mkdir()
            shutil.copytree(SYMPY, workspace, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache'))
            workspace.chmod(0o777)
            if condition == 'positive' and batch == 1:
                (workspace / 'sympy/calculus/taylor.py').write_text(TAYLOR, encoding='utf-8')
                with (workspace / 'sympy/calculus/__init__.py').open('a', encoding='utf-8') as f:
                    f.write('\nfrom .taylor import taylor_polynomial, taylor_coefficient\n')
                (workspace / 'sympy/calculus/tests/test_taylor.py').write_text(TAYLOR_TEST, encoding='utf-8')
            elif condition == 'positive':
                (workspace / 'sympy/matrices/charutil.py').write_text(CHARUTIL, encoding='utf-8')
                with (workspace / 'sympy/matrices/__init__.py').open('a', encoding='utf-8') as f:
                    f.write('\nfrom .charutil import characteristic_data\n')
                (workspace / 'sympy/matrices/tests/test_charutil.py').write_text(CHAR_TEST, encoding='utf-8')
            name = f'swe-sympy-qual-{batch}-{condition}'
            cmd = ['docker', 'run', '--name', name, '--rm', '--pull', 'never', '--network', 'none',
                   '--read-only', '--cpus', '2', '--memory', '3g', '--pids-limit', '256', '--cap-drop', 'ALL',
                   '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,nosuid,size=128m',
                   '-e', 'PYTHONPATH=/workspace/sympy', '-e', 'PYTHONDONTWRITEBYTECODE=1',
                   '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
                   '--mount', f'type=bind,src={workspace},dst=/workspace/sympy',
                   '--mount', f'type=bind,src={hidden},dst=/checks/test_sympy_symbolic_math.py,readonly',
                   '--mount', f'type=bind,src={DEPS},dst=/deps,readonly', '--workdir', '/workspace/sympy',
                   '--entrypoint', 'python3', IMAGE, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
                   '/checks/test_sympy_symbolic_math.py']
            outcome = run(cmd, case / 'pytest.log', timeout=300)
            text = (case / 'pytest.log').read_text(encoding='utf-8', errors='replace')
            outcome['pytest_summary'] = next((line.strip() for line in reversed(text.splitlines())
                                               if re.search(r'\d+ (?:passed|failed|error)', line)), '')
            outcome['benchmark_test_sha256'] = sha(hidden)
            outcome['task_sha256'] = sha(task)
            result['cases'][f'batch{batch}_{condition}'] = outcome
    receipt = OUT / 'receipt.json'
    receipt.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(receipt), 'sha256': sha(receipt), 'cases': {
        name: {'exit': value['exit'], 'summary': value['pytest_summary']} for name, value in result['cases'].items()}}))


if __name__ == '__main__':
    main()
