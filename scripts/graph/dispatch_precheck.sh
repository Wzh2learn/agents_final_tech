#!/usr/bin/env bash
# dispatch_precheck.sh — 常备派发前置检查: watcher「双实证」输入合同。
# F-0907-1: 挂了 crontab ≠ 观察器在跑; 执行位 + 绑定当前 watcher 的执行收据缺一不可。
# 只读取证: 不执行 watcher、不制造 tick、不安装/修改 cron、不访问网络/服务。
# JSON 收据是可审计合同, 不是防恶意伪造的证明, 也不保证 cron 将来会运行。
# 使用 Python 3 标准库校验 JSON、时间与路径; bash 仅用于 -n 静态语法检查。
set -uo pipefail

exec python3 - "$@" <<'PY'
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(64, f"参数错误: {message}\n")


def nonempty(value):
    if not value.strip():
        raise argparse.ArgumentTypeError("参数值不得为空")
    return value


def nonnegative_integer(value):
    if not re.fullmatch(r"[0-9]+", value):
        raise argparse.ArgumentTypeError("年龄上限必须是非负整数分钟 (0 = 不限年龄)")
    return int(value)


parser = Parser(
    prog="dispatch_precheck.sh",
    allow_abbrev=False,
    description="watcher 双实证输入合同校验 (只读, 不执行 watcher, 不制造 tick)",
    epilog=(
        "每个 watcher 至少一份 JSON 收据: watcher=绝对路径, watcher_sha256=当前字节完整 SHA256, "
        "observed_at=含时区 ISO8601 时间, exit_code=整数 0。拒绝未来时间; 新鲜度不使用 mtime。"
        "收据是可审计合同, 不防恶意伪造。退出码: 0=合同通过, 1=校验失败, 64=参数错误。"
        "cron 仅静态支持五字段或 @宏后的简单绝对路径调用 (可前置 bash/sh), "
        "以 > 或 >> 日志路径 2>&1 结尾; 不验证调度或运行环境。"
    ),
)
parser.add_argument("--watcher", action="append", required=True, type=nonempty, metavar="PATH")
parser.add_argument("--tick-marker", action="append", required=True, type=nonempty, metavar="JSON")
parser.add_argument("--cron-line", action="append", default=[], type=nonempty)
parser.add_argument("--max-tick-age-min", type=nonnegative_integer, default=0, metavar="N")
args = parser.parse_args()
rc = 0


def fail(message):
    global rc
    rc = 1
    print(f"  FAIL  {message}")


def check_watcher(path):
    if not path.is_file():
        raise ValueError("watcher 不存在或不是普通文件")
    if not os.access(path, os.X_OK):
        raise ValueError("watcher 缺执行位 (F-0907-1): 修复后才可派发")
    data = path.read_bytes()
    if not data:
        raise ValueError("watcher 是空文件")
    syntax = subprocess.run(
        ["bash", "-n", "--", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        errors="replace",
        timeout=10,
    )
    if syntax.returncode:
        raise ValueError(f"bash -n 不通过: {syntax.stderr.strip()}")
    digest = hashlib.sha256(data).hexdigest()
    print(f"  PASS  bash -n; mode={stat.filemode(path.stat().st_mode)} sha256={digest} bytes={len(data)}")
    return digest


def check_cron(line, watchers):
    # Deliberately not a cron/shell interpreter. Unsupported constructs fail closed.
    if "\n" in line or "\r" in line:
        raise ValueError("cron 必须是单行")
    if line.lstrip().startswith("@"):
        parts = line.split(None, 1)
        if parts[0] not in {"@reboot", "@yearly", "@annually", "@monthly", "@weekly", "@daily", "@midnight", "@hourly"}:
            raise ValueError("未知 cron @宏")
        expected = 2
    else:
        parts = line.split(None, 5)
        expected = 6
    if len(parts) != expected:
        raise ValueError("无法分离 cron 调度字段与调用命令")
    # Require a simple stdout log followed by stderr duplication, in that order.
    redirect = re.fullmatch(r"(.+?)\s+(>>|>)\s*(.+?)\s+2>&1\s*", parts[-1])
    if not redirect:
        raise ValueError("无法静态核验日志: 要求 > 或 >> 日志路径 2>&1")
    invocation, _, log_text = redirect.groups()
    if re.search(r"[;&|<>`$%*?(){}#\[\]\\]", invocation + log_text):
        raise ValueError("复杂 shell 调用/展开无法静态核验")
    command = shlex.split(invocation)
    logs = shlex.split(log_text)
    if not command or len(logs) != 1:
        raise ValueError("调用目标或日志路径无法静态核验")
    interpreters = {"bash", "sh", "/bin/bash", "/usr/bin/bash", "/bin/sh", "/usr/bin/sh"}
    if command[0] in interpreters:
        interpreter = shutil.which(command[0])
        if not interpreter or not Path(interpreter).is_file():
            raise ValueError("解释器不存在或不可执行")
        if len(command) < 2:
            raise ValueError("解释器后缺 watcher 目标")
        target = command[1]
    else:
        target = command[0]
    path = Path(target)
    if not path.is_absolute():
        raise ValueError("cron 目标必须是绝对路径 (不支持 wrapper 或解释器选项)")
    path = path.resolve()
    if path not in watchers or not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError("cron 目标未知、不存在或未通过 --watcher 检查")
    log = Path(logs[0]).resolve()
    if log.exists() and not log.is_file():
        raise ValueError("日志必须指向普通文件, 不得丢弃到 /dev/null")
    print(f"  PASS  静态调用绑定 {path}; stdout/stderr -> {logs[0]} (未执行, 未核验调度)")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"JSON 字段重复: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"非法 JSON 常量: {value}")


def check_receipt(path, watchers):
    if not path.is_file():
        raise ValueError("tick 不存在或不是普通文件")
    receipt = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=unique_object,
        parse_constant=reject_constant,
    )
    fields = {"watcher", "watcher_sha256", "observed_at", "exit_code"}
    if not isinstance(receipt, dict) or not fields.issubset(receipt):
        raise ValueError("tick 必须是含 watcher/watcher_sha256/observed_at/exit_code 的 JSON 对象")
    target = receipt["watcher"]
    if not isinstance(target, str) or not Path(target).is_absolute():
        raise ValueError("收据 watcher 必须是绝对路径")
    watcher = Path(target).resolve()
    if watcher not in watchers:
        raise ValueError("收据绑定未知 watcher 或 watcher 未通过检查")
    digest = receipt["watcher_sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest) or digest.lower() != watchers[watcher]:
        raise ValueError("watcher_sha256 与传入 watcher 当前字节不符")
    if type(receipt["exit_code"]) is not int or receipt["exit_code"] != 0:
        raise ValueError("exit_code 必须是整数 0 (不接受布尔值、浮点数或字符串)")
    observed = receipt["observed_at"]
    iso_timestamp = r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:[.,][0-9]+)?(?:Z|[+-](?:[01][0-9]|2[0-3])(?::?[0-5][0-9])?)"
    if not isinstance(observed, str) or not re.fullmatch(iso_timestamp, observed):
        raise ValueError("observed_at 必须是含时区 ISO8601 时间 (如 2026-09-22T08:00:00+08:00)")
    observed_time = datetime.fromisoformat(observed.replace("Z", "+00:00"))
    age_seconds = (datetime.now(timezone.utc) - observed_time).total_seconds()
    if age_seconds < 0:
        raise ValueError("observed_at 是未来时间")
    if args.max_tick_age_min > 0 and age_seconds > args.max_tick_age_min * 60:
        raise ValueError(f"收据过期: age={age_seconds / 60:.2f}min > {args.max_tick_age_min}min (按 observed_at)")
    print(f"  PASS  执行收据合同通过: watcher={watcher} observed_at={observed} age={age_seconds / 60:.2f}min")
    return watcher


print("=== A4w 派发前置: 双实证输入合同检查 (只读) ===")
print("收据是可审计合同, 不防恶意伪造; 本预检不执行 watcher、不制造 tick。")
watchers = {}
for value in args.watcher:
    print(f"[watcher] {value}")
    try:
        path = Path(value).resolve()
        watchers[path] = check_watcher(path)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        fail(str(exc))

for line in args.cron_line:
    print(f"[cron-line] {line}")
    try:
        check_cron(line, watchers)
    except (OSError, ValueError, RuntimeError) as exc:
        fail(str(exc))

covered = set()
for value in args.tick_marker:
    print(f"[tick-marker] {value}")
    try:
        covered.add(check_receipt(Path(value), watchers))
    except (OSError, ValueError, RuntimeError, OverflowError) as exc:
        fail(str(exc))
for watcher in watchers.keys() - covered:
    fail(f"watcher 缺少合格执行收据: {watcher}")

conclusion = "双实证齐备 (输入合同通过), 可派发" if rc == 0 else "不满足 — 停下修完再派发 (不得带假设硬跑)"
print(f"=== 结论: {conclusion} ===")
sys.exit(rc)
PY
