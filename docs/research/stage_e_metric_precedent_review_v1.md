# Stage E Metric Precedent Review v1

Status: bounded public-metadata review; conclusions use explicit evidence labels.

## 1. Search boundary

`FACT`: this review reuses the frozen local OpenAlex result sets under `/home/testuser/wzh/research_stage_e_d_20261009/sources/openalex/` and bounded official repository/publication metadata. It does not claim systematic-review completeness.

`FACT`: no paid API, model, judge, production service, database, dataset body, or package installation was used.

## 2. Precedent matrix

| Area | Source and revision | What the source supports | What it does not support | Licence status | Label |
|---|---|---|---|---|---|
| Mutation testing | Jia and Harman, *An Analysis and Survey of the Development of Mutation Testing*, September 2011, [DOI](https://doi.org/10.1109/TSE.2010.62) | Detection/kill metrics depend on mutant validity and equivalent-mutant handling | Stage E checkpoint visibility formula | IEEE license terms | `FACT` metadata; `INFERENCE` denominator analogy |
| Fault localization | Abreu et al., *On the Accuracy of Spectrum-based Fault Localization*, September 2007, [DOI](https://doi.org/10.1109/TAIC.PART.2007.13) | Localization/ranking accuracy is distinct from detection | A claim that `13/118` measures general localization superiority | Publisher terms | `FACT` metadata; `INFERENCE` construct separation |
| AI measurement governance | NIST AI 100-1, January 2023, [DOI](https://doi.org/10.6028/NIST.AI.100-1) | MEASURE 2.13 evaluates effectiveness of TEVV metrics; MEASURE 3.2 addresses unavailable/difficult metrics | Project-specific metric names or thresholds | NIST technical-series statement | `FACT` source wording |
| Generative-AI measurement | NIST AI 600-1, July 2024, [PDF](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) | Lifecycle and deployment measurement documentation; TEVV metric effectiveness | Stage E equivalence or harmfulness definitions | NIST technical-series statement | `FACT` source wording |
| Process supervision | Lightman et al., *Let's Verify Step by Step*, arXiv published 2023-05-31, [repo](https://github.com/openai/prm800k) at `7ecc794...` | Step-level labels are separate from final outcome | Correctness of Stage E synthetic labels | Repository MIT; data-specific licence `UNVERIFIED` | `FACT`; `UNVERIFIED` data licence |
| Automated process supervision | Wang et al., Math-Shepherd, arXiv v3 2024-02-19 / ACL 2024, [ACL](https://aclanthology.org/2024.acl-long.510/) | Automated prefix-to-outcome process labels using hard/soft continuation estimates | An official released data schema or Stage E label transfer | Paper licence and dataset licence `UNVERIFIED` | `FACT` paper; `UNVERIFIED` repository/data |
| Observability practice | Local OpenAlex discovery records in `observability_metrics.json` | The literature often correlates logs, metrics, and traces or diagnoses failures | A standardized “checkpoint visibility” metric | Mixed/unverified across records | `FACT` search record; `UNVERIFIED` normative standard |

## 3. Precedent verdict

`INFERENCE`: the closest precedents support four methodological obligations:

1. validity-gate the denominator before scoring;
2. separate detection from localization;
3. evaluate the effectiveness of the measurement process itself;
4. expose operating-point sensitivity rather than report one threshold only.

`FACT`: none of the inspected sources supplies the exact combination used here—absorption-based `visible_frozen`, per-family visibility profiles, gamma-conditioned visibility, visibility-by-detection cells, and matched-FPR protocol differences.

`INFERENCE`: Stage E should therefore call the battery **project-defined observability metrics**, with adjacent literature used for rationale rather than authority.

`VALUE`: preserve the narrow precedent claim because it protects the project-specific derivation from being presented as a recognized external standard.

## 4. Exact blockers

`UNVERIFIED`:

- No full IEEE text was downloaded for the two metric-precedent papers; conclusions rely on official bibliographic metadata plus bounded abstract/domain knowledge and must not be quoted as text.
- No canonical open observability standard defining checkpoint visibility was identified.
- No official Math-Shepherd repository, released dataset card, schema, or licence was established.
- No dataset-specific licence for PRM800K was established beyond the repository's root MIT text.

## 5. Source receipt

`FACT`: exact URLs, revisions, licences, schema evidence, and blockers are recorded in [`source_audit_v1.json`](../../research/stage_e_stage_d_20261009/source_audit_v1.json).
