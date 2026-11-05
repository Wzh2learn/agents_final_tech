#!/usr/bin/env python3
"""One source-only local-model proposal using the official rendered contract.

This direct-message transport is an adaptation, not the official agent executor
or a complete train/validation/test run. Never use it to modify a frozen target.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
INPUT = ROOT / 'rethinkskill_sphinx_adapter_20261105_v2'
TASK_SHA = '9ea3ad181bf7b6a3e47e33d7637979a66844ad7fd3cf311c13c9f3cdc46e19b8'
POLICY_SHA = 'd91ec94e3f13a324dffd38c0519f84f87d030f7ec9ff6884debc1274e2b9a8e7'
PROBE_SHA = 'a54db66b92ecab0b249901e4ee6aa30f73d21d672d8421ebba12ea13db57002d'
TARGET_MARKERS = ('sphinx-doc__sphinx-8588', '#8588', 'test_TypeAliasNamespace')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--diagnostic-long', action='store_true',
                        help='Separate post-hoc 6000-token output-cap diagnostic; no overwrite')
    mode.add_argument('--constrained', action='store_true',
                      help='Separate 6000-token schema-constrained transport diagnostic')
    args = parser.parse_args()
    out = ROOT / ('rethinkskill_sphinx_direct_candidate_20261105_constrained' if args.constrained else
                 'rethinkskill_sphinx_direct_candidate_20261105_long' if args.diagnostic_long
                  else 'rethinkskill_sphinx_direct_candidate_20261105')
    output_cap = 6000 if args.diagnostic_long or args.constrained else 2500
    if out.exists():
        raise FileExistsError('candidate already attempted; inspect prior ledger')
    task, policy, probe = INPUT / 'task.md', INPUT / 'optimizer_policy.md', INPUT / 'receipt.json'
    if sha(task) != TASK_SHA or sha(policy) != POLICY_SHA or sha(probe) != PROBE_SHA:
        raise ValueError('frozen optimizer source contract changed')
    task_text, policy_text = task.read_text(encoding='utf8'), policy.read_text(encoding='utf8')
    if any(marker.casefold() in (task_text + policy_text).casefold() for marker in TARGET_MARKERS):
        raise ValueError('literal target marker in source-only input')
    payload = {'model': 'Qwen3.6-35B-A3B-Q4_K_M.gguf', 'temperature': 0.2, 'seed': 7201,
               'max_tokens': output_cap, 'chat_template_kwargs': {'enable_thinking': False},
               'messages': [{'role': 'system', 'content': policy_text},
                            {'role': 'user', 'content': task_text}]}
    if args.constrained:
        payload['response_format'] = {'type': 'json_object', 'schema': {
            'type': 'object', 'properties': {
                'operation': {'type': 'string', 'enum': ['add', 'delete', 'replace', 'noop']},
                'candidate_skill': {'type': 'string'}, 'rationale': {'type': 'string'}},
            'required': ['operation', 'candidate_skill', 'rationale'],
            'additionalProperties': False}}
    request_bytes = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf8')
    if len(request_bytes) > 1_000_000:
        raise ValueError('source-only request unexpectedly large')
    out.mkdir()
    request_path = out / 'request.json'
    request_path.write_bytes(request_bytes)
    ledger_path = out / 'ledger.json'
    ledger = {'status': 'ATTEMPT_STARTED', 'physical_http_attempts': 1, 'usage': None,
              'request_sha256': sha(request_path), 'source_task_sha256': TASK_SHA, 'output_cap': output_cap,
              'schema_constrained': args.constrained,
              'scope': 'post-hoc source-only direct-model adaptation; no target execution or validation gate'}
    ledger_path.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf8')
    started = time.monotonic()
    try:
        request = urllib.request.Request('http://127.0.0.1:8004/v1/chat/completions',
            data=request_bytes, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(request, timeout=300) as response:
            raw = response.read()
        raw_path = out / 'response.json'
        raw_path.write_bytes(raw)
        parsed = json.loads(raw)
        text = parsed['choices'][0]['message']['content']
        if not isinstance(text, str):
            raise ValueError('model content is not text')
        (out / 'response.txt').write_text(text, encoding='utf8')
        ledger.update({'status': 'RECEIVED_UNVALIDATED', 'response_sha256': sha(raw_path),
                       'response_text_sha256': sha(out / 'response.txt'), 'usage': parsed.get('usage'),
                       'finish_reason': parsed['choices'][0].get('finish_reason')})
    except Exception as exc:
        ledger.update({'status': 'FAILED_UNKNOWN_USAGE', 'error_type': type(exc).__name__})
        raise
    finally:
        ledger['seconds'] = round(time.monotonic() - started, 3)
        ledger_path.write_text(json.dumps(ledger, indent=2) + '\n', encoding='utf8')
    print(json.dumps(ledger))


if __name__ == '__main__':
    main()
