import json, re, collections
recs = json.load(open('data/research/tatqa_raw_2026/tatqa_dataset_train.json')) + \
       json.load(open('data/research/tatqa_raw_2026/tatqa_dataset_dev.json'))
year = re.compile(r'(19|20)\d{2}')
def multi_period(rec):
    hdr = [str(c) for c in rec['table']['table'][0]]
    return len([h for h in hdr if year.search(h)]) >= 2

ok = 0; by_rec = collections.Counter(); pool = []
for r in recs:
    mp = multi_period(r)
    for q in r.get('questions', []):
        if (q.get('req_comparison') is True and q.get('answer_type') == 'arithmetic'
                and q.get('answer_from') == 'table' and str(q.get('scale','')).strip() != '' and mp):
            ok += 1; by_rec[r['table']['uid']] += 1
            if len(pool) < 3:
                pool.append({'uid': r['table']['uid'][:8], 'q': q.get('question','')[:90],
                             'scale': q.get('scale'), 'answer': q.get('answer'),
                             'derivation': q.get('derivation')})
origins_ge2 = [u for u, c in by_rec.items() if c >= 2]
print('eligible questions (comparison+arithmetic+table+scale+multi-period):', ok)
print('distinct origin records containing >=1 such question:', len(by_rec))
print('origin records containing >=2 such questions:', len(origins_ge2))
print('top origin record counts:', by_rec.most_common(5))
for p in pool: print(' sample:', p)