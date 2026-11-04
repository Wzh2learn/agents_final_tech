#!/usr/bin/env python3
"""Qualify the exposed SkillLearnBench stock-visualization format shift.

The official task is adapted to an offline, ARM64 development environment:
only its npm install command is replaced by a check for a separately verified
D3 package. The published solution and tests are never mounted into an agent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
UPSTREAM = ROOT / 'SkillLearnBench'
TASKS = UPSTREAM / 'tasks/stock-data-visualization'
QUAL = ROOT / 'stock_format_qualification_20261104'
DEPS = Path('/home/testuser/wzh/projects/agents_final_tech/venv/lib/python3.12/site-packages')
BROWSERS = Path('/home/testuser/.cache/ms-playwright')
IMAGE = 'agent-stockviz-verifier:20261104'
COMMIT = '726e1f79b96b0cb3d729d0e55a1c847e0b5353ae'
D3_SHA = 'fbb8da602a76f4ed49bac3561da62d8149fa121b8fd15685bacc21355d3a3322'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_digest(path: Path) -> dict:
    acc = hashlib.sha256()
    files = 0
    for item in sorted(path.rglob('*')):
        if item.is_symlink():
            raise ValueError(f'symlink in input tree: {item}')
        if item.is_file():
            acc.update(item.relative_to(path).as_posix().encode() + b'\0')
            acc.update(bytes.fromhex(digest(item)))
            files += 1
    if not files:
        raise ValueError('empty input tree')
    return {'files': files, 'sha256': acc.hexdigest()}


def offline_solution(source: str) -> str:
    old = 'npm install d3@6.7.0 --silent'
    if source.count(old) != 1:
        raise ValueError('upstream solution has changed')
    return source.replace(old, 'test -f /tmp/node_modules/d3/dist/d3.min.js', 1)


def command(args: list[str], timeout: int, log: Path) -> dict:
    start = time.monotonic()
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=timeout, stdin=subprocess.DEVNULL)
        output, rc = result.stdout, result.returncode
    except subprocess.TimeoutExpired as exc:
        output, rc = exc.stdout or b'', 124
    log.write_bytes(output)
    return {'exit_code': rc, 'seconds': round(time.monotonic() - start, 3),
            'log_sha256': digest(log)}


def qualify(output: Path) -> dict:
    if subprocess.check_output(['git', '-C', str(UPSTREAM), 'rev-parse', 'HEAD'], text=True).strip() != COMMIT:
        raise ValueError('unexpected upstream revision')
    d3 = QUAL / 'd3.v6.7.0.min.js'
    if digest(d3) != D3_SHA:
        raise ValueError('D3 integrity mismatch')
    image_id = subprocess.check_output(['docker', 'image', 'inspect', IMAGE, '--format', '{{.Id}}'], text=True).strip()
    output.mkdir(parents=True, exist_ok=False)
    result = {'status': 'EXPOSED_DEVELOPMENT_NOT_OFFICIAL', 'revision': COMMIT,
              'image_id': image_id, 'd3_sha256': D3_SHA, 'cases': {},
              'adaptation': 'only npm install replaced by check of pinned offline D3',
              'agent_model_requests': 0}
    common = ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--cpus', '2',
              '--memory', '2g', '--pids-limit', '256', '--cap-drop', 'ALL',
              '--security-opt', 'no-new-privileges', '--shm-size', '512m']
    for version in (1, 2, 3):
        task = TASKS / f'stock-data-visualization-{version}'
        case = output / f'task_{version}'
        case.mkdir()
        work = case / 'output'
        work.mkdir()
        # The container drops DAC override; only its isolated scratch output
        # and verifier-log mounts need to be writable by the container user.
        work.chmod(0o777)
        logs = case / 'logs'
        logs.mkdir()
        logs.chmod(0o777)
        source = task / 'solution/solve.sh'
        adapted = case / 'offline_solve.sh'
        adapted.write_text(offline_solution(source.read_text(encoding='utf-8')), encoding='utf-8')
        build = common + ['--mount', f'type=bind,src={task / "environment/data"},dst=/root/data,readonly',
                          '--mount', f'type=bind,src={work},dst=/root/output',
                          '--mount', f'type=bind,src={adapted},dst=/source/solve.sh,readonly',
                          '--mount', f'type=bind,src={d3},dst=/tmp/node_modules/d3/dist/d3.min.js,readonly',
                          'python:3.12-slim', 'bash', '/source/solve.sh']
        build_result = command(build, 180, case / 'solution.log')
        verify = common + ['-e', 'PYTHONPATH=/deps', '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
                           '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'PLAYWRIGHT_BROWSERS_PATH=/ms-playwright',
                           '--mount', f'type=bind,src={work},dst=/root/output,readonly',
                           '--mount', f'type=bind,src={task / "tests"},dst=/tests,readonly',
                           '--mount', f'type=bind,src={logs},dst=/logs/verifier',
                           '--mount', f'type=bind,src={DEPS},dst=/deps,readonly',
                           '--mount', f'type=bind,src={BROWSERS},dst=/ms-playwright,readonly',
                           IMAGE, 'python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '/tests/test_outputs.py']
        verify_result = command(verify, 240, case / 'reference_verifier.log')
        result['cases'][str(version)] = {'instruction_sha256': digest(task / 'instruction.md'),
            'input_tree': tree_digest(task / 'environment/data'), 'source_sha256': digest(source),
            'offline_source_sha256': digest(adapted), 'verifier_sha256': digest(task / 'tests/test_outputs.py'),
            'solution': build_result, 'reference_verifier': verify_result}
        print(json.dumps({'task': version, 'solution_exit': build_result['exit_code'],
                          'verifier_exit': verify_result['exit_code']}), flush=True)
    # An empty deliverable tests the evaluator's ability to reject a known-bad output.
    negative = output / 'empty_output'
    negative.mkdir()
    negative_logs = output / 'empty_logs'
    negative_logs.mkdir()
    negative_logs.chmod(0o777)
    target = TASKS / 'stock-data-visualization-2'
    verify = common + ['-e', 'PYTHONPATH=/deps', '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
                       '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'PLAYWRIGHT_BROWSERS_PATH=/ms-playwright',
                       '--mount', f'type=bind,src={negative},dst=/root/output,readonly',
                       '--mount', f'type=bind,src={target / "tests"},dst=/tests,readonly',
                       '--mount', f'type=bind,src={negative_logs},dst=/logs/verifier',
                       '--mount', f'type=bind,src={DEPS},dst=/deps,readonly',
                       '--mount', f'type=bind,src={BROWSERS},dst=/ms-playwright,readonly',
                       IMAGE, 'python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '/tests/test_outputs.py']
    result['empty_negative'] = command(verify, 240, output / 'empty_verifier.log')
    result['qualification_pass'] = (all(c['solution']['exit_code'] == 0 and c['reference_verifier']['exit_code'] == 0
                                        for c in result['cases'].values())
                                    and result['empty_negative']['exit_code'] == 1)
    receipt = output / 'receipt.json'
    receipt.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'qualification_pass': result['qualification_pass'], 'receipt_sha256': digest(receipt)}))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = qualify(args.output)
    if not result['qualification_pass']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
