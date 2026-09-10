"""R1 (TASK-20260910-R1): status.sh 一页健康 + --json + 只读契约回归。

覆盖卡内可机器化的验收项:
  G-1 查看命令不再覆盖仓内 docs_lint 报告件 (本卡正题)
  G-2 --json 可机器解析 + schema_version + 六项键齐备 (取不到的项显式 UNAVAILABLE)
  G-3 人读与 JSON 同源
  G-4 零端点自证 + 端点守卫阳性对照 (curl/wget/nc 真被拦)
  只读归因: 并发他卡新建的未跟踪文件不得算本命令写盘 (R1 抽验修掉的假字段)

不锁 overall == PASS: 健康页会如实反映三方 HEAD 漂移等实时状态, 那属被测系统而非本测试。
"""
import hashlib
import json
import os
import re
import subprocess

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS = os.path.join("scripts", "graph", "status.sh")
REPORT = os.path.join("logs", "graph", "docs_lint_report.json")
SCHEMA_VERSION = "1.0"
SIX_ITEMS = ("head_alignment", "ports_processes", "loop_b", "b4_window",
             "crontab", "working_tree")
TOP_KEYS = ("schema_version", "generated_at", "host", "repo_root", "mode",
            "endpoint_calls", "endpoint_guard_refusals", "readonly_check",
            "overall", "failures", "warnings", "unavailable_items", "items", "extras")
MODEL_PORTS = (":8004", ":8006", ":8008")
EXTERNAL_WRITERS = {
    "logs/graph/dispatch_log.md", "logs/graph/docs_lint_report.json",
    "logs/graph/verify-report.json", "logs/graph/loop_b_last_status",
    "logs/graph/governance_drift_latest.md", "logs/graph/governance_cron.log",
    "logs/graph/pytest_latest.txt", "logs/graph/pytest_loopb.txt",
    "logs/graph/loop_b.log", "logs/graph/loop_a.log",
    "config/schema_suggestions.json",
}


def _source():
    with open(os.path.join(REPO, STATUS), encoding="utf-8") as fh:
        return fh.read()


def _report_sha():
    path = os.path.join(REPO, REPORT)
    if not os.path.isfile(path):
        return "ABSENT"
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _status(args, timeout=300, local_head=None):
    env = dict(os.environ)
    env["STATUS_ROOT"] = REPO
    env.pop("STATUS_LOCAL_HEAD", None)
    if local_head is not None:
        env["STATUS_LOCAL_HEAD"] = local_head
    return subprocess.run(["bash", STATUS] + list(args), cwd=REPO,
                          capture_output=True, text=True, timeout=timeout, env=env)


@pytest.fixture(scope="module")
def health():
    """跑一次真命令, 前后取报告件 sha; 六项/JSON/只读断言共用这一份实测。"""
    before = _report_sha()
    proc = _status(["--json"])
    after = _report_sha()
    assert proc.returncode == 0, proc.stdout[-3000:] + "\n" + proc.stderr[-3000:]
    return {"model": json.loads(proc.stdout), "sha_before": before, "sha_after": after}


@pytest.fixture(scope="module")
def inner():
    """把 status.sh 内嵌 python 取出来单调 (守卫与归因的单元级阳性对照)。"""
    block = re.search(r"<<'PY_EOF'\n(.*?)\nPY_EOF", _source(), re.S).group(1)
    ns = {"__name__": "status_sh_inner_under_test", "__file__": "<status.sh:inner>"}
    os.environ["STATUS_ROOT"] = REPO
    exec(compile(block, "status.sh:inner", "exec"), ns)
    return ns


# ------------------------------------------------------------ G-1 只读契约 (卡方正题)

def test_status_run_does_not_rewrite_in_repo_docs_lint_report(health):
    """跑 status.sh --json 前后, 仓内报告件 sha256 必须相同。"""
    assert health["sha_before"] == health["sha_after"], (
        "logs/graph/docs_lint_report.json 被查看命令覆盖: %s -> %s"
        % (health["sha_before"][:16], health["sha_after"][:16]))


def test_docs_lint_report_written_outside_repo(health):
    dl = health["model"]["extras"]["docs_lint"]
    assert dl["report_inside_repo"] is False, dl
    assert not os.path.realpath(dl["report_path"]).startswith(
        os.path.realpath(REPO) + os.sep), dl["report_path"]


def test_every_docs_lint_call_redirects_json_outside_repo():
    """:111 旧缺陷 = 调 docs_lint 不带 --json => 走 default 覆盖仓内报告件。"""
    hits = [ln for ln in _source().splitlines() if "scripts/docs_lint.py" in ln]
    assert hits, "status.sh 已不再调 docs_lint? 若是, 请同步更新本用例"
    for ln in hits:
        assert "--json" in ln, ln
    assert 'os.path.join(ROOT, "logs", "graph", "docs_lint_report.json")' not in _source()


# ------------------------------------------------------------- G-2 JSON 机器可解析

def test_json_parseable_with_stable_schema(health):
    model = health["model"]
    assert model["schema_version"] == SCHEMA_VERSION
    for key in TOP_KEYS:
        assert key in model, key


def test_six_items_present_and_never_silently_missing(health):
    model = health["model"]
    assert set(model["items"]) == set(SIX_ITEMS), sorted(model["items"])
    for name in SIX_ITEMS:
        assert "status" in model["items"][name], name
    for name in SIX_ITEMS:
        if model["items"][name]["status"] == "UNAVAILABLE":
            assert name in model["unavailable_items"], name
    assert set(model["unavailable_items"]) <= set(SIX_ITEMS)


# --------------------------------------------------------------- G-3 人读与 JSON 同源

def test_human_output_renders_all_six_sections():
    proc = _status([])
    assert proc.returncode == 0, proc.stderr[-2000:]
    text = proc.stdout
    for needle in ("-- 1.", "-- 2.", "-- 3.", "-- 4.", "-- 5.", "-- 6.",
                   "三方 HEAD", "端口与进程", "Loop B", "B4", "crontab", "脏件清单",
                   "endpoint_calls=0", "取不到的项"):
        assert needle in text, needle


def test_human_and_json_share_one_collection_source():
    src = _source()
    assert "def collect():" in src and "def render_text(m):" in src
    assert src.count("MODEL = collect()") == 1, "两种形态必须渲染同一份 dict"


# ------------------------------------------------------------- G-4 零端点自证

def test_zero_endpoint_self_attestation(health):
    model = health["model"]
    assert model["endpoint_calls"] == 0, model["endpoint_calls"]
    assert model["items"]["ports_processes"]["connect_probe"] is False
    watched = {p["port"] for p in model["items"]["ports_processes"]["ports"]}
    for port in ("8004", "8006", "8008"):
        assert port in watched, port


@pytest.mark.parametrize("cmd", (
    ["curl", "-s", "http://127.0.0.1:8004/v1/models"],
    ["wget", "-qO-", "http://localhost:8006/"],
    ["nc", "-z", "127.0.0.1", "8008"],
))
def test_endpoint_guard_rejects_networking(inner, cmd):
    rc, _, err = inner["run"](cmd)
    assert rc == 126, (cmd, rc, err)
    assert "endpoint guard refused" in err, err


def test_endpoint_guard_lets_local_reads_through(inner):
    rc, _, err = inner["run"](["true"])
    assert rc == 0, err


# ------------------------------------------------------- 只读归因 (含 R1 假字段回归)

def test_untracked_new_files_are_info_only_not_repo_writes(inner):
    """并发另一张卡新建未跟踪文件 => 记信息项, 不得判成本命令写盘。

    同时是 R1 抽验修掉的假字段回归: repo_digest() 早先只走 tracked 路径,
    untracked_added 恒为空。
    """
    d0, p0, u0 = inner["repo_digest"]()
    fake = set(u0) | {"zz_r1_probe_untracked.py"}
    rv = inner["readonly_verdict"](d0, d0, p0, p0, u0, fake)
    assert rv["untracked_added"] == ["zz_r1_probe_untracked.py"], rv
    assert rv["repo_writes"] == 0, rv
    assert "set(untracked_paths())" in _source(), "repo_digest 未采集未跟踪集 => 假字段复发"


def test_repo_write_by_status_is_attributed_to_us(inner):
    """反向对照: 非白名单的 tracked 文件内容变化必须计入 repo_writes。"""
    p0 = {"scripts/graph/status.sh": "aaa"}
    p1 = {"scripts/graph/status.sh": "bbb"}
    rv = inner["readonly_verdict"]("d0", "d1", p0, p1, set(), set())
    assert rv["repo_writes"] == 1, rv
    rv2 = inner["readonly_verdict"]("d0", "d1",
                                    {"logs/graph/loop_b.log": "aaa"},
                                    {"logs/graph/loop_b.log": "bbb"}, set(), set())
    assert rv2["repo_writes"] == 0 and rv2["external_writer_touches"], rv2


# ---------------------------------------------------------------- E-1 本地 HEAD 不伪造

def test_local_head_is_caller_supplied_not_fabricated():
    proc = _status(["--fast", "--json"], local_head="")
    assert proc.returncode == 0, proc.stderr[-2000:]
    head = json.loads(proc.stdout)["items"]["head_alignment"]
    assert head["local_head"] == "UNAVAILABLE", head
    assert head["verdict"] != "ALIGNED", head


def test_local_head_supplied_completes_three_way_check():
    sha = subprocess.run(["git", "--no-optional-locks", "rev-parse", "HEAD"],
                         cwd=REPO, capture_output=True, text=True).stdout.strip()
    proc = _status(["--fast", "--json"], local_head=sha)
    assert proc.returncode == 0, proc.stderr[-2000:]
    head = json.loads(proc.stdout)["items"]["head_alignment"]
    assert head["local_head"] == sha[:7], head
    assert head["verdict"] in ("ALIGNED", "DRIFT", "PARTIAL_ALIGNED"), head


def test_unknown_argument_is_a_hard_error():
    proc = _status(["--no-such-flag"])
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "unknown argument" in proc.stderr, proc.stderr


# ---------------------------------------------------------------- 外部写入者白名单

def test_external_writer_whitelist_matches_loop_b_口径(health):
    rc = health["model"]["readonly_check"]
    assert rc["measured"] is True, rc
    for path in rc["external_writer_touches"]:
        assert path in EXTERNAL_WRITERS, path
    assert rc["repo_writes"] == 0, rc
