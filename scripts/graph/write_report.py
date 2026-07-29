"""Loop B report writer - called by loop_b_verify.sh"""
import json
import datetime
import sys

def main():
    frozen_v = int(sys.argv[1])
    pytest_e = int(sys.argv[2])
    api_f = int(sys.argv[3])
    commit = sys.argv[4]
    report_path = sys.argv[5]

    overall = "PASS"
    if frozen_v > 0 or pytest_e != 0 or api_f > 0:
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
