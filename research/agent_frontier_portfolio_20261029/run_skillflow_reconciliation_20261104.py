#!/usr/bin/env python3
"""Run a no-history SkillFlow reconciliation episode with a separate evaluator."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from qualify_skillflow_reconciliation_20261104 import (
    FAMILY, QUAL, REVISION, ROOT, SITE, SOURCE_ZIP, TASKS, ZIP_SHA, container, run, sha,
)

BASE = Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029/run_skill_episode_output8192.py')
BASE_SHA = '4111a0be97845740769722e2e596871d51c7693d14d2372d7f6931b4d06e7afb'
OUTPUT = ROOT / 'skillflow_reconciliation_agent_20261104'


def replace_once(source: str, old: str, new: str, count: int = 1) -> str:
    if source.count(old) != count:
        raise ValueError(f'unexpected harness fragment: {old[:80]!r}')
    return source.replace(old, new, count)


def prepare(task: str, variant: str) -> tuple[str, Path, dict]:
    if task not in TASKS or (variant == 'stale_example' and task != TASKS[1]):
        raise ValueError('unsupported task/variant')
    if sha(BASE) != BASE_SHA or sha(SOURCE_ZIP) != ZIP_SHA:
        raise ValueError('base harness or source archive changed')
    manifest = json.loads((QUAL / 'MANIFEST.json').read_text(encoding='utf-8'))
    if manifest['revision'] != REVISION:
        raise ValueError('source revision changed')
    for row in manifest['files']:
        path = (QUAL / row['path']).resolve()
        if QUAL.resolve() not in path.parents or sha(path) != row['sha256']:
            raise ValueError('source file changed')
    upstream = json.loads((QUAL / 'runs_01/receipt.json').read_text(encoding='utf-8'))
    independent = json.loads((QUAL / 'runs_01/independent_recheck.json').read_text(encoding='utf-8'))
    for name in TASKS:
        controls = upstream['cases'][name]['controls']
        reference = independent['cases'][name]['reference']['result']
        if controls['reference']['exit'] != 0 or controls['empty']['exit'] == 0:
            raise ValueError('reference or empty-output qualification failed')
        if not reference['deleted_exact_including_multiplicity'] or not reference['changed_fields_exact_including_multiplicity']:
            raise ValueError('independent source recomputation failed')
    source = FAMILY / task
    inputs = source / 'environment/data'
    if variant == 'stale_example':
        counter = json.loads((QUAL / 'counterfactual_02/manifest.json').read_text(encoding='utf-8'))
        check = json.loads((QUAL / 'counterfactual_02/stale_reference_check.json').read_text(encoding='utf-8'))
        if check['manifest_sha256'] != sha(QUAL / 'counterfactual_02/manifest.json'):
            raise ValueError('counterfactual manifest changed')
        if check['check']['result']['changed_fields_exact_including_multiplicity']:
            raise ValueError('stale example negative control unexpectedly passed')
        inputs = QUAL / 'counterfactual_02/input'
        config = json.loads((source / 'solution/task_config.json').read_text(encoding='utf-8'))
        book = inputs / Path(config['excel_file']).name
        if counter['modified_workbook_sha256'] != sha(book):
            raise ValueError('counterfactual workbook changed')
        for name, expected in counter['untouched_inputs'].items():
            if sha(inputs / name) != expected:
                raise ValueError('counterfactual non-workbook input changed')
    input_hashes = {p.name: sha(p) for p in sorted(inputs.iterdir()) if p.is_file() and not p.is_symlink()}
    if len(input_hashes) != 2:
        raise ValueError('expected one PDF and one workbook')
    code = BASE.read_text(encoding='utf-8')
    edits = [
        ("ROOT=Path('/home/testuser/wzh/research_evidence/agent_skill_method_20261029')", f'ROOT=Path({str(OUTPUT)!r})', 1),
        ("UP=Path('/home/testuser/wzh/research_evidence/agent_frontier_20261029/skillsbench_v1_1/tasks')", f'UP=Path({str(FAMILY)!r})', 1),
        ("if task not in ('llm-prefix-cache-replay','dialogue-parser','tictoc-unnecessary-abort-detection') or arm not in ('no_skill','all_skill','select_skill'): raise SystemExit('unsupported')",
         f"if task not in {TASKS!r} or arm != 'no_skill': raise SystemExit('unsupported')", 1),
        ("body=(src/'task.md').read_text(encoding='utf8').split('---',2)[2].strip()",
         "body=(src/'instruction.md').read_text(encoding='utf8').strip()", 1),
        ("(work/'instructions.txt').write_text(body,encoding='utf8')",
         "(work/'instructions.txt').write_text(body,encoding='utf8')\n"
         "for _input in SKILLFLOW_INPUT.iterdir():\n"
         " if not _input.is_file() or _input.is_symlink(): raise ValueError('invalid input')\n"
         " shutil.copy2(_input, work/_input.name)", 1),
        ("Never read an entire large trace into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified file.",
         "The local Python environment includes pypdf and openpyxl; use only the current task inputs.", 1),
        ("len(calls)>=8", "len(calls)>=24", 1),
        ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>1500000", 1),
        ("calls.append('DENIED_OR_LIMIT');self.request.sendall",
         "reason=('method' if line not in allowed else 'request_cap' if len(calls)>=24 "
         "else 'missing_length' if length is None else 'post_byte_cap')\n"
         "   calls.append('DENIED:'+reason);self.request.sendall", 1),
        ("'timeout':120000", "'timeout':300000", 1),
        ("[],[],120)", "[],[],300)", 2),
        ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=1200)", 1),
        ("'--cpus','1','--cap-drop'", "'--cpus','2','--cap-drop'", 1),
        ("'--memory','2g'", "'--memory','3g'", 1),
        ("server=Server(str(sockpath),Handler);",
         "_at=cmd.index('python:3.12-slim'); cmd[_at:_at]=['-e','PYTHONPATH=/deps',"
         "'--mount',f'type=bind,src={DEPS},dst=/deps,readonly']; server=Server(str(sockpath),Handler);", 1),
        ("sockpath.unlink(missing_ok=True)", "sockpath.unlink(missing_ok=True);bridge.rmdir()", 1),
        ("'--mount',f'type=bind,src={work},dst={target}', '--mount',f'type=bind,src={src / \"verifier\"},dst=/verifier,readonly'",
         "'--mount',f'type=bind,src={work},dst={target},readonly', '--mount',f'type=bind,src={src / \"tests\"},dst=/verifier,readonly'", 1),
        ("case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))",
         f"case=ROOT/(task+'__{variant}__'+str(os.getpid()))", 1),
        ("receipt={'task':task,'arm':arm", f"receipt={{'task':task,'arm':'{variant}'", 1),
    ]
    for old, new, count in edits:
        code = replace_once(code, old, new, count)
    compile(code, str(BASE), 'exec')
    metadata = {'status': 'EXPOSED_DEVELOPMENT_NOT_OFFICIAL_HARNESS', 'task': task, 'variant': variant,
                'revision': REVISION, 'instruction_sha256': sha(source / 'instruction.md'),
                'input_hashes': input_hashes, 'verifier_sha256': sha(source / 'tests/test_outputs.py'),
                'source_qualification_sha256': sha(QUAL / 'runs_01/receipt.json'),
                'independent_qualification_sha256': sha(QUAL / 'runs_01/independent_recheck.json'),
                'base_sha256': BASE_SHA, 'derived_sha256': hashlib.sha256(code.encode()).hexdigest(),
                'adapter_sha256': sha(Path(__file__)), 'max_http': 24,
                'max_post_body_bytes': 1500000, 'max_wall_seconds': 1200,
                'upstream_verifier_interpretation': ('ORIGINAL_TASK_ONLY_WRONG_FOR_COUNTERFACTUAL' if variant == 'stale_example' else 'ORIGINAL_TASK'),
                'model': 'qwen3.6-35b-a3b configured; deployed weight hash unverified',
                'sandbox': 'network-free container; bounded local model proxy; no target tests/reference until exit'}
    return code, inputs, metadata


def score_independently(task: str, variant: str, inputs: Path, case: Path) -> dict:
    source = FAMILY / task
    config = json.loads((source / 'solution/task_config.json').read_text(encoding='utf-8'))
    output_path = case / 'work' / Path(config['output_file']).name
    result = {'status': 'NO_OUTPUT', 'model_calls': 0}
    if not output_path.is_file() or output_path.is_symlink():
        return result
    checker = QUAL / 'qualify_skillflow_reconciliation_20261104.py'
    extra = ['--mount', f'type=bind,src={inputs},dst=/inputs,readonly',
             '--mount', f'type=bind,src={source / "solution/task_config.json"},dst=/contract/task_config.json,readonly',
             '--mount', f'type=bind,src={source / "instruction.md"},dst=/instruction.md,readonly',
             '--mount', f'type=bind,src={checker},dst=/checker.py,readonly']
    log = case / 'independent_check.log'
    observed = run(container(case / 'work', extra, ['python', '/checker.py', '--worker'], True), log)
    result = {'status': 'CHECKER_FAILED', 'candidate_sha256': sha(output_path),
              'checker_sha256': sha(checker), 'check': observed, 'model_calls': 0}
    if observed['exit'] == 0:
        result['status'] = 'RECORDED'
        result['result'] = json.loads(log.read_text(encoding='utf-8'))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('task', choices=TASKS)
    parser.add_argument('--variant', choices=('normal', 'stale_example'), default='normal')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    code, inputs, metadata = prepare(args.task, args.variant)
    print(json.dumps(metadata), flush=True)
    if args.check:
        return
    sys.argv = [str(BASE), args.task, 'no_skill']
    namespace = {'__name__': '__main__', '__file__': str(BASE), 'SKILLFLOW_INPUT': inputs}
    try:
        exec(compile(code, str(BASE), 'exec'), namespace)
    finally:
        case = namespace.get('case')
        if case is not None and case.is_dir():
            (case / 'intervention.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    result = score_independently(args.task, args.variant, inputs, case)
    (case / 'independent_receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'independent': result}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
