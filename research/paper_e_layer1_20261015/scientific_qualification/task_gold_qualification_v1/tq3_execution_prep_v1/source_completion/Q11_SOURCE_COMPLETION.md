# Q11 Source Completion - BCE 2019 Q4 Supplementary Information

> Status: `REFERENCE_SOURCE_COMPLETION = RETRIEVAL_BLOCKED`
> Date: 2026-10-16 (Asia/Shanghai)
> Actor: Loop D (AI). No model calls this round; no Layer-2.
> Nature: reference-source verification and registration; not independent human review; no gold is signed.

## 1. Target source

- Official document: BCE Inc. 2019 Q4 Supplementary Information, page 4
- Designated URL: https://www.bce.ca/investors/financial-reporting/2019-Q4/2019-q4-supplementary-information.pdf
- Facts to support (Q11 reference source completion target):
  - Bell Wireless Q4 2019 = 2493
  - Bell Wireless Q4 2018 = 2407
  - Unit = million CAD

## 2. Retrieval attempts (two rounds, both blocked)

| Attempt | Time (UTC) | Method | Result |
|---|---|---|---|
| 1 | 2026-10-16, exact time not recorded (before 03:49Z) | curl default UA | HTTP 302 -> `https://www.bce.ca/geo/index.html`; HTML "Request Rejected / Requete rejetee", 7380 B |
| 2 | 2026-10-16 03:49:53Z | curl + browser UA | Same: 302 -> geo page served by AkamaiGHost; 7380 B |

- Both response bodies are byte-identical: sha256 `6a53e737e4671caa5c72e936d72d17a88561f8e78fa6372260fb1fbe01d05329`, 7380 bytes.
- Evidence files:
  - `bce_2019_q4_retrieval_blocked_attempt1.html`
  - `bce_2019_q4_retrieval_blocked_attempt2.html`
  - `bce_2019_q4_retrieval_attempt2_headers.txt`
  - `bce_retrieval_attempts.json`
- Conclusion: the official PDF is redirected/denied at this network location by Akamai geo/risk controls; the official original cannot be archived. Do not claim the official PDF was archived; do not fabricate a source.

## 3. Registration: OWNER_SUPPLIED_SOURCE_STATEMENT

- Facts relayed by the owner this round (registered as owner statement, not as a verified official original):
  - Source claimed: BCE official 2019 Q4 supplementary information, page 4
  - Bell Wireless Q4 2019 = 2493; Q4 2018 = 2407; unit = million CAD
- Use restriction: reference-side only (`reference_source_completion`); it explains where the reference numbers come from. It is **not** an accepted citation yet; citing requires an accessible source or a proper archive.

## 4. Hard separation: reference_source_completion vs model_input_supplement

- `reference_source_completion` (this file): completes evidence for the scoring/audit side about where reference numbers come from. It never enters any system-under-test input.
- `model_input_supplement`: if a future round wants to add e.g. an explicit "in millions" statement to the **model-visible input**, it must ship as a **separately versioned input artifact**, e.g. `dev_panel/inputs_supplement_v1/Q11.json`, listed beside `inputs_original`/`inputs_perturbed` with its own hash and authorization in PANEL_MANIFEST. Do not mix reference-side material into existing input files; do not rewrite the Q11 input in place.

## 5. Path to unblock

1. Open the designated URL from a network location that is not geo-restricted (or by human browser), download the PDF, and archive page 4 with screenshot/hash.
2. Or have the owner provide a reliable copy of the PDF (with acquisition record); the executor verifies byte hashes before archiving.
3. On success, update this file to `SOURCE_ARCHIVED` and register file hashes.

## 6. Not done / boundaries

- Q11 original question, reference, and quarantine card are unchanged (`measurement_contract_v2/quarantine/Q11.md` untouched).
- 2493/2407/unit were NOT written into any model input.
- No other sources were searched online; only the designated URL was attempted, twice.
- No model/API/training calls.
