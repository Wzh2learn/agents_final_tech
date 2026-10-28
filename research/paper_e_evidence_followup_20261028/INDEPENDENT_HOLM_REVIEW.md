# Independent arithmetic review of the Holm adjustment

Reviewed 2026-10-28 using `mc_recheck.json`, its saved exceedance counts and the 15 comparisons per dataset. This is a numerical and code-contract review, not a rerun of retrieval, qrels or `trec_eval` and not an independent dataset.

For SciFact, the BGE vs BM25(1.2, 0.75) comparison ranks sixth by unadjusted p. Its plus-one Monte Carlo p is 1282/200001 = 0.006409967950; multiplying by its step-down factor 10 gives 0.0640996795. The fifth comparison, BGE vs BM25(0.9, 0.4), has p = 1200/200001 = 0.0059999700; multiplying by 11 gives 0.0659996700. The Holm adjusted value takes the running maximum of all preceding factors and so is 0.0659996700, displayed as 0.066000.

For NFCorpus the target comparison ranks fourth; its value is 259/200001 multiplied by 12 = 0.0155399223. Recomputing plus-one p values and the Holm monotonic recursion from the recorded counts matched all 30 saved comparisons.

Inference still assumes an appropriate paired sign-flip null (within-query exchangeability under the sharp null or suitable symmetry of paired differences) and query independence. Corrections are per dataset and metric family, not across datasets or metric conditions. These choices and the family were constructed after earlier results were known. A non-significant result does not establish equality or show an actual person changed a decision. Numerical review does not verify dataset provenance or scientific generalization.
