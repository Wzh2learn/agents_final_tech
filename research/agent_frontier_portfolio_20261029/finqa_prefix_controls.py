"""Compile matched token-contrast controls from executed prefix witnesses.

The caller must independently replay each witness and bind its encoding to the
input data. This module changes only auxiliary contrast membership; it neither
creates positive targets nor declares a prefix without a witness to be wrong.
"""

import copy
import hashlib

BASE_ARM = 'paired_state_branch'
WITNESS_ARM = 'prefix_witness_mask'
RANDOM_ARM = 'prefix_random_mask'


def point_key(point):
    values = tuple(point[k] for k in ('target_position', 'good_token', 'bad_token'))
    if any(type(v) is not int or v < 0 for v in values) or values[1] == values[2]:
        raise ValueError('invalid contrast point')
    return values


def compile_controls(data, diagnosis, *, data_sha256, seed=17):
    """Remove witnessed sites versus the same number of random sites per source.

    Random removal uses a fixed hash order and the same ordinal decisions in
    repair/closure states. Both controls retain the parent's per-source weight;
    the existing loss averages over the retained sites, so no dose is added.
    """
    if diagnosis['data_sha256'] != data_sha256:
        raise ValueError('witnesses belong to a different dataset')
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rows = data['rows']
    groups = data['paired_rows']
    if sorted(i for group in groups for i in group) != list(range(len(rows))):
        raise ValueError('source groups must partition all targets')
    witnessed = {}
    for case in diagnosis['cases']:
        index = case['row_index']
        if type(index) is not int or not 0 <= index < len(rows):
            raise ValueError('witness row is outside the dataset')
        row = rows[index]
        if any(case[k] != row[k] for k in ('pair_id', 'report')):
            raise ValueError('witness source binding differs')
        if case['role'] != row['boundary_role']:
            raise ValueError('witness role differs')
        if not case['correct_continuations'] or not case['wrong_completed_programs']:
            raise ValueError('both a wrong completion and a correct witness are required')
        point = point_key(case['negative_point'])
        existing = [point_key(p) for p in row['edit_contrasts'][BASE_ARM]]
        if point not in existing or point in witnessed.setdefault(index, set()):
            raise ValueError('witness is duplicate or not an existing loss site')
        witnessed[index].add(point)

    output = copy.deepcopy(data)
    stats = dict(original_points=0, witness_retained_points=0,
                 random_retained_points=0, masked_points=0,
                 random_masks_with_witness=0, affected_groups=0,
                 random_choice_groups=0, empty_after_mask_groups=0,
                 different_mask_groups=0)
    details = []
    for group in groups:
        source = [rows[i] for i in group]
        if len({r['pair_id'] for r in source}) != 1:
            raise ValueError('source group mixes experience identities')
        reference = source[0]['edit_contrasts'][BASE_ARM]
        signatures = [(p['good_token'], p['bad_token']) for p in reference]
        masks = []
        for index in group:
            row = rows[index]
            points = row['edit_contrasts'][BASE_ARM]
            if [(p['good_token'], p['bad_token']) for p in points] != signatures:
                raise ValueError('repair and closure decisions are not aligned')
            keys = [point_key(p) for p in points]
            if len(set(keys)) != len(keys):
                raise ValueError('contrast sites must already be deduplicated')
            for position, good, _ in keys:
                if not row['prompt_token_count'] <= position < len(row['labels']):
                    raise ValueError('contrast is outside the completion')
                if row['labels'][position] != good:
                    raise ValueError('contrast is not bound to a positive target')
            masks.append({j for j, key in enumerate(keys) if key in witnessed.get(index, set())})
        if any(mask != masks[0] for mask in masks[1:]):
            raise ValueError('witness masks must match across paired states')
        mask = masks[0]
        pair_id = source[0]['pair_id']
        order = sorted(range(len(reference)), key=lambda j: hashlib.sha256(
            f'prefix-mask-control:{seed}:{pair_id}:{j}'.encode()).digest())
        random_mask = set(order[:len(mask)])
        for index in group:
            points = rows[index]['edit_contrasts'][BASE_ARM]
            kept = [copy.deepcopy(p) for j, p in enumerate(points) if j not in mask]
            random_kept = [copy.deepcopy(p) for j, p in enumerate(points) if j not in random_mask]
            output['rows'][index]['edit_contrasts'] = {
                WITNESS_ARM: kept, RANDOM_ARM: random_kept}
            stats['original_points'] += len(points)
            stats['witness_retained_points'] += len(kept)
            stats['random_retained_points'] += len(random_kept)
            stats['masked_points'] += len(mask)
            stats['random_masks_with_witness'] += len(mask & random_mask)
        if mask:
            stats['affected_groups'] += 1
            stats['random_choice_groups'] += len(reference) > len(mask)
            stats['empty_after_mask_groups'] += len(reference) == len(mask)
            stats['different_mask_groups'] += mask != random_mask
            details.append(dict(pair_id=pair_id, rows=list(group),
                                original_points_per_state=len(reference),
                                witnessed_ordinals=sorted(mask),
                                random_ordinals=sorted(random_mask)))
    if stats['masked_points'] != diagnosis['counts']['total_ambiguous_points']:
        raise ValueError('witness count differs from its frozen diagnosis')
    return output, dict(counts=stats, groups=details, random_seed=seed)
