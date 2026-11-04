#!/usr/bin/env python3
"""Derive source-only history and one local skill from a real stock episode."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def make_history(source: Path) -> tuple[dict, dict]:
    receipt = json.loads((source / 'receipt.json').read_text(encoding='utf-8'))
    raw = source / 'raw.jsonl'
    if receipt['task'] != 'stock-data-visualization-1' or receipt['raw_sha256'] != sha(raw):
        raise ValueError('not the frozen source task or the raw trace changed')
    actions = []
    errors = []
    for line in raw.read_text(encoding='utf-8').splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            errors.append('UNPARSEABLE_RAW_LINE')
            continue
        part = event.get('part', {})
        state = part.get('state', {})
        if event.get('type') == 'error':
            errors.append(event.get('error', {}).get('name', 'UNKNOWN'))
        if event.get('type') == 'tool_use':
            actions.append({'tool': part.get('tool'), 'status': state.get('status'),
                            'input': json.dumps(state.get('input', {}), ensure_ascii=False)[:1400],
                            'output_tail': str(state.get('output', ''))[-500:]})
    output = source / 'work/output'
    generated = {}
    for relative in ('index.html', 'js/visualization.js', 'css/style.css'):
        path = output / relative
        if path.is_file() and not path.is_symlink():
            generated[relative] = path.read_text(encoding='utf-8', errors='replace')[:24000]
    if not actions:
        raise ValueError('source has no recorded tool actions')
    history = {'source_instruction': (source / 'work/instructions.txt').read_text(encoding='utf-8'),
               'source_generated_files': generated, 'source_actions': actions[-15:], 'source_errors': errors,
               'source_feedback': {'agent_exit': receipt['agent_exit'], 'upstream_verifier_exit': receipt['verifier_exit'],
                                   'verifier_output_tail': (source / 'verifier.txt').read_text(encoding='utf-8', errors='replace')[-4000:]},
               'compaction': 'last 15 source actions, clipped inputs/outputs and up to 24000 chars per generated file; no target task or target verifier'}
    config = {'status': 'EXPOSED_DEVELOPMENT_SOURCE_ONLY', 'source_task': 1, 'source_trace_sha256': sha(raw),
              'source_receipt_sha256': sha(source / 'receipt.json'),
              'source_instruction_sha256': sha(source / 'work/instructions.txt'),
              'generated_file_hashes': {name: sha(output / name) for name in generated},
              'target_task_or_reference_seen_by_author': False,
              'max_tokens': 2500, 'temperature': 0, 'max_http_attempts': 1}
    return history, config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    history, config = make_history(source)
    args.output.mkdir(parents=True, exist_ok=False)
    history_path = args.output / 'source_history.json'
    write_json(history_path, history)
    config['source_history_sha256'] = sha(history_path)
    write_json(args.output / 'config.json', config)
    payload = {'model': 'Qwen3.6-35B-A3B-Q4_K_M.gguf', 'temperature': 0, 'max_tokens': 2500,
               'chat_template_kwargs': {'enable_thinking': False},
               'messages': [{'role': 'system', 'content': 'Create concise, reusable instructions from a past tool-using agent episode and its feedback. Separate general steps from task-specific choices; include observed failures and unresolved assumptions. Do not invent results or copy the old answer as a future answer. Return only the skill text.'},
                            {'role': 'user', 'content': json.dumps(history, ensure_ascii=False)}]}
    request_file = args.output / 'request.json'
    request_file.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    event = {'status': 'ATTEMPT_STARTED', 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'request_sha256': sha(request_file), 'usage': None}
    ledger = args.output / 'ledger.json'
    write_json(ledger, event)
    start = time.monotonic()
    request = urllib.request.Request('http://127.0.0.1:8004/v1/chat/completions',
                                     data=request_file.read_bytes(), headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            response_bytes = response.read()
        response_path = args.output / 'response.json'
        response_path.write_bytes(response_bytes)
        result = json.loads(response_bytes)
        event['usage'] = result.get('usage')
        event['response_model'] = result.get('model')
        choice = result['choices'][0]
        event['finish_reason'] = choice.get('finish_reason')
        text = choice['message'].get('content') or ''
        if not text.strip():
            raise ValueError('empty model content')
        skill = args.output / 'skill.md'
        skill.write_text(text, encoding='utf-8')
        event.update({'status': 'RECEIVED', 'response_sha256': sha(response_path), 'skill_sha256': sha(skill)})
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        event.update({'status': 'FAILED_USAGE_MAY_BE_UNKNOWN', 'error_type': type(exc).__name__})
    event['elapsed_seconds'] = round(time.monotonic() - start, 3)
    write_json(ledger, event)
    print(json.dumps(event), flush=True)


if __name__ == '__main__':
    main()
