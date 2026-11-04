#!/usr/bin/env python3
"""Qualify two related historical SymPy issues in isolated ARM containers.

This is a researcher-side control. It reads the benchmark's gold and test
patches only into a private evaluation directory, never into the clean base
trees that an agent may later receive. It does not run a model.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import time
import zipfile

import pyarrow.parquet as pq

ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
DATA = ROOT / 'swe_contextbench_data_20261104'
OUT = ROOT / 'swe_contextbench_sympy_qualification_20261104_v3'
DATA_MANIFEST = 'bfa76e90221cc82e2c33d24588ff3060756c57679d687f68b29e9e662d68b10c'
IMAGE = 'sha256:648a1999badfe683239ec49e05b2a508e37f762213478122c58fa713f6c00f58'
DEPS = Path('/home/testuser/wzh/projects/agents_final_tech/venv/lib/python3.12/site-packages')
OVERLAY = ROOT / 'sympy_hypothesis_env_20261104'
OVERLAY_MANIFEST = '535659f88bae86059cac418c39634ff14d140eb555828fb7753584225c06d459'
CASES = {
    'source': {
        'id': 'sympy__sympy-19487',
        'data': 'SWEContextBench_Lite_Experience.parquet',
        'rev': '25fbcce5b1a4c7e3956e6062930f4a44ce95a632',
        'archive': 'swe_contextbench_sympy_source_25fbcce5.tar.gz',
        'archive_sha': 'c2d68e442c66575e132b943979cf9a80bfbefd06051c0ff7a4708763b96a69e3',
        'focus': ['sympy/functions/elementary/tests/test_complexes.py::test_sign'],
        'regression': ['sympy/core/tests/test_subs.py::test_subs'],
    },
    'target': {
        'id': 'sympy__sympy-19484',
        'data': 'SWEContextBench_Related_Lite.parquet',
        'rev': '4fa55af041c632f522e622de4b175f03927a7f95',
        'archive': 'swe_contextbench_sympy_target_4fa55af0.tar.gz',
        'archive_sha': '44f3134950014b7947d35ea25b0fdfcc03bbb72d56f84ca8156e13239ab029f2',
        'focus': ['sympy/simplify/tests/test_simplify.py::test_issue_19484'],
        'regression': ['sympy/series/tests/test_gruntz.py::test_I',
                       'sympy/series/tests/test_gruntz.py::test_compare1'],
    },
}


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def checked_dataset() -> None:
    manifest = DATA / 'manifest.json'
    if sha(manifest) != DATA_MANIFEST:
        raise ValueError('dataset manifest changed')
    data = json.loads(manifest.read_text(encoding='utf-8'))
    for item in data['files']:
        if sha(DATA / item['name']) != item['sha256']:
            raise ValueError('dataset file changed')


def dataset_row(spec: dict) -> dict:
    columns = ['instance_id', 'base_commit', 'problem_statement', 'patch', 'test_patch',
               'FAIL_TO_PASS', 'PASS_TO_PASS']
    rows = pq.read_table(DATA / spec['data'], columns=columns).to_pylist()
    matches = [row for row in rows if row['instance_id'] == spec['id']]
    if len(matches) != 1 or matches[0]['base_commit'] != spec['rev']:
        raise ValueError('dataset task or revision mismatch')
    return matches[0]


def checked_overlay() -> None:
    manifest = OVERLAY / 'manifest.json'
    if sha(manifest) != OVERLAY_MANIFEST or not (DEPS / 'pytest').is_dir():
        raise ValueError('test dependencies missing or overlay manifest changed')
    site = (OVERLAY / 'site').resolve()
    expected = set()
    for package in json.loads(manifest.read_text(encoding='utf-8'))['packages']:
        wheel = OVERLAY / package['filename']
        if sha(wheel) != package['sha256']:
            raise ValueError('overlay wheel changed')
        with zipfile.ZipFile(wheel) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                path = (site / member.filename).resolve()
                if (not path.is_relative_to(site) or not path.is_file() or
                        sha_bytes(archive.read(member)) != sha(path)):
                    raise ValueError('overlay file missing or changed')
                expected.add(path)
    if {path.resolve() for path in site.rglob('*') if path.is_file()} != expected:
        raise ValueError('unexpected overlay file')


def extract_safe(archive: Path, destination: Path, rev: str) -> int:
    """Extract only ordinary files under the archive's exact commit prefix."""
    destination.mkdir()
    prefix = 'sympy-' + rev
    count = 0
    with tarfile.open(archive, mode='r:gz') as stream:
        for member in stream:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or '..' in path.parts or not path.parts or
                    path.parts[0] != prefix or not (member.isfile() or member.isdir())):
                raise ValueError('unexpected archive member')
            if len(path.parts) == 1:
                continue
            output = destination.joinpath(*path.parts[1:])
            if member.isdir():
                output.mkdir(parents=True, exist_ok=True)
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                source = stream.extractfile(member)
                if source is None:
                    raise ValueError('archive file missing data')
                with source, output.open('xb') as target:
                    shutil.copyfileobj(source, target)
                count += 1
    if (destination / '.git').exists() or not (destination / 'LICENSE').is_file():
        raise ValueError('unexpected history or missing project license')
    return count


def apply_patch(work: Path, content: str) -> dict:
    data = content.encode('utf-8')
    checked = subprocess.run(['git', 'apply', '--check', '-'], cwd=work, input=data,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    if checked.returncode:
        return {'check_exit': checked.returncode, 'apply_exit': None,
                'diagnostic': checked.stdout.decode('utf-8', errors='replace')[-2000:]}
    applied = subprocess.run(['git', 'apply', '-'], cwd=work, input=data,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    return {'check_exit': checked.returncode, 'apply_exit': applied.returncode,
            'diagnostic': applied.stdout.decode('utf-8', errors='replace')[-2000:]}


def test(work: Path, nodes: list[str], log: Path, label: str) -> dict:
    name = f'contextbench-qual-{label}-{int(time.time())}'
    cmd = ['docker', 'run', '--name', name, '--rm', '--pull', 'never', '--network', 'none',
           '--read-only', '--cpus', '2', '--memory', '3g', '--pids-limit', '256',
           '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
           '--tmpfs', '/tmp:rw,nosuid,size=128m', '-e', 'PYTHONPATH=/workspace:/extra:/deps',
           '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
           '-e', 'HYPOTHESIS_STORAGE_DIRECTORY=/tmp/hypothesis',
           '--mount', f'type=bind,src={work},dst=/workspace,readonly', '--workdir', '/workspace',
           '--mount', f'type=bind,src={DEPS},dst=/deps,readonly',
           '--mount', f'type=bind,src={OVERLAY / "site"},dst=/extra,readonly',
           '--entrypoint', 'python3', IMAGE, '-c',
           'import _distutils_hack; _distutils_hack.add_shim(); import pytest, sys; '
           'raise SystemExit(pytest.main(sys.argv[1:]))', '-q', '-p', 'no:cacheprovider', *nodes]
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=240, check=False)
        code, output = proc.returncode, proc.stdout
    except subprocess.TimeoutExpired as exc:
        code, output = 124, exc.stdout or b''
        subprocess.run(['docker', 'kill', name], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10, check=False)
    log.write_bytes(output)
    lines = output.decode('utf-8', errors='replace').splitlines()
    summary = next((line.strip() for line in reversed(lines)
                    if any(term in line for term in (' passed', ' failed', ' error'))), '')
    return {'exit': code, 'summary': summary, 'seconds': round(time.monotonic() - start, 3),
            'nodes': nodes, 'log_sha256': sha(log)}


def main() -> None:
    if OUT.exists():
        raise FileExistsError('qualification directory already exists')
    checked_dataset()
    checked_overlay()
    subprocess.check_output(['docker', 'image', 'inspect', IMAGE])
    OUT.mkdir()
    result = {'scope': 'HISTORICAL_GITHUB_ISSUES_RESEARCHER_CONTROLS_ARM_ADAPTATION',
              'script_sha256': sha(Path(__file__)), 'dataset_manifest_sha256': DATA_MANIFEST,
              'image': IMAGE, 'overlay_manifest_sha256': OVERLAY_MANIFEST,
              'bootstrap': 'setuptools distutils shim required for historical SymPy on Python 3.12',
              'agent_or_model_calls': 0, 'cases': {}}
    for label, spec in CASES.items():
        archive = ROOT / spec['archive']
        if sha(archive) != spec['archive_sha']:
            raise ValueError('archive digest changed')
        row = dataset_row(spec)
        case = OUT / label
        case.mkdir()
        base = case / 'clean_base'
        nfiles = extract_safe(archive, base, spec['rev'])
        (case / 'task.txt').write_text(row['problem_statement'], encoding='utf-8')
        control = {'instance_id': spec['id'], 'base_commit': spec['rev'],
                   'archive_sha256': sha(archive), 'base_file_count': nfiles,
                   'license_sha256': sha(base / 'LICENSE'),
                   'problem_sha256': sha(case / 'task.txt'),
                   'reference_patch_sha256': sha_bytes(row['patch'].encode('utf-8')),
                   'test_patch_sha256': sha_bytes(row['test_patch'].encode('utf-8')),
                   'benchmark_fail_to_pass': json.loads(row['FAIL_TO_PASS']),
                   'benchmark_pass_to_pass_count': len(json.loads(row['PASS_TO_PASS'])),
                   'arms': {}}
        for arm in ('base_with_tests', 'gold_with_tests'):
            workspace = case / arm
            shutil.copytree(base, workspace)
            outcome = {'test_patch': apply_patch(workspace, row['test_patch'])}
            if outcome['test_patch']['apply_exit'] == 0 and arm == 'gold_with_tests':
                outcome['reference_patch'] = apply_patch(workspace, row['patch'])
            patch_ok = (outcome['test_patch']['apply_exit'] == 0 and
                        (arm != 'gold_with_tests' or outcome['reference_patch']['apply_exit'] == 0))
            if patch_ok:
                outcome['focus'] = test(workspace, spec['focus'], case / (arm + '_focus.log'), label + '-focus')
                outcome['regression'] = test(workspace, spec['regression'], case / (arm + '_regression.log'),
                                             label + '-regression')
            control['arms'][arm] = outcome
        result['cases'][label] = control
    receipt = OUT / 'receipt.json'
    receipt.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(receipt), 'sha256': sha(receipt), 'cases': {
        label: {arm: {'patches_applied': detail['test_patch']['apply_exit'] == 0 and
                      (arm != 'gold_with_tests' or detail.get('reference_patch', {}).get('apply_exit') == 0),
                      'focus': detail.get('focus'), 'regression': detail.get('regression')}
                for arm, detail in case['arms'].items()} for label, case in result['cases'].items()}}))


if __name__ == '__main__':
    main()
