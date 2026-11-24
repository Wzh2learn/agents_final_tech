"""Frozen online-timing plot contracts accept only complete matched policies."""
import json
from pathlib import Path

import pytest


@pytest.fixture
def plotting(monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(source))
    pytest.importorskip('matplotlib')
    import plot_frontiers
    return plot_frontiers


def write_pair(root, plotting, version):
    names = sorted(plotting.ONLINE_POLICIES | (plotting.COMPACT_POLICIES if version == 3 else set()))
    contract = {'schema': f'finance-live-policy-timing-v{version}', 'stage': 'eval', 'dataset': 'finqa',
                'case_order': [{'id': 'q1', 'policy_order': names}],
                'baseline_policies': {'budgetverify': {'method': 'GBM'}}}
    if version == 3:
        contract['compact_oda'] = {'profile': {'model': 'compact', 'checkpoint': 'frozen'}}
    points = {name: {'n': 1, 'correct': 1, 'strict_and_executable': 1,
                     'mean_wall_seconds': i + 1, 'summed_wall_seconds': i + 1}
              for i, name in enumerate(names)}
    collection = {'planned_questions': 1, 'complete_paired_questions': 1, 'stop_reason': None,
                  'complete_pair_policies': points, 'strict_wall_frontier': [names[0]],
                  'strict_and_executable_wall_frontier': [names[0]]}
    path = root / 'collection.json'
    (root / 'run.json').write_text(json.dumps(contract), encoding='utf-8')
    path.write_text(json.dumps(collection), encoding='utf-8')
    return path, contract, collection


@pytest.mark.parametrize('version', [2, 3])
def test_online_schema_preserves_complete_matched_policies(plotting, tmp_path, version):
    path, contract, _ = write_pair(tmp_path, plotting, version)
    report = plotting.load_online(path)
    assert set(report['strata']['correct']['policies']) == set(contract['case_order'][0]['policy_order'])
    if version == 3:
        assert plotting.family('compact-direct', {}) != plotting.family('compact-fallback', {})
        assert plotting.STYLES[plotting.family('compact-direct', {})] != plotting.STYLES[plotting.family('compact-fallback', {})]
        figure, axis = plotting.plt.subplots()
        try:
            plotted = plotting.plot_axis(axis, report, online_score='correct')
            assert {'Compact 8B direct', 'Compact 8B with fallback'} <= plotted
        finally:
            plotting.plt.close(figure)


@pytest.mark.parametrize('bad', ['missing_profile', 'missing_policy', 'duplicate_order',
                                  'incomplete_pair', 'wrong_frontier'])
def test_v3_rejects_invalid_or_incomplete_evidence(plotting, tmp_path, bad):
    path, contract, collection = write_pair(tmp_path, plotting, 3)
    if bad == 'missing_profile':
        del contract['compact_oda']
    elif bad == 'missing_policy':
        del collection['complete_pair_policies']['compact-direct']
    elif bad == 'duplicate_order':
        contract['case_order'][0]['policy_order'][-1] = contract['case_order'][0]['policy_order'][0]
    elif bad == 'incomplete_pair':
        collection['complete_paired_questions'] = 0
    else:
        collection['strict_wall_frontier'] = ['compact-direct']
    (tmp_path / 'run.json').write_text(json.dumps(contract), encoding='utf-8')
    path.write_text(json.dumps(collection), encoding='utf-8')
    with pytest.raises(ValueError):
        plotting.load_online(path)
