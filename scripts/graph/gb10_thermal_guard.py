"""Read GB10 thermal telemetry and admit work only after a verified cooldown."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from math import isfinite
import os
from pathlib import Path
import signal
import subprocess
from tempfile import NamedTemporaryFile
import time


ADMISSION = {"acpi": 75, "gpu": 70, "nvme": 65}
HOT = {"acpi": 88, "gpu": 85, "nvme": 80}
THERMAL_HOLD = 75
SYSFS = Path("/sys")


def text(path):
    try:
        return path.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError):
        return None


def temperature(value, divisor):
    try:
        value = float(value) / divisor
    except (ValueError, TypeError):
        return None
    return value if isfinite(value) and 0 < value <= 150 else None


def nvidia_smi(fields):
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=" + fields, "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3, check=True,
        )
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def throttle_status():
    # NVIDIA renamed these query fields. A missing optional counter is explicit.
    for namespace in ("clocks_event_reasons", "clocks_throttle_reasons"):
        fields = ",".join(f"{namespace}.{kind}_thermal_slowdown" for kind in ("sw", "hw"))
        rows = [[item.strip().casefold() for item in line.split(",")] for line in nvidia_smi(fields)]
        if any("active" in row for row in rows):
            return True
        if rows and all(row == ["not active", "not active"] for row in rows):
            return False
    return None


def sample(root=SYSFS, *, use_smi=True, telemetry=False):
    sensors = {kind: [] for kind in ADMISSION}
    fans = {}
    for zone in sorted((root / "class/thermal").glob("thermal_zone*")):
        name = (text(zone / "type") or "").casefold()
        if name.startswith("acpi"):
            sensors["acpi"].append(zone / "temp")
        elif "gpu" in name or name.startswith("nvidia"):
            sensors["gpu"].append(zone / "temp")
    for device in sorted((root / "class/hwmon").glob("hwmon*")):
        name = (text(device / "name") or "unknown").casefold()
        if name.startswith("acpi"):
            sensors["acpi"].extend(sorted(device.glob("temp*_input")))
        elif name in ("nvidia", "gpu"):
            sensors["gpu"].extend(sorted(device.glob("temp*_input")))
        elif name.startswith("nvme"):
            composite = [p for p in device.glob("temp*_input")
                         if (text(p.with_name(p.name.replace("_input", "_label"))) or "").casefold() == "composite"]
            sensors["nvme"].extend(sorted(composite) or [device / "temp1_input"])
        for path in sorted(device.glob("fan*_input")):
            speed = text(path)
            if speed is not None and speed.isascii() and speed.isdigit():
                fans[f"{device.name}:{name}:{path.name}"] = int(speed)

    values = {}
    complete = {}
    for kind, paths in sensors.items():
        observed = [temperature(text(path), 1000) for path in paths]
        complete[kind] = bool(observed) and None not in observed
        values[kind] = max((value for value in observed if value is not None), default=None)
    if use_smi and not complete["gpu"]:
        observed = [temperature(line, 1) for line in nvidia_smi("temperature.gpu")]
        complete["gpu"] = bool(observed) and None not in observed
        values["gpu"] = max((value for value in [values["gpu"], *observed] if value is not None), default=None)
    thermal_throttle = throttle_status() if use_smi and telemetry else None

    missing = [kind for kind, measured in complete.items() if not measured]
    hot = [kind for kind, value in values.items() if value is not None and value >= HOT[kind]]
    if thermal_throttle is True:
        hot.append("gpu_thermal_throttle")
    ready = not hot and not missing and all(values[kind] <= limit for kind, limit in ADMISSION.items())
    status = "HOT" if hot else "UNKNOWN" if missing else "READY" if ready else "COOLING"
    return {
        "sample_utc": datetime.now(timezone.utc).isoformat(),
        "status": status, "admission_ready": ready, "missing_essentials": missing,
        "hot_components": hot, "temperature_c": values, "fans_rpm": fans,
        "gpu_thermal_throttle": thermal_throttle,
    }


def emit(record, log=None, *, terminal=False):
    line = json.dumps(record, sort_keys=True, allow_nan=False)
    if log is not None:
        with log.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
    if log is None or terminal:
        print(line, flush=True)


def observe(args):
    return sample(
        args.sysfs_root,
        use_smi=not args.no_nvidia_smi and args.sysfs_root == SYSFS,
        telemetry=args.nvidia_smi_telemetry,
    )


def monitor(args):
    while True:
        record = observe(args)
        stopped = args.stop_on_unsafe and record["status"] in ("HOT", "UNKNOWN")
        emit(record, args.log, terminal=stopped)
        if stopped:
            return 2
        time.sleep(args.interval)


def cooldown(args):
    started = time.monotonic()
    stable_since = None
    while True:
        record = observe(args)
        now = time.monotonic()
        if not record["admission_ready"]:
            stable_since = None
        elif stable_since is None:
            stable_since = now
        elapsed = now - started
        stable = 0 if stable_since is None else now - stable_since
        success = args.seconds <= elapsed <= args.timeout and stable >= args.stable_seconds and stable_since is not None
        expired = elapsed >= args.timeout
        record.update(elapsed_seconds=round(elapsed, 3), stable_ready_seconds=round(stable, 3),
                      cooldown_gate="READY" if success else "TIMEOUT" if expired else "WAITING")
        emit(record, args.log, terminal=success or expired)
        if success or expired:
            return 0 if success else 2
        time.sleep(min(args.interval, args.timeout - elapsed))



def available_memory_kib():
    for line in (text(Path("/proc/meminfo")) or "").splitlines():
        if line.startswith("MemAvailable:"):
            fields = line.split()
            if len(fields) == 3 and fields[-1] == "kB" and fields[1].isdigit():
                return int(fields[1])
            return None
    return None


def publish_hold(path, value):
    # An atomic no-overwrite link makes the complete marker available to the child.
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=".thermal-hold-",
                                delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, sort_keys=True, allow_nan=False)
            stream.write("\n")
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def supervise(args):
    hold = getattr(args, "hold_file", None)
    if hold is not None:
        hold = hold.expanduser().absolute()
        if hold.exists() or hold.is_symlink():
            emit({"event": "HOLD_FILE_EXISTS", "hold_file": str(hold)}, args.log, terminal=True)
            return 2
    initial = observe(args)
    emit({**initial, "event": "SUPERVISOR_ADMISSION"}, args.log, terminal=not initial["admission_ready"])
    if not initial["admission_ready"]:
        return THERMAL_HOLD

    child = None
    stop = None
    sent = False

    def forward():
        nonlocal sent
        if child is None or stop is None or sent or child.poll() is not None:
            return
        try:
            os.killpg(child.pid, stop["signal"])
        except ProcessLookupError:
            return
        sent = True

    def request_stop(reason, signum, trigger=None):
        nonlocal stop
        if stop is None:
            stop = {"stop_reason": reason, "signal": int(signum),
                    "stop_utc": datetime.now(timezone.utc).isoformat()}
            if trigger is not None:
                stop["thermal_sample"] = trigger
            try:
                if reason == "thermal" and hold is not None:
                    stop["hold_file"] = str(hold)
                    publish_hold(hold, {**stop, "status": "THERMAL_HOLD", "child_pid": child.pid})
                    stop["hold_file_written"] = True
            except OSError as error:
                stop["hold_file_written"] = False
                stop["hold_file_error"] = str(error)
            finally:
                forward()

    def interrupt(signum, _frame):
        request_stop("supervisor_signal", signum)

    signals = (signal.SIGTERM, signal.SIGINT)
    previous = {signum: signal.signal(signum, interrupt) for signum in signals}
    try:
        if stop is not None:
            emit({**stop, "event": "CHILD_NOT_STARTED", "signal_sent": False}, args.log, terminal=True)
            return 128 + stop["signal"]
        try:
            options = {} if hold is None else {"env": {**os.environ, "GB10_THERMAL_HOLD_FILE": str(hold)}}
            child = subprocess.Popen(args.child, start_new_session=True, **options)
        except OSError as error:
            code = 127 if isinstance(error, FileNotFoundError) else 126
            emit({"event": "CHILD_START_FAILED", "supervisor_returncode": code,
                  "error_type": type(error).__name__}, args.log, terminal=True)
            return code
        forward()
        emit({"event": "CHILD_STARTED", "child_pid": child.pid,
              "start_utc": datetime.now(timezone.utc).isoformat()}, args.log)
        unsafe = 0
        while stop is None:
            try:
                child.wait(timeout=args.interval)
                break
            except subprocess.TimeoutExpired:
                record = observe(args)
                unsafe = unsafe + 1 if record["status"] in ("HOT", "UNKNOWN") else 0
                emit({**record, "event": "CHILD_MONITOR", "child_pid": child.pid,
                      "consecutive_unsafe": unsafe}, args.log)
                if unsafe == 2:
                    request_stop("thermal", signal.SIGTERM, record)
        if stop is not None:
            emit({**stop, "event": "STOP_REQUEST", "child_pid": child.pid, "signal_sent": sent},
                 args.log, terminal=True)
        code = child.wait()
        status = code if code >= 0 else 128 - code
        if sent:
            status = THERMAL_HOLD if stop["stop_reason"] == "thermal" else 128 + stop["signal"]
        emit({"event": "CHILD_EXIT", "child_pid": child.pid, "child_returncode": code,
              "supervisor_returncode": status, "stop_reason": None if stop is None else stop["stop_reason"],
              "signal_sent": sent, "mem_available_kib": available_memory_kib(),
              "exit_utc": datetime.now(timezone.utc).isoformat()}, args.log, terminal=True)
        return status
    finally:
        try:
            if child is not None and child.poll() is None:
                request_stop("supervisor_error", signal.SIGTERM)
                child.wait()
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)


def duration(raw):
    try:
        value = float(raw)
    except ValueError as error:
        raise argparse.ArgumentTypeError("duration must be a finite positive number") from error
    if not isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError("duration must be a finite positive number")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    once = commands.add_parser("sample", help="Print one sample; exit 0 only when ready for admission")
    watch = commands.add_parser("monitor", help="Append timestamped JSON lines at a fixed interval")
    wait = commands.add_parser("cooldown", help="Wait through a minimum idle interval and a continuous series of ready samples")
    guard = commands.add_parser("supervise", help="Supervise an owned POSIX process group and exit 75 on thermal hold")
    for command in (once, watch, wait, guard):
        command.add_argument("--sysfs-root", type=Path, default=SYSFS, help="Sensor filesystem root (default /sys)")
        command.add_argument("--no-nvidia-smi", action="store_true", help="Disable nvidia-smi even as a GPU temperature fallback")
        command.add_argument("--nvidia-smi-telemetry", action="store_true", help="Include optional GPU thermal slowdown counters")
    for command in (watch, wait, guard):
        command.add_argument("--log", type=Path, required=command is guard)
        command.add_argument("--interval", type=duration, default=15)
    watch.add_argument("--stop-on-unsafe", action="store_true", help="Exit 2 on a hot or incomplete sample")
    wait.add_argument("--seconds", type=duration, default=900, help="Minimum elapsed cooldown seconds (default 900)")
    wait.add_argument("--stable-seconds", type=duration, default=180, help="Required span of ready samples (default 180)")
    wait.add_argument("--timeout", type=duration, default=3600, help="End with exit 2 after this many seconds (default 3600)")
    guard.add_argument("--hold-file", type=Path, help="Publish a new thermal hold marker before a thermal SIGTERM")
    guard.add_argument("child", nargs=argparse.REMAINDER, help="Command after --, started in its own POSIX session")
    args = parser.parse_args()
    if args.command == "supervise":
        if os.name != "posix":
            parser.error("supervise requires POSIX process groups")
        if len(args.child) < 2 or args.child[0] != "--":
            parser.error("supervise requires -- COMMAND")
        args.child = args.child[1:]
        return supervise(args)
    if args.command == "sample":
        record = observe(args)
        emit(record)
        return 0 if record["admission_ready"] else 1 if record["status"] == "COOLING" else 2
    if args.command == "monitor":
        return monitor(args)
    if args.timeout < max(args.seconds, args.stable_seconds):
        parser.error("--timeout must cover both cooldown and stable duration")
    return cooldown(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
