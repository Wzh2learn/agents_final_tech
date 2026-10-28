"""Re-score persisted, fixed dense and lexical rankings with trec_eval."""
import csv, json, subprocess, tempfile
from pathlib import Path
DATA = Path('/home/testuser/wzh/beir_audit/clean/data')
TEMP = Path('/tmp/papere_conference_short_20261028')
EXE = '/home/testuser/wzh/beir_audit/trec_eval-main/trec_eval'
obj = json.loads((TEMP/'dense_probe.json').read_text())
max_diff = 0.0; count = 0
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    for name, ds in obj['datasets'].items():
        with open(DATA/name/'qrels/test.tsv', encoding='utf8') as inp, open(td/'qrels','w',encoding='utf8') as out:
            for r in csv.DictReader(inp, delimiter='\t'):
                out.write(f"{r['query-id']} 0 {r['corpus-id']} {r['score']}\n")
        for key in ('dense','bm25'):
            with open(td/'run','w',encoding='utf8') as out:
                for r in ds['rows']:
                    for i, docid in enumerate(r[key+'_top100']):
                        out.write(f"{r['qid']} Q0 {docid} {i+1} {100-i} run\n")
            result = subprocess.check_output([EXE,'-q','-m','ndcg_cut.10',str(td/'qrels'),str(td/'run')],text=True)
            values = {p[1]:float(p[2]) for line in result.splitlines() if len(p:=line.split()) == 3 and p[1] != 'all'}
            assert len(values) == len(ds['rows'])
            for r in ds['rows']:
                diff = abs(values[r['qid']] - r[key+'_ndcg10'])
                max_diff = max(max_diff,diff); count += 1
                assert diff <= 0.000051, (name,key,r['qid'],diff)
print(json.dumps({'measure':'ndcg_cut.10','values_checked':count,'max_deviation':max_diff,
                  'tolerance':0.000051, 'status':'PASS', 'scope':'given fixed top-100 rankings; not tie policy'}))
