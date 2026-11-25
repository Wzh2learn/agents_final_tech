"""Frozen online-timing plot contracts accept only complete matched policies."""
import json
from hashlib import sha256
from pathlib import Path
import sys

import pytest


@pytest.fixture
def plotting(monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(source))
    pytest.importorskip('matplotlib')
    import plot_frontiers
    return plot_frontiers


def write_pair(root, plotting, version, *, dataset='finqa', n=1):
    names = sorted(plotting.ONLINE_POLICIES | (plotting.COMPACT_POLICIES if version >= 3 else set()))
    contract = {'schema': f'finance-live-policy-timing-v{version}', 'stage': 'eval', 'dataset': dataset,
                'case_order': [{'id': f'q{i}', 'policy_order': names} for i in range(n)],
                'baseline_policies': {'budgetverify': {'method': 'GBM'}}}
    if version == 3:
        contract['compact_oda'] = {'profile': {'model': 'compact', 'checkpoint': 'frozen'}}
    if version == 4:
        arm = {'finqa': 'balanced', 'tatqa': 'execution-aligned'}[dataset]
        files = {'adapter_config.json': 'a' * 64, 'adapter_model.safetensors': 'b' * 64}
        checkpoint = sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
        contract.update(full_official_panel=True, case_offset=0, compact_oda={'profile': {
            'model': f'oda-compact-{arm}', 'checkpoint': checkpoint, 'adapter_files': files,
            'evaluated_serving_profile_sha256': 'c' * 64,
        }})
    points = {name: {'n': n, 'correct': n, 'strict_and_executable': n,
                     'mean_wall_seconds': i + 1, 'summed_wall_seconds': n * (i + 1)}
              for i, name in enumerate(names)}
    collection = {'planned_questions': n, 'complete_paired_questions': n, 'stop_reason': None,
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


@pytest.mark.parametrize(('dataset', 'n'), [('finqa', 1147), ('tatqa', 718)])
def test_v4_accepts_complete_official_panels(plotting, tmp_path, dataset, n):
    path, _, _ = write_pair(tmp_path, plotting, 4, dataset=dataset, n=n)
    report = plotting.load_online(path)
    assert report['dataset'] == dataset
    assert report['full_official_panel'] is True
    assert report['strata']['correct']['n'] == n
    assert set(report['strata']['correct']['policies']) == plotting.ONLINE_POLICIES | plotting.COMPACT_POLICIES


@pytest.mark.parametrize('bad', ['pilot_only', 'incomplete', 'offset', 'missing_full_marker', 'wrong_profile',
                                  'wrong_checkpoint', 'missing_policy', 'duplicate_id'])
def test_v4_requires_frozen_full_panel_evidence(plotting, tmp_path, bad):
    n = 22 if bad == 'pilot_only' else 718
    path, contract, collection = write_pair(tmp_path, plotting, 4, dataset='tatqa', n=n)
    if bad == 'incomplete':
        collection['complete_paired_questions'] -= 1
    elif bad == 'offset':
        contract['case_offset'] = 22
    elif bad == 'missing_full_marker':
        del contract['full_official_panel']
    elif bad == 'wrong_profile':
        contract['compact_oda']['profile']['model'] = 'oda-compact-canonical'
    elif bad == 'wrong_checkpoint':
        contract['compact_oda']['profile']['checkpoint'] = '0' * 64
    elif bad == 'missing_policy':
        del collection['complete_pair_policies']['compact-direct']
    elif bad == 'duplicate_id':
        contract['case_order'][1]['id'] = contract['case_order'][0]['id']
    (tmp_path / 'run.json').write_text(json.dumps(contract), encoding='utf-8')
    path.write_text(json.dumps(collection), encoding='utf-8')
    with pytest.raises(ValueError):
        plotting.load_online(path)


def test_online_plot_rejects_mixed_full_and_pilot_runs(plotting, monkeypatch, tmp_path, capsys):
    finqa, tatqa = tmp_path / 'finqa', tmp_path / 'tatqa'
    finqa.mkdir()
    tatqa.mkdir()
    full, _, _ = write_pair(finqa, plotting, 4, n=1147)
    pilot, _, _ = write_pair(tatqa, plotting, 3, dataset='tatqa', n=22)
    output = tmp_path / 'wall_time'
    monkeypatch.setattr(sys, 'argv', ['plot_frontiers.py', '--online-timing', str(full), str(pilot),
                                      '--output', str(output)])
    with pytest.raises(SystemExit) as error:
        plotting.main()
    assert error.value.code == 2
    assert 'both datasets to be complete v4' in capsys.readouterr().err
    assert not output.with_suffix('.pdf').exists()
