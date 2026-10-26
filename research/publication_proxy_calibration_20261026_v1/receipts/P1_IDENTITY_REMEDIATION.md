# P1 Identity Remediation

This receipt corrects identities without rerunning or rewriting the accepted
public actor or its 24-row historical regression JSON.

| Identity | Recount | Meaning |
|---|---:|---|
| Numeric program correctness | 23/24 | Frozen program value equals the frozen expected value under the accepted tolerance |
| Complete semantic answer correctness | 13/24 | Numeric equality plus observable unit plus no unresolved reference-direction conflict |
| Rule-conformant unit agreement | 14/24 | The actor emitted a visible unit on 14 rows |
| Rule-conformant unit `UNKNOWN` | 10/24 | The visible table did not legally bind the unit; these are not numeric failures |

The single unresolved row is `NAT_train_b7814ec0_7b6669a8::original`. Acceptable
reading A is later minus earlier: `2019 - 2018 = -1955`. Acceptable reading B
is the frozen reference direction: `2018 - 2019 = 1955`. The disposition is
`UNRESOLVED`; the report does not select one reading as gold.

Source for all counts:
`p1_rule_execution/full_24_regression.json`, SHA256
`d03da88bcf39e7d9d3e16d1618950784de32a3b1eaa8eb89eb3523a9ff19f6e4`.
