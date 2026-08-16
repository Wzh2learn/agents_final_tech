"""Loop B report writer - called by loop_b_verify.sh

R1 (2026-08-13): extended with three incremental check counts (qa_canary /
git_alignment / docs_lint). Missing extra args are treated as -1 = SKIP so
old 5-arg invocations keep working.
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

    overall = "PASS"
    if (frozen_v > 0 or pytest_e != 0 or api_f > 0
            or canary_f > 0 or git_v > 0 or lint_f > 0
            or topo_v > 0 or watchdog_v > 0):
        overall = "FAIL"

    report = {
        "loop": "B",
        "role": "independent_verification",
        "timestamp": datetime.datetime.now().isoformat(),
        "head_commit": commit,
        "overall": overall,
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
        },
        "action": (
            "Loop A may continue"
            if overall == "PASS"
            else "HALT: Loop A must fix before proceeding"
        ),
    }

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
