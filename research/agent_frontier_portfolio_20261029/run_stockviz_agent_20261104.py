#!/usr/bin/env python3
"""Run exposed-development stock-format episodes using the pinned Agent harness."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from qualify_stockviz_shift_20261104 import COMMIT, D3_SHA, QUAL, TASKS, digest, tree_digest

ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
BASE = Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029/run_skill_episode_output8192.py')
BASE_SHA = '4111a0be97845740769722e2e596871d51c7693d14d2372d7f6931b4d06e7afb'
OUTPUT = ROOT / 'stock_format_agent_20261104'
RECEIPT = QUAL / 'runs_02/receipt.json'
BROWSERS = Path('/home/testuser/.cache/ms-playwright')
VERIFIER_IMAGE = 'agent-stockviz-verifier:20261104'


def replace_once(source: str, old: str, new: str, count: int = 1) -> str:
    if source.count(old) != count:
        raise ValueError(f'unexpected harness fragment: {old[:80]!r}')
    return source.replace(old, new, count)


def prepare(version: int, condition: str, experience: Path | None):
    if digest(BASE) != BASE_SHA:
        raise ValueError('base harness changed')
    qual = json.loads(RECEIPT.read_text(encoding='utf-8'))
    case = qual['cases'][str(version)]
    if not qual['qualification_pass'] or qual['revision'] != COMMIT:
        raise ValueError('qualification did not pass')
    if subprocess.check_output(['docker', 'image', 'inspect', VERIFIER_IMAGE, '--format', '{{.Id}}'], text=True).strip() != qual['image_id']:
        raise ValueError('verifier image differs from qualification')
    src = TASKS / f'stock-data-visualization-{version}'
    if (digest(src / 'instruction.md') != case['instruction_sha256']
            or digest(src / 'tests/test_outputs.py') != case['verifier_sha256']
            or tree_digest(src / 'environment/data') != case['input_tree']
            or digest(QUAL / 'd3.v6.7.0.min.js') != D3_SHA):
        raise ValueError('frozen task, data, verifier or D3 differs')
    if version == 1 and condition != 'no_history':
        raise ValueError('source task must start without history')

    history_mounts = []
    history_hashes = {}
    if condition != 'no_history':
        if experience is None:
            raise ValueError('history condition needs source experience')
        config = json.loads((experience / 'config.json').read_text(encoding='utf-8'))
        history = experience / 'source_history.json'
        if config['source_history_sha256'] != digest(history) or config['source_task'] != 1:
            raise ValueError('source experience changed')
        if condition == 'raw_history':
            mount = history
        else:
            mount = experience / 'skill.md'
            ledger = json.loads((experience / 'ledger.json').read_text(encoding='utf-8'))
            if ledger['status'] != 'RECEIVED' or ledger['skill_sha256'] != digest(mount):
                raise ValueError('generated skill unavailable or changed')
            history_hashes['skill_ledger'] = digest(experience / 'ledger.json')
        dest = '/root/source_history.json' if condition == 'raw_history' else '/root/source_skill.md'
        history_mounts.append((mount, dest))
        history_hashes[dest] = digest(mount)

    code = BASE.read_text(encoding='utf-8')
    edits = [
        ("ROOT=Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029')",
         f'ROOT=Path({str(OUTPUT)!r})', 1),
        ("UP=Path('/home/testuser/wzh/research_evidence/agent_frontier_20261029/skillsbench_v1_1/tasks')",
         f'UP=Path({str(TASKS)!r})', 1),
        ("if task not in ('llm-prefix-cache-replay','dialogue-parser','tictoc-unnecessary-abort-detection') or arm not in ('no_skill','all_skill','select_skill'): raise SystemExit('unsupported')",
         "if task not in ('stock-data-visualization-1','stock-data-visualization-2','stock-data-visualization-3') or arm != 'no_skill': raise SystemExit('unsupported')", 1),
        ("body=(src/'task.md').read_text(encoding='utf8').split('---',2)[2].strip()",
         "body=(src/'instruction.md').read_text(encoding='utf8').strip()", 1),
        ("(work/'instructions.txt').write_text(body,encoding='utf8')",
         "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
         "(work/'data').mkdir(); (work/'d3.v6.7.0.min.js').touch(mode=0o444)\n"
         "for _source,_dest in STOCK_HISTORY: (work/Path(_dest).name).touch(mode=0o444)", 1),
        ("Never read an entire large trace into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified file.",
         "A local D3 6.7.0 bundle is available at /root/d3.v6.7.0.min.js; copy it to the required output path. The task inputs are in /root/data.", 1),
        ("len(calls)>=8", "len(calls)>=24", 1),
        ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>1500000", 1),
        ("'timeout':120000", "'timeout':300000", 1),
        ("[],[],120)", "[],[],300)", 2),
        ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=1200)", 1),
        ("'--cpus','1','--cap-drop'", "'--cpus','2','--cap-drop'", 1),
        ("'--memory','2g'", "'--memory','3g'", 1),
        ("server=Server(str(sockpath),Handler);",
         "_at=cmd.index('python:3.12-slim'); "
         "cmd[_at:_at]=['--mount',f'type=bind,src={src / \"environment/data\"},dst=/root/data,readonly',"
         "'--mount',f'type=bind,src={STOCK_D3},dst=/root/d3.v6.7.0.min.js,readonly'] + "
         "[z for source,dest in STOCK_HISTORY for z in ('--mount',f'type=bind,src={source},dst={dest},readonly')]; "
         "server=Server(str(sockpath),Handler);", 1),
        ("sockpath.unlink(missing_ok=True)", "sockpath.unlink(missing_ok=True);bridge.rmdir()", 1),
        ("# A completely separate non-agent container mounts verifier after the episode;",
         "(case/'verifier_artifacts').mkdir(); (case/'verifier_artifacts').chmod(0o777)\n"
         "# A completely separate non-agent container mounts verifier after the episode;", 1),
        ("'--network','none','--cpus','1','--memory','768m'",
         "'--network','none','--shm-size','512m','--cpus','2','--memory','2g'", 1),
        ("'-e','PYTHONPATH=/deps','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1'",
         "'-e','PYTHONPATH=/deps','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',"
         "'-e','PYTHONDONTWRITEBYTECODE=1','-e','PLAYWRIGHT_BROWSERS_PATH=/ms-playwright',"
         "'--mount',f'type=bind,src={STOCK_BROWSERS},dst=/ms-playwright,readonly',"
         "'--mount',f'type=bind,src={case / \"verifier_artifacts\"},dst=/logs/verifier'", 1),
        ("'--mount',f'type=bind,src={work},dst={target}', '--mount',f'type=bind,src={src / \"verifier\"},dst=/verifier,readonly'",
         "'--mount',f'type=bind,src={work},dst={target},readonly', '--mount',f'type=bind,src={src / \"tests\"},dst=/verifier,readonly'", 1),
        ("'python:3.12-slim','/bin/sh','-c',verifier_command]",
         f"{VERIFIER_IMAGE!r},'/bin/sh','-c',verifier_command]", 1),
        ("case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))",
         f"case=ROOT/(task+'__{condition}__'+str(os.getpid()))", 1),
        ("receipt={'task':task,'arm':arm", f"receipt={{'task':task,'arm':'{condition}'", 1),
    ]
    for old, new, count in edits:
        code = replace_once(code, old, new, count)
    if history_mounts:
        code = replace_once(code, 'Use available tools to implement and execute your solution.',
                            f'Before solving, read {history_mounts[0][1]}, generated from a prior related task. '
                            'Follow the current task. Use available tools to implement and execute your solution.')
    compile(code, str(BASE), 'exec')
    metadata = {'status': 'EXPOSED_DEVELOPMENT_NOT_OFFICIAL', 'task': version, 'condition': condition,
                'source_revision': COMMIT, 'qualification_sha256': digest(RECEIPT),
                'instruction_sha256': case['instruction_sha256'], 'input_tree': case['input_tree'],
                'verifier_sha256': case['verifier_sha256'], 'verifier_image': qual['image_id'],
                'd3_sha256': D3_SHA, 'base_harness_sha256': BASE_SHA,
                'derived_harness_sha256': hashlib.sha256(code.encode()).hexdigest(),
                'adapter_sha256': digest(Path(__file__)), 'source_experience_sha256': history_hashes,
                'max_http': 24, 'max_post_body_bytes': 1500000, 'max_wall_seconds': 1200,
                'model': 'qwen3.6-35b-a3b (configured; deployed weight hash not independently verified)',
                'sandbox': 'network-free container; bounded local model proxy; verifier mounted after agent'}
    return code, history_mounts, metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('task', type=int, choices=(1, 2, 3))
    parser.add_argument('--condition', choices=('no_history', 'raw_history', 'generated_skill'), default='no_history')
    parser.add_argument('--experience', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    code, mounts, metadata = prepare(args.task, args.condition, args.experience)
    print(json.dumps(metadata), flush=True)
    if args.check:
        return
    sys.argv = [str(BASE), f'stock-data-visualization-{args.task}', 'no_skill']
    namespace = {'__name__': '__main__', '__file__': str(BASE), 'STOCK_HISTORY': mounts,
                 'STOCK_D3': QUAL / 'd3.v6.7.0.min.js', 'STOCK_BROWSERS': BROWSERS}
    try:
        exec(compile(code, str(BASE), 'exec'), namespace)
    finally:
        run_dir = namespace.get('case')
        if run_dir is not None and run_dir.is_dir():
            (run_dir / 'intervention.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
