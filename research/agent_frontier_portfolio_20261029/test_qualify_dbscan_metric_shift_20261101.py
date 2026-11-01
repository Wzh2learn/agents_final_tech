from qualify_dbscan_metric_shift_20261101 import equivalent_labels


def test_partition_comparison_handles_label_renaming_and_noise():
    assert equivalent_labels([0, 0, 1, -1], [4, 4, 2, -1])
    assert not equivalent_labels([0, 0, 1, -1], [4, 2, 2, -1])
    assert not equivalent_labels([0, 0, -1], [4, 4, 4])
    assert not equivalent_labels([0, 1], [4])
