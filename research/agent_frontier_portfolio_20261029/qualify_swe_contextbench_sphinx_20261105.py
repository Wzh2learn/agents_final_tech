#!/usr/bin/env python3
"""Privately qualify frozen Sphinx issue tests; never expose references to agents."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import time

import pyarrow.parquet as pq

ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
DATA = ROOT / 'swe_contextbench_data_20261104'
SOURCE = ROOT / 'swe_contextbench_sphinx_source_20261105'
OUT = ROOT / 'swe_contextbench_sphinx_qualification_20261105'
IMAGE = 'sha256:648a1999badfe683239ec49e05b2a508e37f762213478122c58fa713f6c00f58'
LEGACY = Path('/home/testuser/miniconda3/envs/haiguan')
SITE = SOURCE / 'venv38/lib/python3.8/site-packages'
DATA_MANIFEST = 'bfa76e90221cc82e2c33d24588ff3060756c57679d687f68b29e9e662d68b10c'
CASES = {
    'source': ('sphinx-doc__sphinx-8627', 'SWEContextBench_Lite_Experience.parquet',
               '332d80ba8433aea41c3709fa52737ede4405072b',
               'adb43119119b9f3cc0b03c04085b50c99f7d380a4a732b364ecb5800c5a4983c'),
    'target': ('sphinx-doc__sphinx-8588', 'SWEContextBench_Related_Lite.parquet',
               'b237e78f9c233170f271c326bf46b7fb3b103858',
               '98c2bbc623236d90e36e4f1828ae7d75283aa70d624c6bff763f5b52f02c7f05'),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(archive: Path, base: Path, rev: str) -> int:
    base.mkdir(parents=True)
    count = 0
    with tarfile.open(archive, 'r:gz') as tf:
        for item in tf:
            path = PurePosixPath(item.name)
            if (not path.parts or path.parts[0] != 'sphinx-' + rev or path.is_absolute()
                    or '..' in path.parts or not (item.isfile() or item.isdir())):
                raise ValueError(f'unsafe archive entry: {item.name}')
            if len(path.parts) == 1:
                continue
            dest = base.joinpath(*path.parts[1:])
            if item.isdir():
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with tf.extractfile(item) as stream, dest.open('wb') as output:
                    shutil.copyfileobj(stream, output)
                count += 1
    return count


def apply_patch(work: Path, patch: str, destination: Path) -> dict:
    destination.write_text(patch, encoding='utf8')
    commands = [['git', 'apply', '--check', str(destination)], ['git', 'apply', str(destination)]]
    results = []
    for command in commands:
        result = subprocess.run(command, cwd=work, capture_output=True, text=True, timeout=30)
        results.append({'exit': result.returncode, 'stderr': result.stderr[-2000:]})
        if result.returncode:
            break
    return {'sha256': sha(destination), 'steps': results}


def run_test(work: Path, nodes: list[str], logfile: Path, label: str) -> dict:
    if not nodes:
        return {'status': 'NO_TESTS'}
    name = f'sphinx-qualification-{label}-{int(time.time())}'
    cmd = ['docker', 'run', '--name', name, '--rm', '--pull', 'never', '--network', 'none',
           '--read-only', '--cpus', '2', '--memory', '3g', '--pids-limit', '256',
           '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
           '--tmpfs', '/tmp:rw,nosuid,size=128m', '-e', 'HOME=/tmp',
           '-e', 'PYTHONPATH=/workspace:/deps', '-e', 'PYTHONDONTWRITEBYTECODE=1',
           '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
           '--mount', f'type=bind,src={work},dst=/workspace,readonly',
           '--mount', f'type=bind,src={LEGACY},dst=/opt/legacy,readonly',
           '--mount', f'type=bind,src={SITE},dst=/deps,readonly',
           '--workdir', '/workspace', '--entrypoint', '/opt/legacy/bin/python',
           IMAGE, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *nodes]
    started = time.monotonic()
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=240)
        exit_code, output = result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code, output = 124, exc.stdout or b''
        subprocess.run(['docker', 'kill', name], capture_output=True, timeout=10)
    logfile.write_bytes(output)
    return {'exit': exit_code, 'seconds': round(time.monotonic() - started, 3),
            'log_sha256': sha(logfile), 'log_tail': output.decode('utf8', errors='replace').splitlines()[-8:]}


def main() -> None:
    if OUT.exists():
        raise FileExistsError('qualification directory already exists')
    manifest_path = DATA / 'manifest.json'
    if sha(manifest_path) != DATA_MANIFEST or not SITE.is_dir() or not (LEGACY / 'bin/python').is_file():
        raise ValueError('dataset manifest or isolated dependencies unavailable')
    manifest = json.loads(manifest_path.read_text(encoding='utf8'))
    for entry in manifest['files']:
        if sha(DATA / entry['name']) != entry['sha256']:
            raise ValueError('dataset file changed')
    OUT.mkdir()
    package_list = subprocess.run([str(SOURCE / 'venv38/bin/python'), '-m', 'pip', 'freeze'],
                                  capture_output=True, text=True, check=True, timeout=60).stdout
    (OUT / 'dependencies.txt').write_text(package_list, encoding='utf8')
    receipt = {'status': 'IN_PROGRESS', 'scientific_model_calls': 0, 'dataset_manifest': DATA_MANIFEST,
               'script_sha256': sha(Path(__file__)), 'dependency_versions_sha256': sha(OUT / 'dependencies.txt'),
               'interpreter_sha256': sha(LEGACY / 'bin/python3.8'), 'image': IMAGE, 'cases': {}}
    (OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf8')
    cols = ['instance_id', 'base_commit', 'patch', 'test_patch', 'FAIL_TO_PASS', 'PASS_TO_PASS']
    for label, (identity, dataset, rev, archive_sha) in CASES.items():
        archive = SOURCE / (label + '.tar.gz')
        if sha(archive) != archive_sha:
            raise ValueError('archive changed')
        rows = [r for r in pq.read_table(DATA / dataset, columns=cols).to_pylist() if r['instance_id'] == identity]
        if len(rows) != 1 or rows[0]['base_commit'] != rev:
            raise ValueError('dataset identity mismatch')
        row = rows[0]
        case = OUT / label
        clean = case / 'clean_base'
        count = extract(archive, clean, rev)
        case_result = {'identity': identity, 'base': rev, 'archive_sha256': archive_sha,
                       'files': count, 'arms': {}}
        for arm in ('base', 'gold'):
            work = case / arm
            shutil.copytree(clean, work)
            test_patch = apply_patch(work, row['test_patch'], case / f'{arm}_test.patch')
            detail = {'test_patch': test_patch}
            if all(s['exit'] == 0 for s in test_patch['steps']) and len(test_patch['steps']) == 2:
                if arm == 'gold':
                    detail['reference_patch'] = apply_patch(work, row['patch'], case / 'gold_reference.patch')
                if arm == 'base' or (len(detail['reference_patch']['steps']) == 2 and
                                     all(s['exit'] == 0 for s in detail['reference_patch']['steps'])):
                    detail['focus'] = run_test(work, json.loads(row['FAIL_TO_PASS']), case / f'{arm}_focus.log', label + arm + 'f')
                    detail['regression'] = run_test(work, json.loads(row['PASS_TO_PASS']), case / f'{arm}_regression.log', label + arm + 'r')
            case_result['arms'][arm] = detail
        receipt['cases'][label] = case_result
        (OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf8')
    receipt['status'] = 'COMPLETED_CONTROLS_NOT_ADJUDICATED'
    (OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'status': receipt['status'], 'receipt': str(OUT / 'receipt.json'),
                      'sha256': sha(OUT / 'receipt.json'), 'cases': receipt['cases']}))


if __name__ == '__main__':
    main()
