# NIST Measurement Validity Evidence Ledger v2

> 状态: 活跃 | 更新: 2026-10-09 | 取代/被取代: 加强 `nist_tevv_background_evidence_v1.md` 的 exact-source ledger；不改变 Stage E methods

## 1. Sources

- NIST AI 100-1, AI RMF 1.0, January 2023, `https://doi.org/10.6028/NIST.AI.100-1`.
- NIST AI 600-1, Generative AI Profile, July 2024, `https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf`.
- NIST AI 200-2 IPD, TEVV-Athlon, initial public draft announced 2026-08-07, comment period through 2026-10-06, `https://doi.org/10.6028/NIST.AI.200-2.ipd`.

## 2. Exact evidence

| Document | Exact short passage | SOURCE CLAIM | OUR INFERENCE | PAPER USE | NOT SUPPORTED |
|---|---|---|---|---|---|
| AI 100-1 | “objective, repeatable, or scalable ... TEVV processes including metrics, methods, and methodologies are in place, followed, and documented” | TEVV should be documented and repeatable | Measurement objects and rules must be explicit | Methods framing | Does not define checkpoint visibility |
| AI 100-1 | “The degree to which each measurement type provides unique and meaningful information ... should be considered” | Different measurement types require utility review | Visibility/detection/harmfulness should remain separate | Construct separation | Does not prescribe our formulas |
| AI 100-1 MEASURE 1.1 | “risks ... that will not – or cannot – be measured are properly documented” | Unmeasurable risks must be documented | Blindness and unresolved HBR require explicit missingness | Limitations | Does not validate a blind-spot metric |
| AI 100-1 MEASURE 1.2 | “Appropriateness of AI metrics and effectiveness of existing controls are regularly assessed and updated” | Metrics and controls require recurring assessment | Threshold/protocol sensitivity and calibration defects must be disclosed | Motivation anchor | Does not certify our metric validity |
| AI 100-1 MEASURE 1.3 | “independent assessors are involved in regular assessments and updates” | Independent assessment is expected | Loop C/second implementation matter | Governance framing | Not proof our evaluator is independently validated |
| AI 100-1 MEASURE 2.1 | “Test sets, metrics, and details about the tools used during TEVV are documented” | Test sets and tools must be documented | Hashes, denominators and scripts belong in the evidence chain | Reproducibility | No exact schema required |
| AI 100-1 MEASURE 2.13 | “Effectiveness of the employed TEVV metrics and processes ... are evaluated and documented” | TEVV effectiveness is itself measured | Evaluation protocols need meta-evaluation | Core motivation | Does not propose evaluator blind spots |
| AI 600-1 MS-2.13-001 | “demonstrate construct validity for each metric ... biases or statistical variance ... documented” | Construct validity and uncertainty should be modeled | Report estimand-specific uncertainty | Metric design | No universal interval method |
| AI 600-1 MEASURE 4.2 | “real-world scenarios ... reveal issues that might not surface in controlled and optimized testing environments” | Deployment context may reveal hidden issues | External dataflow is future validity evidence | Future work | No current transfer result |
| AI 200-2 IPD | “Input Sought on Initial Public Draft ... through October 6, 2026” | Draft status and active comment period | Use only as 2026 background | Related context | Not a stable method authority |

## 3. Motivation anchor

`VALUE`: recommended anchor:

> NIST asks whether AI metrics and TEVV processes are appropriate and effective. Our work asks a narrower measurement question: can the evaluation protocol observe the controlled failure modes it is supposed to assess?

`FORBIDDEN`: “NIST proposes evaluator blind spots.”

## 4. ITIL boundary

ITIL remains one Introduction/Motivation paragraph for service lifecycle, governance, continual improvement, oversight and accountability. The three advisor phrases remain `OUR MOTIVATION ONLY`. ITIL is not a method contribution or authority for Stage E metrics.
