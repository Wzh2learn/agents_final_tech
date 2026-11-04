#!/usr/bin/env python3
"""Run independent controls against the published EvoClaw config grader.

The public input fixtures and generated outputs stay on GB10. This is a
source-exposed, zero-model qualification of one synthetic benchmark task.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


EVIDENCE = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
REPOSITORY = EVIDENCE / 'evoclawbench_source_20261104'
BENCH = REPOSITORY / 'evoclawbench'
OUT = EVIDENCE / 'evoclaw_config_qualification_20261104_v2'
TASK = BENCH / 'tasks/task_05_config_migration.md'
REVISION = 'd9ec3e1a8873a1dbd142102abc00568765d21088'
IMAGE = 'sha256:80d3b4d54b7ae30338c21522ade57c6a5de5df1315b2e74744c8c0af2546d3d2'
FILES = ('webapp', 'worker', 'gateway', 'scheduler', 'mailer')
RENAMES = {'db': 'database', 'rate_limit': 'rate_limiting', 'notification': 'notifications'}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def migrate(source: dict, wrong_type: bool) -> dict:
    result = {}
    types = {str: 'string', int: 'integer', float: 'float', bool: 'boolean', list: 'list'}
    for key, value in source.items():
        section, field = key.split('.', 1)
        if type(value) not in types:
            raise ValueError(f'unsupported fixture value type: {type(value).__name__}')
        entry = {'value': value, 'type': 'incorrect_type' if wrong_type else types[type(value)]}
        result.setdefault(RENAMES.get(section, section), {})[field] = entry
    return result


def independent_errors(source: dict, candidate: object) -> list[str]:
    expected = migrate(source, False)
    errors = []

    def compare(want: object, got: object, path: str) -> None:
        if type(want) is not type(got):
            errors.append(f'{path}:type')
        elif isinstance(want, dict):
            for key in sorted(set(want) | set(got)):
                child = f'{path}.{key}' if path else str(key)
                if key not in want or key not in got:
                    errors.append(f'{child}:missing_or_extra')
                else:
                    compare(want[key], got[key], child)
        elif want != got:
            errors.append(f'{path}:value')

    compare(expected, candidate, '')
    return errors


def main() -> None:
    revision = subprocess.check_output(['git', '-C', str(REPOSITORY), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != REVISION:
        raise ValueError('unexpected upstream revision')
    if OUT.exists():
        raise FileExistsError('refusing to overwrite prior qualification')
    text = TASK.read_text(encoding='utf-8')
    match = re.search(r'## Automated Checks\s*```python\s*\n(.*?)\n```', text, re.DOTALL)
    if not match:
        raise ValueError('upstream automated checks not found')
    OUT.mkdir(parents=True)
    grader = OUT / 'upstream_grader.py'
    grader.write_text(match.group(1) + '\n', encoding='utf-8')
    runner = OUT / 'evaluate.py'
    runner.write_text(
        'import json, sys\n'
        'from upstream_grader import grade\n'
        'print(json.dumps(grade([], sys.argv[1]), sort_keys=True))\n', encoding='utf-8')
    result = {'upstream_revision': revision, 'task_sha256': digest(TASK),
              'grader_sha256': digest(grader), 'script_sha256': digest(Path(__file__)),
              'fixture_sha256': {}, 'cases': {}}
    for case in ('correct', 'wrong_type', 'empty'):
        workspace = OUT / case
        (workspace / 'outputs').mkdir(parents=True)
        inputs = workspace / 'assets/config_migration'
        inputs.mkdir(parents=True)
        errors, total_fields = [], 0
        for name in FILES:
            source = BENCH / f'assets/config_migration/{name}_v1.json'
            result['fixture_sha256'][name] = digest(source)
            shutil.copyfile(source, inputs / source.name)
            data = json.loads(source.read_text(encoding='utf-8'))
            total_fields += len(data)
            if case != 'empty':
                candidate = migrate(data, case == 'wrong_type')
                (workspace / f'outputs/{name}_v2.json').write_text(
                    json.dumps(candidate, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                errors.extend(f'{name}:{item}' for item in independent_errors(data, candidate))
        cmd = ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--read-only',
               '--cpus', '2', '--memory', '2g', '--pids-limit', '128', '--cap-drop', 'ALL',
               '--security-opt', 'no-new-privileges', '-e', 'PYTHONDONTWRITEBYTECODE=1',
               '--mount', f'type=bind,src={workspace},dst=/work,readonly',
               '--mount', f'type=bind,src={OUT},dst=/checks,readonly',
               IMAGE, 'python3', '/checks/evaluate.py', '/work']
        completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, timeout=120, check=True)
        scores = json.loads(completed.stdout)
        result['cases'][case] = {'upstream_checks': len(scores),
                                 'upstream_all_one': all(x == 1 for x in scores.values()),
                                 'upstream_scores': scores,
                                 'input_fields': total_fields,
                                 'independent_error_count': len(errors) if case != 'empty' else None,
                                 'independent_errors': errors if case != 'empty' else None}
    correct, wrong, empty = (result['cases'][name] for name in ('correct', 'wrong_type', 'empty'))
    if not correct['upstream_all_one'] or correct['independent_error_count']:
        raise ValueError('positive control did not pass both checks')
    if not wrong['upstream_all_one'] or wrong['independent_error_count'] != wrong['input_fields']:
        raise ValueError('wrong-type control did not reproduce expected disagreement')
    if empty['upstream_all_one']:
        raise ValueError('empty control was accepted')
    receipt = OUT / 'receipt.json'
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(receipt), 'sha256': digest(receipt),
                      'input_fields': correct['input_fields'], 'upstream_checks': correct['upstream_checks'],
                      'wrong_type_independent_errors': wrong['independent_error_count'],
                      'correct_all_one': correct['upstream_all_one'],
                      'wrong_type_all_one': wrong['upstream_all_one'],
                      'empty_all_one': empty['upstream_all_one']}))


if __name__ == '__main__':
    main()
