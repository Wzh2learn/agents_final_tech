"""Intentionally different LRU negative control for offline verifier qualification.

This is not the specified S3FIFO policy, a skill-using agent or a strong
baseline. It uses only the task-provided trace and cache capacity.
"""
import collections
import json

with open('/root/config.json', encoding='utf8') as f:
    cfg = json.load(f)
resident = collections.OrderedDict()
capacity = cfg['cache_capacity_blocks']
size = cfg['block_size']
rows = []
with open('/root/trace.jsonl', encoding='utf8') as f:
    for idx, line in enumerate(f):
        item = json.loads(line)
        hashes = item['hash_ids']
        prefix = 0
        for h in hashes:
            if h not in resident:
                break
            prefix += 1
        rows.append({'idx': idx, 'prompt_tokens': item['input_length'],
                     'hit_tokens': min(prefix * size, item['input_length'])})
        for h in hashes:
            if h in resident:
                resident.move_to_end(h)
            else:
                if len(resident) >= capacity:
                    resident.popitem(last=False)
                resident[h] = True
prompt = sum(r['prompt_tokens'] for r in rows)
hit = sum(r['hit_tokens'] for r in rows)
out = {'total_requests': len(rows), 'total_prompt_tokens': prompt,
       'total_hit_tokens': hit, 'overall_hit_rate': hit / prompt,
       'final_cache_blocks': len(resident), 'per_request': rows}
with open('/root/report.json', 'w', encoding='utf8') as f:
    json.dump(out, f)
print('LRU_DIAGNOSTIC', len(rows), f"{hit / prompt:.6f}", len(resident))
