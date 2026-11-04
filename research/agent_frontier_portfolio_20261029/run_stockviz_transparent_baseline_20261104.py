#!/usr/bin/env python3
"""Apply a disclosed source-feedback and file-format rule to the source Agent's output.

This researcher-authored development control uses the failed source artifact,
source feedback and exposed target format, not either target's reference code.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

from qualify_stockviz_shift_20261104 import BROWSERS, DEPS, D3_SHA, IMAGE, QUAL, ROOT, TASKS, digest, tree_digest

SOURCE = ROOT / 'stock_format_agent_20261104/stock-data-visualization-1__no_history__1079719'
OUTPUT = ROOT / 'stock_format_agent_20261104/transparent_baseline'


def adapt_javascript(text: str, version: int) -> str:
    parsers = {2: ('json', 'json'), 3: ('tsv', 'tsv')}
    if version not in parsers:
        raise ValueError('unsupported target')
    old = 'd3.csv("/output/data/stock-descriptions.csv")'
    parser, extension = parsers[version]
    if text.count(old) != 1:
        raise ValueError('source program no longer has the expected data call')
    return text.replace(old, f'd3.{parser}("data/stock-descriptions.{extension}")', 1)


def main() -> None:
    source_receipt = json.loads((SOURCE / 'receipt.json').read_text(encoding='utf-8'))
    if source_receipt['task'] != 'stock-data-visualization-1' or source_receipt['raw_sha256'] != digest(SOURCE / 'raw.jsonl'):
        raise ValueError('source trace differs')
    qualification = json.loads((QUAL / 'runs_02/receipt.json').read_text(encoding='utf-8'))
    if not qualification['qualification_pass'] or digest(QUAL / 'd3.v6.7.0.min.js') != D3_SHA:
        raise ValueError('qualification or D3 failed')
    image_id = subprocess.check_output(['docker', 'image', 'inspect', IMAGE, '--format', '{{.Id}}'], text=True).strip()
    if image_id != qualification['image_id']:
        raise ValueError('verifier image changed')
    OUTPUT.mkdir(parents=True, exist_ok=False)
    summary = {'status': 'EXPOSED_DEVELOPMENT_RESEARCHER_AUTHORED_CONTROL',
               'source_raw_sha256': source_receipt['raw_sha256'],
               'source_receipt_sha256': digest(SOURCE / 'receipt.json'),
               'source_feedback_sha256': digest(SOURCE / 'verifier.txt'),
               'construction': 'Use actual source HTML/CSS/JS; fix its known source-data URL; switch loader using target file extension; copy target input preserving folders.',
               'researcher_has_seen_target_instructions_and_tests': True,
               'model_requests': 0, 'cases': {}}
    source_output = SOURCE / 'work/output'
    for version in (2, 3):
        start = time.monotonic()
        task = TASKS / f'stock-data-visualization-{version}'
        if tree_digest(task / 'environment/data') != qualification['cases'][str(version)]['input_tree']:
            raise ValueError('target input differs from qualification')
        case = OUTPUT / f'task_{version}'
        output = case / 'output'
        logs = case / 'logs'
        (output / 'js').mkdir(parents=True)
        (output / 'css').mkdir()
        logs.mkdir()
        logs.chmod(0o777)
        for name in ('index.html', 'css/style.css'):
            src = source_output / name
            if not src.is_file() or src.is_symlink():
                raise ValueError(f'missing source output {name}')
            shutil.copy2(src, output / name)
        shutil.copy2(QUAL / 'd3.v6.7.0.min.js', output / 'js/d3.v6.min.js')
        shutil.copytree(task / 'environment/data', output / 'data', symlinks=False)
        js = source_output / 'js/visualization.js'
        (output / 'js/visualization.js').write_text(adapt_javascript(js.read_text(encoding='utf-8'), version), encoding='utf-8')
        verify = ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--cpus', '2',
                  '--memory', '2g', '--pids-limit', '256', '--cap-drop', 'ALL',
                  '--security-opt', 'no-new-privileges', '--shm-size', '512m',
                  '-e', 'PYTHONPATH=/deps', '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
                  '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'PLAYWRIGHT_BROWSERS_PATH=/ms-playwright',
                  '--mount', f'type=bind,src={output},dst=/root/output,readonly',
                  '--mount', f'type=bind,src={task / "tests"},dst=/tests,readonly',
                  '--mount', f'type=bind,src={logs},dst=/logs/verifier',
                  '--mount', f'type=bind,src={DEPS},dst=/deps,readonly',
                  '--mount', f'type=bind,src={BROWSERS},dst=/ms-playwright,readonly',
                  IMAGE, 'python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '/tests/test_outputs.py']
        try:
            run = subprocess.run(verify, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 stdin=subprocess.DEVNULL, timeout=240)
            rc, content = run.returncode, run.stdout
        except subprocess.TimeoutExpired as exc:
            rc, content = 124, exc.stdout or b''
        log = case / 'verifier.log'
        log.write_bytes(content)
        summary['cases'][str(version)] = {'verifier_exit': rc, 'seconds': round(time.monotonic() - start, 3),
            'verifier_sha256': digest(task / 'tests/test_outputs.py'), 'log_sha256': digest(log),
            'input_tree': tree_digest(task / 'environment/data'), 'source_js_sha256': digest(js),
            'adapted_js_sha256': digest(output / 'js/visualization.js')}
        print(json.dumps({'task': version, 'verifier_exit': rc}), flush=True)
    receipt = OUTPUT / 'receipt.json'
    receipt.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt_sha256': hashlib.sha256(receipt.read_bytes()).hexdigest()}), flush=True)


if __name__ == '__main__':
    main()
