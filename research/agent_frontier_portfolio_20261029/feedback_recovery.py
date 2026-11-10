"""Small DEV_ONLY feedback-recovery controller and Astropy paired pilot.

Uses the existing native OpenCode harness and independent Astropy evaluator.
Preparation is model-free; execution requires the frozen plan's SHA-256.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import random
import re
import shutil
import subprocess
import sys
import threading
import time

PRIVATE = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
METHODS = ('ordinary', 'simple', 'fcdr')
CAPS = {'posts': 8, 'seconds': 300, 'context': 65536, 'output': 8192}
SEED = 7201
REVIEW_SHA = '65c1b7f8f3c5f94213942b8546456655a7ff8e71bfc857c69541c67b94e0ac31'
SITES = {
    'A4': ('ccer_target_full_20261110', 58),
    'A5': ('ccer_target_mask_20261110', 52),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def new_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def content_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return '\n'.join(x.get('text', '') for x in value if isinstance(x, dict))
    return ''


def tool_results(messages):
    calls = {}
    for message in messages:
        for call in message.get('tool_calls', []) or []:
            function = call.get('function', {})
            args = function.get('arguments', {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            calls[call.get('id')] = (function.get('name', '').split('.')[-1], args)
        if message.get('role') == 'tool':
            key = message.get('tool_call_id')
            if key in calls:
                name, args = calls[key]
                yield key, name, args, content_text(message.get('content'))


def failure_kind(text):
    # Only apply to executed command output, never to source-file text.
    if re.search(r'(?:^|\n)(?:E\s+)?AttributeError:.*NoneType', text):
        return 'implementation_precondition'
    if re.search(r'(?:^|\n)(?:E\s+)?(?:AttributeError:.*has no attribute|NameError:)', text):
        return 'api_precondition'
    if re.search(r'\b[1-9]\d* failed\b|(?:^|\n)(?:E\s+)?AssertionError:', text):
        return 'test_or_implementation'
    if re.search(r'(?:^|\n)(?:E\s+)?(?:\w*Error:|DeprecationWarning:)', text):
        return 'execution_setup'
    return None


def scope_hashes(work, command, output):
    paths = set(re.findall(r'(?:/root/)?(astropy/[\w./-]+\.py)', command + '\n' + output))
    result = {}
    for rel in sorted(paths)[:12]:
        parts = PurePosixPath(rel)
        if parts.is_absolute() or '..' in parts.parts:
            continue
        path = Path(work) / rel
        if path.is_symlink() or not path.is_file():
            continue
        result[rel] = sha(path)
    return result


class RecoveryController:
    def __init__(self, method, case, seed_feedback):
        if method not in METHODS + ('capture',):
            raise ValueError('unknown recovery method')
        self.method, self.case = method, Path(case)
        self.work = self.case / 'work'
        self.wire = self.case / 'wire'
        self.wire.mkdir(exist_ok=False)
        self.lock = threading.Lock()
        self.index = 0
        self.seen = set()
        self.pending = {}
        self.quiet_rounds = 0
        self.instructions_visible = False
        self.observe('seed-feedback', 'bash', seed_feedback['input'], seed_feedback['output'])

    def observe(self, key, name, args, text):
        if key in self.seen:
            return False
        self.seen.add(key)
        if name != 'bash':
            return False
        command = args.get('command', '')
        kind = failure_kind(text)
        signature = re.sub(r'\s+', ' ', command).strip()
        if kind:
            self.pending[signature] = {
                'kind': kind, 'command': command,
                'scope': scope_hashes(self.work, command, text),
                'summary': text[-1400:],
            }
            return True
        if re.search(r'\b[1-9]\d* passed\b', text) and not re.search(r'\b[1-9]\d* (?:failed|errors?)\b', text):
            self.pending.pop(signature, None)
            return True
        return False

    def advice(self):
        if self.method == 'ordinary':
            return ('Continue the current repair using the available tool feedback. '
                    'Preserve useful work and verify the requested behavior before finishing.')
        if self.method == 'simple':
            return ('Simple recovery rules: check imports or the current API after a missing-name '
                    'or missing-attribute error; inspect the reported implementation frame for a '
                    'runtime error; after changing code rerun the failed checks. Change an empty '
                    'search instead of repeating it. Use current file versions, not old results. '
                    'If diagnosis is ambiguous or reads bring no new evidence, choose one small '
                    'executable probe distinguishing a faulty test from a faulty implementation, '
                    'then edit the implicated artifact.')
        items = []
        for value in self.pending.values():
            changed = any(not (self.work / rel).is_file() or sha(self.work / rel) != digest
                          for rel, digest in value['scope'].items())
            items.append({'kind': value['kind'], 'command': value['command'][:250],
                          'status': 'RETEST_AFTER_RELEVANT_EDIT' if changed else 'UNRESOLVED'})
        latest = items[-1] if items else None
        if latest is None:
            action = 'CONTINUE: use current public task evidence; retain successful work.'
        elif latest['status'].startswith('RETEST'):
            action = 'REVALIDATE: this failure predates a change in a related file; run the relevant check again.'
        elif latest['kind'] == 'api_precondition':
            action = ('QUERY: verify the callable or attribute on the current object/API before changing '
                      'production code. Repair a mistaken probe invocation using the public task contract.')
        elif self.quiet_rounds >= 2:
            action = ('PIVOT: two request rounds supplied no new diagnostic result. Choose one small '
                      'executable probe distinguishing a faulty test from a faulty implementation, '
                      'then edit the implicated artifact; avoid rereading unchanged material.')
        else:
            action = ('QUERY_OR_EDIT: identify the premise contradicted by the current failure; '
                      'use a focused executable check if its origin is ambiguous, then repair it.')
        return ('Feedback recovery state (execution policy, not a task answer):\n'
                + json.dumps({'outstanding': items[-3:], 'next_action': action}, ensure_ascii=False))

    def augment(self, payload):
        with self.lock:
            self.index += 1
            index = self.index
            original = copy.deepcopy(payload)
            forwarded = copy.deepcopy(payload)
            diagnostics = False
            for key, name, args, text in tool_results(payload.get('messages', [])):
                if name == 'read' and args.get('filePath') == '/root/instructions.txt':
                    self.instructions_visible = True
                diagnostics = self.observe(key, name, args, text) or diagnostics
            self.quiet_rounds = 0 if diagnostics else self.quiet_rounds + 1
            # Summarization requests are recorded but are not made into actor decisions.
            injected = bool(payload.get('tools')) and self.instructions_visible and self.method != 'capture'
            if injected:
                forwarded.setdefault('messages', []).append({'role': 'user', 'content': self.advice()})
                if forwarded['messages'][:-1] != original.get('messages', []):
                    raise ValueError('original conversation changed')
            if forwarded.get('tools') != original.get('tools'):
                raise ValueError('tool permissions changed')
            new_json(self.wire / f'request-{index:03d}-received.json', original)
            new_json(self.wire / f'request-{index:03d}-forwarded.json', forwarded)
            new_json(self.wire / f'policy-{index:03d}.json', {
                'method': self.method, 'injected': injected, 'quiet_rounds': self.quiet_rounds,
                'common_feedback_observed_in_tool_result': self.instructions_visible,
                'pending': self.pending, 'original_messages_preserved': True,
            })
            return forwarded, index

    def send(self, upstream, data, index):
        path = self.wire / f'send-{index:03d}.json'
        new_json(path, {'status': 'SENDING', 'bytes': len(data)})
        try:
            upstream.sendall(data)
        except BaseException:
            path.write_text(json.dumps({'status': 'UNCERTAIN_PARTIAL_SEND', 'bytes': len(data)}))
            raise
        path.write_text(json.dumps({'status': 'SENT', 'bytes': len(data)}))


def install_snapshot(directory, work, expected):
    directory, work = Path(directory), Path(work)
    if sha(directory / 'snapshot.json') != expected:
        raise ValueError('recovery snapshot manifest changed')
    data = json.loads((directory / 'snapshot.json').read_text())
    prefix = data.get('project_prefix', 'astropy/')
    if prefix not in ('astropy/', 'sympy/'):
        raise ValueError('unadmitted project prefix')
    for rel, value in data['files'].items():
        p = PurePosixPath(rel)
        if p.is_absolute() or '..' in p.parts or not (rel.startswith(prefix) and rel.endswith('.py')):
            raise ValueError('unsafe recovery path')
        src, dst = directory / 'files' / rel, work / rel
        if sha(src) != value['after'] or (sha(dst) if dst.is_file() else None) != value['before']:
            raise ValueError('recovery source or baseline changed')
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    experience = directory / 'source_experience.md'
    if data.get('experience_sha256'):
        if sha(experience) != data['experience_sha256']:
            raise ValueError('source experience changed')
        shutil.copyfile(experience, work / 'source_experience.md')
    new_json(work.parent / 'recovery_start.json', {
        'snapshot_sha256': expected,
        'files': {rel: sha(work / rel) for rel in data.get('files', {})},
        'experience_sha256': data.get('experience_sha256'),
    })


def instrument(code, root, snapshot, method, replace):
    root, snapshot = Path(root), Path(snapshot)
    manifest_sha = sha(snapshot / 'snapshot.json')
    module_dir = str(Path(__file__).resolve().parent)
    code = replace(code, 'from pathlib import Path',
                   f'from pathlib import Path\nsys.path.insert(0,{module_dir!r})\n'
                   'from feedback_recovery import RecoveryController, install_snapshot')
    anchor = "shutil.copytree(src/'clean_base',work,dirs_exist_ok=True)"
    code = replace(code, anchor, anchor + f'\ninstall_snapshot(Path({str(snapshot)!r}),work,{manifest_sha!r})')
    code = replace(code, "body=(src/'task.txt').read_text(encoding='utf8').strip()",
                   f"body=Path({str(snapshot / 'common_instructions.txt')!r}).read_text(encoding='utf8')")
    anchor = "sockpath=bridge/'model.sock';"
    init = (f"recovery=RecoveryController({method!r},case,json.loads(Path({str(snapshot / 'feedback.json')!r}).read_text()))\n")
    code = replace(code, anchor, init + anchor)
    code = replace(code, 'def relay(a,b):', 'def relay(a,b,response_path=None):')
    anchor = '    (b if x is a else a).sendall(data)'
    code = replace(code, anchor,
                   '    if x is b and response_path is not None:\n'
                   "     with response_path.open('ab') as response_log:response_log.write(data)\n" + anchor)
    anchor = " payload['temperature'],payload['seed']=temperature,seed"
    code = replace(code, anchor, anchor + '\n payload,wire_index=recovery.augment(payload)')
    anchor = " return b'\\r\\n'.join(lines)+b'\\r\\n\\r\\n'+body,metadata,len(body)"
    code = replace(code, anchor, " metadata['wire_index']=wire_index\n" + anchor)
    anchor = '  try:upstream.sendall(first);relay(self.request,upstream)'
    code = replace(code, anchor,
                   "  try:\n"
                   "   if line.startswith(b'POST'):recovery.send(upstream,first,meta['wire_index'])\n"
                   "   else:upstream.sendall(first)\n"
                   "   relay(self.request,upstream,(case/'wire'/('response-%03d.http'%meta['wire_index'])) if line.startswith(b'POST') else None)")
    compile(code, '<feedback-recovery-native-harness>', 'exec')
    return code


def astropy_runtime():
    import run_swe_contextbench_astropy_20261105 as astro
    return astro


def component_hashes(astro):
    modules = (astro, astro.core, astro.requests_runner, astro.qual, astro.shared,
               astro.actor_dependencies, astro.tool_runtime_module)
    return {str(Path(x.__file__).resolve()): sha(x.__file__) for x in modules}


def wire_summary(case, snapshot_sha):
    """Verify actual forwarding and intervention delivery before the next arm."""
    wire = Path(case) / 'wire'
    sends = [json.loads(p.read_text()) for p in sorted(wire.glob('send-*.json'))]
    policies = [json.loads(p.read_text()) for p in sorted(wire.glob('policy-*.json'))]
    start = json.loads((Path(case) / 'recovery_start.json').read_text())
    faults = []
    if start['snapshot_sha256'] != snapshot_sha:
        faults.append('SNAPSHOT_IDENTITY')
    if not any(p['injected'] and p['common_feedback_observed_in_tool_result'] for p in policies):
        faults.append('NO_DELIVERED_POLICY')
    if any(p['status'] != 'SENT' for p in sends):
        faults.append('UNCERTAIN_UPSTREAM_SEND')
    for path in sorted(wire.glob('response-*.http')):
        first = path.open('rb').readline().decode('ascii', errors='replace').strip()
        if not re.match(r'HTTP/\d(?:\.\d)? 200\b', first):
            faults.append('UPSTREAM_STATUS:' + first[:80])
    if len(list(wire.glob('response-*.http'))) != len(sends):
        faults.append('MISSING_UPSTREAM_RESPONSE')
    if not sends or len(sends) > CAPS['posts']:
        faults.append('UPSTREAM_REQUEST_COUNT')
    return {'sent_posts': sum(p['status'] == 'SENT' for p in sends),
            'uncertain_posts': sum(p['status'] != 'SENT' for p in sends),
            'injected_requests': sum(p['injected'] for p in policies), 'faults': faults}


def prepare(root):
    astro = astropy_runtime()
    root = Path(root).resolve()
    if root.parent != PRIVATE or root.exists():
        raise ValueError('use a new direct child of the private research directory')
    review_path = PRIVATE / 'fcdr_feedback_review_v1.json'
    if sha(review_path) != REVIEW_SHA:
        raise ValueError('feedback review changed')
    astro.preflight('target')  # Read-only verification; no new controls or model probes.
    review = json.loads(review_path.read_text())
    root.mkdir()
    snapshots = {}
    for site, (attempt, line_number) in SITES.items():
        name = 'astro-full32k' if site == 'A4' else 'astro-masked32k'
        old = Path(review['cases'][name]['path'])
        if sha(old / 'raw.jsonl') != review['cases'][name]['raw_sha256']:
            raise ValueError('historical trace changed')
        events = [(i, json.loads(s)) for i, s in enumerate((old / 'raw.jsonl').read_text().splitlines(), 1)]
        node = next(d for i, d in events if i == line_number)
        later = [d['part']['tool'] for i, d in events if i > line_number and d.get('type') == 'tool_use']
        if any(name not in ('read', 'grep', 'glob', 'list') for name in later):
            raise ValueError('later mutations prevent final-work snapshot reuse')
        snap = root / 'snapshots' / site
        snap.mkdir(parents=True)
        clean = astro.qual.OUT / 'target/clean_base'
        files = {}
        for src in sorted((old / 'work/astropy').rglob('*.py')):
            rel = src.relative_to(old / 'work').as_posix()
            if rel == 'astropy/_version.py':
                continue
            before = clean / rel
            before_sha = sha(before) if before.is_file() else None
            if sha(src) == before_sha:
                continue
            if src.is_symlink():
                raise ValueError('unexpected source link')
            dst = snap / 'files' / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            files[rel] = {'before': before_sha, 'after': sha(dst)}
        experience = old / 'work/source_experience.md'
        if experience.is_file():
            shutil.copyfile(experience, snap / 'source_experience.md')
        feedback = {'input': node['part']['state']['input'], 'output': node['part']['state']['output']}
        new_json(snap / 'feedback.json', feedback)
        public_task = (old / 'frozen_instructions.txt').read_text()
        common = (public_task + '\n\nRecovery from an existing candidate, not from the original baseline. '
                  'The current files retain the previous implementation and self-authored tests. '
                  'Do not discard them wholesale. A previous source record, if present, is at '
                  '/root/source_experience.md. The last executed command and its actual output were:\n'
                  + '\nCommand:\n' + feedback['input']['command']
                  + '\n\nReturned output:\n' + feedback['output']
                  + '\nA self-authored assertion is evidence about that probe, not an independent task oracle. '
                    'Do not change an expected value solely to make a test pass. '
                    'Continue the task using public files and tools.\n')
        if max(map(len, common.splitlines())) > 1800:
            raise ValueError('common feedback would be truncated by the read tool')
        (snap / 'common_instructions.txt').write_text(common, encoding='utf-8')
        record = {'site': site, 'old_trace_sha256': sha(old / 'raw.jsonl'), 'feedback_line': line_number,
                  'later_tools_read_only': later, 'files': files,
                  'experience_sha256': sha(experience) if experience.is_file() else None,
                  'feedback_sha256': sha(snap / 'feedback.json'),
                  'common_instructions_sha256': sha(snap / 'common_instructions.txt')}
        new_json(snap / 'snapshot.json', record)
        snapshots[site] = {'path': str(snap), 'sha256': sha(snap / 'snapshot.json')}
    order = [(site, method) for site in SITES for method in METHODS]
    random.Random(SEED).shuffle(order)
    episodes = []
    for site, method in order:
        parent = root / (site + '__' + method)
        parent.mkdir()
        (parent / 'runtime').mkdir()
        snap = Path(snapshots[site]['path'])
        code = astro.derive(parent, 'target', 'none', None, seed=SEED,
                            max_posts=CAPS['posts'], max_seconds=CAPS['seconds'],
                            context_limit=CAPS['context'], output_limit=CAPS['output'])
        code = instrument(code, parent, snap, method, astro.core.replace_once)
        harness = parent / 'harness.py'
        harness.write_text(code, encoding='utf-8')
        episodes.append({'site': site, 'method': method, 'parent': str(parent),
                         'harness_sha256': sha(harness), 'snapshot': snapshots[site]})
    plan = {'schema': 'fcdr_recovery_pilot_v1', 'status': 'PREPARED_DEV_ONLY', 'seed': SEED,
            'caps_per_episode': CAPS, 'max_total_posts': 48, 'episodes': episodes,
            'script_sha256': sha(__file__), 'astropy_runner_sha256': sha(astro.__file__),
            'component_sha256': component_hashes(astro),
            'hypothesis': 'stateful feedback-scoped recovery improves on ordinary and simple recovery',
            'comparison_unit': 'two exposed states of one Astropy task; not independent tasks',
            'new_model_requests': 0}
    new_json(root / 'PLAN.json', plan)
    return {'plan': str(root / 'PLAN.json'), 'sha256': sha(root / 'PLAN.json'), 'episodes': len(episodes)}


def execute(root, expected, limit=None):
    import fcntl
    astro = astropy_runtime()
    root = Path(root).resolve()
    if root.parent != PRIVATE or sha(root / 'PLAN.json') != expected:
        raise ValueError('plan identity differs')
    plan = json.loads((root / 'PLAN.json').read_text())
    if sha(__file__) != plan['script_sha256'] or component_hashes(astro) != plan['component_sha256']:
        raise ValueError('implementation changed after preparation')
    with (root / 'owner.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        results = []
        newly_run = 0
        for ep in plan['episodes']:
            parent = Path(ep['parent'])
            result_path = parent / 'RESULT.json'
            case = parent / f'target__none__seed{SEED}'
            if result_path.exists():
                previous = json.loads(result_path.read_text())
                if previous['plan_sha256'] != expected or previous['harness_sha256'] != ep['harness_sha256']:
                    raise ValueError('completed attempt identity changed')
                if previous.get('raw_sha256') and sha(case / 'raw.jsonl') != previous['raw_sha256']:
                    raise ValueError('completed trace changed')
                results.append(previous)
                if previous.get('status'):
                    raise ValueError('prior infrastructure fault requires review, not automatic retry')
                continue
            if limit is not None and newly_run >= limit:
                break
            if (parent / 'STARTED.json').exists():
                raise ValueError('existing attempt is preserved; do not restart automatically')
            if sha(parent / 'harness.py') != ep['harness_sha256']:
                raise ValueError('prepared harness changed')
            new_json(parent / 'STARTED.json', {**ep, 'plan_sha256': expected, 'start_unix': time.time()})
            process = subprocess.Popen([sys.executable, str(parent / 'harness.py'), 'target', 'no_skill'],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            outer_timeout = False
            try:
                stdout, stderr = process.communicate(timeout=CAPS['seconds'] + 120)
            except subprocess.TimeoutExpired:
                outer_timeout = True
                name = f'agent-skill-{process.pid}'
                info = subprocess.run(['docker', 'inspect', name], capture_output=True)
                if info.returncode == 0:
                    mounts = json.loads(info.stdout)[0].get('Mounts', [])
                    if any(x.get('Source') == str(case / 'work') for x in mounts):
                        subprocess.run(['docker', 'kill', name], capture_output=True, timeout=20)
                process.kill()
                stdout, stderr = process.communicate(timeout=30)
            (parent / 'launcher.stdout').write_bytes(stdout)
            (parent / 'launcher.stderr').write_bytes(stderr)
            result = {**ep, 'launcher_exit': process.returncode, 'plan_sha256': expected,
                      'outer_timeout': outer_timeout}
            if (case / 'receipt.json').is_file():
                receipt = json.loads((case / 'receipt.json').read_text())
                if sha(case / 'raw.jsonl') != receipt['raw_sha256']:
                    raise ValueError('actor trace changed')
                tokens = receipt.get('step_finish_tokens', [])
                result.update(agent_exit=receipt['agent_exit'],
                              posts=sum(x.startswith('POST ') for x in receipt['model_http_requests']),
                              reported_tokens=sum(x.get('total', 0) for x in tokens),
                              input=sum(x.get('input', 0) for x in tokens),
                              output=sum(x.get('output', 0) for x in tokens),
                              cache_read=sum(x.get('cache', {}).get('read', 0) for x in tokens),
                              raw_sha256=receipt['raw_sha256'], evaluation=astro.evaluate('target', case))
                result['wire'] = wire_summary(case, ep['snapshot']['sha256'])
                if result['wire']['faults'] or outer_timeout:
                    result['status'] = 'INFRASTRUCTURE_FAULT_REQUIRES_REVIEW'
            else:
                result['status'] = 'HARNESS_FAILURE_REQUIRES_REVIEW'
            new_json(result_path, result)
            results.append(result)
            newly_run += 1
            progress = {k: result.get(k) for k in ('site', 'method', 'posts', 'reported_tokens', 'agent_exit', 'status')}
            progress['score_exits'] = {k: result.get('evaluation', {}).get(k, {}).get('exit')
                                       for k in ('focus', 'regression', 'issue_probe')}
            print(json.dumps(progress), flush=True)
            if result.get('status'):
                break
        new_json(root / f'RESULTS_{len(results):02d}.json',
                 {'plan_sha256': expected, 'results': results, 'training': 0})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--plan-sha')
    parser.add_argument('--episode-limit', type=int, help='Run this many new episodes; completed attempts are verified and skipped.')
    args = parser.parse_args()
    if args.prepare:
        print(json.dumps(prepare(args.root)))
    elif not args.plan_sha:
        parser.error('execution requires --plan-sha')
    else:
        if args.episode_limit is not None and args.episode_limit < 1:
            parser.error('episode limit must be positive')
        execute(args.root, args.plan_sha, args.episode_limit)


if __name__ == '__main__':
    main()
