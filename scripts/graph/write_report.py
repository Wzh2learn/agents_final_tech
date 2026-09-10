"""Loop B report writer - called by loop_b_verify.sh

R1 (2026-08-13): extended with three incremental check counts (qa_canary /
git_alignment / docs_lint). Missing extra args are treated as -1 = SKIP so
old 5-arg invocations keep working.

F03 修复 (2026-09-10, TASK-20260910-A4A5A4W) — **单一 verdict 同源**:
  改前本模块自己用 counts 重算一遍 overall, 而 bash 侧 write_report() 也算一遍
  **且公式不同** (bash 漏 pg_pool) => 同一个 PG-only 故障得到 JSON=FAIL /
  SHELL=PASS 两份互相矛盾的判定。
  现在 overall **只由调用方 (loop_b_verify.sh) 判定并以第 12 个参数传入**,
  本模块只消费; 重算值仅用于一致性交叉核对, 一旦发现与传入值不符就把
  `verdict_consistency` 标成 MISMATCH 并以非零退出码暴露, 不再各写各的。
"""
import json
import datetime
import sys


def _status(count: int) -> str:
    if count < 0:
        return "SKIP"
    return "PASS" if count == 0 else "FAIL"


def main():
    frozen_v = int(sys.argv[1])
    pytest_e = int(sys.argv[2])
    api_f = int(sys.argv[3])
    commit = sys.argv[4]
    report_path = sys.argv[5]
    # R1 incremental args (backward compatible: missing => -1 = SKIP)
    canary_f = int(sys.argv[6]) if len(sys.argv) > 6 else -1
    git_v = int(sys.argv[7]) if len(sys.argv) > 7 else -1
    lint_f = int(sys.argv[8]) if len(sys.argv) > 8 else -1
    topo_v = int(sys.argv[9]) if len(sys.argv) > 9 else -1
    watchdog_v = int(sys.argv[10]) if len(sys.argv) > 10 else -1
    pgpool_v = int(sys.argv[11]) if len(sys.argv) > 11 else -1  # T2 2026-08-24: pg_pool_guard
    # F03: 单一信源的 overall 由 bash 传入 (缺省 -> 本模块兜底推导并标注来源)
    verdict_arg = sys.argv[12].strip().upper() if len(sys.argv) > 12 else ""

    derived = "PASS"
    if (frozen_v > 0 or pytest_e != 0 or api_f > 0
            or canary_f > 0 or git_v > 0 or lint_f > 0
            or topo_v > 0 or watchdog_v > 0 or pgpool_v > 0):
        derived = "FAIL"

    if verdict_arg in ("PASS", "FAIL"):
        overall = verdict_arg
        verdict_source = "loop_b_verify.sh (single source)"
        consistency = "OK" if overall == derived else "MISMATCH"
    elif verdict_arg:
        overall = "FAIL"
        verdict_source = "invalid verdict argument: %r" % (verdict_arg,)
        consistency = "MISMATCH"
    else:
        # 向后兼容: 旧调用方未传 verdict -> 由本模块推导并显式标注来源
        overall = derived
        verdict_source = "write_report.py fallback (caller did not pass a verdict)"
        consistency = "NOT_APPLICABLE"

    report = {
        "loop": "B",
        "role": "independent_verification",
        "timestamp": datetime.datetime.now().isoformat(),
        "head_commit": commit,
        "overall": overall,
        "verdict_source": verdict_source,
        "verdict_derived_from_counts": derived,
        "verdict_consistency": consistency,
        "checks": {
            "frozen_nodes": {
                "status": "PASS" if frozen_v == 0 else "FAIL",
                "violations": frozen_v,
            },
            "pytest": {
                "status": "PASS" if pytest_e == 0 else "FAIL",
                "exit_code": pytest_e,
            },
            "api_anchors": {
                "status": "PASS" if api_f == 0 else "FAIL",
                "failures": api_f,
            },
            "qa_canary": {
                "status": _status(canary_f),
                "failures": canary_f,
            },
            "git_alignment": {
                "status": _status(git_v),
                "violations": git_v,
            },
            "docs_lint": {
                "status": _status(lint_f),
                "failures": lint_f,
            },
            "model_topology": {
                "status": _status(topo_v),
                "violations": topo_v,
            },
            "agent_watchdog": {
                "status": _status(watchdog_v),
                "violations": watchdog_v,
            },
            "pg_pool_guard": {
                "status": _status(pgpool_v),
                "violations": pgpool_v,
            },
        },
        "action": (
            "Loop A may continue"
            if overall == "PASS"
            else "HALT: Loop A must fix before proceeding"
        ),
    }

    try:
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
    except OSError as e:
        sys.stderr.write("[write_report] ERROR 报告写入失败: %s (%s)\n" % (report_path, e))
        return 1

    if consistency == "MISMATCH":
        # 守卫自检失败: 调用方判定与计数推导矛盾 => 本次报告不可信, 单独退出码 4
        sys.stderr.write(
            "[write_report] VERDICT MISMATCH: caller said %s but counts imply %s "
            "— 两份判定不同源, 报告已写出但必须修调用方\n" % (overall, derived))
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
