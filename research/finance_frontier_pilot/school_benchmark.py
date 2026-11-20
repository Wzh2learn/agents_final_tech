"""Collect the managed DeepSeek independent arm through the campus budget gateway."""

import argparse
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socketserver
import sys
import threading
import time
from types import SimpleNamespace

from benchmark_actions import action_cost, collect_case, digest_file, freeze, read_panel, recorded_call
from run_pilot import OpenCode, write_json
from scoring import _metric_type


REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from scripts.graph import research_school_gateway as campus


PROJECT_CAP = 1_000_000_000
RECORDED_PRIOR_CHARGE = 60_404_610
CAPS = {'posts': 1, 'seconds': 500, 'combined_wire_bytes': 16 * 1024**2}
ACTION = 'independent'


def read_profile(path, expected_digest):
    if digest_file(path) != expected_digest:
        raise ValueError('managed API profile digest mismatch')
    profile = json.loads(path.read_text(encoding='utf-8'))
    gateway = {key: profile[key] for key in ('provider', 'base_url', 'model_id', 'context', 'output')}
    validated = dict(provider='bupt_chat_v1', base_url=campus.BASE_URL, model_id=campus.MODEL, context=262144)
    if (gateway != dict(validated, output=gateway['output']) or gateway['output'] not in (4096, 8192)
            or set(profile) != {*gateway, 'opencode_context', 'temperature'}
            or type(profile['opencode_context']) is not int
            or not gateway['output'] < profile['opencode_context'] <= gateway['context']
            or type(profile['temperature']) not in (int, float)
            or not math.isfinite(profile['temperature']) or not 0 <= profile['temperature'] <= 2):
        raise ValueError('unsupported managed API profile')
    return profile, gateway


def payload_for_prompt(value, prompt, temperature):
    if not isinstance(value, dict) or value.get('model') != campus.MODEL:
        raise ValueError('unexpected source model')
    if value.get('tools') or value.get('tool_choice') not in (None, 'none'):
        raise ValueError('independent arm accepts final-only requests')
    messages = value.get('messages')
    if not isinstance(messages, list) or not all(isinstance(msg, dict) for msg in messages):
        raise ValueError('invalid OpenCode message list')
    user = [msg.get('content') for msg in messages if msg.get('role') == 'user']

    def text(content):
        if isinstance(content, list) and all(isinstance(part, dict) and part.get('type') == 'text'
                                             and isinstance(part.get('text'), str) for part in content):
            return ''.join(part['text'] for part in content)
        return content

    content = text(user[0]) if len(user) == 1 else None
    # OpenCode wraps its single CLI argument in quotes, retaining literal line breaks.
    cli_prompt = '"' + prompt.replace('"', '\\"') + '"'
    if (content not in (prompt, cli_prompt)
            or any(msg.get('role') not in ('system', 'user') or not isinstance(text(msg.get('content')), str)
                   for msg in messages)):
        raise ValueError('OpenCode payload does not match the frozen source prompt')
    # Use only the external API fields needed by the matched independent arm.
    # The managed service does not expose a verified weight revision or deterministic seed.
    payload = {'model': campus.MODEL, 'messages': messages, 'temperature': temperature}
    return payload, {'version': 'finance_frontier_final_only_v1', 'tools_present': False}


@contextmanager
def source_relay(root, key, budget, gateway, prompt, temperature):
    import run_alfworld_actor_20261106 as actor
    import run_contextbench_source as core
    import run_django_aggregation_agent_20261106 as agg

    transport = SimpleNamespace(
        Relay=core.Relay, sha=core.sha,
        prepare_tool_contract=lambda value: payload_for_prompt(value, prompt, temperature),
    )
    backend = campus.SchoolBackend(key, budget, transport)
    backend.verify(gateway)
    root.mkdir()
    relay = backend.make_relay(root, gateway, SimpleNamespace(actor=actor, agg=agg),
                               deadline=time.monotonic() + CAPS['seconds'], caps=CAPS)

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            relay.handle(self.request)

    with socketserver.TCPServer(('127.0.0.1', 0), Handler) as server:
        background = threading.Thread(target=server.serve_forever, daemon=True)
        background.start()
        try:
            yield f'http://127.0.0.1:{server.server_address[1]}/v1'
        finally:
            relay.close()
            server.shutdown()
            background.join()


def charged(rows):
    return (sum(row['state'] != 'not_sent' for row in rows),
            sum(row.get('usage', {}).get('total_tokens', campus.REQUEST_TOKEN_CEILING)
                for row in rows if row['state'] != 'not_sent'))


def measured_usage(usage):
    details = usage.get('completion_tokens_details') or {}
    prompt_details = usage.get('prompt_tokens_details') or {}
    return dict(input=usage['prompt_tokens'], output=usage['completion_tokens'], total=usage['total_tokens'],
                reasoning=details.get('reasoning_tokens'), cache_read=prompt_details.get('cached_tokens'),
                cache_write=prompt_details.get('cache_write_tokens'), steps=1)


def bind_provider_result(target, run_digest, row, collected):
    path = target / 'provider_receipt.json'
    result = dict(collected)
    result['opencode_usage'] = collected['usage']
    result['usage'] = (measured_usage(row['usage']) if row and row['state'] == 'complete' else None)
    if row is None or row['state'] == 'not_sent':
        result['usage'] = dict(input=0, output=0, total=0, reasoning=0, cache_read=0, cache_write=0, steps=0)
    if row is None or row.get('http_status') != 200:
        result['errors'] = [*result['errors'], {'name': 'CampusDeliveryFailure'}]
    result['provider'] = row
    result['provider_posts'] = charged([row])[0] if row is not None else 0
    freeze(path, {'run_contract': run_digest, 'opencode_call_sha256': digest_file(target / 'call.json'),
                  'metered_result': result})
    return result


def replay_case(target, run_digest, rows, actor_prompt):
    path = target / 'provider_receipt.json'
    saved = json.loads(path.read_text(encoding='utf-8'))
    raw_path = target / 'call.json'
    expected_request = dict(prompt_sha256=hashlib.sha256(actor_prompt.encode('utf-8')).hexdigest(),
                            run_contract=run_digest, actor='solve')
    if (saved['run_contract'] != run_digest or saved['opencode_call_sha256'] != digest_file(raw_path)
            or json.loads((target / 'request.json').read_text(encoding='utf-8')) != expected_request
            or (target / 'prompt.txt').read_text(encoding='utf-8') != actor_prompt + '\n'):
        raise ValueError('cached campus action does not match the frozen request')
    result = saved['metered_result']
    row = result['provider']
    if row is not None and (not 1 <= row['index'] <= len(rows) or rows[row['index'] - 1] != row):
        raise ValueError('cached campus action has no matching authoritative ledger row')
    return bind_provider_result(target, run_digest, row, json.loads(raw_path.read_text(encoding='utf-8')))


def collect(args, root, ledger_root):
    public, gold, panel = read_panel(args.panel, args.dataset)
    if any(row['dataset'] == 'tatqa' for row in public):
        if args.metric_dir is None:
            raise ValueError('TAT-QA requires the official metric directory')
        _metric_type(args.metric_dir)
    profile, gateway = read_profile(args.api_profile, args.api_profile_sha256)
    freeze(root / 'run.json', {
        'schema': 'finance-benchmark-actions-v1', 'namespace': args.namespace, 'panel': panel,
        'dataset': args.dataset, 'actions': [ACTION], 'model': campus.MODEL,
        'api_profile_sha256': args.api_profile_sha256, 'endpoint': campus.BASE_URL,
        'serve_sha256': args.api_profile_sha256, 'opencode_sha256': digest_file(args.opencode),
        'seed': 17, 'provider_seed': None, 'context': profile['opencode_context'],
        'output': {'solve': gateway['output']}, 'temperature': profile['temperature'],
    })
    run_digest = digest_file(root / 'run.json')
    budget = campus.BatchBudget(ledger_root)
    try:
        freeze(ledger_root / 'opening.json', {'project_cap': PROJECT_CAP,
                                             'historical_charged_tokens': args.prior_charged_tokens})
        posts, tokens = charged(budget.rows)
        batches = root / 'batches'
        batches.mkdir(exist_ok=True)
        batch_path = batches / f'{args.batch}.json'
        existing = json.loads(batch_path.read_text(encoding='utf-8')) if batch_path.exists() else {}
        batch = dict(max_posts=args.max_posts, token_cap=args.token_cap,
                     posts_before=existing.get('posts_before', posts), tokens_before=existing.get('tokens_before', tokens))
        freeze(batch_path, batch)
        budget.posts = batch['posts_before'] + args.max_posts
        budget.tokens = min(PROJECT_CAP - args.prior_charged_tokens, batch['tokens_before'] + args.token_cap)
        key = os.environ.get('BUPT_API_KEY')
        return collect_rows(args, root, public, gold, run_digest, key, budget, profile, gateway)
    finally:
        budget.close()


def collect_rows(args, root, public, gold, run_digest, key, budget, profile, gateway):
    started = time.monotonic()
    first_row = len(budget.rows)
    temporary = root / 'outcomes.jsonl.tmp'
    completed = attempted = delivered = unknown = 0
    with temporary.open('w', encoding='utf-8') as stream:
        for row in public:
            case_id = hashlib.sha256(row['id'].encode('utf-8')).hexdigest()[:24]
            target = root / 'calls' / row['dataset'] / case_id / ACTION
            cached = (target / 'provider_receipt.json').is_file()
            if not cached:
                if target.exists():
                    raise RuntimeError(f'incomplete campus action requires ledger reconciliation: {target}')
                posts, tokens = charged(budget.rows)
                if posts >= budget.posts or tokens + campus.REQUEST_TOKEN_CEILING > budget.tokens:
                    break
                if not key:
                    raise ValueError('BUPT_API_KEY must be available in the authorized process environment')

            def call(name, role, prompt):
                if (name, role) != (ACTION, 'solve'):
                    raise ValueError('unexpected campus action')
                if cached:
                    return replay_case(target, run_digest, budget.rows, prompt)
                target.mkdir(mode=0o700, parents=True)
                before = len(budget.rows)
                with source_relay(target / 'relay', key, budget, gateway, prompt, profile['temperature']) as base:
                    actor = OpenCode(target / 'solve', args.opencode, base, campus.MODEL,
                                     gateway['output'], profile['opencode_context'], profile['temperature'])
                    result = recorded_call(actor, prompt, target, run_digest)
                provider = budget.rows[before:]
                if len(provider) > 1 or budget.pending is not None:
                    raise RuntimeError('one-source campus request limit violated')
                return bind_provider_result(target, run_digest, provider[0] if provider else None, result)

            receipt = {}

            def capture(name, role, prompt):
                result = call(name, role, prompt)
                receipt.update({field: result[field] for field in
                                ('usage', 'elapsed_seconds', 'exit_code', 'finish', 'errors', 'provider_posts')})
                receipt.update(path=(target / 'provider_receipt.json').relative_to(root).as_posix(),
                               cached_this_pass=cached)
                return result

            actions = collect_case(row, gold[row['dataset'], row['id']], [ACTION], capture, args.metric_dir)
            actions[ACTION]['cost'] = action_cost([receipt])
            outcome = {'dataset': row['dataset'], 'id': row['id'], 'report': row['report'],
                       'actions': actions, 'calls': {ACTION: receipt}}
            stream.write(json.dumps(outcome, ensure_ascii=False, allow_nan=False) + '\n')
            completed += 1
            attempted += receipt['provider_posts']
            delivered += bool(receipt['provider_posts'] and not receipt['exit_code'] and not receipt['errors'])
            unknown += receipt['usage'] is None
    if completed == len(public):
        temporary.replace(root / 'outcomes.jsonl')
    posts, debit = charged(budget.rows[first_row:])
    write_json(root / f'collection_{args.batch}.json', {
        'rows': completed, 'panel_rows': len(public), 'complete': completed == len(public),
        'provider_posts': attempted, 'delivered': delivered, 'unknown_provider_usage': unknown,
        'new_calls_this_pass': posts, 'new_gateway_debit_including_unknown': debit,
        'collection_wall_seconds_this_pass': time.monotonic() - started,
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panel', type=Path, required=True)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--namespace', required=True)
    parser.add_argument('--dataset', choices=('finqa', 'tatqa'))
    parser.add_argument('--api-profile', type=Path, required=True)
    parser.add_argument('--api-profile-sha256', required=True)
    parser.add_argument('--batch', required=True)
    parser.add_argument('--max-posts', type=int, required=True)
    parser.add_argument('--token-cap', type=int, required=True)
    parser.add_argument('--prior-charged-tokens', type=int, required=True,
                        help='Historical project charges including unknown reservations before this shared ledger')
    parser.add_argument('--metric-dir', type=Path)
    parser.add_argument('--opencode', type=Path, default=Path.home() / '.opencode/bin/opencode')
    args = parser.parse_args()
    for name in (args.namespace, args.batch):
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]*', name):
            parser.error('namespace and batch must be single directory names')
    if (not re.fullmatch(r'[0-9a-f]{64}', args.api_profile_sha256) or args.max_posts < 1
            or args.token_cap < campus.REQUEST_TOKEN_CEILING
            or not RECORDED_PRIOR_CHARGE <= args.prior_charged_tokens < PROJECT_CAP):
        parser.error('require a profile digest, explicit caps and a reconciled historical charge')
    private = Path.home() / 'wzh/research_evidence'
    if not private.is_dir() or sys.platform != 'linux':
        parser.error('campus collection requires the GB10 research evidence workspace')
    private = private.resolve()
    args.run_dir = args.run_dir.resolve()
    args.panel = args.panel.resolve()
    if not (args.run_dir.is_relative_to(private) and args.panel.is_relative_to(args.run_dir / 'panel')
            and re.fullmatch(r'finance_frontier_benchmark_\d{8}_v\d+', args.run_dir.name)):
        parser.error('use only the current finance benchmark workspace and its generated panels')
    args.opencode = args.opencode.resolve()
    import fcntl
    root = args.run_dir / args.namespace
    root.mkdir(mode=0o700, exist_ok=True)
    with (root / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        collect(args, root, private / '.finance_frontier_campus_budget')


if __name__ == '__main__':
    main()
