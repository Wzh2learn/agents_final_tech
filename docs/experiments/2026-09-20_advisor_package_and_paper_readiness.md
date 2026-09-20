# 导师材料包与小论文完成度盘点（2026-09-20, 只准备不外发）

> 状态: 盘点件（2026-09-20, Loop D 主线程, 零端点）| 取代/被取代: 不取代任何件
> 性质: **只整理文件与摘要, 本批未外发任何材料**（红线: 专利正式申请状态未确认前不上传 arXiv / 不公开代码 / 不对外发送任何版本）
> 边界: 本批**未改 `docs/33` 与 `docs/34` 一个字节**（用户裁定); 本件只做清单与盘点, 不改任何被盘点件
> 取值时间: 2026-09-20; 全部 sha256 为 16 位前缀, 口径 = 整文件字节

## 1 导师材料包候选（三组, 共 18 件; 未发送）

### 1.1 导师提供的 hbkeyan 材料（仓外, 5 件；来源 = 导师, 本仓只读）

| # | 文件 | 字节 | sha256(16) | 定位 |
|---|---|---|---|---|
| 1 | `hbkeyan/2604.13717v1.pdf` | 1 737 030 | `c93b36bfab7a123e` | "An Empirical Investigation of Practical LLM-as-a-Judge Improvement Techniques on RewardBench 2"（ComposoAI）⇒ 对位论文四簇之四「裁判可靠性」 |
| 2 | `hbkeyan/2604.15715v1.pdf` | 6 033 525 | `65692cd88a7e3741` | GTA-2（Benchmarking General Tool Agents）⇒ 大论文章 1 的方法骨架引用源 |
| 3 | `hbkeyan/大模型长流程测评专利.pdf` | 822 639 | `7db456dc685318f7` | 导师/合作方专利底座 ⇒ 大论文章 4（PSO 驱动测评优化）落点 |
| 4 | `hbkeyan/长流程.md` | 5 781 | `2a7c8dfe354a4748` | GTA-2 精读笔记（Algorithm 1 递归聚合 / Root SR / Leaf SR / Tool SR / Score-Cost） |
| 5 | `hbkeyan/指标公式.md` | 18 705 | `89bf8279e2627b15` | 指标公式汇编（GTA-2 递归聚合 / RAGAS 五件套 / pass_k / RDC / RDS / VAF / GDS / MOP / TSR / ARS / ATS / ECE / Brier） |

**⚠ 已知脆弱点（只记不改）**: 该 5 件在**仓库上一层** `D:\AIRcommend\JinRongAgents\hbkeyan\`, 属**仓外材料** ⇒ 单独 clone 本仓无法解析。引用时须写明基准目录。

### 1.2 论文侧仓内件（本仓 tracked, 11 件）

| # | 文件 | 字节 | sha256(16) | 说明 |
|---|---|---|---|---|
| 6 | `paper/draft_v0_s1_s2_s6.md` | 19 788 | `89f46d5017eab273` | 小论文正文草稿 v0（S1/S2/S3shell/S6/S7shell + 效度威胁 stub） |
| 7 | `docs/experiments/2026-08-29_long_horizon_eval_paper_blueprint.md` | 12 041 | `ee600f04dc9c5fd7` | 会议小论文蓝图（主张-证据-缺口矩阵 + 章节骨架 S1-S7 + Phase 1-5） |
| 8 | `docs/34_专利_小论文_大论文协同研究路线.md` | 14 602 | `2d9e51e3426af63e` | 上位路线文档（专利-小论文-大论文协同）**本批未改** |
| 9 | `docs/experiments/2026-08-30_phase_a_autopsy_and_claim_set_v2.md` | 21 781 | `3fe8aba95de1a09a` | Phase A 冻结件（Claim Set v2 + 六件尸检） |
| 10 | `docs/experiments/2026-08-31_d1_audit_report.md` | 15 135 | `21c63f99f188b610` | D1 审计报告（118 注入三分类 85/7/26） |
| 11 | `docs/experiments/2026-08-31_d2_cross_matcher_phase_a.md` | 15 825 | `e2705a10d30ccd21` | D2 跨匹配器阶段 A |
| 12 | `docs/experiments/2026-08-31_d2_cross_matcher_phase_b.md` | 23 338 | `b7c1729c5a88a4d4` | D2 跨匹配器阶段 B |
| 13 | `docs/experiments/2026-08-31_related_work_v4.md` | 17 398 | `7e8a74c49156a0da` | 相关工作 v4（四簇定位 + BibTeX 实查） |
| 14 | `docs/experiments/2026-09-08_d3_autopsy_decision_record.md` | 44 560 | `7f95a467d26ff11c` | D3 autopsy 决策记录（七层分层 + agreement 谓词草案） |
| 15 | `docs/experiments/2026-09-07_d3_stage_b_closeout.md` | 26 367 | `83562987faff00e2` | D3 阶段 B 收口（27/27 抽验 PASS） |
| 16 | `docs/experiments/2026-09-20_kd_literature_candidates.md` | 15 555 | `92e09b09e0f2b863` | 知识蒸馏候选文献核验表（18 条; 服务 Discussion / 大论文路线） |

### 1.3 已发送件（本机留档；发送动作已由用户完成）

| # | 文件 | 字节 | sha256(16) | 状态 |
|---|---|---|---|---|
| 17 | `advisor_send_0826/31_导师进展汇报_v2_20260825.docx` | 697 743 | `6a40b662886a1cb5` | 已发送（09-11 用户确认） |
| 18 | `advisor_send_0826/demo_v3.mp4` | 36 432 630 | `c3d44cc53a891fee` | 用户 09-13 确认**已亲发** ⇒ INDEX `:142`「待发送」已过期（待主线程更正, 本批未动） |

## 2 小论文完成度盘点

蓝图 = 7 页正文 + 参考文献 + 附录; 章节骨架 S1-S7（预算合计 **7.0p**）。

| 节 | 预算 | 内容 | 草稿状态（`paper/draft_v0_s1_s2_s6.md`） | 组装 |
|---|---|---|---|---|
| S1 | 0.75p | 问题: 最终正确 != 每步可靠; 协议本身可能失明 | **已写**（:9, ~296 词） | 待 T1/T2 数字回填 |
| S2 | 1.25p | 分层检查点评测框架（树 + 契约 + Judge + 证据链） | **已写**（:44, ~527 词） | 待 T1/T6 数字回填 |
| S3 | 1.5p | 缺陷可见性诊断 | **shell 已落**（:108, ~422 词; 决策 10=c） | 整节组装待 **T7** |
| S4 | 1.0p | 协议严谨性（权重搜索 null + 跨匹配器 + matched-FPR） | **未落**（仅在蓝图 `:35`） | 待 T7 |
| S5 | 1.5p | 实验（主结果表 + 敏感性 + 消融 + 外部效度） | **未落**（仅在蓝图 `:36`） | 待 T7 |
| S6 | 0.5p | 闭环案例（评测发现 -> VGRM 门控 -> 规则固化） | **已写**（:153, ~172 词） | 基本就绪 |
| S7 | 0.5p | 讨论 + 局限 + 结论 | **shell 已落**（:194, ~619 词; 决策 10=c） | 整节组装待 **T7** |
| — | — | Threats to validity | **stub**（:177, ~115 词; 决策 3 已落） | 正式组装待 T7 |

### 2.1 草稿内未闭合占位（7 处 [TODO], 逐条）

| 占位 | 落点 | 阻塞源 |
|---|---|---|
| `[TODO-*]` 总则 | :5 | 纪律声明（未产出的数字一律显式占位, 不编造） |
| `[TODO-T1: four-protocol baseline comparison table]` | :34 | T1 未执行 |
| `[TODO-T2: threshold-grid sensitivity of the spectrum]` | :35 | T2 未执行 |
| `[TODO-T1/T6: 端到端/扁平/分层专家基线 + 匹配竞争效度威胁与 oracle 天花板]` | :72 | T1/T6 未执行 |
| `[TODO-T6-crossref]` | :258 | T6 交叉引用待补 |
| `[TODO: algorithm-description 产伪代码]` | :262 | Algorithm 1 伪代码未入稿（审稿人视角标 **blocking-占位**） |
| （S7 前瞻句更正） | :232-:250 | **已处理**: D4 押后（决策 21=D）已将前瞻句以只增不改注记更正 |

### 2.2 两条硬阻塞（### 影响投稿时点, 逐条列明）

1. **T7 未执行** —— S3/S4/S5/S7 四节整节组装全部挂在 T7; 而 T7 的输入 T1/T2/T6 中 **T1/T2/T6 已由 W1 合并窗执行完毕**（见 `logs/graph/eval/w1_window_report.md`）, 但**数字尚未回填草稿**（草稿 :34/:35/:72 仍为占位）⇒ **T7 的真正的缺口 = 回填 + 组装, 不是再跑实验**。
2. **Algorithm 1 伪代码未入稿** —— 审稿人视角五问已把它列为 blocking-占位（:262）; 修法 = 用 `algorithm-description` 技能产出伪代码并与 `eval_checkpoint_aggregate.py` 逐行对位。

### 2.3 一条知识产权硬门（非本批可解）

蓝图 §6 逐字: 「专利交底书已发导师（08-22）, 尚无正式申请日确认」⇒ 投稿前必须**导师/代理确认申请状态 + 权利要求覆盖核对**; 确认前**不上传 arXiv / 不公开代码 / 不对外发送任何版本**。**该门只有用户能解**。

## 3 本批做了什么 / 没做什么

- **做了**: 只读盘点 18 件材料（含 size + sha256）、逐节核对小论文完成度、列出 7 处 [TODO] 与 2 条硬阻塞。
- **没做（明确）**: 未外发任何材料; 未改 `docs/33` / `docs/34`; 未改任何被盘点件的正文; 未上传 arXiv; 未公开代码; 未起任何 run; 未触任何端口。
- **下一步（待用户裁定, 本批不自行推进）**: ① 想发哪几件给导师（hbkeyan 5 件全发? 只发 GTA-2 + 专利?）② 是否先补 T7 回填与 Algorithm 1 再发。