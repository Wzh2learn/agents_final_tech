# Paper E Layer-1 Independent Gold Summary v1

**Status:** `GOLD_NOT_ESTABLISHED`  
**Feasibility verdict:** **Independent gold NOT established on this dev corpus** under the frozen contract; the U rate exceeds 30%.

## Evidence

- **Primary:** 59 dev cases were labelled independently of the audited greedy matcher and semantic judge; `plan_sha256=a275e55ae3485db5f37716c6c6c229f9d4efd58dfbb078af2db5768cc043e3d9`.
- **Primary contingency (checker verdict × independent gold):**

| checker verdict | E | H | U |
|---|---:|---:|---:|
| visible | 6 | 11 | 31 |
| blind | 6 | 1 | 4 |

- **Exploratory rates:** `P(H | blind)=0.090909`, `P(E | visible)=0.125000`, `U rate=0.593220`.
- **Engineering:** `calls=0`; value-invariance was recomputed bytewise for `59/59` dev cases; input, plan, label, join, and contingency self-checks: `PASS`.

## Boundary

The result is a descriptive feasibility/dev contingency only. It is not a population rate, does
not establish an OCR conclusion, and does not by itself claim a harmful blind spot. Checker
verdicts were comparison targets only and were not used to assign any `E`, `H`, or `U` label.

## Human Adjudication

`35` dev case(s) remain `INSUFFICIENT_EVIDENCE` and must not be auto-labelled:

- `"b48bb5fb-ea46-4a44-a39e-f2554719d158"1"Accumulated Other Comprehensive Income (Loss)""income(收入)""mixed_lang""income(收入)"107` — uid=b48bb5fb-ea46-4a44-a39e-f2554719d158, col=1, reasons=source_header_empty_after_norm
- `"fa0ed823-f4a8-4063-b895-a517f9447dad"3"Medicare Part D Subsidy Receipts""收款""alias_variant""收款"314` — uid=fa0ed823-f4a8-4063-b895-a517f9447dad, col=3, reasons=source_header_empty_after_norm
- `"e2d0f4f9-d15b-4537-bc7a-625729013ba4"0"£m""m [1]""prefix_noise""序号前缀"385` — uid=e2d0f4f9-d15b-4537-bc7a-625729013ba4, col=0, reasons=nearest_neighbour_tie
- `"24ff90f9-79ee-4e0e-a1ec-1d94abe7bc8b"2"% of associated net revenues""turnover""alias_variant""turnover"426` — uid=24ff90f9-79ee-4e0e-a1ec-1d94abe7bc8b, col=2, reasons=source_header_empty_after_norm
- `"24ff90f9-79ee-4e0e-a1ec-1d94abe7bc8b"4"% of associated net revenues""营业总收入""alias_variant""营业总收入"426` — uid=24ff90f9-79ee-4e0e-a1ec-1d94abe7bc8b, col=4, reasons=source_header_empty_after_norm
- `"5bf40a9b-38a9-47db-8c83-c3a854ee71b7"1"CONSOLIDATED""CONSOLI2016年交易日D""date_variant""交易日/0"587` — uid=5bf40a9b-38a9-47db-8c83-c3a854ee71b7, col=1, reasons=source_header_empty_after_norm
- `"bf4ac2c0-98c9-481c-ba0c-c6728b3b3540"4"Unearned Revenue""营业收入""alias_variant""营业收入"737` — uid=bf4ac2c0-98c9-481c-ba0c-c6728b3b3540, col=4, reasons=source_header_empty_after_norm
- `"425ee1c7-fb82-4853-994a-9876c414fbd5"3"Total tangible fixed assets""资产总额(万元)""unit_suffix""资产总额(万元)"772` — uid=425ee1c7-fb82-4853-994a-9876c414fbd5, col=3, reasons=source_header_empty_after_norm
- `"f47d9a01-a25d-436c-a28b-7aa04e2df491"0"£m""m [1]""prefix_noise""序号前缀"1041` — uid=f47d9a01-a25d-436c-a28b-7aa04e2df491, col=0, reasons=nearest_neighbour_tie
- `"ea1f0fff-a213-4475-8b1c-221157649595"2"Accumulated Unrealised Gains or Losses on Cash Flow Hedges""现金流量""alias_variant""现金流量"1079` — uid=ea1f0fff-a213-4475-8b1c-221157649595, col=2, reasons=source_header_empty_after_norm
- `"1e712660-7b78-4791-8264-e517efde2e62"2"Weighted Average Grant Date Fair Value""Weighted Average Grant 对账日期 / date Fair Value""date_variant""对账日期/2"1128` — uid=1e712660-7b78-4791-8264-e517efde2e62, col=2, reasons=source_header_empty_after_norm
- `"ed76bf6b-4d46-42b2-88ff-b2205470c8af"4"Deferred Revenue (current)""营收""alias_variant""营收"1148` — uid=ed76bf6b-4d46-42b2-88ff-b2205470c8af, col=4, reasons=source_header_empty_after_norm
- `"38eb9da5-5c73-4366-af5f-9bd01019938a"2"Weighted-Average Grant Date Fair Value Per Share""Weighted-Average Grant date 2021-报表明细日期 Fair Value Per Share""date_variant""报表明细日期/1"1167` — uid=38eb9da5-5c73-4366-af5f-9bd01019938a, col=2, reasons=source_header_empty_after_norm
- `"2953b803-d49b-4fbb-8dc2-d9a3bec9d67e"0"Allocation of GasLog Partners’ profit/(loss)(*)""profit(万元)""unit_suffix""profit(万元)"1195` — uid=2953b803-d49b-4fbb-8dc2-d9a3bec9d67e, col=0, reasons=nearest_neighbour_tie
- `"617deeb3-f222-4172-a824-c62fc2214a89"1"CONSOLIDATE""CONSOLI2017期末""date_variant""期末日期/3"1290` — uid=617deeb3-f222-4172-a824-c62fc2214a89, col=1, reasons=source_header_empty_after_norm
- `"73a817fc-25df-494d-b0f2-79cfdab34076"1"Dividends Paid(1)""dividend""alias_variant""dividend"1327` — uid=73a817fc-25df-494d-b0f2-79cfdab34076, col=1, reasons=source_header_empty_after_norm
- `"bdeeb701-bae6-4a36-86d6-108c8e43c5e2"2"Percent Expected to be Recognized as Revenue""sales""alias_variant""sales"1596` — uid=bdeeb701-bae6-4a36-86d6-108c8e43c5e2, col=2, reasons=source_header_empty_after_norm
- `"648e1260-d160-45d2-a744-57be0fd89850"1"Purchased Intangible Assets""assets(资产)""mixed_lang""assets(资产)"1599` — uid=648e1260-d160-45d2-a744-57be0fd89850, col=1, reasons=source_header_empty_after_norm
- `"32cfcadb-add0-4cc1-9956-41ac073477c4"2"As a % of Segment Revenue (1)""营收""alias_variant""营收"1611` — uid=32cfcadb-add0-4cc1-9956-41ac073477c4, col=2, reasons=source_header_empty_after_norm
- `"1860a2e9-4ce1-4f18-bd9b-f84fd2ef62aa"2"Weighted-average grant date fair value""Weighted-average grant date 2021-对账日期 fair value""date_variant""对账日期/1"1683` — uid=1860a2e9-4ce1-4f18-bd9b-f84fd2ef62aa, col=2, reasons=source_header_empty_after_norm
- `"50e78448-3cf5-439c-a609-ee866bd1f05a"2"US$""US [1]""prefix_noise""序号前缀"1699` — uid=50e78448-3cf5-439c-a609-ee866bd1f05a, col=2, reasons=source_header_empty_after_norm
- `"fd39b5b5-7426-4db6-bbf7-d3c5111ce543"2"Interest Rate (per annum)""利息""alias_variant""利息"1744` — uid=fd39b5b5-7426-4db6-bbf7-d3c5111ce543, col=2, reasons=source_header_empty_after_norm
- `"aca23e3e-967d-40a9-b6bb-3c095786a3b7"1"Positive (Negative) Impact to Net Income""net profit""alias_variant""net profit"1935` — uid=aca23e3e-967d-40a9-b6bb-3c095786a3b7, col=1, reasons=source_header_empty_after_norm
- `"7a249c43-5e24-447e-9da1-3d5982aca590"1"Consolidated""Consoli2019期末d""date_variant""期末日期/3"1970` — uid=7a249c43-5e24-447e-9da1-3d5982aca590, col=1, reasons=source_header_empty_after_norm
- `"d6d9f70a-17b6-4530-b497-f73d59f0f0cb"0"Revenue by segment""营收""alias_variant""营收"2175` — uid=d6d9f70a-17b6-4530-b497-f73d59f0f0cb, col=0, reasons=source_header_empty_after_norm
- `"d8c20406-c646-4689-b645-5260bf17499d"0"Financial income and expenses""income(收入)""mixed_lang""income(收入)"2211` — uid=d8c20406-c646-4689-b645-5260bf17499d, col=0, reasons=source_header_empty_after_norm
- `"6bf238a5-0a3e-492d-91f8-7f62d3b37fba"0"Income statement expense""收入(income)""mixed_lang""收入(income)"2246` — uid=6bf238a5-0a3e-492d-91f8-7f62d3b37fba, col=0, reasons=source_header_empty_after_norm
- `"8692f92d-668a-452d-be7a-2b491ee27585"0"Income tax expense""income(收入)""mixed_lang""income(收入)"2265` — uid=8692f92d-668a-452d-be7a-2b491ee27585, col=0, reasons=source_header_empty_after_norm
- `"d7d65228-96c1-4890-951c-c3d7578f8031"3"Cash dividend per share (NT dollars)""Cash divdend per share (NT dollars)""ocr_similar""divdend"2284` — uid=d7d65228-96c1-4890-951c-c3d7578f8031, col=3, reasons=source_header_empty_after_norm
- `"54c494f7-d731-49bf-b9cd-d494aea72e34"2"Accumulated Amortization""amort""alias_variant""amort"2325` — uid=54c494f7-d731-49bf-b9cd-d494aea72e34, col=2, reasons=source_header_empty_after_norm
- `"3789d7da-dc3e-4cd7-b639-d6805211405a"1"Revenues""sales""alias_variant""sales"2345` — uid=3789d7da-dc3e-4cd7-b639-d6805211405a, col=1, reasons=source_header_empty_after_norm
- `"3789d7da-dc3e-4cd7-b639-d6805211405a"3"Income (loss) from vessel operations""income(收入)""mixed_lang""income(收入)"2345` — uid=3789d7da-dc3e-4cd7-b639-d6805211405a, col=3, reasons=source_header_empty_after_norm
- `"b6fa85a0-a203-4ed3-8c4d-6c1b5a8b08c1"3"Accounts Receivable, Net""帐号""alias_variant""帐号"2368` — uid=b6fa85a0-a203-4ed3-8c4d-6c1b5a8b08c1, col=3, reasons=source_header_empty_after_norm
- `"e9d3bb25-89ab-4aed-8bec-5501d5fe7b16"3"31,""3①""prefix_noise""①②圈号"2477` — uid=e9d3bb25-89ab-4aed-8bec-5501d5fe7b16, col=3, reasons=source_header_empty_after_norm
- `"abba843f-be4e-4905-8bab-19942dbfedef"3"Floating rate financial assets""资产(assets)""mixed_lang""资产(assets)"2482` — uid=abba843f-be4e-4905-8bab-19942dbfedef, col=3, reasons=source_header_empty_after_norm
