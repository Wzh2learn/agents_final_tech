"""Behavioral checks for the compact research-context gate."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/graph/research_context_check.py'
PATHS = (
    'memory/STATE.md',
    'memory/THREADS.md',
    'docs/research/README.md',
    'docs/research/LOOP_D_RESEARCH_PROMPT.md',
    'research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md',
    'research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md',
    'research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md',
)


def seed(root):
    for name in PATHS:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('current\n', encoding='utf-8')


def run(root, *args):
    result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(root), *map(str, args)],
                            capture_output=True, text=True, encoding='utf-8')
    return result, json.loads(result.stdout)


def test_cap_is_utf8_bytes_and_accepts_exact_boundary(tmp_path):
    root = tmp_path / 'repo'
    seed(root)
    state = root / 'memory/STATE.md'
    state.write_text('汉' * 1365 + 'x', encoding='utf-8')
    proc, result = run(root)
    item = next(x for x in result['files'] if x['path'] == 'memory/STATE.md')
    assert proc.returncode == 0
    assert item['bytes'] == item['cap'] == 4096
    state.write_text('汉' * 1365 + 'xx', encoding='utf-8')
    proc, result = run(root)
    assert proc.returncode == 1
    assert any(x['kind'] == 'file_cap' and x['path'] == 'memory/STATE.md' for x in result['failures'])


def test_missing_and_local_links_with_fragments(tmp_path):
    root = tmp_path / 'repo'
    seed(root)
    (root / 'memory/THREADS.md').unlink()
    state = root / 'memory/STATE.md'
    state.write_text('[ok](../docs/research/README.md#section)\n'
                     '[missing](../docs/research/missing.md#item)\n'
                     '[web](https://example.test/no) [local](#heading)\n'
                     '```md\n[example](no-file.md)\n```\n', encoding='utf-8')
    proc, result = run(root)
    assert proc.returncode == 1
    assert {(f['kind'], f['path']) for f in result['failures']} == {
        ('missing_file', 'memory/THREADS.md'), ('broken_link', 'memory/STATE.md')}
    assert next(f for f in result['failures'] if f['kind'] == 'broken_link')['target'] == '../docs/research/missing.md#item'


def test_total_cap_and_external_json_matches_stdout(tmp_path):
    root = tmp_path / 'repo'
    seed(root)
    for name, size in zip(PATHS[:5], (4096, 5120, 4096, 6144, 10240)):
        (root / name).write_text('x' * size, encoding='utf-8')
    (root / PATHS[5]).write_text('x' * 4096, encoding='utf-8')
    output = tmp_path / 'report.json'
    proc, result = run(root, '--json', output)
    assert proc.returncode == 1
    assert any(x['kind'] == 'total_cap' for x in result['failures'])
    assert not any(x['kind'] == 'file_cap' for x in result['failures'])
    assert json.loads(output.read_text(encoding='utf-8')) == result


def test_json_destination_cannot_write_into_repo(tmp_path):
    root = tmp_path / 'repo'
    seed(root)
    output = root / 'report.json'
    proc = subprocess.run([sys.executable, str(SCRIPT), '--root', str(root), '--json', str(output)],
                          capture_output=True, text=True)
    assert proc.returncode == 2
    assert not output.exists()
