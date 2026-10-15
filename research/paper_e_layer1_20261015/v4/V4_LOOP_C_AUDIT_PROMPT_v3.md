ACK FIRST LINE: ACK pe-l1-v4-audit: Loop C independent auditor

ROLE: Loop C independent auditor on GB10. Read-only. Do not modify runner, contract, fixtures, or preflight receipt.

GOAL:
Audit the v4 compact pipeline before any held-out label is computed. Verify that v4 is a single
governing contract with a machine-checkable implementation, that the synthetic preflight passed,
and that no held-out label or checker verdict has been read as a label source.

SOURCES:
- research/paper_e_layer1_20261015/v4/LAYER1_V4_COMPACT_CONTRACT_v1.json
- research/paper_e_layer1_20261015/v4/V4_GOVERNING_MANIFEST_v1.json
- research/paper_e_layer1_20261015/v4/run_v4.py
- research/paper_e_layer1_20261015/v4/fixtures/SYNTHETIC_FIXTURES_v1.json
- research/paper_e_layer1_20261015/v4/PREFLIGHT_RECEIPT_v1.json

CHALLENGE AND VERDICT PER ITEM (PASS / CONDITIONAL / FAIL):
1. Single authority: the manifest pins the contract and fixtures; no competing v4 contract exists.
2. Contract completeness: inputs pinned, held-out-only sample, closed reason codes, decision gate,
   stop conditions, zero-call budget, and checker-read-after-label-freeze policy are all present.
3. Preflight honesty: preflight PASS is reproduced from fixtures only; it does not read the real
   injection map, heldout labels, or checker verdicts.
4. Runner order: compute labels -> write labels_frozen hash -> only then read checker target.
   The heldout mode must not read dev labels for any decision.
5. Fixture coverage: direct E, non-target-empty E, harmful other-column H, target-empty U,
   target-collision U, tie U, injected-empty U, non-target-empty H are all covered.
6. Claim boundary: no population rate, OCR result, harmful blind spot, or Layer-2 activation is
   claimed before the heldout run and its post-result audit.

ALSO CHECK:
- Any scope change beyond the single frozen column-local rule = STOP.
- Any hidden use of checker verdicts before labels_frozen hash = STOP.
- Any path where changing fixtures or contract after preflight would not invalidate the run = FAIL.
- Recompute the preflight fixture results from the runner logic; report mismatches.

OUTPUT:
If write is permitted, write only:
`research/paper_e_layer1_20261015/v4/V4_LOOP_C_AUDIT_v3.md`
Otherwise include the full audit in your final reply and state write blocked.

End with `VERDICT: PASS / CONDITIONAL / FAIL`.

FORBIDDEN:
No heldout label computation; no checker read for labelling; no edits outside the audit file;
no git write; no model/network/training call beyond this audit.


PINNED RUNNER:
runner sha256 = 9b53a271d2c7d44a579dd22a913954bac4ba08287809577a056f8c0078599755. Check that run_v4.py handles the real injection_map schema {mapping:[...],meta:{...}} and uses mapping entries for the heldout selection.



PINNED V2 ARTIFACTS:
contract sha256 = 167a2d02a3913d95125722d3069d55e23c50eaa38d84479f6f8e57e5c3fc7e65
runner sha256 = cc26f0450c98d43fc712e762f721eb5b61e59584eac385b07f95530d4a38953d
manifest sha256 = e4be3187f7ad0c7422405ce8d2a5c5660e8d4d6752c72c7bc568d07884ad7461
fixtures sha256 = 0d3f023b04ced843355c58999af0c6d9af3e959a2a4852169da951b577555acd
preflight receipt sha256 = 2dc09b184f0976dec5810345cddec8481e6a92f555951c334db039130220adce

V2 FIX CHECK:
Verify F-1 (equality/collision precedence stated and implemented), F-2 (injection_id defined), F-3 (checker byte-read deferred until after labels freeze), F-4 (misleading self-attestation removed/replaced), and freeze enforcement (heldout run requires a PASS preflight receipt whose contract/fixtures/manifest hashes match current files). Any remaining defect is CONDITIONAL or FAIL.

