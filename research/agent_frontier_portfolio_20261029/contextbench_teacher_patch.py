"""One-post, source-only teacher patch diagnostic; never a learning-effect claim."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
PUBLIC_HELPERS = Path('/home/testuser/wzh/projects/agents_final_tech/research/agent_frontier_portfolio_20261029')
PRIVATE = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
SOURCE = 'sympy__sympy-21055'
CODE = 'sympy/assumptions/refine.py'
PROFILE_SHA = '9cbb51bb6dc64583cb376f81e8f8c1c28400cb494fce2793f1fa2ce60e39a279'
SYSTEM = ('Repair the supplied source implementation using the public task and executed public reproduction. '
          'Return only one unified diff for ' + CODE + '. Do not change tests, create/delete/rename files, '
          'or include prose. You may wrap the entire diff in one diff code fence. No tools are available.')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()


def wire_body(payload):
    return json.dumps(payload, separators=(',', ':')).encode()  # Exact native.exchange serialization.


def safe(path):
    path = Path(path)
    if not path.is_absolute() or path != path.resolve(): raise ValueError('canonical absolute path required')
    for item in (path, *path.parents):
        if item.is_symlink() or item.is_file() and item.stat().st_nlink != 1: raise ValueError('linked input')
    return path


def read_ref(ref, *, binary=False):
    if type(ref) is not dict or set(ref) != {'path', 'sha256'}: raise ValueError('exact path/SHA required')
    raw = safe(ref['path']).read_bytes()
    if sha(raw) != ref['sha256']: raise ValueError('frozen input SHA changed')
    return raw if binary else decode(raw)


def new(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as out: out.write(encoded(value) + b'\n')


def module(ref, filename):
    if Path(ref['path']) not in (HERE / filename, PUBLIC_HELPERS / filename): raise ValueError('unapproved helper path')
    read_ref(ref, binary=True)
    spec = importlib.util.spec_from_file_location('_teacher_patch_' + filename[:-3], ref['path'])
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def reproduction(raw, call_id):
    rows = [decode(line) for line in raw.splitlines() if line.strip()]
    calls = [x['part'] for x in rows if x.get('type') == 'tool_use' and isinstance(x.get('part'), dict)]
    matches = [x for x in calls if x.get('callID') == call_id]
    if len(matches) != 1 or matches[0] != calls[-1]: raise ValueError('exact last completed reproduction required')
    part = matches[0]; state = part.get('state', {}); meta = state.get('metadata', {})
    if (part.get('tool') != 'bash' or state.get('status') != 'completed' or
            set(state.get('input', {})) != {'command'} or type(state['input']['command']) is not str or
            type(state.get('output')) is not str or meta.get('output') != state['output'] or
            type(meta.get('exit')) is not int or meta.get('truncated') is not False):
        raise ValueError('incomplete public command/output')
    return dict(call_id=call_id, command=state['input']['command'], output=state['output'], exit=meta['exit'])


def messages_for(public, code, feedback):
    # Only this allowlist enters the teacher input; manifests, scorer patches and paths do not.
    user = ('Public source task (verbatim):\n' + public + '\n\nPublic source file ' + CODE + ':\n' + code +
            '\n\nExecuted public reproduction:\n' + feedback['command'] + '\nExit: ' + str(feedback['exit']) +
            '\nActual output:\n' + feedback['output'])
    return [dict(role='system', content=SYSTEM), dict(role='user', content=user)]


def payload_for(messages, profile, thinking):
    if type(thinking) is not bool: raise ValueError('boolean thinking mode required')
    return dict(model=profile['model_id'], messages=copy.deepcopy(messages), seed=17, temperature=0.2,
                max_tokens=8192, stream=True, stream_options=dict(include_usage=True),
                chat_template_kwargs=dict(enable_thinking=thinking), tools=[], tool_choice='none', parallel_tool_calls=False)


def token_counter(profile):
    # Actual serving template and actual kwargs for EACH arm; no weights or endpoints.
    from transformers import AutoTokenizer
    model = Path(profile['model_root']); template = safe(profile['template_path']).read_bytes()
    if sha(template) != profile['template_sha256']: raise ValueError('serving template changed')
    files = {str(model / name): sha(safe(model / name).read_bytes()) for name in ('tokenizer.json', 'tokenizer_config.json')}
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True, trust_remote_code=False, use_fast=True)
    binding = dict(files=files, template_sha256=sha(template), transformers=importlib.metadata.version('transformers'),
                   tokenizers=importlib.metadata.version('tokenizers'))
    def count(payload):
        tokens = tokenizer.apply_chat_template(payload['messages'], chat_template=template.decode(),
            tools=payload['tools'] or None, tokenize=True, return_dict=False, add_generation_prompt=True,
            **payload['chat_template_kwargs'])
        if type(tokens) is not list or not tokens or any(type(token) is not int or token < 0 for token in tokens):
            raise ValueError('serving tokenizer must return one nonempty list of integer token IDs')
        number = len(tokens)
        return dict(template_input_tokens=number, reserved_output_tokens=8192, context=32768,
                    safety_margin_tokens=512, fits_with_margin=number + 8192 + 512 <= 32768,
                    token_return_type=type(tokens).__module__ + '.' + type(tokens).__name__,
                    enable_thinking=payload['chat_template_kwargs']['enable_thinking'], payload_sha256=sha(wire_body(payload)))
    return count, binding


def load_inputs(path, digest):
    ref = dict(path=str(safe(path)), sha256=digest); p = read_ref(ref)
    keys = {'schema', 'source_manifest', 'source_receipt', 'source_raw', 'source_closure', 'profile',
            'source_runner', 'transport', 'reproduction_call_id', 'code_paths', 'output_root', 'caps'}
    if set(p) != keys or p['schema'] != 'CONTEXTBENCH_TEACHER_PATCH_V1' or p['code_paths'] != [CODE]:
        raise ValueError('unsupported source-only patch protocol')
    caps = p['caps']
    if (set(caps) != {'posts', 'seconds', 'combined_wire_bytes'} or any(type(v) is not int for v in caps.values()) or
            caps['posts'] != 1 or not 1 <= caps['seconds'] <= 1200 or not 1 <= caps['combined_wire_bytes'] <= 64 * 1024**2):
        raise ValueError('one-post bounded caps required')
    source = module(p['source_runner'], 'run_contextbench_source.py')
    transport = module(p['transport'], 'alfworld_native_actor.py')
    m = read_ref(p['source_manifest']); old = safe(p['source_manifest']['path']).parent
    if Path(p['source_manifest']['path']).name != 'manifest.json': raise ValueError('source manifest name differs')
    verified, h, _, profile = source.verify(old, p['source_manifest']['sha256'], initial=False)
    if verified != m or m['source'] != SOURCE or m['repo'] != 'sympy/sympy' or m['profile'] != p['profile'] or p['profile']['sha256'] != PROFILE_SHA:
        raise ValueError('wrong source/profile')
    if source.tree(old / 'work') != m['baseline']: raise ValueError('closed source work was changed')
    h.teacher.validate_vllm_model_profile(p['profile']['path'], p['profile']['sha256'], full=False)
    receipt = read_ref(p['source_receipt']); closure = read_ref(p['source_closure']); raw = read_ref(p['source_raw'], binary=True)
    if (Path(p['source_receipt']['path']) != old / 'receipt.json' or Path(p['source_raw']['path']) != old / 'raw.jsonl' or
            receipt['source'] != SOURCE or receipt['manifest_sha256'] != p['source_manifest']['sha256'] or
            receipt['raw_sha256'] != p['source_raw']['sha256'] or receipt['source_success'] is not False or
            receipt['changed_artifacts'] != [] or receipt['status'] != 'GENERATION_FAULT' or
            closure.get('source_id') != SOURCE or closure.get('status') != 'EXPLAINED_BUDGET_CLOSED_UNREPAIRED' or
            closure.get('manifest_sha256') != p['source_manifest']['sha256'] or closure.get('receipt_sha256') != p['source_receipt']['sha256'] or
            closure.get('actual_forwarded_POST') != receipt['accounting']['actual_forwarded_posts'] or
            closure.get('source_success') is not False or closure.get('changed_artifacts') != [] or
            not transport.valid_usage(closure.get('provider_usage')) or
            closure['provider_usage']['total_tokens'] != receipt['accounting'].get('provider_total_tokens_known') or
            closure.get('unknown_usage_requests') != 0 or receipt['accounting']['integrity_passed'] is not True or
            receipt['accounting'].get('unknown_usage_requests') != [] or receipt['accounting'].get('uncertain_partial_sends') != 0 or
            type(receipt['accounting']['actual_forwarded_posts']) is not int or receipt['accounting']['actual_forwarded_posts'] <= 0 or
            len(m['labels']['f2p']) != 1 or len(m['labels']['ptp']) != 13):
        raise ValueError('actual closed unrepaired source binding differs')
    feedback = reproduction(raw, p['reproduction_call_id'])
    public = (old / 'inputs/source_task.txt').read_bytes(); code = safe(old / 'baseline' / CODE).read_bytes()
    if sha(public) != m['public_task_sha256'] or sha(code) != m['baseline'][CODE]: raise ValueError('source bytes changed')
    output = safe(p['output_root'])
    if PRIVATE not in output.parents or old == output or old in output.parents or output in old.parents:
        raise ValueError('independent private output root required')
    count, tokenizer = token_counter(profile)
    messages = messages_for(public.decode(), code.decode(), feedback)
    payloads = {arm: payload_for(messages, profile, arm == 'true') for arm in ('false', 'true')}
    proofs = {arm: count(payload) for arm, payload in payloads.items()}
    if not all(proof['fits_with_margin'] for proof in proofs.values()): raise ValueError('actual arm template exceeds context reserve')
    manifest = dict(schema='CONTEXTBENCH_TEACHER_PATCH_PREPARED_V1', protocol=ref, root=str(output),
        module_sha256=sha(Path(__file__).read_bytes()), source=SOURCE, source_public_task_sha256=sha(public),
        source_code_sha256={CODE: sha(code)}, reproduction=feedback, messages_sha256=sha(encoded(messages)),
        payload_sha256={k: sha(wire_body(v)) for k, v in payloads.items()}, tokenizer=tokenizer, template_checks=proofs,
        payload_byte_scope='native.exchange compact json.dumps, ensure_ascii=True; exact actual request body',
        interpretation='D-located exposed-source capability diagnostic; identical messages, only enable_thinking differs.',
        reasoning_parser='UNKNOWN_CURRENT_SERVER_METADATA', prior_source_cost=closure['provider_usage'])
    return dict(p=p, manifest=manifest, source=source, transport=transport, h=h, m=m, profile=profile,
                old=old, root=output, payloads=payloads, count=count, messages=messages)


def prepare(path, digest):
    b = load_inputs(path, digest); root = b['root']
    root.mkdir(parents=True, mode=0o700)  # Exclusive root, including after an interrupted prepare.
    new(root / 'manifest.json', b['manifest']); new(root / 'messages.json', b['messages'])
    for arm, payload in b['payloads'].items(): new(root / ('payload_' + arm + '.json'), payload)
    return dict(status='CPU_PREPARED', root=str(root), manifest_sha256=sha((root / 'manifest.json').read_bytes()), models_called=0)


def verify_prepared(b, digest):
    m = read_ref(dict(path=str(b['root'] / 'manifest.json'), sha256=digest))
    if m != b['manifest'] or decode((b['root'] / 'messages.json').read_bytes()) != b['messages']:
        raise ValueError('prepared inputs changed')
    for arm, payload in b['payloads'].items():
        if decode((b['root'] / ('payload_' + arm + '.json')).read_bytes()) != payload: raise ValueError('prepared arm payload changed')


def response_channels(raw):
    channels = dict(content='', reasoning='', reasoning_content=''); finish = None; done = False
    for event in re.split(rb'\r?\n\r?\n', raw):
        data = b'\n'.join(line[5:].lstrip(b' ') for line in event.splitlines() if line.startswith(b'data:'))
        if not data: continue
        if done: raise ValueError('SSE after DONE')
        if data == b'[DONE]': done = True; continue
        item = decode(data)
        if item.get('error'): raise ValueError('model SSE error')
        choices = item.get('choices', [])
        if not choices: continue
        if len(choices) != 1 or choices[0].get('index') != 0: raise ValueError('single response choice required')
        choice = choices[0]; delta = choice.get('delta', {})
        if set(delta) - {*channels, 'role'} or delta.get('role', 'assistant') != 'assistant': raise ValueError('unexpected response channel/tools')
        for key in channels:
            value = delta.get(key)
            if value is not None:
                if type(value) is not str: raise ValueError('nontext response channel')
                channels[key] += value
        if choice.get('finish_reason') is not None:
            if finish is not None: raise ValueError('duplicate finish')
            finish = choice['finish_reason']
    if not done or finish is None: raise ValueError('incomplete SSE response')
    return dict(**channels, finish_reason=finish, raw_sse_sha256=sha(raw))


def strict_diff(content):
    adapted = content; adaptation = 'none'
    fence = re.fullmatch(r'```diff\n(.*\n)```\n?', content, re.DOTALL)
    if fence:
        adapted = fence[1]; adaptation = 'one complete outer diff fence removed'
    if not adapted.endswith('\n'): raise ValueError('diff must end with LF; no automatic repair')
    lines = adapted.splitlines(); start = 0
    if lines and lines[0] == 'diff --git a/' + CODE + ' b/' + CODE: start = 1
    if start < len(lines) and re.fullmatch(r'index [0-9a-f]+\.\.[0-9a-f]+( 100644)?', lines[start]): start += 1
    if lines[start:start + 2] != ['--- a/' + CODE, '+++ b/' + CODE]: raise ValueError('exact existing allowed source diff required')
    body = lines[start + 2:]
    if not body or not body[0].startswith('@@ '): raise ValueError('missing unified hunk')
    for line in body:
        if line.startswith('@@ '):
            if not re.fullmatch(r'@@ -\d+(,\d+)? \+\d+(,\d+)? @@.*', line): raise ValueError('bad hunk')
        elif not line or line[0] not in ' +-\\': raise ValueError('prose/second patch/file operation forbidden')
        if line.startswith(('--- ', '+++ ')): raise ValueError('multiple file headers forbidden')
    return adapted, adaptation


def complete_score(score, labels):
    suites = score.get('suites', {})
    return (score.get('passed') is True and score.get('status') == 'EVALUATED' and set(suites) == {'f2p', 'ptp'} and
        all(not value.get('error') and not value.get('cleanup_error') and value.get('exit') == 0 and
            value.get('coverage', {}).get('complete') is True and
            value['coverage'].get('reported_tests') == len(labels[name]) and value['coverage'].get('extra_ids') == [] and
            value['coverage'].get('labels') == dict.fromkeys(labels[name], 'passed')
            for name, value in suites.items()))


def check_release(ref, b, arm, digest):
    release = read_ref(ref); root = b['root'] / arm
    expected = dict(schema='CONTEXTBENCH_TEACHER_PATCH_RELEASE_V1', protocol=b['manifest']['protocol'],
        prepared_manifest_sha256=digest, module_sha256=b['manifest']['module_sha256'], arm=arm,
        output_root=str(root), caps=b['p']['caps'], authorization='ONE_REAL_MODEL_POST')
    if release != expected: raise ValueError('explicit exact arm release required')
    return release


def execute(path, digest, prepared_sha, arm, release_ref):
    if arm not in ('false', 'true'): raise ValueError('exact false/true arm required')
    b = load_inputs(path, digest); verify_prepared(b, prepared_sha); release = check_release(release_ref, b, arm, prepared_sha)
    source, transport, h = b['source'], b['transport'], b['h']; root = b['root'] / arm; caps = b['p']['caps']
    with source.resource_lock():
        root.mkdir(mode=0o700)  # A failed execution is never retried in this root.
        started = time.monotonic(); attempts = []; budget = h.actor.Budget(**dict(max_posts=1, max_bytes=caps['combined_wire_bytes'], seconds=caps['seconds']))
        result = dict(status='GENERATION_FAULT', source=SOURCE, arm=arm, source_success=False,
                      protocol=b['manifest']['protocol'], prepared_manifest_sha256=prepared_sha, release=release)
        previous = signal.getsignal(signal.SIGTERM)
        def interrupted(*_): raise InterruptedError('SIGTERM')
        signal.signal(signal.SIGTERM, interrupted)
        fatal = None
        try:
            new(root / 'reservation.json', release)
            shutil.copytree(b['old'] / 'baseline', root / 'baseline'); shutil.copytree(root / 'baseline', root / 'work')
            for item in (root / 'work').rglob('*'):
                if item.is_file(): item.chmod(item.stat().st_mode | 0o200)
            (root / 'scoring').mkdir(); shutil.copyfile(b['old'] / 'scoring/test.patch', root / 'scoring/test.patch')
            result['backend'] = h.teacher.verify_vllm_backend(b['profile'])  # Execute only; no shared server changes.
            raw = transport.exchange(h.actor, root, b['payloads'][arm], budget, b['count'],
                                     (b['profile']['host'], b['profile']['port']), attempts)
            channels = response_channels(raw); new(root / 'channels.json', channels); result['response'] = channels
            if not transport.accounting(attempts, budget)['integrity_passed']: raise ValueError('unknown/partial model accounting; no retry')
            if channels['finish_reason'] != 'stop': raise ValueError('unfinished/nontext model output; no retry or patch repair')
            diff, adaptation = strict_diff(channels['content'])
            (root / 'adapted.diff').write_bytes(diff.encode()); result['adaptation'] = adaptation
            helper, _ = h.pool.helpers(); applied = helper.apply_patch(root / 'work', diff)
            new(root / 'patch_receipt.json', applied); result['patch'] = applied
            if applied['check_exit'] != 0 or applied['apply_exit'] != 0: raise ValueError('generated diff did not apply; no repair')
            result['changed_artifacts'] = source.candidate_diff(root)
            if [x['path'] for x in result['changed_artifacts']] != [CODE]: raise ValueError('candidate escaped allowed source file')
            result['scoring'] = source.score(root, b['m'], h)
            result['source_success'] = complete_score(result['scoring'], b['m']['labels']); result['status'] = 'EVALUATED'
        except BaseException as exc:
            result['error'] = dict(type=type(exc).__name__, detail=str(exc))
            if isinstance(exc, (KeyboardInterrupt, SystemExit)): fatal = exc
        finally:
            signal.signal(signal.SIGTERM, previous)
            result['wall_seconds'] = time.monotonic() - started; result['accounting'] = transport.accounting(attempts, budget)
            result['prior_source_cost_reference'] = b['p']['source_closure']; new(root / 'receipt.json', result)
        if fatal: raise fatal
    return dict(status=result['status'], source_success=result['source_success'], root=str(root), receipt_sha256=sha((root / 'receipt.json').read_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__); mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare', action='store_true'); mode.add_argument('--check-only', action='store_true'); mode.add_argument('--execute', action='store_true')
    parser.add_argument('--protocol', required=True); parser.add_argument('--protocol-sha', required=True)
    parser.add_argument('--manifest-sha'); parser.add_argument('--arm', choices=('false', 'true'))
    parser.add_argument('--release'); parser.add_argument('--release-sha'); args = parser.parse_args()
    if args.execute:
        if not all((args.manifest_sha, args.arm, args.release, args.release_sha)): parser.error('execute needs manifest SHA, arm, release path/SHA')
        result = execute(args.protocol, args.protocol_sha, args.manifest_sha, args.arm, dict(path=args.release, sha256=args.release_sha))
    elif args.prepare: result = prepare(args.protocol, args.protocol_sha)
    else:
        b = load_inputs(args.protocol, args.protocol_sha)
        if args.manifest_sha: verify_prepared(b, args.manifest_sha)
        result = dict(status='CPU_CHECKED', template_checks=b['manifest']['template_checks'], models_called=0)
    print(json.dumps(result)); return 1 if result['status'] == 'GENERATION_FAULT' else 0


if __name__ == '__main__': sys.exit(main())
