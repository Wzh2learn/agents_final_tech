#!/usr/bin/env python3
"""Repeat the SymPy target with pinned test dependencies and measured sampling metadata."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sys

import run_swe_sympy_20261104 as sympy_run

common = sympy_run.common
ROOT = common.ROOT / 'swe_sympy_repeat_overlay_20261104_v2'
SOURCE_ROOT = sympy_run.RUNS
CONDITIONS = ('none', 'generated_skill', 'neutral_plan', 'conditioned_plan')
SEEDS = (7101, 7102)
TEMPERATURE = 0.2
MAX_HTTP, MAX_BYTES, MAX_SECONDS = 48, 6000000, 1800

# This exact function is inserted into the isolated proxy and exercised by preflight.
CAPTURE_SOURCE = r'''
def capture_sampling(first, length, recv, temperature, seed):
 header,body=first.split(b'\r\n\r\n',1)
 if length is None or length < 0 or len(body) > length: raise ValueError('invalid content length')
 while len(body)<length:
  chunk=recv(min(65536,length-len(body)))
  if not chunk: raise EOFError('short request body')
  body+=chunk
 payload=json.loads(body.decode('utf-8'))
 if not isinstance(payload,dict): raise ValueError('non-object request')
 before_temperature,before_seed=payload.get('temperature'),payload.get('seed')
 payload['temperature'],payload['seed']=temperature,seed
 body=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf-8')
 lines=header.split(b'\r\n')
 matches=[i for i,line in enumerate(lines) if line.lower().startswith(b'content-length:')]
 if len(matches)!=1: raise ValueError('ambiguous content length')
 lines[matches[0]]=b'Content-Length: '+str(len(body)).encode('ascii')
 keys=('model','temperature','seed','top_p','max_tokens','max_completion_tokens')
 meta={k:payload.get(k) if isinstance(payload.get(k),(str,int,float,type(None))) else None for k in keys}
 meta.update({'temperature_before':before_temperature if isinstance(before_temperature,(int,float,type(None))) else None,
              'seed_before':before_seed if isinstance(before_seed,(int,type(None))) else None,
              'original_length':length,'forwarded_length':len(body)})
 return b'\r\n'.join(lines)+b'\r\n\r\n'+body,meta,len(body)
'''


def preflight() -> None:
    sympy_run.validate()
    sympy_run.validate_hypothesis_overlay()
    ns = {'json': json}
    exec(compile(CAPTURE_SOURCE, '<capture-test>', 'exec'), ns)
    original = {'model': 'local', 'messages': [{'content': 'private prompt 私有内容'}]}
    payload = json.dumps(original, ensure_ascii=False).encode('utf-8')
    chunks = [payload[7:21], payload[21:]]
    first = (b'POST /v1/chat/completions HTTP/1.1\r\nContent-Length: '
             + str(len(payload)).encode('ascii') + b'\r\n\r\n' + payload[:7])
    whole, meta, forwarded = ns['capture_sampling'](first, len(payload), lambda n: chunks.pop(0), TEMPERATURE, 7101)
    headers, body = whole.split(b'\r\n\r\n', 1)
    assert json.loads(body) == {**original, 'temperature': TEMPERATURE, 'seed': 7101} and forwarded == len(body)
    assert b'Content-Length: ' + str(forwarded).encode('ascii') in headers
    assert meta['seed'] == 7101 and meta['temperature'] == TEMPERATURE
    assert meta['seed_before'] is None and meta['temperature_before'] is None
    assert 'messages' not in meta and 'private prompt' not in json.dumps(meta)
    specified = json.dumps({**original, 'temperature': 0.8, 'seed': 42}).encode('utf-8')
    header = b'POST /v1/chat/completions HTTP/1.1\r\nContent-Length: ' + str(len(specified)).encode('ascii')
    changed, meta2, _ = ns['capture_sampling'](header + b'\r\n\r\n' + specified, len(specified),
                                                lambda n: b'', TEMPERATURE, 7101)
    assert meta2['temperature_before'] == 0.8 and meta2['seed_before'] == 42
    assert json.loads(changed.split(b'\r\n\r\n', 1)[1])['temperature'] == TEMPERATURE
    try:
        ns['capture_sampling'](header + b'\r\nContent-Length: 0\r\n\r\n' + specified,
                               len(specified), lambda n: b'', TEMPERATURE, 7101)
    except ValueError:
        pass
    else:
        raise AssertionError('ambiguous content length accepted')
    try:
        ns['capture_sampling'](first, len(payload), lambda n: b'', TEMPERATURE, 7101)
    except EOFError:
        pass
    else:
        raise AssertionError('short request accepted')
    for condition in CONDITIONS:
        make_harness(condition, SEEDS[0], None if condition == 'none' else Path('/tmp/source_experience.md'))
    print(json.dumps({'status': 'READY_NO_MODEL_CALL', 'capture_controls': 'PASS',
                      'overlay_manifest_sha256': sympy_run.HYPOTHESIS_MANIFEST_SHA}))


def make_harness(condition: str, seed: int, experience: Path | None) -> str:
    if condition not in CONDITIONS or seed not in SEEDS:
        raise ValueError('invalid repeat condition or seed')
    code = sympy_run.derive('target', condition, experience)
    code = common.replace_once(code, 'len(calls)>=32', f'len(calls)>={MAX_HTTP}', 2)
    code = common.replace_once(code, 'sum(payload_bytes)+length>4000000',
                               f'sum(payload_bytes)+length>{MAX_BYTES}', 1)
    code = common.replace_once(code, 'stderr=subprocess.PIPE,timeout=1500)',
                               f'stderr=subprocess.PIPE,timeout={MAX_SECONDS})', 1)
    code = common.replace_once(code, 'calls=[]; payload_bytes=[];', 'calls=[]; payload_bytes=[]; sampling=[];', 1)
    code = common.replace_once(code, 'class Handler(socketserver.BaseRequestHandler):',
                               CAPTURE_SOURCE + '\nclass Handler(socketserver.BaseRequestHandler):', 1)
    old = "  if line.startswith(b'POST'):payload_bytes.append(length)"
    new = ("  if line.startswith(b'POST'):\n"
           "   payload_bytes.append(length)\n"
           f"   try:first,meta,forwarded=capture_sampling(first,length,self.request.recv,{TEMPERATURE},{seed})\n"
           "   except (ValueError,EOFError,UnicodeDecodeError):\n"
           "    calls.append('DENIED:invalid_metadata');self.request.sendall("
           "b'HTTP/1.1 400 Bad Request\\r\\nContent-Length: 0\\r\\nConnection: close\\r\\n\\r\\n');return\n"
           "   payload_bytes[-1]=forwarded\n"
           f"   if sum(payload_bytes)>{MAX_BYTES}:\n"
           "    calls.append('DENIED:post_byte_cap_after_override');self.request.sendall("
           "b'HTTP/1.1 403 Forbidden\\r\\nContent-Length: 0\\r\\nConnection: close\\r\\n\\r\\n');return\n"
           "   sampling.append(meta)\n"
           "   with (case/'sampling_metadata.jsonl').open('a',encoding='utf-8') as log:\n"
           "    log.write(json.dumps(meta,separators=(',',':'))+'\\n');log.flush()")
    code = common.replace_once(code, old, new, 1)
    code = common.replace_once(code, "receipt={'task':task", "receipt={'sampling_metadata':sampling,'task':task", 1)
    old = "(work/'opencode.json').write_text(json.dumps(cfg),encoding='utf8')"
    new = (f"cfg['agent']={{'build':{{'temperature':{TEMPERATURE},'seed':{seed}}}}}\n" + old)
    code = common.replace_once(code, old, new, 1)
    old = "'-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1']"
    new = ("'-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1','-e','PYTHONPATH=/extra:/deps',"
           f"'--mount','type=bind,src={sympy_run.HYPOTHESIS_ROOT / 'site'},dst=/extra,readonly']")
    code = common.replace_once(code, old, new, 1)
    compile(code, '<repeat-derived-harness>', 'exec')
    return code


def run_one(condition: str, seed: int) -> None:
    preflight()
    ROOT.mkdir(parents=True, exist_ok=True)
    started = ROOT / f'{condition}__seed_{seed}.started.json'
    completed = ROOT / f'{condition}__seed_{seed}.completed.json'
    failed = ROOT / f'{condition}__seed_{seed}.error.json'
    if started.exists() or completed.exists() or failed.exists():
        raise FileExistsError('repeat already planned; inspect its receipt before retrying')
    expected = {'status': 'STARTED', 'condition': condition, 'seed': seed, 'temperature': TEMPERATURE,
                'max_http': MAX_HTTP, 'max_request_bytes': MAX_BYTES, 'max_wall_seconds': MAX_SECONDS,
                'overlay_manifest_sha256': sympy_run.HYPOTHESIS_MANIFEST_SHA,
                'source_root': str(SOURCE_ROOT), 'scope': 'same target, frozen experience, repaired test environment'}
    started.write_text(json.dumps(expected, indent=2) + '\n', encoding='utf-8')
    common.RUNS, common.SOURCE_RUNS = ROOT, SOURCE_ROOT
    common.MAX_HTTP, common.MAX_REQUEST_BYTES, common.MAX_WALL_SECONDS = MAX_HTTP, MAX_BYTES, MAX_SECONDS
    common.derived_harness = lambda task, c, exp: make_harness(c, seed, exp)
    reservation_path = ROOT / f'target__{condition}__{os.getpid()}.reservation.json'
    try:
        common.run('target', condition)
        reservation = json.loads(reservation_path.read_text(encoding='utf-8'))
        case = Path(reservation['case'])
        receipt = json.loads((case / 'receipt.json').read_text(encoding='utf-8'))
        if reservation['status'] != 'COMPLETED' or receipt['raw_sha256'] != common.sha(case / 'raw.jsonl'):
            raise ValueError('repeat evidence incomplete')
        sampling = receipt['sampling_metadata']
        sampling_log = case / 'sampling_metadata.jsonl'
        persisted = [json.loads(line) for line in sampling_log.read_text(encoding='utf-8').splitlines()]
        norm = lambda rows: Counter(json.dumps(row, sort_keys=True) for row in rows)
        if norm(sampling) != norm(persisted):
            raise ValueError('persisted sampling metadata does not match receipt')
        same_seed = bool(sampling) and all(x.get('seed') == seed for x in sampling)
        same_temperature = bool(sampling) and all(x.get('temperature') == TEMPERATURE for x in sampling)
        expected.update({'status': 'COMPLETED', 'started_sha256': common.sha(started),
                         'case': str(case), 'reservation_sha256': common.sha(reservation_path),
                         'sampling_log_sha256': common.sha(sampling_log),
                         'sampling_requests': len(sampling), 'seed_observed_as_requested': same_seed,
                         'temperature_observed_as_requested': same_temperature})
        completed.write_text(json.dumps(expected, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'case': str(case), 'sampling_requests': len(sampling),
                          'seed_observed_as_requested': same_seed,
                          'temperature_observed_as_requested': same_temperature}))
    except Exception as exc:
        expected.update({'status': 'ERROR', 'started_sha256': common.sha(started),
                         'error_type': type(exc).__name__})
        failed.write_text(json.dumps(expected, indent=2) + '\n', encoding='utf-8')
        raise


def summarize() -> None:
    sympy_run.validate()
    sympy_run.validate_hypothesis_overlay()
    checks = sympy_run.PROBE_ROOT / 'probe.py'
    frozen = json.loads((sympy_run.PROBE_ROOT / 'pre_run_controls.json').read_text(encoding='utf-8'))
    if common.sha(checks) != frozen['probe_sha256']:
        raise ValueError('behavior probe changed')
    out = ROOT / 'verification'
    if out.exists():
        raise FileExistsError('verification already exists')
    out.mkdir()
    rows = []
    for seed in SEEDS:
        for condition in CONDITIONS:
            planned_path = ROOT / f'{condition}__seed_{seed}.completed.json'
            planned = json.loads(planned_path.read_text(encoding='utf-8'))
            started = ROOT / f'{condition}__seed_{seed}.started.json'
            if planned['status'] != 'COMPLETED' or planned['started_sha256'] != common.sha(started):
                raise ValueError('repeat incomplete')
            case = Path(planned['case'])
            reservation_path = ROOT / (case.name + '.reservation.json')
            reservation = json.loads(reservation_path.read_text(encoding='utf-8'))
            receipt_path, score_path = case / 'receipt.json', case / 'benchmark_receipt.json'
            receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
            score = json.loads(score_path.read_text(encoding='utf-8'))
            if (common.sha(reservation_path) != planned['reservation_sha256']
                    or common.sha(receipt_path) != reservation['raw_receipt_sha256']
                    or common.sha(score_path) != reservation['benchmark_receipt_sha256']
                    or common.sha(case / 'raw.jsonl') != receipt['raw_sha256']
                    or common.sha(case / 'sampling_metadata.jsonl') != planned['sampling_log_sha256']
                    or not score['candidate_unchanged']):
                raise ValueError('repeat receipt mismatch')
            for name, expected in score['candidate_artifact_sha256_after'].items():
                artifact = case / 'work' / name
                actual = common.sha(artifact) if artifact.is_file() and not artifact.is_symlink() else None
                if actual != expected:
                    raise ValueError('candidate changed after benchmark')
            label = f'{condition}_{seed}'
            behavior = sympy_run.execute_probe(case / 'work', checks, label, out)
            native = sympy_run.run_native_test(case / 'work', label + '_native', True, out)
            usage, calls = receipt['step_finish_tokens'], receipt['model_http_requests']
            sources = [p for p in SOURCE_ROOT.iterdir() if p.is_dir() and p.name.startswith('source__none__')]
            if len(sources) != 1:
                raise ValueError('expected one source episode')
            source = sources[0]
            evidence = {'generated_skill': source / 'generated_skill.md',
                        'neutral_plan': source / 'target_plans/neutral_plan/plan.md',
                        'conditioned_plan': source / 'target_plans/conditioned_plan/plan.md'}.get(condition)
            if evidence and common.sha(evidence) != reservation['experience_sha256']:
                raise ValueError('repeat experience changed')
            expected_lines = evidence.read_text(encoding='utf-8').splitlines() if evidence else []
            seen, reads = {}, 0
            for line in (case / 'raw.jsonl').read_text(encoding='utf-8').splitlines():
                event = json.loads(line)
                part, state = event.get('part', {}), event.get('part', {}).get('state', {})
                if (evidence and event.get('type') == 'tool_use' and part.get('tool') == 'read'
                        and state.get('input', {}).get('filePath') == '/root/source_experience.md'):
                    reads += 1
                    for entry in str(state.get('output', '')).splitlines():
                        match = re.match(r'^(\d+): ?(.*)$', entry)
                        if match:
                            index = int(match.group(1))
                            if index in seen and seen[index] != match.group(2):
                                raise ValueError('inconsistent experience read')
                            seen[index] = match.group(2)
            exact_read = bool(evidence and len(seen) == len(expected_lines) and all(
                seen.get(i) == expected_lines[i - 1] for i in range(1, len(expected_lines) + 1)))
            rows.append({'condition': condition, 'seed': seed, 'case': case.name,
                         'agent_exit': receipt['agent_exit'], 'benchmark': score['summary'],
                         'benchmark_exit': score['exit'], 'behavior': behavior['result'],
                         'native': native, 'seed_observed_as_requested': planned['seed_observed_as_requested'],
                         'temperature_observed_as_requested': planned['temperature_observed_as_requested'],
                         'http_post': sum(x.startswith('POST ') for x in calls),
                         'denied': [x for x in calls if x.startswith('DENIED')],
                         'reported_tokens': sum(x.get('total', 0) for x in usage),
                         'cache_read_included': sum(x.get('cache', {}).get('read', 0) for x in usage),
                         'elapsed_seconds': receipt['elapsed_seconds'], 'raw_sha256': receipt['raw_sha256'],
                         'experience_reads': reads, 'experience_lines_seen': len(seen),
                         'experience_lines_total': len(expected_lines), 'experience_read_exact': exact_read})
    summary = {'scope': 'SAME_TARGET_FIXED_EXPERIENCE_REPEATS_ADAPTED_ENVIRONMENT', 'cases': rows,
               'http_post': sum(row['http_post'] for row in rows),
               'reported_tokens': sum(row['reported_tokens'] for row in rows),
               'cache_read_included': sum(row['cache_read_included'] for row in rows),
               'overlay_manifest_sha256': sympy_run.HYPOTHESIS_MANIFEST_SHA,
               'behavior_probe_sha256': common.sha(checks)}
    path = out / 'summary.json'
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'summary': str(path), 'sha256': common.sha(path), 'result': summary}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--condition', choices=CONDITIONS)
    parser.add_argument('--seed', type=int, choices=SEEDS)
    parser.add_argument('--summarize', action='store_true')
    args = parser.parse_args()
    if args.preflight:
        preflight()
    elif args.summarize:
        summarize()
    elif args.condition and args.seed:
        run_one(args.condition, args.seed)
    else:
        parser.error('select --preflight, --summarize, or a condition and seed')
