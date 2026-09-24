# D-C 下载批准精确范围附件（GitHub API 元数据实测，零下载，2026-09-24）

> 状态: 决策支持件（Loop D）| 服务决策包 D-C | 仅 API 元数据（路径+字节数），未下载任何数据体
> 目的: 把 D-C 从「批准下载 metadata+gold」细化为「批准以下精确路径清单」，批准后即可执行装配。

## 1 FinQA（P1 process/checkpoint 流）

| 路径 | 字节 | 用途 | 范围 |
|---|---|---|---|
| `dataset/train.json` | 78 216 616 | process/checkpoint 标签派生（proposal/train） | **本次批准范围** |
| `dataset/dev.json` | 10 954 658 | 内部 dev（阈值/可学性） | **本次批准范围** |
| `dataset/test.json` | 14 395 143 | 后续 gated 评估（sealed 决策后） | 预留，不在本次 |
| `dataset/private_test.json` | 5 597 114 | 无 gold（leaderboard 专用） | **排除** |

许可：repo 级 MIT（已取证 sha 92c0e67b…）；README 报告数据 CC-BY 4.0（registry 记
README_REPORTS_CC_BY_4_0_RECHECK_AT_FETCH）⇒ 下载时复核 README 许可节并记录。

## 2 Valentine（P2 action 来源，schema-matching）

批准范围 = `experiments/data/` 下 10 个 NYC Open Data 目录（schema 对 + gold 匹配）：
City_Government__Capital_Projects、City_Government__DCM_StreetCenterLine、
City_Government__DPR_AthleticFacilities_001、City_Government__DSNY_Districts_With_Disposal_Vendor_Assignments、
City_Government__NYC_Municipal_Building_Energy_Benchmarking_Results、Education__COVID-19_Free_Meals_Locations、
Housing_&_Development__Housing_Maintenance_Code_Complaints_and_Problems、
Housing_&_Development__Public_Design_Commission_Outdoor_Public_Art_Invent、
Recreation__Swim_for_Life__2016_to_2020、Transportation__DOT_In-house_Street_Resurfacing_Projects。
另含 `LICENSE`（Apache-2.0，已取证 sha f4960433…）与 `experiments/bench.py`（协议参考，只读）。
逐目录字节数于下载时记录（API 目录列表不含递归大小）。

## 3 批准语义与排除项

- 批准 = 允许将上述精确路径下载到 GB10 包暂存区（仓外），下载时记录 sha256 与时间，随后按门序列装配；
  任何清单外路径仍需新批准。
- 排除：全文 PDF、private_test.json、其他仓库、任何私有数据。
- 下载不改变任何门；DATA_NO_GO 仅在装配+双次 precheck+独立复核后重评。
