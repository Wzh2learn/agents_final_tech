"""CPU engineering controls only: synthetic sources and fake socket pairs, no model evidence."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'
sys.path.insert(0, str(HERE))
import run_contextbench_source as m
import qualify_contextbench_pool as pool
import run_alfworld_actor_20261106 as actor
import run_django_aggregation_agent_20261106 as agg
from scripts.graph import research_actor_dependencies as deps


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value))
    return m.sha(path)


@pytest.fixture
def prepared_inputs(tmp_path, monkeypatch):
    """Synthetic metadata/projection; real tree/hash and projection verification."""
    private = tmp_path / 'private'; private.mkdir(); monkeypatch.setattr(m, 'PRIVATE', private)
    result_root = private / 'qualification'; result_root.mkdir(); cases = {}; rows = []; sources = dict(m.SOURCES)
    projection = private / 'projection'; (projection / 'runtime/bin').mkdir(parents=True)
    (projection / 'runtime/bin/python').write_text('synthetic CPU control, not executable')
    (projection / 'deps/default').mkdir(parents=True)
    (projection / 'deps/default/asgiref.py').write_text('synthetic third party')
    dep_manifest = dict(version=1, python='3.8', blocked_packages=['django'], site_names=['default'],
        source_site_paths={'default': str(private / 'swe_contextbench_django_env_20261104/site')}, files={name: dict(sha256=digest, bytes=(projection/name).stat().st_size) for name, digest in m.tree(projection).items()})
    dep_sha = write_json(projection / 'manifest.json', dep_manifest)
    sources['django__django-12453'] = (*sources['django__django-12453'][:-1], dep_sha); monkeypatch.setattr(m, 'SOURCES', sources)
    for source, (repo, base, target, count, _) in sources.items():
        root = result_root / source; clean = root / 'clean_base'; (clean / 'tests').mkdir(parents=True)
        (clean / 'module.py').write_text('value = 0\n'); (clean / 'tests/test_public.py').write_text('assert True\n')
        task = root / 'task.txt'; task.write_text('Public author suggestion diff is allowed.\n')
        patch = root / 'test.patch'; patch.write_text('synthetic evaluator-only tests')
        cases[source] = dict(spec=dict(instance_id=source, repo=repo, base_commit=base, role='source', related_target_id=target),
            qualification=dict(qualified=True), labels=dict(f2p=['test.fail'], ptp=['test.pass' + str(i) for i in range(count)]),
            clean_base_sha256=m.tree(clean), input_sha256={'task.txt': m.sha(task), 'test.patch': m.sha(patch)})
        rows.append(dict(source=source, target=target, clean_base=str(clean)))
    receipt = result_root / 'receipt.json'; digest = write_json(receipt, dict(status='QUALIFIED', model_calls=0, cases=cases))
    monkeypatch.setattr(m, 'RESULT_SHA', digest)
    registry = private / 'registry.json'; registry_sha = write_json(registry, dict(schema='qualified_source_target_pairs_v1', source_result=dict(path=str(receipt), sha256=digest), rows=rows))
    monkeypatch.setattr(m, 'REGISTRY_SHA', registry_sha)
    profile = private / 'profile.json'; profile_sha = write_json(profile, dict(model_id='qwen38-27b-fp8', context=32768, output=8192, host='127.0.0.1', port=1))
    monkeypatch.setattr(m, 'PROFILE_SHA', profile_sha)
    binaries = private / 'bin'; binaries.mkdir()
    for name in ('opencode', 'rg'): (binaries / name).write_text('synthetic tool')
    def forbidden(*_, **__): raise AssertionError('prepare must not execute or inspect a backend')
    h = SimpleNamespace(actor=actor, agg=agg, deps=deps, pool=pool,
        teacher=SimpleNamespace(_vllm_profile_fields=lambda _: None, validate_vllm_model_profile=forbidden, verify_vllm_backend=forbidden),
        tools=SimpleNamespace(OPENCODE=binaries / 'opencode', RG=binaries / 'rg', ripgrep_binding=lambda: []))
    monkeypatch.setattr(m, 'helpers', lambda: h)
    monkeypatch.setattr(m, 'scoring_dependencies', lambda *_: dict(bindings={}, limits='synthetic CPU dependency control'))
    return SimpleNamespace(private=private, root=private / 'attempt', registry=registry, registry_sha=registry_sha,
        source='django__django-12453', projection=projection, projection_sha=dep_sha, profile=profile, profile_sha=profile_sha, h=h,
        receipt=receipt, cases=cases)


def prepare(f):
    return m.prepare(f.registry, f.registry_sha, f.source, f.root, f.projection, f.projection_sha, f.profile, f.profile_sha)


def test_prepare_has_zero_process_endpoint_and_verbatim_public_input(prepared_inputs, monkeypatch):
    f = prepared_inputs
    def forbidden(*_, **__): raise AssertionError('CPU prepare crossed execution boundary')
    monkeypatch.setattr(subprocess, 'Popen', forbidden); monkeypatch.setattr(socket, 'create_connection', forbidden)
    result = prepare(f); manifest, _, _, _ = m.verify(f.root, result['manifest_sha256'])
    assert result['status'] == 'CPU_PREPARED'
    assert manifest['models_called'] == manifest['container_runs'] == 0
    original = f.receipt.parent / f.source / 'task.txt'
    assert (f.root / 'inputs/source_task.txt').read_bytes() == original.read_bytes()
    assert (f.root / 'inputs/task.txt').read_text().endswith(original.read_text())
    assert manifest['public_task_sha256'] == m.sha(original)
    assert manifest['wrapped_prompt_sha256'] != manifest['public_task_sha256']
    assert not (f.root / 'work/test.patch').exists() and not (f.root / 'inputs/reference.patch').exists()
    assert set(manifest['components']) and manifest['baseline'] == manifest['work']
    assert not (f.root / 'reservation.json').exists()


@pytest.mark.parametrize('change', ['target', 'hash', 'hardlink', 'symlink'])
def test_reject_wrong_identity_and_linked_clean_before_root(prepared_inputs, change):
    f = prepared_inputs
    if change == 'target': f.source = 'django__django-31051'
    elif change == 'hash': f.registry_sha = '0' * 64
    else:
        clean = f.receipt.parent / f.source / 'clean_base'
        if change == 'hardlink': os.link(clean / 'module.py', clean / 'alias.py')
        else: (clean / 'alias.py').symlink_to(clean / 'module.py')
    with pytest.raises(ValueError): prepare(f)
    assert not f.root.exists()


def test_wrong_profile_and_target_injection_rejected(prepared_inputs):
    f = prepared_inputs; f.profile_sha = '0' * 64
    with pytest.raises(ValueError, match='profile'): prepare(f)
    f.profile_sha = m.PROFILE_SHA; result = prepare(f)
    (f.root / 'inputs/task.txt').write_text('django__django-31051 target must not be introduced')
    with pytest.raises(ValueError, match='inputs'): m.verify(f.root, result['manifest_sha256'])


def test_projection_must_match_qualified_source_site(prepared_inputs, monkeypatch):
    f = prepared_inputs; manifest_path = f.projection / 'manifest.json'; v = json.loads(manifest_path.read_text())
    v['source_site_paths']['default'] = str(f.private / 'other-site'); f.projection_sha = write_json(manifest_path, v)
    sources = dict(m.SOURCES); sources[f.source] = (*sources[f.source][:-1], f.projection_sha); monkeypatch.setattr(m, 'SOURCES', sources)
    with pytest.raises(ValueError, match='qualified dependency'): prepare(f)
    assert not f.root.exists()


def test_actor_mounts_exact_source_surface_and_reject_ancestor(prepared_inputs):
    f = prepared_inputs; result = prepare(f); manifest, h, projection, profile = m.verify(f.root, result['manifest_sha256'])
    bridge = f.private / 'bridge'; bridge.mkdir()
    command = m.docker_command(f.root, projection, bridge, profile, h, 'fake-control')
    mounts = [command[i+1] for i, word in enumerate(command) if word == '--mount']
    assert len(mounts) == 7
    assert {v.split('dst=')[1].split(',')[0] for v in mounts} == {'/workspace', '/inputs', '/extra', '/deps', '/model', '/opt/opencode', '/usr/local/bin/rg'}
    assert command[command.index('--network')+1] == 'none' and '--read-only' in command
    assert str(f.receipt.parent) not in ' '.join(mounts) and '--privileged' not in command
    assert command[command.index('--user')+1] != '0:0'
    projection['runtime'] = str(f.root)
    with pytest.raises(ValueError, match='ancestor'): m.docker_command(f.root, projection, bridge, profile, h, 'fake')


def wire_payload(client, payload):
    body = json.dumps(payload).encode()
    client.sendall(b'POST /v1/chat/completions HTTP/1.1\r\nContent-Length: ' + str(len(body)).encode() + b'\r\n\r\n' + body)


def fake_upstream(monkeypatch):
    """Socket pairs only, no listening endpoint; capture the actual serialized POST."""
    bodies = []; workers = []
    def connect(*_, **__):
        sender, receiver = socket.socketpair()
        def respond():
            data = b''
            while b'\r\n\r\n' not in data: data += receiver.recv(65536)
            head, body = data.split(b'\r\n\r\n', 1)
            size = int(next(l.split(b':', 1)[1] for l in head.split(b'\r\n') if l.startswith(b'Content-Length:')))
            while len(body) < size: body += receiver.recv(size-len(body))
            bodies.append(body)
            response = b'data: {"usage":{"total_tokens":7}}\n\ndata: [DONE]\n\n'
            receiver.sendall(b'HTTP/1.1 200 OK\r\nContent-Length: ' + str(len(response)).encode() + b'\r\n\r\n' + response); receiver.close()
        worker = threading.Thread(target=respond); worker.start(); workers.append(worker); return sender
    monkeypatch.setattr(socket, 'create_connection', connect)
    return bodies, workers


def exchange(relay, payload=None):
    client, receiver = socket.socketpair(); client.settimeout(5)
    worker = threading.Thread(target=relay.handle, args=(receiver,)); worker.start()
    wire_payload(client, {'messages': [{'role': 'user', 'content': 'synthetic CPU control'}]} if payload is None else payload)
    data = b''
    while True:
        piece = client.recv(65536)
        if not piece: break
        data += piece
    client.close(); worker.join(5); assert not worker.is_alive(); return data


def relay_at(tmp_path, caps=None):
    return m.Relay(tmp_path, dict(host='127.0.0.1', port=1, model_id='qwen38-27b-fp8', output=8192),
        SimpleNamespace(actor=actor, agg=agg), deadline=time.monotonic()+10, caps=caps)


def test_fake_wire_exact_payload_and_concurrent_actual_post_cap(tmp_path, monkeypatch):
    bodies, upstreams = fake_upstream(monkeypatch); relay = relay_at(tmp_path, dict(posts=2, seconds=10, combined_wire_bytes=100000))
    responses = []; workers = [threading.Thread(target=lambda: responses.append(exchange(relay))) for _ in range(5)]
    for w in workers: w.start()
    for w in workers: w.join(5); assert not w.is_alive()
    for w in upstreams: w.join(5)
    bill = relay.accounting(); assert len(bodies) == bill['actual_forwarded_posts'] == 2
    assert sum(r.startswith(b'HTTP/1.1 403') for r in responses) == 3
    events = [json.loads(l) for l in (tmp_path / 'forward_ledger.jsonl').read_text().splitlines()]
    stored = [(tmp_path / 'wire' / f'{e["request"]:05d}.request.json').read_bytes() for e in events if e['event'] == 'forwarded']
    assert sorted(stored) == sorted(bodies)
    assert bill['actual_forwarded_body_bytes'] == sum(map(len, bodies)) and bill['provider_total_tokens_known'] == 14
    value = json.loads(bodies[0]); assert (value['seed'], value['temperature'], value['max_tokens'], value['chat_template_kwargs']) == (17, .2, 8192, {'enable_thinking': False})


def test_connection_failure_is_not_forwarded_or_billed_then_retry_can_send(tmp_path, monkeypatch):
    relay = relay_at(tmp_path, dict(posts=1, seconds=10, combined_wire_bytes=100000))
    def refused(*_, **__): raise ConnectionRefusedError('fake endpoint')
    monkeypatch.setattr(socket, 'create_connection', refused); assert exchange(relay).startswith(b'HTTP/1.1 502')
    bill = relay.accounting(); assert bill['actual_forwarded_posts'] == bill['actual_forwarded_body_bytes'] == bill['budget_reserved_combined_wire_bytes'] == 0
    bodies, workers = fake_upstream(monkeypatch); assert exchange(relay).startswith(b'HTTP/1.1 200')
    for w in workers: w.join(5)
    assert len(bodies) == relay.accounting()['actual_forwarded_posts'] == 1
    assert relay.accounting()['integrity_passed'] is False


@pytest.mark.parametrize('payload', [[], {'temperature': float('nan')}])
def test_malformed_projection_payload_fails_before_send(tmp_path, monkeypatch, payload):
    def forbidden(*_, **__): raise AssertionError('must fail before send')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    # model_payload overwrites temperature; put NaN in an untouched field.
    if isinstance(payload, dict): payload = {'messages': [float('nan')]}
    relay = relay_at(tmp_path); assert exchange(relay, payload).startswith(b'HTTP/1.1 502')
    assert relay.accounting()['actual_forwarded_posts'] == 0


def test_uncertain_partial_send_is_preserved_and_consumes_cap(tmp_path, monkeypatch):
    class Broken:
        def settimeout(self, _): pass
        def sendall(self, _): raise OSError('fake partial send; extent unknown')
        def close(self): pass
    monkeypatch.setattr(socket, 'create_connection', lambda *_, **__: Broken())
    relay = relay_at(tmp_path, dict(posts=1, seconds=10, combined_wire_bytes=100000))
    assert exchange(relay).startswith(b'HTTP/1.1 502')
    assert exchange(relay).startswith(b'HTTP/1.1 403')
    bill = relay.accounting(); assert bill['uncertain_partial_sends'] == 1 and bill['actual_forwarded_posts'] == 0
    assert bill['budget_reserved_combined_wire_bytes'] > 0 and bill['actual_forwarded_body_bytes'] == 0


def test_stop_owned_rejects_unknown_identity_without_rm(tmp_path, monkeypatch):
    cid = tmp_path / 'cid'; cid.write_text('a'*64); calls = []
    def run(cmd, **_): calls.append(cmd); return SimpleNamespace(returncode=0, stdout=b'"/someone-else"', stderr=b'')
    monkeypatch.setattr(subprocess, 'run', run)
    with pytest.raises(ValueError, match='ownership'): m.stop_owned(cid, 'ours')
    assert len(calls) == 1 and calls[0][:2] == ['docker', 'inspect']


@pytest.mark.parametrize('fault', [None, subprocess.TimeoutExpired('fake-owned-docker', 1), KeyboardInterrupt(), InterruptedError('fake SIGTERM')])
def test_owned_run_preserves_raw_and_cleans_exact_cid_on_all_exits(tmp_path, monkeypatch, fault):
    calls = []; cid = tmp_path / 'cid'; cid.write_text('a'*64)
    class Process:
        returncode = 0
        def __init__(self, cmd, **kwargs): kwargs['stdout'].write(b'{"type":"text"}\n'); self.waits = 0
        def wait(self, **_):
            self.waits += 1
            if fault is not None and self.waits == 1: self.returncode = None; raise fault
            self.returncode = 0; return 0
        def poll(self): return self.returncode
        def kill(self): raise AssertionError('fake process already collected')
    def cleanup(path, name): calls.append((path, name)); return {'cid': 'a'*64, 'name': name}
    monkeypatch.setattr(subprocess, 'Popen', Process); monkeypatch.setattr(m, 'stop_owned', cleanup)
    stdout, stderr = tmp_path / 'raw', tmp_path / 'stderr'
    record = m.run_owned(['fake-owned-docker'], 'ours', cid, stdout, stderr, 1)
    assert calls == [(cid, 'ours')] and stdout.read_bytes() == b'{"type":"text"}\n'
    assert bool(record.get('error')) == (fault is not None)
    assert record['stdout_sha256'] == m.sha(stdout)


def test_existing_lock_is_nonblocking_and_missing_lock_not_created(tmp_path, monkeypatch):
    lock = tmp_path / 'model_resource.lock'; monkeypatch.setattr(m, 'LOCK', lock)
    with pytest.raises(FileNotFoundError):
        with m.resource_lock(): pass
    assert not lock.exists(); lock.write_text('existing owner record')
    with m.resource_lock():
        with pytest.raises(BlockingIOError):
            with m.resource_lock(): pass
    assert lock.read_text() == 'existing owner record'


@pytest.mark.parametrize('state', ['passed', 'failed', 'xfailed', 'xpassed', 'skipped', 'missing'])
def test_candidate_scoring_never_accepts_nonpass_or_missing(tmp_path, monkeypatch, state):
    (tmp_path / 'baseline/tests').mkdir(parents=True); (tmp_path / 'baseline/tests/test_a.py').write_text('public tests')
    (tmp_path / 'work/tests').mkdir(parents=True); (tmp_path / 'work/tests/test_a.py').write_text('actor modified tests')
    (tmp_path / 'scoring').mkdir(); (tmp_path / 'scoring/test.patch').write_text('frozen source test patch')
    def tests(candidate, repo, labels, runner, output, suite, h):
        assert (candidate / 'tests/test_a.py').read_text() == 'public tests'
        record = dict(exit=0 if state=='passed' else 1, result=dict(tests={} if state=='missing' else {n: state for n in labels}, fatal=[]))
        record['coverage'] = pool.classify(labels, record); return record
    monkeypatch.setattr(m, 'scored_test', tests)
    h = SimpleNamespace(pool=SimpleNamespace(helpers=lambda: (SimpleNamespace(apply_patch=lambda *_: dict(check_exit=0, apply_exit=0)), None), RUNNER='synthetic test runner'))
    result = m.score(tmp_path, dict(repo='django/django', labels=dict(f2p=['a'], ptp=['b'])), h)
    assert result['passed'] is (state == 'passed')


@pytest.mark.parametrize('error', [None, {'name':'UnknownError'}, {'name':'APIError', 'data':{'statusCode':409}}])
def test_zero_exit_stop_or_opaque_error_never_becomes_success(tmp_path, error):
    raw = tmp_path / 'raw'
    raw.write_text(json.dumps({'type':'tool_use','part':{'state':{'error':'ordinary tool feedback'}}})+'\n'+
        (json.dumps({'type':'error','error':error})+'\n' if error else ''))
    result = dict(status='ACTOR_RETURNED', actor_exit=0, raw_errors=m.raw_errors(raw), actor={},
        accounting=dict(integrity_passed=True, actual_forwarded_posts=1), scoring=dict(passed=True))
    assert m.successful(result) is (error is None)
    result['actor_exit'] = 137; assert m.successful(result) is False

def test_deadline_rechecked_after_connect_before_any_wire_post(tmp_path, monkeypatch):
    relay = relay_at(tmp_path); sent = []
    class Delayed:
        def sendall(self, data): sent.append(data)
        def settimeout(self, _): pass
        def makefile(self, *_): raise OSError('must never reach response parsing')
        def close(self): pass
    def connect(*_, **__): relay.deadline = time.monotonic() - 1; return Delayed()
    monkeypatch.setattr(socket, 'create_connection', connect)
    exchange(relay)
    assert sent == [] and relay.accounting()['actual_forwarded_posts'] == 0


def test_response_wire_cap_keeps_known_request_and_unknown_response_usage(tmp_path, monkeypatch):
    bodies, workers = fake_upstream(monkeypatch)
    # Request fits, but the received response cannot be forwarded within the ceiling.
    relay = relay_at(tmp_path, dict(posts=1, seconds=10, combined_wire_bytes=250))
    exchange(relay)
    for w in workers: w.join(5)
    bill = relay.accounting()
    assert bill['actual_forwarded_posts'] == 1 and bill['actual_forwarded_body_bytes'] == len(bodies[0])
    assert bill['unknown_usage_requests'] == [1] and bill['provider_total_tokens_known'] == 0
    assert bill['budget_reserved_combined_wire_bytes'] <= 250 and bill['integrity_passed'] is False


def test_changed_component_binding_fails_verification(prepared_inputs):
    f = prepared_inputs; prepare(f); path = f.root / 'manifest.json'; manifest = json.loads(path.read_text())
    manifest['components'][str(Path(m.__file__).resolve())] = '0' * 64
    digest = write_json(path, manifest)
    with pytest.raises(ValueError, match='source/tool'): m.verify(f.root, digest)

@pytest.mark.parametrize('fault_type', ['KeyboardInterrupt', 'InterruptedError', 'TimeoutExpired'])
def test_execute_fault_closes_without_starting_new_scorer(prepared_inputs, monkeypatch, fault_type):
    """Engineering lifecycle simulation; no server, Docker, backend or source outcome."""
    from contextlib import contextmanager
    f = prepared_inputs; digest = prepare(f)['manifest_sha256']; order = []
    @contextmanager
    def locked(): order.append('lock'); yield
    monkeypatch.setattr(m, 'resource_lock', locked)
    def validate(*_, **kwargs):
        assert order == ['lock'] and kwargs == {'full': True}; order.append('weights')
    f.h.teacher.validate_vllm_model_profile = validate
    f.h.teacher.verify_vllm_backend = lambda _: dict(fake_engineering_backend=True)
    class FakeServer:
        def __init__(self, path, handler): Path(path).write_text('fake owned socket artifact')
        def serve_forever(self): pass
        def server_close(self): pass
        def shutdown(self): pass
    monkeypatch.setattr(m.socketserver, 'ThreadingUnixStreamServer', FakeServer)
    def collected(cmd, name, cid, stdout, stderr, timeout):
        stdout.write_text('{"type":"text"}\n'); stderr.write_text('')
        return dict(exit=None, error=dict(type=fault_type, message='fake engineering interruption'), cleanup=dict(fake=True))
    monkeypatch.setattr(m, 'run_owned', collected)
    def no_scoring(*_): raise AssertionError('a stopped actor must not launch a scorer')
    monkeypatch.setattr(m, 'score', no_scoring)
    result = m.execute(f.root, digest, f.registry, f.registry_sha, f.source)
    assert result['status'] == ('RUNTIME_ERROR' if fault_type == 'TimeoutExpired' else 'INTERRUPTED')
    assert result['source_success'] is False and 'scoring' not in result
    assert 'finalization_error' not in result and (f.root / 'receipt.json').is_file()
    assert result['accounting']['actual_forwarded_posts'] == 0


def test_busy_resource_refuses_before_reservation_or_live_validation(prepared_inputs, monkeypatch):
    from contextlib import contextmanager
    f = prepared_inputs; digest = prepare(f)['manifest_sha256']
    @contextmanager
    def busy(): raise BlockingIOError('synthetic existing model owner'); yield
    monkeypatch.setattr(m, 'resource_lock', busy)
    with pytest.raises(BlockingIOError): m.execute(f.root, digest, f.registry, f.registry_sha, f.source)
    assert not (f.root / 'reservation.json').exists() and not (f.root / 'receipt.json').exists()


def test_close_rejects_connection_that_returns_after_shutdown(tmp_path, monkeypatch):
    """Fake delayed connect: close must prohibit its later first POST."""
    relay = relay_at(tmp_path); connecting = threading.Event(); release = threading.Event(); frames = []
    class LateSocket:
        closed = False
        def settimeout(self, _): pass
        def sendall(self, data): frames.append(data); raise OSError('fake attempted send after close')
        def shutdown(self, _): self.closed = True
        def close(self): self.closed = True
    upstream = LateSocket()
    def connect(*_, **__):
        connecting.set(); assert release.wait(3); return upstream
    monkeypatch.setattr(socket, 'create_connection', connect)
    client, receiver = socket.socketpair(); worker = threading.Thread(target=relay.handle, args=(receiver,))
    worker.start(); wire_payload(client, {'messages': []})
    try:
        assert connecting.wait(3); relay.close(); release.set(); worker.join(3)
        assert not worker.is_alive() and upstream.closed and frames == []
        bill = relay.accounting()
        assert bill['actual_forwarded_posts'] == bill['uncertain_partial_sends'] == bill['budget_reserved_combined_wire_bytes'] == 0
        assert bill['integrity_passed'] is False
    finally: release.set(); client.close(); worker.join(3)


def test_close_cannot_cross_check_and_actual_send_boundary(tmp_path, monkeypatch):
    """Fake attribute gate pauses between guard evaluation and calling sendall."""
    relay = relay_at(tmp_path); ready = threading.Event(); decision = threading.Event(); close_done = threading.Event()
    frame_after_close = []; probe = []
    class GatedSocket:
        closed = False
        def settimeout(self, _): pass
        @property
        def sendall(self):
            ready.set(); assert decision.wait(3); return self.write_fragment
        def write_fragment(self, packet):
            frame_after_close.append(self.closed)
            raise OSError('fake partial send; bill extent remains unknown')
        def shutdown(self, _): self.closed = True
        def close(self): self.closed = True
    upstream = GatedSocket(); monkeypatch.setattr(socket, 'create_connection', lambda *_, **__: upstream)
    def closer():
        assert ready.wait(3)
        acquired = relay.lock.acquire(blocking=False); probe.append(acquired)
        if acquired:
            try: relay.close()
            finally: relay.lock.release()
            decision.set()
        else:
            decision.set(); relay.close()
        close_done.set()
    close_worker = threading.Thread(target=closer); close_worker.start()
    client, receiver = socket.socketpair(); worker = threading.Thread(target=relay.handle, args=(receiver,))
    worker.start(); wire_payload(client, {'messages': []})
    try:
        worker.join(3); close_worker.join(3)
        assert not worker.is_alive() and not close_worker.is_alive() and close_done.is_set()
        assert frame_after_close == [False] and probe == [False]
        bill = relay.accounting()
        assert bill['actual_forwarded_posts'] == 0 and bill['uncertain_partial_sends'] == 1
        assert bill['budget_reserved_combined_wire_bytes'] > 0 and bill['integrity_passed'] is False
    finally: decision.set(); client.close(); worker.join(3); close_worker.join(3)


def test_close_is_bounded_when_locked_fake_send_honors_timeout(tmp_path, monkeypatch):
    """Engineering timing control: scale the production bound down, not the episode."""
    monkeypatch.setattr(m, 'SEND_TIMEOUT', 0.05, raising=False)
    relay = relay_at(tmp_path); sending = threading.Event(); release = threading.Event(); configured = []
    class BlockingSocket:
        timeout = None
        def settimeout(self, seconds): self.timeout = seconds; configured.append(seconds)
        def sendall(self, packet):
            sending.set(); release.wait(self.timeout)
            raise socket.timeout('fake partial write reached its configured timeout')
        def shutdown(self, _): pass
        def close(self): pass
    monkeypatch.setattr(socket, 'create_connection', lambda *_, **__: BlockingSocket())
    client, receiver = socket.socketpair(); worker = threading.Thread(target=relay.handle, args=(receiver,))
    worker.start(); wire_payload(client, {'messages': []})
    closer = threading.Thread(target=relay.close)
    try:
        assert sending.wait(3); closer.start(); closer.join(1)
        assert not closer.is_alive(), 'close waited for the episode timeout instead of the short send bound'
        worker.join(1); assert not worker.is_alive()
        assert 0 < configured[0] <= .05
        bill = relay.accounting()
        assert bill['actual_forwarded_posts'] == 0 and bill['uncertain_partial_sends'] == 1
        assert bill['actual_forwarded_body_bytes'] == 0 and bill['budget_reserved_combined_wire_bytes'] > 0
        assert bill['integrity_passed'] is False
    finally:
        release.set(); client.close(); worker.join(3)
        if closer.ident is not None: closer.join(3)


def test_successful_fake_send_restores_response_deadline_timeout(tmp_path, monkeypatch):
    assert m.SEND_TIMEOUT == 5.0
    bodies, workers = fake_upstream(monkeypatch); connect = socket.create_connection; trace = []
    class SocketView:
        def __init__(self, sock): self.sock = sock; self.timeout = None
        def settimeout(self, seconds): self.timeout = seconds; trace.append(('timeout', seconds)); self.sock.settimeout(seconds)
        def sendall(self, packet): trace.append(('send', self.timeout)); self.sock.sendall(packet)
        def makefile(self, *args, **kwargs): return self.sock.makefile(*args, **kwargs)
        def shutdown(self, how): return self.sock.shutdown(how)
        def close(self): self.sock.close()
    monkeypatch.setattr(socket, 'create_connection', lambda *a, **kw: SocketView(connect(*a, **kw)))
    relay = relay_at(tmp_path); assert exchange(relay).startswith(b'HTTP/1.1 200')
    for worker in workers: worker.join(3)
    assert trace[0] == ('timeout', 5.0) and trace[1] == ('send', 5.0)
    assert trace[-1][0] == 'timeout' and 5.0 < trace[-1][1] <= 10
    bill = relay.accounting()
    assert bill['actual_forwarded_posts'] == 1 and bill['provider_total_tokens_known'] == 7 and bill['integrity_passed'] is True


@pytest.mark.parametrize('stderr,missing', [
    (b'error: no such object: ', True),
    (b'Error response from daemon: No such container: ', True),
    (b'permission denied while trying to connect to the Docker daemon socket: ', False),
    (b'Cannot connect to the Docker daemon at unix:///var/run/docker.sock: ', False),
])
def test_missing_cid_case_normalization_does_not_accept_operational_errors(tmp_path, monkeypatch, stderr, missing):
    cid = tmp_path / 'cid'; cid.write_text('a' * 64); calls = []
    def inspect(cmd, **_):
        calls.append(cmd)
        return SimpleNamespace(returncode=1, stdout=b'', stderr=stderr + b'a' * 64 + b'\n')
    monkeypatch.setattr(subprocess, 'run', inspect)
    if missing:
        result = m.stop_owned(cid, 'ours')
        assert result == dict(cid='a' * 64, name='ours', status='ALREADY_REMOVED')
    else:
        with pytest.raises(ValueError, match='ownership not proven'): m.stop_owned(cid, 'ours')
    assert len(calls) == 1 and calls[0] == ['docker', 'inspect', '--format', '{{json .Name}}', 'a' * 64]
