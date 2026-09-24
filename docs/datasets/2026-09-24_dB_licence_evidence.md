# D-B 签署证据附件：许可主文本实测（零下载，2026-09-24）

> 状态: 决策支持件（Loop D）| 服务决策包 D-B（licence_record 签署）| 仅元数据/README 文本，未下载数据体
> 目的: 把签署人需要面对的主文本与开放法务问题摆齐；签署 = accepted_by/accepted_at + 对下列范围的确认。

## 1 实测主文本

| 源 | 文本 | 实测 |
|---|---|---|
| FinQA repo LICENSE | MIT | 已取证 sha256 92c0e67b…（1 067 B） |
| FinQA README @0f16e286 | **零许可提及**（licen/CC BY/Creative 检索 0 行；6 518 B，sha eb86779c…） | registry 行 `README_REPORTS_CC_BY_4_0_RECHECK_AT_FETCH` 在记录 head 上**被证伪** |
| Valentine repo LICENSE | Apache-2.0 | 已取证 sha256 f4960433…（11 365 B） |
| Valentine 数据上游 | NYC Open Data 各数据集条款 | 仓内未转载条款文本；上游条款 govern 数据再分发 |

## 2 签署人面对的范围确认

1. FinQA：repo 级 MIT 覆盖代码；**数据许可在仓内无陈述** ⇒ 签署人需 (a) 接受「repo MIT + 上游论文/页面许可」组合并记录风险，或 (b) 先取上游显式陈述再签；
2. Valentine：Apache-2.0 覆盖 repo；NYC 目录数据受 NYC Open Data 上游条款 govern ⇒ 签署人确认再分发用途（training/tuning/evaluation/rule_acceptance）与上游条款兼容；
3. 署名义务：MIT notice 保留、Apache notice 保留；若他处适用 CC-BY 则按其署名；
4. licence_record 的 covered_artifact_sha256 仅覆盖入包工件哈希；许可范围判断不写入工件、只写入签署记录。

## 3 更正归属（registry 行修改归 ONLINE 卡/用户处置）

registry 行 finqa 的 `data_license_state = README_REPORTS_CC_BY_4_0_RECHECK_AT_FETCH` 在记录 head 上被证伪
（README 零许可提及）。更正为 `README_SILENT_ON_DATA_LICENSE_AT_RECORDED_HEAD` 属 registry 行修改，
归 ONLINE 卡/用户处置；本件只记录证伪事实与证据（README sha + 检索 0 行），在裁定前保持现状。
