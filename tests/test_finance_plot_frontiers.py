"""Frozen online-timing plot contracts accept only complete matched policies."""
import csv
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


def write_joint_pareto_fixture(plotting, root, monkeypatch, *, timed=3, all_missing=False, steady_workers=None):
    from benchmark_actions import action_cost
    from cohorts import UPSTREAM
    import live_policy_timing as timing

    monkeypatch.setitem(timing.OFFICIAL_COUNTS, 'finqa', 3)
    arms = timing.JOINT_POLICIES
    order = [{'id': f'q{i}', 'report': f'r{i}', 'policy_order': list(arms)} for i in range(3)]
    plan = {'schema': 'finance-live-joint-timing-plan-v1', 'dataset': 'finqa',
            'case_order': order, 'policies': list(arms),
            'panel': {'public.jsonl': 'a' * 64, 'references.jsonl': 'b' * 64},
            'official_source': {'split': 'test', 'sha256': UPSTREAM['finqa'][2], 'source_questions': 3,
                                'path': str(root / 'not-copied-source.json')}}
    steady = {} if steady_workers is None else {
        'joint_workers': steady_workers, 'joint_steady_block': 32,
        'actor_store_scope': timing.ISOLATED_ACTOR_STORE, 'local_selection': 'confidence-rerank-v1',
    }
    if steady:
        plan.update(schema=timing.JOINT_STEADY_PLAN, driver_sha256={'live_policy_timing.py': 'c' * 64}, **steady)
    plan_path = root / 'joint_plan.json'
    plan_path.write_text(json.dumps(plan), encoding='utf-8')
    shard = root / 'shards/00000'
    shard.mkdir(parents=True)
    (shard / 'run.json').write_text(json.dumps({
        'schema': timing.JOINT_STEADY_SHARD if steady else 'finance-live-joint-timing-shard-v1',
        'joint_plan_sha256': plotting.digest(plan_path), 'case_offset': 0, 'case_order': order, **steady,
    }), encoding='utf-8')
    outcomes = []
    # Compact, DeepSeek, CAR and TabFM can be non-dominated in 3-D even when a 2-D projection hides one.
    props = [(10, 4, 1), (30, 3, 2), (40, 2, 2), (60, 5, 1), (10, 4, 1),
             (50, 5, 1), (50, 6, 0), (60, 5, 0)]
    for i, case in enumerate(order[:timed]):
        records = {}
        for j, (name, (tokens, wall, correct)) in enumerate(zip(arms, props, strict=True)):
            path = Path('calls') / case['id'] / name / 'call.json'
            (shard / path).parent.mkdir(parents=True)
            (shard / path).write_text('{}', encoding='utf-8')
            usage = None if (j == 6 and (i == 2 or all_missing)) else {'total': tokens}
            call = {'usage': usage, 'elapsed_seconds': .1, 'path': path.as_posix()}
            executable = i < correct or i == 2
            records[name] = {'status': 'complete', 'result': {'strict': executable or (j == 3 and i == 1),
                                                             'executable': executable},
                             'wall_seconds': wall if i < 2 else wall + 30,
                             'calls': {'solve': call}, 'cost': action_cost([call])}
        row = {**case, 'dataset': 'finqa', 'complete_pair': True, 'policies': records}
        if steady:
            for record in records.values():
                record['actor_slot'] = i
            row.update(block_index=0, block_size=len(order), block_slot=i)
            if i == 0:
                row['arm_batches'] = {name: {'attempted_routes': len(order), 'complete_routes': len(order)} for name in arms}
        outcomes.append(row)
    (shard / 'outcomes.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in outcomes), encoding='utf-8')
    return plan_path, shard


def test_joint_pareto_matches_all_eight_methods_on_one_usage_cohort(plotting, monkeypatch, tmp_path):
    write_joint_pareto_fixture(plotting, tmp_path, monkeypatch)
    paired = []
    rows = {row['policy']: row for row in plotting.load_joint_pareto(tmp_path, paired_rows=paired)}
    assert set(rows) == set(plotting.JOINT_PARETO_LABELS)
    assert {row['scope'] for row in rows.values()} == {'full_official'}
    assert {(row['timed_n'], row['common_cost_complete_n']) for row in rows.values()} == {(3, 2)}
    assert {name for name, row in rows.items() if row['on_three_axis_frontier']} == {
        'joint-compact', 'deepseek-direct', 'car-compiled', 'budgetverify-tabfm-compiled',
    }
    compact = rows['joint-compact']
    assert compact['common_request_tokens'] == 20 and compact['timed_total_request_tokens'] == 30
    assert compact['common_mean_wall_seconds'] == 4 and compact['timed_mean_wall_seconds'] == 14
    assert compact['common_strict_executable'] == 1 and compact['timed_strict_executable'] == 2
    unknown = next(row for row in rows.values() if row['timed_unknown_usage_calls'])
    assert unknown['timed_unknown_usage_questions'] == 1 and unknown['timed_total_request_tokens'] is None
    assert unknown['timed_known_request_tokens'] == unknown['common_request_tokens']
    gbm = rows['budgetverify-gbm-compiled']
    assert gbm['common_strict_correct'] == 2 and gbm['common_strict_executable'] == 1
    comparisons = {row['comparator']: row for row in paired}
    assert set(comparisons) == set(rows) - {'joint-compact'}
    assert {row['common_cost_complete_n'] for row in paired} == {2}
    assert {row['comparison_cohort'] for row in paired} == {'all_eight_common_metered'}
    deepseek = comparisons['deepseek-direct']
    assert deepseek['timing_scope'] == 'full_official' and deepseek['timed_n'] == 3
    assert (deepseek['recovered_strict_executable'], deepseek['harmed_strict_executable']) == (0, 1)
    assert deepseek['delta_strict_executable_pp'] == -50
    assert deepseek['delta_request_tokens_per_question'] == -20
    assert deepseek['delta_wall_seconds_per_question'] == 1
    assert deepseek['tokens_ci_lower_per_question'] == -20 and deepseek['wall_ci_upper_seconds_per_question'] == 1
    assert deepseek['point_dominance'] == 'tradeoff'
    assert comparisons['budgetverify-tabfm-compiled']['point_dominance'] == 'tie'
    assert comparisons['author-cascade']['point_dominance'] == 'proposed'


@pytest.mark.parametrize('workers', [4, 6, 8])
def test_joint_pareto_reads_rolling_plan_without_current_driver_digest(plotting, monkeypatch, tmp_path, workers):
    write_joint_pareto_fixture(plotting, tmp_path, monkeypatch, steady_workers=workers)
    rows = plotting.load_joint_pareto(tmp_path)
    assert len(rows) == 8
    assert {(row['scheduling'], row['joint_workers'], row['frozen_block_size']) for row in rows} == {('rolling', workers, 32)}


def test_joint_pareto_partial_cli_labels_scope_and_writes_three_artifacts(plotting, monkeypatch, tmp_path):
    write_joint_pareto_fixture(plotting, tmp_path, monkeypatch, timed=2)
    with pytest.raises(ValueError, match='2/3 complete pairs'):
        plotting.load_joint_pareto(tmp_path)
    output = tmp_path / 'export/live'
    monkeypatch.setattr(sys, 'argv', ['plot_frontiers', '--joint-pareto', str(tmp_path), '--allow-partial',
                                     '--output', str(output)])
    plotting.main()
    with output.with_name('live_pareto.tsv').open(encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    assert len(rows) == 8
    assert {(row['scope'], row['timed_n'], row['official_n']) for row in rows} == {('partial_frozen_prefix', '2', '3')}
    assert {(row['scheduling'], row['frozen_block_size']) for row in rows} == {('serial', '1')}
    assert output.with_name('live_pareto.pdf').read_bytes().startswith(b'%PDF')
    assert output.with_name('live_pareto.png').read_bytes().startswith(b'\x89PNG')
    with output.with_name('live_pareto_paired.tsv').open(encoding='utf-8') as stream:
        paired = list(csv.DictReader(stream, delimiter='\t'))
    assert len(paired) == 7
    assert {(row['timing_scope'], row['common_cost_complete_n'], row['official_n']) for row in paired} == {
        ('partial_frozen_prefix', '2', '3'),
    }


def test_joint_pareto_rejects_mixing_rolling_and_wave_schedules(plotting, monkeypatch, tmp_path, capsys):
    def load(path, *, allow_partial, paired_rows):
        dataset = path.name
        return [{'dataset': dataset, 'joint_workers': 4, 'actor_store_scope': 'isolated',
                 'local_selection': 'same-selection', 'scheduling':
                 'rolling' if dataset == 'finqa' else 'wave', 'frozen_block_size': 32 if dataset == 'finqa' else 4}]

    monkeypatch.setattr(plotting, 'load_joint_pareto', load)
    monkeypatch.setattr(sys, 'argv', ['plot_frontiers', '--joint-pareto', 'finqa', 'tatqa',
                                     '--output', str(tmp_path / 'export/live')])
    with pytest.raises(SystemExit) as exit_state:
        plotting.main()
    assert exit_state.value.code == 2
    assert 'one load protocol' in capsys.readouterr().err


def test_joint_pareto_rejects_mixing_full_gate_compiler_or_service_profiles(plotting, monkeypatch, tmp_path, capsys):
    def load(path, *, allow_partial, paired_rows):
        return [{'dataset': path.name, 'scope': 'full_official', 'joint_workers': 4, 'actor_store_scope': 'isolated',
                 'scheduling': 'rolling', 'frozen_block_size': 32, 'local_selection': 'same-selection',
                 'shared_workload_sha256': path.name}]

    monkeypatch.setattr(plotting, 'load_joint_pareto', load)
    monkeypatch.setattr(sys, 'argv', ['plot_frontiers', '--joint-pareto', 'finqa', 'tatqa',
                                     '--output', str(tmp_path / 'export/live')])
    with pytest.raises(SystemExit) as exit_state:
        plotting.main()
    assert exit_state.value.code == 2
    assert 'same gate, compiler and serving profiles' in capsys.readouterr().err


def test_joint_pareto_keeps_full_denominator_when_no_common_cost_cohort(plotting, monkeypatch, tmp_path):
    write_joint_pareto_fixture(plotting, tmp_path, monkeypatch, all_missing=True)
    paired = []
    rows = plotting.load_joint_pareto(tmp_path, paired_rows=paired)
    assert {row['timed_n'] for row in rows} == {3}
    assert len(paired) == 7
    assert all(case['point_dominance'] == 'unavailable' and case['delta_strict_executable_pp'] is None for case in paired)
    assert {row['common_cost_complete_n'] for row in rows} == {0}
    assert all(row['on_three_axis_frontier'] is None and row['common_request_tokens'] is None for row in rows)


@pytest.mark.parametrize('bad', ['duplicate_official_id', 'missing_timed_arm', 'mismatched_cost', 'mismatched_seconds'])
def test_joint_pareto_rejects_unbound_coverage_or_cost(plotting, monkeypatch, tmp_path, bad):
    plan_path, shard = write_joint_pareto_fixture(plotting, tmp_path, monkeypatch)
    if bad == 'duplicate_official_id':
        plan = json.loads(plan_path.read_bytes())
        plan['case_order'][0]['id'] = plan['case_order'][1]['id']
        plan_path.write_text(json.dumps(plan), encoding='utf-8')
    else:
        path = shard / 'outcomes.jsonl'
        rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        if bad == 'missing_timed_arm':
            del rows[0]['policies']['joint-compact']
        elif bad == 'mismatched_cost':
            rows[0]['policies']['joint-compact']['cost']['total_tokens'] += 1
        else:
            rows[0]['policies']['joint-compact']['cost']['summed_call_seconds'] += .1
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
    with pytest.raises(ValueError):
        plotting.load_joint_pareto(tmp_path)


def test_joint_pareto_accepts_float_rounding_between_interpreters(plotting, monkeypatch, tmp_path):
    from math import nextafter

    _, shard = write_joint_pareto_fixture(plotting, tmp_path, monkeypatch)
    path = shard / 'outcomes.jsonl'
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    cost = rows[0]['policies']['joint-compact']['cost']
    cost['summed_call_seconds'] = nextafter(cost['summed_call_seconds'], float('inf'))
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')

    assert plotting.load_joint_pareto(tmp_path)[0]['timed_n'] == 3


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


def write_stratified_pair(root, plotting, dataset):
    n = 24
    population, _ = plotting.FULL_OFFICIAL_COMPACT[dataset]
    path, contract, summary = write_pair(root, plotting, 4, dataset=dataset, n=n)
    assignments = {case['id']: 'single-short' if index < 8 else 'multi-long'
                   for index, case in enumerate(contract['case_order'])}
    contract.update(schema=plotting.STRATIFIED_LATENCY_SCHEMA, full_official_panel=False,
                    official_source={'source_questions': population},
                    stratified_sampling={
                        'seed': 20261126, 'method': 'deterministic stratified hash',
                        'length_metric': 'visible context length', 'depth_metric': 'reference depth',
                        'population_n': population, 'sample_n': n, 'stratum_by_id': assignments,
                        'strata': {'single-short': {'population_n': 200, 'sample_n': 8},
                                   'multi-long': {'population_n': population - 200, 'sample_n': 16}},
                    })
    points = summary['complete_pair_policies']
    for point in points.values():
        point.update(median_wall_seconds=point['mean_wall_seconds'], p90_wall_seconds=point['mean_wall_seconds'])
    for reference, field in plotting.LATENCY_REFERENCES:
        comparisons = {}
        for name, point in points.items():
            if name != reference:
                difference = points[reference]['mean_wall_seconds'] - point['mean_wall_seconds']
                comparisons[name] = {'strict': {'n': n, 'excluded_n': 0, 'report_clusters': 18,
                                                plotting.WALL_DELTA: difference,
                                                'interval_95': {plotting.WALL_DELTA: [difference - 1, difference + 1]}}}
        summary[field] = {'proposed': reference, 'comparisons': comparisons}
    (root / 'run.json').write_text(json.dumps(contract), encoding='utf-8')
    path.write_text(json.dumps(summary), encoding='utf-8')
    return path, contract, summary


def test_stratified_online_cli_exports_sample_scoped_latency(plotting, monkeypatch, tmp_path):
    reports = []
    for dataset in ('finqa', 'tatqa'):
        root = tmp_path / dataset
        root.mkdir()
        reports.append(write_stratified_pair(root, plotting, dataset)[0])
    labels = []

    def inspect_plot(reports, output, label, **options):
        labels.append(label)
        figure, axis = plotting.plt.subplots()
        try:
            plotting.plot_axis(axis, reports[0], online_score='correct')
            assert 'Stratified sample' in axis.get_title(loc='left')
        finally:
            plotting.plt.close(figure)

    monkeypatch.setattr(plotting, 'render', inspect_plot)
    output = tmp_path / 'stratified'
    monkeypatch.setattr(sys, 'argv', ['plot_frontiers.py', '--online-timing', *map(str, reports),
                                      '--output', str(output)])
    plotting.main()
    assert labels == ['Stratified sample online wall time']
    with (tmp_path / 'stratified_latency.tsv').open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    assert len(rows) == 22
    assert {r['scope'] for r in rows} == {'unweighted_stratified_sample'}
    assert {r['paired_n'] for r in rows} == {'24'}
    assert {r['dataset'] for r in rows} == {'finqa', 'tatqa'}
    compact = next(r for r in rows if r['dataset'] == 'finqa' and r['policy'] == 'compact-fallback')
    car = next(r for r in rows if r['dataset'] == 'finqa' and r['policy'] == 'car')
    delta = float(compact['mean_wall_seconds']) - float(car['mean_wall_seconds'])
    assert compact['compact_fallback_minus_policy_mean_delta_seconds'] == ''
    assert float(car['compact_fallback_minus_policy_mean_delta_seconds']) == delta
    assert float(car['compact_fallback_minus_policy_interval_95_high_seconds']) == delta + 1
    assert not (tmp_path / 'stratified_comparison.tsv').exists()


@pytest.mark.parametrize('bad', ['counts', 'scope', 'adapter', 'paired_delta'])
def test_stratified_latency_rejects_inconsistent_measurements(plotting, tmp_path, bad):
    path, contract, summary = write_stratified_pair(tmp_path, plotting, 'tatqa')
    if bad == 'counts':
        contract['stratified_sampling']['strata']['multi-long']['sample_n'] -= 1
    elif bad == 'scope':
        contract['full_official_panel'] = True
    elif bad == 'adapter':
        contract['compact_oda']['profile']['model'] = 'oda-compact-canonical'
    else:
        summary['compact_paired_online_wall']['comparisons']['car']['strict'][plotting.WALL_DELTA] += 1
    (tmp_path / 'run.json').write_text(json.dumps(contract), encoding='utf-8')
    path.write_text(json.dumps(summary), encoding='utf-8')
    with pytest.raises(ValueError):
        plotting.load_online(path)


@pytest.mark.parametrize('bad', [None, 'order', 'summary'])
def test_fresh_comparison_uses_one_usage_cohort_for_all_policies(plotting, tmp_path, bad):
    n = 718
    path, contract, collection = write_pair(tmp_path, plotting, 4, dataset='tatqa', n=n)
    names = contract['case_order'][0]['policy_order']
    collection['complete_pair_policies'][names[-1]]['correct'] -= 1
    collection['complete_pair_policies'][names[-1]]['strict_and_executable'] -= 1
    path.write_text(json.dumps(collection), encoding='utf-8')
    with path.with_name('outcomes.jsonl').open('w', encoding='utf-8') as stream:
        for index, case in enumerate(contract['case_order']):
            first = index == 0
            records = {}
            for j, name in enumerate(names):
                correct = not (first and name == names[-1] and bad != 'summary')
                total = None if first and name == names[0] else 10 + j
                records[name] = {'status': 'complete', 'result': {'strict': correct, 'executable': True},
                                 'wall_seconds': j + 1,
                                 'cost': {'total_tokens': total, 'unknown_usage_calls': int(total is None)}}
            order = names[::-1] if first and bad == 'order' else names
            row = {'id': case['id'], 'dataset': 'tatqa', 'policy_order': order,
                   'policies': records, 'complete_pair': True}
            stream.write(json.dumps(row) + '\n')
    if bad:
        with pytest.raises(ValueError, match='planned pair' if bad == 'order' else 'timing summary'):
            plotting.load_online(path, fresh_comparison=True)
        return

    report = plotting.load_online(path, fresh_comparison=True)
    assert report['fresh_token_strata']['correct']['token_frontier'] == [names[0]]
    output = tmp_path / 'comparison.tsv'
    plotting.write_fresh_comparison([report], output)
    with output.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    assert len(rows) == 11
    assert {row['paired_n'] for row in rows} == {str(n)}
    assert {row['common_usage_n'] for row in rows} == {str(n - 1)}
    assert rows[-1]['strict_correct'] == str(n - 1)
    assert rows[0]['strict_correct'] == str(n)
    assert {row['common_usage_strict_correct'] for row in rows} == {str(n - 1)}
    assert rows[-1]['common_usage_total_tokens'] == str((n - 1) * 20)
