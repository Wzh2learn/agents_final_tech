import json, re, collections
recs = json.load(open('data/research/tatqa_raw_2026/tatqa_dataset_train.json')) + \
       json.load(open('data/research/tatqa_raw_2026/tatqa_dataset_dev.json'))
year = re.compile(r'(19|20)\d{2}')
def mp(rec):
    hdr = [str(c) for c in rec['table']['table'][0]]
    return len([h for h in hdr if year.search(h)]) >= 2
c1=c2=c3=c4=c5=0
types = collections.Counter()
for r in recs:
    m = mp(r)
    for q in r.get('questions', []):
        if q.get('req_comparison') is True:
            c1 += 1
            types['answer_type:' + str(q.get('answer_type'))] += 1
            types['answer_from:' + str(q.get('answer_from'))] += 1
            types['scale_type:' + type(q.get('scale')).__name__ + ':' + str(q.get('scale'))[:12]] += 1
            if q.get('answer_type') == 'arithmetic':
                c2 += 1
                if q.get('answer_from') == 'table':
                    c3 += 1
                    if str(q.get('scale','')).strip() != '':
                        c4 += 1
                        if m: c5 += 1
print('1) req_comparison True:', c1)
print('2) + arithmetic      :', c2)
print('3) + answer_from table:', c3)
print('4) + scale non-empty  :', c4)
print('5) + multi-period rec :', c5)
print()
for k, v in types.most_common(12): print(f'  {v:>5}  {k}')