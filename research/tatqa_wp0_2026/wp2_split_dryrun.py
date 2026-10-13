#!/usr/bin/env python3
"""WP-2 split dry-run (DRAFT, not frozen): propose origin roles by an outcome-blind hash rule. No model calls."""
import hashlib
import json
import pathlib

ROOT = pathlib.Path('.').resolve()
man = json.loads((ROOT / 'data/research/tatqa_wp0_2026/origin_manifest.json').read_text(encoding='utf-8'))
items = json.loads((ROOT / 'data/research/tatqa_wp0_2026/candidate_items_v1.json').read_text(encoding='utf-8'))
origins = man['origins']
seed = 'wp2-split-dryrun-20261013'
ranked = sorted(origins, key=lambda o: hashlib.sha256((seed + ':' + o['origin_id']).encode()).hexdigest())

roles = {
    'pilot': [o['origin_id'] for o in ranked[0:8]],
    'pilot_reserve': [o['origin_id'] for o in ranked[8:16]],
    'development': [o['origin_id'] for o in ranked[16:18]],
    'history': [o['origin_id'] for o in ranked[18:22]],
}
multi = {o['origin_id']: len(o['usable_rows']) for o in origins}
items_per_origin = {}
for it in items['items']:
    items_per_origin[it['origin_id']] = items_per_origin.get(it['origin_id'], 0) + 1
all_ids = [x for v in roles.values() for x in v]
checks = {
    'roles_disjoint': len(set(all_ids)) == len(all_ids),
    'pilot_origins_with_ge2_rows': str(sum(1 for x in roles['pilot'] if multi.get(x, 0) >= 2)) + '/8',
    'current_max_items_per_origin': max(items_per_origin.values()) if items_per_origin else 0,
    'item_extension_needed': 'pilot requires 2 items per origin; the current list emits 1 item per origin -> extend the item builder at freeze (176 origins have >=2 usable rows)',
}
receipt = {
    'schema': 'wp2_split_dryrun_v1',
    'status': 'DRAFT_NOT_FROZEN',
    'seed': seed,
    'rule': 'sha256(seed:origin_id) ascending; [0:8]=pilot, [8:16]=pilot_reserve, [16:18]=development, [18:22]=history',
    'counts': {
        'origins_total': len(origins),
        'origins_with_ge2_usable_rows': sum(1 for o in origins if len(o['usable_rows']) >= 2),
        'candidate_items': len(items['items']),
        'distinct_item_origins': len(items_per_origin),
    },
    'roles': roles,
    'checks': checks,
}
out = ROOT / 'data/research/tatqa_wp0_2026/wp2_split_dryrun_receipt.json'
out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps(receipt['counts'], indent=1))
print(json.dumps(receipt['checks'], indent=1))
print('receipt:', out)
