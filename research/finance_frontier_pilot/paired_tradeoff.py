"""Report-cluster bootstrap for a pair of fixed policies on matched questions."""

import numpy as np


SEED = 20261119
TAIL = .0125  # Two axes, two tails per axis, overall alpha .05.


def contrast(proposed, comparator, ids, reports, cost_name, cost_delta, draws, excluded):
    groups = {}
    for ident in sorted(ids):
        first, second = proposed[ident], comparator[ident]
        group = groups.setdefault(reports[ident], [0, 0, 0.])
        group[0] += 1
        group[1] += int(first.strict) - int(second.strict)
        group[2] += cost_delta(first, second)

    result = {'n': len(ids), 'excluded_n': excluded, 'report_clusters': len(groups),
              'strict_delta_pp': None, cost_name: None, 'interval_95': None,
              'dominance': 'undetermined'}
    if not groups:
        return result

    totals = np.asarray([groups[report] for report in sorted(groups)], dtype=float)
    counts, strict, cost = totals.sum(axis=0)
    result.update(strict_delta_pp=float(100 * strict / counts), **{cost_name: float(cost / counts)})
    if len(groups) < 2:
        return result

    rng = np.random.default_rng(SEED)
    samples = np.empty((draws, 2), dtype=float)
    for begin in range(0, draws, 512):
        end = min(begin + 512, draws)
        selected = rng.integers(0, len(groups), size=(end - begin, len(groups)))
        counts, strict, cost = totals[selected].sum(axis=1).T
        samples[begin:end, 0] = 100 * strict / counts
        samples[begin:end, 1] = cost / counts

    strict_interval, cost_interval = np.quantile(samples, [TAIL, 1 - TAIL], axis=0).T.tolist()
    result['interval_95'] = {'strict_delta_pp': strict_interval, cost_name: cost_interval}
    low_accuracy, high_accuracy = strict_interval
    low_cost, high_cost = cost_interval
    if low_accuracy >= 0 and high_cost <= 0 and (low_accuracy > 0 or high_cost < 0):
        result['dominance'] = 'proposed'
    elif high_accuracy <= 0 and low_cost >= 0 and (high_accuracy < 0 or low_cost > 0):
        result['dominance'] = 'comparator'
    return result


def paired_tradeoff(proposed, comparator, ids, reports, draws=10000):
    """Estimate proposed minus comparator with paired report resampling.

    Token effects use pairwise-complete records. Recorded serial-call seconds
    use all paired records and do not measure fresh online wall time.
    """
    ids = tuple(ids)
    unique = set(ids)
    if draws < 1 or len(unique) != len(ids) or any(unique - rows.keys() for rows in (proposed, comparator, reports)):
        raise ValueError('Expected positive draws and unique matched question and report IDs')
    complete = [ident for ident in ids
                if not (proposed[ident].unknown_usage_calls or comparator[ident].unknown_usage_calls)]
    tokens = contrast(proposed, comparator, complete, reports, 'mean_token_delta',
                      lambda first, second: first.known_tokens - second.known_tokens,
                      draws, len(ids) - len(complete))
    seconds = contrast(proposed, comparator, ids, reports, 'mean_serial_call_seconds_delta',
                       lambda first, second: first.serial_seconds - second.serial_seconds, draws, 0)
    return {
        'tokens': tokens, 'serial_call_seconds': seconds, 'draws': draws, 'seed': SEED,
        'interval_method': 'Paired report-cluster percentile bootstrap, Bonferroni rectangle within each contrast. '
                           'Intervals require at least two reports and are not family-wise across comparisons.',
    }
