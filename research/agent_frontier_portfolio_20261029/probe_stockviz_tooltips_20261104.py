#!/usr/bin/env python3
"""Post-hoc tooltip diagnostic; supports opacity as well as class visibility.

The published test looks for a `.visible` class. This separate probe reports
actual computed style and text after a synthetic event, plus whether Playwright
can physically hover the same circle. It does not replace the published score.
"""
from __future__ import annotations

import argparse
from functools import partial
import hashlib
import http.server
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading

from qualify_stockviz_shift_20261104 import BROWSERS, DEPS, IMAGE, QUAL, ROOT, TASKS, digest


def worker() -> None:
    from playwright.sync_api import sync_playwright

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory='/root/output'))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    result = {'probe': 'POST_HOC_TOOLTIP_DIAGNOSTIC', 'errors': []}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on('pageerror', lambda e: result['errors'].append(str(e)[:400]))
            response = page.goto(f'http://127.0.0.1:{server.server_port}/index.html', wait_until='load', timeout=30000)
            result['http_status'] = response.status if response else None
            page.wait_for_timeout(4000)
            circles = page.locator('svg circle')
            result['circle_count'] = circles.count()
            result['row_count'] = page.locator('table tbody tr').count()
            data = page.evaluate('''() => [...document.querySelectorAll('svg circle')].map((e,i) => {
              const d=e.__data__ || {}; return {index:i,ticker:d.ticker||d.symbol||null,
              sector:d.sector||null, name:d.full_name||d['full name']||d.name||null}; })''')
            stock = next((d for d in data if d['ticker'] and d['sector']
                          and 'etf' not in str(d['sector']).lower()), None)
            if stock is None:
                result['status'] = 'NO_IDENTIFIABLE_BOUND_STOCK'
            else:
                circle = circles.nth(stock['index'])
                circle.dispatch_event('mouseover', {'bubbles': True})
                page.wait_for_timeout(200)
                tips = page.locator('#tooltip, .tooltip, [role="tooltip"]')
                def visible_tips():
                    visible = []
                    for i in range(tips.count()):
                        state = tips.nth(i).evaluate('''e => {const s=getComputedStyle(e); const r=e.getBoundingClientRect();
                          return {display:s.display, visibility:s.visibility, opacity:Number(s.opacity),
                                  width:r.width,height:r.height,text:e.innerText||''};}''')
                        if (state['display'] != 'none' and state['visibility'] != 'hidden'
                                and state['opacity'] > 0.1 and state['width'] > 0 and state['height'] > 0):
                            visible.append(state)
                    return visible
                visible = visible_tips()
                result['synthetic_mouseover'] = {
                    'ticker': stock['ticker'], 'sector': stock['sector'], 'tooltip_count': len(visible),
                    'ticker_in_tooltip': any(str(stock['ticker']).lower() in x['text'].lower() for x in visible),
                    'sector_in_tooltip': any(str(stock['sector']).lower() in x['text'].lower() for x in visible),
                    'name_in_tooltip': (any(str(stock['name']).lower() in x['text'].lower() for x in visible)
                                        if stock['name'] else None)}
                try:
                    circle.dispatch_event('mouseout', {'bubbles': True})
                    page.mouse.move(0, 0)
                    page.wait_for_timeout(300)
                    circle.hover(timeout=2500)
                    page.wait_for_timeout(300)
                    actual = visible_tips()
                    result['physical_hover'] = {'status': 'PLAYWRIGHT_HOVER_SUCCEEDED',
                        'tooltip_count': len(actual),
                        'ticker_in_tooltip': any(str(stock['ticker']).lower() in x['text'].lower() for x in actual),
                        'sector_in_tooltip': any(str(stock['sector']).lower() in x['text'].lower() for x in actual),
                        'name_in_tooltip': (any(str(stock['name']).lower() in x['text'].lower() for x in actual)
                                            if stock['name'] else None)}
                except Exception as exc:
                    result['physical_hover'] = {'status': type(exc).__name__}
                page.mouse.move(0, 0)
                page.wait_for_timeout(300)
                etfs = [d for d in data if d['ticker'] and d['sector']
                        and 'etf' in str(d['sector']).lower()]
                result['etf_physical_hover'] = {'status': 'NO_IDENTIFIABLE_ETF'}
                for etf in etfs[:5]:
                    try:
                        circles.nth(etf['index']).hover(timeout=1500)
                        page.wait_for_timeout(300)
                        result['etf_physical_hover'] = {'status': 'PLAYWRIGHT_HOVER_SUCCEEDED',
                            'ticker': etf['ticker'], 'tooltip_count': len(visible_tips())}
                        break
                    except Exception:
                        result['etf_physical_hover'] = {'status': 'HOVER_UNREACHABLE'}
                result['status'] = 'OBSERVED'
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print(json.dumps(result, ensure_ascii=False))


def opacity_control() -> None:
    """Change only how the passing reference toggles tooltip visibility."""
    reference = QUAL / 'runs_02/task_2/output'
    root = QUAL / 'opacity_control_20261104'
    output = root / 'output'
    logs = root / 'logs'
    root.mkdir(parents=True, exist_ok=False)
    shutil.copytree(reference, output)
    logs.mkdir()
    logs.chmod(0o777)
    original = (reference / 'js/visualization.js').read_text(encoding='utf-8')
    show, hide = ".classed('visible', true)", ".classed('visible', false)"
    if original.count(show) != 1 or original.count(hide) != 1:
        raise ValueError('reference tooltip implementation changed')
    revised = original.replace(show, ".style('opacity', 1)", 1).replace(hide, ".style('opacity', 0)", 1)
    (output / 'js/visualization.js').write_text(revised, encoding='utf-8')
    # Compare file names and bytes, except for the explicitly modified JS.
    ref_files = {p.relative_to(reference) for p in reference.rglob('*') if p.is_file()}
    out_files = {p.relative_to(output) for p in output.rglob('*') if p.is_file()}
    changed = [str(p) for p in sorted(ref_files & out_files) if digest(reference / p) != digest(output / p)]
    if ref_files != out_files or changed != ['js/visualization.js']:
        raise ValueError('unexpected change in control')
    task = TASKS / 'stock-data-visualization-2'
    command = ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--cpus', '2',
               '--memory', '2g', '--pids-limit', '256', '--cap-drop', 'ALL',
               '--security-opt', 'no-new-privileges', '--shm-size', '512m',
               '-e', 'PYTHONPATH=/deps', '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
               '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'PLAYWRIGHT_BROWSERS_PATH=/ms-playwright',
               '--mount', f'type=bind,src={output},dst=/root/output,readonly',
               '--mount', f'type=bind,src={task / "tests"},dst=/tests,readonly',
               '--mount', f'type=bind,src={logs},dst=/logs/verifier',
               '--mount', f'type=bind,src={DEPS},dst=/deps,readonly',
               '--mount', f'type=bind,src={BROWSERS},dst=/ms-playwright,readonly',
               IMAGE, 'python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
               '/tests/test_outputs.py', '-k', 'test_tooltips_non_etf_and_etf']
    run = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, timeout=120, check=False)
    log = root / 'upstream_tooltip_test.log'
    log.write_bytes(run.stdout)
    probe = subprocess.run([sys.executable, str(Path(__file__).resolve()), str(output)],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                           timeout=120, check=True)
    observed = json.loads(probe.stdout.decode('utf-8'))
    receipt = {'status': 'POST_HOC_CONSTRUCTED_CONTROL', 'reference_js_sha256': digest(reference / 'js/visualization.js'),
               'control_js_sha256': digest(output / 'js/visualization.js'), 'changed_files': changed,
               'upstream_tooltip_test_exit': run.returncode, 'upstream_log_sha256': digest(log),
               'independent_probe': observed, 'model_requests': 0}
    path = root / 'receipt.json'
    path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'receipt': receipt, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('output_dir', type=Path, nargs='?')
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--opacity-control', action='store_true')
    args = parser.parse_args()
    if args.worker:
        worker()
        return
    if args.opacity_control:
        opacity_control()
        return
    if args.output_dir is None:
        parser.error('output_dir is required')
    output = args.output_dir.resolve(strict=True)
    if ROOT.resolve() not in output.parents or not output.is_dir():
        raise ValueError('expected a private research evidence output directory')
    cmd = ['docker', 'run', '--rm', '--pull', 'never', '--network', 'none', '--cpus', '2',
           '--memory', '2g', '--pids-limit', '256', '--cap-drop', 'ALL',
           '--security-opt', 'no-new-privileges', '--shm-size', '512m',
           '-e', 'PYTHONPATH=/deps', '-e', 'PLAYWRIGHT_BROWSERS_PATH=/ms-playwright',
           '--mount', f'type=bind,src={output},dst=/root/output,readonly',
           '--mount', f'type=bind,src={Path(__file__).resolve()},dst=/probe.py,readonly',
           '--mount', f'type=bind,src={Path(__file__).with_name("qualify_stockviz_shift_20261104.py").resolve()},dst=/qualify_stockviz_shift_20261104.py,readonly',
           '--mount', f'type=bind,src={DEPS},dst=/deps,readonly',
           '--mount', f'type=bind,src={BROWSERS},dst=/ms-playwright,readonly',
           IMAGE, 'python', '/probe.py', '--worker']
    completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               stdin=subprocess.DEVNULL, timeout=90, check=False)
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode('utf-8', errors='replace')[-2000:])
    print(completed.stdout.decode('utf-8').strip())


if __name__ == '__main__':
    main()
