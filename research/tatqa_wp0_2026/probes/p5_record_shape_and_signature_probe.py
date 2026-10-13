import json, collections, hashlib
tr = json.load(open('data/research/tatqa_raw_2026/tatqa_dataset_train.json'))
dv = json.load(open('data/research/tatqa_raw_2026/tatqa_dataset_dev.json'))
print('train records:', len(tr), '| dev records:', len(dv))
r = tr[0]
print('record keys:', sorted(r.keys()))
print('table keys:', sorted(r['table'].keys()))
print('table.uid:', r['table']['uid'][:12])
print('paragraphs:', len(r['paragraphs']), '| first para keys:', sorted(r['paragraphs'][0].keys()))
print('para uid match table uid?', r['paragraphs'][0].get('uid') == r['table']['uid'])
print('questions:', len(r.get('questions', [])), '| first q keys:', sorted(r['questions'][0].keys()) if r.get('questions') else None)
# do paragraphs repeat across records (same report)?
sig = collections.Counter()
for x in tr+dv:
    h = hashlib.sha256(' '.join(p.get('text','') for p in x.get('paragraphs',[])).encode()).hexdigest()[:16]
    sig[h] += 1
print('distinct paragraph-set signatures:', len(sig), '| appearing >1:', sum(1 for v in sig.values() if v>1))
print('largest group:', sig.most_common(3))
# question/answer structure for a two-period task
q = r['questions'][0]
print('question text sample:', q.get('question','')[:120])
print('answer sample:', json.dumps(q.get('answer',{}))[:160])