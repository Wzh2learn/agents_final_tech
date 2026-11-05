import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
import time

import pytest

from scripts.graph.research_auto_record import RecordingPendingError, recorded_episode, recover_episode
from scripts.graph import research_auto_record
from scripts.graph.research_evidence_graph import validate


EPISODE = "source__none__seed7"


def artifacts(root):
    side = json.loads((root / (EPISODE + ".auto_record.json")).read_text(encoding="utf-8"))
    graph = json.loads((root / (EPISODE + ".evidence_graph.json")).read_text(encoding="utf-8"))
    return side, graph


def test_real_subprocess_receipt_and_tamper(tmp_path):
    @recorded_episode(tmp_path, 7)
    def run(task, condition):
        (tmp_path / (EPISODE + ".started.json")).write_text('{}', encoding='utf-8')
        case = tmp_path / EPISODE
        case.mkdir()
        (case / 'raw.jsonl').write_text('raw\n', encoding='utf-8')
        proc = subprocess.run([sys.executable, '-c', 'print("offline")'], capture_output=True, check=True)
        assert proc.stdout.strip() == b'offline'
        (tmp_path / (EPISODE + ".completed.json")).write_text(json.dumps(
            {'status': 'COMPLETED', 'posts': 2, 'reported_tokens': 100, 'cache_read_included': 30}), encoding='utf-8')
    run('source')
    side, graph = artifacts(tmp_path)
    assert side['costs']['posts'] == 2
    assert side['costs']['reported_tokens'] == 100 and side['costs']['cache_read_included'] == 30
    assert side['cost_contract'] == 'FORMAT_VALID_UNBOUND'
    assert side['scientific_outcome'] == 'UNKNOWN_NOT_INFERRED'
    assert validate(tmp_path, graph)['valid']
    check = json.loads((tmp_path / (EPISODE + '.evidence_check.json')).read_text(encoding='utf-8'))
    assert check['valid'] and len(check['graph_sha256']) == 64
    (tmp_path / EPISODE / 'raw.jsonl').write_text('tampered', encoding='utf-8')
    assert not validate(tmp_path, graph)['valid']
    with pytest.raises(ValueError, match='stale'):
        recover_episode(tmp_path, EPISODE)
    with pytest.raises(FileExistsError):
        run('source')


@pytest.mark.parametrize('failure', ['nonzero', 'timeout'])
def test_failure_records_unknown_and_does_not_rerun(tmp_path, failure):
    calls = []
    @recorded_episode(tmp_path, 7)
    def run(task, condition):
        calls.append(1)
        (tmp_path / (EPISODE + '.started.json')).write_text('{}', encoding='utf-8')
        if failure == 'timeout':
            subprocess.run([sys.executable, '-c', 'import time;time.sleep(2)'], timeout=0.05, check=True)
        else:
            subprocess.run([sys.executable, '-c', 'raise SystemExit(3)'], check=True)
    with pytest.raises((subprocess.TimeoutExpired, subprocess.CalledProcessError)):
        run('source')
    side, graph = artifacts(tmp_path)
    assert side['receipt_status'] == 'UNKNOWN'
    assert side['costs']['posts'] is None and side['costs']['reported_tokens'] is None
    assert validate(tmp_path, graph)['valid']
    with pytest.raises(FileExistsError):
        run('source')
    assert calls == [1]


def test_concurrent_reservation_and_recovery(tmp_path):
    calls = []
    @recorded_episode(tmp_path, 7)
    def run(task, condition):
        calls.append(1)
        time.sleep(.1)
    def attempt():
        try:
            run('source')
            return 'ran'
        except FileExistsError:
            return 'reserved'
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: attempt(), range(2))) == ['ran', 'reserved']
    assert len(calls) == 1
    before = (tmp_path / (EPISODE + '.auto_record.json')).read_bytes()
    recover_episode(tmp_path, EPISODE)
    assert (tmp_path / (EPISODE + '.auto_record.json')).read_bytes() == before


def test_orphan_reservation_recovery_never_executes(tmp_path):
    (tmp_path / (EPISODE + '.auto_reservation.json')).write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='may still be running'):
        recover_episode(tmp_path, EPISODE)
    assert recover_episode(tmp_path, EPISODE, abandoned=True)
    side, graph = artifacts(tmp_path)
    assert side['costs']['elapsed_seconds'] is None
    assert validate(tmp_path, graph)['valid']


def test_recovery_can_finish_missing_evidence_check(tmp_path):
    @recorded_episode(tmp_path, 7)
    def run(task, condition):
        pass
    run('source')
    check = tmp_path / (EPISODE + '.evidence_check.json')
    check.unlink()
    recover_episode(tmp_path, EPISODE)
    assert json.loads(check.read_text(encoding='utf-8'))['valid']


@pytest.mark.parametrize('suffix', ['.harness.py', '.runner.stdout', '.runner.stderr'])
def test_existing_harness_or_log_prevents_execution(tmp_path, suffix):
    (tmp_path / (EPISODE + suffix)).write_text('existing', encoding='utf-8')
    @recorded_episode(tmp_path, 7)
    def run(task, condition):
        pytest.fail('must not execute')
    with pytest.raises(FileExistsError):
        run('source')


def test_sidecar_publish_failure_preserves_terminal_and_recovers(tmp_path, monkeypatch):
    original = research_auto_record.os.link
    def fail_sidecar(source, destination):
        if str(destination).endswith('.auto_record.json'):
            raise OSError('simulated publish failure')
        return original(source, destination)
    monkeypatch.setattr(research_auto_record.os, 'link', fail_sidecar)
    calls = []
    @recorded_episode(tmp_path, 7)
    def run(task, condition):
        calls.append(1)
        (tmp_path / (EPISODE + '.completed.json')).write_text('{"status":"COMPLETED"}', encoding='utf-8')
    with pytest.raises(RecordingPendingError, match='do not rerun automatically') as error:
        run('source')
    assert error.value.episode_id == EPISODE
    terminal = json.loads((tmp_path / (EPISODE + '.auto_terminal.json')).read_text(encoding='utf-8'))
    assert terminal['execution_returned'] is True and terminal['elapsed_seconds'] >= 0
    assert not (tmp_path / (EPISODE + '.auto_record.json')).exists()
    with pytest.raises(FileExistsError):
        run('source')
    monkeypatch.setattr(research_auto_record.os, 'link', original)
    recover_episode(tmp_path, EPISODE)
    side, graph = artifacts(tmp_path)
    assert calls == [1] and validate(tmp_path, graph)['valid']
    assert side['costs']['elapsed_seconds'] == terminal['elapsed_seconds']


def test_recording_failure_does_not_mask_episode_error(tmp_path, monkeypatch, capsys):
    original = research_auto_record.os.link

    def fail_sidecar(source, destination):
        if str(destination).endswith('.auto_record.json'):
            raise OSError('simulated publish failure')
        return original(source, destination)

    monkeypatch.setattr(research_auto_record.os, 'link', fail_sidecar)
    calls = []

    @recorded_episode(tmp_path, 7)
    def run(task, condition):
        calls.append(1)
        raise ValueError('original episode failure')

    with pytest.raises(ValueError, match='original episode failure'):
        run('source')
    assert 'sidecar pending' in capsys.readouterr().err
    terminal = json.loads((tmp_path / (EPISODE + '.auto_terminal.json')).read_text(encoding='utf-8'))
    assert terminal['execution_returned'] is False
    with pytest.raises(FileExistsError):
        run('source')
    monkeypatch.setattr(research_auto_record.os, 'link', original)
    recover_episode(tmp_path, EPISODE)
    assert calls == [1]
    assert artifacts(tmp_path)[0]['costs']['elapsed_seconds'] == terminal['elapsed_seconds']


def test_success_inside_callers_except_still_reports_recording_failure(tmp_path, monkeypatch):
    original = research_auto_record.os.link

    def fail_sidecar(source, destination):
        if str(destination).endswith('.auto_record.json'):
            raise OSError('simulated publish failure')
        return original(source, destination)

    monkeypatch.setattr(research_auto_record.os, 'link', fail_sidecar)

    @recorded_episode(tmp_path, 7)
    def run(task, condition):
        return 'complete'

    try:
        raise ValueError('caller error')
    except ValueError:
        with pytest.raises(RecordingPendingError):
            run('source')


@pytest.mark.parametrize('elapsed', [True, -1, '5', float('inf')])
def test_recovery_rejects_invalid_terminal_elapsed(tmp_path, elapsed):
    (tmp_path / (EPISODE + '.auto_reservation.json')).write_text('{}', encoding='utf-8')
    (tmp_path / (EPISODE + '.auto_terminal.json')).write_text(json.dumps(
        {'version': 1, 'episode_id': EPISODE, 'elapsed_seconds': elapsed}), encoding='utf-8')
    recover_episode(tmp_path, EPISODE)
    assert artifacts(tmp_path)[0]['costs']['elapsed_seconds'] is None


def test_recovery_legacy_terminal_without_duration_is_unknown(tmp_path):
    (tmp_path / (EPISODE + '.auto_reservation.json')).write_text('{}', encoding='utf-8')
    (tmp_path / (EPISODE + '.auto_terminal.json')).write_text(json.dumps(
        {'version': 1, 'episode_id': EPISODE, 'execution_returned': True}), encoding='utf-8')
    recover_episode(tmp_path, EPISODE)
    assert artifacts(tmp_path)[0]['costs']['elapsed_seconds'] is None


def test_first_episode_creates_missing_private_root(tmp_path):
    root = tmp_path / 'new-root'
    @recorded_episode(root, 7)
    def run(task, condition):
        assert root.is_dir()
    run('source')
    side, graph = artifacts(root)
    assert side['usage_completeness'] == 'UNKNOWN_NOT_INFERRED_FROM_RECEIPT'
    assert validate(root, graph)['valid']


def test_concurrent_processes_execute_episode_once(tmp_path):
    code = '''
import sys,time
from pathlib import Path
from scripts.graph.research_auto_record import recorded_episode
@recorded_episode(Path(sys.argv[1]), 7)
def run(task, condition):
    with (Path(sys.argv[1]) / "calls.txt").open("a") as f: f.write("ran\\n")
    time.sleep(.3)
try:
    run("source")
    print("ran")
except FileExistsError:
    print("reserved")
'''
    a = subprocess.Popen([sys.executable, '-c', code, str(tmp_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    b = subprocess.Popen([sys.executable, '-c', code, str(tmp_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out_a, err_a = a.communicate(timeout=15)
    out_b, err_b = b.communicate(timeout=15)
    assert a.returncode == b.returncode == 0, (err_a, err_b)
    assert sorted([out_a.strip(), out_b.strip()]) == ['ran', 'reserved']
    assert (tmp_path / 'calls.txt').read_text().splitlines() == ['ran']


@pytest.mark.parametrize('name', ['completed', 'raw', 'case'])
def test_recovery_rejects_external_symlinks(tmp_path, name):
    root = tmp_path / 'private'
    root.mkdir()
    (root / (EPISODE + '.auto_reservation.json')).write_text('{}', encoding='utf-8')
    (root / (EPISODE + '.auto_terminal.json')).write_text('{}', encoding='utf-8')
    outside = tmp_path / 'external'
    outside.mkdir()
    (outside / 'raw.jsonl').write_text('external', encoding='utf-8')
    (outside / 'completed.json').write_text('{"posts":123}', encoding='utf-8')
    try:
        if name == 'completed':
            (root / (EPISODE + '.completed.json')).symlink_to(outside / 'completed.json')
        elif name == 'case':
            (root / EPISODE).symlink_to(outside, target_is_directory=True)
        else:
            case = root / EPISODE
            case.mkdir()
            (case / 'raw.jsonl').symlink_to(outside / 'raw.jsonl')
    except OSError:
        pytest.skip('symlinks unavailable')
    with pytest.raises(ValueError, match='unsafe episode artifact'):
        recover_episode(root, EPISODE)
    assert not (root / (EPISODE + '.auto_record.json')).exists()


@pytest.mark.parametrize('receipt', [
    '{"posts":1.5,"reported_tokens":100,"cache_read_included":1000}',
    '{"posts":1,"posts":2}',
    '{"posts":NaN}',
    '{"posts":true}',
])
def test_invalid_cost_contract_preserves_raw_and_no_trust(tmp_path, receipt):
    @recorded_episode(tmp_path, 7)
    def run(task, condition):
        (tmp_path / (EPISODE + '.completed.json')).write_text(receipt, encoding='utf-8')
    run('source')
    side, graph = artifacts(tmp_path)
    assert side['cost_contract'] == 'INVALID' and side['cost_errors']
    assert side['costs']['posts'] is None
    assert side['costs']['reported_tokens'] is None
    assert side['costs']['cache_read_included'] is None
    assert (tmp_path / (EPISODE + '.completed.json')).read_text(encoding='utf-8') == receipt
    assert validate(tmp_path, graph)['valid']


@pytest.mark.parametrize('mismatch', [False, True])
def test_breakdown_requires_bound_raw_and_matching_total(tmp_path, mismatch):
    @recorded_episode(tmp_path, 7)
    def run(task, condition):
        case = tmp_path / EPISODE
        case.mkdir()
        raw = case / 'raw.jsonl'
        steps = [{'input': 80, 'output': 20, 'reasoning': 3, 'total': 100,
                  'cache': {'read': 30}}]
        raw.write_text(json.dumps({'type':'step_finish', 'part':{'tokens':steps[0]}}) + '\n', encoding='utf-8')
        digest = hashlib.sha256(raw.read_bytes()).hexdigest()
        (case / 'receipt.json').write_text(json.dumps({'raw_sha256': digest,
            'step_finish_tokens': steps, 'model_http_requests':['POST /v1']}), encoding='utf-8')
        (tmp_path / (EPISODE + '.completed.json')).write_text(json.dumps({
            'status': 'COMPLETED', 'raw_sha256': 'bad' if mismatch else digest,
            'posts': 1, 'reported_tokens': 100, 'cache_read_included': 30}), encoding='utf-8')
    run('source')
    side, _ = artifacts(tmp_path)
    if mismatch:
        assert side['cost_contract'] == 'INVALID'
        assert side['costs']['input_tokens'] is None and side['costs']['reported_tokens'] is None
    else:
        assert side['cost_contract'] == 'FORMAT_VALID_BOUND'
        assert side['token_breakdown_source'] == 'BOUND_RAW_AND_STEP_RECEIPT'
        assert [side['costs'][k] for k in ('input_tokens','output_tokens','reasoning_tokens')] == [80,20,3]


def test_posts_mismatch_is_invalid_and_uncounted(tmp_path):
    @recorded_episode(tmp_path, 7)
    def run(task, condition):
        case = tmp_path / EPISODE
        case.mkdir()
        token = {'input': 1, 'output': 2, 'reasoning': 0, 'total': 3, 'cache': {'read': 0}}
        raw = case / 'raw.jsonl'
        raw.write_text(json.dumps({'type': 'step_finish', 'part': {'tokens': token}}) + '\n', encoding='utf-8')
        digest = hashlib.sha256(raw.read_bytes()).hexdigest()
        (case / 'receipt.json').write_text(json.dumps({'raw_sha256':digest,
            'step_finish_tokens':[token], 'model_http_requests':['POST /v1']}), encoding='utf-8')
        (tmp_path / (EPISODE + '.completed.json')).write_text(json.dumps({'raw_sha256':digest,
            'posts':999, 'reported_tokens':3, 'cache_read_included':0}), encoding='utf-8')
    run('source')
    side, _ = artifacts(tmp_path)
    assert side['cost_contract'] == 'INVALID' and side['costs']['posts'] is None
    assert any('posts differs' in e for e in side['cost_errors'])
