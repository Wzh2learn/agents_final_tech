# D2 跨匹配器验证报告 · 阶段 A（确定性三件, 零端点）

> 卡号: TASK-20260831-D2（定稿 + 加编两阶段切分）| 执行者: Loop A（GB10）| 执行日期: 2026-08-31
> 判据冻结: 卡 §2 预注册 P-1..P-5 + 卡 §redlines（执行后不溯及）
> R3 降级表述（引用源）: 「D2 跨匹配器若谱形显著改变 → 改为"盲区位置匹配器相关, 谱结构（存在全盲类型）匹配器无关"」
> 底表: `logs/graph/eval/d1_mutant_validity_audit.json`（只读, all_pass=true）| 工件: `logs/graph/eval/d2_cross_matcher_det.json`
> 脚本: `research/paper_d2_cross_matcher_det.py` | 风险: 低（零端点, 冻结件只读）
> 本报告只收集与判定工件内门; 主张层（论文含义）判定归主线程 autopsy（收集与判定分离）。

## 1. 执行结果

阶段 A 四件（编辑距离族）全部跑通, 工件 **payload 逐字节确定**（两次实跑 `payload_sha256` 全等 = `caf1e3bdea4621c685f184d308bdd9123c843f20fb00909fb5a945ef3d0c9558`; 摘要在 payload 收口后计算, 承 W2 f1bf00b 教训）。

门态: **G0/G3/G4/G5/G6 全 PASS**, **G1 FAIL**, `all_pass = false`, 脚本 exit 1（= 按卡「任一门失败上报, 不静默处置」设计语义, 非管线故障）。

- **G0 复现门 PASS**: 生产贪心件逐条复算 D1 底表 118 注入 × 6 字段 **零失配**, 三分类 **85/7/26**、吸收行 **33**、锚点按型检出（alias 36 / date 12 / mixed 19 / **ocr 0** / prefix 13 / unit 5）全部与 D1 一致 → 跨匹配器比较的分母与口径可信。
- **G1（P-1）FAIL — 半真半假**: ocr_similar 全盲存续 **成立**（四件皆 0/13, 任意 γ 下可见数恒 0）; 谱排序 τ ≥ 0.8 **不成立**（归一化列 τ_min = **0.733333** @ γ=0.3）。→ **R3 降级条款按预注册自动生效并入本报告, 零改判**。
- **G3（P-3）PASS**: 7 条等价注入在四件下 **零翻转**（保持吸收-等价）。
- **G4（P-4）PASS**: ports_touched = **[]**, model_calls = **0**, 冻结件与底表前后 sha 全等, 甲方标识终工件 **零命中**。
- **G5（P-5）PASS**: 33 吸收注入 × 3 预注册列 = **99 格无缺格**（含补充列 132 格亦无缺格）, 矩阵内翻转 **0**。
- **G6 PASS**: digest 重读复算自洽。

**方向性结果已触发**（卡内红线注记 + THREADS `#D2-DIRECTIONAL-TRIGGER`: τ<0.8 = 记账后立即上报, 不等 autopsy 排期）→ 见 §4 与本报告 §5 汇报。

## 2. 匹配器矩阵（打分 × 分配 两轴分解）

唯一变量 = 打分口径 × 分配算法; canonical 字段集与归一化恒用生产 `normalize_header`（语料侧控制量）。

| 件 | 打分 | 分配 | 预注册 | H/E/HI | τ_min vs 生产 | 全盲类型 |
|---|---|---|---|---|---|---|
| greedy_production | 生产档位（绝对 ed≤1） | 生产贪心 `map_headers` | ✅ | 85/7/26 | 1.0（自反） | ocr_similar |
| greedy_normalized | 相对 ed/max_len ≤ 0.20 | 生产贪心 | ✅ | **80/7/31** | **0.733333** | ocr_similar |
| hungarian_production | 生产档位 | Hungarian 全局最优（T6 在库件） | ✅ | 85/7/26 | 1.0 | ocr_similar |
| hungarian_normalized | 相对 ed | Hungarian | 补充列 | **80/7/31** | 0.733333 | ocr_similar |

归一化打分带冻结口径: 复用生产档位带（含 `_SUSPECT_KW` 守卫）, 仅把编辑距离档改为 `1 + (1 − ed/max_len)`, 合格条件 `min_len≥3 且 (ed≤1 或 rel≤0.20)` = 生产一档的**严格超集**。

## 3. 可见性谱（锚点 γ=0.2, 可见数/注入数）

| 类型 | 注入数 | greedy_prod | greedy_norm | hung_prod | hung_norm |
|---|---|---|---|---|---|
| alias_variant | 47 | 0.7660 (36) | 0.7660 (36) | 0.7660 (36) | 0.7660 (36) |
| date_variant | 17 | 0.7059 (12) | **0.4118 (7)** | 0.7059 (12) | **0.4118 (7)** |
| mixed_lang | 20 | 0.9500 (19) | 0.9500 (19) | 0.9500 (19) | 0.9500 (19) |
| **ocr_similar** | 13 | **0.0 (0)** | **0.0 (0)** | **0.0 (0)** | **0.0 (0)** |
| prefix_noise | 16 | 0.8125 (13) | 0.8125 (13) | 0.8125 (13) | 0.8125 (13) |
| unit_suffix | 5 | 1.0000 (5) | 1.0000 (5) | 1.0000 (5) | 1.0000 (5) |

**单轴驱动**: 五类数字在四件下逐字节不动, 唯一变动 = `date_variant`（12→7）。γ 网格全表见工件 `payload.spectrum`。τ 逐 γ: 归一化列 γ=0.2 → 1.0, γ=0.3 → 0.733333, γ=0.5 → 0.857143, γ≥0.7 → 1.0（τ_mean 0.918）。γ=0.3 失配机理: 生产件该 γ 下 date_variant 升至首位（0.6471）而归一化件被压至第 3 位 → 13 同序 / 2 逆序 / 15 对 → τ-b = 11/15 = 0.733333（人工独立复算同值）。

## 4. 迁移矩阵与谱形改变的毒性定性（DR-3 验收）

**33 条 D1 吸收注入（E7 + HI26）× 匹配器**: 四件全表 **零翻转** —— D1 认定的盲区在所有测试匹配器下**恒为盲区**（吸收状态单调保持）。

**新增盲区来自生产件 H 类的 5 条迁移**（非矩阵内行, 故与"零翻转"不矛盾）:

| uid | col | 类型 | dH 生产 → 归一化 | 正确字段? | keyset 不变? | 良性吸收 | 仅因类型闸门未计入 E |
|---|---|---|---|---|---|---|---|
| 16ebd25a | 2 | date_variant | 0.5 → 0.0 | ✅ | ✅ | ✅ | ✅ |
| 1860a2e9 | 2 | date_variant | 0.5 → 0.0 | ✅ | ✅ | ✅ | ✅ |
| 1e712660 | 2 | date_variant | 0.5 → 0.0 | ✅ | ✅ | ✅ | ✅ |
| 38eb9da5 | 2 | date_variant | 0.5 → 0.0 | ✅ | ✅ | ✅ | ✅ |
| d423c6ef | 0 | date_variant | 1.0 → 0.0 | ✅ | ✅ | ✅ | ✅ |

**要点（交 autopsy 判读, 本报告不下主张层结论）**: 5/5 翻转全部是**良性正确吸收**（漂移表头被映射到**正确** canonical 字段且标准字段集不变）, 且 5/5 只因类型不在冻结 `EQUIV_TYPES = {alias_variant, mixed_lang, prefix_noise}` 内而未计入 E 类。即: **τ 失败的谱形改变幅度由 E/HI 的类型闸门驱动, 而非由新增危害驱动**（`visibility_gained_HI_to_H = 0`, 无一例由不可见转为可见）。机理 = 长英文表头（len 18–60）下绝对 ed≤1 过严, 改相对阈值后这些漂移本就可正确映射。

**轴归因**: 分配轴（贪心→Hungarian）**零翻转 / τ=1.0** → 谱对分配算法不敏感; 打分轴（绝对→相对 ed）**5 翻转 / τ=0.733** → 谱对打分口径敏感。

**HI 机制构成随件变化**（供 D3 救援先验参考）: 生产件 silent 15 / dilution 11; 归一化件 silent **21** / dilution 10。

## 5. R3 判据对照

| 降级条款半句 | 本窗证据 | 判定 |
|---|---|---|
| 「盲区位置匹配器相关」 | 全盲集合在四件下恒为 `[ocr_similar]`, 交集 = 并集 = {ocr_similar}, 集合完全相同 | **不支持**（位置未随匹配器移动） |
| 「谱结构（存在全盲类型）匹配器无关」 | 存在全盲类型这一结构跨全部四件存续 | **支持** |

实际改变的是**非全盲类型的可见率与名次**（date_variant 0.7059→0.4118, γ=0.3 下名次 1→3）, 即谱排序层面显著改变而全盲位置不动。按预注册, P-1 τ 条款不满足 → R3 降级表述自动生效入报告; 但降级表述的第一半句在本窗证据下**不成立**, 主张层表述如何落笔归 autopsy（见 §7 待拍板项）。

## 6. 红线自查

- **零端点**: `ports_touched = []`（socket 层封死后建立出站连接在构造上不可能, 退出时护栏完整性复核确认未被卸装）; `model_calls = 0`; 本卡全程未使用 :8006, J7 端点鲁棒性窗未开启。AST 作用域检索: 本窗脚本 + 自有导入链（D1/T2/T6）**零 http 客户端**; 生产匹配器 `scripts/m1_statement_parser.py` 自带 OCR/VLM helper 故列作用域外并逐条披露（urllib/subprocess 12 处）, 其「本窗从未调用」由 socket 封死 + 试连自证 + `hasattr` API 存在性断言三重证明。
- **试连披露（非端点使用）**: 护栏自证主动打 `:8004` 共 4 次（create_connection / getaddrinfo / socket.connect / 模块级）, 全部在系统调用前抛 `RuntimeError` 拦截, **零字节收发**; 与 D1 跑同一试连并记 `ports_touched=[]` 口径一致, 已在工件 `socket_attempts_blocked_disclosure` 逐事件披露, 自证来源之外的尝试 = 0。
- **判据冻结**: P-1..P-5 常量写死于脚本常量区, 执行后零改动; G1 失败按卡内 `on_violation` 走 R3 降级条款, 未做任何静默改判或阈值回调。
- **只读**: D1 底表 + drift 三件 + T2 工件 + T6 脚本执行前后 sha256 全等（`frozen_and_baseline_inputs_unchanged = true`）; 冻结节点零改动。
- **甲方标识**: 终工件（含全部 claim 字段）`client_identifier_scan = []` 零命中; 逐注入只用 uid + 列号。
- **git**: 逐路径 add, 无 `-A`, 无 amend。

## 7. 过程记账（含一处自证护栏缺陷, 已修）

1. **护栏自证反噬 G4（本窗实修）**: 初版 `_BlockedSocket.connect()` 把「被拦下的尝试端口」记进 `PORTS_TOUCHED`, 而 `guard_self_test()` 按设计主动打 `:8004` 验证拦截生效 → 自证试连被当作端点使用, G4 误判 FAIL（`ports_touched=[8004]`）。修法是分离两个语义: `ports_touched` = 实际建立的出站连接（护栏封死 → 恒空）, 被拦尝试单列 `socket_attempts_blocked_disclosure` 全披露; 并补退出时护栏完整性复核（防中途卸装）+ 自证来源外尝试必须为零 → **判据强度净增, 非放宽**。教训同族 = 机械强制层要防的"声明摘要 ≠ 存储工件": 自证件若把自己的探针算成违规, 第一次 FAIL 会被误读成红线事故。
2. **一次性分析脚本的链式比较陷阱**: 现场取证用 `prod[k]['class']!='H'==False` 被 Python 链式比较吃掉, 恒假 → 首版机理统计误报「0 翻转」。交付脚本内无此写法（用 `==`/`in` 显式判类), 但同一坑第二次出现 → 按 Hook Escalation 阶梯记教训, 是否上机械强制归治理线。
3. **阶段切分生效**: 首跑令牌耗尽（629k 零产出）的失败模式由加编的「确定性三件先行」阻断 —— 阶段 A 独立跑通并交付, 嵌入件不作本跑阻塞项。

## 8. 阶段 B 状态

阶段 B（bge-m3 嵌入匹配器, 预注册 P-2 探索性无过判, 独立工件 `logs/graph/eval/d2_cross_matcher_embed.json`）**未在本跑产出**: 阶段 A 交付后本窗收口, 按卡内「若上下文不足则独立派发, 记账不算新改期」处理。资产前置证伪在位（`~/wzh/models/hf/bge-m3` config + 权重 + sentence-transformers 布局）。

## 9. 复算与工件

```bash
python3 research/paper_d2_cross_matcher_det.py   # exit 1 = G1 预注册失配（设计语义）; 重写工件
```

工件顶层 `gates` / `payload.gate_details`（G0/G1/G3/G4/G5 逐门明细）/ `payload.prereg_predicates` / `payload.sha_before`。

## 10. 收据

<!-- SUMMARY-GUARD
artifact: logs/graph/eval/d2_cross_matcher_det.json
sha256: 7bb268e5da19590c9f58e71e293c3b66e4e5071f53932b41792ec8fb0ea1f146
claims:
  payload_sha256 = caf1e3bdea4621c685f184d308bdd9123c843f20fb00909fb5a945ef3d0c9558
  gates.G0_production_reproduces_d1 = true
  gates.G1_p1_blind_persistence_and_tau = false
  gates.G3_p3_equivalence_stability = true
  gates.G4_p4_zero_endpoint_and_readonly = true
  gates.G5_p5_transition_matrix_completeness = true
  gates.G6_digest_self_consistency = true
  gates.all_pass = false
  payload.counts_by_matcher.greedy_production.H = 85
  payload.counts_by_matcher.greedy_production.E = 7
  payload.counts_by_matcher.greedy_production.HI = 26
  payload.counts_by_matcher.greedy_production.total = 118
  payload.counts_by_matcher.greedy_normalized.H = 80
  payload.counts_by_matcher.greedy_normalized.E = 7
  payload.counts_by_matcher.greedy_normalized.HI = 31
  payload.counts_by_matcher.hungarian_production.H = 85
  payload.counts_by_matcher.hungarian_production.HI = 26
  payload.counts_by_matcher.hungarian_normalized.H = 80
  payload.counts_by_matcher.hungarian_normalized.HI = 31
  payload.spectrum.greedy_production["0.2"].by_type.ocr_similar.visible = 0
  payload.spectrum.greedy_production["0.2"].by_type.ocr_similar.n = 13
  payload.spectrum.greedy_production["0.2"].by_type.date_variant.visibility_rate = 0.7059
  payload.spectrum.greedy_normalized["0.2"].by_type.date_variant.visibility_rate = 0.4118
  payload.spectrum.hungarian_production["0.2"].by_type.date_variant.visibility_rate = 0.7059
  payload.spectrum.hungarian_normalized["0.2"].by_type.date_variant.visibility_rate = 0.4118
  payload.ordering_kendall_tau.greedy_production.tau_min = 1.0
  payload.ordering_kendall_tau.greedy_normalized.tau_min = 0.733333
  payload.ordering_kendall_tau.hungarian_production.tau_min = 1.0
  payload.ordering_kendall_tau.hungarian_normalized.tau_min = 0.733333
  payload.gate_details.G1_p1_blind_persistence_and_tau.blind_gate_pass = true
  payload.gate_details.G1_p1_blind_persistence_and_tau.tau_gate_pass = false
  payload.gate_details.G1_p1_blind_persistence_and_tau.r3_fallback_engaged = true
  payload.r3_assessment.blind_intersection_prereg_family[0] = ocr_similar
  payload.r3_assessment.blind_set_identical_across_prereg_family = true
  payload.matcher_class_transitions.greedy_normalized.n_flips = 5
  payload.matcher_class_transitions.greedy_normalized.visibility_lost_H_to_HI = 5
  payload.matcher_class_transitions.greedy_normalized.visibility_gained_HI_to_H = 0
  payload.matcher_class_transitions.greedy_normalized.n_benign_correct_absorption = 5
  payload.matcher_class_transitions.greedy_normalized.n_blocked_from_E_only_by_frozen_type_rule = 5
  payload.matcher_class_transitions.hungarian_production.n_flips = 0
  payload.r3_assessment.axis_attribution.assignment_axis_hungarian_flips = 0
  payload.r3_assessment.axis_attribution.scoring_axis_normalized_flips = 5
  payload.transition_matrix.rows_are_d1_absorption_injections = 33
  payload.gate_details.G5_p5_transition_matrix_completeness.cells_missing = 0
  payload.gate_details.G5_p5_transition_matrix_completeness.cells_expected_prereg = 99
  payload.equivalence_stability.n_equivalence_rows = 7
  payload.equivalence_stability.n_flips = 0
  payload.zero_endpoint.ports_touched = []
  payload.zero_endpoint.model_calls = 0
  payload.redline_self_check.client_identifier_zero_entered = true
  payload.redline_self_check.frozen_and_baseline_inputs_unchanged = true
  payload.gate_details.G0_production_reproduces_d1.n_mismatches = 0
  payload.gate_details.G0_production_reproduces_d1.n_rows = 118
END-SUMMARY-GUARD -->

---

## 附节 · 阶段 B 已产出（2026-08-31 同窗续跑, 本文件既有正文零改动）

本报告 §8「阶段 B 未在本跑产出」自本附节起失效（原文保留作审计痕迹, 不覆写）: 阶段 B 已在同会话续跑完成并独立交付 —— 脚本 `research/paper_d2_cross_matcher_embed.py`, 工件 `logs/graph/eval/d2_cross_matcher_embed.json`（payload_sha256 `299ab1c7acfc…1f950`, 全门 PASS, 双跑一致）, 报告 `docs/experiments/2026-08-31_d2_cross_matcher_phase_b.md`。

阶段 B 对阶段 A 结论的两点补充（细节与判读归该报告）:

1. **第二打分基下 `ocr_similar` 仍未被照亮**（0/13, 任意 γ）→ §5 第二半句「谱结构（存在全盲类型）匹配器无关」由编辑距离族扩展到语义嵌入族; D1 的 33 盲区行在嵌入两件下 **0 例转为可见**。
2. **盲区集合随打分基单调扩张而非平移**: 全盲集合 生产/归一化族 `{ocr_similar}` → greedy_embedding `{ocr_similar, prefix_noise}` → hungarian_embedding `{+ unit_suffix}`; 且嵌入臂的 8 次翻转方向与阶段 A 相反（`HI(threshold_dilution) → E`, 8/8 keyset 全等）→ 阶段 A §4「谱形改变由 E/HI 类型闸门驱动, 非新增危害驱动」在第二打分基下同向复现。
