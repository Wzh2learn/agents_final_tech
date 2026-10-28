"""Post-hoc fixed-source dense/lexical BEIR exploration; writes per-query runs.

No tuning or test-derived instruction is used. This is not preregistered.
Run from the repository root with existing GB10 data and cached model.
"""
from pathlib import Path
import hashlib, json, os, sys, time
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent
default_code = ROOT.parents[2] / 'paper_e_public_eval_20261028' / 'code' if len(ROOT.parents) > 2 else ROOT
sys.path.insert(0, os.environ.get('BEIR_AUDIT_CODE', str(default_code)))
import beir_audit as audit

DATA = Path('/home/testuser/wzh/beir_audit/clean/data')
MODEL = Path('/home/testuser/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5/snapshots/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a')
OUT = Path('/tmp/papere_conference_short_20261028/dense_probe.json')
assert MODEL.is_dir()
audit.self_test()
t0 = time.time()
model = SentenceTransformer(str(MODEL), device='cuda' if torch.cuda.is_available() else 'cpu', local_files_only=True)
model.max_seq_length = 512
result = {'status': 'POSTHOC_DEVELOPMENT', 'model': 'BAAI/bge-small-en-v1.5',
          'revision': MODEL.name, 'model_weights_sha256': hashlib.sha256((MODEL / 'model.safetensors').read_bytes()).hexdigest(),
          'query_prefix': 'Represent this sentence for searching relevant passages: ',
          'max_sequence_length': 512, 'software': {'torch': torch.__version__}, 'datasets': {}}
for name in ('scifact', 'nfcorpus'):
    d = DATA / name
    corpus_list = list(audit.read_jsonl(str(d / 'corpus.jsonl')))
    corpus = {x['_id']: x for x in corpus_list}
    qrels = audit.read_qrels(str(d / 'qrels/test.tsv'))
    queries = [x for x in audit.read_jsonl(str(d / 'queries.jsonl')) if x['_id'] in qrels]
    ids = list(corpus)
    docs = [' '.join((corpus[k].get('title') or '', corpus[k].get('text') or '')).strip() for k in ids]
    emb = model.encode(docs, batch_size=64, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=True)
    qemb = model.encode([result['query_prefix'] + q['text'] for q in queries], batch_size=64, convert_to_numpy=True, normalize_embeddings=True)
    baseline = audit.BM25(corpus, 1.2, 0.75)
    rows = []
    for i, q in enumerate(queries):
        qid = q['_id']; relevance = qrels[qid]
        dense = audit.rank(emb @ qemb[i], ids, 'id_asc', 100)
        lexical = audit.rank(baseline.scores(q['text']), ids, 'id_asc', 100)
        rows.append({'qid': qid, 'dense_top100': dense, 'bm25_top100': lexical,
                     'dense_ndcg10': audit.ndcg_cut(dense, relevance, 10),
                     'bm25_ndcg10': audit.ndcg_cut(lexical, relevance, 10)})
    diffs = np.array([r['dense_ndcg10'] - r['bm25_ndcg10'] for r in rows])
    rng = np.random.default_rng(20261028)
    boot = np.mean(diffs[rng.integers(0, len(diffs), size=(2000, len(diffs)))], axis=1)
    result['datasets'][name] = {'corpus_count': len(corpus), 'judged_queries': len(rows),
       'input_sha256': {str(p.relative_to(d)): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in (d/'corpus.jsonl',d/'queries.jsonl',d/'qrels/test.tsv')},
       'dense_mean_ndcg10': float(np.mean([r['dense_ndcg10'] for r in rows])),
       'bm25_mean_ndcg10': float(np.mean([r['bm25_ndcg10'] for r in rows])),
       'paired_delta': float(np.mean(diffs)), 'bootstrap_95': np.percentile(boot, [2.5,97.5]).tolist(), 'rows': rows}
result['elapsed_seconds'] = time.time() - t0
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
print('wrote', OUT, 'elapsed', result['elapsed_seconds'])
