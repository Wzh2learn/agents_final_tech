# Case 3 — auditing a public retrieval evaluation (BEIR), corrected

Date: 2026-10-28 (revision 3). Loop D direct execution. **Model generation calls: 0.**
Supersedes `results/v1_uncorrected/`. The old JSONs are kept unchanged for comparison.

---

## 0. What the first version got wrong

| # | Defect | Consequence | Status |
|---|---|---|---|
| 1 | nDCG binarised relevance | trec_eval `ndcg_cut` takes the **raw qrels grade** as gain. Counter-example rels [1,2], ranking [1,2]: binary gives 1.0, official 0.8597188 | fixed; self-test pins it |
| 2 | MAP divided by `min(n_rel, K)` | trec_eval `map_cut.K` divides by **total n_rel**. Two relevant, K=1, first hit: old 1.0, official 0.5 | fixed; self-test pins it |
| 3 | Control pairing reversed | `truth_diff` held (degraded, other) while assertions were (other, degraded), so `true_different_flagged` was 0 in every view | fixed; base/degraded paired explicitly, direction checked |
| 4 | Naive leaderboard as strawman | B0's stable sort forced an order between equal duplicates; that "false positive" was an artefact of the naive sort | fixed; a point-estimate baseline that respects exact equality added |
| 5 | recall@100 called a "strong simple baseline" | it changes the ranking target, so it is not the same task | removed from B1; kept only as a separate multi-target sensitivity |
| 6 | CI containing 0 read as equality | "not distinguished" ≠ "proved equal" | wording corrected throughout |
| 7 | No multiplicity control | 10 pairs at 95% expects ~0.5 spurious orders | Holm-adjusted permutation p-values added |
| 8 | `flip@10` compared ordered lists | 36.5% mixed reordering with genuine membership change | split into order / member-set / boundary-tie rates |
| 9 | CLI in the note did not match the script | could not be replayed as written | both scripts now take `--data/--out`; replayed from a clean directory |
| 10 | "200/200 self-consistency" implied official equivalence | two implementations of the same assumption | reworded: equivalence to the published definition; `pytrec_eval` was not run |

## 1. Frozen contract (unchanged except where noted)

| Element | Value |
|---|---|
| Benchmark | BEIR official distribution, `public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/` |
| Subsets | `scifact` 5,183 docs / 300 judged test queries / 339 positive pairs / **all grades 1**; `nfcorpus` 3,633 docs / 323 queries / 12,334 positive pairs / **grades 1 (11,758) and 2 (576)** |
| Splits | `qrels/test.tsv` only |
| Systems | BM25 (0.9,0.4), (1.2,0.75), (0.5,0.3), (1.5,0.6); TF-IDF cosine — all rebuilt from the released corpus, no model |
| Metrics | trec_eval `ndcg_cut` (graded gain), `map_cut.K` (denominator n_rel), `recall.K`; k ∈ {10,100}; binary-gain nDCG reported alongside |
| Uncertainty | query-level bootstrap, 2,000 resamples (uncorrected intervals); paired sign-flip permutation with **Holm** over the 10 pairs (corrected). The two are reported separately; an interval containing 0 means *not excluded*, not *proved equal* |
| Controls | exact duplicate (correct verdict: indistinguishable) and top-document degradation (correct verdict: worse), each checked for direction |
| Query/corpus id overlap | 0 on both subsets, so BEIR's `ignore_identical_ids` default cannot bind |

**Provenance of the freeze claim.** No independent timestamped pre-registration exists
for this contract; it was written after the first BEIR run had already been seen.
It is therefore **post-hoc / developmental**, not pre-registered. The corrections
below were made because the definitions were wrong, not because the results were
unwelcome: two of them make the audit's story *weaker*.

## 2. A — what the corrected metric does to the numbers

### SciFact: no change, because the qrels are binary

| System | nDCG@10 (old) | nDCG@10 (new, graded) | binary | MAP@10 |
|---|---|---|---|---|
| BM25 (1.5, 0.6) | 0.6662 | 0.6662 | 0.6662 | 0.6246 |
| BM25 (1.2, 0.75) | 0.6622 | 0.6622 | 0.6622 | 0.6174 |
| BM25 (0.9, 0.4) | 0.6611 | 0.6611 | 0.6611 | 0.6180 |
| BM25 (0.5, 0.3) | 0.6552 | 0.6552 | 0.6552 | 0.6099 |
| TF-IDF | 0.6329 | 0.6329 | 0.6329 | 0.5796 |

### NFCorpus: the correction reorders the table and halves MAP

| System | nDCG@10 (old) | nDCG@10 (new) | binary | MAP@10 (old) | MAP@10 (new) |
|---|---|---|---|---|---|
| BM25 (1.5, 0.6) | 0.3090 | **0.3092** | 0.3090 | 0.2225 | **0.1193** |
| BM25 (1.2, 0.75) | 0.3058 | **0.3062** | 0.3058 | 0.2201 | 0.1175 |
| TF-IDF | 0.3065 | **0.3052** | 0.3065 | 0.2200 | 0.1162 |
| BM25 (0.9, 0.4) | 0.3042 | **0.3045** | 0.3042 | 0.2203 | 0.1180 |
| BM25 (0.5, 0.3) | 0.2994 | **0.3011** | 0.2994 | 0.2162 | 0.1159 |

**The ranking changes**: TF-IDF drops from 2nd to 3rd, behind BM25(1.2, 0.75).
MAP@10 roughly halves because the denominator is the number of relevant documents
(mean ≈ 38 per query on NFCorpus), not the cutoff.

### Support after multiplicity control

| | SciFact | NFCorpus |
|---|---|---|
| pairs with CI excluding 0 (uncorrected) | 3 / 10 | 4 / 10 |
| pairs surviving **Holm** (p < 0.05) | **2 / 10** | **1 / 10** |
| which | BM25(1.5) > TF-IDF (+0.033), BM25(1.2) > TF-IDF (+0.029) | BM25(1.5) > BM25(0.5) (+0.0082) |
| dropped by correction | BM25(0.9) > TF-IDF (p_holm = 0.14) | three pairs, p_holm ≥ 0.22 |

### Tie order, counted three ways (NFCorpus; SciFact is 0 on all three)

| Measure | Rate |
|---|---|
| top-10 differs as an **ordered list** | 36.5% |
| top-10 differs as a **member set** | **25.7%** |
| a tie sits exactly at the **10/11 boundary** | 25.7% |
| aggregate nDCG@10 movement | **0.0000485** (0.30453945 vs 0.30449093; four decimals print as 0.0000, which is not zero) |

Local instability in a quarter of queries, invisible in the headline number.

## 3. B — the before/after comparison, corrected

Three views on the same target (mean graded nDCG@10) and the same information:

| View | Asserted orders (SciFact / NFCorpus) | Duplicate control | Degradation control |
|---|---|---|---|
| B0 naive leaderboard (orders even equal means) | 15 / 15 | **fails** (asserts an order on an exact duplicate) | passes |
| B1 point estimate (equal means = tie) | **14 / 14** | **passes** | **passes** |
| A audit (paired bootstrap CI excludes 0) | 9 / 7 | passes | passes |
| A with Holm | 7 / 5 | passes | passes |

**The audit's advantage over a careful simple baseline is not demonstrated.** B1 is
one line of code, uses no resampling, and already passes both constructed controls.
The earlier claim that the audit "removes a false positive" described a defect of the
naive sort, not a property of the audit.

What the audit still contributes is narrower: it withdraws five further orders on
SciFact and seven on NFCorpus, and it states the leaderboard's support as one or two
orderings rather than ten. **Withdrawal is not refutation**: those pairs are *not
distinguished*, which is not the same as *shown equal*.

Controls, with direction verified:

| Control | Correct verdict | Observed |
|---|---|---|
| exact duplicate of BM25(0.9,0.4) | indistinguishable | difference 0.0000, interval [0.000, 0.000] |
| top document pushed below the cutoff | base worse | SciFact +0.480 [0.414, 0.544]; NFCorpus +0.071 [0.052, 0.092] |

### 原判断 → 审计 → 结果 → 代价

| | |
|---|---|
| 原判断（修正前稿） | nDCG@10 上 5 个系统可完全排序；审计消除 1 个假阳性、检出 1 个退化 |
| 修正后 | 该"假阳性"是朴素排序的产物；会处理相等的点估计同样通过两个对照。真正成立的只有：SciFact 2/10、NFCorpus 1/10 对可分离 |
| 结果 | 结论收窄：审计把"排序"变成"支持度陈述"，不纠正错误答案；并列序使 25.7% 查询的前十成员改变而总量不动 |
| 代价 | 4 次指标扫描 + 自助 + 置换检验，< 10 秒 CPU，**0 次生成** |

## 4. What still does not hold

- Two subsets of **one** benchmark family; not two benchmarks.
- Lexical deterministic systems only; nothing about dense or generative retrieval,
  and no model-quality claim.
- `pytrec_eval` was not executed, **but the official `trec_eval` binary was**:
  version 10.0-rc3, built from the upstream source. 18,690 per-query values
  (both subsets, five systems, k=10/100) agree to the binary's four-decimal
  printed precision; maximum deviation 5.0e-05, which is half of the last
  printed digit. Scope: it validates the metric definitions *given a ranking*,
  not the audit's tie-breaking.
- The freeze claim is post-hoc. No independent timestamped pre-registration exists.
- No claim that any published BEIR number is wrong: this audits what a table
  supports, not what a system scored.

## 5. Reproduction (from a clean directory)

```bash
curl -sSL -O https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip
curl -sSL -O https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/nfcorpus.zip
unzip -q scifact.zip && unzip -q nfcorpus.zip
python code/beir_audit.py    --data . --out result.json      # self-tests run first
python code/beir_audit_ab.py --data . --out ab_result.json

# official per-query cross-check (needs the trec_eval binary built from source)
python code/official_crosscheck.py --data . --trec_eval /path/to/trec_eval --out official.json
```

Data (zip SHA-256): `scifact 536e14446a0ba56ed1398ab1055f39fe852686ecad24a6306c80c490fa8e0165`,
`nfcorpus efe5be03f8c5b86a5870102d0599d227c8c6e2484328e68c6522560385671b0b`.
Licensing: the BEIR distribution ships no LICENSE and disclaims licensing; this
repository redistributes **no data**, only code and aggregate metrics.
