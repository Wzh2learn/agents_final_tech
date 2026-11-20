from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


@pytest.fixture
def tradeoff(monkeypatch):
    source = Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'
    monkeypatch.syspath_prepend(str(source))
    from paired_tradeoff import paired_tradeoff

    return paired_tradeoff


def outcome(strict, tokens, seconds, *, unknown=0):
    return SimpleNamespace(strict=strict, known_tokens=tokens, unknown_usage_calls=unknown,
                           serial_seconds=seconds, executable=True)


def test_unknown_tokens_use_pairwise_complete_questions(tradeoff):
    ids = ('complete_a', 'complete_b', 'unknown')
    reports = dict(zip(ids, ('a', 'b', 'a'), strict=True))
    proposed = {ident: outcome(True, 20, 2) for ident in ids}
    compare = {ident: outcome(False, 10, 3) for ident in ids}
    proposed['unknown'] = outcome(False, 0, 6, unknown=1)
    compare['unknown'] = outcome(True, 200, 2)
    result = tradeoff(proposed, compare, ids, reports)
    tokens, seconds = result['tokens'], result['serial_call_seconds']
    assert (tokens['n'], tokens['excluded_n'], tokens['report_clusters']) == (2, 1, 2)
    assert (tokens['strict_delta_pp'], tokens['mean_token_delta']) == (100, 10)
    assert tokens['interval_95'] == {'strict_delta_pp': [100, 100], 'mean_token_delta': [10, 10]}
    assert tokens['dominance'] == 'undetermined'
    assert (seconds['n'], seconds['excluded_n'], seconds['report_clusters']) == (3, 0, 2)
    assert seconds['strict_delta_pp'] == pytest.approx(100 / 3)
    assert seconds['mean_serial_call_seconds_delta'] == pytest.approx(2 / 3)


def test_both_axes_share_cluster_draws_and_question_denominators(tradeoff):
    ids = ('a1', 'a2', 'a3', 'b')
    proposed = {ident: outcome(ident != 'b', 20 if ident == 'b' else 0, 0) for ident in ids}
    compare = {ident: outcome(ident == 'b', 10, 0) for ident in ids}
    reports = {ident: ident[0] for ident in ids}
    result = tradeoff(proposed, compare, ids, reports, draws=15)
    expected = []
    rng = np.random.default_rng(20261119)
    for resampled in rng.integers(0, 2, size=(15, 2)):
        questions = [ident for cluster in resampled for ident in ids if reports[ident] == 'ab'[cluster]]
        total = sum(proposed[ident].strict - compare[ident].strict for ident in questions)
        expected.append([100 * total / len(questions), -10 * total / len(questions)])
    acc, cost = np.quantile(expected, [.0125, .9875], axis=0).T.tolist()
    assert result['tokens']['strict_delta_pp'] == 50
    assert result['tokens']['mean_token_delta'] == -5
    assert result['tokens']['interval_95'] == {'strict_delta_pp': acc, 'mean_token_delta': cost}
    assert result['tokens']['dominance'] == 'undetermined'
    assert tradeoff(proposed, compare, reversed(ids), reports, draws=15) == result


def test_exact_pareto_at_one_equal_axis_and_complete_tie(tradeoff):
    reports = {'a': 'a', 'b': 'b'}
    cheap = {ident: outcome(True, 2, 1) for ident in reports}
    costly = {ident: outcome(True, 5, 1) for ident in reports}
    assert tradeoff(cheap, costly, reports, reports)['tokens']['dominance'] == 'proposed'
    assert tradeoff(costly, cheap, reports, reports)['tokens']['dominance'] == 'comparator'
    tied = tradeoff(cheap, costly, reports, reports)['serial_call_seconds']
    assert tied['dominance'] == 'undetermined'
    assert tied['interval_95'] == {'strict_delta_pp': [0, 0], 'mean_serial_call_seconds_delta': [0, 0]}
    wrong = {ident: outcome(False, 2, 1) for ident in reports}
    assert tradeoff(cheap, wrong, reports, reports)['tokens']['dominance'] == 'proposed'


def test_zero_usage_complete_and_single_report_have_no_inferential_interval(tradeoff):
    proposed = {'a': outcome(True, 0, 4, unknown=1)}
    compare = {'a': outcome(False, 1, 8)}
    result = tradeoff(proposed, compare, ['a'], {'a': 'report'})
    assert result['tokens'] == {'n': 0, 'excluded_n': 1, 'report_clusters': 0, 'strict_delta_pp': None,
                                'mean_token_delta': None, 'interval_95': None, 'dominance': 'undetermined'}
    seconds = result['serial_call_seconds']
    assert (seconds['strict_delta_pp'], seconds['mean_serial_call_seconds_delta']) == (100, -4)
    assert seconds['interval_95'] is None and seconds['dominance'] == 'undetermined'
    assert tradeoff({}, {}, [], {})['serial_call_seconds']['n'] == 0
    with pytest.raises(ValueError, match='unique matched'):
        tradeoff(proposed, compare, ['a', 'a'], {'a': 'report'})
