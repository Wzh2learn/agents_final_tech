"""Compare base and adapted ODA under the shared native compact contract."""

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import median

from benchmark_actions import digest_file, freeze, read_panel
from compact_consensus import api_usage, compact_prompt, compact_request, evaluate_choices, grade_choices
from diagnose import paired_effect
from live_policy_timing import OFFICIAL_COUNTS

ARCHIVED_ADAPTED_COMPILER = 'ae9be2eef98e06faff1367651de60367a989d97c015d9bd047ad3e4c6a65b0bf'


def read(path):
    return json.loads(path.read_bytes())


def arm(directory, model, index, identity):
    settings = read(directory / 'run.json')
    profile_path = Path(settings['serving_profile'])
    profile = read(profile_path)
    driver = Path(__file__).resolve().parent
    compilers = {digest_file(driver / 'table_scope_replay.py')}
    if model == 'oda-compact-joint':
        # Re-execution below must reproduce every archived decision under the current compiler.
        compilers.add(ARCHIVED_ADAPTED_COMPILER)
    if (settings['model'] != model or profile['model'] != model
            or settings['serving_profile_sha256'] != digest_file(profile_path)
            or settings['panel_sha256'] != identity or settings['dataset'] is not None
            or settings['max_tokens'] != 80 or settings['single_temperature'] != 0
            or settings['seed'] != 20261127 or settings['workers'] != 4
            or settings['planned'] or settings['without_logprobs'] or settings['shared_request_cache']
            or not settings['measure_exclusive_engine'] or 1 not in settings['n']
            or settings['compiler_sha256'] not in compilers
            or settings['scorer_sha256'] != digest_file(driver / 'scoring.py')):
        raise ValueError(f'Wrong model or frozen compact configuration at {directory}')
    metric = Path(settings['metric_dir'])
    finished = read(directory / 'summary.json')
    receipts = {}
    with (directory / 'cases.jsonl').open(encoding='utf-8') as stream:
        for receipt in map(json.loads, stream):
            if receipt['n'] != 1:
                continue
            key = receipt['dataset'], receipt['id']
            row, gold, seed = index[key]
            expected = compact_request(compact_prompt(row), model, n=1, max_tokens=80,
                                       temperature=0, seed=seed)
            actual = receipt['request'].copy()
            salt = actual.pop('cache_salt', None)
            response = receipt['response']
            if (actual != expected or not salt or key in receipts or receipt['report'] != row['report']
                    or receipt['transport'] != 'vllm_chat_nonstream' or response['model'] != model):
                raise ValueError(f'Wrong or duplicate single-sample request for {key}')
            decision = evaluate_choices(row, response, 1)
            grade = grade_choices(row, decision, gold, metric)
            usage = api_usage(response)
            if decision != receipt['decision'] or grade != receipt['score'] or usage != receipt['usage']:
                raise ValueError(f'Native replay disagrees with the saved receipt for {key}')
            receipts[key] = {'correct': grade['strict_executable'], 'usage': usage,
                             'wall_seconds': receipt['route_wall_seconds']}
    if receipts.keys() != index.keys():
        raise ValueError(f'Full official coverage is required at {directory}')
    return receipts, profile, metric, finished


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('panel', 'base', 'adapted', 'output'):
        parser.add_argument(f'--{name}', required=True, type=Path)
    args = parser.parse_args()
    public, gold, identity = read_panel(args.panel, None)
    if Counter(row['dataset'] for row in public) != OFFICIAL_COUNTS:
        raise ValueError('Expected exactly the FinQA and arithmetic TAT-QA official panels')
    index = {(row['dataset'], row['id']): (row, gold[row['dataset'], row['id']], 20261127 + 8 * i)
             for i, row in enumerate(public)}
    base, bp, bm, bsum = arm(args.base, 'oda-fin-rl-8b', index, identity)
    adapted, ap, am, asum = arm(args.adapted, 'oda-compact-joint', index, identity)
    if (bp.get('base_only') is not True or 'request_adapter' not in bp or bp['request_adapter'] is not None
            or any(bp[key] != ap[key] for key in ('image', 'argv', 'mounts', 'adapter_files')) or bm != am):
        raise ValueError('The two requests must share the vLLM engine contract and exact ODA weights')
    datasets = {}
    for dataset, n in OFFICIAL_COUNTS.items():
        keys = [key for key in index if key[0] == dataset]
        rows = [(index[key][0]['report'], {'adapted': adapted[key], 'base': base[key]}) for key in keys]
        scores = paired_effect(rows, (('adapted', 'correct'), ('base', 'correct')), 10000)
        arms = {}
        for name, sampled, summary in (('base', base, bsum), ('adapted', adapted, asum)):
            items = [sampled[key] for key in keys]
            known = [item['usage'] for item in items if item['usage'] is not None]
            correct = sum(item['correct'] for item in items)
            recorded = summary[f'{dataset}/n1']
            if (recorded['questions'], recorded['strict_executable']) != (n, correct):
                raise ValueError(f'Run summary does not reproduce {name} {dataset}')
            arms[name] = {'strict_executable': correct, 'known_logical_request_tokens': sum(
                usage['total_tokens'] for usage in known), 'missing_usage': n - len(known),
                'median_measured_wall_seconds': median(item['wall_seconds'] for item in items)}
        datasets[dataset] = {'paired_accuracy': scores, 'arms': arms}
    freeze(args.output, {'schema': 'finance-compact-base-native-paired-v1', 'panel_sha256': identity,
                         'base_cases_sha256': digest_file(args.base / 'cases.jsonl'),
                         'adapted_cases_sha256': digest_file(args.adapted / 'cases.jsonl'),
                         'datasets': datasets})


if __name__ == '__main__':
    main()
