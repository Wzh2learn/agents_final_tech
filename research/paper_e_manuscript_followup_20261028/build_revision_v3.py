"""Create a separately named, evidence-bounded revision of the frozen v2 draft."""
from pathlib import Path

root = Path(__file__).resolve().parent
source = (root / 'paper_e_review_revision_v2.md').read_text(encoding='utf-8')
edits = [
    ('The third case concerns researcher-generated lexical runs and one post-hoc dense comparison, not the published BEIR leaderboard.',
     'The third case concerns researcher-generated lexical runs and post-hoc dense and six-system sensitivity analyses, not the published BEIR leaderboard.'),
    ('Compare matched thresholds and report the measurement surface.',
     'Account for score rescaling and report the active measurement surface.'),
    ('The observed surface consists of mapping and regression artifacts; the primary drop rule compares the original and injected parsing-root scores.',
     'The observed surface consists of mapping and regression artifacts. In the reported comparison, the flat protocol uses the field-hit-rate drop, while the hierarchical expert protocol uses a recursively weighted parsing-root drop; detection is based on those drops under the reported fixed operating points.'),
    ('Thus corresponding thresholds satisfy θ_H = 0.375 θ_F; different fixed operating thresholds can yield different detection rates despite the same ordering.',
     'For these observed scores, corresponding thresholds approximately satisfy θ_H = 0.375 θ_F; applying fixed operating points without corresponding rescaling can yield different detection rates despite the same ordering.'),
    ('Across three seeds the descriptive detection table-run ratio was 219/282, using 119 unique source-table identifiers.',
     'Across three seeds under the flat protocol, the descriptive detection table-run ratio was 219/282 (75/95, 76/97, and 68/90), using 119 unique source-table identifiers.'),
    ('The corrected source-informed identity analysis reproduces 442 hard-negative occurrences in 305 records sharing canonical text identity with a gold passage elsewhere and gold loss in 33 records under the inspected metadata filter.',
     'The corrected, source-informed identity analysis reproduces two known properties: 442 hard-negative occurrences across 305 records share canonical text identity with another record’s gold passage, and the inspected metadata filter loses gold evidence in 33 records.'),
    ('Cutoff choice also affected ordering. For one BM25 configuration on NFCorpus, reversing document-ID tie order changed the ordered top ten for 36.5% of queries and changed the top-ten document set for 25.7%.',
     'Changing cutoff from k=10 to k=100 also affected system ordering. Separately, for one BM25 configuration on NFCorpus at k=10, reversing document-ID tie order changed the ordered top ten for 36.5% of queries and changed top-ten membership for 25.7%.'),
    ('**Post-hoc dense exploration.**', '**Post-hoc dense exploration and six-system sensitivity analysis.**'),
    ('**Post-hoc six-system sensitivity analysis.** We further assessed six retrieval runs, including BGE and five lexical configurations, using the saved query-level outcomes.',
     'To examine multiplicity sensitivity in the combined family, we subsequently assessed six retrieval runs, including BGE and five lexical configurations, using the saved query-level outcomes.'),
    ('**Table 4. Exploratory BGE versus BM25(1.2, 0.75) comparison in the six-system family.**',
     '**Table 4. Exploratory BGE versus BM25(1.2, 0.75) graded nDCG@10 comparison in the six-system family, with 200,000 sign-flip draws per pair.**'),
    ('| Dataset | Queries | Mean difference, BGE minus BM25 | Unadjusted sign-flip p | Holm-adjusted p, 15 pairs |',
     '| Dataset | Queries | Mean graded nDCG@10 difference, BGE minus BM25 | Unadjusted two-sided sign-flip p | Holm-adjusted p, 15 pairs |'),
    ('At α = 0.05, this selected SciFact comparison does not meet the family-adjusted threshold, whereas the NFCorpus comparison does.',
     'Holm step-down adjustment enforces monotonicity over the ordered p-values within each family. At α = 0.05, this selected SciFact comparison does not meet the family-adjusted threshold, whereas the NFCorpus comparison does.'),
]
for before, after in edits:
    assert source.count(before) == 1, (before, source.count(before))
    source = source.replace(before, after)
with (root / 'paper_e_review_revision_v3.md').open('w', encoding='utf-8', newline='\n') as out:
    out.write(source)
print(f'Created v3 with {len(edits)} exact, verified replacements.')
