import json, collections, re
tr = json.load(open('data/research/tatqa_raw_2026/tatqa_dataset_train.json'))
dv = json.load(open('data/research/tatqa_raw_2026/tatqa_dataset_dev.json'))
recs = tr + dv
rc = collections.Counter(); sc = collections.Counter(); at = collections.Counter(); af = collections.Counter()
year = re.compile(r'(19|20)\d{2}')
multi = 0
for x in recs:
    hdr = [str(c) for c in x['table']['table'][0]]
    if len([h for h in hdr if year.search(h)]) >= 2: multi += 1
    for q in x.get('questions', []):
        rc[str(q.get('req_comparison'))] += 1
        sc[str(q.get('scale'))] += 1
        at[str(q.get('answer_type'))] += 1
        af[str(q.get('answer_from'))] += 1
print('records with >=2 year-like header cols:', multi, '/', len(recs))
print('req_comparison values:', rc.most_common())
print('answer_type values:', at.most_common())
print('answer_from values:', af.most_common())
print('scale values (top 12):', sc.most_common(12))