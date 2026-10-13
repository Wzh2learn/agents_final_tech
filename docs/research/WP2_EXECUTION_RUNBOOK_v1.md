# WP-2 执行手册 v1（四步法：穷举 → 自下而上 → 量变排序 → 单门拍板）

> 2026-10-13 | 状态：READY_TO_EXECUTE_AFTER_APPROVAL（零模型调用；本文档本身不授权运行）
> 依据：评测协议 v1、蓝皮书 §2、WP1 完成记录（freeze 清单）、split dry-run 收据。

## 1. 穷举：WP-2 的全部子项（S0–S11）

| # | 子项 | 性质 | 现状 |
|---|---|---|---|
| S0 | 预冻结软件修复（unit-gate 对齐 / 数字渲染加固 / 泄漏句补齐） | 软件·Loop A | 已列入 freeze 清单，未派发 |
| S1 | 题本扩建：>=2 题/原点（pilot 需要 2 题/原点；当前 1 题/原点） | 软件·确定性 | 待办（176 origins 有 >=2 可用行） |
| S2 | target_unit 赋权 + item freeze（目标单位/时期/gold 规则冻结） | 设计决定+冻结 | 待办 |
| S3 | 分组冻结（origin→role：pilot 8 / reserve 8 / dev >=2 / history >=4） | 确定性 | dry-run 已做（DRAFT） |
| S4 | 经验采集（history：8 episodes / >=4 origins，<=40 调用内） | 需 actor | 待 MODEL_GO |
| S5 | 开发段（4 题 / >=2 origins；S 臂规则锁死） | 需 actor | 待 MODEL_GO |
| S6 | 臂上下文构建（E/C <=5% token 差；盲 id；S 规则包） | 确定性 | 规格就绪 |
| S7 | 预注册冻结（全哈希：协议/题集/分组/actor/checker/分析脚本） | 冻结 | 骨架已有 |
| S8 | C 预检审计（pre-result） | 审计 | 待 S7 |
| S9 | pilot 执行（4x16x2=128 episodes，<=256 调用；总 cap 300） | 需 actor | 待批准 |
| S10 | 分析（origin 级配对 E-B/E-C/E-S/C-B + 成本） | 确定性 | 脚本待写（S0 同批） |
| S11 | 门裁决与报告（CONTINUE/STOP/UNDETERMINED） | 裁决 | 待 S9/S10 |

## 2. 自下而上核验表（每项四个便宜问题）

| # | 独立目标/许可？ | 下一个便宜动作 | 前置 | 干净停止点 |
|---|---|---|---|---|
| S0 | 是（纯软件） | 派 Loop A 一轮 bounded fix | 无（可先做） | 修复失败即 SOFTWARE_NOT_QUALIFIED |
| S1 | 是（既有数据重算） | 扩 builder 到 >=2 题/原点 | S0 可并行 | <16 eligible 即报告 |
| S2 | 设计决定 | 给出赋权规则草案（thousand->unit 等） | 导师偏好可选 | 规则无法定义即重设计 |
| S3 | 是（确定性规则） | dry-run 已出；冻结时重跑同规则 | S1/S2 | 不足 8 unseen 即停 |
| S4 | 需 MODEL_GO | 在批准窗口内采集 8 episodes | P2/P3/P4 | 采集超预算即停 |
| S5 | 依赖 S4 | 4 题开发 + S 规则锁死 | S4 | 规则无法冻结即停 |
| S6 | 是（离线） | 构建 E/C/S 上下文并计 token 差 | S4/S5 | >5% 差且无法调平即停 |
| S7 | 是（冻结动作） | 组装 prereg v1 全哈希 | S0-S6 | 任一哈希不解析即停 |
| S8 | 审计 | C 预检一次（max 1 次重审） | S7 | 非 PASS 即 STOP_BRANCH |
| S9 | 需批准 | 按冻结顺序执行 128 episodes | S8 | 超 cap / 泄漏即停 |
| S10 | 是（确定性） | 分析脚本先冻哈希再跑 | S9 | 口径不一致即 INVALID |
| S11 | 裁决 | 按门表出结论 | S10 | 不达标即 UNDETERMINED/STOP |

## 3. 量变→质变排序（为什么是这个顺序）

- S0/S1/S2 = 造好尺子与题本：便宜、可复用；失败立即停，零浪费；
- S3-S6 = 小批量真实执行（<=40 调用）产生 4-8 条真实经验与上下文；
- S7/S8 = 冻结 + 预检：把所有"读数方式"钉死，避免事后解释空间；
- S9 = 一次性主实验；在此之前全部小验证必须绿；
- S10/S11 = 是否进入下一轮（量变积累点：多来源/多任务的小复现可在此后展开）。

## 4. 拍板点（唯一需要决策的）

1. P2 feedback-right（5 个空）；
2. P3 actor 选择 + MODEL_GO（Qwen3-8B / 4B）；
3. P4 预算窗口（上限已写死：<=300 请求、0 judge）。
三项齐 -> 按 §5 执行；任一缺 -> 只做 S0-S3（不需要模型）。

## 5. 绿灯后的坐标序列（不自动执行）

1. `loop A: WP-2 pre-freeze fixes`（S0+S10 脚本；bounded card）
2. S1 题本扩建 + S2/S3 冻结 -> 收据入档
3. 采集窗口：S4/S5（<=40 调用）-> S6 上下文 -> S7 prereg 冻结
4. C 预检（S8）-> pilot（S9）-> 分析（S10）-> 门裁决（S11）
每步留 receipt 路径；任何一步失败按 §2 停止点处理，不自动重试。

## 6. 停止条件（继承，不新增）

- 泄漏/桥失败/B 天花板 -> STOP_THIS_PANEL；S 全解 -> NEW_METHOD_NOT_NECESSARY；
- 其余未定 -> UNDETERMINED；一次有理由的收缩上限沿用 blueprint §2.5。
