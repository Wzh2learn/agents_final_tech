# Case 3 — auditing a public retrieval evaluation (BEIR), A and B in one case

Date: 2026-10-28. Loop D direct execution. **Model generation calls in this case: 0.**
All numbers below come from `results/BEIR_AUDIT_RESULT_20261028.json` and
`results/BEIR_AB_RESULT_20261028.json`, produced by `code/beir_audit.py` and
`code/beir_audit_ab.py` on the released data.

---

## 1. Why this is an independent system

Paper E's first two cases are a bespoke staged document evaluator and FinRank.
This case audits a different public evaluation system with different mechanics:

- the data are released corpora, queries and relevance judgements, not a pipeline
  we built;
- the metric definitions are the ones the official path uses (`ndcg_cut`,
  `map_cut`, `recall`), not ours;
- the decision under audit is a **leaderboard ordering**, not a single score;
- the perturbation that matters here is a **cutoff and a tie order**, not a
  document-identity rule.

What transfers is the audit discipline, not the mechanism.

## 2. Frozen contract (set before any result was read)

| Element | Value |
|---|---|
| Benchmark | BEIR distribution, official host `public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/` |
| Subsets | `scifact` (5,183 docs, 300 judged test queries, 339 positive pairs) and `nfcorpus` (3,633 docs, 323 judged test queries, 12,334 positive pairs) |
| Splits | `qrels/test.tsv` only; `train`/`dev` untouched |
| Systems | BM25 (k1,b) ∈ {(0.9,0.4), (1.2,0.75), (0.5,0.3), (1.5,0.6)} and TF-IDF cosine, all rebuilt from the released corpus |
| Metrics | trec_eval definitions; k ∈ {10, 100} |
| Uncertainty | query-level bootstrap, 2,000 resamples, seed 20261028 |
| Controls | a duplicate system (identical scores) and a degraded system (top-ranked document pushed below the cutoff) |
| Exposure | this is a first audit of these subsets by this project; no earlier result on them exists to leak into the design |

Metrics are implemented twice: the production implementation and a second
independent statement of the same definition agree on 200 checks per subset with
**0 mismatches**. `pytrec_eval` is not installed on the machine, so the official
binary was not run; that is stated as a limitation, not glossed over.

Dataset licensing: the BEIR distribution ships **no LICENSE file** and its README
states that it does not vouch for a right to use the datasets. This audit
therefore **redistributes no data**: the repository carries code and aggregate
metrics only. Anyone reusing the numbers must obtain the corpora themselves.

## 3. A — does the reported leaderboard survive the audit

### SciFact (mean nDCG@10, 95% query-bootstrap interval)

| System | nDCG@10 | interval | nDCG@100 | Recall@100 |
|---|---|---|---|---|
| BM25 (1.5, 0.6) | 0.6662 | [0.619, 0.713] | 0.6908 | 0.8826 |
| BM25 (1.2, 0.75) | 0.6622 | [0.616, 0.709] | 0.6851 | 0.8826 |
| BM25 (0.9, 0.4) | 0.6611 | [0.614, 0.707] | 0.6858 | 0.8852 |
| BM25 (0.5, 0.3) | 0.6552 | [0.608, 0.701] | 0.6786 | 0.8844 |
| TF-IDF | 0.6329 | [0.586, 0.676] | 0.6602 | 0.8916 |

Only **3 of 10** pairs separate, and all three are BM25 above TF-IDF
(+0.028 to +0.033). No pair of BM25 configurations separates: the printed
internal order rests on 0.001–0.011 with intervals containing zero.

### NFCorpus

| System | nDCG@10 | nDCG@100 | Recall@100 |
|---|---|---|---|
| BM25 (1.5, 0.6) | 0.3090 | 0.2532 | 0.2358 |
| TF-IDF | 0.3065 | 0.2504 | 0.2371 |
| BM25 (1.2, 0.75) | 0.3058 | 0.2518 | 0.2360 |
| BM25 (0.9, 0.4) | 0.3042 | 0.2520 | 0.2367 |
| BM25 (0.5, 0.3) | 0.2994 | 0.2482 | 0.2353 |

**4 of 10** pairs separate, three of them inside the BM25 family. The audit is
therefore not uniformly conservative: it separates when the sample supports it.

### Two protocol choices move the ordering

- **Cutoff**: k=10 and k=100 give **different orderings on both subsets**; on
  NFCorpus TF-IDF moves from 2nd to 4th.
- **Tie order** inside exactly equal scores: **36.5%** of NFCorpus queries get a
  different top-10, while the aggregate moves by **0.0002**. SciFact has no
  exact ties at the cutoff, so its tie gap is exactly 0 — the same protocol is
  stable on one subset and unstable on another.

## 4. B — does the audit change the decision, and in the right places

Three views on the same runs and the same information:

| View | What it adds | Orders asserted (SciFact / NFCorpus) | Duplicate pair | Degraded system |
|---|---|---|---|---|
| B0 official leaderboard | nothing | 15 / 15 | ordered (false positive) | — |
| B1 strong simple rule | recall@100 | 15 / 15 | still ordered | — |
| A audit | paired bootstrap + k + tie sensitivity | **9 / 7** | indistinguishable (correct) | worse (correct) |

Controls:

| Control | Correct verdict | Audit verdict | Value |
|---|---|---|---|
| duplicate of a BM25 system | indistinguishable | indistinguishable | difference 0.0000, interval [0.000, 0.000] |
| degraded (top doc pushed below cutoff) | worse | worse | SciFact +0.480 [0.414, 0.544]; NFCorpus +0.071 [0.052, 0.092] |

The strong simple baseline is not merely neutral, it **misleads**: recall@100
ranks TF-IDF first on both subsets while nDCG@10 ranks it last or second, so
adding a cheap extra number produces a different unsupported ordering rather
than a better one.

### 原判断 → 审计 → 结果 → 代价

| | |
|---|---|
| 原判断 | "BM25(1.5,0.6) > BM25(1.2,0.75) > BM25(0.9,0.4) > BM25(0.5,0.3) > TF-IDF；系统名次可直接引用" |
| 审计发现 | 10 对里只有 3 对（SciFact）/ 4 对（NFCorpus）可分离；BM25 家族内部次序不可分离；k 与并列序都能改变名次；NFCorpus 36.5% 的查询 top-10 随并列序变化而总量只动 0.0002 |
| 结果 | 断言数 15→9 / 15→7；重复系统被判"不可区分"（消除 1 个假阳性）；退化系统仍被判"更差"（保留真阳性）；"BM25 > TF-IDF" 这一条结论保留 |
| 代价 | 4 次指标扫描 + 2,000 次自助重采样，约 8 秒 CPU，**0 次模型生成**；不改变任何原输出 |

## 5. What this case does not establish

- Two subsets of **one** benchmark family: not two benchmarks.
- Lexical, deterministic systems only. Nothing here about dense or generative
  retrieval, and no model-quality claim.
- The instability is a property of the **reporting protocol**, not a defect of
  any retriever.
- The official `pytrec_eval` binary was not executed; equivalence rests on two
  independent re-implementations agreeing 200/200 per subset.
- No claim that these subsets' published numbers are wrong: the audit changes
  what can be concluded from a table, not what any system scored.

## 6. Reproduction

```bash
# data (official host; ~2.8 MB + ~2.4 MB)
curl -sSL -O https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip
curl -sSL -O https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/nfcorpus.zip
unzip -q scifact.zip && unzip -q nfcorpus.zip

python code/beir_audit.py    --data . --out result.json
python code/beir_audit_ab.py --data . --out ab_result.json
```

Data hashes (zip, SHA-256): `scifact 536e14446a0ba56ed1398ab1055f39fe852686ecad24a6306c80c490fa8e0165`,
`nfcorpus efe5be03f8c5b86a5870102d0599d227c8c6e2484328e68c6522560385671b0b`.
