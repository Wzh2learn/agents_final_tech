# Evidence locations and Git scope

Two generated research datasets are retained outside Git, in accordance with repository rules. The 5 MB guard is not bypassed by compression or splitting. As of 2026-10-28 they exist locally and at the GB10 paths below; SHA-256 was independently compared after transfer. These paths are private working evidence, not a public artifact or a license to redistribute source datasets.

| File | GB10 evidence path | SHA-256 |
| --- | --- | --- |
| `six_system_result.json` | `/home/testuser/wzh/research_evidence/paper_e_20261028/six_system_result.json` | `b4596b01db7557570f644fcecf0325af6a18261637e47b6c9e112480fb87acdc` |
| `dense_probe.json` | `/home/testuser/wzh/research_evidence/paper_e_20261028/dense_probe.json` | `c7833c9bb78ca0246e25c13e0518fbe39bfa11b5bc5a68491154355cd1a4e738` |

`audit_six.py` retains the original execution paths, including a `/tmp` input; for replay, provision the pinned inputs and paths deliberately and verify hashes. The numerical recheck accepts the six-system JSON as its first command-line argument. Reproduction also needs the licensed BEIR data, original scorer and `trec_eval`; the saved results do not by themselves prove access or redistribution rights.
