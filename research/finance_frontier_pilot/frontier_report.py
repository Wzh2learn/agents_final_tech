"""Aggregate matched official outcomes without rerunning a scorer or a policy selector."""

import argparse
from hashlib import sha256
import json
from math import fsum, isclose, isfinite
from pathlib import Path
from statistics import median, quantiles
from typing import NamedTuple

from benchmark_actions import action_cost, digest_file
from run_pilot import load_lines, write_json


TIERS = ('low', 'mid', 'high')
MODELS = ('oda-8b', 'qwen-27b', 'deepseek')
CONTRACT_CASCADE = 'contract_8b_free_qwen_deepseek'
ODA_METHODS = ('low', 'free', 'dsl_fallback', 'contract_compile', 'compiled_fallback')
INDEPENDENT_EXPOSURE = 'no_pilot_or_reserved_context_detected'


class Outcome(NamedTuple):
    strict: int
    known_tokens: int
    unknown_usage_calls: int
    calls: int
    serial_seconds: float


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def matched(rows, ids, label, dataset=None):
    if dataset is not None:
        rows = [row for row in rows if row['dataset'] == dataset]
    index = {row['id']: row for row in rows}
    if index.keys() != set(ids) or len(index) != len(rows):
        raise ValueError(f'{label}: expected exactly one row for each matched question')
    return index


def outcome(strict, cost):
    known, unknown, calls = (cost[key] for key in ('known_tokens', 'unknown_usage_calls', 'calls'))
    seconds = cost['summed_call_seconds']
    if (type(strict) not in (bool, int) or strict not in (0, 1)
            or any(type(value) is not int or value < 0 for value in (known, unknown, calls))
            or not 0 <= unknown <= calls or not isfinite(seconds) or seconds < 0
            or ('total_tokens' in cost and cost['total_tokens'] != (None if unknown else known))):
        raise ValueError('invalid matched correctness, usage or call duration')
    return Outcome(int(strict), known, unknown, calls, seconds)


def selected_action(row, action):
    saved = row['actions'][action]
    calls = saved['calls']
    if not calls or len(set(calls)) != len(calls):
        raise ValueError(f'{row["id"]}: invalid {action} call list')
    cost = action_cost([row['calls'][name] for name in calls])
    if cost != saved['cost']:
        raise ValueError(f'{row["id"]}: recorded {action} cost differs from its receipts')
    return outcome(saved['strict'], cost)


def summarize(rows):
    correct = sum(row.strict for row in rows)
    known = sum(row.known_tokens for row in rows)
    unknown = sum(row.unknown_usage_calls for row in rows)
    serial = [row.serial_seconds for row in rows]
    return {'n': len(rows), 'correct': correct, 'accuracy': correct / len(rows),
            'calls': sum(row.calls for row in rows), 'total_tokens': None if unknown else known,
            'known_tokens': known, 'known_tokens_are_lower_bound': bool(unknown),
            'unknown_usage_calls': unknown,
            'unknown_usage_questions': sum(row.unknown_usage_calls > 0 for row in rows),
            'summed_call_seconds': fsum(serial), 'mean_serial_call_seconds': fsum(serial) / len(rows),
            'median_serial_call_seconds': median(serial),
            'p90_serial_call_seconds': quantiles(serial, n=10, method='inclusive')[-1] if len(serial) > 1 else serial[0]}


def check_summary(source, measured, *, cascade=False):
    correctness, tokens = ('strict', 'tokens') if cascade else ('correct', 'total_tokens')
    seconds = 'mean_serial_call_seconds' if cascade else 'summed_call_seconds'
    if (source[correctness] != measured['correct'] or source[tokens] != measured['total_tokens']
            or any(source[key] != measured[key] for key in ('n', 'known_tokens', 'unknown_usage_calls'))
            or not isclose(source[seconds], measured[seconds], abs_tol=1e-8)
            or (not cascade and source['calls'] != measured['calls'])):
        raise ValueError('reported policy summary differs from its matched items')


def car_items(root, oda, ids, dataset, panel, oda_digest):
    contract = read(root / 'run.json')
    if (contract['schema'] != 'finance-car-collection-v1' or contract['stage'] != 'eval'
            or contract['dataset'] != dataset or contract['panel'] != panel
            or contract['draft_collection'] != oda_digest or not contract['policy']):
        raise ValueError('CAR outcomes need the matched ODA drafts, frozen panel and policy')
    rows = matched(load_lines(root / 'outcomes.jsonl'), ids, 'CAR', dataset)
    results = {}
    for ident, row in rows.items():
        draft = oda[ident]
        if row['report'] != draft['report'] or row['draft_correct'] != draft['actions']['low']['strict']:
            raise ValueError(f'{ident}: CAR draft differs from ODA')
        calls = [draft['calls'][name] for name in ('low', 'car_probe')]
        relative = f'calls/{sha256(ident.encode("utf-8")).hexdigest()[:24]}/call.json'
        if row['attempted_repair']:
            if row['repair_receipt'] != relative:
                raise ValueError(f'{ident}: CAR repair receipt is missing or unmatched')
            calls.append(read(root / relative))
        elif row['repair_receipt'] is not None:
            raise ValueError(f'{ident}: a closed CAR gate cannot have a selected repair')
        cost = action_cost(calls)
        if cost != row['cost']:
            raise ValueError(f'{ident}: CAR cost differs from its receipts')
        results[ident] = outcome(row['strict'], cost)
    return results, {'family': 'CAR adaptation', 'policy_sha256': contract['policy'],
                     'probe_decoding': contract.get('probe_decoding')}


def budget_items(report, oda, ids, dataset, provenance, expected_method):
    order = report['eval_ids']
    if (report['dataset'] != dataset or report['method'] != expected_method or set(order) != set(ids)
            or len(order) != len(ids) or report['inputs']['eval'] != provenance):
        raise ValueError(f'{expected_method}: report, panel or ODA run differs')
    tiers = {tier: {ident: selected_action(oda[ident], tier) for ident in order} for tier in TIERS}
    labels = report.get('eval_strict_by_tier')
    if labels is None and 'verifier_replay' in report:
        raise ValueError('decoder-enabled reports must publish matched per-item High correctness')
    if labels is not None:
        if set(labels) != set(TIERS) or any(len(values) != len(order) for values in labels.values()):
            raise ValueError('BudgetVerify requires one label per eval question and tier')
        for tier in TIERS:
            for ident, strict in zip(order, labels[tier], strict=True):
                original = tiers[tier][ident]
                if (type(strict) not in (int, bool) or strict not in (0, 1)
                        or (strict != original.strict and (tier != 'high' or 'verifier_replay' not in report))):
                    raise ValueError(f'{ident}: invalid or unmatched BudgetVerify {tier} label')
                tiers[tier][ident] = original._replace(strict=int(strict))

    policies = {}
    candidates = [(f'fixed_{tier}', record, {}) for tier, record in report['fixed'].items()]
    for point in report['policies']:
        if point['calibration_frontier']:
            candidates.append((f'lambda_{point["lambda"]:g}', point['eval'],
                               {'lambda': point['lambda'], 'calibration_frontier': True, 'config': point['config']}))
    for name, record, details in candidates:
        actions = record['tiers_in_eval_order']
        items = {ident: tiers[action][ident] for ident, action in zip(order, actions, strict=True)}
        check_summary(record['all'], summarize(list(items.values())))
        policies[name] = (items, {'family': 'BudgetVerify adaptation', 'classifier': report['method'],
                                  'verifier_replay': 'verifier_replay' in report,
                                  'batch_prediction_seconds': record.get('prediction_batch_seconds'), **details})
    return policies


def cascade_items(report, oda_policies, ids):
    representation = report['representation']
    input_rows = {name: matched(point['items'], ids, name) for name, point in report['policies'].items()}
    direct = {}
    for model in MODELS:
        rows = input_rows[f'always_{model}']
        if any(row['selected'] != model or row['queried'] != [model] for row in rows.values()):
            raise ValueError(f'{model}: non-direct receipt for a single-model baseline')
        direct[model] = {ident: outcome(row['strict'], {**row, 'calls': 1}) for ident, row in rows.items()}
    local = 'low' if representation == 'raw' else 'contract_compile'
    if direct['oda-8b'] != oda_policies[local]:
        raise ValueError(f'Cascade {representation}: ODA decisions differ from matched ODA actions')
    direct['oda-8b-free'] = oda_policies['free']
    policies = {}
    for name, rows in input_rows.items():
        items = {}
        for ident, row in rows.items():
            queried = row['queried']
            if (row['selected'] not in MODELS or row['selected'] not in queried
                    or len(set(queried)) != len(queried) or not set(queried) <= direct.keys()
                    or ('oda-8b-free' in queried and name != CONTRACT_CASCADE)):
                raise ValueError(f'{name}: invalid selected-call path for {ident}')
            source = (oda_policies['compiled_fallback'] if name == CONTRACT_CASCADE and row['selected'] == 'oda-8b'
                      else direct[row['selected']])
            receipts = [direct[model][ident] for model in queried]
            measured = outcome(row['strict'], {**row, 'calls': len(queried)})
            if (measured.strict != source[ident].strict
                    or measured.known_tokens != sum(item.known_tokens for item in receipts)
                    or measured.unknown_usage_calls != sum(item.unknown_usage_calls for item in receipts)
                    or not isclose(measured.serial_seconds, fsum(item.serial_seconds for item in receipts), abs_tol=1e-8)):
                raise ValueError(f'{name}: selected outcome or charged calls differ for {ident}')
            items[ident] = measured
        point = report['policies'][name]
        check_summary(point['all'], summarize(list(items.values())), cascade=True)
        family = ('Execution-contract cascade' if name == CONTRACT_CASCADE else 'Cascade Routing adaptation'
                  if 'target_mean_tokens' in point else 'Fixed baseline')
        policies[name] = (items, {'family': family, 'representation': representation,
                                  'target_mean_tokens': point.get('target_mean_tokens')})
    return policies


def frontier(points, cost):
    complete = {name: row for name, row in points.items() if row[cost] is not None}
    return sorted(name for name, row in complete.items() if not any(
        other[cost] <= row[cost] and other['correct'] >= row['correct']
        and (other[cost] < row[cost] or other['correct'] > row['correct'])
        for other in complete.values()))


def build_report(args):
    public_path = args.panel / 'public.jsonl'
    rows = [row for row in load_lines(public_path) if row['dataset'] == args.dataset]
    public = {row['id']: row['report'] for row in rows}
    if not public or len(public) != len(rows):
        raise ValueError('the panel must contain unique matched question IDs')
    panel = {path.name: digest_file(path) for path in (public_path, args.panel / 'references.jsonl')}
    oda_contract = read(args.oda_run / 'run.json')
    if (oda_contract['schema'] != 'finance-benchmark-actions-v1' or oda_contract['panel'] != panel
            or oda_contract['dataset'] not in (None, args.dataset)):
        raise ValueError('ODA run and frozen panel differ')
    provenance = {key: digest_file(args.oda_run / key) for key in ('run.json', 'outcomes.jsonl')}
    oda = matched(load_lines(args.oda_run / 'outcomes.jsonl'), public, 'ODA', args.dataset)
    if any(oda[ident]['report'] != report for ident, report in public.items()):
        raise ValueError('ODA report identifiers differ from the frozen panel')
    oda_policies = {action: {ident: selected_action(row, action) for ident, row in oda.items()}
                    for action in ODA_METHODS}
    policies = {f'oda/{action}': (items, {'family': 'Fixed ODA action'}) for action, items in oda_policies.items()}
    policies['car'] = car_items(args.car_run, oda, public, args.dataset, panel, provenance['outcomes.jsonl'])
    for tag, path, method in (('gbm', args.budgetverify_gbm, 'GBM'),
                              ('tabfm', args.budgetverify_tabfm, 'TabFM-1.0.0-PyTorch')):
        policies.update({f'budgetverify/{tag}/{name}': value for name, value in
                         budget_items(read(path), oda, public, args.dataset, provenance, method).items()})

    raw, compiled = read(args.cascade_raw), read(args.cascade_compiled)
    if (raw['representation'] != 'raw' or compiled['representation'] != 'compiled'
            or raw['dataset'] != args.dataset or compiled['dataset'] != args.dataset
            or any(raw[key] != compiled[key] for key in ('profiles', 'author_revision', 'campus_ledger_sha256',
                                                         'matched_input_sha256'))):
        raise ValueError('Cascade raw/compiled runs differ in inputs, profiles or gateway ledger')
    for report in (raw, compiled):
        representation = report['representation']
        policies.update({f'cascade/{representation}/{name}': value for name, value in
                         cascade_items(report, oda_policies, public).items()})

    strata = {'all': list(public)}
    exposure_path = args.panel / 'exposure.json'
    if exposure_path.is_file():
        exposure = matched(read(exposure_path), public, 'exposure', args.dataset)
        for ident, row in exposure.items():
            strata.setdefault(f'exposure/{row["exposure"]}', []).append(ident)
        if independent := strata.get(f'exposure/{INDEPENDENT_EXPOSURE}'):
            strata['no_detected_overlap'] = independent
            if exposed := [ident for ident in public if exposure[ident]['exposure'] != INDEPENDENT_EXPOSURE]:
                strata['detected_overlap'] = exposed
    complete = [ident for ident in public
                if all(not items[ident].unknown_usage_calls for items, _ in policies.values())]
    strata['common_complete_usage'] = complete
    result = {}
    for group, ids in strata.items():
        points = ({name: summarize([items[ident] for ident in ids]) for name, (items, _) in policies.items()}
                  if ids else {})
        result[group] = {'n': len(ids), 'policies': points,
                         'serial_call_time_frontier': frontier(points, 'mean_serial_call_seconds')}
    result['common_complete_usage'].update(
        excluded_n=len(public) - len(complete),
        token_frontier=frontier(result['common_complete_usage']['policies'], 'total_tokens'))
    acquisition = {}
    for name, source, key, scope in (
        ('oda', args.oda_run, 'collection_wall_seconds_this_pass', 'Collector pass over its requested actions and rows.'),
        ('car', args.car_run, 'collection_wall_seconds', 'CAR evaluation pass, excluding earlier draft/probe acquisition.'),
    ):
        collection = source / 'collection.json'
        if collection.is_file():
            acquisition[name] = {key: read(collection)[key], 'scope': scope}
    return {'dataset': args.dataset, 'n': len(public), 'panel': panel, 'oda': provenance,
            'input_sha256': {name: digest_file(path) for name, path in (
                ('car', args.car_run / 'outcomes.jsonl'), ('budgetverify_gbm', args.budgetverify_gbm),
                ('budgetverify_tabfm', args.budgetverify_tabfm), ('cascade_raw', args.cascade_raw),
                ('cascade_compiled', args.cascade_compiled))},
            'policy_metadata': {name: info for name, (_, info) in policies.items()},
            'token_cost': 'The common complete-usage stratum retains questions with complete usage for every '
                          'included policy. Known sums with missing usage are lower bounds.',
            'timing': {'serial_call_seconds': 'Sum of recorded elapsed durations for selected calls on each question.',
                       'online_policy_wall_seconds': None, 'acquisition_wall': acquisition},
            'strata': result}


def render_table(report):
    rows = ['policy\tn\tstrict\taccuracy\ttotal_tokens\tknown_tokens\tunknown_usage_calls\t'
            'mean_serial_call_seconds\tcommon_complete_n\tcommon_complete_tokens\t'
            'common_complete_accuracy\tcommon_complete_token_frontier']
    full = report['strata']['all']
    shared = report['strata']['common_complete_usage']
    for name, row in sorted(full['policies'].items()):
        tokens = 'unknown' if row['total_tokens'] is None else str(row['total_tokens'])
        pair = shared['policies'].get(name)
        pair_stats = f'{pair["total_tokens"]}\t{pair["accuracy"]:.6f}' if pair is not None else 'n/a\tn/a'
        rows.append(f'{name}\t{row["n"]}\t{row["correct"]}\t{row["accuracy"]:.6f}\t{tokens}\t{row["known_tokens"]}'
                    f'\t{row["unknown_usage_calls"]}\t{row["mean_serial_call_seconds"]:.3f}'
                    f'\t{shared["n"]}\t{pair_stats}\t{int(name in shared["token_frontier"])}')
    return '\n'.join(rows) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=('finqa', 'tatqa'), required=True)
    for name in ('panel', 'oda-run', 'car-run', 'budgetverify-gbm', 'budgetverify-tabfm',
                 'cascade-raw', 'cascade-compiled', 'output'):
        parser.add_argument(f'--{name}', type=Path, required=True)
    parser.add_argument('--table', type=Path, help='Optional TSV with full-panel points')
    args = parser.parse_args()
    if args.output.exists() or (args.table is not None and
                                (args.table.exists() or args.table.resolve() == args.output.resolve())):
        parser.error('Use fresh and distinct output files')
    report = build_report(args)
    write_json(args.output, report)
    if args.table is not None:
        args.table.write_text(render_table(report), encoding='utf-8')


if __name__ == '__main__':
    main()
