# D2 跨匹配器验证报告 · 阶段 B（bge-m3 本地嵌入件, 零端点）

> 卡号: TASK-20260831-D2（定稿 + 加编两阶段切分, 阶段 B 独立派发条款未启用 = 同会话续跑）| 执行者: Loop A（GB10）| 执行日期: 2026-08-31
> 判据冻结: 卡 §2 预注册 P-1..P-5 零改动; **P-2 嵌入臂 = 探索性, 预注册不设通过/失败判据 → 本报告不判定嵌入臂优劣**
> 底表（只读）: `logs/graph/eval/d1_mutant_validity_audit.json` + 阶段 A 工件 `logs/graph/eval/d2_cross_matcher_det.json`（前后 sha 全等, 零覆写）
> 工件: `logs/graph/eval/d2_cross_matcher_embed.json`（独立件, 与阶段 A 件分离）| 脚本: `research/paper_d2_cross_matcher_embed.py`
> 前置报告: `docs/experiments/2026-08-31_d2_cross_matcher_phase_a.md`（阶段 A = 编辑距离族四件, 已交付 7b49fb3）
> 本报告只收集与判定工件内门; 主张层（论文含义）判定归主线程 autopsy（收集与判定分离）。

## 1. 执行结果

阶段 B 两件（bge-m3 余弦打分 × 贪心 / Hungarian 两分配轴）一次跑通, **全门 PASS**（G0/G1/G3/G4/G5/G6 → `all_pass = true`, exit 0）。

- **确定性与可复现**: 两次实跑 `payload_sha256` 逐字节全等 = `299ab1c7acfc8b272fce6c1a3bbf18ca01d35810d715cd1b62c3c651f121f950`; 原始文件差异仅 `.meta.generated` 一个时间戳字段（与阶段 A 同口径, 摘要在 payload 收口后计算）。
- **G0 复现门 PASS**: 阶段 B 内重算生产件仍逐条复现 D1 底表 118 注入 × 6 字段 **零失配** → 嵌入件对比的分母与口径可信（否则嵌入谱无对照意义）。
- **G1 定标有效性门 PASS**: 阈值可定标（286 正控对, 0 < 0.5439 < 1）且**先于任何注入打分冻结** —— 此为定标有效性, **不是 P-2 过判**。
- **G3（P-3 同口径观察, 非判据）**: 等价 7 条在嵌入两列下保持吸收-等价, **零翻转**。
- **G4（P-4 零端点自证）PASS**: `ports_touched = []`、`model_service_calls = 0`、只读件前后 sha 全等、甲方标识零命中。
- **G5（P-5 矩阵完整）PASS**: 33 吸收注入 × 3 列（生产参照 + 嵌入两探索列）= 99 格零缺格。
- **G6 digest 自洽 PASS**; `payload_sha256` 与顶层 `gates` 分离入件。

**方向性读数（按 `#D2-DIRECTIONAL-TRIGGER` 立即上报, 不等 autopsy 排期）**: 阶段 A 已因 τ_min = 0.733 < 0.8 触发; 本跑两个嵌入臂 τ_min = **0.276026 / −0.298142**（显著更低）, 同时 `ocr_similar` 13/13 在任意 γ 下可见数恒 **0**（未被照亮）。P-2 无过判 → 这些是**证据而非门失败**; 对 R3 两半句的最新合看见 §5。

## 2. 打分基与资产（本地 HF 权重, 全程零模型服务调用）

| 项 | 值 |
|---|---|
| 模型 | `~/wzh/models/hf/bge-m3`（config + `pytorch_model.bin` sha `b5e0ce3470…`, 2,271,145,830 B） |
| 设备 | `device="cpu"` 显式, torch threads 8（**刻意不占 GPU**: GB10 显存由 :8004 生产 llama-server 持有, 本窗零争用） |
| 装载 | `SentenceTransformer(..., local_files_only=True)` + 离线 env 三件套（`HF_HUB_OFFLINE` / `TRANSFORMERS_OFFLINE` / `HF_DATASETS_OFFLINE` = 1） |
| 编码量 | 496 文本 / 16 本地批（`local_encoded_texts` / `local_inference_batches`, 与 `model_service_calls = 0` **分列披露**） |
| 护栏时序 | socket 封死**先于** `sentence_transformers` 导入与模型装载（装载期任何 hub 联网尝试都会被拦并逐事件披露）; 实测被拦事件 3 条 = 护栏自证三探针（create_connection / getaddrinfo / socket.connect）全部, **模型导入-装载-编码路径贡献 0 次出站尝试** |
| 打分 | 归一化后余弦（表头原文 × canonical 原文, 文本级缓存 ⇒ 批确定 ⇒ 结果确定）; `cos ≤ 阈值` 记 0 不合格 |
| 分配 | 贪心件 = 与阶段 A 归一化件同构（(score, len) 降序先到先得）; Hungarian 件 = T6 `hungarian_max`, cos×1000 经 T6 标量编码 |

继承口径: 可见性判定 / 三分类 / γ 网格 / τ-b 逐字沿用阶段 A 件（`research/paper_d2_cross_matcher_det.py`），唯一变量 = 打分基（字符串编辑距离 → 语义嵌入余弦）。

## 3. 阈值定标（先于注入打分冻结, 与注入语料零重叠 ⇒ 非循环定标）

定标规则（预注册 P-2 内嵌规则）: 阈值 = 生产 schema `(standard, synonym)` 正控余弦分布 **p05**; 正控取自 `config/m1_table_schema.json`（286 对, 与注入语料无交集）, 负控 = 跨字段对（286 对, 按 `NEG_SAMPLE_MOD` 确定性抽样）。看结果后不调阈值。

| 量 | 值 |
|---|---|
| 冻结阈值 | **0.5439** |
| 正控 n / 分布 | 286; min 0.458183 / p05 0.543866 / median 0.811071 / p75 **1.0** / max 1.0 / mean 0.811796 / sd 0.158414 |
| 负控 n / 分布 | 286; min 0.344851 / median 0.514428 / p75 **0.556794** / p95 0.676647 / max 0.803954 / mean 0.517239 / sd 0.085526 |
| 分离边际 p05(正) − p95(负) | **−0.13278（< 0）** |

**如实入账（不调阈值救它）**:

1. **正负控重叠**: 负控 p75 = 0.5568 已高于冻结阈值 ⇒ 至少 25% 的**跨字段对**通过阈值门; 中位数 0.5144 亦紧贴阈值。bge-m3 余弦在「中文短表头 × 字段名」这一量纲上**分离力弱**, 阈值只能作弱门控。
2. **正控含同串对**: 286 对里 74 对（25.9%）是 `standard == synonym` 的字面同一对（cos = 1.0）, 正控 p75 = 1.0 即由该簇驱动 ⇒ 正控分布偏乐观, p05 实由 212 个非同一对的下尾决定。
3. 二者合起来 = 嵌入臂「高相似即命中」的判据宽于编辑距离族的绝对阈值, 直接机理见 §4 的可见率整体塌降与 §6 的吸收条数上升。

## 4. 每匹配器可见性谱（γ 网格, 可见数 / 该型注入数）

锚点 γ=0.2（生产三分类 H/E/HI 口径下）:

| 类型 | n | greedy_production（参照） | greedy_embedding | hungarian_embedding |
|---|---|---|---|---|
| alias_variant | 47 | 36（0.766） | 14（0.2979） | 12（0.2553） |
| date_variant | 17 | 12（0.7059） | 6（0.3529） | 6（0.3529） |
| mixed_lang | 20 | 19（0.95） | 1（0.05） | 1（0.05） |
| **ocr_similar** | 13 | **0（0.0）** | **0（0.0）** | **0（0.0）** |
| prefix_noise | 16 | 13（0.8125） | **0（0.0）** | **0（0.0）** |
| unit_suffix | 5 | 5（1.0） | 2（0.4） | **0（0.0）** |

整体三分类与全盲集合:

| 件 | 打分 | H / E / HI（118） | 全盲类型（任意 γ 恒 0） | τ_min vs 生产 |
|---|---|---|---|---|
| greedy_production | 编辑距离生产档位 | 85 / 7 / 26 | `[ocr_similar]` | 1.0 |
| greedy_embedding | bge-m3 余弦 + 贪心 | **23 / 57 / 38** | `[ocr_similar, prefix_noise]` | **0.276026** |
| hungarian_embedding | bge-m3 余弦 + Hungarian | **19 / 66 / 33** | `[ocr_similar, prefix_noise, unit_suffix]` | **−0.298142** |

逐 γ 的 τ-b（对生产贪心谱）:

| 件 | 0.2 | 0.3 | 0.5 | 0.7 | 0.9 |
|---|---|---|---|---|---|
| greedy_embedding | 0.276026 | 0.596285 | 0.771517 | 0.833333 | 0.833333 |
| hungarian_embedding | −0.298142 | 0.596285 | 0.771517 | 0.833333 | 0.833333 |

- **锚点处谱形最不稳健, 高 γ 处趋同**: 锚点名次 生产件 `unit ≻ mixed ≻ prefix ≻ alias ≻ date ≻ ocr` → greedy_embedding `unit ≻ date ≻ alias ≻ mixed ≻ (ocr≈prefix)` → hungarian_embedding `date ≻ alias ≻ mixed ≻ (ocr≈prefix≈unit)`; 生产件的第 1 名（unit_suffix）与第 5 名（date_variant）在 Hungarian 嵌入件里变成末位（并列）与首位 —— 首末对调即足以把 τ-b 压到负值（−0.298142）。γ≥0.5 后两嵌入件名次完全相同（date ≻ alias ≻ mixed ≻ 三类并列底部; γ=0.9 时 mixed 升到第 2）, τ 同为 0.771517 / 0.833333。
- **唯一在嵌入件下仍保持较高可见率的类型 = date_variant**（0.3529, γ≥0.3 时 5/17 恒可见且名列第 1）: 日期写法在语义嵌入空间里与财务字段名距离最远, 故 dH 仍被拉开; mixed_lang（跨语种字段名）恰恰相反 —— 嵌入把它"读懂"了, 可见率 0.95 → 0.05。
- **可见率整体塌降不来自盲区行**: 33 行矩阵内零例转为 H（§6）, 生产件 H 类 85 → 嵌入件 23/19 的 −62/−66 全部落在**原可见行变不可见**（宽阈值 + 语义吸附），即"新盲"集中在矩阵外的 H 群体, 属打分基替换的必然方向。

## 5. 全盲存续与盲区位置（R3 对照, 阶段 A + B 合看 6 件 / 2 打分基）

阶段 A 四件（编辑距离族）+ 阶段 B 两件事 = 6 个匹配器, 两种打分基:

| R3 降级表述半句 | 阶段 A 证据 | 阶段 B 新增证据 | 合看 |
|---|---|---|---|
| 「盲区位置匹配器相关」 | 四件全盲集合恒 = `{ocr_similar}`, 完全相同 → 不支持 | 嵌入件事件: `ocr_similar` **未被照亮**（0/13, 任意 γ）; 但全盲集合**扩大**为 `{ocr_similar, prefix_noise}` / `{ocr_similar, prefix_noise, unit_suffix}` | 需区分两问: ① 生产盲区是否随匹配器消失 → **否**（6 件恒含 ocr_similar, 且 D1 的 33 盲区行零例转可见）; ② 盲区**范围/位置**是否随打分基移动 → **是, 单调扩张**（新盲点位 prefix_noise / unit_suffix 出现在嵌入族） |
| 「谱结构（存在全盲类型）匹配器无关」 | 四件存续 → 支持 | 第二打分基（语义余弦）同样存在全盲类型, 且交集非空 = `{ocr_similar}` | **支持增强**（跨两种打分基存续） |

即: 预注册的"存在全盲类型"这一结构性质, 在语义嵌入这一**不同打分基**下依旧成立, 且六件全盲集合交集非空; 而"盲区具体落在哪些类型"随打分基变化（编辑距离族内恒等, 换到嵌入族则扩张）。**如何落笔归 autopsy**; 本报告的口径提醒: 第一半句若按「盲区消失/移动」与「盲区集合扩张」两种读法, 证据方向不同, 不宜笼统写成"匹配器相关"。

## 6. 迁移矩阵（33 条 D1 吸收注入 × 3 列, DR-3 验收）

列 = 生产参照 + 嵌入两探索列; 99 格零缺格。翻转（相对 D1 类标签）: 生产列 **0**、greedy_embedding **8**、hungarian_embedding **8**（同一批 8 行, 两嵌入列同号）。

| uid（前 8） | col | 类型 | D1 类 / 机制 | 嵌入两件 → 类 / keyset 全等 |
|---|---|---|---|---|
| 24ff90f9 | 2 | alias_variant | HI / threshold_dilution | E / ✅ |
| 24ff90f9 | 4 | alias_variant | HI / threshold_dilution | E / ✅ |
| 32cfcadb | 2 | alias_variant | HI / threshold_dilution | E / ✅ |
| 32cfcadb | 4 | alias_variant | HI / threshold_dilution | E / ✅ |
| 97176853 | 2 | alias_variant | HI / threshold_dilution | E / ✅ |
| 97176853 | 4 | alias_variant | HI / threshold_dilution | E / ✅ |
| e11338f6 | 4 | alias_variant | HI / threshold_dilution | E / ✅ |
| ea031e89 | 0 | mixed_lang | HI / threshold_dilution | E / ✅ |

- **翻转方向与阶段 A 相反**: 阶段 A 的 5 翻转是 `H → HI`（原可见变盲, 且 5/5 只因类型闸门未计 E）; 阶段 B 的 8 翻转是 **`HI → E`**（原"设计意图缺陷成立而协议无信号"变为"映射标准字段集与原表一致的良性吸收"）。类型全落 `EQUIV_TYPES` 内（alias 7 + mixed_lang 1）⇒ 一旦 keyset 变全等就自动进 E。
- **毒性定性**: 8/8 在嵌入件下 keyset 全等 ⇒ 输出结构无变化, 嵌入件的翻转不是"新增危害", 而是**把稀释型盲区改判为良性等价**; 同时矩阵内 **0 例转为 H** ⇒ D1 的 33 盲区在任意 γ 锚点下仍全不可见（盲区保持, 只是标签从 HI 搬到 E）。
- **严格吸收口径**（injected 表头被映射回原 target canonical）: 33 行中生产件 **22** → 嵌入两件 **30** —— 嵌入件吸收得更多, 与 §4 可见率塌降同向。
- **HI 机制构成（118 全口径, 供 D3 救援先验）**: 生产 silent 15 / dilution 11 → greedy_embedding **silent 31 / dilution 7**, hungarian_embedding **silent 29 / dilution 4**（稀释型大幅转成静默吸收型）。

## 7. P-3 等价稳定性在嵌入件下的观察（非判据）

7 条 D1 等价注入（E）× 3 列 = 21 格零缺格, **零翻转**（保持 `absorbed && canonical_keyset_identical`）。P-3 属编辑距离族预注册条款, 此处只作同口径观察; 阶段 A 的 P-3 判定（四件零翻转）不因本跑改动。

## 8. 红线自查

- **零端点**: `ports_touched = []`（socket 层封死后建立出站连接在构造上不可能; 退出时护栏完整性复核确认未卸装）、`model_service_calls = 0`（脚本无任何服务端调用路径 + AST 作用域检索零 http 客户端）、被拦试连 3 条全部可归因护栏自证三探针（系统调用前抛错, 零字节收发）⇒ **模型装载/编码零联网尝试**。`:8006` 全程零触碰, J7 端点鲁棒性窗未开启。本地推理量单列（16 批 / 496 文本）, 不与端点调用混记。
- **判据冻结**: P-1..P-5 常量写死于脚本常量区, 与阶段 A 同; P-2 按卡**不设过判** —— 工件 `prereg_predicates.P2_embedding_verdict = none`, `p2_findings.no_pass_fail_adjudicated = true`, 本报告不对嵌入臂下"通过/失败"结论。阈值 p05 规则先于打分冻结, 负控重叠与同串对入账后**未回调阈值**。
- **只读 / 独立件**: 阶段 A 工件**未被覆写**（`phase_a_artifact_not_overwritten = true`, `phase_a_sha_unchanged = true` = 执行前后 `7bb268e5da19…` 全等）; D1 底表 + drift 两件 + T2 工件 + 阶段 A 件 sha 全等（`gates.G4.pass` 内含 `after == watch`）; 冻结节点（`tests/test_m1_service.py` / `~/wzh/m1_samples/**` / `frozen_hashes.txt`）零改动, 未触发 REQUEST_UNFREEZE。
- **甲方标识**: 终工件与本报告 `client_identifier_scan = []` 零命中; 逐注入只用 uid（UUID）+ 列号, 矩阵只落类型与状态。
- **git**: 逐路径 add（无 `-A`）, 无 amend; 阶段 A 已交付 commit 不被改写。

## 9. 过程记账

1. **阶段 A 的护栏语义修复在阶段 B 直接生效**: 复用 `d2._install_network_guard` / `guard_self_test` 后, 自证试连不再污染 `ports_touched`, G4 首跑即 PASS（阶段 A 修前为误判 FAIL）。
2. **装载顺序按卡内风险预案执行**: `sentence_transformers` 导入放在护栏**之内**（而非之前）, 以获取"导入期联网亦被拦"的更强自证; 实跑证明该顺序无副作用（本跑脚本全程 wall clock < 30 s, 含 CPU 装载与 496 文本编码; 被拦事件全部可归因自证探针, 该路径贡献 0 次）⇒ 无需按预案把导入上移, **未做任何判据收窄**。
3. **未改阶段 A 判据、未改生产匹配器、未改 schema**: 嵌入件只换打分基; `normalize_header` / canonical 集恒用生产口径, 语料侧控制量与阶段 A 一致。
4. **成本控制**: 阶段 B 与阶段 A 首跑的失败模式（四匹配器统一接口一次性设计）隔离 —— 嵌入件独立脚本 + 复用阶段 A 机器件, 本跑脚本一次写通一次跑通。

## 10. 复算与工件

```bash
# 阶段 B（本件）: exit 0 = 定标有效 + 矩阵完整 + 零端点自证; 重写工件（仅时间戳字段变）
HF_HUB_OFFLINE=1 python3 research/paper_d2_cross_matcher_embed.py
# 阶段 A（前置件, 不受本跑影响）: exit 1 = G1 预注册 τ 失配（卡设计语义）
python3 research/paper_d2_cross_matcher_det.py
```

`payload` 顶层键: `inputs_sha256` / `criterion_provenance` / `model_asset` / `threshold_calibration` / `matchers` / `spectrum` / `ordering_kendall_tau` / `blind_types` / `transition_matrix` / `equivalence_stability` / `p2_findings` / `counts_by_matcher` / `gate_details` / `prereg_predicates` / `redline_self_check`。

## 11. 归主线程（收集与判定分离, 本窗不代拍）

1. **方向性触发已两次入账**（阶段 A τ=0.733; 阶段 B 嵌入族 τ=0.276 / −0.298 + 全盲集合扩张）: R3 降级表述两半句的落笔需区分"盲区消失"与"盲区集合扩张", 且需决定**是否把嵌入族纳入 R3 的匹配器集**（P-2 探索性 ⇒ 纳入即改变判据口径, 属主张层裁定）。
2. **E/HI 类型闸门 vs 翻转毒性**（阶段 A §4 + 本阶段 §6 的 8 例反向翻转）: 谱形改变在两个打分基下都由类型闸门驱动而非新增危害驱动 —— 是否上升为对 D1 三分类定义的方法学主张（涉冻结设计稿 §2）。
3. **弱阈值是打分基性质还是域性质**: 正负控重叠（margin −0.133）+ 25.9% 同串对 ⇒ 若 D3（matched-specificity）要引入嵌入臂, 阈值定标口径需先定（是否剔同串对 / 是否改分位）。
4. D2 两阶段均已产出 → 本窗可收口, 等 autopsy 后排 D3。

## 12. 收据

<!-- SUMMARY-GUARD
artifact: logs/graph/eval/d2_cross_matcher_embed.json
sha256: ed3d3905e42c41ab71d4dfacc64a3609de2dd12d5e20cf9b5b363a90d29d4bbf
claims:
  payload_sha256 = "299ab1c7acfc8b272fce6c1a3bbf18ca01d35810d715cd1b62c3c651f121f950"
  gates.G0_production_reproduces_d1 = true
  gates.G1_threshold_calibration_valid = true
  gates.G3_equivalence_observation_noncriterion = true
  gates.G4_p4_zero_endpoint_and_readonly = true
  gates.G5_transition_matrix_completeness = true
  gates.G6_digest_self_consistency = true
  gates.all_pass = true
  payload.threshold_calibration.threshold_frozen = 0.5439
  payload.threshold_calibration.percentile = 5.0
  payload.threshold_calibration.n_positive_control_pairs = 286
  payload.threshold_calibration.n_negative_control_cross_field = 286
  payload.threshold_calibration.separation_margin_p05_pos_minus_p95_neg = -0.13278
  payload.threshold_calibration.positive_control_distribution.p05 = 0.543866
  payload.threshold_calibration.positive_control_distribution.p75 = 1.0
  payload.threshold_calibration.negative_control_distribution.p75 = 0.556794
  payload.threshold_calibration.negative_control_distribution.p95 = 0.676647
  payload.threshold_calibration.frozen_before_injection_scoring = true
  payload.counts_by_matcher.greedy_production.H = 85
  payload.counts_by_matcher.greedy_production.E = 7
  payload.counts_by_matcher.greedy_production.HI = 26
  payload.counts_by_matcher.greedy_production.total = 118
  payload.counts_by_matcher.greedy_embedding.H = 23
  payload.counts_by_matcher.greedy_embedding.E = 57
  payload.counts_by_matcher.greedy_embedding.HI = 38
  payload.counts_by_matcher.hungarian_embedding.H = 19
  payload.counts_by_matcher.hungarian_embedding.E = 66
  payload.counts_by_matcher.hungarian_embedding.HI = 33
  payload.counts_by_matcher.greedy_production.hi_by_mechanism.absorption_silent = 15
  payload.counts_by_matcher.greedy_production.hi_by_mechanism.threshold_dilution = 11
  payload.counts_by_matcher.greedy_embedding.hi_by_mechanism.absorption_silent = 31
  payload.counts_by_matcher.greedy_embedding.hi_by_mechanism.threshold_dilution = 7
  payload.counts_by_matcher.hungarian_embedding.hi_by_mechanism.absorption_silent = 29
  payload.counts_by_matcher.hungarian_embedding.hi_by_mechanism.threshold_dilution = 4
  payload.spectrum.greedy_production["0.2"].by_type.ocr_similar.visible = 0
  payload.spectrum.greedy_production["0.2"].by_type.ocr_similar.n = 13
  payload.spectrum.greedy_production["0.2"].by_type.mixed_lang.visibility_rate = 0.95
  payload.spectrum.greedy_embedding["0.2"].by_type.ocr_similar.visible = 0
  payload.spectrum.greedy_embedding["0.2"].by_type.mixed_lang.visibility_rate = 0.05
  payload.spectrum.greedy_embedding["0.2"].by_type.date_variant.visibility_rate = 0.3529
  payload.spectrum.greedy_embedding["0.2"].by_type.prefix_noise.visible = 0
  payload.spectrum.greedy_embedding["0.2"].by_type.unit_suffix.visible = 2
  payload.spectrum.hungarian_embedding["0.2"].by_type.ocr_similar.visible = 0
  payload.spectrum.hungarian_embedding["0.2"].by_type.prefix_noise.visible = 0
  payload.spectrum.hungarian_embedding["0.2"].by_type.unit_suffix.visible = 0
  payload.blind_types.greedy_production[0] = "ocr_similar"
  payload.blind_types.greedy_embedding[0] = "ocr_similar"
  payload.blind_types.greedy_embedding[1] = "prefix_noise"
  payload.blind_types.hungarian_embedding[0] = "ocr_similar"
  payload.blind_types.hungarian_embedding[1] = "prefix_noise"
  payload.blind_types.hungarian_embedding[2] = "unit_suffix"
  payload.ordering_kendall_tau.greedy_production.tau_min = 1.0
  payload.ordering_kendall_tau.greedy_embedding.tau_min = 0.276026
  payload.ordering_kendall_tau.hungarian_embedding.tau_min = -0.298142
  payload.ordering_kendall_tau.greedy_embedding.per_gamma["0.5"].tau = 0.771517
  payload.ordering_kendall_tau.greedy_embedding.per_gamma["0.9"].tau = 0.833333
  payload.ordering_kendall_tau.hungarian_embedding.per_gamma["0.2"].tau = -0.298142
  payload.p2_findings.no_pass_fail_adjudicated = true
  payload.p2_findings.ocr_similar_under_embedding.visible_any_gamma = false
  payload.p2_findings.ocr_similar_under_embedding.n = 13
  payload.p2_findings.absorption_maintained_of_33.greedy_production = 22
  payload.p2_findings.absorption_maintained_of_33.greedy_embedding = 30
  payload.p2_findings.absorption_maintained_of_33.hungarian_embedding = 30
  payload.transition_matrix.rows_are_d1_absorption_injections = 33
  payload.transition_matrix.columns[1] = "greedy_embedding"
  payload.gate_details.G5_transition_matrix_completeness.cells_expected = 99
  payload.gate_details.G5_transition_matrix_completeness.cells_missing = 0
  payload.gate_details.G5_transition_matrix_completeness.flip_count_by_matcher.greedy_production = 0
  payload.gate_details.G5_transition_matrix_completeness.flip_count_by_matcher.greedy_embedding = 8
  payload.gate_details.G5_transition_matrix_completeness.flip_count_by_matcher.hungarian_embedding = 8
  payload.gate_details.G0_production_reproduces_d1.n_rows = 118
  payload.gate_details.G0_production_reproduces_d1.n_mismatches = 0
  payload.equivalence_stability.n_equivalence_rows = 7
  payload.equivalence_stability.n_flips = 0
  payload.equivalence_stability.missing_cells = 0
  payload.gate_details.G4_p4_zero_endpoint_and_readonly.ports_touched = []
  payload.gate_details.G4_p4_zero_endpoint_and_readonly.model_service_calls = 0
  payload.gate_details.G4_p4_zero_endpoint_and_readonly.local_inference_batches = 16
  payload.gate_details.G4_p4_zero_endpoint_and_readonly.local_encoded_texts = 496
  payload.gate_details.G4_p4_zero_endpoint_and_readonly.socket_attempts_blocked.n = 3
  payload.gate_details.G4_p4_zero_endpoint_and_readonly.active_connection_probes.all_blocked = true
  payload.gate_details.G4_p4_zero_endpoint_and_readonly.endpoint_violations = []
  payload.gate_details.G4_p4_zero_endpoint_and_readonly.frozen_and_baseline_inputs_unchanged = true
  payload.model_asset.device = "cpu"
  payload.model_asset.torch_threads = 8
  payload.model_asset.weights_bytes = 2271145830
  payload.model_asset.local_files_only = true
  payload.redline_self_check.phase_a_artifact_not_overwritten = true
  payload.redline_self_check.phase_a_sha_unchanged = true
  payload.redline_self_check.client_identifier_zero_entered = true
  payload.prereg_predicates.P4_zero_endpoint_self_proof_phase_b = true
  payload.prereg_predicates.P5_matrix_complete_phase_b_columns = true
END-SUMMARY-GUARD -->
