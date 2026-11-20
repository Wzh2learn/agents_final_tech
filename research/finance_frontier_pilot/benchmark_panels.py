"""Prepare official TRAIN fit/calibration splits and complete evaluation inventories."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

from cohorts import exclusion_lists, read_source, table_signature, tatqa_reserved_overlap


SEED = 'finance-frontier-benchmark-v1'
TRAIN = {
    'finqa': (
        'train',
        'https://github.com/czyssrs/FinQA/blob/0f16e2867befa6840783e58be38c9efb9229d742/dataset/train.json',
        '49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6',
        6251,
    ),
    'tatqa': (
        'train',
        'https://github.com/NExTplusplus/TAT-QA/blob/870accc41953dcde885aabeb963d94aabdc0fbc3/dataset_raw/tatqa_dataset_train.json',
        '2df6e722cdbaaa37efcbfb280f5c9a15be29a6ec18f618ef936fe63cc6d07c69',
        5543,
    ),
}


def identity_keys(public):
    report = public['report']
    keys = [('id', public['id']), ('report', report), ('table', table_signature(public['table']))]
    if public['dataset'] == 'finqa' and (filing := re.fullmatch(r'([^/]+/\d{4})/.+', report)):
        keys.append(('filing', filing[1].casefold()))
    return keys


def source_components(rows):
    neighbors = defaultdict(list)
    keysets = [identity_keys(public) for public, _, _ in rows]
    for index, keys in enumerate(keysets):
        for key in keys:
            neighbors[key].append(index)
    visited = set()
    for index in range(len(rows)):
        if index in visited:
            continue
        component, pending, keys = [], [index], set()
        visited.add(index)
        while pending:
            member = pending.pop()
            component.append(rows[member])
            for key in keysets[member]:
                keys.add(key)
                for neighbor in neighbors.pop(key, ()):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        pending.append(neighbor)
        yield component, keys


def priority(dataset, purpose, id_):
    return hashlib.sha256(f'{SEED}|{dataset}|{purpose}|{id_}'.encode()).digest()


def select_train(dataset, train, target, excluded_ids, fit_size, calibration_size, allowed_ids=None):
    train_ids = {public['id'] for public, _, _ in train}
    unknown = (excluded_ids | (allowed_ids or set())) - train_ids
    if unknown:
        raise ValueError(f'{dataset}: membership contains {len(unknown)} IDs outside the official training scope')
    target_keys = {key for public, _, _ in target for key in identity_keys(public)}
    protected_keys = {('id', id_) for id_ in excluded_ids}
    available = {'fit': [], 'calibration': []}
    audit = Counter()
    for component, keys in source_components(train):
        target_overlap = keys & target_keys
        protected_overlap = keys & protected_keys
        if target_overlap or protected_overlap:
            audit['excluded_source_groups'] += 1
            audit['excluded_train_questions'] += len(component)
            for field in {field for field, _ in target_overlap}:
                audit[f'groups_matching_eval_{field}'] += 1
            if protected_overlap:
                audit['groups_matching_protected_train'] += 1
            continue
        eligible = component if allowed_ids is None else [row for row in component if row[0]['id'] in allowed_ids]
        if not eligible:
            audit['groups_outside_allowed_train'] += 1
            continue
        stable_id = min(public['id'] for public, _, _ in component)
        assignment = 'fit' if priority(dataset, 'assignment', stable_id)[0] < 171 else 'calibration'
        representative = min(eligible, key=lambda row: (priority(dataset, 'representative', row[0]['id']), row[0]['id']))
        available[assignment].append((priority(dataset, 'order', stable_id), stable_id, representative))
    chosen = {}
    for name, count in [('fit', fit_size), ('calibration', calibration_size)]:
        options = available[name]
        audit[f'available_{name}_groups'] = len(options)
        if not 0 < count <= len(options):
            raise ValueError(f'{dataset}: requested {count} {name} groups from {len(options)} eligible groups')
        chosen[name] = [row for _, _, row in sorted(options)[:count]]
    return chosen, dict(audit)


def evaluation_exposure(path, target_metadata, target):
    payload = json.loads(path.read_text(encoding='utf-8'))
    labels = payload['published_question_membership']
    if any(set(row) != {'dataset', 'id', 'exposure'} or
           any(not isinstance(value, str) or not value for value in row.values()) for row in labels):
        raise ValueError('evaluation exposure must contain dataset, id, and exposure strings only')
    keys = {(row['dataset'], row['id']) for row in labels}
    expected = {(public['dataset'], public['id']) for public, _, _ in target}
    if len(labels) != len(keys) or keys != expected:
        raise ValueError('evaluation exposure must cover all target questions exactly once')
    for dataset, metadata in target_metadata.items():
        if payload['summary'][dataset]['dataset_revision_sha256'] != metadata['sha256']:
            raise ValueError(f'{dataset}: exposure source revision differs from the official target')
    return labels


def split_tatqa_exposure(labels, target, table_membership):
    tatqa = [row for row in target if row[0]['dataset'] == 'tatqa']
    reserved, audit = tatqa_reserved_overlap(tatqa, table_membership)
    tagged = {row['id'] for row in labels if row['dataset'] == 'tatqa' and row['exposure'] == 'reserved_C3_table'}
    if tagged != reserved or audit['matching_contexts'] != audit['reserved_tables']:
        raise ValueError('C3 table projection differs from the published evaluation exposure')
    by_table = defaultdict(list)
    for row, _, _ in tatqa:
        if row['id'] in reserved:
            by_table[row['report']].append(row['id'])

    def c3_priority(ident):
        return hashlib.sha256(f'tatqa-scale-c3-v1|dev|{ident}'.encode()).hexdigest()

    exact = {min(ids, key=c3_priority) for ids in by_table.values()}
    if len(exact) != audit['reserved_tables']:
        raise ValueError('cannot reconstruct one C3 question per validated official table')
    return [
        {**row, 'exposure': 'reserved_C3_exact' if row['id'] in exact else 'reserved_C3_same_table'}
        if row['dataset'] == 'tatqa' and row['id'] in reserved else row
        for row in labels
    ]


def prepare(sources, exclude_train_ids, fit_size, calibration_size, exposure_path=None, *, allow_train_ids=None,
            tatqa_reserved=None):
    rows = {split: [] for split in ('fit', 'calibration', 'eval')}
    allow_train_ids = allow_train_ids or {}
    summary = {'seed': SEED, 'datasets': {},
               'selection': 'One question per connected source group. Group hashes assign fit or calibration before '
                            'fixed-priority prefix selection, so larger sizes extend each split. '
                            'Official evaluation inventory includes the complete pinned split.'}
    for dataset, (train_path, eval_path) in sources.items():
        train, train_meta = read_source(dataset, train_path, upstream=TRAIN)
        target, target_meta = read_source(dataset, eval_path)
        allowed = allow_train_ids.get(dataset)
        chosen, audit = select_train(dataset, train, target, exclude_train_ids[dataset], fit_size, calibration_size,
                                     allowed_ids=allowed)
        chosen['eval'] = sorted(target, key=lambda row: row[0]['id'])
        for split, selected in chosen.items():
            rows[split].extend(selected)
        summary['datasets'][dataset] = {
            'train': train_meta, 'eval': target_meta,
            'protected_train_ids': len(exclude_train_ids[dataset]),
            'allowed_train_ids': len(allowed) if allowed is not None else None,
            'overlap_audit': audit,
            'partition_questions': {split: len(selected) for split, selected in chosen.items()},
            'partition_strata': {
                split: dict(Counter(stratum for _, _, stratum in selected)) for split, selected in chosen.items()
            },
        }
    exposure = None
    if exposure_path is not None:
        exposure = evaluation_exposure(exposure_path,
                                       {dataset: info['eval'] for dataset, info in summary['datasets'].items()},
                                       rows['eval'])
        if tatqa_reserved is not None:
            exposure = split_tatqa_exposure(exposure, rows['eval'], tatqa_reserved)
        summary['eval_exposure'] = {'rows': len(exposure), 'path': str(exposure_path.resolve()),
                                    'sha256': hashlib.sha256(exposure_path.read_bytes()).hexdigest()}
    return rows, summary, exposure


def write_prepared(output, rows, manifest, exposure):
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    for split, selected in rows.items():
        directory = output / split
        directory.mkdir(mode=0o700)
        with ((directory / 'public.jsonl').open('x', encoding='utf-8', newline='\n') as public_file,
              (directory / 'references.jsonl').open('x', encoding='utf-8', newline='\n') as ref_file):
            for public, qa, _ in selected:
                reference = {'dataset': public['dataset'], 'id': public['id'],
                             'gold': {field: value for field, value in qa.items() if field != 'question'}}
                for stream, record in ((public_file, public), (ref_file, reference)):
                    stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n')
    if exposure is not None:
        (output / 'eval/exposure.json').write_text(json.dumps(exposure, indent=2) + '\n', encoding='utf-8')
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('finqa-train', 'finqa-test', 'tatqa-train', 'tatqa-dev'):
        parser.add_argument(f'--{flag}', type=Path, required=True)
    parser.add_argument('--exclude-train-ids', type=Path,
                        help='Verified public protected membership JSON {"finqa": [IDs], "tatqa": [IDs]}.')
    parser.add_argument('--allow-train-ids', type=Path,
                        help='Certified disjoint train-pool JSON {"finqa": [IDs]}. Omitted datasets are unrestricted.')
    parser.add_argument('--eval-exposure', type=Path, help='Optional full_eval_exposure.json for reporting only')
    parser.add_argument('--tatqa-reserved', type=Path,
                        help='Public C3 table projection for separating exact questions from same-table items')
    parser.add_argument('--fit-size', type=int, default=96, help='Independent TRAIN sources per dataset')
    parser.add_argument('--calibration-size', type=int, default=48, help='Independent TRAIN sources per dataset')
    parser.add_argument('--output', type=Path, help='Fresh output directory')
    parser.add_argument('--dry-run', action='store_true', help='Verify and print the manifest without writing inputs')
    args = parser.parse_args()
    if not args.dry_run and args.output is None:
        parser.error('--output is required unless --dry-run is used')
    if args.tatqa_reserved is not None and args.eval_exposure is None:
        parser.error('--tatqa-reserved also requires --eval-exposure')
    exclusions = exclusion_lists(args.exclude_train_ids)
    allowed = exclusion_lists(args.allow_train_ids)
    if not (exclusions.get('finqa') or allowed.get('finqa')):
        parser.error('provide nonempty verified FinQA IDs in --exclude-train-ids or --allow-train-ids')
    rows, manifest, exposure = prepare(
        {'finqa': (args.finqa_train, args.finqa_test), 'tatqa': (args.tatqa_train, args.tatqa_dev)},
        {dataset: exclusions.get(dataset, set()) for dataset in TRAIN},
        args.fit_size, args.calibration_size, args.eval_exposure, allow_train_ids=allowed,
        tatqa_reserved=args.tatqa_reserved,
    )
    manifest['membership_inputs'] = {
        name: {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        for name, path in [('protected', args.exclude_train_ids), ('allowed', args.allow_train_ids),
                           ('tatqa_c3_public_tables', args.tatqa_reserved)]
        if path is not None
    }
    if not args.dry_run:
        write_prepared(args.output, rows, manifest, exposure)
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
