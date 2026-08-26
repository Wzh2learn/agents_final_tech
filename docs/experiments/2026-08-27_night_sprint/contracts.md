# Sprint contracts · 08-27 夜间科研（骨架 v2.2 落地 + 决定性实验备战）

## T1 噪声体制实验设计稿
交付物: docs/experiments/2026-08-27_noise_regime_exp_design.md（台账 #12 设计稿 + 窗口卡草稿）
验收谓词:
- 五节必备全在（预注册 / 前提假设清单 / 交互假设检查 / 工件清单 / 回滚口径）
- 预注册预测节含机械判据（噪声档位↑ → 无门控臂退化率单调升 ∧ 门控臂降幅有界 ε; 两臂再同 → 转扩语料不恋战）
- 噪声三档 a/b/c 定义 + OCR 第四档预留不入首批注记
- 改动面清单: vgmc_exp1.py 仅加 --noise 注入层 ≤50 行（列函数级改动点, 不写码）
- 窗口卡草稿在文末（待批, 今晚不开窗）
范围外: 不执行任何实验 / 不改 vgmc_exp1.py / 不动生产

## T2 小 B 盲锥章节骨架
交付物: docs/experiments/2026-08-27_blind_cone_chapter_skeleton.md
验收谓词:
- 五节骨架: 问题定义 → 盲锥测度（命题 2）→ 注入分类学与 crosswalk → K2 v2 实证 → 局限与 C4 衔接
- 图清单三张: 数据源=checkpoint_discrimination_tables_v2.json, 每张含 schema + caption + 数字溯源行
- 实证数字全部带工件路径（75/95, 96/118, 六类谱, OCR 13/13）
- §5.3.3 口径注记原样携带
范围外: 不写正文 / 不画 / 不跑新实验 / 骨架正文（侧线资产）不碰

## T3 缺工具设计稿两件
交付物: docs/experiments/2026-08-27_bandit_gate_v0_design.md + docs/experiments/2026-08-27_submodular_rho_protocol.md
验收谓词:
- bandit 稿: 样本源审计结论（生产 23 + 实验 53 + replay 扩展, 够/不够一句裁定）+ Thompson 于 (τ,ε) 网格设计 + DPO 薄注记
- ρ 稿: 复用实验 1 流水零额外 LLM 证明 + 子集顺序消融协议 + ρ 计算式
范围外: 不写实现代码 / 不动 #9 #11

## T4 Loop C 差分审计
交付物: docs/experiments/2026-08-27_night_sprint/evidence_t4_audit.md
验收谓词:
- 骨架数字 7 条逐条对工件（每条: 骨架值 / 工件值 / 命令 / 一致?）
- 4/42 vs 4/53 裁定一行（以 vgmc_exp1_results.json 为准）
- mapping 刷新状态 × git log 交叉核对行
范围外: 骨架正文只读不改（侧线资产）
