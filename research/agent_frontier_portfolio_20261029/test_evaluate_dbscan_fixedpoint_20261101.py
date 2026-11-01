from evaluate_dbscan_fixedpoint_20261101 import greedy_metrics


def test_greedy_matching_and_unmatched_cases():
    f1, delta = greedy_metrics([(0, 0), (10, 0)], [(1, 0), (9, 0)])
    assert f1 == 1.0 and delta == 1.0
    f1, delta = greedy_metrics([(0, 0)], [(100, 0)])
    assert f1 == 0.0 and delta is None
    f1, delta = greedy_metrics([], [(1, 0)])
    assert f1 == 0.0 and delta is None
