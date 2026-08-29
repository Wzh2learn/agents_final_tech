# W1 窗口汇报: T1/T2/T6 零端点合并窗口（单会话三段顺序）

> 任务卡: docs/experiments/2026-08-30_w1_window_card_t1t2t6.md（TASK-20260830-01, risk low, window approved）
> 执行: Loop A | 收口: 2026-08-30 | 端点调用: 0（三脚本各自 socket 层护栏 + 源码扫描零命中）
> 复算命令: `python3 research/paper_t1_eval_baselines.py` / `..._t2_visibility_sensitivity.py` / `..._t6_matching_competition.py`
> 复算验证: 三脚本连续双跑 payload_sha256 逐字节一致（收口抽验发现扫描集漂移缺陷并修复，见 §6 第 6 条 / commit 7eaef88）

## 1 执行结果（三段各一行）

| 段 | 结果 | 关键数字 |
|---|---|---|
| T1 评测基线对照 E1.1-E1.4 | **PASS** | G1 臂A root_scores 最大误差 0.0；G1 臂B 75/95（冻结 75/95）；G2 PSO 均值 1.4326（冻结 1.432574，误差 2.6e-05）最差 M7 0.0926（误差 0.0） |
| T2 可见性敏感性 E2.1-E2.3 | **PASS** | G3 S 档 75/95（by_type 计数误差 0，逐注入零失配）；等价变异 7 条（预期 ≈7）；ocr 全盲 5/5 个 γ 点成立 |
| T6 匹配竞争控制 E5.1-E5.2 | **PASS** | G4 贪心臂 75/95 零失配；oracle plain 0.952381 / overlay 0.597015（误差 0.0 / 0.0）；分配差异 0+0 列，翻转 0 条 → 分支 a |

段间不互锁规则未被触发（三段一次通过，无改期重跑，无 BLOCKED 段）。

## 2 工件路径

- `logs/graph/eval/t1_eval_baseline_comparison.json`（payload_sha256 `0ce023d6f83340dbc0e43a810b85c2d361a4b174337cdabc7da015f15c9ca87d`）
- `logs/graph/eval/t2_visibility_sensitivity.json`（payload_sha256 `827b1f828fcaf171893d27b2cc379bbe2ccae82564943d4826d06fe7903e9114`）
- `logs/graph/eval/t6_matching_competition.json`（payload_sha256 `901cd9fea3055f2e84ef3114e8e8ec0707a979f3f5fc27eb8ee494aea06ef2f3`）
- `logs/graph/eval/pso_weight_search_v0.json`（GB10 在盘既有工件首次入库，非新产，卡第 0 步）
- 本汇报 `logs/graph/eval/w1_window_report.md`

三脚本各含 `payload_sha256`（摘要范围 = 工件 `sha256_scope` 列出的确定性结果段，meta 时间戳/runtime 不入摘要）；修复后同输入双跑摘要一致（T2 另有段内双跑门 `determinism_double_run_identical=True`）。上列三个摘要为 7eaef88 之后的稳定值：修复只改 `zero_endpoint` 的扫描集来源，G1-G4 与全部结果段逐字段与修复前相等（脚本化对账：除 meta/payload_sha256/zero_endpoint 外 core 段 deep-equal = True）。

## 3 数字摘要

### 3.1 复现门 G1-G4（任务卡 §5 验收证据表）

| 声明 | 验证位置 | 实测值 |
|---|---|---|
| G1 臂A root_scores 误差 <0.01 | `payload.gates.g1_max_err` | **0.0**（9 mutant x 2 树 = 18 格全零误差） |
| G1 臂B 75/95 逐表一致 | `payload.gates.g1_armb_tables` | **75/95**（表级失配 0，注入级 0，by_type 六类计数逐项相等） |
| G2 PSO 均值 1.4326±0.01 | `payload.gates.g2_mean_sep` | **1.4326**（vs 冻结 1.432574，误差 2.6e-05） |
| G2 最差 M7 0.093±0.01 | `payload.gates.g2_worst_sep` | **0.0926**（0.0） |
| G3 S 档复现误差 0 | `payload.gates.g3_*` | **75/95** + by_type 计数误差 **0** |
| G4 贪心臂 + oracle 复现 | `payload.gates.g4_*` | **75/95** / 0.952381 / 0.597015（误差 0.0 / 0.0） |
| 零端点自证 | 卡 P5 grep + 各工件 `zero_endpoint.clean` | grep 零命中；三工件 clean = True/True/True |
| 附加：Algorithm 1 聚合同构 | `payload.aggregation_isomorphism` | 与 `scripts/eval_checkpoint_aggregate.py` 最大误差 **0.0** |

### 3.2 T1 臂 A 四协议（检出落点：E1.1 混池终局，E1.2-E1.4 受影响子树根；τ=2.0）

| 协议 | 检出 | 均值分离度（子树根 / 混池终局） | 最差 mutant | 定位率 | 成本（打分单元） |
|---|---|---|---|---|---|
| E1.1 end-to-end | 2/9 | 2.505278 / 1.252633 | M7_nf_fail_3 0.2083 | 0.0 | 2 根 |
| E1.2 flat | 4/9 | 2.5072 / 1.253611 | M7_nf_fail_3 0.1667 | 1.0 | 12 叶 |
| E1.3 hier expert | 3/9 | 2.505278 / 1.252633 | M7_nf_fail_3 0.2083 | 1.0 | 12 叶 |
| E1.4 hier + PSO | 4/9 | 2.856256 / 1.428156 | M7_nf_fail_3 0.0926 | 1.0 | 12 叶 |

### 3.3 T1 臂 B 三协议（95 表 / 118 注入；E1.4 设计稿标 N/A）

| 协议 | 表级检出 | bootstrap 95% CI | 注入级检出 | 定位率 | 最坏类型 |
|---|---|---|---|---|---|
| E1.1 end-to-end | 95/95 = 1.0 | [1.0, 1.0] | 112/118 | 0.0 | alias 0.8723 |
| E1.2 flat（=冻结判据） | 75/95 = 0.7895 | [0.6947, 0.8737] | 85/118 | 1.0 | ocr 0.0 |
| E1.3 hier expert | 20/95 = 0.2105 | [0.1263, 0.2947] | 13/118 | 1.0 | ocr/prefix/unit 0.0 |
| E1.4 hier + PSO | N/A | 设计稿 §3.2: PSO 权重在臂 A 的 11 维内部节点空间，与臂 B 实例化树不同构，不迁移 | — | — | — |

判据评估（设计稿 §4.6 / §1 降级表述触发）：E1.3 相对 E1.1/E1.2 在检出维度**无优势**（臂 A 3/9 vs E1.1 2/9、E1.2 4/9；臂 B 表级 0.2105 远低于 E1.2 0.7895），换来的是定位率 1.0 vs 0.0 → **触发预注册降级表述评估**（本窗只产证据，表述切换在 T7 写作卡）。臂 B E1.3 的机制归因：剪枝后 parse 树里 field.hit_rate 权重占比 3/8，根分降幅 = 3.75·ΔH，同 τ=2.0 等效 ΔH ≥ 0.533（严到 2.7 倍）。

### 3.4 T2 五组关键数

1. **ocr_similar 全 γ 网格可见率 = 0**（γ∈{0.2,0.3,0.5,0.7,0.9} 五点全 0）→ 预注册预测成立，主张 C1 的全盲维在阈值扰动下稳定。
2. **类型不均匀（注入级极差）**：γ=0.2 → 1.0；0.3 → 0.6471；0.5 → 0.5882；0.7/0.9 → 0.3。**字面判据（全网格 ≥0.5）在 0.7/0.9 两点不成立**，失败点 ['0.7', '0.9']；归因 = 单注入边际降幅按 1/n_canonical 量化、被表宽主导（多数表 n≥4 → 单列损失 ΔH≤0.25）。排序不均匀性本身在全网格存续（ocr 稳居 0 下界，每点 ≥3 类严格高于下界）→ 设计稿 §4.2 的实质要求成立，字面阈值不成立，两条分开入账。
3. **等价变异 = 7 条**（alias 4 + prefix 3 + mixed 0）与预注册预期逐条一致；校正后 ocr 全盲不变、alias/prefix 校正后可见率 = 1.0，主结论存续。
4. **强度梯度**：五类 W ≤ S 无一违反（alias W 0.1277 vs S 0.9149，余四类 W=0）；W 档 6 例非零可见全部归因为重复列竞争（tier≥2 且 ΔH=0，工件 `w_arm_partial_absorption_attribution` 三条谓词全 true）。
5. **ocr S′ 档 = 8/13 可见**（预注册 ≥10/13 **未达**）；构造性偏差已逐条归因：首个差异位邻接重复字符只在替换型损坏时把编辑距离推到 2，删除/插入型会落回 1（实测 8 条距离2 + 5 条距离1）。**机制判据零反例**：距离 2 的 8/8 全部可见，距离 1 的 5/5 全部被吸收 → 吸收区 = 精确 ∪ 归一化包含 ∪ 编辑距离≤1 得到实证划界。

### 3.5 T6 分支归属

- 分支 = **a**（分配差异表数 0 / 列数 0，Hungarian 权重增量 0.0，贪心 95/95 表已全局最优，注入级翻转 0 条含 ocr 13 条全不翻转）。
- 求解器自证：300 随机矩阵与暴力枚举最优值零间隙（`solver_validation.bruteforce_exact=True`）+ 贪心必次优的正例可被识别（`positive_control_detects_improvement=True`）→ 0 差异不是求解器退化造成的假阳性。
- 判据 P2：ocr 翻转 0 条（预测"多数不翻转"成立，实测全不翻转）。
- 判据 P3 影响范围 = **无实质改变**（极差 greedy 1.0 vs hungarian 1.0；表级判别 75 vs 75；数值规则执行前写定于脚本 `IMPACT_RULE`，不随实算调整）。
- 机制证据升级：13/13 形近串在真值 canonical 上获正分（tier 1 兜底）且**无更高分竞争列**；全语料 22 条吸收全部满足该条件 → 吸收是打分层给出的『无异常』结论，换任何分配策略同样命中。E5.2 天花板（plain 40/42 = 0.952381，overlay 40/67 = 0.597015）独立重算复现，与匹配器下界 0.558095 / 0.594762 分列不混同。

## 4 红线自查（五条逐项）

| 红线 | 自查方式 | 结论 |
|---|---|---|
| 甲方数据零进入 | 三脚本 grep `m1_samples` 零命中；底座 = `data/research/drift_v0`（TAT-QA 公开 + 合成注入）+ VGMC 碰撞语料（同源派生） | PASS |
| 零端点（无网络/无模型调用，不夹带 E1.5/E1.6） | 卡 P5 grep（`urlopen\|requests\.\|http://\|https://\|:800[0-9]\|:5050`）三脚本零命中；各脚本运行时 socket 层护栏（连接即抛）；`endpoint_calls=0`；工件 `zero_endpoint.clean=true` | PASS |
| 冻结节点/冻结工件零改动 | `git diff --name-only d3d31b0..HEAD`（开窗基线→收口）只含本卡 7 个路径（3 脚本 + 4 工件；本汇报为第 8 个）；frozen_hashes.txt 五件 md5 逐一复核 = 全 OK；四件对账工件 + 树配置 + 聚合脚本 + 生产解析器 diff 全空（解析器最后改动仍为 2026-08-12）；docs/experiments/ 本窗零新增零改写 | PASS |
| 禁 git add -A / 禁 amend / 只 add 本卡文件 | 本卡全部 commit（4 feat + 1 fix + 本汇报 docs）逐路径 add（工件目录被 .gitignore 覆盖，用 `git add -f <显式路径>`）；无 amend；工作区第三方改动（config/schema_suggestions.json、logs/graph/{dispatch_log.md,docs_lint_report.json,loop_b_last_status,verify-report.json}）未入任何 commit；fix commit 只触本卡三脚本 + 三工件 | PASS |
| T3/T5 不在本窗 / :8006 零触碰 / 专利终态件只读 | 未触 t3/t5 设计稿与任务卡；无任何 :8006 引用（grep 零命中）；专利件未读未写 | PASS |

### 与本窗无关的记账（不处置）

- Loop B 开窗前最近一轮 overall=FAIL，唯一 FAIL 项 = `git_alignment`（本地 main 领先 origin/main：开窗时 ahead 2 → 本窗 5 个 commit 后 ahead 7 → 本汇报 commit 后 ahead 8），其余 7 项含 frozen_nodes / pytest / api_anchors / qa_canary 全 PASS。推送属对外写操作，不在本卡授权范围 → 留 Loop D 决定。
- 收口清单扫描（AGENTS.md 2026-08-29 制度化）：`scripts/graph/governance_drift_scan.py` 实跑 = 15 hits / registered 4。新登记 4 条中 3 条是本窗三件预注册设计稿的 INDEX 状态词"待执行"已过期（W1 已执行完 T1/T2/T6，属真漂移），第 4 条为无关的 `superpowers/plans/2026-08-29-long-hori…`。处置 = **不在本窗**：改 `docs/INDEX.md` 状态词超出本卡"只 add 本卡脚本与工件"红线，且属 Loop D neat 收尾职责 → 留台账待核。副作用如实入账：扫描器按设计写入了 `docs/29_graph_engineering_roadmap.md` 与 `logs/graph/governance_drift_latest.md`，两件在本卡授权外故**不 add、留工作区**（登记幂等，下轮扫描不重复）。

## 5 commit 清单

```
7eaef88 fix(research): W1 零端点自扫描改为固定清单, 重算可复现 payload_sha256
0d337b9 feat(research): T6 匹配竞争控制 E5.1-E5.2 零端点执行
670dc44 feat(research): T2 W 档部分吸收逐条归因（重复列竞争）
1333cae feat(research): T2 可见性敏感性 E2.1-E2.3 零端点执行
cca4144 feat(research): T1 评测基线对照 E1.1-E1.4 零端点执行
```

段 T1 另含 `feat(research)` 首 commit 内 `logs/graph/eval/pso_weight_search_v0.json` 首次入库（卡第 0 步指定，既有工件入账非新产）。

收口之后的两枚记账 commit（同属本窗，逐路径 add）：`86d4d55` = 本汇报入库；`de0a789` = `memory/STATE.md` W1 结果段入账（Loop A 记忆协议 Phase 5 L1）。开窗基线 `d3d31b0` → 收口共 7 枚 commit，触及路径 = 本卡 3 脚本 + 4 工件 + 本汇报 + STATE.md（九件），冻结件与治理件零改动。

## 6 pivot 与偏差登记（如实记录，不静默改判据）

1. **PSO 输入口径 pivot**：设计稿 §2 列出的臂 A 工件为 08-26 `checkpoint_discrimination_report.json`，但 PSO v0 工件生成于 08-21，其 control.live_leaves 与 delta 实际来自 `checkpoint_discrimination_report_20260819.json`（全叶 10.0、M5 delta -6.0）。按 08-19 口径复算 G2 精确复现（1.4326 / 0.0926，逐 mutant 最大误差 0.0001）；按设计稿所列 08-26 口径复算为均值 1.428156、最差 0.0926，同样落在 ±0.01 门内。两口径均入工件 `arm_a_pso_reproduction.caliber_variants`，G1（臂A）以 08-26 v2 报告为准（误差 0.0）。→ 建议 T7 写作引用 PSO 数字时标注输入报告版本。
2. **T2 γ 网格字面判据部分不成立**（0.7/0.9 极差 0.3 < 0.5）：机制归因与"排序不均匀性存续"的实质判据一并入账（§3.4 第 2 条）。
3. **T2 S′ 档未达 ≥10/13**（实测 8/13）：构造性偏差，非机制反例；机制侧 13/13 同构成立。→ 下一轮如需真正"距离 ≥2"档，须在预注册里改构造（例如追加双字符扰动并声明距离下界），本窗不改冻结构造。
4. **等价变异口径**：设计稿写 `mapping_inj == mapping_orig`（文本层），实测文本层完全一致 0 例、行为等价（标准字段集不变）19 例——吸收的定义本身就是"映射值换成注入文本"，两者不可能同时成立。按设计稿 §3.2 的 locality_clean 注记取行为等价口径，两种计数同时入工件（`n_mapping_text_identical` / `n_mapping_keyset_identical`）。
5. **E1.1 臂 B 表级 95/95 的读法**：其判据"终局映射任何变化即检出"会把吸收型漂移（字段仍在、标签已换）也计入检出，且定位率恒 0 → 该协议的高检出是阈值产物，不是能力，写作时须与臂 A 的 E1.1（混池标量把分离度腰斩、检出反而降到 2/9）对照呈现。
6. **收口抽验发现并修复：零端点自扫描集漂移使 payload_sha256 不可复现**（commit `7eaef88`）：三脚本 `self_source_scan()` 原以 `(REPO/"research").glob("paper_t*_*.py")` 枚举扫描集，而 `zero_endpoint` 落在摘要范围内 → 摘要随目录内容漂移。实测重算 T1 `files_scanned` 1→3、T2 2→3，两件工件 payload_sha256 变化，直接违反卡 §1"python3 重算命令可复现全部数字"；前瞻风险更大：T3/T5 脚本一旦落盘，本窗三件全部失配。修法 = 扫描集钉死为脚本内常量 `SCAN_MANIFEST`（本窗三段脚本名），新增 `missing_files`，`clean` = 无违规命中且清单无缺件。回归四条：①三件连续双跑摘要一致 ②除 `zero_endpoint` 外全部结果段与修复前已提交工件 deep-equal（G1-G4 零变化、三件 `all_pass=true` 不变）③探针实验：临时新建 `research/paper_t9_probe.py` 后重跑 T1，摘要不变（探针已删，未入库）④卡 P5 grep 仍零命中。→ 治理结论：零端点窗口的自扫描必须钉死清单，不得用目录枚举；T3/T5 派卡时写入脚本模板。

## 7 事后复盘（卡 §9）

- **结果**：三段全 PASS，G1-G4 全过且三项为逐格零误差；五个 commit（4 feat + 1 fix）+ 本汇报；三工件 + 收口前复现门重跑全部通过。零端点、零冻结改动、零甲方进入。
- **关键洞察**：
  1. C2（分层优于扁平）在**检出维度不成立**、在**定位维度成立**，且两维不可通约——臂 B E1.3 用 2.7 倍的阈值严格度换 1.0 定位率。这把论文的主张从"优越"逼向"等效成本下的可归因性"，正是预注册降级表述预留的路径。
  2. 阈值型可见性判据（γ 网格）在单注入边际上被表宽量化，测的是"表有几列"而不是"缺陷多重"；吸收区（无阈值）判据才是类型谱的度量。这条方法论结论同时解释了 T1 臂 B 与 T2 的全部 γ 现象，可直接进论文 §威胁/度量选择。
  3. 匹配竞争在打分层级下**完全不可由分配层消解**（贪心 95/95 全局最优 + 22/22 吸收无更高分竞争列）。C1 的可见性谱因此不需要"匹配器次优性"注记；效度威胁节改写为"根因在打分层污染"，并附求解器自证防假阳性。
- **推翻的旧判断**：
  1. "PSO 数字对不上 = 聚合实现有 bug"——实际是输入报告版本差异（supersede 指针：本汇报 §6.1 与工件 `arm_a_pso_reproduction.caliber_variants`；冻结报告两版本并存于 logs/graph/eval/）。
  2. "设计稿 §3.1 的未涉叶按 missing_score 补位"作为重算口径——按该口径臂 A/PSO 两门都不可能通过（parse 叶 missing=0 会把根分砸到 0）；实测冻结口径为"叶 = 基线叶分 + delta，未涉叶取基线值"，与 `research/pso/pso_weight_search.py` 的 `mutant_scores()` 一致（supersede 指针：工件 `arm_a.g1_root_score_reproduction.per_cell` 全零误差 + `aggregation_isomorphism.max_abs_err=0`）。设计稿正文未改（判据冻结），差异在此登记。
- **喂给了什么**：
  - **T4 窗**（需端点）：臂 A 的 E1.5 Full Judge / E1.6 3 seeds 仍缺；本窗已把"≥3 seeds CI 可算"一维用表级 bootstrap CI（2000 次，seed 20260830）部分承担并如实注记，T4 只需补真实多种子。
  - **T7 写作**：§3.2-3.5 四张表 = 论文 C1/C2 两主张的评测基线节与效度威胁节素材；§6 五条偏差登记即 limitations/construct-validity 小节的原始出处；`scoring_layer_evidence.rows` 提供 ocr 13 条逐列打分审计清单。
  - **治理**：frozen md5 复核 + 零端点 grep 可作为后续零端点窗口的自查模板（本卡三脚本内嵌的 `_install_network_guard` + `self_source_scan` 可复制）。补一条硬约束：复制时必须连同钉死的 `SCAN_MANIFEST` 一起复制（§6.6 的漂移缺陷正因漏了这一步）；另，"收口抽验 = 重跑一遍并比对摘要"本身被证明是必要的门，建议写进零端点窗卡的收尾动作序。
