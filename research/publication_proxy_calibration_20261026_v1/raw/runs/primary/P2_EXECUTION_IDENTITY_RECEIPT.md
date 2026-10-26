# P2 Execution Identity Receipt

The scientific model outputs are bound to the frozen selection/reference
sources, visible-context payload, prompt template, local checkpoint files and
per-attempt call records. The pre-generation formal preflight is preserved as
`P2_REMEDIATION_PREFLIGHT_BEFORE_GENERATION.json`; it passed and records zero
generated outputs at qualification time.

The runner source that executed generation and scoring was not separately
hashed before the first call. Its source is reconstructed post hoc from the
current runner by removing only the later per-attempt scoring enrichment and
restoring the original retry/wall-time ledger labels. The reconstruction is
preserved at `P2_GENERATION_RUNNER_SOURCE.py`; its SHA256 is
`e20bfb2f4da16bb1a028ed9ab67ea14c75d7a960f420bcd74d136e2e377e4868`.
This is an explicit engineering reproducibility qualification, not a claim
that the original pre-generation runner hash was captured.

| Bound object | SHA256 |
|---|---|
| Formal preflight receipt | `fbcea1922c2d5ebbfe93e97352ed7092714e79c2550eeec43b52b4b3de8f00e5` |
| Model interface qualification | `2b7e475364f7c7f35871fc8a86385022883546a419b2cc1154ba477f41db0cc9` |
| Reconstructed generation runner | `e20bfb2f4da16bb1a028ed9ab67ea14c75d7a960f420bcd74d136e2e377e4868` |
| Current scoring-enriched runner | `bc7073200e04ef41990f3082ec6da9f69f9bf79d1a93cdee6da3a8753039a91c` |
| Contracts and prompt template | `bf010ea69b88ef3fbd44119d0cad50e11ad954238b58c52e289289c7ccec6431` |
| Visible-context adapter | `a09de0584b49d042bb70170c5fb79a1fa2a9061af670c42e5238cc80055dce95` |
| Local model actor | `dc15a85b9a2d29ca4f82b1358a1e79c4e440793567f185e122ff91f248b91585` |
| Strict parser | `29a28aff913ff02dc063cd3be34b8f3b11c0ef7e05d130c400775f8cb2c911ba` |
| Decimal calculator | `d76bc167f560fb8b971ddb30dacc611def5b49c5ec4e1499218d76ded67a5edf` |
| Tri-state semantic matcher | `f211676a7f414d97edd508d13d2a46d399b8d90cad505817b97d46f0f4ecf2c7` |
| Scorer-input builder | `075836dbf1c6057e407370699fc291bc10a2c37237e6506a1ddf76f1e38ccb25` |
| Historical future matcher | `fced9f1c5c465a7b207322630aeb79af0acd5bd747cfd94d533f9e264f70e131` |
| Final 40-attempt raw ledger | `03f714dd0c8946e82e4e3b9fa7f74efb9911ac59236ec164929ac5e9afa38450` |
| Final calibration result | `d62b52726fcfae958b71d6a6d9a1333d809feb9d34377572f293987d6229e1db` |

The raw ledger contains all 40 attempts, including all four bounded retries,
strict parse outcomes, complete responses, semantic outcomes and risk flags.
No output, token, retry or failure is removed from the scientific accounting.
