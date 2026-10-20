#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''TQ chain runner (TQ-4 / TQ-5): schedule-driven, budgeted, resumable (authorized bounded chain 2026-10-16).

Reuses the proven TQ-3 bounded mechanics (ledger-before-send, reserve/settle, aux token counting,
isolation, crash resume, raw capture) and adds:
- config-driven step schedules (frozen per panel; actor / b / c steps; candidate sources for part 2)
- dual ledger (per-run + chain master mirror)
- v2 evidence schema prompts (templates v2), strict payload stripping for candidates
- per-run caps plus recording for chain totals (per-run caps imply chain bounds: 40/4/400k each)

Stdlib only. No HTTP besides http://127.0.0.1:8004. Run with --config <chain_config.json>.
'''
import argparse
import datetime as dt
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path

BASE = 'http://127.0.0.1:8004'
MODEL_ID = 'Qwen3.6-35B-A3B-Q4_K_M.gguf'
MODEL_PATH = '/home/testuser/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-GGUF/Qwen3.6-35B-A3B-Q4_K_M.gguf'
SERVER_BIN = '/home/testuser/.lmstudio/extensions/backends/llama.cpp-linux-arm64-nvidia-cuda13-2.16.0/llama-server'
MODEL_SHA_EXPECTED = '4ac6a06bce551257267f49ad2226f8671a22519ccc1a4dde9d5b433d1f2a410d'
SERVER_SHA_EXPECTED = '037e02419e78256ed4227af31fc0b2602ff04c670fb7ad4fa2429fafb03bd55d'
REQUEST_PARAMS = {
    'temperature': 0,
    'top_p': 1,
    'seed': 20261016,
    'max_tokens': 2048,
    'stream': False,
    'response_format': {'type': 'json_object'},
    'chat_template_kwargs': {'enable_thinking': False},
}
PROMPT_TOKEN_CAP = 8192
GEN_TOKEN_CAP = 2048
RESERVE_TOKENS = 10240
TOTAL_TOKEN_CAP = 400000
GEN_REQUEST_CAP = 40
RETRY_CAP = 4
REQUEST_TIMEOUT_S = 120
WINDOW_CAP_MIN = 90
UTC = dt.timezone.utc
TZ8 = dt.timezone(dt.timedelta(hours=8))
CRLF = bytes([13, 10])
LF = bytes([10])



def now_utc():
    return dt.datetime.now(UTC)




def iso(t=None):
    return (t or now_utc()).strftime('%Y-%m-%dT%H:%M:%SZ')




def beijing(t=None):
    return (t or now_utc()).astimezone(TZ8)




def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()




def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            block = f.read(1 << 20)
            if not block:
                break
            h.update(block)
    return h.hexdigest()




def lf_norm(b):
    return b.replace(CRLF, LF)




def crlf_norm(b):
    return lf_norm(b).replace(LF, CRLF)




def seamash_expected(expected, data):
    if sha256_bytes(data) == expected:
        return 'raw'
    if sha256_bytes(lf_norm(data)) == expected:
        return 'lf'
    if sha256_bytes(crlf_norm(data)) == expected:
        return 'crlf'
    return None




def write_json(path, obj):
    path = Path(path)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')
    os.replace(str(tmp), str(path))




def append_jsonl(path, obj):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + chr(10))
        f.flush()
        os.fsync(f.fileno())




def parse_templates(templates_md):
    text = Path(templates_md).read_text(encoding='utf-8-sig')
    lines = text.split(chr(10))
    marks = ['## 1. actor template', '## 2. B checker template', '## 3. C checker template', '## 4. Substitution']
    idx = []
    for m in marks:
        hit = None
        for i, l in enumerate(lines):
            if l.startswith(m):
                hit = i
                break
        if hit is None:
            raise ValueError('template marker missing: ' + m)
        idx.append(hit)

    def block(a, b):
        chunk = lines[a + 1:b]
        sys_i = None
        usr_i = None
        for i, l in enumerate(chunk):
            if l.strip() == 'System prompt (fixed):' and sys_i is None:
                sys_i = i
            elif l.strip() == 'User prompt:' and usr_i is None:
                usr_i = i
        if sys_i is None or usr_i is None or usr_i <= sys_i:
            raise ValueError('prompt markers missing in section')
        system = chr(10).join(chunk[sys_i + 1:usr_i]).strip()
        user = chr(10).join(chunk[usr_i + 1:]).strip()
        return system, user

    a_sys, a_usr = block(idx[0], idx[1])
    b_sys, b_usr = block(idx[1], idx[2])
    c_sys, c_usr = block(idx[2], idx[3])
    return {'a': (a_sys, a_usr), 'b': (b_sys, b_usr), 'c': (c_sys, c_usr)}




def _table_json(rec):
    return json.dumps(rec['table'], ensure_ascii=False, separators=(',', ':'))




def _para_json(rec):
    return json.dumps(rec['paragraphs'], ensure_ascii=False, separators=(',', ':'))




def render_actor(tpl, case, rec):
    system, user = tpl['a']
    u = (user.replace('{question}', rec['question'])
             .replace('{table_json}', _table_json(rec))
             .replace('{paragraphs_json}', _para_json(rec))
             .replace('{task_id}', case))
    return [{'role': 'system', 'content': system}, {'role': 'user', 'content': u}]




def render_b(tpl, rec, actor_obj):
    system, user = tpl['b']
    out_json = json.dumps(actor_obj, ensure_ascii=False, separators=(',', ':'))
    u = (user.replace('{question}', rec['question'])
             .replace('{table_json}', _table_json(rec))
             .replace('{paragraphs_json}', _para_json(rec))
             .replace('{actor_output_json}', out_json))
    return [{'role': 'system', 'content': system}, {'role': 'user', 'content': u}]




def render_c(tpl, rec, actor_obj):
    system, user = tpl['c']
    ans = actor_obj.get('answer')
    cand = ans if isinstance(ans, str) else json.dumps(ans, ensure_ascii=False, separators=(',', ':'))
    u = (user.replace('{question}', rec['question'])
             .replace('{table_json}', _table_json(rec))
             .replace('{paragraphs_json}', _para_json(rec))
             .replace('{candidate_answer_only}', cand))
    return [{'role': 'system', 'content': system}, {'role': 'user', 'content': u}]




def http_request(url, payload=None, timeout=30):
    t0 = time.time()
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, headers=headers)
    res = {'url': url, 'ok': False, 'status': None, 'kind': None, 'elapsed_s': None, 'body': None}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            res.update({'ok': True, 'status': r.status, 'body': body.decode('utf-8', 'replace'),
                        'content_type': r.headers.get('Content-Type'), 'date': r.headers.get('Date')})
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b''
        res.update({'status': e.code, 'body': body.decode('utf-8', 'replace'),
                    'kind': 'http_4xx' if 400 <= e.code < 500 else 'http_5xx'})
    except Exception as e:
        reason = getattr(e, 'reason', None)
        is_timeout = isinstance(e, (TimeoutError, socket.timeout)) or isinstance(reason, (TimeoutError, socket.timeout)) or 'timed out' in str(e).lower()
        res.update({'kind': 'timeout' if is_timeout else 'connect_error', 'error': type(e).__name__ + ': ' + str(e)[:400]})
    res['elapsed_s'] = round(time.time() - t0, 3)
    return res




class Ledger:
    def __init__(self, path):
        self.path = Path(path)
        self.entries = []
        if self.path.exists():
            for line in self.path.read_text(encoding='utf-8').splitlines():
                if line.strip():
                    self.entries.append(json.loads(line))

    def append(self, obj):
        obj = dict(obj)
        obj.setdefault('utc', iso())
        append_jsonl(self.path, obj)
        self.entries.append(obj)

    def gen_attempts(self):
        return sum(1 for e in self.entries if e.get('op') == 'reserve')

    def item_attempts(self, key):
        return sum(1 for e in self.entries if e.get('op') == 'reserve' and e.get('item_key') == key)

    def retries_used(self):
        return sum(1 for e in self.entries if e.get('op') == 'reserve' and e.get('retry'))

    def unsettled_tokens(self):
        total = 0
        for e in self.entries:
            if e.get('op') == 'reserve':
                total += int(e.get('reserved', 0))
            elif e.get('op') == 'settle':
                total -= int(e.get('freed', 0))
        return total

    def settled_tokens(self):
        return sum(int(e.get('settled', 0)) for e in self.entries if e.get('op') == 'settle')

    def item_state(self, key):
        settles = [e for e in self.entries if e.get('op') == 'settle' and e.get('item_key') == key]
        reserves = [e for e in self.entries if e.get('op') == 'reserve' and e.get('item_key') == key]
        refusals = [e for e in self.entries if e.get('op') == 'refuse' and e.get('item_key') == key]
        if any(e.get('ok') for e in settles):
            return 'done'
        if reserves and len(settles) < len(reserves):
            return 'inflight'
        if settles:
            return 'failed'
        if refusals:
            return 'refused'
        return 'pending'

    def last_seq(self, key):
        seqs = [int(e.get('seq', 0)) for e in self.entries if e.get('op') == 'reserve' and e.get('item_key') == key]
        return max(seqs) if seqs else None




class Aux:
    def __init__(self, path):
        self.path = Path(path)
        self.entries = []
        if self.path.exists():
            for line in self.path.read_text(encoding='utf-8').splitlines():
                if line.strip():
                    self.entries.append(json.loads(line))
        self.next_id = sum(1 for e in self.entries if e.get('op') == 'aux_send') + 1

    def append(self, obj):
        obj = dict(obj)
        obj.setdefault('utc', iso())
        append_jsonl(self.path, obj)
        self.entries.append(obj)

    def used(self, typ, key):
        return sum(1 for e in self.entries if e.get('op') == 'aux_send' and e.get('type') == typ and e.get('item_key') == key)




def window_stop_reason(ctx):
    now = now_utc()
    if ctx['first_request_utc'] is None:
        bj = beijing(now)
        if bj.strftime('%Y-%m-%d') not in tuple(ctx.get('allowed_dates') or []):
            return 'OUTSIDE_ALLOWED_DATES'
        hm = bj.hour * 60 + bj.minute
        if hm < 540 or hm > 1110:
            return 'OUTSIDE_START_WINDOW'
    else:
        if now - ctx['first_request_utc'] > dt.timedelta(minutes=WINDOW_CAP_MIN):
            return 'WINDOW_90MIN_EXCEEDED'
    if beijing(now).hour >= 20:
        return 'AFTER_2000_BEIJING'
    return None




def aux_count_prompt(ctx, item, messages):
    key = item['key']
    aux = ctx['aux']
    rendered = None
    count = None
    method = 'byte-bound'
    if ctx['aux_flags']['apply'] and aux.used('apply-template', key) < 1:
        aux_id = aux.next_id
        aux.next_id += 1
        aux.append({'op': 'aux_send', 'aux_id': aux_id, 'type': 'apply-template', 'item_key': key})
        res = http_request(BASE + '/apply-template', {'messages': messages, 'chat_template_kwargs': REQUEST_PARAMS['chat_template_kwargs']}, timeout=30)
        ok = False
        if res.get('ok'):
            try:
                j = json.loads(res['body'])
                if isinstance(j.get('prompt'), str) and j['prompt']:
                    rendered = j['prompt']
                    ok = True
            except Exception:
                ok = False
        if not ok:
            ctx['aux_flags']['apply'] = False
        aux.append({'op': 'aux_done', 'aux_id': aux_id, 'type': 'apply-template', 'item_key': key, 'status': res.get('status'), 'ok': ok})
    if rendered is not None and ctx['aux_flags']['tokenize'] and aux.used('tokenize', key) < 1:
        aux_id = aux.next_id
        aux.next_id += 1
        aux.append({'op': 'aux_send', 'aux_id': aux_id, 'type': 'tokenize', 'item_key': key})
        res = http_request(BASE + '/tokenize', {'content': rendered}, timeout=30)
        ok = False
        if res.get('ok'):
            try:
                j = json.loads(res['body'])
                toks = j.get('tokens')
                if isinstance(toks, list) and toks:
                    count = len(toks)
                    method = 'apply-template+tokenize'
                    ok = True
            except Exception:
                ok = False
        if not ok:
            ctx['aux_flags']['tokenize'] = False
        aux.append({'op': 'aux_done', 'aux_id': aux_id, 'type': 'tokenize', 'item_key': key, 'status': res.get('status'), 'ok': ok, 'tokens': count})
    if count is None:
        joined = messages[0]['content'] + chr(10) + messages[1]['content']
        count = len(joined.encode('utf-8')) + 512
        method = 'byte-bound-plus-512'
    return {'count': count, 'method': method, 'rendered_prompt': rendered}




def attempt_generation(item, messages, ctx):
    ledger = ctx['ledger']
    key = item['key']
    retry = ledger.item_attempts(key) > 0
    if ledger.gen_attempts() + 1 > GEN_REQUEST_CAP:
        ledger.append({'op': 'refuse', 'item_key': key, 'reason': 'GEN_REQUEST_CAP'})
        return {'outcome': 'refused', 'kind': 'GEN_REQUEST_CAP'}
    if ledger.unsettled_tokens() + RESERVE_TOKENS > TOTAL_TOKEN_CAP:
        ledger.append({'op': 'refuse', 'item_key': key, 'reason': 'TOKEN_CAP'})
        return {'outcome': 'refused', 'kind': 'TOKEN_CAP'}
    if retry and ledger.retries_used() >= RETRY_CAP:
        ledger.append({'op': 'refuse', 'item_key': key, 'reason': 'RETRY_CAP'})
        return {'outcome': 'refused', 'kind': 'RETRY_CAP'}
    w = window_stop_reason(ctx)
    if w:
        ledger.append({'op': 'refuse', 'item_key': key, 'reason': w})
        return {'outcome': 'stopped', 'kind': w}
    cc = aux_count_prompt(ctx, item, messages)
    if cc['count'] > PROMPT_TOKEN_CAP:
        ledger.append({'op': 'refuse', 'item_key': key, 'reason': 'PROMPT_TOKEN_CAP', 'count': cc['count'], 'method': cc['method']})
        return {'outcome': 'refused', 'kind': 'PROMPT_TOKEN_CAP'}
    seq = ledger.gen_attempts() + 1
    ledger.append({'op': 'reserve', 'seq': seq, 'item_key': key, 'retry': bool(retry), 'reserved': RESERVE_TOKENS, 'prompt_count': cc['count'], 'count_method': cc['method']})
    if ctx['first_request_utc'] is None:
        ctx['first_request_utc'] = now_utc()
        ctx['u']['first_request_utc'] = iso(ctx['first_request_utc'])
    rendered = cc['rendered_prompt']
    pf = ctx['run_dir'] / 'prompts' / (str(seq).zfill(4) + '_' + key.replace('|', '_') + '.json')
    write_json(pf, {'seq': seq, 'item_key': key, 'messages': messages,
                    'messages_sha256': sha256_bytes(json.dumps(messages, ensure_ascii=False, separators=(',', ':')).encode('utf-8')),
                    'apply_template_prompt': rendered,
                    'apply_template_prompt_sha256': sha256_bytes(rendered.encode('utf-8')) if rendered else None,
                    'prompt_count': cc['count'], 'count_method': cc['method']})
    payload = {'model': MODEL_ID, 'messages': messages}
    payload.update(REQUEST_PARAMS)
    res = http_request(BASE + '/v1/chat/completions', payload, timeout=REQUEST_TIMEOUT_S)
    usage = None
    if res.get('ok') and res.get('body'):
        try:
            j = json.loads(res['body'])
            if isinstance(j.get('usage'), dict):
                usage = j['usage']
        except Exception:
            usage = None
    settled = 0
    freed = 0
    if usage is not None:
        tt = usage.get('total_tokens')
        if isinstance(tt, int) and 0 <= tt <= RESERVE_TOKENS:
            settled = tt
            freed = RESERVE_TOKENS - settled
    ledger.append({'op': 'settle', 'seq': seq, 'item_key': key, 'ok': bool(res.get('ok')), 'kind': res.get('kind') or 'ok', 'status': res.get('status'), 'settled': settled, 'freed': freed, 'usage': usage})
    print(json.dumps({'t': iso(), 'seq': seq, 'item': key, 'ok': bool(res.get('ok')), 'kind': res.get('kind') or 'ok', 'gen': ledger.gen_attempts(), 'settled': ledger.settled_tokens()}, ensure_ascii=True), flush=True)
    return {'outcome': 'sent', 'seq': seq, 'res': res, 'usage': usage, 'settled': settled}




def extract_completion_text(res):
    if not res.get('ok') or not res.get('body'):
        return None, 'no_response_body'
    try:
        j = json.loads(res['body'])
    except Exception as e:
        return None, 'response_body_not_json: ' + str(e)[:200]
    try:
        ch = j.get('choices')
        msg = ch[0].get('message') or {}
        content = msg.get('content')
        if isinstance(content, str):
            return content, None
        return None, 'no_content_string'
    except Exception as e:
        return None, 'choices_parse_error: ' + str(e)[:200]




def parse_actor_text(text):
    try:
        obj = json.loads(text)
    except Exception:
        return None, False, 'json_parse_error'
    if not isinstance(obj, dict):
        return None, False, 'not_object'
    ans = obj.get('answer')
    if ans is None or (isinstance(ans, str) and ans.strip() == ''):
        return obj, False, 'missing_or_empty_answer'
    return obj, True, None




def parse_decision_text(text):
    try:
        obj = json.loads(text)
    except Exception:
        return None, 'json_parse_error'
    if not isinstance(obj, dict):
        return None, 'not_object'
    d = obj.get('decision')
    if d not in ('accept', 'alarm', 'abstain'):
        return None, 'invalid_decision'
    return obj, None




def save_raw(ctx, item, out, attempt_retry, parse_info):
    seq = out['seq']
    res = out['res']
    raw = {'seq': seq, 'item_key': item['key'], 'arm': item['arm'], 'case': item['case'], 'variant': item['variant'],
           'retry': bool(attempt_retry), 'utc': iso(),
           'request': {'url': BASE + '/v1/chat/completions', 'model': MODEL_ID, 'params': REQUEST_PARAMS},
           'http': {'ok': bool(res.get('ok')), 'status': res.get('status'), 'kind': res.get('kind'), 'elapsed_s': res.get('elapsed_s'), 'body_text': res.get('body'), 'error': res.get('error')},
           'usage': out.get('usage'), 'parse': parse_info}
    fn = str(seq).zfill(4) + '_' + item['arm'] + '_' + item['case'] + '_' + item['variant'] + '.json'
    write_json(ctx['run_dir'] / 'raw' / fn, raw)
    return fn




def run_item_loop(item, messages, ctx):
    ledger = ctx['ledger']
    while True:
        attempts = ledger.item_attempts(item['key'])
        out = attempt_generation(item, messages, ctx)
        if out['outcome'] != 'sent':
            return out
        res = out['res']
        text, terr = extract_completion_text(res)
        store = {'result': None, 'valid': False, 'error': terr}
        if text is not None:
            if item['arm'] == 'actor':
                obj, valid, err = parse_actor_text(text)
                store = {'result': obj, 'valid': bool(valid), 'error': err}
            else:
                obj, err = parse_decision_text(text)
                store = {'result': obj, 'valid': obj is not None, 'error': err}
        fn = save_raw(ctx, item, out, attempts > 0, store)
        if res.get('ok'):
            return {'outcome': 'ok', 'res': res, 'seq': out['seq'], 'raw_file': fn, 'parse': store}
        kind = res.get('kind')
        retryable = kind in ('http_5xx', 'timeout', 'connect_error')
        if retryable and ledger.retries_used() < RETRY_CAP and attempts < 3:
            continue
        return {'outcome': 'failed', 'kind': kind, 'res': res, 'seq': out['seq'], 'raw_file': fn, 'parse': store}




def process_item(item, messages, ctx, state_store, streak):
    outcome = run_item_loop(item, messages, ctx)
    kind = outcome.get('kind')
    if outcome['outcome'] == 'stopped':
        state_store[item['key']] = {'status': 'not_run'}
        return ('stop', kind)
    if outcome['outcome'] == 'refused':
        if kind in ('GEN_REQUEST_CAP', 'TOKEN_CAP', 'RETRY_CAP'):
            state_store[item['key']] = {'status': 'not_run'}
            return ('stop', kind)
        state_store[item['key']] = {'status': 'refused_other'}
        return ('continue', None)
    if outcome['outcome'] == 'ok':
        streak['n'] = 0
        parse = outcome['parse']
        state_store[item['key']] = {'status': 'valid' if parse['valid'] else 'invalid', 'obj': parse['result'] if parse['valid'] else None}
        return ('continue', None)
    if kind == 'http_4xx' and ctx['ledger'].gen_attempts() == 1:
        state_store[item['key']] = {'status': 'failed'}
        return ('stop', 'FIRST_REQUEST_REJECTED_HTTP_4XX')
    if kind == 'connect_error':
        streak['n'] += 1
        if streak['n'] >= 2:
            state_store[item['key']] = {'status': 'failed'}
            return ('stop', 'CONSECUTIVE_CONNECT_FAILURES')
    else:
        streak['n'] = 0
    state_store[item['key']] = {'status': 'failed'}
    return ('continue', None)




def load_actor_from_raw(run_dir, ledger, key):
    seq = ledger.last_seq(key)
    if seq is None:
        return None, False
    prefix = str(seq).zfill(4) + '_'
    for p in sorted((run_dir / 'raw').glob(prefix + '*.json')):
        try:
            j = json.loads(p.read_text(encoding='utf-8-sig'))
        except Exception:
            return None, False
        parse = j.get('parse') or {}
        if parse.get('valid') and isinstance(parse.get('result'), dict):
            return parse['result'], True
        return None, False
    return None, False




def capture_model_pin(run_dir, aux):
    info = {'schema': 'tq3_model_pin_v1', 'model_id': MODEL_ID, 'base_url': BASE, 'generated_utc': iso()}
    r = http_request(BASE + '/v1/models', timeout=30)
    info['models_ok'] = bool(r.get('ok'))
    ids = []
    if r.get('ok') and r.get('body'):
        try:
            j = json.loads(r['body'])
            for m in j.get('data', []):
                ids.append(m.get('id'))
        except Exception:
            pass
    info['models_ids'] = ids
    aux.append({'op': 'aux_done', 'type': 'service-meta', 'status': r.get('status'), 'ok': bool(r.get('ok'))})
    r2 = http_request(BASE + '/props', timeout=30)
    info['props_ok'] = bool(r2.get('ok'))
    if r2.get('ok') and r2.get('body'):
        write_json(run_dir / 'service_props.json', {'body_text': r2['body']})
        try:
            p = json.loads(r2['body'])
            info['props_model_path'] = p.get('model_path')
            ct = p.get('chat_template')
            if isinstance(ct, str):
                info['chat_template_sha256'] = sha256_bytes(ct.encode('utf-8'))
                info['chat_template_len'] = len(ct)
            dgs = p.get('default_generation_settings') or {}
            info['props_n_ctx'] = dgs.get('n_ctx') if isinstance(dgs, dict) else None
            info['props_total_slots'] = p.get('total_slots')
        except Exception as e:
            info['props_parse_error'] = str(e)[:200]
    t0 = time.time()
    model_sha = None
    if Path(MODEL_PATH).exists():
        try:
            pr = subprocess.run(['sha256sum', MODEL_PATH], capture_output=True, text=True, timeout=1800)
            if pr.returncode == 0 and pr.stdout:
                model_sha = pr.stdout.split()[0]
        except Exception:
            model_sha = None
    info['model_file_sha256'] = model_sha
    info['model_sha256_expected'] = MODEL_SHA_EXPECTED
    server_sha = None
    if Path(SERVER_BIN).exists():
        try:
            pr2 = subprocess.run(['sha256sum', SERVER_BIN], capture_output=True, text=True, timeout=1800)
            if pr2.returncode == 0 and pr2.stdout:
                server_sha = pr2.stdout.split()[0]
        except Exception:
            server_sha = None
    info['server_bin_sha256'] = server_sha
    info['server_sha256_expected'] = SERVER_SHA_EXPECTED
    info['hash_elapsed_s'] = round(time.time() - t0, 1)
    info['identity_ok'] = bool(model_sha == MODEL_SHA_EXPECTED and server_sha == SERVER_SHA_EXPECTED and MODEL_ID in ids and info.get('props_model_path') == MODEL_PATH)
    return info




class DualLedger(Ledger):
    '''Per-run ledger + chain master mirror (master entries carry panel/run meta).'''

    def __init__(self, path, master_path, meta):
        super().__init__(path)
        self.master_path = Path(master_path)
        self.meta = dict(meta)

    def append(self, obj):
        super().append(obj)
        m = dict(obj)
        m.update(self.meta)
        append_jsonl(self.master_path, m)


def load_config(path, root_override=None):
    cfg = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    root = Path(root_override) if root_override else Path(cfg['root'])
    cfg['_config_path'] = str(Path(path).resolve())
    cfg['_root'] = root
    cfg['_templates'] = root / cfg['templates_md']
    cfg['_manifest'] = root / cfg['material_manifest']
    cfg['_lf_pins'] = root / cfg['material_pins_lf']
    cfg['_out_root'] = root / cfg['out_root']
    cfg['_master'] = root / cfg['master_ledger']
    return cfg


def check_material_pins(cfg):
    m = json.loads(cfg['_manifest'].read_text(encoding='utf-8-sig'))
    lf = {}
    if cfg['_lf_pins'].exists():
        lf = json.loads(cfg['_lf_pins'].read_text(encoding='utf-8-sig')).get('files', {})
    bad = []
    unreadable = []
    channels = {}
    root = cfg['_root']
    for f in m.get('files', []):
        p = root / f['path']
        if not p.exists():
            bad.append({'path': f['path'], 'error': 'missing'})
            continue
        try:
            data = p.read_bytes()
        except Exception as e:
            unreadable.append({'path': f['path'], 'error': str(e)[:120]})
            continue
        raw = sha256_bytes(data)
        exp = f['sha256']
        lf_exp = lf.get(f['path'])
        if raw == exp:
            ch = 'raw'
        elif lf_exp is not None and raw == lf_exp:
            ch = 'lf-caliber'
        elif sha256_bytes(lf_norm(data)) == exp:
            ch = 'lf-norm'
        elif sha256_bytes(crlf_norm(data)) == exp:
            ch = 'crlf-norm'
        elif lf_exp is not None and sha256_bytes(lf_norm(data)) == lf_exp:
            ch = 'lf-caliber-normalised'
        else:
            ch = None
        if ch is None:
            bad.append({'path': f['path'], 'expected_raw': exp, 'expected_lf_caliber': lf_exp, 'actual_raw': raw})
        else:
            channels[ch] = channels.get(ch, 0) + 1
    return {'checked': len(m.get('files', [])), 'mismatches': bad, 'unreadable': unreadable,
            'channels': channels, 'lf_caliber_available': bool(lf), 'ok': (not bad and not unreadable)}


def strip_candidate(c):
    return {'task_id': c['task_id'], 'answer': c['answer'], 'evidence': c['evidence']}


def build_step_item(step):
    return {'key': step['key'], 'arm': step['kind'], 'case': step['task_id'], 'variant': step.get('variant', 'perturbed')}


def get_source_obj(ctx, step):
    if step.get('source') == 'candidate':
        c = ctx['candidates'].get(step.get('candidate_id'))
        if not c:
            return None, 'CANDIDATE_MISSING'
        return strip_candidate(c), None
    sk = step.get('source_key')
    state = ctx['state'].get(sk)
    if state and state.get('status') == 'valid' and state.get('obj'):
        return state['obj'], None
    obj, valid = load_actor_from_raw(ctx['run_dir'], ctx['ledger'], sk)
    if valid:
        return obj, None
    return None, 'BLOCKED_NO_VALID_ACTOR'


def load_run_jsonl(path):
    out = {}
    p = Path(path)
    if p.exists():
        for line in p.read_text(encoding='utf-8').splitlines():
            if line.strip():
                j = json.loads(line)
                out[j.get('item_key')] = j
    return out


def cmd_run(cfg, resume_id=None):
    out_root = cfg['_out_root']
    out_root.mkdir(parents=True, exist_ok=True)
    cfg['_master'].parent.mkdir(parents=True, exist_ok=True)
    if resume_id:
        run_dir = out_root / resume_id
        if not run_dir.exists():
            print('run dir not found: ' + str(run_dir))
            return 2
    else:
        rid = now_utc().strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]
        run_dir = out_root / rid
        if run_dir.exists():
            print('run dir already exists: ' + str(run_dir))
            return 2
        (run_dir / 'raw').mkdir(parents=True)
        (run_dir / 'prompts').mkdir()
    auth_path = cfg.get('authorization_file')
    auth = None
    if auth_path:
        cand = Path(auth_path)
        auth = cand if cand.exists() else (cfg['_root'] / auth_path)
    auth_sha = sha256_file(auth) if auth is not None and auth.exists() else None
    meta = {'schema': 'tq_chain_run_meta_v1', 'run_id': run_dir.name, 'panel': cfg['panel_id'], 'created_utc': iso(),
            'config_sha256': sha256_file(cfg['_config_path']), 'runner_sha256': sha256_file(Path(__file__).resolve()),
            'templates_md_sha256': sha256_file(cfg['_templates']), 'authorization_sha256': auth_sha,
            'authorization_file_resolved': str(auth) if auth is not None else None,
            'request_params': REQUEST_PARAMS, 'base_url': BASE, 'model_id': MODEL_ID,
            'steps_total': len(cfg['steps']), 'resumed': bool(resume_id)}
    write_json(run_dir / 'RUN_META.json', meta)
    pc = check_material_pins(cfg)
    write_json(run_dir / 'PIN_CHECK_BEFORE.json', pc)
    if not pc['ok']:
        write_json(run_dir / 'RECEIPT.json', {'schema': 'tq_chain_receipt_v1', 'run_id': run_dir.name, 'panel': cfg['panel_id'],
                                              'status': 'STOPPED', 'stop_reason': 'MATERIAL_PIN_DRIFT', 'pin_check_before': pc,
                                              'generated_utc': iso()})
        print('STOPPED: MATERIAL_PIN_DRIFT')
        return 2
    ledger = DualLedger(run_dir / 'request_ledger.jsonl', cfg['_master'], {'panel': cfg['panel_id'], 'run_id': run_dir.name})
    aux = Aux(run_dir / 'aux_ledger.jsonl')
    ctx = {'run_dir': run_dir, 'ledger': ledger, 'aux': aux, 'first_request_utc': None,
           'aux_flags': {'apply': True, 'tokenize': True}, 'u': {},
           'allowed_dates': cfg['budget'].get('allowed_dates', []),
           'state': {}, 'inputs': {}, 'candidates': {}, 'cfg': cfg}
    for e in ledger.entries:
        if e.get('op') == 'reserve' and ctx['first_request_utc'] is None:
            try:
                ctx['first_request_utc'] = dt.datetime.strptime(e['utc'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=UTC)
            except Exception:
                pass
    if ctx['first_request_utc'] is not None:
        ctx['u']['first_request_utc'] = iso(ctx['first_request_utc'])
    if cfg.get('candidates_file'):
        cf = json.loads((cfg['_root'] / cfg['candidates_file']).read_text(encoding='utf-8-sig'))
        ctx['candidates'] = {c['candidate_id']: c for c in cf['candidates']}
    mp_path = run_dir / 'MODEL_PIN.json'
    if mp_path.exists():
        mp = json.loads(mp_path.read_text(encoding='utf-8-sig'))
    else:
        mp = capture_model_pin(run_dir, aux)
        write_json(mp_path, mp)
    if not mp.get('identity_ok'):
        write_json(run_dir / 'RECEIPT.json', {'schema': 'tq_chain_receipt_v1', 'run_id': run_dir.name, 'panel': cfg['panel_id'],
                                              'status': 'STOPPED', 'stop_reason': 'MODEL_IDENTITY_DRIFT', 'model_pin': mp,
                                              'generated_utc': iso()})
        print('STOPPED: MODEL_IDENTITY_DRIFT')
        return 2
    tpl = parse_templates(cfg['_templates'])
    existing_skips = load_run_jsonl(run_dir / 'skips.jsonl')
    for step in cfg['steps']:
        st = ledger.item_state(step['key'])
        if st == 'done':
            if step['kind'] == 'actor':
                obj, valid = load_actor_from_raw(run_dir, ledger, step['key'])
                ctx['state'][step['key']] = {'status': 'valid' if valid else 'invalid', 'obj': obj if valid else None}
            continue
        if st == 'inflight':
            ctx['state'][step['key']] = {'status': 'inflight'}
            continue
        if st in ('failed', 'refused'):
            ctx['state'][step['key']] = {'status': st}
            continue
        if step['key'] in existing_skips:
            ctx['state'][step['key']] = {'status': 'skipped', 'reason': existing_skips[step['key']].get('reason')}
            continue
        rec = ctx['inputs'].get(step['input'])
        if rec is None:
            rec = json.loads((cfg['_root'] / step['input']).read_text(encoding='utf-8-sig'))
            ctx['inputs'][step['input']] = rec
        if step['kind'] == 'actor':
            messages = render_actor(tpl, step['task_id'], rec)
        else:
            src, err = get_source_obj(ctx, step)
            if src is None:
                reason = err or 'SOURCE_MISSING'
                append_jsonl(run_dir / 'skips.jsonl', {'item_key': step['key'], 'arm': step['kind'], 'case': step['task_id'],
                                                       'variant': step.get('variant'), 'skipped': True, 'reason': reason, 'utc': iso()})
                ctx['state'][step['key']] = {'status': 'skipped', 'reason': reason}
                continue
            messages = render_b(tpl, rec, src) if step['kind'] == 'b' else render_c(tpl, rec, src)
        item = build_step_item(step)
        act, kind = process_item(item, messages, ctx, ctx['state'], {'n': 0})
        if act == 'stop':
            stop_reason = kind
            break
    else:
        stop_reason = None
    pc2 = check_material_pins(cfg)
    write_json(run_dir / 'PIN_CHECK_AFTER.json', pc2)
    if not pc2['ok'] and not stop_reason:
        stop_reason = 'MATERIAL_PIN_DRIFT_AFTER'
    status = 'COMPLETED' if not stop_reason else 'PARTIAL'
    receipt = {'schema': 'tq_chain_receipt_v1', 'run_id': run_dir.name, 'panel': cfg['panel_id'], 'status': status,
               'stop_reason': stop_reason, 'generated_utc': iso(), 'first_request_utc': ctx['u'].get('first_request_utc'),
               'gen_attempts': ledger.gen_attempts(), 'retries_used': ledger.retries_used(),
               'tokens_settled': ledger.settled_tokens(), 'tokens_unsettled': ledger.unsettled_tokens(),
               'pin_check_before_ok': pc.get('ok'), 'pin_check_after_ok': pc2.get('ok'),
               'model_identity_ok': mp.get('identity_ok'),
               'aux_ops': sum(1 for e in aux.entries if e.get('op') == 'aux_send'), 'steps_total': len(cfg['steps'])}
    write_json(run_dir / 'RECEIPT.json', receipt)
    print(json.dumps({'panel': cfg['panel_id'], 'run_id': run_dir.name, 'status': status, 'stop_reason': stop_reason,
                      'gen_attempts': ledger.gen_attempts()}, ensure_ascii=True))
    return 0 if status == 'COMPLETED' else 3


def cmd_plan(cfg):
    tpl = parse_templates(cfg['_templates'])
    cands = {}
    if cfg.get('candidates_file'):
        cf = json.loads((cfg['_root'] / cfg['candidates_file']).read_text(encoding='utf-8-sig'))
        cands = {c['candidate_id']: c for c in cf['candidates']}
    cache = {}
    rows = []
    for step in cfg['steps']:
        rec = cache.get(step['input'])
        if rec is None:
            rec = json.loads((cfg['_root'] / step['input']).read_text(encoding='utf-8-sig'))
            cache[step['input']] = rec
        if step['kind'] == 'actor':
            msgs = render_actor(tpl, step['task_id'], rec)
        else:
            if step.get('source') == 'candidate':
                src = strip_candidate(cands[step['candidate_id']])
            else:
                src = {'task_id': step['task_id'], 'answer': '0000', 'evidence': []}
            msgs = render_b(tpl, rec, src) if step['kind'] == 'b' else render_c(tpl, rec, src)
        est = len((msgs[0]['content'] + chr(10) + msgs[1]['content']).encode('utf-8')) + 512
        rows.append({'step': step['step'], 'key': step['key'], 'kind': step['kind'], 'byte_bound': est})
    tpl_sha = {}
    for k, v in tpl.items():
        tpl_sha[k] = sha256_bytes((v[0] + chr(10) + v[1]).encode('utf-8'))
    print(json.dumps({'panel': cfg['panel_id'], 'steps': len(rows), 'max_byte_bound': max(r['byte_bound'] for r in rows),
                      'template_sha256': tpl_sha, 'rows': rows}, ensure_ascii=True))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    ap.add_argument('--root', default=None)
    ap.add_argument('--plan', action='store_true')
    ap.add_argument('--check-pins', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--resume', default=None)
    args = ap.parse_args()
    cfg = load_config(args.config, root_override=args.root)
    if args.check_pins:
        r = check_material_pins(cfg)
        print(json.dumps(r, ensure_ascii=True))
        return 0 if r['ok'] else 2
    if args.plan:
        return cmd_plan(cfg)
    if args.resume:
        return cmd_run(cfg, resume_id=args.resume)
    if args.run:
        return cmd_run(cfg)
    ap.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
