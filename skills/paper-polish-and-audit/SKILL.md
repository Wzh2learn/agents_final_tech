---
name: paper-polish-and-audit
description: |
  Pre-submission final audit for a research paper. Reviews the manuscript from a first-time
  reviewer's perspective with configurable project-specific rules (terminology lock, 
  claim verification, compilation check). Use when you have a complete draft and are 
  preparing to submit. Triggers: 论文终审, 投稿前检查, review my paper, 帮我审查论文.
when_to_use: paper draft is "done" and submission deadline is approaching, final quality gate before submit
---

# Paper Pre-Submission Audit

A final audit wrapper that applies systematic review methodology before submission.

## Audit Checklist

### 1. Terminology consistency
- [ ] All key terms are used consistently throughout (no synonym drift)
- [ ] Acronyms defined on first use, then used consistently
- [ ] Method component names match between text, figures, and tables
- [ ] Related work section uses the same terms as the rest of the paper

### 2. Claim verification (Red Lines)
- [ ] Every quantitative claim has a corresponding table/figure entry
- [ ] No stale numbers from earlier experimental runs
- [ ] "Significant improvement" claims backed by statistical tests or clear margins
- [ ] No over-claims: "state-of-the-art" only if truly compared against all relevant baselines
- [ ] Computational cost claims (e.g., "same training budget") are verifiable

### 3. Compilation and formatting
- [ ] All `\cite{}` keys resolve (no "??" in PDF)
- [ ] All `\ref{}` labels resolve
- [ ] No unbalanced braces or encoding errors
- [ ] Figures and tables are referenced in text and appear near their first reference
- [ ] Page limit respected (including references/appendix per venue rules)

### 4. Cross-version sync (if applicable)
- [ ] LaTeX source ↔ any backup/translated versions are consistent in core content
- [ ] Abstract matches the body's actual contributions (abstracts often lag behind rewrites)
- [ ] Conclusion's claimed contributions match what's actually in the paper

### 5. Reviewer perspective check
- [ ] Motivation is clear in the first paragraph (why should anyone care?)
- [ ] The gap between related work and your contribution is explicitly stated
- [ ] Experimental setup is reproducible from the text alone
- [ ] Limitations section exists and is honest
- [ ] Figures are readable at print size (not just on a large monitor)

### 6. AI writing pattern removal
- [ ] No "delve into", "it is important to note that", "in conclusion"
- [ ] No redundant hedging ("it can be argued that perhaps")
- [ ] Active voice preferred over passive
- [ ] Specific claims preferred over vague qualifiers

## Process
1. Run through the checklist above, section by section
2. For each issue found, note: location, severity (blocks submission / should fix / nice-to-have)
3. Fix blockers first, then should-fix items
4. Re-read the abstract and introduction last (they suffer most from edit drift)

## Related skills
- General review methodology: use `paper-review` skill for Layer 1 (self-audit)
- AI pattern removal: use `paper-polish` skill for systematic language cleanup
- Full paper pipeline: use `research-paper-pipeline` skill for end-to-end writing
