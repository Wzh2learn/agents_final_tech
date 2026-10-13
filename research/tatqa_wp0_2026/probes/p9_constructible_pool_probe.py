import json, re, collections
recs = json.load(open('data/research/tatqa_raw_2026/tatqa_dataset_train.json')) + \
       json.load(open('data/research/tatqa_raw_2026/tatqa_dataset_dev.json'))
year = re.compile(r'(19|20)\d{2}')
unit = re.compile(r'%|\$|¥|£|€|EUR|USD|RMB|CNY|million|thousand|billion|m\b|bn\b', re.I)
num = re.compile(r'^\(?-?[\d,]+(\.\d+)?\)?$')
def clean(v):
    s = str(v).strip().replace(',', '').replace('(', '-').replace(')', '')
    return float(s) if num.match(str(v).strip().replace(',', '')) or re.fullmatch(r'\(?-?[\d,]+(\.\d+)?\)?', str(v).strip()) else None
constructible = []
for r in recs:
    t = r['table']['table']
    if len(t) < 2: continue
    hdr = [str(c) for c in t[0]]
    per = [i for i, h in enumerate(hdr) if year.search(h)]
    if len(per) < 2: continue
    if not any(unit.search(h) for h in hdr): continue
    rows_ok = 0
    for row in t[1:]:
        vals = [clean(row[i]) for i in per if i < len(row)]
        if sum(v is not None for v in vals) >= 2: rows_ok += 1
    if rows_ok >= 1:
        constructible.append((r['table']['uid'], len(per), rows_ok))
print('records satisfying multi-period + unit + >=1 numeric two-period row:', len(constructible))
print('distinct origins (records) available:', len(constructible))
by_row = collections.Counter(min(c, 5) for _, _, c in constructible)
print('rows-ok distribution (capped at 5):', sorted(by_row.items()))
print('records with >=2 usable rows:', sum(1 for _, _, c in constructible if c >= 2))
for uid, p, c in constructible[:5]: print(f'  sample uid={uid[:8]} periods={p} usable_rows={c}')