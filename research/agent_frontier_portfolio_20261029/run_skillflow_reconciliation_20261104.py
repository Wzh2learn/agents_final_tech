#!/usr/bin/env python3
"""Run a no-history SkillFlow reconciliation episode with a separate evaluator."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

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


def prepare(task: str, variant: str, condition: str = 'no_history',
            experience: Path | None = None) -> tuple[str, Path, dict, tuple[Path, str] | None]:
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
    history_mount = None
    if condition != 'no_history':
        if task != TASKS[1] or experience is None:
            raise ValueError('source experience applies only to the target task')
        config = json.loads((experience / 'config.json').read_text(encoding='utf-8'))
        if config['source_task'] != TASKS[0] or config['history_sha256'] != sha(experience / 'source_history.json'):
            raise ValueError('source experience changed')
        if condition == 'source_history':
            file = experience / 'readable_history.txt'
            if config['readable_history_sha256'] != sha(file):
                raise ValueError('readable history changed')
            history_mount = (file, '/root/source_history_readable.txt')
        elif condition == 'generated_skill':
            file = experience / 'skill.md'
            ledger = json.loads((experience / 'ledger.json').read_text(encoding='utf-8'))
            if ledger['status'] != 'RECEIVED' or ledger['skill_sha256'] != sha(file):
                raise ValueError('source skill unavailable or changed')
            history_mount = (file, '/root/source_skill.md')
        else:
            raise ValueError('unsupported experience condition')
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
         " shutil.copy2(_input, work/_input.name)\n"
         "if SKILLFLOW_HISTORY: (work/Path(SKILLFLOW_HISTORY[1]).name).touch(mode=0o444)", 1),
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
         "'--mount',f'type=bind,src={DEPS},dst=/deps,readonly'] + "
         "(['--mount',f'type=bind,src={SKILLFLOW_HISTORY[0]},dst={SKILLFLOW_HISTORY[1]},readonly'] if SKILLFLOW_HISTORY else []); "
         "server=Server(str(sockpath),Handler);", 1),
        ("sockpath.unlink(missing_ok=True)", "sockpath.unlink(missing_ok=True);bridge.rmdir()", 1),
        ("'--mount',f'type=bind,src={work},dst={target}', '--mount',f'type=bind,src={src / \"verifier\"},dst=/verifier,readonly'",
         "'--mount',f'type=bind,src={work},dst={target},readonly', '--mount',f'type=bind,src={src / \"tests\"},dst=/verifier,readonly'", 1),
        ("case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))",
         f"case=ROOT/(task+'__{variant if condition == 'no_history' else variant + '__' + condition}__'+str(os.getpid()))", 1),
        ("receipt={'task':task,'arm':arm", f"receipt={{'task':task,'arm':'{variant}__{condition}'", 1),
    ]
    for old, new, count in edits:
        code = replace_once(code, old, new, count)
    if history_mount:
        code = replace_once(code, 'Use available tools to implement and execute your solution.',
                            f'Before solving, read {history_mount[1]} from a prior related task; '
                            'decide what applies and follow the current task. '
                            'Use available tools to implement and execute your solution.')
    compile(code, str(BASE), 'exec')
    metadata = {'status': 'EXPOSED_DEVELOPMENT_NOT_OFFICIAL_HARNESS', 'task': task, 'variant': variant, 'condition': condition,
                'revision': REVISION, 'instruction_sha256': sha(source / 'instruction.md'),
                'input_hashes': input_hashes, 'verifier_sha256': sha(source / 'tests/test_outputs.py'),
                'source_qualification_sha256': sha(QUAL / 'runs_01/receipt.json'),
                'independent_qualification_sha256': sha(QUAL / 'runs_01/independent_recheck.json'),
                'base_sha256': BASE_SHA, 'derived_sha256': hashlib.sha256(code.encode()).hexdigest(),
                'adapter_sha256': sha(Path(__file__)), 'max_http': 24,
                'max_post_body_bytes': 1500000, 'max_wall_seconds': 1200,
                'upstream_verifier_interpretation': ('ORIGINAL_TASK_ONLY_WRONG_FOR_COUNTERFACTUAL' if variant == 'stale_example' else 'ORIGINAL_TASK'),
                'model': 'qwen3.6-35b-a3b configured; deployed weight hash unverified',
                'sandbox': 'network-free container; bounded local model proxy; no target tests/reference until exit',
                'source_experience_sha256': {history_mount[1]: sha(history_mount[0])} if history_mount else {}}
    return code, inputs, metadata, history_mount


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


def build_source_experience(source: Path, output: Path) -> None:
    """Generate one skill from the recorded source episode and source-only feedback."""
    source = source.resolve(strict=True)
    if OUTPUT.resolve() not in source.parents:
        raise ValueError('source episode is not in the private research directory')
    receipt = json.loads((source / 'receipt.json').read_text(encoding='utf-8'))
    independent = json.loads((source / 'independent_receipt.json').read_text(encoding='utf-8'))
    raw = source / 'raw.jsonl'
    if (receipt['task'] != TASKS[0] or receipt['raw_sha256'] != sha(raw)
            or receipt['agent_exit'] != 0 or receipt['verifier_exit'] != 0
            or independent['status'] != 'RECORDED'
            or not independent['result']['deleted_exact_including_multiplicity']
            or not independent['result']['changed_fields_exact_including_multiplicity']):
        raise ValueError('source episode or validation is not qualified')
    actions = []
    for line in raw.read_text(encoding='utf-8').splitlines():
        event = json.loads(line)
        part = event.get('part', {})
        state = part.get('state', {})
        if event.get('type') == 'tool_use':
            actions.append({'tool': part.get('tool'), 'status': state.get('status'),
                            'input': state.get('input', {}),
                            'output_tail': str(state.get('output', ''))[-2000:]})
    if not actions:
        raise ValueError('source episode has no recorded actions')
    config_path = FAMILY / TASKS[0] / 'solution/task_config.json'
    task_config = json.loads(config_path.read_text(encoding='utf-8'))
    output_path = source / 'work' / Path(task_config['output_file']).name
    if output_path.is_symlink() or not output_path.is_file():
        raise ValueError('source output missing or is a symlink')
    history = {'source_instruction': (source / 'work/instructions.txt').read_text(encoding='utf-8'),
               'source_actions': actions, 'source_result': json.loads(output_path.read_text(encoding='utf-8')),
               'source_feedback': (source / 'verifier.txt').read_text(encoding='utf-8', errors='replace'),
               'compaction': 'all recorded tool actions; each tool output clipped to its last 2000 characters; source only'}
    encoded = json.dumps(history, ensure_ascii=False, separators=(',', ':'))
    chunks = [encoded[i:i + 700] for i in range(0, len(encoded), 700)]
    readable = ('Source episode history as a losslessly wrapped JSON stream. Each numbered line is a consecutive chunk; '
                'concatenate the text after | in order to reconstruct the exact JSON. The current task may differ.\n'
                + ''.join(f'{i:04d}|{chunk}\n' for i, chunk in enumerate(chunks)))
    if ''.join(line.split('|', 1)[1] for line in readable.splitlines()[1:]) != encoded:
        raise ValueError('source history wrapping is not lossless')
    output.mkdir(parents=True, exist_ok=False)
    (output / 'source_history.json').write_text(json.dumps(history, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (output / 'readable_history.txt').write_text(readable, encoding='utf-8')
    config = {'status': 'SOURCE_ONLY_EXPOSED_DEVELOPMENT', 'source_task': TASKS[0],
              'source_trace_sha256': sha(raw), 'source_receipt_sha256': sha(source / 'receipt.json'),
              'source_feedback_sha256': sha(source / 'verifier.txt'), 'source_output_sha256': sha(output_path),
              'source_independent_receipt_sha256': sha(source / 'independent_receipt.json'),
              'history_sha256': sha(output / 'source_history.json'),
              'readable_history_sha256': sha(output / 'readable_history.txt'),
              'history_scope': history['compaction'], 'target_instruction_or_tests_given_to_model': False,
              'temperature': 0, 'max_tokens': 2500, 'max_http_attempts': 1}
    (output / 'config.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    payload = {'model': 'Qwen3.6-35B-A3B-Q4_K_M.gguf', 'temperature': 0, 'max_tokens': 2500,
               'chat_template_kwargs': {'enable_thinking': False},
               'messages': [{'role': 'system', 'content': 'Create concise reusable instructions from a past tool-using agent episode and its feedback. Separate general steps from task-specific choices; include observed failures and unresolved assumptions. Do not invent results or copy the old answer as a future answer. Return only the skill text.'},
                            {'role': 'user', 'content': encoded}]}
    request_path = output / 'request.json'
    request_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    ledger_path = output / 'ledger.json'
    ledger = {'status': 'ATTEMPT_STARTED', 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'request_sha256': sha(request_path), 'usage': None}
    ledger_path.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
    started = time.monotonic()
    request = urllib.request.Request('http://127.0.0.1:8004/v1/chat/completions', data=request_path.read_bytes(),
                                     headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            raw_response = response.read()
        (output / 'response.json').write_bytes(raw_response)
        response = json.loads(raw_response)
        ledger['usage'] = response.get('usage')
        ledger['response_model'] = response.get('model')
        choice = response['choices'][0]
        ledger['finish_reason'] = choice.get('finish_reason')
        content = choice['message'].get('content') or ''
        if not content.strip():
            raise ValueError('empty source skill')
        (output / 'skill.md').write_text(content, encoding='utf-8')
        ledger.update({'status': 'RECEIVED', 'response_sha256': sha(output / 'response.json'),
                       'skill_sha256': sha(output / 'skill.md')})
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        ledger.update({'status': 'FAILED_USAGE_MAY_BE_UNKNOWN', 'error_type': type(exc).__name__})
    ledger['elapsed_seconds'] = round(time.monotonic() - started, 3)
    ledger_path.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(ledger), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('task', choices=TASKS)
    parser.add_argument('--variant', choices=('normal', 'stale_example'), default='normal')
    parser.add_argument('--condition', choices=('no_history', 'source_history', 'generated_skill'), default='no_history')
    parser.add_argument('--experience', type=Path)
    parser.add_argument('--build-source-experience', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.build_source_experience:
        if args.task != TASKS[0] or args.experience is None:
            parser.error('source experience requires the first task and --experience output')
        build_source_experience(args.build_source_experience, args.experience)
        return
    code, inputs, metadata, history_mount = prepare(args.task, args.variant, args.condition, args.experience)
    print(json.dumps(metadata), flush=True)
    if args.check:
        return
    sys.argv = [str(BASE), args.task, 'no_skill']
    namespace = {'__name__': '__main__', '__file__': str(BASE), 'SKILLFLOW_INPUT': inputs,
                 'SKILLFLOW_HISTORY': history_mount}
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
