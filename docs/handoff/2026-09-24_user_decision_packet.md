# 用户决策包（2026-09-24，解锁实验线所需的最小决策集）

> 状态: 决策请求件（Loop D）| 目的: 把「等待用户」的隐含状态变成可逐条裁定的显式选项；
> 每条给出「裁定后解锁什么 / 不裁定则维持什么 / 证据指针」。本件不授权任何下载、不改任何门。

## D-A：label_ledger 独立复核的 canonical 参考裁定（关键路径）

背景：label_ledger 要求每行 gold_action/gold_target 经两个独立 reviewer + 裁决；复核需要一份
canonical 字段参考。当前 corpus（drift-v0，TAT-QA 派生）的 schema 角色按「只取官方 schema/metadata」
裁定为 BLOCKED（协议件 §6：TAT-QA 仓内元数据仅 README 第 48 行注记，逐表列级官方记载在池外）。
若用管线自有映射配置作参考，标签复核会退化为「确认系统自己的 schema」，独立性不成立。

选项：
1. 用户提供官方 schema 摘录（TAT-QA 论文/网站的表结构节，作为只读参考件入仓并记来源）⇒ 解锁当前 corpus 的 label_ledger 复核 → feature ledger → manifest 装配 → DATA_NO_GO 重评。
2. 裁定变更：允许管线映射配置作为**内部复核参考**（仅限 label 复核用途，schema 角色仍 BLOCKED）⇒ 同上解锁，但独立性论证需在审计件中显式承载该裁定的局限。
3. 维持现状：label_ledger 只服务 P1-future 包（FinQA schema 草案已备）⇒ 当前 corpus 的 Phase 1a 继续停门，实验线只在 P1-future 路径推进。

## D-B：licence_record 签署（用户行为）

permitted_uses 四用途与 covered 哈希已备（协议件 §2 模板，两已填哈希 2026-09-24 只读复核）；
status/accepted_by/accepted_at 只能由用户签署。裁定后解锁 licence_permission 门。
覆盖范围是否涵盖数据文件属法务判断（模板已标 PENDING_LEGAL_REVIEW），可一并裁定或外询。

## D-C：P1-future 包的数据下载批准（可选现在做）

FinQA process/checkpoint 与 Valentine NYC 的 schema 草案、置信度草案、analysis_plan 模板、
receipt/ledger 运行器与装配检查单均已备齐（审计过）。若现在批准下载范围（仅 metadata+gold 字段、
不含全文 PDF 等），即可在 GB10 走 SOURCE_GO→LABEL_GO→SPLIT_GO 装配未来包；不批准则维持草案态。

## D-D：Loop A sandbox 口径裁定（LC-GOV-002 派发前置）

LC-GOV-002（治理/归档清单）READY 但 owner 为 Loop A（codex exec）；派发需裁定沙箱口径
（report-only 只读沙箱是否足够）。裁定后派发；不裁定则该卡保持 READY 且不派发。

## D-E：MIMO provider 单独批排期

loopa-exec / loopa-diag 两 profile 已对齐 deepseek-v4.1-flash + Token_Plan_Chat（路由层）；
config.toml 中 Xiaomi_Token_Plan provider 段的清理留待单独批（用户已裁定另批处理）。

## D-F：专利状态确认（外发总门）

确认前所有稿件仅限内部审阅、不上 arXiv、不公开代码（release_gate 维持）。
确认后解锁送审流程（小论文评估保底轨已备齐）。
## 裁定结果（用户 2026-09-25，逐条对应）

- **D-A = 选项 3**：本轮不提供官方 TAT-QA schema excerpt；label review 推迟到 P1-future package；
  主线程不得自行构造或替代官方 schema（当前 corpus 的 schema 角色维持 BLOCKED，P1 包用已审计的
  FinQA schema 草案）。
- **D-B = 批准**：D-B annex 所列四项 licence scope confirmation 获批准，**仅限该 annex 精确范围**，
  不扩展到其他数据源或许可口径 ⇒ licence_record 的 accepted_by/accepted_at 可以用户裁定填入。
- **D-C = 批准最小下载范围**：FinQA train.json + dev.json；Valentine 十个 NYC 目录 + LICENSE + bench.py；
  任何额外文件/目录/数据集须重新申报等待批准。下载执行于 GB10 仓外暂存
  ~/wzh/phase1a_staging_20260925/（监控中），sha256 与字节数落 manifest。
- **D-D = 授权范围设计**：Loop A sandbox scoping 仅限范围设计；不启动生产端口、不重启服务。
- **D-E = MIMO 继续挂起**：Loop A 用已跑通路由（deepseek-v4.1-flash / Token_Plan_Chat），Loop C 用 qwen3.8-max。
- **D-F = 维持**：专利未确认前不上 arXiv、不公开代码、不外发；任何 external release 需用户单独确认。
- 恢复指令：按已落地的 runner / manifest / audit 链路继续推进，不重做已完成部分。
