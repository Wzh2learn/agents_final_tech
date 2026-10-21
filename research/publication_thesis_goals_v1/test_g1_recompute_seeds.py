from g1_recompute_seeds import (
    cluster_bootstrap,
    leave_one_seed_out,
    summarize_protocol,
    uid_overlap_summary,
)


def rows() -> list[dict]:
    return [
        {"uid": "a", "seed": 42, "flag": True},
        {"uid": "a", "seed": 20260831, "flag": False},
        {"uid": "b", "seed": 42, "flag": True},
        {"uid": "c", "seed": 20260831, "flag": False},
    ]


def test_source_table_summary_keeps_run_and_uid_estimands_distinct() -> None:
    summary = summarize_protocol(rows(), "flag", n_boot=200)
    assert summary["table_runs"] == 4
    assert summary["detected_table_runs"] == 2
    assert summary["run_weighted_rate"] == 0.5
    assert summary["unique_source_table_uids"] == 3
    assert abs(summary["uid_equal_rate"] - (0.5 + 1.0 + 0.0) / 3) < 1e-12
    assert len(summary["source_table_cluster_bootstrap"]["run_weighted_rate_ci95"]) == 2


def test_overlap_and_leave_one_seed_out() -> None:
    overlap = uid_overlap_summary(rows())
    assert overlap["unique_source_table_uids"] == 3
    assert overlap["uid_seed_overlap_counts"] == {
        "seen_in_1_seed(s)": 2,
        "seen_in_2_seed(s)": 1,
    }
    assert leave_one_seed_out(rows(), "flag") == {
        "omit_42": {"table_runs": 2, "detected": 0, "rate": 0.0},
        "omit_20260831": {"table_runs": 2, "detected": 2, "rate": 1.0},
        "omit_20260832": {"table_runs": 4, "detected": 2, "rate": 0.5},
    }


def test_cluster_bootstrap_is_deterministic() -> None:
    assert cluster_bootstrap(rows(), "flag", n_boot=100) == cluster_bootstrap(
        rows(), "flag", n_boot=100
    )
