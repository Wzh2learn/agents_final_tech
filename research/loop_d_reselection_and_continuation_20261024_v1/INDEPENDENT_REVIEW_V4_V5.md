# Independent AI Review V4/V5

Date: 2026-10-24, Asia/Shanghai

Identity: `INDEPENDENT_AI_SCIENTIFIC_REVIEW`, not human gold or blind review.

## Verdict

- Source-role isolation is implemented at `table_uid` and available higher
  source IDs. The evidence remains TAT-QA same-source; it is not cross-benchmark
  independence.
- Ordinary SFT is a strong baseline only on the bounded 24-family panel. The
  ordinary-versus-visible intervals include zero, so the report must not imply
  a population-level superiority claim.
- V4 and V5 support stopping the narrow-task and diversity-weighted error
  repair recipes. They do not disprove all natural-error repair methods.
- C3 has no policy increment. Semantic checking lowers the absolute number of
  accepted wrong outputs but worsens conditional wrong-delivery risk and loses
  correct coverage; denominator repair never applied.
- Ledger arithmetic is correct: 3,495,424 training tokens, 3,396 attempts,
  8,707,353 total tokens, 624 new attempts and 1,340,468 new tokens.

## Responses

1. The source-disjoint manifest and source-role tests are preserved. The
   reviewer could not independently inspect the full manifest from the summary
   alone; this limitation is retained rather than hidden.
2. V4's summary contains 216 confirmation generation attempts and 119,729
   generation tokens. The separate 48 natural-error collection attempts and
   25,444 tokens are recorded in the ledger and total 264/145,173 for V4.
3. The source-disjoint panel is described as frozen and source-disjoint, not
   “fresh” or independent benchmark evidence.
4. C3 is reported as `absolute wrong accepted down, conditional risk up,
   correct coverage down`, not as a beneficial semantic policy.
5. The next experiment is exactly one: continuation from the ordinary
   checkpoint with general-task rehearsal plus a small natural-error correction
   set, evaluated on a new source-role-disjoint family after freezing the split.
