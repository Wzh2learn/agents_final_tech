# Related Work 贡献边界矩阵 v1

> 状态：投稿/大论文支持件，不替代主稿 Related Work | 更新：2026-10-04
> 来源：`paper/teacher_review_draft_v1.md` §2、`paper/references_v0.md`
> 纪律：只使用仓内已核验条目；不新增 venue、不扩大本文证据范围、不把 future work 写成已有贡献。

## 1 四簇贡献边界

| 簇 | 代表工作（仓内 cite key） | 工作共同关注 | 本文差异与边界 |
|---|---|---|---|
| Meta-evaluation / protocol sensitivity | `amrhein2022aces`, `amrhein2023aceswmt`, `moghe2024acesjournal`, `deviyani2025contextual`, `kendiukhov2026ranking`, `du2026promptranking`, `ross2024goodmetric` | 指标是否能区分真实错误/可接受变体；排名是否随协议轴、提示子集、种子或目标属性变化 | 本文先问协议能否**观测**注入缺陷，再谈指标排序；贡献是 checkpoint visibility profile、silent absorption 与协议敏感性边界，不是提出更强指标 |
| Process-level / hierarchical evaluation | `fan2026agentprocessbench`, `chung2026webstep`, `wang2026gta2` | 从最终结果深入中间过程；用递归/状态轨迹定位工具或 web agent 错误 | 本文复用递归 checkpoint 聚合形式，但增加 deterministic contracts、missing-evidence policy、受控 header 注入与按 family 的可见性分解；不主张层级检测优于扁平，不主张已建立额外定位收益 |
| Mutation testing / fault injection | `cho2025metamorphic`, `tan2026agentchaos` | 通过受控变化或故障注入检验 metric/test 是否注意到缺陷 | 本文保留 killed/surviving 之外的第三种结果 silent absorption，并区分 evaluator blind spot 与 scored layer 不可观测的 invalid mutant；不把合成注入泛化为自然缺陷分布 |
| LLM-as-judge reliability | `zheng2023judge`, `li2025robustjudge`, `li2025scoringbias` | 位置、冗长、自偏好、扰动敏感性等 judge 可靠性问题 | 本文把 judge 限于语义叶，contractible property 走 deterministic check，隐藏 injected ground truth，并披露 judge resolution/sample limits；不声称 judge 可互换或 cell-level agreement |

## 2 与本文主张的直接映射

| 主稿主张 | Related Work 需要保留的差异句 | 当前证据边界 |
|---|---|---|
| 评估协议自身可能看不见缺陷 | 先问 visibility，再问 detection；不能把 metric ranking 当作缺陷可见性 | 95 表 / 118 注入的冻结语料；不外推自然分布 |
| 层级结构提供分解而非更强检测 | 与 GTA-2 的递归聚合相邻，但本文强调 evidence decomposition | matched-FPR 下 `[0,0]` 退化区间；一般多叶条件未证 |
| Silent absorption 是独立结果类 | 与 mutation testing 的 killed/surviving 二分不同 | OCR-like 13/13 absorbed；范围限当前 evaluator |
| Deterministic contract + leakage-protected judge | 与 LLM judge 可靠性文献相邻，但本文不把 judge 当最终 oracle | judge 只评语义叶；cell-level interchangeability 未证 |

## 3 KD / agent distillation 的 future-work 边界

`hinton2015distilling`、`gou2021kdsurvey`、`xu2024kdsurveyllm`、`qiu2025agentdistill`、`liu2025structuredagent`、`chen2026counteraction`、`ma2026mopd` 只能放 Discussion / future work。当前没有学生训练结果，不得把模型矩阵、60 对 DPO 素材或已完成的 146 列 exploratory Q3 review 写成 distillation evidence。正式 KD 主实验仍受 `DATA_NO_GO`、`NOT_IDENTIFIED`、V2-3 与专利门约束。

## 4 投稿前检查

1. Related Work 保留“共同关注—差异—边界”三层结构，不退化为逐篇摘要。
2. `submission_references_arr_www_v1.md` 的 15 条主稿引用集合继续与 References/BibTeX 对账。
3. venue 未核条目继续写 `arXiv preprint`；不得把候选 venue 当已核事实。
4. 主稿不新增外部文献或未核数字；本矩阵只提供写作与审稿导航。
