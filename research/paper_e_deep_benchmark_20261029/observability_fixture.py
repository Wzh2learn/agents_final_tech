"""Exhaustive finite observability fixture. Synthetic only; not an agent run."""
from itertools import product
from collections import Counter

# (world, coarse observation, extra evidence, labelled H). H is a constructed
# ground truth, not a direct proxy for evidence and not claimed as real harm.
rows = [
    ('w1', 'A', 'left', 0), ('w2', 'A', 'left', 0),
    ('w3', 'A', 'right', 1), ('w4', 'B', 'left', 0),
    ('w5', 'B', 'right', 1), ('w6', 'C', 'right', 1),
]

def exhaustive(key):
    values=sorted({key(r) for r in rows})
    errors=[]
    for pred in product([0,1],repeat=len(values)):
        mapping=dict(zip(values,pred))
        errors.append(sum(mapping[key(r)] != r[3] for r in rows))
    fibers={v:Counter(r[3] for r in rows if key(r)==v) for v in values}
    analytical=sum(min(c[0],c[1]) for c in fibers.values())
    assert min(errors)==analytical
    return analytical, len(values), len(errors)

if __name__ == '__main__':
    coarse=exhaustive(lambda r:r[1]); enriched=exhaustive(lambda r:(r[1],r[2]))
    assert coarse == (2,3,8) and enriched == (0,5,32)
    print('SYNTHETIC_ONLY; coarse minimum errors: 2/6; enriched: 0/6')
