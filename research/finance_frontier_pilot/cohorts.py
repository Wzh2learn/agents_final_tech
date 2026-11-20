"""Freeze official FinQA test and TAT-QA arithmetic dev question samples."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import unicodedata


SEED = 'finance-frontier-20261119-v1'
UPSTREAM = {
    'finqa': (
        'test',
        'https://github.com/czyssrs/FinQA/blob/0f16e2867befa6840783e58be38c9efb9229d742/dataset/test.json',
        '831dbfb2e785dbc227f895ce3f24046433467aec67b09db2bd6ac7692a8a30dc',
        1147,
    ),
    'tatqa': (
        'dev',
        'https://github.com/NExTplusplus/TAT-QA',
        '8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5',
        718,
    ),
}


def read_source(dataset, path, *, upstream=UPSTREAM):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    split, url, expected_sha256, expected_items = upstream[dataset]
    if digest != expected_sha256:
        raise ValueError(f'{dataset}: expected canonical {split} snapshot, got SHA-256 {digest}')
    data = json.loads(raw)
    candidates = []
    if dataset == 'finqa':
        for row in data:
            qa = row['qa']
            steps = qa['program'].count('(')
            if steps == 0:
                raise ValueError(f'{row["id"]}: reference lacks a program step')
            candidates.append(({
                'dataset': dataset, 'id': row['id'], 'report': row['filename'],
                'question': qa['question'], 'table': row['table'],
                'pre_text': row['pre_text'], 'post_text': row['post_text'],
            }, qa, 'single' if steps == 1 else 'multi'))
    else:
        for row in data:
            paragraphs = [paragraph['text'] for paragraph in row['paragraphs']]
            for qa in row['questions']:
                if qa['answer_type'] == 'arithmetic':
                    candidates.append(({
                        'dataset': dataset, 'id': qa['uid'], 'report': 'TAT-QA/' + row['table']['uid'],
                        'question': qa['question'], 'table': row['table']['table'],
                        'pre_text': paragraphs, 'post_text': [],
                    }, qa, 'arithmetic'))
    ids = {public['id'] for public, _, _ in candidates}
    if len(ids) != len(candidates) or len(ids) != expected_items:
        raise ValueError(f'{dataset}: expected {expected_items} unique eligible official questions')
    source = {'split': split, 'url': url, 'path': str(path.resolve()), 'sha256': digest,
              'source_records': len(data), 'source_questions': len(ids)}
    return candidates, source


def sample(candidates, size, excluded):
    available = [row for row in candidates if row[0]['id'] not in excluded]
    total = len(available)
    if not 0 < size <= total:
        raise ValueError(f'cannot select {size} questions from {total} eligible questions')
    counts = Counter(stratum for _, _, stratum in available)
    quotas = {name: size * count // total for name, count in counts.items()}
    by_remainder = sorted(counts, key=lambda name: (-(size * counts[name] % total), name))
    for name in by_remainder[:size - sum(quotas.values())]:
        quotas[name] += 1

    def priority(row):
        public = row[0]
        key = '|'.join((SEED, public['dataset'], public['id']))
        return hashlib.sha256(key.encode('utf-8')).digest(), public['id']

    selected = []
    for row in sorted(available, key=priority):
        stratum = row[2]
        if quotas[stratum]:
            selected.append(row)
            quotas[stratum] -= 1
    return selected, counts


def exclusion_lists(path):
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or set(data) - UPSTREAM.keys():
        raise ValueError('exclusions must map dataset names to lists of public question IDs')
    result = {}
    for name, ids in data.items():
        if not isinstance(ids, list) or any(not isinstance(id_, str) or not id_ for id_ in ids):
            raise ValueError(f'{name}: expected a list of public question IDs')
        result[name] = set(ids)
    return result


def table_signature(table):
    rows = [
        [' '.join(unicodedata.normalize('NFKC', str(cell)).casefold().split()) for cell in row]
        for row in table
    ]
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def finqa_train_overlap(candidates, path):
    # Both archived FinQA 64-question panels use official TRAIN. Compare with
    # the public source directly, without opening either archived experiment.
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != '49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6':
        raise ValueError('unexpected FinQA TRAIN snapshot for exclusion audit')
    train = json.loads(raw)
    ids = {row['id'] for row in train}
    reports = {row['filename'] for row in train}
    tables = {table_signature(row['table']) for row in train}
    matching_ids = {row['id'] for row, _, _ in candidates if row['id'] in ids}
    matching_reports = {row['id'] for row, _, _ in candidates if row['report'] in reports}
    matching_tables = {row['id'] for row, _, _ in candidates if table_signature(row['table']) in tables}
    audit = {'train_questions': len(train), 'train_sha256': digest, 'matching_ids': len(matching_ids),
             'matching_reports': len(matching_reports), 'matching_tables': len(matching_tables)}
    return matching_ids | matching_reports | matching_tables, audit


def tatqa_reserved_overlap(candidates, path):
    # Only the pre-outcome table membership, projected from the archived
    # selection metadata, is admitted. No tasks, labels, scores or runs.
    rows = json.loads(path.read_text(encoding='utf-8'))
    if len(rows) != 64 or any(set(row) != {'table_uid', 'table_signature'} for row in rows):
        raise ValueError('expected the 64 table memberships with UID and signature only')
    observed = {row['report'].removeprefix('TAT-QA/'): table_signature(row['table']) for row, _, _ in candidates}
    for row in rows:
        if observed.get(row['table_uid']) != row['table_signature']:
            raise ValueError('sealed TAT-QA table membership disagrees with the pinned official snapshot')
    reserved_uids = {row['table_uid'] for row in rows}
    reserved_content = {row['table_signature'] for row in rows}
    if len(reserved_uids) != 64 or len(reserved_content) != 64:
        raise ValueError('duplicate sealed TAT-QA table membership')
    reserved_reports = {uid for uid, signature in observed.items() if signature in reserved_content}
    excluded = {row['id'] for row, _, _ in candidates if row['report'].removeprefix('TAT-QA/') in reserved_reports}
    return excluded, {'reserved_tables': len(reserved_uids), 'matching_contexts': len(reserved_reports),
                      'matching_questions': len(excluded)}


def freeze(output, finqa, tatqa, size=200, exclusions=None, *, finqa_train=None, tatqa_reserved=None):
    exclusions = exclusion_lists(exclusions)
    public_rows, references = [], []
    manifest = {'seed': SEED, 'size_per_dataset': size, 'datasets': {},
                'sampling': 'SHA-256 of seed|dataset|id within proportional question strata. '
                            'Largest-remainder quotas. No table deduplication or outcome filtering.'}
    for dataset, path in [('finqa', finqa), ('tatqa', tatqa)]:
        candidates, src = read_source(dataset, path)
        excluded = exclusions.get(dataset, set())
        overlap = None
        if dataset == 'finqa' and finqa_train is not None:
            extra, overlap = finqa_train_overlap(candidates, finqa_train)
            excluded |= extra
        if dataset == 'tatqa' and tatqa_reserved is not None:
            extra, overlap = tatqa_reserved_overlap(candidates, tatqa_reserved)
            excluded |= extra
        selected, counts = sample(candidates, size, excluded)
        for public, qa, _ in selected:
            public_rows.append(public)
            references.append({'dataset': dataset, 'id': public['id'],
                               'gold': {name: value for name, value in qa.items() if name != 'question'}})
        manifest['datasets'][dataset] = {
            **src,
            'source_strata': dict(Counter(stratum for _, _, stratum in candidates)),
            'eligible_strata': dict(counts),
            'selected_strata': dict(Counter(stratum for _, _, stratum in selected)),
            'excluded_source_ids': sorted({public['id'] for public, _, _ in candidates} & excluded),
            'overlap_audit': overlap,
            'selected_contexts': len({public['report'] for public, _, _ in selected}),
            'selected_ids': [public['id'] for public, _, _ in selected],
        }
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, rows in [('public.jsonl', public_rows), ('references.jsonl', references)]:
        with (output / name).open('x', encoding='utf-8', newline='\n') as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
    with (output / 'manifest.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--finqa', required=True, type=Path)
    parser.add_argument('--tatqa', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--size', default=200, type=int)
    parser.add_argument('--exclude-ids', type=Path,
                        help='Optional public question-ID exclusions as a JSON object keyed by dataset')
    parser.add_argument('--finqa-train', type=Path, help='Official TRAIN source to exclude cross-split overlap')
    parser.add_argument('--tatqa-reserved', type=Path, help='Pre-outcome table UID and signature projection')
    args = parser.parse_args()
    manifest = freeze(args.output, args.finqa, args.tatqa, args.size, args.exclude_ids,
                      finqa_train=args.finqa_train, tatqa_reserved=args.tatqa_reserved)
    print(json.dumps({name: {key: details[key] for key in ('source_questions', 'selected_strata',
                                                          'selected_contexts', 'overlap_audit')}
                      for name, details in manifest['datasets'].items()}))


if __name__ == '__main__':
    main()
