"""Aggregate matched benchmark outcomes, with optional first-answer receipt verification."""

import argparse
from hashlib import sha256
import json
from math import fsum, isclose, isfinite
from pathlib import Path
from statistics import median, quantiles
from typing import NamedTuple

from benchmark_actions import action_cost, digest_file
from budget_policy import calibration_operating_point
from diagnose import paired_effect
from paired_tradeoff import paired_tradeoff
from run_pilot import load_lines, write_json


TIERS = ('low', 'mid', 'high')
MODELS = ('oda-8b', 'qwen-27b', 'deepseek')
CONTRACT_CASCADE = 'contract_8b_free_qwen_deepseek'
FLAGSHIP = f'cascade/compiled/{CONTRACT_CASCADE}'
CAR_COMPILED = 'car_compiled'
INTERVAL_ANCHORS = ('cascade/compiled/nonexecution_8b_qwen_deepseek',
                    'cascade/compiled/nonexecution_deepseek_qwen', 'oda/compiled_fallback', 'car')
TRADEOFF_BASELINES = (*INTERVAL_ANCHORS, 'cascade/compiled/cascade_routing_1.5',
                      'cascade/raw/cascade_routing_1.5',
                      'cascade/compiled/nonexecution_qwen_deepseek', 'cascade/compiled/nonexecution_8b_deepseek_qwen',
                      *(f'cascade/compiled/always_{model}' for model in MODELS))
BOOTSTRAP_DRAWS = 10000
ODA_METHODS = ('low', 'free', 'dsl_fallback', 'contract_compile', 'compiled_fallback')
INDEPENDENT_EXPOSURE = 'no_pilot_or_reserved_context_detected'


class Outcome(NamedTuple):
    strict: int
    known_tokens: int
    unknown_usage_calls: int
    calls: int
    serial_seconds: float
    executable: bool | None = None


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def matched(rows, ids, label, dataset=None):
    if dataset is not None:
        rows = [row for row in rows if row['dataset'] == dataset]
    index = {row['id']: row for row in rows}
    if index.keys() != set(ids) or len(index) != len(rows):
        raise ValueError(f'{label}: expected exactly one row for each matched question')
    return index


def execution_flag(value):
    if value is not None and (type(value) not in (bool, int) or value not in (0, 1)):
        raise ValueError('execution flag must be binary or unknown')
    return None if value is None else bool(value)


def matched_execution(value, source, label):
    value = execution_flag(value)
    if value is not None and source is not None and value != source:
        raise ValueError(f'{label}: execution flag differs from its matched source')
    return source if value is None else value


def outcome(strict, cost, *, executable=None):
    known, unknown, calls = (cost[key] for key in ('known_tokens', 'unknown_usage_calls', 'calls'))
    seconds = cost['summed_call_seconds']
    if (type(strict) not in (bool, int) or strict not in (0, 1)
            or any(type(value) is not int or value < 0 for value in (known, unknown, calls))
            or not 0 <= unknown <= calls or not isfinite(seconds) or seconds < 0
            or ('total_tokens' in cost and cost['total_tokens'] != (None if unknown else known))):
        raise ValueError('invalid matched correctness, usage or call duration')
    return Outcome(int(strict), known, unknown, calls, seconds, execution_flag(executable))


def selected_action(row, action):
    saved = row['actions'][action]
    calls = saved['calls']
    if not calls or len(set(calls)) != len(calls):
        raise ValueError(f'{row["id"]}: invalid {action} call list')
    cost = action_cost([row['calls'][name] for name in calls])
    if cost != saved['cost']:
        raise ValueError(f'{row["id"]}: recorded {action} cost differs from its receipts')
    executable = execution_flag(saved.get('executable'))
    if executable and (action == 'free' or (action in ('dsl_fallback', 'compiled_fallback') and 'free' in calls)):
        raise ValueError(f'{row["id"]}: free numeric output cannot be an executed program')
    return outcome(saved['strict'], cost, executable=executable)


def summarize(rows):
    correct = sum(row.strict for row in rows)
    known = sum(row.known_tokens for row in rows)
    unknown = sum(row.unknown_usage_calls for row in rows)
    execution_unknown = sum(row.executable is None for row in rows)
    joint_unknown = sum(row.strict and row.executable is None for row in rows)
    serial = [row.serial_seconds for row in rows]
    return {'n': len(rows), 'correct': correct, 'accuracy': correct / len(rows),
            'executable': None if execution_unknown else sum(row.executable is True for row in rows),
            'strict_and_executable': None if joint_unknown else sum(row.strict and row.executable is True for row in rows),
            'execution_known_n': len(rows) - execution_unknown, 'execution_unknown_n': execution_unknown,
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
            or any(source[key] != measured[key] for key in ('executable', 'strict_and_executable')
                   if source.get(key) is not None)
            or (not cascade and source['calls'] != measured['calls'])):
        raise ValueError('reported policy summary differs from its matched items')


def car_items(root, oda, ids, dataset, panel, oda_digest):
    contract = read(root / 'run.json')
    if (contract['schema'] != 'finance-car-collection-v1' or contract['stage'] != 'eval'
            or contract['dataset'] != dataset or contract['panel'] != panel
            or contract['draft_collection'] != oda_digest or not contract['policy']):
        raise ValueError('CAR outcomes need the matched ODA drafts, frozen panel and policy')
    rows = matched(load_lines(root / 'outcomes.jsonl'), ids, 'CAR', dataset)
    results, compiled = {}, {}
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
        retained = not row['attempted_repair'] or row.get('repaired') is False
        execution_source = execution_flag(draft['actions']['low'].get('executable')) if retained else None
        execution = matched_execution(row.get('executable'), execution_source, f'CAR/{ident}')
        results[ident] = outcome(row['strict'], cost, executable=execution)
        if 'compiled_selection' in row:
            selection = row['compiled_selection']
            if (not isinstance(selection, dict) or set(selection) != {'strict', 'executable'}
                    or any(type(value) is not bool for value in selection.values())
                    or type(row.get('repaired')) is not bool or (row['repaired'] and not row['attempted_repair'])):
                raise ValueError(f'{ident}: invalid compiled CAR selection')
            item = outcome(selection['strict'], cost, executable=selection['executable'])
            if retained:
                expected = selected_action(draft, 'contract_compile')
                if (item.strict, item.executable) != (expected.strict, expected.executable):
                    raise ValueError(f'{ident}: compiled CAR selection differs from retained ODA draft')
            elif not execution or not item.executable:
                raise ValueError(f'{ident}: the accepted CAR repair must remain executable')
            compiled[ident] = item
    metadata = {'family': 'CAR adaptation', 'policy_sha256': contract['policy'],
                'probe_decoding': contract.get('probe_decoding')}
    policies = {'car': (results, metadata)}
    if compiled:
        if compiled.keys() != results.keys():
            raise ValueError('compiled CAR selections must cover the matched panel')
        policies[CAR_COMPILED] = (compiled, {**metadata, 'representation': 'compiled_selected_submission'})
    return policies


def budget_items(report, oda, ids, dataset, provenance, expected_method):
    order = report['eval_ids']
    if (report['dataset'] != dataset or report['method'] != expected_method or set(order) != set(ids)
            or len(order) != len(ids) or report['inputs']['eval'] != provenance):
        raise ValueError(f'{expected_method}: report, panel or ODA run differs')
    tiers = {tier: {ident: selected_action(oda[ident], tier) for ident in order} for tier in TIERS}
    labels = report.get('eval_strict_by_tier')
    execution_flags = report.get('eval_executable_by_tier')
    replayed = 'verifier_replay' in report
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
    if execution_flags is not None and (set(execution_flags) != set(TIERS)
                                        or any(len(values) != len(order) for values in execution_flags.values())):
        raise ValueError('BudgetVerify requires one execution flag per eval question and tier')
    for tier in TIERS:
        flags = execution_flags[tier] if execution_flags is not None else [None] * len(order)
        for ident, flag in zip(order, flags, strict=True):
            item = tiers[tier][ident]
            source = None if replayed and tier == 'high' else item.executable
            execution = matched_execution(flag, source, f'BudgetVerify/{tier}/{ident}')
            tiers[tier][ident] = item._replace(executable=execution)

    compiled = report.get('eval_public_compiler_by_tier')
    compiled_tiers = {}
    if compiled is not None:
        if not replayed or set(compiled) != set(TIERS):
            raise ValueError('The shared compiler requires decoded results for all BudgetVerify tiers')
        for tier, flags in compiled.items():
            if (set(flags) != {'strict', 'executable'} or any(len(column) != len(order) for column in flags.values())
                    or any(type(value) is not bool for column in flags.values() for value in column)):
                raise ValueError(f'BudgetVerify shared compiler: malformed {tier} flags')
            compiled_tiers[tier] = {
                ident: tiers[tier][ident]._replace(strict=int(strict), executable=executable)
                for ident, strict, executable in zip(order, flags['strict'], flags['executable'], strict=True)
            }

    policies = {}
    compiled_policies = {}
    candidates = [(f'fixed_{tier}', record, {}) for tier, record in report['fixed'].items()]
    deploy_name = None
    if all('calibration' in point for point in report['policies']):
        deploy = calibration_operating_point(report['policies'])
        deploy_name = 'fixed_low' if deploy is None else f'lambda_{deploy["lambda"]:g}'
    for point in report['policies']:
        if point['calibration_frontier']:
            candidates.append((f'lambda_{point["lambda"]:g}', point['eval'],
                               {'lambda': point['lambda'], 'calibration_frontier': True, 'config': point['config']}))
    for name, record, details in candidates:
        actions = record['tiers_in_eval_order']
        items = {ident: tiers[action][ident] for ident, action in zip(order, actions, strict=True)}
        check_summary(record['all'], summarize(list(items.values())))
        metadata = {'family': 'BudgetVerify adaptation', 'classifier': report['method'],
                    'verifier_replay': replayed, 'calibration_operating_point_2x': name == deploy_name,
                    'batch_prediction_seconds': record.get('prediction_batch_seconds'), **details}
        policies[name] = items, metadata
        if compiled_tiers:
            compiled_items = {ident: compiled_tiers[tier][ident] for ident, tier in zip(order, actions, strict=True)}
            compiled_policies[name] = compiled_items, {**metadata, 'public_compiler': 'shared_public_contract_v1'}
    return policies, compiled_policies


def shared_budgetverify_inputs(gbm, tabfm):
    inputs = gbm['inputs']
    if (set(inputs) != {'fit', 'calibration', 'eval'}
            or any(set(split) != {'run.json', 'outcomes.jsonl'} for split in inputs.values())
            or tabfm['inputs'] != inputs):
        raise ValueError('BudgetVerify GBM and TabFM require identical fit, calibration and eval receipts')
    replay_fields = ('run_profile', 'eval_ids', 'verifier_replay', 'eval_strict_by_tier', 'eval_public_compiler_by_tier')
    flag_key = 'eval_executable_by_tier'
    if (any(gbm.get(field) != tabfm.get(field) for field in replay_fields)
            or (flag_key in gbm and flag_key in tabfm and gbm[flag_key] != tabfm[flag_key])):
        raise ValueError('BudgetVerify GBM and TabFM require the same tier outcomes and verifier decoding')
    return inputs


def cascade_items(report, oda_policies, ids):
    representation = report['representation']
    input_rows = {name: matched(point['items'], ids, name) for name, point in report['policies'].items()}
    direct = {}
    for model in MODELS:
        rows = input_rows[f'always_{model}']
        if any(row['selected'] != model or row['queried'] != [model] for row in rows.values()):
            raise ValueError(f'{model}: non-direct receipt for a single-model baseline')
        direct[model] = {ident: outcome(row['strict'], {**row, 'calls': 1}, executable=row.get('executable'))
                         for ident, row in rows.items()}
    local = 'low' if representation == 'raw' else 'contract_compile'
    for ident, item in direct['oda-8b'].items():
        matched_oda = oda_policies[local][ident]
        if item._replace(executable=None) != matched_oda._replace(executable=None):
            raise ValueError(f'Cascade {representation}: ODA decisions differ from matched ODA actions')
        execution = matched_execution(item.executable, matched_oda.executable, f'Cascade/{representation}/ODA/{ident}')
        direct['oda-8b'][ident] = item._replace(executable=execution)
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
            execution = matched_execution(row.get('executable'), source[ident].executable, f'{name}/{ident}')
            measured = outcome(row['strict'], {**row, 'calls': len(queried)}, executable=execution)
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


def frontier(points, cost, success='correct'):
    complete = {name: row for name, row in points.items() if row[cost] is not None}
    return sorted(name for name, row in complete.items() if not any(
        other[cost] <= row[cost] and other[success] >= row[success]
        and (other[cost] < row[cost] or other[success] > row[success])
        for other in complete.values()))


def matched_frontiers(policies, strata):
    ids = strata['all']
    known_usage = [ident for ident in ids
                   if all(not items[ident].unknown_usage_calls for items, _ in policies.values())]
    known_execution = [ident for ident in ids
                       if all(items[ident].executable is not None for items, _ in policies.values())]
    usage_ids = set(known_usage)
    known_both = [ident for ident in known_execution if ident in usage_ids]
    strata = {**strata, 'common_complete_usage': known_usage, 'common_complete_execution': known_execution,
              'common_complete_usage_and_execution': known_both}
    result = {}
    for name, cohort in strata.items():
        points = ({policy: summarize([items[ident] for ident in cohort])
                   for policy, (items, _) in policies.items()} if cohort else {})
        result[name] = {'n': len(cohort), 'policies': points,
                        'serial_call_time_frontier': frontier(points, 'mean_serial_call_seconds')}
    for group, cost, metric, field in (
        ('common_complete_usage', 'total_tokens', 'correct', 'token_frontier'),
        ('common_complete_execution', 'mean_serial_call_seconds', 'strict_and_executable',
         'executable_correct_serial_call_time_frontier'),
        ('common_complete_usage_and_execution', 'total_tokens', 'strict_and_executable',
         'executable_correct_token_frontier'),
    ):
        record = result[group]
        record['excluded_n'] = len(ids) - record['n']
        record[field] = frontier(record['policies'], cost, metric)
    return strata, result


def reference_depth_strata(programs: dict[str, str | None]) -> dict[str, list[str]]:
    """Split FinQA questions by reference depth for reporting after evaluation."""
    if not any(program is not None for program in programs.values()):
        return {}
    if any(not isinstance(program, str) or '(' not in program for program in programs.values()):
        raise ValueError('FinQA depth stratification requires a reference program for each question')
    strata = {}
    for ident, program in programs.items():
        depth = 'single' if program.count('(') == 1 else 'multi'
        strata.setdefault(f'reference_depth/{depth}', []).append(ident)
    return strata


def paired_evaluation(policies, public, strata):
    missing = {FLAGSHIP, *INTERVAL_ANCHORS} - policies.keys()
    if missing:
        raise ValueError(f'Missing paired comparison anchors: {sorted(missing)}')
    proposed = policies[FLAGSHIP][0]
    by_stratum = {}
    for group in ('all', 'no_detected_overlap'):
        if group not in strata:
            continue
        ids = strata[group]
        clusters = len({public[ident] for ident in ids})
        comparisons = {}
        for name, (baseline, _) in policies.items():
            if name == FLAGSHIP:
                continue
            differences = [proposed[ident].strict - baseline[ident].strict for ident in ids]
            contrast = {'n': len(ids), 'clusters': clusters, 'gains': differences.count(1),
                        'harms': differences.count(-1), 'net_pp': 100 * sum(differences) / len(ids)}
            if name in INTERVAL_ANCHORS:
                examples = [(public[ident], {'flagship': {'strict': proposed[ident].strict},
                                              'comparator': {'strict': baseline[ident].strict}}) for ident in ids]
                bootstrap = paired_effect(examples, (('flagship', 'strict'), ('comparator', 'strict')), BOOTSTRAP_DRAWS)
                contrast['paired_cluster_percentile_95_pp'] = bootstrap['paired_cluster_percentile_95_pp']
            comparisons[name] = contrast
        by_stratum[group] = comparisons
    return {'flagship': FLAGSHIP, 'interval_anchors': list(INTERVAL_ANCHORS),
            'bootstrap': {'draws': BOOTSTRAP_DRAWS, 'seed': 20261119,
                          'cluster': 'FinQA report or TAT-QA table context as recorded by the panel.',
                          'interval': 'Pointwise paired cluster percentile 95% interval in percentage points.'},
            'by_stratum': by_stratum}


def paired_compiler_effect(policies, public, strata):
    """Compare the same first replies with and without public compilation."""
    by_stratum = {group: {} for group in ('all', 'no_detected_overlap', 'reference_depth/single', 'reference_depth/multi')
                  if group in strata}
    first_replies = {}
    columns = (('compiled', 'strict'), ('raw', 'strict'))
    for model in MODELS:
        raw, _ = policies[f'cascade/raw/always_{model}']
        compiled, _ = policies[f'cascade/compiled/always_{model}']
        if any(raw[ident]._replace(strict=0, executable=None) != compiled[ident]._replace(strict=0, executable=None)
               for ident in public):
            raise ValueError(f'{model}: the same-call compiler comparison has different recorded charges')
        first_replies[model] = raw, compiled
        for group, models in by_stratum.items():
            ids = strata[group]
            metrics = {}
            for name in ('strict', 'strict_and_executable'):
                observable = ids if name == 'strict' else [ident for ident in ids
                                                           if raw[ident].executable is not None
                                                           and compiled[ident].executable is not None]
                examples = [(public[ident], {
                    arm: {'strict': bool(rows[ident].strict and (name == 'strict' or rows[ident].executable))}
                    for arm, rows in (('raw', raw), ('compiled', compiled))
                }) for ident in observable]
                metrics[name] = {'n': 0} if not examples else {
                    **paired_effect(examples, columns, BOOTSTRAP_DRAWS),
                    'raw_correct': sum(outcomes['raw']['strict'] for _, outcomes in examples),
                    'compiled_correct': sum(outcomes['compiled']['strict'] for _, outcomes in examples),
                }
            models[model] = metrics
    rescue_overlap = {}
    for group in by_stratum:
        counts = [0] * (len(MODELS) + 1)
        exclusive = dict.fromkeys(MODELS, 0)
        all_raw_wrong = all_raw_wrong_rescued = 0
        for ident in strata[group]:
            rescued = [model for model, (raw, compiled) in first_replies.items()
                       if not raw[ident].strict and compiled[ident].strict]
            counts[len(rescued)] += 1
            if len(rescued) == 1:
                exclusive[rescued[0]] += 1
            if all(not raw[ident].strict for raw, _ in first_replies.values()):
                all_raw_wrong += 1
                all_raw_wrong_rescued += bool(rescued)
        rescue_overlap[group] = {'n': len(strata[group]), 'rescued_by_model_count': counts,
                                 'rescued_by_only': exclusive, 'all_raw_wrong': all_raw_wrong,
                                 'all_raw_wrong_rescued': all_raw_wrong_rescued}
    return {'scope': 'Raw versus compiled on the same direct model calls. The joint metric uses pairs with both '
                     'execution flags known. Intervals resample reports or table contexts within each contrast.',
            'by_stratum': by_stratum, 'strict_rescue_overlap_by_stratum': rescue_overlap}


def paired_tradeoff_report(policies, public, strata):
    """Report paired uncertainty at named operating points independent of eval accuracy."""
    names = [name for name in TRADEOFF_BASELINES if name in policies]
    missing = [name for name in TRADEOFF_BASELINES if name not in policies]
    if CAR_COMPILED in policies:
        names.append(CAR_COMPILED)
    for classifier in ('tabfm', 'gbm'):
        prefix = f'budgetverify/{classifier}/'
        budget_points = [name for name, (_, metadata) in policies.items()
                         if name.startswith(prefix) and metadata.get('calibration_operating_point_2x')]
        if len(budget_points) > 1:
            raise ValueError(f'Expected one deployment operating point for BudgetVerify {classifier}')
        if not budget_points:
            missing.append(f'{prefix}calibration_operating_point_2x')
            continue
        point = budget_points[0]
        names.append(point)
        compiled = point.replace('budgetverify/', 'budgetverify_compiled/', 1)
        if compiled in policies:
            names.append(compiled)
    proposed = policies[FLAGSHIP][0]
    by_stratum = {}
    executable_by_stratum = {}
    for group in ('all', 'no_detected_overlap'):
        if group in strata:
            by_stratum[group] = {name: paired_tradeoff(proposed, policies[name][0], strata[group], public,
                                                        draws=BOOTSTRAP_DRAWS) for name in names}
            executable_by_stratum[group] = {
                name: paired_tradeoff(proposed, policies[name][0], strata[group], public,
                                      draws=BOOTSTRAP_DRAWS, require_execution=True) for name in names}
    return {'proposed': FLAGSHIP, 'anchors': names, 'unavailable_anchors': missing, 'by_stratum': by_stratum,
            'strict_and_executable_by_stratum': executable_by_stratum,
            'execution_scope': 'The joint success metric retains only pairs with both execution flags known.',
            'token_scope': 'Same questions with complete token usage in both policies for each contrast.',
            'time_scope': 'Sum of recorded calls per question. Fresh online timing is supplementary.'}


def literal_ratio_sensitivity(compiled, policies, strata):
    """Validate fixed-call target scoring changes against the headline baselines."""
    sensitivity = compiled.get('literal_ratio_sensitivity')
    if sensitivity is None:
        return None
    if (compiled['dataset'] != 'finqa' or not isinstance(sensitivity, dict)
            or not isinstance(sensitivity.get('rule'), str) or not sensitivity['rule'].strip()
            or not isinstance(sensitivity.get('policies'), dict) or not sensitivity['policies']):
        raise ValueError('literal ratio sensitivity requires a FinQA rule and fixed policies')
    fields = ('n', 'baseline_correct', 'guarded_correct', 'gains', 'harms', 'changed_values')
    for name, scopes in sensitivity['policies'].items():
        qualified = f'cascade/compiled/{name}'
        if (qualified not in policies or policies[qualified][1]['target_mean_tokens'] is not None or not isinstance(scopes, dict)
                or 'all' not in scopes or set(scopes) - {'all', 'no_detected_overlap'}):
            raise ValueError(f'{name}: literal ratio sensitivity requires a fixed policy and valid strata')
        for group in ('all', 'no_detected_overlap'):
            if group not in scopes:
                continue
            counts = scopes[group]
            if (group not in strata or not isinstance(counts, dict)
                    or any(type(counts.get(key)) is not int for key in fields)):
                raise ValueError(f'{name}/{group}: invalid literal ratio sensitivity counts or stratum')
            n, baseline, guarded, gains, harms, changed = (counts[key] for key in fields)
            expected = strata[group]['policies'][qualified]
            if (n != expected['n'] or baseline != expected['correct']
                    or guarded != baseline + gains - harms or not 0 <= gains <= n - baseline
                    or not 0 <= harms <= baseline or not gains + harms <= changed <= n):
                raise ValueError(f'{name}/{group}: literal ratio sensitivity counts differ from matched outcomes')
            if group != 'all' and any(counts[key] > scopes['all'][key] for key in fields):
                raise ValueError(f'{name}/{group}: literal ratio sensitivity exceeds full-cohort counts')
    return {**sensitivity, 'scope': 'Fixed recorded selections and charges. Separate scoring sensitivity.'}


def build_direct_report(args):
    """Verify and summarize the matched first replies before secondary actions finish."""
    from benchmark_actions import read_panel
    from cascade_benchmark import managed_direct_wall, replay_independent
    from school_benchmark import campus

    rows, gold, panel = read_panel(args.panel, args.dataset)
    public = {row['id']: row['report'] for row in rows}
    ledger = read(args.campus_ledger)
    provider_models = (None, campus.QWEN_MODEL, campus.MODEL)
    policies, inputs, wall = {}, {}, {}
    for arm, run, provider in zip(MODELS, args.direct_runs, provider_models, strict=True):
        contract_path = run / 'run.json'
        contract = read(contract_path)
        model = provider or 'oda-fin-rl-8b'
        if (contract['schema'] != 'finance-benchmark-actions-v1' or contract['panel'] != panel
                or contract['model'] != model or contract['dataset'] not in (None, args.dataset)
                or 'independent' not in contract['actions']
                or (provider is not None and contract['endpoint'] != campus.BASE_URL)):
            raise ValueError(f'{arm}: unexpected first-answer collection contract')
        early = run / 'direct_outcomes.jsonl'
        source = early if provider is None and early.is_file() else run / 'outcomes.jsonl'
        records = load_lines(source)
        native = matched(records, public, arm, args.dataset)
        if any(native[ident]['report'] != report for ident, report in public.items()):
            raise ValueError(f'{arm}: native report identifiers differ from the panel')
        run_digest = digest_file(contract_path)
        inputs[arm] = {'run.json': run_digest, source.name: digest_file(source)}
        if provider:
            wall[arm] = managed_direct_wall(records, args.dataset, public)
        for representation in ('raw', 'compiled'):
            outcomes = {}
            for row in rows:
                ident = row['id']
                measured, _ = replay_independent(run, run_digest, row, gold[args.dataset, ident], native[ident],
                                                  provider, ledger, args.metric_dir, representation)
                item = outcome(measured['strict'], measured['cost'], executable=measured['executable'])
                if provider is None and representation == 'compiled' and item != selected_action(
                        native[ident], 'contract_compile'):
                    raise ValueError(f'{arm}: stored compiler result differs from its first reply for {ident}')
                outcomes[ident] = item
            policies[f'cascade/{representation}/always_{arm}'] = outcomes, {'family': 'Fixed baseline'}

    scopes = {'all': list(public)}
    if args.dataset == 'finqa':
        scopes.update(reference_depth_strata({ident: gold[args.dataset, ident].get('program') for ident in public}))
    exposure_path = args.panel / 'exposure.json'
    if exposure_path.is_file():
        exposure = matched(read(exposure_path), public, 'exposure', args.dataset)
        independent = [ident for ident in public if exposure[ident]['exposure'] == INDEPENDENT_EXPOSURE]
        if independent:
            scopes['no_detected_overlap'] = independent
    scopes, strata = matched_frontiers(policies, scopes)
    return {'scope': 'Single-model direct arms only. Secondary actions and routed comparisons use the full report.',
            'dataset': args.dataset, 'n': len(public), 'panel': panel, 'first_answer_inputs': inputs,
            'campus_ledger_sha256': digest_file(args.campus_ledger), 'strata': strata,
            'policy_metadata': {name: info for name, (_, info) in policies.items()},
            'paired_compiler_effect': paired_compiler_effect(policies, public, scopes),
            'timing': {'native_managed_direct_wall': wall,
                       'serial_calls': 'Recorded original one-call durations. End-to-end timing coverage is separate.'}}


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
    policies.update(car_items(args.car_run, oda, public, args.dataset, panel, provenance['outcomes.jsonl']))
    gbm, tabfm = read(args.budgetverify_gbm), read(args.budgetverify_tabfm)
    budget_inputs = shared_budgetverify_inputs(gbm, tabfm)
    for tag, record, method in (('gbm', gbm, 'GBM'), ('tabfm', tabfm, 'TabFM-1.0.0-PyTorch')):
        native, compiled_budget = budget_items(record, oda, public, args.dataset, provenance, method)
        policies.update({f'budgetverify/{tag}/{name}': value for name, value in native.items()})
        policies.update({f'budgetverify_compiled/{tag}/{name}': value for name, value in compiled_budget.items()})

    raw, compiled = read(args.cascade_raw), read(args.cascade_compiled)
    if (raw['representation'] != 'raw' or compiled['representation'] != 'compiled'
            or raw['dataset'] != args.dataset or compiled['dataset'] != args.dataset
            or raw.get('managed_direct_wall') != compiled.get('managed_direct_wall')
            or any(raw[key] != compiled[key] for key in ('profiles', 'author_revision', 'campus_ledger_sha256',
                                                         'matched_input_sha256'))):
        raise ValueError('Cascade raw/compiled runs differ in inputs, profiles or gateway ledger')
    for report in (raw, compiled):
        representation = report['representation']
        policies.update({f'cascade/{representation}/{name}': value for name, value in
                         cascade_items(report, oda_policies, public).items()})

    strata = {'all': list(public)}
    if args.dataset == 'finqa':
        references = matched(load_lines(args.panel / 'references.jsonl'), public, 'FinQA references', args.dataset)
        strata.update(reference_depth_strata({ident: row['gold'].get('program') for ident, row in references.items()}))
    exposure_path = args.panel / 'exposure.json'
    if exposure_path.is_file():
        exposure = matched(read(exposure_path), public, 'exposure', args.dataset)
        for ident, row in exposure.items():
            strata.setdefault(f'exposure/{row["exposure"]}', []).append(ident)
        if independent := strata.get(f'exposure/{INDEPENDENT_EXPOSURE}'):
            strata['no_detected_overlap'] = independent
            if exposed := [ident for ident in public if exposure[ident]['exposure'] != INDEPENDENT_EXPOSURE]:
                strata['detected_overlap'] = exposed
    strata, result = matched_frontiers(policies, strata)
    acquisition = {}
    for name, source, key, scope in (
        ('oda', args.oda_run, 'collection_wall_seconds_this_pass', 'Collector pass over its requested actions and rows.'),
        ('car', args.car_run, 'collection_wall_seconds', 'CAR evaluation pass, excluding earlier draft/probe acquisition.'),
    ):
        collection = source / 'collection.json'
        if collection.is_file():
            acquisition[name] = {key: read(collection)[key], 'scope': scope}
    report = {'dataset': args.dataset, 'n': len(public), 'panel': panel, 'oda': provenance,
            'input_sha256': {name: digest_file(path) for name, path in (
                ('car', args.car_run / 'outcomes.jsonl'), ('budgetverify_gbm', args.budgetverify_gbm),
                ('budgetverify_tabfm', args.budgetverify_tabfm), ('cascade_raw', args.cascade_raw),
                ('cascade_compiled', args.cascade_compiled))},
            'budgetverify_inputs': budget_inputs, 'policy_metadata': {name: info for name, (_, info) in policies.items()},
            'paired_strict_evaluation': paired_evaluation(policies, public, strata),
            'paired_compiler_effect': paired_compiler_effect(policies, public, strata),
            'paired_tradeoff_evaluation': paired_tradeoff_report(policies, public, strata),
            'token_cost': 'The common complete-usage stratum retains questions with complete usage for every '
                          'included policy. Known sums with missing usage are lower bounds.',
            'execution': 'Executable counts require known execution flags. Joint counts require known flags '
                         'for every strict match. Joint frontiers use shared known flags. The joint token '
                         'frontier also requires complete usage.',
            'reference_depth_scope': 'FinQA reference-program step count, used only after decisions are recorded.',
            'timing': {'serial_call_seconds': 'Sum of recorded elapsed durations for selected calls on each question.',
                       'online_policy_wall_seconds': None, 'acquisition_wall': acquisition,
                       'native_managed_direct_wall': raw.get('managed_direct_wall'),
                       'native_managed_timing_scope': 'Original, fresh single-model requests through native selection. '
                                                      'The replayed policies have separate timing evidence.'},
            'strata': result}
    if (sensitivity := literal_ratio_sensitivity(compiled, policies, result)) is not None:
        report['literal_ratio_sensitivity'] = sensitivity
    if 'oda_prepend_tradeoff' in compiled:
        report['oda_prepend_tradeoff'] = compiled['oda_prepend_tradeoff']
    return report


def render_table(report):
    header = ('policy\tn\tstrict\taccuracy\ttotal_tokens\tknown_tokens\tunknown_usage_calls\t'
              'mean_serial_call_seconds\tcommon_complete_n\tcommon_complete_tokens\t'
              'common_complete_accuracy\tcommon_complete_token_frontier\texecutable\tstrict_and_executable\t'
              'execution_known_n\texecution_unknown_n')
    strata = report['strata']
    joint_axes = (
        ('common_complete_execution', 'mean_serial_call_seconds', 'executable_correct_serial_call_time_frontier', '.3f'),
        ('common_complete_usage_and_execution', 'total_tokens', 'executable_correct_token_frontier', 'd'),
    ) if 'common_complete_execution' in strata else ()
    for group, cost, _, _ in joint_axes:
        header += f'\t{group}_n\t{group}_correct\t{group}_{cost}\t{group}_frontier'
    rows = [header]
    full = strata['all']
    shared = strata['common_complete_usage']
    for name, row in sorted(full['policies'].items()):
        tokens = 'unknown' if row['total_tokens'] is None else str(row['total_tokens'])
        pair = shared['policies'].get(name)
        pair_stats = f'{pair["total_tokens"]}\t{pair["accuracy"]:.6f}' if pair is not None else 'n/a\tn/a'
        flags = '\t'.join('unknown' if row[key] is None else str(row[key])
                          for key in ('executable', 'strict_and_executable', 'execution_known_n', 'execution_unknown_n'))
        line = (f'{name}\t{row["n"]}\t{row["correct"]}\t{row["accuracy"]:.6f}\t{tokens}\t{row["known_tokens"]}'
                f'\t{row["unknown_usage_calls"]}\t{row["mean_serial_call_seconds"]:.3f}'
                f'\t{shared["n"]}\t{pair_stats}\t{int(name in shared["token_frontier"])}\t{flags}')
        for group, cost, frontier_field, precision in joint_axes:
            cohort = strata[group]
            point = cohort['policies'].get(name)
            metrics = f'{point["strict_and_executable"]}\t{point[cost]:{precision}}' if point is not None else 'n/a\tn/a'
            line += f'\t{cohort["n"]}\t{metrics}\t{int(name in cohort[frontier_field])}'
        rows.append(line)
    return '\n'.join(rows) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', choices=('finqa', 'tatqa'), required=True)
    primary_inputs = ('oda-run', 'car-run', 'budgetverify-gbm', 'budgetverify-tabfm', 'cascade-raw', 'cascade-compiled')
    for name in ('panel', 'output'):
        parser.add_argument(f'--{name}', type=Path, required=True)
    for name in primary_inputs:
        parser.add_argument(f'--{name}', type=Path)
    parser.add_argument('--direct-runs', nargs=3, type=Path, metavar=('ODA', 'QWEN', 'DEEPSEEK'),
                        help='Publish the first-answer comparison independently of secondary baselines')
    parser.add_argument('--campus-ledger', type=Path, help='Frozen authoritative campus ledger for direct arms')
    parser.add_argument('--metric-dir', type=Path, help='Pinned TAT-QA scorer for direct receipt replay')
    parser.add_argument('--table', type=Path, help='Optional TSV with full-panel points')
    args = parser.parse_args()
    if args.output.exists() or (args.table is not None and
                                (args.table.exists() or args.table.resolve() == args.output.resolve())):
        parser.error('Use fresh and distinct output files')
    if args.direct_runs:
        if args.campus_ledger is None or (args.dataset == 'tatqa' and args.metric_dir is None):
            parser.error('Direct arms require --campus-ledger and the official metric for TAT-QA')
        report = build_direct_report(args)
    else:
        missing = [name for name in primary_inputs if getattr(args, name.replace('-', '_')) is None]
        if missing:
            parser.error('Full report requires ' + ', '.join(f'--{name}' for name in missing))
        report = build_report(args)
    write_json(args.output, report)
    if args.table is not None:
        args.table.write_text(render_table(report), encoding='utf-8')


if __name__ == '__main__':
    main()
