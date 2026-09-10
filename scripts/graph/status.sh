#!/usr/bin/env bash
# status.sh — 一页健康 (L1) + 机器可读输出 (docs/29 L3 前提 ⑤)
# 用法:
#   bash scripts/graph/status.sh                     # 人读一页健康
#   bash scripts/graph/status.sh --json              # 同上数据, JSON 渲染
#   STATUS_LOCAL_HEAD=$(git -C ~/wzh/projects/agents_final_tech rev-parse --short HEAD) \
#     ssh jinrong-dev "STATUS_LOCAL_HEAD=$LOCAL_HEAD bash ~/wzh/projects/agents_final_tech/scripts/graph/status.sh"
#     ^ 三方 HEAD 的「本地侧」无法从 GB10 反查 (无回连 ssh) ⇒ 由调用方经 STATUS_LOCAL_HEAD 传入;
#       未传入时该项显式标 UNAVAILABLE, 不伪造对齐结论 (TASK-20260910-R1 前提 E-1 实测)。
#
# 只读契约 (TASK-20260910-R1, 决策 19=A; 承审计 F09/A20):
#   1. 不改任何仓内文件 —— docs_lint 的 --json 报告重定向到仓外临时目录 (A20 销账)。
#   2. 零端点 —— 不向 :8004/:8006/:8008 发任何请求; 端口只用 ss 列举, 不连接。
#      run() 内置 endpoint guard, 命令串含 http:// 或模型端口即拒绝执行。
#   3. 单一数据源 —— 采集一次成 dict, 人读与 --json 是同结构的两种渲染 (不得各算一遍)。
#
# 2026-08-22 T3: 端口 +8006/8007/8008; Loop B 最近 PASS; B4 两列口径 (复用 b4_checkpoint.compute)。
# 2026-09-10 R1: 一页健康六项 + --json + 消除 docs_lint 写副作用。
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 2

MODE="text"
FAST="${STATUS_FAST:-0}"
LOCAL_HEAD="${STATUS_LOCAL_HEAD:-}"
while [ $# -gt 0 ]; do
  case "$1" in
    --json) MODE="json" ;;
    --fast) FAST=1 ;;
    --local-head) shift; LOCAL_HEAD="${1:-}" ;;
    --local-head=*) LOCAL_HEAD="${1#*=}" ;;
    -h|--help) sed -n '1,22p' "$0"; exit 0 ;;
    *) echo "status.sh: unknown argument: $1 (supported: --json --local-head <sha> --fast)" >&2; exit 2 ;;
  esac
  shift
done

PY="./venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"
[ -n "$PY" ] || { echo "[!] status.sh: python 不可用" >&2; exit 3; }

STATUS_MODE="$MODE" STATUS_LOCAL_HEAD="$LOCAL_HEAD" STATUS_ROOT="$ROOT" STATUS_FAST="$FAST" \
  exec "$PY" - <<'PY_EOF'
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.environ.get("STATUS_ROOT") or os.getcwd()
MODE = os.environ.get("STATUS_MODE", "text")
LOCAL_HEAD = (os.environ.get("STATUS_LOCAL_HEAD") or "").strip()

SCHEMA_VERSION = "1.0"
NA = "UNAVAILABLE"
MODEL_PORTS = (":8004", ":8006", ":8008")
FORBIDDEN = ("curl", "wget", "http://", "https://", "nc ", "ncat") + MODEL_PORTS
WATCH_PORTS = ("5050", "4096", "8004", "8005", "8006", "8007", "8008", "8100", "15432")
PROTECTED_TMUX = ("graph-loop-b", "opencode-serve")
B4_ROLLBACK_POINT = 3294          # Phase 0 回滚点 (2026-08-21); 半开区间口径同 b4_checkpoint.py
DISPATCH_STALE_MIN = 240          # 超过视为陈旧 (warn), 与旧版人读习惯一致
PG_WARN_CONNS = 80
RUNTIME_PREFIXES = ("logs/",)     # 脏件清单中属运行产物 => 只列不计入 verdict
# 外部写入者白名单: Loop B (scripts/graph/loop_b_verify.sh:222 同口径) 每 30 分钟
# 与夜间 cron 会写这些 tracked 运行产物。它们若在一次 status.sh 运行窗口内变动,
# 归因是外部进程而非本命令, 故单列 external_writer_touches, 不计入 repo_writes。
EXTERNAL_WRITERS = (
    "logs/graph/dispatch_log.md", "logs/graph/docs_lint_report.json",
    "logs/graph/verify-report.json", "logs/graph/loop_b_last_status",
    "logs/graph/governance_drift_latest.md", "logs/graph/governance_cron.log",
    "logs/graph/pytest_latest.txt", "logs/graph/pytest_loopb.txt",
    "logs/graph/loop_b.log", "logs/graph/loop_a.log",
    "config/schema_suggestions.json",
)

endpoint_calls = 0                 # 零端点自证: run() 是唯一外部命令出口, 且无任何 HTTP 客户端调用点
guard_refusals = []                # 守卫拦下的命令 = 反证「守卫真的在生效」(阳性对照见测试)


def run(cmd, timeout=20, shell=False):
    """Read-only command runner with an endpoint guard. Never raises."""
    joined = cmd if shell else " ".join(cmd)
    for bad in FORBIDDEN:
        if bad in joined:
            guard_refusals.append("%s <- %s" % (bad, joined[:120]))
            return 126, "", "endpoint guard refused: %s" % bad
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                           timeout=timeout, shell=shell)
        return p.returncode, p.stdout or "", p.stderr or ""
    except FileNotFoundError as exc:
        return 127, "", "command not found: %s" % exc
    except Exception as exc:
        return 125, "", "%s: %s" % (type(exc).__name__, exc)


def git(*args, **kw):
    # --no-optional-locks: 拒绝 git 顺手写 .git/index (只读契约)
    return run(["git", "--no-optional-locks"] + list(args), **kw)


def read_text(rel):
    path = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except Exception:
        return None


def tail_last_match(rel, needle, max_bytes=1 << 19):
    text = read_text(rel)
    if text is None:
        return None, NA
    text = text[-max_bytes:]
    hit = ""
    for line in text.splitlines():
        if needle in line:
            hit = line
    return hit, ("OK" if hit else "NONE")


# ------------------------------------------------- 只读契约自证 (仓内文件内容摘要)

def tracked_paths():
    rc, out, _ = git("ls-files", "-z")
    if rc != 0:
        return []
    return [p for p in out.split("\0") if p]


def untracked_paths():
    rc, out, _ = git("ls-files", "--others", "--exclude-standard", "-z")
    return [p for p in out.split("\0") if p] if rc == 0 else []


def _digest_of(paths):
    agg = hashlib.sha256()
    per = {}
    for path in sorted(set(paths)):
        fp = os.path.join(ROOT, path)
        try:
            if not os.path.isfile(fp):
                per[path] = "ABSENT"
                continue
            h = hashlib.md5()
            with open(fp, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 16), b""):
                    h.update(chunk)
            per[path] = h.hexdigest()
        except Exception as exc:
            per[path] = "ERR:%s" % type(exc).__name__
    for path in sorted(per):
        agg.update(("%s|%s\n" % (path, per[path])).encode("utf-8", "replace"))
    return agg.hexdigest(), per


def repo_digest():
    """内容级摘要: (排序后的 路径+md5) 聚合成一个 sha256, 外加逐文件映射供 diff。

    只读实现, 不写任何文件。

    归因范围 (2026-09-10 R1 定, 记卡 §9 已知限制):
      * tracked (git 索引内) 文件的内容变化 => 计入 repo_writes (本命令写过仓内文件);
      * 未跟踪新增 => 只作信息项 untracked_added。理由 = 同仓可能并发另一张卡的合法
        新建文件 (例: 2026-09-10 A4/A5 批), 把「别人新建文件」判成本命令写盘 = 假阳性。
        本命令自身唯一的写盘点是 docs_lint --json, 已被重定向到仓外并单列断言。
    返回 (digest, per_tracked, untracked_set); 未跟踪集单独取, 否则
    untracked_added 永远为空 = 假字段 (2026-09-10 R1 抽验发现并修)。
    """
    digest, per = _digest_of(tracked_paths())
    return digest, per, set(untracked_paths())


def readonly_verdict(before, after, per_before, per_after, unc_before, unc_after):
    """前/后仓内内容摘要之差 = 本命令是否写过仓内文件的实测。

    归因口径: 外部写入者白名单内的件变动记 external_writer_touches (不记账到本命令);
    其余任何变动 = repo_writes > 0 => 只读契约破裂 => overall FAIL。
    """
    changed = sorted(p for p in set(per_before) | set(per_after)
                     if per_before.get(p) != per_after.get(p))
    mine = [p for p in changed if p not in EXTERNAL_WRITERS]
    extern = [p for p in changed if p in EXTERNAL_WRITERS]
    untracked_added = sorted(unc_after - unc_before)
    untracked_gone = sorted(unc_before - unc_after)
    return {"measured": bool(before and after),
            "untracked_added": untracked_added, "untracked_removed": untracked_gone,
            "digest_before": before[:16] if before else NA,
            "digest_after": after[:16] if after else NA,
            "changed_paths": changed,
            "external_writer_touches": extern,
            "repo_writes": len(mine)}


# ---------------------------------------------------------------- 采集: 一次成模型

def _same_commit(a, b):
    """SHA 前缀安全比较: 短哈希 (7+) 与全哈希 (40) 混用不得误判为漂移。

    R1 自测抓到: 调用方按卡内示例传 40 位全 SHA 时, 早先按字符串相等比较 => 假 DRIFT。
    """
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    if not a or not b or a == NA or b == NA:
        return False
    n = min(len(a), len(b))
    return a[:n] == b[:n]


def item_head():
    rc, out, _ = git("rev-parse", "HEAD")
    gb10_full = out.strip() if rc == 0 and out.strip() else NA
    rc2, out2, _ = git("log", "-1", "--format=%ci", "HEAD")
    when = (out2.strip() or NA)[:16]
    rc3, out3, err3 = git("ls-remote", "origin", "main", timeout=12)
    github_full = out3.split()[0] if rc3 == 0 and out3.strip() else NA
    local_full = LOCAL_HEAD or NA
    have = [p for p in (github_full, local_full) if p != NA]
    if gb10_full == NA:
        verdict = NA
    elif not have:
        verdict = NA
    elif all(_same_commit(gb10_full, p) for p in have):
        verdict = "ALIGNED" if len(have) == 2 else "PARTIAL_ALIGNED"
    else:
        verdict = "DRIFT"
    gb10 = gb10_full[:7] if gb10_full != NA else NA
    github = github_full[:7] if github_full != NA else NA
    local = local_full[:7] if local_full != NA else NA
    notes = []
    if github == NA:
        notes.append("github 侧不可达: %s" % (err3.strip()[:120] or "ls-remote 无输出"))
    if local == NA:
        notes.append("本地侧 HEAD 需由调用方传入 STATUS_LOCAL_HEAD/--local-head (GB10 无回连通道)")
    return {"status": "OK" if gb10 != NA else NA,
            "gb10_head": gb10, "gb10_head_time": when,
            "github_head": github, "local_head": local,
            "verdict": verdict, "notes": notes}


def item_ports():
    rc, out, err = run(["ss", "-ltnp"])
    tool = "ss"
    if rc != 0 or not out.strip():
        rc, out, err = run(["netstat", "-ltn"])
        tool = "netstat"
    if not out.strip():
        return {"status": NA, "reason": (err or out or "ss/netstat 均不可用").strip()[:120],
                "source": tool, "connect_probe": False, "ports": [],
                "tmux_sessions": [], "tmux_status": NA, "protected_missing": []}
    listening = {}
    for line in out.splitlines()[1:]:
        cols = line.split()
        if len(cols) < 4:
            continue
        local = cols[3]
        port = local.rsplit(":", 1)[-1]
        if not port.isdigit():
            continue
        proc = ""
        for tok in cols:
            if tok.startswith("users:"):
                proc = tok.split('"')[1] if '"' in tok else tok
                break
        listening.setdefault(port, proc)
    ports = [{"port": p, "state": "UP" if p in listening else "down",
              "process": listening.get(p) or ""} for p in WATCH_PORTS]
    rc2, out2, err2 = run(["tmux", "ls"])
    both = (out2 + err2).lower()
    if rc2 == 0 and out2.strip():
        sessions = sorted(l.split(":")[0] for l in out2.splitlines() if l.strip())
        sess_status = "OK"
    elif "no server" in both or "no sessions" in both or "not found" not in both and rc2 == 1:
        sessions, sess_status = [], "OK"
    else:
        sessions, sess_status = [], NA
    missing = [p for p in PROTECTED_TMUX if sess_status == "OK" and p not in sessions]
    return {"status": "OK", "source": tool, "connect_probe": False, "ports": ports,
            "tmux_sessions": sessions, "tmux_status": sess_status,
            "protected_missing": missing}


def item_loop_b():
    last = read_text("logs/graph/loop_b_last_status")
    last = last.strip() if last is not None else NA
    vr = {"status": NA}
    raw = read_text("logs/graph/verify-report.json")
    if raw is not None:
        try:
            d = json.loads(raw)
            vr = {"status": "OK", "timestamp": d.get("timestamp", NA),
                  "overall": d.get("overall", NA), "head_commit": d.get("head_commit", NA)}
        except Exception as exc:
            vr = {"status": NA, "reason": "verify-report.json 解析失败: %s" % type(exc).__name__}
    line, lstatus = tail_last_match("logs/graph/loop_b.log", "REPORT: overall=")
    return {"status": "OK" if (last != NA or vr["status"] == "OK") else NA,
            "last_status_file": last, "verify_report": vr,
            "log_last_report": {"status": lstatus, "line": line or ""}}


def item_b4():
    rel = "logs/graph/b4_ask_log.jsonl"
    text = read_text(rel)
    if text is None:
        return {"status": NA, "reason": "%s 缺失" % rel}
    lines = text.splitlines()
    rows = []
    for ln in lines:
        ln = ln.strip()
        if ln:
            try:
                rows.append(json.loads(ln))
            except Exception:
                pass
    err = sum(1 for r in rows if r.get("status") == "error")
    last = rows[-1].get("ts", NA) if rows else "-"
    seg = {}
    try:
        sys.path.insert(0, os.path.join(ROOT, "scripts", "graph"))
        from b4_checkpoint import compute       # 只读纯函数; main() 才写文件, 不走
        for key, start in (("after_rollback_point", B4_ROLLBACK_POINT), ("full", 0)):
            c = compute(lines, start)
            c["fb_rate_pct"] = c.get("fb_rate")
            seg[key] = c
    except Exception as exc:
        seg = {"status": NA, "reason": "b4_checkpoint.compute 不可用: %s" % exc}
    return {"status": "OK", "log": rel, "lines": len(lines), "error_rows": err,
            "last_ts": last, "rollback_point": B4_ROLLBACK_POINT, "segments": seg}


def item_crontab():
    rc, out, err = run(["crontab", "-l"])
    if rc != 0 and not out.strip():
        if "no crontab" in (out + err).lower():
            return {"status": "OK", "count": 0, "entries": [], "note": "当前用户无 crontab 条目"}
        return {"status": NA, "reason": (err or out).strip()[:120] or "crontab -l 退出码 %s" % rc}
    entries = [l for l in out.splitlines() if l.strip() and not l.strip().startswith("#")]
    return {"status": "OK", "count": len(entries), "entries": entries}


def item_dirty():
    rc, out, err = git("status", "--porcelain")
    if rc != 0:
        return {"status": NA, "reason": (err or out).strip()[:120] or "git status 退出码 %s" % rc}
    entries = [l for l in out.splitlines() if l.strip()]
    source = [e for e in entries if e.strip().split(maxsplit=1)[-1].split("/")[0] not in
              tuple(p.rstrip("/") for p in RUNTIME_PREFIXES)]
    return {"status": "OK", "count": len(entries), "entries": entries,
            "non_runtime_count": len(source)}


def extra_dispatch():
    rel = "logs/graph/dispatch_log.md"
    text = read_text(rel)
    if text is None:
        return {"status": NA, "reason": "%s 缺失" % rel}
    lines = [l for l in text.splitlines() if l.strip()]
    age_min = -1
    try:
        age_min = int((dt.datetime.now().timestamp() -
                       os.stat(os.path.join(ROOT, rel)).st_mtime) / 60)
    except Exception:
        pass
    return {"status": "OK", "last_line": (lines[-1][:120] if lines else ""),
            "updated_minutes_ago": age_min}


def extra_frozen():
    rel = "scripts/graph/frozen_hashes.txt"
    text = read_text(rel)
    if text is None:
        return {"status": NA, "reason": "%s 缺失" % rel}
    bad, checked = [], 0
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cols = line.split()
        if len(cols) < 2:
            continue
        want, path = cols[0], cols[1]
        checked += 1
        fp = path if os.path.isabs(path) else os.path.join(ROOT, path)
        if not os.path.isfile(fp):
            bad.append("missing: %s" % path)
            continue
        h = hashlib.md5()
        try:
            with open(fp, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 16), b""):
                    h.update(chunk)
        except Exception as exc:
            bad.append("unreadable: %s (%s)" % (path, type(exc).__name__))
            continue
        if h.hexdigest() != want:
            bad.append("drift: %s" % path)
    return {"status": "OK" if not bad else "FAIL", "checked": checked, "violations": bad}


def extra_docs_lint(tmpdir):
    """A20 修复点: --json 重定向到仓外临时目录 => 查看命令不再覆盖仓内报告件。"""
    report = os.path.join(tmpdir, "docs_lint_report.json")
    py = "./venv/bin/python"
    if not os.path.isdir(os.path.join(ROOT, "venv", "bin")):
        py = sys.executable
    rc, out, err = run([py, "scripts/docs_lint.py", "--json", report], timeout=120)
    first = (out.splitlines() or [""])[0].strip()
    summary = {"status": "OK" if rc in (0, 1) else NA, "exit_code": rc,
               "headline": first or (err.strip()[:120] or NA), "report_path": report,
               "report_inside_repo": report.startswith(ROOT + os.sep)}
    txt = read_text(report)
    if txt:
        try:
            d = json.loads(txt)
            summary["overall"] = d.get("overall", NA)
            summary["fail_count"] = len(d.get("fails", []))
            summary["warn_count"] = len(d.get("warns", []))
            summary["fails"] = d.get("fails", [])
        except Exception as exc:
            summary["parse_error"] = type(exc).__name__
    return summary


def extra_sync_skills(tmpdir):
    rc, out, err = run(["bash", "scripts/graph/sync_skills.sh", "--check"], timeout=120)
    line = (out.strip().splitlines() or [""])[-1].strip()
    return {"status": "OK" if rc in (0, 1) else NA, "exit_code": rc,
            "verdict": line or "执行失败", "repo_side_effects": False}


def extra_runtime():
    """PG 池 + opencode.db (既有 T2 项; 仓外只读)。"""
    out = {}
    rc, o, _ = run(["docker", "exec", "pgvector_15432", "psql", "-U", "postgres", "-t", "-A", "-c",
                    "select count(*) from pg_stat_activity where datname is not null"], timeout=25)
    rc2, o2, _ = run(["docker", "exec", "pgvector_15432", "psql", "-U", "postgres", "-t", "-A", "-c",
                      "select count(*) from pg_stat_activity where state='idle' and datname is not null"],
                     timeout=25)
    total = o.strip() or NA
    idle = o2.strip() or NA
    out["pg_pool"] = {"status": "OK" if total != NA else NA, "total": total, "idle": idle,
                      "thresholds": {"warn": PG_WARN_CONNS, "fail": 95}}
    db = os.path.expanduser("~/.local/share/opencode/opencode.db")
    if not os.path.isfile(db):
        out["opencode_db"] = {"status": NA, "reason": "库文件不存在: %s" % db}
        return out
    try:
        import sqlite3
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)   # 强制只读, 不落 WAL/SHM
        s, pa, m = (con.execute("select count(*) from " + t).fetchone()[0]
                    for t in ("session", "part", "message"))
        con.close()
        out["opencode_db"] = {"status": "OK", "session": s, "part": pa, "message": m}
    except Exception as exc:
        out["opencode_db"] = {"status": NA, "reason": "%s: %s" % (type(exc).__name__, exc)}
    return out


def collect():
    fast = (os.environ.get("STATUS_FAST") or "0") == "1"
    dig_before, per_before, unc_before = (NA, {}, set()) if fast else repo_digest()
    tmpdir = tempfile.mkdtemp(prefix="status_sh_", dir=os.environ.get("TMPDIR") or "/tmp")
    try:
        items = {
            "head_alignment": item_head(),
            "ports_processes": item_ports(),
            "loop_b": item_loop_b(),
            "b4_window": item_b4(),
            "crontab": item_crontab(),
            "working_tree": item_dirty(),
        }
        extras = {
            "dispatch_log": extra_dispatch(),
            "frozen_hashes": extra_frozen(),
            "docs_lint": extra_docs_lint(tmpdir),
            "sync_skills": extra_sync_skills(tmpdir),
            "runtime": extra_runtime(),
        }
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    dig_after, per_after, unc_after = (NA, {}, set()) if fast else repo_digest()
    readonly = {"status": NA, "reason": "--fast 跳过实测"} if fast else \
        readonly_verdict(dig_before, dig_after, per_before, per_after,
                         unc_before, unc_after)

    fails, warns = [], []
    for name, it in items.items():
        if it.get("status") == NA:
            warns.append("%s: %s" % (name, it.get("reason", NA)))
        elif it.get("verdict") == "DRIFT":
            fails.append("head_alignment: DRIFT %s" % it)
        elif it.get("verdict") == "PARTIAL_ALIGNED":
            warns.append("head_alignment: 本地侧未传入, 只核得两方")
    if items["ports_processes"].get("protected_missing"):
        warns.append("ports_processes: 缺 tmux 会话 %s" % items["ports_processes"]["protected_missing"])
    vr = items["loop_b"]["verify_report"]
    if vr.get("status") == "OK" and vr.get("overall") not in ("PASS",):
        fails.append("loop_b: overall=%s" % vr.get("overall"))
    if items["working_tree"].get("status") == "OK" and items["working_tree"].get("non_runtime_count"):
        warns.append("working_tree: %s 个非运行产物脏件" % items["working_tree"]["non_runtime_count"])
    if extras["frozen_hashes"].get("status") == "FAIL":
        fails.append("frozen_hashes: %s" % "; ".join(extras["frozen_hashes"]["violations"][:3]))
    dl = extras["docs_lint"]
    if dl.get("overall") == "FAIL":
        fails.append("docs_lint: %s fail" % dl.get("fail_count"))
    if dl.get("warn_count"):
        warns.append("docs_lint: %s warn" % dl.get("warn_count"))
    if extras["sync_skills"].get("exit_code") not in (0,):
        warns.append("sync_skills: %s" % extras["sync_skills"].get("verdict"))
    dp = extras["dispatch_log"]
    if dp.get("updated_minutes_ago", -1) > DISPATCH_STALE_MIN:
        warns.append("dispatch_log: 末条距今 %s 分钟 (> %s)" % (dp["updated_minutes_ago"], DISPATCH_STALE_MIN))
    pg = extras["runtime"]["pg_pool"]
    if pg.get("status") == "OK" and str(pg.get("total", "")).isdigit() and int(pg["total"]) > PG_WARN_CONNS:
        warns.append("pg_pool: total=%s" % pg["total"])
    if readonly.get("repo_writes"):
        fails.append("readonly_contract: 查看命令改动了 %s 个仓内文件: %s" % (
            readonly["repo_writes"], ", ".join(
                [p for p in readonly["changed_paths"] if p not in EXTERNAL_WRITERS][:5])))
    if readonly.get("external_writer_touches"):
        warns.append("readonly_contract: 窗口内 %s 个运行产物被外部进程改动 (白名单归因, 非本命令): %s" % (
            len(readonly["external_writer_touches"]),
            ", ".join(readonly["external_writer_touches"][:4])))
    unavailable = sorted(k for k, v in items.items() if v.get("status") == NA)
    overall = "FAIL" if fails else ("WARN" if warns else "PASS")

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "host": os.uname().nodename,
        "repo_root": ROOT,
        "mode": MODE,
        "endpoint_calls": endpoint_calls,
        "endpoint_guard_refusals": list(guard_refusals),
        "readonly_check": readonly,
        "overall": overall,
        "failures": fails,
        "warnings": warns,
        "unavailable_items": unavailable,
        "items": items,
        "extras": extras,
    }


# ---------------------------------------------------------------- 渲染: 同源两形态

def st(status):
    return status if status in (NA,) else status


def kv(v):
    return v if v not in (None, "") else NA


def render_text(m):
    L = []
    it, ex = m["items"], m["extras"]
    L.append("== status.sh 一页健康 %s | host=%s ==" % (m["generated_at"], m["host"]))
    for f in m["failures"]:
        L.append("[X] FAIL   %s" % f)
    for w in m["warnings"]:
        L.append("[!] WARN   %s" % w)
    rc = m["readonly_check"]
    L.append("overall: %s   endpoint_calls=%s   repo_writes=%s   guard_refusals=%s" % (
        m["overall"], m["endpoint_calls"],
        rc.get("repo_writes", NA) if rc.get("measured") else NA, len(m["endpoint_guard_refusals"])))
    if rc.get("measured"):
        L.append("readonly : digest %s -> %s; 本命令写入 %s 项; 外部进程窗口内触碰 %s 项" % (
            rc.get("digest_before"), rc.get("digest_after"), rc.get("repo_writes"),
            ", ".join(rc.get("external_writer_touches", [])) or "0"))
    else:
        L.append("readonly : %s: %s" % (NA, rc.get("reason")))

    h = it["head_alignment"]
    L.append("-- 1. 三方 HEAD 对齐 [%s] --" % h["verdict"])
    L.append("  GB10   : %s (%s)" % (kv(h["gb10_head"]), kv(h["gb10_head_time"])))
    L.append("  GitHub : %s" % kv(h["github_head"]))
    L.append("  本地侧 : %s" % kv(h["local_head"]))
    for n in h["notes"]:
        L.append("  note   : %s" % n)

    p = it["ports_processes"]
    L.append("-- 2. 端口与进程 [%s] (只列举不连接; 源=%s) --" % (p["status"], kv(p.get("source", NA))))
    if p["status"] == NA:
        L.append("  %s: %s" % (NA, kv(p.get("reason"))))
    else:
        L.append("  " + " ".join("%s=%s%s" % (":" + x["port"], x["state"],
                  "(" + x["process"] + ")" if x["process"] else "") for x in p["ports"]))
        L.append("  tmux   : %s" % (", ".join(p["tmux_sessions"]) or p["tmux_status"]))
        L.append("  禁杀   : %s%s" % (", ".join(PROTECTED_TMUX),
                  "" if not p["protected_missing"] else "  [!] 缺: " + ", ".join(p["protected_missing"])))

    lb = it["loop_b"]
    L.append("-- 3. Loop B 最近 PASS [%s] --" % lb["status"])
    L.append("  last_status : %s" % kv(lb["last_status_file"]))
    vr = lb["verify_report"]
    if vr["status"] == NA:
        L.append("  verify-report: %s %s" % (NA, kv(vr.get("reason"))))
    else:
        L.append("  verify-report: %s overall=%s head=%s" % (kv(vr["timestamp"]), kv(vr["overall"]), kv(vr["head_commit"])))
    lr = lb["log_last_report"]
    L.append("  log 末条  : %s" % (kv(lr["line"]) or lr["status"]))

    b4 = it["b4_window"]
    L.append("-- 4. B4 两列口径 [%s] --" % b4["status"])
    if b4["status"] == NA:
        L.append("  %s: %s" % (NA, kv(b4.get("reason"))))
    else:
        L.append("  asks=%s (error=%s) last=%s" % (b4["lines"], b4["error_rows"], kv(b4["last_ts"])))
        seg = b4["segments"]
        if seg.get("status") == NA:
            L.append("  segments: %s %s" % (NA, kv(seg.get("reason"))))
        else:
            for label, key in (("回滚点后 (%d 起)" % (B4_ROLLBACK_POINT + 1), "after_rollback_point"),
                               ("全量 (1 起)", "full")):
                c = seg[key]
                fr = "N/A" if c.get("fb_rate_pct") is None else "%s%%" % c["fb_rate_pct"]
                L.append("  %s: attempted=%s completed=%s fallback_rate=%s "
                         "(timeout_fb=%s fast_fb=%s direct=%s)" % (
                             label, c.get("attempted"), c.get("agent_completed"), fr,
                             c.get("agent_timeout_fb"), c.get("fast_fallback"), c.get("pure_direct")))

    ct = it["crontab"]
    L.append("-- 5. crontab 现行条目 [%s] --" % ct["status"])
    if ct["status"] == NA:
        L.append("  %s: %s" % (NA, kv(ct.get("reason"))))
    elif not ct["entries"]:
        L.append("  (无条目) %s" % kv(ct.get("note")))
    else:
        for e in ct["entries"]:
            L.append("  %s" % e)

    wt = it["working_tree"]
    L.append("-- 6. GB10 脏件清单 [%s] --" % wt["status"])
    if wt["status"] == NA:
        L.append("  %s: %s" % (NA, kv(wt.get("reason"))))
    elif not wt["entries"]:
        L.append("  clean")
    else:
        L.append("  %s 项 (其中非运行产物 %s 项):" % (wt["count"], wt["non_runtime_count"]))
        for e in wt["entries"][:15]:
            L.append("    %s" % e)
        if len(wt["entries"]) > 15:
            L.append("    ... 另 %s 项" % (len(wt["entries"]) - 15))

    L.append("-- 附加项 --")
    dp = ex["dispatch_log"]
    if dp["status"] == NA:
        L.append("  dispatch_log : %s %s" % (NA, kv(dp.get("reason"))))
    else:
        L.append("  dispatch_log : 末条距今 %s 分钟 | %s" % (dp["updated_minutes_ago"], dp["last_line"]))
    fz = ex["frozen_hashes"]
    L.append("  frozen_hashes: %s (%s 项)%s" % ("PASS" if fz["status"] == "OK" else fz["status"],
             fz.get("checked", NA), "" if fz["status"] == "OK" else " -> " + "; ".join(fz["violations"][:3])))
    dl = ex["docs_lint"]
    L.append("  docs_lint    : %s (exit=%s; 报告件落仓外, 仓内零写入)" % (kv(dl.get("overall", dl["status"])), dl["exit_code"]))
    for f in dl.get("fails", [])[:3]:
        L.append("    FAIL %s" % f)
    ss = ex["sync_skills"]
    L.append("  sync_skills  : %s" % kv(ss["verdict"]))
    rt = ex["runtime"]
    pg = rt["pg_pool"]
    L.append("  PG 池        : %s" % (NA if pg["status"] == NA else "total=%s idle=%s (warn>%s/fail>95)"
             % (pg["total"], pg["idle"], PG_WARN_CONNS)))
    od = rt["opencode_db"]
    L.append("  opencode.db  : %s" % (NA if od["status"] == NA else "session=%s part=%s message=%s"
             % (od["session"], od["part"], od["message"])))
    L.append("  取不到的项   : %s" % (", ".join(m["unavailable_items"]) or "无"))
    L.append("== end ==")
    return "\n".join(L)


if __name__ == "__main__":
    MODEL = collect()
    if MODE == "json":
        print(json.dumps(MODEL, ensure_ascii=False, indent=1))
    else:
        print(render_text(MODEL))
    sys.exit(0)          # 健康页恒 0: verdict 在 overall 字段里, 不让 set -e 调用方误伤
PY_EOF
