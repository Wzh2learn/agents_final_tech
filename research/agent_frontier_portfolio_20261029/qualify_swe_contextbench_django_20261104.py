#!/usr/bin/env python3
"""Qualify two related Django issues with private reference controls on ARM."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import time
import re

import qualify_swe_contextbench_sympy_20261104 as shared

ROOT = shared.ROOT
OUT = ROOT / 'swe_contextbench_django_qualification_20261104'
ENV = ROOT / 'swe_contextbench_django_env_20261104'
CASES = {
    'source': {
        'id': 'django__django-16910', 'data': 'SWEContextBench_Lite_Experience.parquet',
        'rev': '4142739af1cda53581af4169dbe16d6cd5e26948',
        'archive': 'swe_contextbench_django_source_4142739a.tar.gz',
        'archive_sha': 'ed411099b0adee652b6d109a5ad62210cc2686547c23cfab9102a818ed5c5569',
        'focus': ['select_related_onetoone.tests.ReverseSelectRelatedTestCase.test_inheritance_deferred2',
                  'defer_regress.tests.DeferRegressionTest.test_reverse_one_to_one_relations'],
        'regression': ['select_related_onetoone.tests.ReverseSelectRelatedValidationTests.test_reverse_related_validation',
                       'defer_regress.tests.DeferDeletionSignalsTests.test_delete_defered_model'],
    },
    'target': {
        'id': 'django__django-35356', 'data': 'SWEContextBench_Related_Lite.parquet',
        'rev': '53719d6b5b745dd99b1ab9315afb242f706ebbf1',
        'archive': 'swe_contextbench_django_target_53719d6b.tar.gz',
        'archive_sha': 'e7667e43b342187407400f9323cc424a77a198b2bab2f2d3cd1cbac926bd8f24',
        'focus': ['defer_regress.tests.DeferRegressionTest.test_self_referential_one_to_one'],
        'regression': ['defer_regress.tests.DeferDeletionSignalsTests.test_delete_defered_model',
                       'defer_regress.tests.DeferRegressionTest.test_basic'],
    },
}


def extract(archive: Path, destination: Path, rev: str) -> dict:
    destination.mkdir()
    prefix, count, skipped = 'django-' + rev, 0, []
    with tarfile.open(archive, 'r:gz') as stream:
        for member in stream:
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != prefix:
                raise ValueError('unsafe archive path')
            if member.issym():
                # Four documentation-theme links are irrelevant to the selected tests;
                # do not materialize links in an agent-accessible tree.
                if (not member.name.startswith(prefix + '/docs/_theme/djangodocs-epub/static/') or
                        not member.linkname.startswith('../../djangodocs/static/')):
                    raise ValueError('unexpected symbolic link')
                skipped.append(member.name)
                continue
            if not (member.isfile() or member.isdir()):
                raise ValueError('unexpected archive member type')
            if len(path.parts) == 1:
                continue
            output = destination.joinpath(*path.parts[1:])
            if member.isdir():
                output.mkdir(parents=True, exist_ok=True)
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                source = stream.extractfile(member)
                if source is None:
                    raise ValueError('archive file missing')
                with source, output.open('xb') as target:
                    shutil.copyfileobj(source, target)
                count += 1
    if len(skipped) != 4 or (destination / '.git').exists() or not (destination / 'LICENSE').is_file():
        raise ValueError('unexpected source archive or history')
    return {'files': count, 'omitted_documentation_symlinks': skipped}


def test(work: Path, labels: list[str], log: Path, name: str) -> dict:
    container = f'django-contextbench-{name}-{int(time.time())}'
    cmd = ['docker', 'run', '--name', container, '--rm', '--pull', 'never', '--network', 'none',
           '--read-only', '--cpus', '2', '--memory', '3g', '--pids-limit', '256',
           '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
           '--tmpfs', '/tmp:rw,nosuid,size=128m', '-e', 'PYTHONPATH=/workspace:/extra',
           '-e', 'PYTHONDONTWRITEBYTECODE=1', '--mount', f'type=bind,src={work},dst=/workspace,readonly',
           '--mount', f'type=bind,src={ENV / "site"},dst=/extra,readonly', '--workdir', '/workspace',
           '--entrypoint', 'python3', shared.IMAGE, 'tests/runtests.py', '--settings=test_sqlite',
           '--parallel=1', '--verbosity=1', *labels]
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=240, check=False)
        code, output = proc.returncode, proc.stdout
    except subprocess.TimeoutExpired as exc:
        code, output = 124, exc.stdout or b''
        subprocess.run(['docker', 'kill', container], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10, check=False)
    log.write_bytes(output)
    lines = output.decode('utf-8', errors='replace').splitlines()
    summary = [line.strip() for line in lines if line.startswith(('Ran ', 'FAILED ', 'OK'))]
    return {'exit': code, 'summary': summary[-2:], 'seconds': round(time.monotonic() - started, 3),
            'labels': labels, 'log_sha256': shared.sha(log)}


def main() -> None:
    if OUT.exists():
        raise FileExistsError('qualification already exists')
    shared.checked_dataset()
    site, wheels = ENV / 'site', ENV / 'wheelhouse'
    wheel_hashes = {p.name: shared.sha(p) for p in sorted(wheels.glob('*.whl'))}
    if len(wheel_hashes) != 2 or not (site / 'asgiref').is_dir() or not (site / 'sqlparse').is_dir():
        raise ValueError('private Django dependencies are missing')
    site_hashes = {p.relative_to(site).as_posix(): shared.sha(p) for p in sorted(site.rglob('*'))
                   if p.is_file() and not p.is_symlink()}
    OUT.mkdir()
    manifest = OUT / 'dependency_manifest.json'
    manifest.write_text(json.dumps({'wheels': wheel_hashes, 'site_files': site_hashes},
                                   sort_keys=True, indent=2) + '\n', encoding='utf-8')
    result = {'scope': 'TWO_HISTORICAL_DJANGO_ISSUES_PRIVATE_REFERENCE_CONTROLS_ARM',
              'script_sha256': shared.sha(Path(__file__)), 'dataset_manifest_sha256': shared.DATA_MANIFEST,
              'image': shared.IMAGE, 'dependency_manifest_sha256': shared.sha(manifest),
              'agent_or_model_calls': 0, 'cases': {}}
    for label, spec in CASES.items():
        archive = ROOT / spec['archive']
        if shared.sha(archive) != spec['archive_sha']:
            raise ValueError('archive hash changed')
        row = shared.dataset_row(spec)
        case = OUT / label
        case.mkdir()
        base = case / 'clean_base'
        extraction = extract(archive, base, spec['rev'])
        (case / 'task.txt').write_text(row['problem_statement'], encoding='utf-8')
        record = {'instance_id': spec['id'], 'base_commit': spec['rev'], 'archive_sha256': shared.sha(archive),
                  'extraction': extraction, 'license_sha256': shared.sha(base / 'LICENSE'),
                  'problem_sha256': shared.sha(case / 'task.txt'),
                  'test_patch_sha256': shared.sha_bytes(row['test_patch'].encode('utf-8')),
                  'reference_patch_sha256': shared.sha_bytes(row['patch'].encode('utf-8')),
                  'benchmark_fail_to_pass': json.loads(row['FAIL_TO_PASS']),
                  'benchmark_pass_to_pass_count': len(json.loads(row['PASS_TO_PASS'])), 'arms': {}}
        for arm in ('base_with_tests', 'gold_with_tests'):
            work = case / arm
            shutil.copytree(base, work)
            data = {'test_patch': shared.apply_patch(work, row['test_patch'])}
            if data['test_patch']['apply_exit'] == 0 and arm == 'gold_with_tests':
                data['reference_patch'] = shared.apply_patch(work, row['patch'])
            if data['test_patch']['apply_exit'] == 0 and (
                    arm != 'gold_with_tests' or data['reference_patch']['apply_exit'] == 0):
                data['focus'] = test(work, spec['focus'], case / (arm + '_focus.log'), label + '-focus')
                data['regression'] = test(work, spec['regression'], case / (arm + '_regression.log'),
                                          label + '-regression')
            record['arms'][arm] = data
            print(json.dumps({'case': label, 'arm': arm, 'focus': data.get('focus'),
                              'regression': data.get('regression')}), flush=True)
        result['cases'][label] = record
        (OUT / 'progress.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    after = {p.relative_to(site).as_posix(): shared.sha(p) for p in sorted(site.rglob('*'))
             if p.is_file() and not p.is_symlink()}
    result['dependencies_unchanged'] = after == site_hashes
    receipt = OUT / 'receipt.json'
    receipt.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(receipt), 'sha256': shared.sha(receipt)}), flush=True)


def regression_labels(spec: dict) -> tuple[list[str], list[str]]:
    labels, unresolved = [], []
    for item in json.loads(shared.dataset_row(spec)['PASS_TO_PASS']):
        old = re.fullmatch(r'[^()]+\s+\(([^()]+)\)', item)
        if old:
            labels.append(old.group(1))
            continue
        parts = item.split('::')
        if len(parts) < 2 or not parts[0].startswith('tests/') or not parts[0].endswith('.py'):
            unresolved.append(item)
            continue
        labels.append(parts[0][len('tests/'):-len('.py')].replace('/', '.') + '.' + '.'.join(parts[1:]))
    if len(set(labels)) != len(labels):
        raise ValueError('duplicate Django regression labels')
    return labels, unresolved


def full_regression() -> None:
    """Recheck parseable PASS_TO_PASS labels and retain unmapped entries."""
    original = OUT / 'receipt.json'
    if shared.sha(original) != '3c0e97a962c1607fb6aca351438a79c48b1b1528ae7e3f971bec099095094ff4':
        raise ValueError('Django controls changed')
    out = OUT / 'full_regression_v2'
    out.mkdir(exist_ok=False)
    results = {'scope': 'PARSEABLE_PUBLISHED_PASS_TO_PASS_LABELS_ON_PRIVATE_CONTROL_COPIES',
               'controls_sha256': shared.sha(original), 'agent_or_model_calls': 0, 'cases': {}}
    for label, spec in CASES.items():
        labels, unresolved = regression_labels(spec)
        results['cases'][label] = {'count': len(labels), 'unresolved_labels': unresolved, 'arms': {}}
        for arm in ('base_with_tests', 'gold_with_tests'):
            record = test(OUT / label / arm, labels, out / f'{label}_{arm}.log', label + '-full-regression')
            results['cases'][label]['arms'][arm] = record
            (out / 'progress.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
            print(json.dumps({'case': label, 'arm': arm, 'result': record}), flush=True)
    receipt = out / 'receipt.json'
    receipt.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(receipt), 'sha256': shared.sha(receipt)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--full-regression', action='store_true')
    args = parser.parse_args()
    full_regression() if args.full_regression else main()
