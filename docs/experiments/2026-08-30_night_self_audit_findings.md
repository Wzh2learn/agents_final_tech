# 夜间自审 findings（Loop D 自审, 2026-08-30 夜卡）

> 性质: findings 清单, 不含"通过"结论（结论权在 Loop C 与用户; self-eval-bias 理由 = 同上下文自评倾向宽容, 故只列发现不裁决）
> 装载: paper-review-check / broken-window-check / self-eval-bias（参照）/ jinrong-docs-sync / verify-before-done

## A. 九项独立审计攻击面预跑（计划文档清单, 逐项发现）

1. 三者关系吸收: docs/34 专利锚点表+技术链+收敛原则在位; **发现 F-A1（polish）**: paper 草稿 S2 未交叉引用专利四型 crosswalk（v2 工件 patent_crosswalk 键在, 草稿未引）。
2. VGRM 主线回潮: S6 = 0.5p 案例, 无主贡献措辞; 无发现。
3. PSO 遗漏: S2 [TODO-T4] + Pareto 现版在位; 无发现。
4. 缺陷可见性遗漏: S1/S2 + fig1 在位; 无发现。
5. 盲锥过度主张: 草稿零"盲锥"字样, 用 visibility profile/blind region; 无发现。
6. 非显著包装正结果: S6 显式非显著 + W1 报告 C2 降级讨论入一页纸; 无发现。
7. 专利公开边界: docs/34 §6 + 蓝图 §6 在位; **发现 F-A7（polish）**: paper/ 草稿缺边界脚注（内部草稿/申请日前禁止公开）, 已在本 commit 补。
8. Graph Loop 覆盖: T1-T8 + W1/W2 + T3/T5 卡在位; **发现 F-A8（注记）**: 蓝图 E2.5（真实 OCR 错误分布）无独立卡——挂 T5 治理后（C4 菜单依赖）, 非静默缺口, 本页纸备查。
9. 只写文档不产工件: W1 三工件+G1-G4+sha 在位; T4/T3/T5 按序列待执行, 非违反; 无发现。

## B. broken-window-check（近 24h 声称完成件 vs 文件事实）

| 声称 | 文件事实 | 判定 |
|---|---|---|
| 三预注册稿 §1 原样引用蓝图判据 | grep 蓝图 C1/C2/C5 成功标准串于三稿 = 命中 | 坐实 |
| T3 卡前提含工件在位验证+解冻范围条款 | 卡 P1/P2 在位 | 坐实 |
| T5 卡门 <10% + 增益阈值 | 卡 acceptance 在位（≤5% 预期 / <10% 门 / ≥50% 增益） | 坐实 |
| W1 卡 P1-P5 + G1-G4 | 卡在位; W1 工件门全过 | 坐实 |
| 引文核验清零 | rw v3 定稿头 + INDEX 行 + arXiv 实查记录 | 坐实 |
| 图稿两图 + Pareto 不造数 | fig1/fig2 在位; Pareto 当时 SKIP 声称与现 current_v0 标注一致 | 坐实 |
| **INDEX figures_paper 行"Pareto 待 T4"** | current_v0 已产（标注现版） | **漂移 D-B1: 行文本需更新（本 commit 修）** |
| W2 卡预算 120≤200 | 卡 §P3 算式在位 | 坐实 |

## C. 治理体检

- docs_lint 本地: 预期 FAIL[4]（sync_skills 本机 CRLF 结构性, 08-23 教训在案, GB10 为准）; 其余四项（INDEX 覆盖/死链/状态头/台账防漂移）以本次运行输出为准, 新失败即登记。
- 漂移扫描: 运行 governance_drift_scan.py, 命中自动登记 docs/29（设计行为）。
- skill 注册表一致性: 本机结构性不可跑, GB10 侧 08-29 77/77 在案。

## D. 汇总

blocking 级: 0（S2 两 blocking-占位为草稿待补项, 已入 draft 注记, 非治理违反）。
polish/漂移: F-A1, F-A7, D-B1（均本 commit 处置或占位）; F-A8 备查。
