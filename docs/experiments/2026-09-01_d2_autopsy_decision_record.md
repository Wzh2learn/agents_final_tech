# D2 跨匹配器窗 Autopsy 决策记录

- 日期: 2026-09-01 | 尸检: Loop D 主线程（零端点）| 执行: Loop A（GB10, tmux）
- 窗口: TASK-20260831-D2（首跑 + 改期 #1 → R2 两阶段: 确定性三件 + bge-m3 嵌入）
- 状态: 收口绿态, 判定请求 ×2 已圈选（09-01, §5 注记）; 判据文本零改动、不溯及

## 0. 派发与证据链

- 首跑 `tmux loop-a-d2`（08-31 22:22 派发, 标准模板: `cat scripts/graph/loop_a_exec_constraints.md <卡> | codex exec --dangerously-bypass-approvals-and-sandbox --profile loopa-exec`）→ 令牌耗尽 629,428 tokens 零产出 → 改期 #1（卡加编两阶段, 83cb9ae, ≤2 纪律内）。
- R2 `tmux loop-a-d2-r2`（08-31 23:03 派发, 同模板）→ 阶段 A 交付 7b49fb3 / 阶段 B 交付 f0b3a89; 观察器 `/tmp/d2r2_watcher.sh`（唯一会话名避前缀坑）09-01 00:20 SESSION_ENDED attempts=16 自删, done 件 `logs/graph/eval/loop_a_d2_r2_done.json` 落盘, crontab 自清。
- 三方对齐: 11df397（local=origin=GB10, GB10 未先 pull 分叉已合, 无内容冲突; 在制件 6bf3391 入账）。
- 主线程抽验: 阶段 A `research/paper_d2_spotcheck_recompute.py`（bbc4ae7, 4/5, 唯一 FAIL=τ 口径分歧本身, 裁定 b 后自洽）; 阶段 B `research/paper_d2_phase_b_spotcheck_recompute.py` **12/12 全 PASS**（`logs/graph/eval/d2_phase_b_spotcheck_recompute.json`）。

## 1. Findings（先行）

- **F-D2-1 τ 门失败属实 + 0.8286 撤销（教训 #4）**: 裁定 b 维持执行口径（并列取平均名次 + tau-b）, 归一化族 τ=[1.0, 0.7333, 0.8571, 1.0, 1.0], τ_min=0.7333<0.8; 0.8286 五种算法变体不可复算（疑 (0.8+0.8571)/2）, 已撤销销账（THREADS #D2-TAU-METHOD-DISCREPANCY 更正注记 + #LESSON-UNREPRODUCIBLE-NUMBER-4 + docs/29 A18 守卫缺口）。实质证据不受影响: 打分轴单轴驱动, date_variant 5 例 H→HI（表头 40-48 字符, 归一化稀释, 边际 ΔH 0.5→0, 率 0.7059→0.4118）[d2_cross_matcher_det.json]。
- **F-D2-2 确定性族盲集恒同（半句 A 否定）**: 4 匹配器全盲集合恒 = [ocr_similar], 交集=并集; 分配轴零翻转（Hungarian vs greedy τ=1.0）[d2_cross_matcher_det.json]。
- **F-D2-3 嵌入打分基谱整体塌降 + 盲集单调扩张（方向性触发第二次）**: H/E/HI 85/7/26 → greedy_embedding 23/57/38 / hungarian_embedding 19/66/33; τ_min vs 生产 0.276026/−0.298142; 盲集 {ocr}→{ocr,prefix}→{ocr,prefix,unit}; 但 ocr_similar 13/13 在六件事/两种打分基/任意 γ 恒零可见 → 半句 B 获第二打分基支持; 须区分「盲区消失 = 否」与「盲区范围移动 = 是」[d2_cross_matcher_embed.json]。
- **F-D2-4 翻转全为良性 HI→E, 零例转可见**: 33×3=99 格零缺格, 翻转 0/8/8, 8 例全 HI(threshold_dilution)→E（7 alias + 1 mixed_lang, keyset 全等）; 严格吸收 22/33→30/30/33 口径 = absorbed 字段; HI 稀释先验 11 → 7/4（供 D3 救援）[d2_cross_matcher_embed.json]。
- **F-D2-5 弱门控（定标诚实入账）**: 阈值 = schema 正控 p05 0.5439（先于注入打分冻结, 未回调）; 负控 p75 0.5568 > 阈值, margin −0.13278, 正控含 74/286 同串对 → 嵌入臂若入 D3 须先定标尺 [d2_cross_matcher_embed.json]。
- **F-D2-6 流程发现**: ① 首跑令牌耗尽 = 单跑范围过大 → 两阶段切分 + 增量写脚本有效（阶段 A 独立绿态下限兑现）; ② 观察器 tmux `-t` 前缀匹配坑以唯一会话名修复（R2 观察器全程正常）; ③ GB10 未先 pull 即提交致分叉 → 合并无冲突, 三方对齐纪律重申「先提交在制件再 pull」; ④ P-2「探索性无过判」预注册设计有效: 全门 PASS 但不判过判, 证据与判据分离。
- **F-D2-7 预注册不完善项（裁定入账）**: R3 降级条款未预期「盲区范围移动」须与「盲区消失」区分; 条款与证据失配如实入账（判据文本零改动）[THREADS #RULING-TAU-B-R3-FALLBACK ③]。
- **F-D2-8 扫描词表假阳性（非阻断）**: `client_identifier_scan` 的 `sample_` 命中脚本常量名 `NEG_SAMPLE_MOD`, 工件本体干净; 是否收严（要求 `sample_` 后接数字）挂治理备查, 不立卡。

## 2. Claim Set v2 状态更新

- **R3 可见性边界机制**: 降级条款已适用（用户 09-01 裁定, Claim Set v2 适用注记在案）——半句 A 不入论文（F-D2-2）; 半句 B 成立且获第二打分基支持（F-D2-3）; 打分轴敏感性（长度归一化稀释长表头）入边界条件节。阶段 B 盲集扩张与半句 A 适用域的调和 = 判定请求 §5-①。
- **边界条件节素材（三件）**: ① 打分轴敏感性（date_variant 5 例, 机制在 det 工件）; ② 嵌入打分基谱塌降 + 盲集范围移动（探索性, 无过判）; ③ 弱门控定标（正负控重叠 + 同串对）。
- **R1/R2**: D2 不削弱——R1 谱以生产匹配器为准, 确定性族内谱形跨匹配器稳定（F-D2-2）; R2 定位轴与匹配器无关。PSO/J7/:8006 与本窗无关。
- **D1 决策承接核销**: DR-3（D2 迁移矩阵验收）完成 = F-D2-4; DR-5（稀释 11 例入 D3 救援先验）数据在案 = HI 稀释先验 11→7/4。

## 3. 决策（DR）

- **DR-D2-1** R3 论文落笔: 冻结在适用注记, 待 §5-① 圈选后动笔（T7 衔接）。
- **DR-D2-2** 嵌入族定位: 默认不入 R1/R2 主谱（不同打分基）, 只入边界条件/探索节; 是否纳入 R3 匹配器集属主张层 = §5-① 一并裁。
- **DR-D2-3** D3 卡前置: 嵌入臂若引用须先定标尺（剔同串对/分位敏感性, 零端点部分可先行入卡）= §5-②。
- **DR-D2-4** INDEX 状态翻绿（本 commit）: 定稿卡「执行中」→「收口绿态（autopsy 完成）」; 阶段 A/B 报告「待 autopsy」→「autopsy 完成」。
- **DR-D2-5** 治理: 守卫缺口已登记 docs/29 A18（机械强制扩展待方案）; F-D2-8 挂备查不立卡。
- **DR-D2-6** 窗口纪律执行状况: 改期 #1 与观察器前缀坑补录获用户批准; 分叉已对齐; 收集与判定分离守住（P-2 无过判, 判定全部留本记录与用户圈选）。

## 4. 红线自查（窗口级）

- 零端点: 两阶段 `ports_touched=[]` / `model_service_calls=0`（阶段 B 本地推理 16 批 496 文本单列, 护栏先装, 3 拦截事件全归因自证探针）; :8006 零触碰（五条件窗未使用）; J7 未开; :5050/生产配置零改。
- 判据冻结: P-1..P-5 零改动; τ 裁定只撤不可复算数字, 判据文本零改动不溯及; R3 降级条款按预注册适用。
- 只读: D1 底表 / drift / T2 / 阶段 A 工件 sha 全等（抽验 #11 复算匹配）; 冻结节点零改动; 甲方标识零命中; 专利终态件未触。
- 质量基线: pytest 402 passed / 13 skipped; docs_lint 0/0（GB10 为准）; 对外零发送。

## 5. 判定请求（≤2, 待用户圈选）

**① R3 半句 A 适用域与盲集扩张表述**（F-D2-3 与已裁半句 A 的调和）:
- a)（推荐）维持裁定: 半句 A 不入论文; 盲集扩张作为探索性发现入边界条件节, 表述为「盲区范围在不同打分基间可能移动（扩张）, 但未有任何类型转可见; 全盲类型的存在跨打分基稳健」——判据零改动, 证据表述最保守;
- b) 半句 A 精化重入: 「核心盲点位（ocr_similar）匹配器无关, 盲集范围随打分基变动」, 判据措辞需补更正注记;
- c) 全缓: 待 D3/D4 证据齐后一并落笔。

**② D3 嵌入臂弱门控定标**（F-D2-5）:
- a)（推荐）D3 卡先带零端点定标诊断段（剔同串对/换分位/域性质判别）, 再定嵌入臂引用方式;
- b) D3 不引嵌入臂, 定标缓至 Phase C 统计冻结时处理。

> [09-01 圈选 | 用户] ①=a: R3 半句 A 维持裁定不入论文; 盲集扩张作单臂探索性发现入边界条件节, 冻结措辞: 「盲区范围可随打分基移动（{ocr}→{ocr,prefix}→{ocr,prefix,unit}, 单调, 无类型转可见）; 全盲类型存在跨打分基稳健（ocr_similar 13/13 恒零可见）」。不升主张, 判据文本零改动。②=a: D3 卡先带「零端点定标诊断段」（弱门控三项证据重诊断嵌入阈值标尺; 诊断结论按预注册映射决定嵌入臂引用方式 = 校准后引用 / 降为敏感性分析 / 不引并记录理由）; D3 主体 = matched-FPR + 阈值稀释救援通道, 统计口径引 Phase C 草案 §2。F4 分叉处置批准, 三方纪律常备。

## 6. 下一步（圈选后）

1. D3 matched-specificity 拟卡: 零端点 clean controls 定标先行（含 ② 圈选内容）; judge 重打分 = 端点窗白天（:8004 主, :8006 按五条件）。
2. D3 后停一次 autopsy → D4（=原 T3, 解冻条款: 仅 validation split, 完成即恢复冻结）。
3. T5 视觉降 P2 按需另批; J7 不开; Phase B 文献队列（venue DBLP 核验）与 Phase C 统计冻结按既有排期。

<!-- SUMMARY-GUARD
artifact: logs/graph/eval/d2_phase_b_spotcheck_recompute.json
sha256: 49ca09315c605ce5041cf65a1f133f7d72ae4b5e5ea9c6e622f19889c0630c86
claims:
  n_checks = 12
  n_pass = 12
  all_pass = true
END-SUMMARY-GUARD -->
