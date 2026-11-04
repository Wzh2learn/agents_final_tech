#!/usr/bin/env python3
"""Qualify two exposed SkillFlow tasks in an isolated, adapted ARM environment.

Runs the published reference and its inner test suite, then two output controls.
The official Docker image and test.sh wrapper are not run; no agent or model runs.
"""
from __future__ import annotations

import hashlib
import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
QUAL = ROOT / 'skillflow_reconciliation_qualification_20261104'
FAMILY = QUAL / 'test_tasks/Cross-Format-Data-Reconciliation'
SOURCE_ZIP = ROOT / 'skillflow_two_tasks_20261104.zip'
REVISION = 'ecaadb0e25d5d5cfd87bd86d81e77b4abe3a00bc'
ZIP_SHA = '1b6c6a271314a04f850726a58fc249770fbc68fe3083c19ff4fb98ed924f3cfc'
TASKS = ('01-cloud-service-portfolio-diff', '02-hospital-capacity-portfolio-diff')
SITE = Path('/home/testuser/wzh/projects/agents_final_tech/venv/lib/python3.12/site-packages')
OVERLAY = QUAL / 'deps_pdfplumber'
IMAGE = 'agent-stockviz-verifier:20261104'
IMAGE_ID = 'sha256:80d3b4d54b7ae30338c21522ade57c6a5de5df1315b2e74744c8c0af2546d3d2'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def container(work: Path, extra: list[str], command: list[str], readonly_work: bool) -> list[str]:
    opts = ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none',
            '--cpus', '2', '--memory', '3g', '--pids-limit', '256', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '-e', 'PYTHONPATH=/overlay:/deps',
            '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
            '--mount', f'type=bind,src={SITE},dst=/deps,readonly',
            '--mount', f'type=bind,src={OVERLAY},dst=/overlay,readonly',
            '--mount', f'type=bind,src={work},dst=/root' + (',readonly' if readonly_work else '')]
    return opts + extra + [IMAGE] + command


def run(cmd: list[str], log: Path, timeout: int = 180) -> dict:
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=timeout, check=False)
        rc, content = proc.returncode, proc.stdout
    except subprocess.TimeoutExpired as exc:
        rc, content = 124, exc.stdout or b''
    log.write_bytes(content)
    return {'exit': rc, 'seconds': round(time.monotonic() - start, 3), 'log_sha256': sha(log)}


def independent_worker() -> None:
    """Read the original PDF/XLSX using libraries other than the reference solver."""
    from openpyxl import load_workbook
    from pypdf import PdfReader

    config = json.loads(Path('/contract/task_config.json').read_text(encoding='utf-8'))
    pdf = Path('/inputs') / Path(config['pdf_file']).name
    xlsx = Path('/inputs') / Path(config['excel_file']).name
    pages = PdfReader(pdf).pages
    text = '\n'.join(page.extract_text(extraction_mode='layout') for page in pages)
    rows = [re.split(r'\s{2,}', line.strip()) for line in text.splitlines() if line.strip()]
    book = load_workbook(xlsx, read_only=True, data_only=True)
    spreadsheet = list(book.active.values)
    book.close()
    headers = rows[0]
    if list(spreadsheet[0]) != headers or any(len(row) != len(headers) for row in rows):
        raise ValueError('PDF and workbook structures differ')
    old = {row[0]: dict(zip(headers, row)) for row in rows[1:]}
    new = {str(row[0]): dict(zip(headers, row)) for row in spreadsheet[1:]}
    if len(old) != len(rows) - 1 or len(new) != len(spreadsheet) - 1:
        raise ValueError('duplicate input ID')
    numeric = set(config['int_columns'] + config['float_columns'])

    def canonical(value, field):
        if value is None:
            return ('empty', '')
        if field in numeric:
            if isinstance(value, bool):
                return ('boolean', str(value))
            return ('numeric', str(Decimal(str(value)).normalize()))
        return ('text', str(value).strip())

    def event(item):
        return (str(item['id']), str(item['field']), canonical(item['old_value'], item['field']),
                canonical(item['new_value'], item['field']))

    deleted = sorted(set(old) - set(new))
    changes = sorted((item, field, canonical(old[item][field], field), canonical(new[item][field], field))
                     for item in sorted(set(old) & set(new)) for field in headers if field != 'ID'
                     and canonical(old[item][field], field) != canonical(new[item][field], field))
    candidate = json.loads(Path(config['output_file']).read_text(encoding='utf-8'))
    actual_deleted = candidate.get(config['deleted_key'], [])
    actual_changes = candidate.get(config['modified_key'], [])
    sample_text = Path('/instruction.md').read_text(encoding='utf-8')
    match = re.search(r'```json\s*(.*?)\s*```', sample_text, flags=re.S)
    sample = json.loads(match.group(1)) if match else {}
    sample_deleted = sample.get(config['deleted_key'], [])
    sample_changes = sample.get(config['modified_key'], [])
    result = {'pdf_rows': len(old), 'xlsx_rows': len(new), 'gold_deleted_count': len(deleted),
              'gold_changed_fields_count': len(changes), 'candidate_deleted_count': len(actual_deleted),
              'candidate_deleted_unique': len(actual_deleted) == len(set(actual_deleted)),
              'deleted_exact_including_multiplicity': sorted(actual_deleted) == deleted,
              'changed_fields_exact_including_multiplicity': sorted(event(x) for x in actual_changes) == changes,
              'example_deleted_matches': sum(x in deleted for x in sample_deleted),
              'example_deleted_total': len(sample_deleted),
              'example_change_matches': sum(event(x) in changes for x in sample_changes),
              'example_change_total': len(sample_changes)}
    print(json.dumps(result, ensure_ascii=False))


def independent_check() -> None:
    receipt = QUAL / 'runs_01/receipt.json'
    upstream = json.loads(receipt.read_text(encoding='utf-8'))
    if upstream['source_archive_sha256'] != ZIP_SHA:
        raise ValueError('unexpected qualification source')
    out = QUAL / 'runs_01/independent_recheck.json'
    if out.exists():
        raise ValueError('independent receipt already exists')
    result = {'status': 'POST_HOC_INDEPENDENT_PARSER_SAME_INPUT', 'qualification_sha256': sha(receipt),
              'checker_sha256': sha(Path(__file__)), 'model_calls': 0, 'cases': {}}
    for name in TASKS:
        task = FAMILY / name
        case = QUAL / 'runs_01' / name
        result['cases'][name] = {}
        for mode in ('reference', 'empty', 'duplicate_deleted_id'):
            folder = case / mode
            extra = ['--mount', f'type=bind,src={task / "environment/data"},dst=/inputs,readonly',
                     '--mount', f'type=bind,src={task / "solution/task_config.json"},dst=/contract/task_config.json,readonly',
                     '--mount', f'type=bind,src={task / "instruction.md"},dst=/instruction.md,readonly',
                     '--mount', f'type=bind,src={Path(__file__).resolve()},dst=/checker.py,readonly']
            cmd = container(folder, extra, ['python', '/checker.py', '--worker'], True)
            log = case / f'{mode}_independent.log'
            observed = run(cmd, log)
            if observed['exit'] == 0:
                observed['result'] = json.loads(log.read_text(encoding='utf-8'))
            result['cases'][name][mode] = observed
            print(json.dumps({'task': name, 'mode': mode, 'exit': observed['exit'],
                              'result': observed.get('result')}), flush=True)
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': str(out), 'sha256': sha(out)}), flush=True)


def prepare_counterfactual() -> None:
    """Alter one input cell while retaining the intentionally stale instruction."""
    from openpyxl import load_workbook

    task = FAMILY / TASKS[1]
    config = json.loads((task / 'solution/task_config.json').read_text(encoding='utf-8'))
    original = task / 'environment/data'
    out = QUAL / 'counterfactual_02'
    out.mkdir(exist_ok=False)
    inputs = out / 'input'
    shutil.copytree(original, inputs)
    book_name = Path(config['excel_file']).name
    before = load_workbook(original / book_name, data_only=False)
    after = load_workbook(inputs / book_name, data_only=False)
    sheet = after.active
    headers = [cell.value for cell in sheet[1]]
    if headers.count('ID') != 1 or headers.count('Capacity2024') != 1:
        raise ValueError('counterfactual fields not unique')
    id_col, target_col = headers.index('ID') + 1, headers.index('Capacity2024') + 1
    matching = [row for row in range(2, sheet.max_row + 1) if sheet.cell(row, id_col).value == 'HCP0001']
    if len(matching) != 1:
        raise ValueError('counterfactual target ID not unique')
    cell = sheet.cell(matching[0], target_col)
    old = cell.value
    if not isinstance(old, (int, float)) or isinstance(old, bool):
        raise ValueError('counterfactual cell is not numeric')
    cell.value = old + 10
    after.save(inputs / book_name)
    after.close()
    check = load_workbook(inputs / book_name, data_only=False)
    if before.sheetnames != check.sheetnames:
        raise ValueError('workbook sheet names changed')
    diffs = []
    for sheet_name in before.sheetnames:
        lhs, rhs = before[sheet_name], check[sheet_name]
        if (lhs.max_row, lhs.max_column) != (rhs.max_row, rhs.max_column):
            raise ValueError('workbook dimensions changed')
        for row in range(1, lhs.max_row + 1):
            for col in range(1, lhs.max_column + 1):
                left, right = lhs.cell(row, col).value, rhs.cell(row, col).value
                if left != right:
                    diffs.append({'sheet': sheet_name, 'cell': lhs.cell(row, col).coordinate,
                                  'old': left, 'new': right})
    before.close()
    check.close()
    if len(diffs) != 1 or diffs[0]['old'] != old or diffs[0]['new'] != old + 10:
        raise ValueError('counterfactual changed more than the intended cell')
    untouched = {}
    for path in sorted(original.iterdir()):
        if path.name != book_name:
            if sha(path) != sha(inputs / path.name):
                raise ValueError('non-workbook input changed')
            untouched[path.name] = sha(path)
    manifest = {'status': 'SYNTHETIC_POST_HOC_STALE_EXAMPLE', 'task': TASKS[1],
                'source_archive_sha256': sha(SOURCE_ZIP), 'instruction_sha256': sha(task / 'instruction.md'),
                'original_workbook_sha256': sha(original / book_name), 'modified_workbook_sha256': sha(inputs / book_name),
                'untouched_inputs': untouched, 'cell_diffs': diffs, 'model_calls': 0}
    manifest_path = out / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    reference = QUAL / 'runs_01' / TASKS[1] / 'reference'
    extra = ['--mount', f'type=bind,src={inputs},dst=/inputs,readonly',
             '--mount', f'type=bind,src={task / "solution/task_config.json"},dst=/contract/task_config.json,readonly',
             '--mount', f'type=bind,src={task / "instruction.md"},dst=/instruction.md,readonly',
             '--mount', f'type=bind,src={Path(__file__).resolve()},dst=/checker.py,readonly']
    log = out / 'stale_reference_check.log'
    observed = run(container(reference, extra, ['python', '/checker.py', '--worker'], True), log)
    if observed['exit'] != 0:
        raise ValueError(f'counterfactual independent checker failed: {observed["exit"]}')
    observed['result'] = json.loads(log.read_text(encoding='utf-8'))
    if observed['result']['changed_fields_exact_including_multiplicity']:
        raise ValueError('stale reference unexpectedly matches the modified input')
    receipt = out / 'stale_reference_check.json'
    receipt.write_text(json.dumps({'manifest_sha256': sha(manifest_path), 'check': observed}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PREPARED', 'manifest_sha256': sha(manifest_path),
                      'stale_reference_receipt_sha256': sha(receipt), 'result': observed['result']}))


def main() -> None:
    manifest = json.loads((QUAL / 'MANIFEST.json').read_text(encoding='utf-8'))
    if manifest['revision'] != REVISION or sha(SOURCE_ZIP) != ZIP_SHA:
        raise ValueError('source revision or archive changed')
    for row in manifest['files']:
        path = (QUAL / row['path']).resolve()
        if QUAL.resolve() not in path.parents or sha(path) != row['sha256']:
            raise ValueError(f'source file changed: {row["path"]}')
    image = subprocess.check_output(['docker', 'image', 'inspect', IMAGE, '--format', '{{.Id}}'], text=True).strip()
    if image != IMAGE_ID:
        raise ValueError('qualification image changed')
    output = QUAL / 'runs_01'
    output.mkdir(exist_ok=False)
    result = {'status': 'EXPOSED_DEVELOPMENT_ADAPTED_ENVIRONMENT', 'revision': REVISION,
              'source_archive_sha256': sha(SOURCE_ZIP), 'source_manifest_sha256': sha(QUAL / 'MANIFEST.json'),
              'image_id': image, 'pythonpath': '/overlay:/deps', 'model_calls': 0,
              'qualification_script_sha256': sha(Path(__file__)), 'cases': {}}
    for name in TASKS:
        task = FAMILY / name
        case = output / name
        case.mkdir()
        config = json.loads((task / 'solution/task_config.json').read_text(encoding='utf-8'))
        destination = Path(config['output_file'])
        if destination.parent != Path('/root') or destination.name != str(destination.relative_to('/root')):
            raise ValueError('unexpected output path')
        work = case / 'reference'
        shutil.copytree(task / 'environment/data', work)
        work.chmod(0o777)
        solve = run(container(work, ['--mount', f'type=bind,src={task / "solution"},dst=/solution,readonly'],
                              ['/bin/bash', '/solution/solve.sh'], False), case / 'reference_solve.log')
        result['cases'][name] = {'source_test_sha256': sha(task / 'tests/test_outputs.py'),
                                 'source_solution_sha256': sha(task / 'solution/tools/reconcile_snapshot.py'),
                                 'source_config_sha256': sha(task / 'solution/task_config.json'),
                                 'reference_solve': solve, 'controls': {}}
        if solve['exit'] != 0 or not (work / destination.name).is_file():
            result['cases'][name]['status'] = 'REFERENCE_NOT_PRODUCED'
            continue
        raw = json.loads((work / destination.name).read_text(encoding='utf-8'))
        deleted_key = config['deleted_key']
        if not raw.get(deleted_key):
            raise ValueError('reference contains no deleted ID for the negative control')
        modified = dict(raw)
        modified[deleted_key] = sorted(raw[deleted_key] + [raw[deleted_key][0]])
        for mode, candidate in (('reference', raw), ('empty', {}), ('duplicate_deleted_id', modified)):
            folder = case / mode
            if mode != 'reference':
                folder.mkdir()
                folder.chmod(0o777)
                (folder / destination.name).write_text(json.dumps(candidate, indent=2) + '\n', encoding='utf-8')
            check = run(container(folder, ['--mount', f'type=bind,src={task / "tests"},dst=/tests,readonly'],
                                  ['python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '/tests/test_outputs.py'], True),
                        case / f'{mode}_test.log')
            check['candidate_sha256'] = sha(folder / destination.name)
            check['deleted_id_count'] = len(candidate.get(deleted_key, []))
            check['unique_deleted_id_count'] = len(set(candidate.get(deleted_key, [])))
            result['cases'][name]['controls'][mode] = check
        result['cases'][name]['status'] = 'RECORDED'
        print(json.dumps({'task': name, 'solve_exit': solve['exit'],
                          'test_exits': {k: v['exit'] for k, v in result['cases'][name]['controls'].items()}}), flush=True)
    receipt = output / 'receipt.json'
    receipt.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt_sha256': sha(receipt), 'path': str(receipt)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--independent', action='store_true')
    parser.add_argument('--counterfactual', action='store_true')
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.worker:
        independent_worker()
    elif args.independent:
        independent_check()
    elif args.counterfactual:
        prepare_counterfactual()
    else:
        main()
