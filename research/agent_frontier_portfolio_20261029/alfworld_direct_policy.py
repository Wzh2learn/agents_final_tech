"""Native HTTP + admissible-action constraint baseline; CPU preparation is not a run."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import re
import time

HERE = Path(__file__).resolve().parent
CAPS = dict(posts=128, seconds=1800, world_actions=100, model_payload_bytes_combined=64000000)
KEYS = ('observation', 'score', 'done', 'won', 'action_count', 'admissible_commands')
SYSTEM = ('Complete the household task using its public goal and actual environment feedback. '
          'The initial reset is historical after an action; read every subsequent response. '
          'Each accepted action, including look, consumes one real step. Only native won=true proves success. '
          'FORMAT_HINT: Return exactly one JSON object, no markdown, explanation, reasoning or extra fields. '
          'Use exactly one field: action with an exact string from the latest admissible_commands, '
          'or stop with the boolean true (the stop form is {"stop":true}).')
CONTINUE = 'Continue the unfinished task.'


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8') as out:
        json.dump(value, out, ensure_ascii=False)
        out.write('\n')


def dependencies():
    spec = importlib.util.spec_from_file_location('direct_policy_study', HERE / 'alfworld_context_study.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def strict_json(text: str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def decision_schema(commands: list[str]) -> dict:
    branches = [{'type': 'object', 'properties': {'stop': {'const': True}},
                 'required': ['stop'], 'additionalProperties': False}]
    if commands:
        branches.insert(0, {'type': 'object', 'properties': {
            'action': {'type': 'string', 'enum': list(dict.fromkeys(commands))}},
            'required': ['action'], 'additionalProperties': False})
    return {'oneOf': branches}


def parse_decision(text: str, commands: list[str]) -> dict:
    value = strict_json(text)
    if type(value) is dict and set(value) == {'action'} and type(value['action']) is str and value['action'] in commands:
        return value
    if type(value) is dict and set(value) == {'stop'} and value['stop'] is True:
        return value
    raise ValueError('model JSON is not one exact admissible action or stop=true')


class ByteLimit(Exception):
    pass


def http_transport(profile: dict):
    """One non-streaming POST; preserve received bytes, never retry or fall back."""
    def send(body, deadline, allowance, emit):
        def remaining():
            value = deadline - time.monotonic()
            if value <= 0:
                raise TimeoutError('episode deadline')
            return value
        conn = http.client.HTTPConnection(profile['host'], profile['port'], timeout=remaining())
        try:
            conn.request('POST', '/v1/chat/completions', body,
                         {'Content-Type': 'application/json', 'Connection': 'close'})
            emit('sent', True)
            conn.sock.settimeout(remaining())
            response = conn.getresponse()
            emit('headers', {'status': response.status, 'reason': response.reason,
                             'headers': response.getheaders()})
            if response.length is not None and response.length > allowance:
                raise ByteLimit('HTTP body exceeds remaining physical byte cap')
            expected, received = response.length, 0
            while not response.isclosed():
                if allowance <= 0:
                    raise ByteLimit('HTTP body reached physical byte cap before EOF')
                if conn.sock is not None:
                    conn.sock.settimeout(remaining())
                chunk = response.read(min(65536, allowance))
                if not chunk:
                    break
                emit('body', chunk)
                allowance -= len(chunk)
                received += len(chunk)
            if expected is not None and received != expected:
                raise http.client.HTTPException('incomplete HTTP response body')
        finally:
            conn.close()
    return send


def run_policy(root: Path, reset: dict, step, transport, core, profile: dict, qualify,
               validate, *, caps: dict | None = None, mode: str = 'OWNED_FAKE', now=time.monotonic) -> dict:
    """Injected I/O permits CPU contracts; only CLI execution labels real model calls."""
    if mode not in {'OWNED_FAKE', 'REAL_DEVELOPMENT'} or (profile['context'], profile['output']) != (32768, 8192):
        raise ValueError('8B context/output and explicit evidence mode required')
    caps = core.episode_caps(CAPS if caps is None else caps)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    project = lambda state: validate(dict(state) if set(state) == {'error'} else {k: state[k] for k in KEYS})
    current = project(reset)
    if set(current) == {'error'}:
        raise ValueError('initial public state required')
    started = now()
    deadline = started + caps['seconds']
    budget = core.Budget(caps['posts'], caps['model_payload_bytes_combined'], caps['seconds'])
    messages = [{'role': 'system', 'content': SYSTEM},
                {'role': 'user', 'content': 'Original public goal and initial state:\n' + json.dumps(current, ensure_ascii=False)}]
    exchanges, events, usage, errors = [], [], [], []
    continuations = step_calls = 0
    phase, world_known = 'model', True
    status = 'FAILED'
    write(root / 'config.json', dict(profile=profile, caps=caps, seed=17, enable_thinking=False,
                                   mode=mode, system_prompt=SYSTEM, source_experience=False))
    try:
        while True:
            if current['won'] or current['done']:
                status = 'WON' if current['won'] else 'DONE_UNWON'
                break
            if current['action_count'] >= caps['world_actions']:
                status = 'WORLD_LIMIT'
                break
            if budget.posts >= caps['posts'] or now() >= deadline:
                status = 'POST_LIMIT' if budget.posts >= caps['posts'] else 'EPISODE_TIMEOUT'
                break
            phase = 'model'
            payload = core.model_payload({'messages': messages}, 'student8b', profile, 17, False)
            payload.update(stream=False, response_format={'type': 'json_object', 'schema': decision_schema(current['admissible_commands'])})
            payload.pop('stream_options', None)
            body = json.dumps(payload, separators=(',', ':')).encode()
            index = str(budget.posts + 1).zfill(5)
            (root / (index + '.request.json')).write_bytes(body)
            proof = qualify(payload)
            write(root / (index + '.template.json'), proof)
            if (proof['context'], proof['reserved_output_tokens']) != (32768, 8192) or proof['template_input_tokens'] + 8192 + 512 > 32768:
                status = 'CONTEXT_LIMIT'
                break
            if len(body) > caps['model_payload_bytes_combined'] - budget.request_bytes - budget.response_bytes:
                status = 'BYTE_LIMIT'
                break
            try:
                budget.reserve(len(body))
            except ValueError:
                status = 'EPISODE_TIMEOUT' if now() >= deadline else 'BYTE_LIMIT'
                break
            exchange = {'index': budget.posts, 'confirmed_sent': False, 'complete': False, 'usage': None,
                        'request_sha256': hashlib.sha256(body).hexdigest(), 'response_body_bytes': 0}
            exchanges.append(exchange)
            response_path = root / (index + '.response.body')
            try:
                with response_path.open('xb') as raw:
                    def emit(kind, value):
                        if kind == 'sent':
                            exchange['confirmed_sent'] = True
                        elif kind == 'headers':
                            exchange.update(value)
                        elif kind == 'body':
                            if len(value) > caps['model_payload_bytes_combined'] - budget.request_bytes - budget.response_bytes:
                                raise ByteLimit('transport exceeded response allowance')
                            raw.write(value)
                            exchange['response_body_bytes'] += len(value)
                            budget.response(len(value))
                        else:
                            raise ValueError('unknown transport event')
                    transport(body, deadline, caps['model_payload_bytes_combined'] - budget.request_bytes - budget.response_bytes, emit)
                exchange['complete'] = True
                if exchange.get('status') != 200:
                    status = 'INTERFACE_BLOCKED' if exchange.get('status') in {400, 404, 422} else 'HTTP_ERROR'
                    break
                result = strict_json(response_path.read_bytes().decode('utf-8'))
                value = result.get('usage')
                if type(value) is dict and all(type(value.get(k)) is int and value[k] >= 0 for k in ('prompt_tokens', 'completion_tokens', 'total_tokens')):
                    exchange['usage'] = value
                    usage.append(value)
                if result.get('model', profile['model_id']) != profile['model_id']:
                    status = 'INTERFACE_BLOCKED'
                    break
                choices = result['choices']
                if len(choices) != 1 or choices[0]['message'].get('reasoning_content') not in (None, ''):
                    raise ValueError('one final-content choice without reasoning required')
                if choices[0].get('finish_reason') != 'stop':
                    status = 'MODEL_OUTPUT_LIMIT'
                    break
                text = choices[0]['message']['content']
                decision = parse_decision(text, current['admissible_commands'])
                messages.append({'role': 'assistant', 'content': text})
            finally:
                exchange['response_sha256'] = sha(response_path)
                write(root / (index + '.exchange.json'), exchange)
            if now() >= deadline:
                status = 'EPISODE_TIMEOUT'
                break
            if 'stop' in decision:
                if continuations == 0 and budget.posts < caps['posts'] and now() + 5 < deadline:
                    continuations += 1
                    messages.append({'role': 'user', 'content': CONTINUE})
                    continue
                status = 'MODEL_STOP'
                break
            step_calls += 1
            phase = 'world'
            observed = project(step(decision['action'], max(.001, min(10., deadline-now()))))
            event = {'action': decision['action'], 'state': observed}
            events.append(event)
            write(root / ('step_' + str(step_calls).zfill(5) + '.json'), event)
            messages.append({'role': 'user', 'content': 'Actual environment response:\n' + json.dumps(observed, ensure_ascii=False)})
            if 'error' not in observed:
                current = observed
    except TimeoutError as exc:
        status = 'TRANSPORT_TIMEOUT' if phase == 'model' else 'NATIVE_TIMEOUT'
        world_known = phase != 'world'
        errors.append(str(exc))
    except ByteLimit as exc:
        status = 'BYTE_LIMIT'
        errors.append(str(exc))
    except (OSError, http.client.HTTPException) as exc:
        status = 'TRANSPORT_ERROR' if phase == 'model' else 'NATIVE_INTERFACE_ERROR'
        world_known = phase != 'world'
        errors.append(str(exc))
    except Exception as exc:
        status = 'MODEL_CONTRACT_ERROR' if phase == 'model' else 'NATIVE_INTERFACE_ERROR'
        world_known = phase != 'world'
        errors.append(str(exc))
    cached = [u.get('prompt_tokens_details', {}).get('cached_tokens')
              if isinstance(u.get('prompt_tokens_details'), dict) else None for u in usage]
    cache_known = len(usage) == len(exchanges) and bool(usage) and all(
        type(c) is int and 0 <= c <= u['prompt_tokens'] for c, u in zip(cached, usage))
    receipt = dict(label='OWNED_FAKE_NOT_SCIENTIFIC' if mode == 'OWNED_FAKE' else 'NATIVE_ENUM_COMBINATION_DEVELOPMENT',
                   status=status, errors=errors, won=current['won'], final_world_state=current, world_state_known=world_known,
                   model_posts=budget.posts, confirmed_sent_posts=sum(x['confirmed_sent'] for x in exchanges),
                   unconfirmed_delivery_posts=sum(not x['confirmed_sent'] for x in exchanges),
                   real_model_calls=sum(x['confirmed_sent'] for x in exchanges) if mode == 'REAL_DEVELOPMENT' else 0,
                   unknown_usage_model_posts=len(exchanges)-len(usage),
                   provider_usage={k: sum(u[k] for u in usage) for k in ('prompt_tokens','completion_tokens','total_tokens')} if usage else None,
                   provider_usage_scope='known_responses_only',
                   provider_cached_input_tokens=sum(cached) if cache_known else None,
                   provider_uncached_input_tokens=sum(u['prompt_tokens'] for u in usage)-sum(cached) if cache_known else None,
                   model_request_payload_bytes=budget.request_bytes, model_response_wire_bytes=budget.response_bytes,
                   request_byte_measurement='serialized payload reserved; partial transport delivery may be unknown',
                   elapsed_seconds=now()-started, world_actions=current['action_count']-reset['action_count'],
                   world_step_calls=step_calls, ordinary_continuations=continuations,
                   response_receipts=exchanges, native_errors=[x for x in events if 'error' in x['state']],
                   pure_harness_causal_claim=False, replayed_actions=0)
    write(root / 'receipt.json', receipt)
    return receipt


@contextmanager
def resource_lock(path: Path):
    import fcntl
    with path.open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def prepare(root: Path, pool_path: Path, pool_sha: str, case_id: str) -> dict:
    study = dependencies()
    pool = study.task_pool()
    root = pool.private_path(root)
    if root.parent != study.QUAL / 'context_study_v1/direct_policy_v1' / case_id / 'student8b' or not re.fullmatch(r'attempt_v[1-9][0-9]*', root.name):
        raise ValueError('use direct_policy_v1/case_id/student8b/attempt_vN')
    _, binding = pool.select_game(pool_path, pool_sha, case_id)
    core = study.recovery().actor()
    profile = core.load_profile('student8b')
    tokenizer, _ = study.recovery().token_qualifier('student8b', profile)
    root.mkdir(parents=True, exist_ok=False)
    manifest = dict(case_id=case_id, pool_path=str(pool_path), pool_sha256=pool_sha, pool_binding=binding,
                    profile=profile, tokenizer_binding=tokenizer, caps=CAPS, system_prompt=SYSTEM,
                    components={**study.components(), str(Path(__file__).resolve()): sha(Path(__file__))})
    write(root / 'manifest.json', manifest)
    return manifest


def execute(root: Path, digest: str) -> dict:
    study = dependencies()
    root = study.task_pool().private_path(root)
    if sha(root / 'manifest.json') != digest:
        raise ValueError('manifest changed')
    m = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    if root.parent != study.QUAL / 'context_study_v1/direct_policy_v1' / m['case_id'] / 'student8b' or not re.fullmatch(r'attempt_v[1-9][0-9]*', root.name):
        raise ValueError('direct-policy namespace changed')
    core = study.recovery().actor()
    profile = core.load_profile('student8b')
    binding, qualify = study.recovery().token_qualifier('student8b', profile)
    _, pool_binding = study.task_pool().select_game(m['pool_path'], m['pool_sha256'], m['case_id'])
    if (m['components'] != {**study.components(), str(Path(__file__).resolve()): sha(Path(__file__))} or
            m['profile'] != profile or m['tokenizer_binding'] != binding or m['pool_binding'] != pool_binding or m['caps'] != CAPS or m['system_prompt'] != SYSTEM):
        raise ValueError('frozen direct-policy inputs changed')
    with resource_lock(study.QUAL / 'context_study_v1/model_resource.lock'):
        write(root / 'reservation.json', {'manifest_sha256': digest, 'mode': 'REAL_DEVELOPMENT'})
        world = None
        try:
            world, reset, _ = study.task_pool().start_world(root, m['case_id'], 17, 'execute', CAPS, m['pool_path'], m['pool_sha256'])
            bridge = study.recovery().bridge()
            result = run_policy(root / 'episode', reset, lambda action, timeout: bridge.client_step(world[1]/'s', action, timeout=timeout),
                                http_transport(profile), core, profile, qualify, bridge.validate_response, mode='REAL_DEVELOPMENT')
        finally:
            if world:
                core.stop_world(world)
        terminal = study.final_state(root)
        write(root / 'terminal_native.json', {'state': terminal, 'world_log_sha256': sha(root/'execute_world.jsonl')})
        result.update(final_world_state=terminal, won=terminal['won'] if terminal else None,
                      world_state_known=terminal is not None, world_actions=terminal['action_count']-reset['action_count'] if terminal else None,
                      episode_receipt_sha256=sha(root/'episode/receipt.json'))
        write(root / 'receipt.json', result)
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--run-root', required=True, type=Path)
    parser.add_argument('--pool', type=Path)
    parser.add_argument('--pool-sha')
    parser.add_argument('--case-id')
    parser.add_argument('--manifest-sha')
    args = parser.parse_args()
    if args.prepare:
        if not all((args.pool, args.pool_sha, args.case_id)) or args.manifest_sha:
            parser.error('prepare requires pool, pool-sha and case-id only')
        result = prepare(args.run_root, args.pool, args.pool_sha, args.case_id)
    else:
        if not args.manifest_sha or any((args.pool, args.pool_sha, args.case_id)):
            parser.error('execute requires only the frozen manifest SHA and run root')
        result = execute(args.run_root, args.manifest_sha)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
