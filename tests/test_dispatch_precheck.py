"""Local contract regressions; synthetic receipts are NOT runtime evidence."""

import hashlib
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/graph/dispatch_precheck.sh"


@pytest.fixture(autouse=True)
def offline_only(tmp_path, monkeypatch):
    """Assert zero network calls, including Python children of the shell CLI."""
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(args)
        raise AssertionError("network access is forbidden")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    guard = tmp_path / "offline-guard"
    guard.mkdir()
    attempted = tmp_path / "forbidden-access"
    (guard / "sitecustomize.py").write_text(
        "import os, sys\n"
        "def audit(event, args):\n"
        "    if event.startswith('socket.'):\n"
        "        with open(os.environ['PRECHECK_FORBIDDEN'], 'a') as log:\n"
        "            log.write(event + '\\n')\n"
        "        raise RuntimeError('network access is forbidden')\n"
        "sys.addaudithook(audit)\n",
        encoding="utf-8",
    )
    for command in ("curl", "wget", "ssh", "nc", "ncat", "telnet", "crontab"):
        stub = guard / command
        stub.write_text(
            '#!/bin/sh\nprintf "%s\\n" "$0" >> "$PRECHECK_FORBIDDEN"\nexit 99\n',
            encoding="utf-8",
        )
        stub.chmod(0o700)
    monkeypatch.setenv("PRECHECK_FORBIDDEN", str(attempted))
    monkeypatch.setenv(
        "PATH", os.pathsep.join((str(guard), str(Path(sys.executable).parent), os.environ["PATH"]))
    )
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join((str(guard), str(ROOT / "src"))))
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    monkeypatch.delenv("BASH_ENV", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    yield
    assert calls == [], "the test attempted network access"
    assert not attempted.exists(), "the CLI attempted network/cron access"


def run_precheck(*args):
    return subprocess.run(
        ["bash", str(SCRIPT), *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=5,
    )


def write_receipt(path, watcher, /, **overrides):
    receipt = {
        "watcher": str(watcher.resolve()),
        "watcher_sha256": hashlib.sha256(watcher.read_bytes()).hexdigest(),
        "observed_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
        "exit_code": 0,
    }
    receipt.update(overrides)
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return path


@pytest.fixture
def evidence(tmp_path):
    ran = tmp_path / "watcher-was-executed"
    watcher = tmp_path / "watcher with spaces.sh"
    watcher.write_text(
        f"#!/usr/bin/env bash\nprintf 'executed' > {shlex.quote(str(ran))}\nexit 23\n",
        encoding="utf-8",
    )
    watcher.chmod(0o700)
    tick = write_receipt(tmp_path / "tick.json", watcher)
    yield watcher, tick
    assert not ran.exists(), "precheck must never execute the watcher"


def assert_rejected(result, code=1):
    assert result.returncode == code, result.stdout + result.stderr
    assert "双实证齐备" not in result.stdout
    assert "Traceback" not in result.stderr


def test_requires_watcher(evidence):
    _, tick = evidence
    assert_rejected(run_precheck("--tick-marker", tick), code=64)


def test_rejects_arbitrary_document_tick(evidence):
    watcher, _ = evidence
    result = run_precheck(
        "--watcher", watcher, "--tick-marker", ROOT / "templates/task_card_template.md"
    )
    assert_rejected(result)


def test_valid_synthetic_receipt_is_read_only(evidence):
    watcher, tick = evidence
    before = [(path.read_bytes(), path.stat().st_mtime_ns) for path in evidence]
    result = run_precheck("--watcher", watcher, "--tick-marker", tick)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "双实证齐备" in result.stdout
    assert before == [(path.read_bytes(), path.stat().st_mtime_ns) for path in evidence]


@pytest.mark.parametrize("option", ["--watcher", "--tick-marker", "--cron-line", "--max-tick-age-min"])
@pytest.mark.parametrize("value", [(), ("",), ("--tick-marker",)])
def test_missing_option_value_is_usage_error(evidence, option, value):
    watcher, tick = evidence
    assert_rejected(run_precheck(
        "--watcher", watcher, "--tick-marker", tick, option, *value
    ), code=64)


@pytest.mark.parametrize("age", ["-1", "1.5", "NaN", "abc", "1e2", "+1", " "])
def test_invalid_age_is_usage_error(evidence, age):
    watcher, tick = evidence
    assert_rejected(
        run_precheck("--watcher", watcher, "--tick-marker", tick, "--max-tick-age-min", age),
        code=64,
    )


def test_help_and_missing_required_inputs(evidence):
    watcher, _ = evidence
    assert run_precheck("--help").returncode == 0
    assert_rejected(run_precheck(), code=64)
    assert_rejected(run_precheck("--watcher", watcher), code=64)
    assert_rejected(run_precheck("--unknown"), code=64)


@pytest.mark.parametrize("field", ["watcher", "watcher_sha256", "observed_at", "exit_code"])
def test_missing_receipt_field(evidence, field):
    watcher, tick = evidence
    receipt = json.loads(tick.read_text())
    del receipt[field]
    tick.write_text(json.dumps(receipt), encoding="utf-8")
    assert_rejected(run_precheck("--watcher", watcher, "--tick-marker", tick))


@pytest.mark.parametrize(
    "field,value",
    [
        ("watcher", "relative.sh"),
        ("watcher", None),
        ("watcher", 42),
        ("watcher_sha256", "0" * 64),
        ("watcher_sha256", "not-a-hash"),
        ("watcher_sha256", None),
        ("observed_at", "not-a-date"),
        ("observed_at", "2026-09-01T12:00:00"),
        ("observed_at", "2026-02-30T12:00:00Z"),
        ("observed_at", 42),
        ("observed_at", None),
        ("exit_code", 1),
        ("exit_code", -1),
        ("exit_code", False),
        ("exit_code", 0.0),
        ("exit_code", "0"),
        ("exit_code", None),
    ],
)
def test_invalid_receipt_fields(evidence, field, value):
    watcher, tick = evidence
    write_receipt(tick, watcher, **{field: value})
    assert_rejected(run_precheck("--watcher", watcher, "--tick-marker", tick))


@pytest.mark.parametrize("contents", ["", "{", "[]", "null", '"text"', "0", "\xff"])
def test_invalid_json_receipts(evidence, contents):
    watcher, tick = evidence
    tick.write_bytes(contents.encode("latin-1"))
    assert_rejected(run_precheck("--watcher", watcher, "--tick-marker", tick))


@pytest.mark.parametrize("suffix", [', "exit_code": 0', ', "extra": NaN', ', "extra": Infinity'])
def test_receipt_json_must_be_unambiguous(evidence, suffix):
    watcher, tick = evidence
    tick.write_text(tick.read_text().rstrip()[:-1] + suffix + "}", encoding="utf-8")
    assert_rejected(run_precheck("--watcher", watcher, "--tick-marker", tick))


def test_receipt_cannot_bind_a_missing_watcher(evidence, tmp_path):
    watcher, tick = evidence
    write_receipt(tick, watcher, watcher=str(tmp_path / "missing.sh"))
    assert_rejected(run_precheck("--watcher", watcher, "--tick-marker", tick))


@pytest.mark.parametrize("kind", ["missing", "directory", "fifo"])
def test_tick_must_be_regular_file(evidence, kind):
    watcher, tick = evidence
    tick.unlink()
    if kind == "directory":
        tick.mkdir()
    elif kind == "fifo":
        os.mkfifo(tick)
    assert_rejected(run_precheck("--watcher", watcher, "--tick-marker", tick))


@pytest.mark.parametrize("kind", ["missing", "directory", "fifo", "not-executable", "syntax", "empty"])
def test_invalid_watcher(evidence, kind):
    watcher, tick = evidence
    if kind in {"missing", "directory", "fifo"}:
        watcher.unlink()
        if kind == "directory":
            watcher.mkdir()
        elif kind == "fifo":
            os.mkfifo(watcher)
    else:
        if kind == "not-executable":
            watcher.chmod(0o600)
        elif kind == "syntax":
            watcher.write_text("#!/bin/bash\nif then\n", encoding="utf-8")
        else:
            watcher.write_text("", encoding="utf-8")
        write_receipt(tick, watcher)
    assert_rejected(run_precheck("--watcher", watcher, "--tick-marker", tick))


def test_receipt_binds_current_watcher_bytes(evidence):
    watcher, tick = evidence
    watcher.write_text(watcher.read_text() + "# changed after receipt\n", encoding="utf-8")
    assert_rejected(run_precheck("--watcher", watcher, "--tick-marker", tick))


def test_each_watcher_needs_its_own_receipt(evidence, tmp_path):
    watcher, tick = evidence
    other = tmp_path / "other.sh"
    other.write_bytes(watcher.read_bytes())  # Same hash alone must not authorize another path.
    other.chmod(0o700)
    other_tick = write_receipt(tmp_path / "other.json", other)
    # An extra receipt for an undeclared watcher must fail even with a valid receipt present.
    assert_rejected(run_precheck(
        "--watcher", watcher, "--tick-marker", tick, "--tick-marker", other_tick
    ))
    args = ("--watcher", watcher, "--watcher", other, "--tick-marker", tick)
    assert_rejected(run_precheck(*args, "--tick-marker", tick))
    result = run_precheck(*args, "--tick-marker", other_tick)
    assert result.returncode == 0, result.stdout + result.stderr


def test_bad_receipt_cannot_hide_behind_a_valid_one(evidence, tmp_path):
    watcher, tick = evidence
    bad_tick = write_receipt(tmp_path / "bad.json", watcher, exit_code=1)
    assert_rejected(run_precheck(
        "--watcher", watcher, "--tick-marker", tick, "--tick-marker", bad_tick
    ))


@pytest.mark.parametrize("age", ["0", "10"])
def test_future_receipt_is_always_rejected(evidence, age):
    watcher, tick = evidence
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    write_receipt(tick, watcher, observed_at=future.isoformat())
    assert_rejected(run_precheck(
        "--watcher", watcher, "--tick-marker", tick, "--max-tick-age-min", age
    ))


@pytest.mark.parametrize("seconds", [601, 7200])
def test_recent_mtime_does_not_rescue_expired_receipt(evidence, seconds):
    watcher, tick = evidence
    old = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    write_receipt(tick, watcher, observed_at=old.isoformat())
    os.utime(tick, None)
    assert_rejected(run_precheck(
        "--watcher", watcher, "--tick-marker", tick, "--max-tick-age-min", "10"
    ))


@pytest.mark.parametrize("zone", [timezone.utc, timezone(timedelta(hours=8)), timezone(timedelta(hours=-5))])
def test_fresh_receipt_with_old_mtime_passes(evidence, zone):
    watcher, tick = evidence
    fresh = (datetime.now(zone) - timedelta(minutes=1)).isoformat()
    if zone == timezone.utc:
        fresh = fresh.replace("+00:00", "Z")
    write_receipt(tick, watcher, observed_at=fresh)
    os.utime(tick, (1, 1))
    result = run_precheck(
        "--watcher", watcher, "--tick-marker", tick, "--max-tick-age-min", "10"
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_zero_age_disables_only_staleness_check(evidence):
    watcher, tick = evidence
    write_receipt(tick, watcher, observed_at="2000-01-01T00:00:00Z")
    for age in ("0", "000"):
        result = run_precheck(
            "--watcher", watcher, "--tick-marker", tick, "--max-tick-age-min", age
        )
        assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("invocation", ["", "bash ", "/bin/bash ", "/bin/sh "])
@pytest.mark.parametrize("schedule", ["5 3 * * *", "@reboot"])
def test_static_cron_bound_to_declared_watcher(evidence, tmp_path, invocation, schedule):
    watcher, tick = evidence
    log = tmp_path / "watcher log.txt"
    cron = f"{schedule} {invocation}{shlex.quote(str(watcher))} >>{shlex.quote(str(log))} 2>&1"
    result = run_precheck("--watcher", watcher, "--tick-marker", tick, "--cron-line", cron)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not log.exists(), "precheck must not execute cron or create logs"


@pytest.mark.parametrize("invocation", ["", "bash ", "/bin/bash "])
@pytest.mark.parametrize("exists", [True, False])
def test_cron_unknown_or_missing_target_never_passes(evidence, tmp_path, invocation, exists):
    watcher, tick = evidence
    unknown = tmp_path / "unknown.sh"
    if exists:
        unknown.write_bytes(watcher.read_bytes())
        unknown.chmod(0o700)
    cron = f"5 3 * * * {invocation}{unknown} >> {tmp_path / 'log'} 2>&1"
    result = run_precheck("--watcher", watcher, "--tick-marker", tick, "--cron-line", cron)
    assert_rejected(result)
    cron_output = result.stdout.split("[cron-line]", 1)[1].split("[tick-marker]", 1)[0]
    assert "PASS" not in cron_output


@pytest.mark.parametrize("suffix", [
    "", " 2>&1", " >> /dev/null 2>&1", " >> log", " 2>&1 >> log",
    " # ignored >> log 2>&1", " () >> log 2>&1", " {a,b} >> log 2>&1",
])
def test_cron_requires_a_real_failure_log(evidence, suffix):
    watcher, tick = evidence
    cron = f"5 3 * * * {shlex.quote(str(watcher))}{suffix}"
    assert_rejected(run_precheck("--watcher", watcher, "--tick-marker", tick, "--cron-line", cron))


@pytest.mark.parametrize("prefix", ["echo ", "bash -c ", "/missing/bash ", "env bash "])
def test_cron_unverifiable_invocation_fails_closed(evidence, prefix):
    watcher, tick = evidence
    cron = f"5 3 * * * {prefix}{shlex.quote(str(watcher))} >> log 2>&1"
    assert_rejected(run_precheck("--watcher", watcher, "--tick-marker", tick, "--cron-line", cron))
