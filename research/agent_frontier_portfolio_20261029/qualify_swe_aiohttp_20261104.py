#!/usr/bin/env python3
"""Qualify two SWE-Skills-Bench aiohttp tasks on GB10, without a model."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
BENCH = ROOT / 'swe_skills_bench_source_20261104'
AIO = ROOT / 'aiohttp_swe_skills_20261104'
WHEELS = ROOT / 'swe_aiohttp_env_20261104/wheels'
OUT = ROOT / 'swe_aiohttp_qualification_20261104_v4'
DEPS = Path('/home/testuser/wzh/projects/agents_final_tech/venv/lib/python3.12/site-packages')
BENCH_REV = '4d3450d9216a590a8726fcb3604b5143daca776b'
AIO_REV = 'c41e3b6ea2eccdeb6a32f9755525aecac48ba265'
WHEEL_SHA = {
    'pytest_aiohttp-1.1.0-py3-none-any.whl': 'f39a11693a0dce08dd6c542d241e199dd8047a6e6596b2bcfa60d373f143456d',
    'pytest_asyncio-1.4.0-py3-none-any.whl': '933ca923a23075a87fb7070c0ec272a6848489824d887c85c812670932835aa1',
    'pytest_timeout-2.4.0-py3-none-any.whl': 'c42667e5cdadb151aeb5b26d114aff6bdf5a907f176a007a30b940d3d865b5c2',
}
BASE_IMAGE = 'sha256:80d3b4d54b7ae30338c21522ade57c6a5de5df1315b2e74744c8c0af2546d3d2'
BASE_TAG = 'agent-stockviz-verifier:20261104'
IMAGE = 'swe-aiohttp-evaluator:20261104'

MAP_CONTROL = '''
async def map_concurrent(func, items, *, limit, return_exceptions=False):
    import asyncio
    if type(limit) is not int or limit <= 0:
        raise ValueError("limit must be a positive integer")
    items = list(items)
    semaphore = asyncio.Semaphore(limit)
    async def one(item):
        async with semaphore:
            return await func(item)
    tasks = [asyncio.create_task(one(item)) for item in items]
    try:
        return await asyncio.gather(*tasks, return_exceptions=return_exceptions)
    except BaseException:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
'''
MAP_TEST = '''
import asyncio
from aiohttp.helpers import map_concurrent

def test_map_concurrent_order():
    async def square(x):
        return x * x
    assert asyncio.run(map_concurrent(square, [1, 2, 3], limit=2)) == [1, 4, 9]
'''
POOL_CONTROL = '''
import asyncio

class TaskPool:
    def __init__(self, max_concurrency):
        if type(max_concurrency) is not int or max_concurrency <= 0:
            raise ValueError("max_concurrency must be a positive integer")
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._tasks = []
        self._closed = False

    async def __aenter__(self):
        return self

    def submit(self, coro):
        if self._closed:
            coro.close()
            raise RuntimeError("pool is closed")
        async def run():
            async with self._semaphore:
                return await coro
        task = asyncio.create_task(run())
        self._tasks.append(task)
        return task

    async def join(self):
        return await asyncio.gather(*self._tasks)

    async def __aexit__(self, exc_type, exc, tb):
        self._closed = True
        if exc_type is not None:
            for task in self._tasks:
                task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)
        else:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        return False
'''
POOL_TEST = '''
import asyncio
from aiohttp.task_pool import TaskPool

def test_task_pool_order():
    async def main():
        async with TaskPool(2) as pool:
            for n in (1, 2, 3):
                pool.submit(asyncio.sleep(0, result=n))
            return await pool.join()
    assert asyncio.run(main()) == [1, 2, 3]
'''


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commit(path: Path) -> str:
    return subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()


def run(cmd: list[str], log: Path, timeout: int = 300) -> dict:
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=timeout, check=False)
        code, data = proc.returncode, proc.stdout
    except subprocess.TimeoutExpired as exc:
        code, data = 124, exc.stdout or b''
        if '--name' in cmd:
            subprocess.run(['docker', 'kill', cmd[cmd.index('--name') + 1]], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=10, check=False)
    log.write_bytes(data)
    return {'exit': code, 'seconds': round(time.monotonic() - start, 3), 'log_sha256': sha(log)}


def main() -> None:
    if OUT.exists():
        raise FileExistsError('refusing to overwrite previous qualification')
    if (commit(BENCH) != BENCH_REV or commit(AIO) != AIO_REV
            or any(sha(WHEELS / name) != value for name, value in WHEEL_SHA.items())):
        raise ValueError('source or wheel identity changed')
    base_id = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', BASE_TAG],
                                      text=True).strip()
    if base_id != BASE_IMAGE:
        raise ValueError('local base image changed')
    if subprocess.check_output(['git', '-C', str(AIO), 'status', '--porcelain'], text=True).strip():
        raise ValueError('source checkout is not clean')
    OUT.mkdir(parents=True)
    build = OUT / 'build'
    build.mkdir()
    (build / 'wheels').mkdir()
    for name in WHEEL_SHA:
        shutil.copyfile(WHEELS / name, build / 'wheels' / name)
    (build / 'deps.pth').write_text('/deps\n', encoding='utf-8')
    (build / 'Dockerfile').write_text(
        f'FROM {BASE_TAG}\n'
        'COPY wheels /tmp/wheels\n'
        'COPY deps.pth /usr/local/lib/python3.12/site-packages/external_research_deps.pth\n'
        'RUN python3 -m pip install --no-index --no-deps /tmp/wheels/*.whl\n',
        encoding='utf-8')
    build_result = run(['docker', 'build', '--network', 'none', '--pull=false', '-t', IMAGE, str(build)],
                       OUT / 'build.log')
    result = {'benchmark_revision': BENCH_REV, 'repository_revision': AIO_REV, 'wheel_sha256': WHEEL_SHA,
              'base_image': BASE_IMAGE, 'script_sha256': sha(Path(__file__)), 'build': build_result, 'cases': {},
              'scope': 'Researcher-authored positive controls; benchmark tasks on a real fixed repository, '
                       'not natural historical issues or an official harness run.'}
    if build_result['exit'] != 0:
        (OUT / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        raise RuntimeError('isolated evaluator image build failed; see preserved receipt')
    result['image_id'] = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', IMAGE],
                                                  text=True).strip()
    for batch in (1, 2):
        hidden = BENCH / f'tests/batch{batch}/test_asyncio_patterns.py'
        task = BENCH / f'tasks/batch{batch}/asyncio-patterns.md'
        for condition in ('empty', 'positive'):
            case = OUT / f'batch{batch}_{condition}'
            workspace = case / 'aiohttp'
            case.mkdir()
            shutil.copytree(AIO, workspace, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache'))
            workspace.chmod(0o777)
            if condition == 'positive':
                if batch == 1:
                    with (workspace / 'aiohttp/helpers.py').open('a', encoding='utf-8') as f:
                        f.write('\n' + MAP_CONTROL)
                    (workspace / 'tests/test_map_concurrent.py').write_text(MAP_TEST, encoding='utf-8')
                else:
                    (workspace / 'aiohttp/task_pool.py').write_text(POOL_CONTROL, encoding='utf-8')
                    (workspace / 'tests/test_task_pool.py').write_text(POOL_TEST, encoding='utf-8')
            name = f'swe-aiohttp-qual-{batch}-{condition}'
            cmd = ['docker', 'run', '--name', name, '--rm', '--pull', 'never', '--network', 'none',
                   '--read-only', '--cpus', '2', '--memory', '3g', '--pids-limit', '256', '--cap-drop', 'ALL',
                   '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,nosuid,size=128m',
                   '-e', 'PYTHONPATH=/workspace/aiohttp', '-e', 'PYTHONDONTWRITEBYTECODE=1',
                   '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
                   '-e', 'PYTEST_ADDOPTS=-p pytest_asyncio.plugin -p pytest_timeout',
                   '--mount', f'type=bind,src={workspace},dst=/workspace/aiohttp',
                   '--mount', f'type=bind,src={hidden},dst=/checks/test_asyncio_patterns.py,readonly',
                   '--mount', f'type=bind,src={DEPS},dst=/deps,readonly',
                   '--workdir', '/workspace/aiohttp', '--entrypoint', 'python3', result['image_id'],
                   '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '/checks/test_asyncio_patterns.py']
            outcome = run(cmd, case / 'pytest.log')
            output = (case / 'pytest.log').read_text(encoding='utf-8', errors='replace')
            outcome['pytest_summary'] = next((line.strip() for line in reversed(output.splitlines())
                                               if re.search(r'\d+ (?:passed|failed|error)', line)), '')
            outcome['benchmark_test_sha256'] = sha(hidden)
            outcome['task_sha256'] = sha(task)
            result['cases'][f'batch{batch}_{condition}'] = outcome
    receipt = OUT / 'receipt.json'
    receipt.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(receipt), 'sha256': sha(receipt), 'image_id': result['image_id'],
                      'cases': {key: {'exit': value['exit'], 'summary': value['pytest_summary']}
                                for key, value in result['cases'].items()}}))


if __name__ == '__main__':
    main()
