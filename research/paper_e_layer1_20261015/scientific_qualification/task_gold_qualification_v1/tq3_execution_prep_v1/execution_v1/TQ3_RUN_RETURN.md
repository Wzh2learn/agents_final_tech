# TQ3_RUN_RETURN - TQ-3 开发性运行交付入口

> run_id: `20261016T051556Z_af4c2db6`
> status: `COMPLETED`（stop_reason=null）；system_outcome 来自真实运行；scientific_gold_validity = NOT_ESTABLISHED
> 授权: `run_card/RUN_AUTHORIZATION_20261016_v1.md`（G1-G5 专项覆盖，单次开发性运行）
> 执行: GB10 本地服务 Qwen3.6-35B-A3B-Q4_K_M.gguf @127.0.0.1:8004；Loop D 落地与执行；本文件为交付入口

## 1. 预算与合规账本（全部来自账本/收据，可复核）

- 生成请求 36 次（12 actor + 12 B + 12 C）；重试 0 次；上限 40 未触顶。
- token: prompt 28,848 + completion 5,008 = 33,856（结算值）；预留从未超过 400,000 上限。
- 时间: 首请求 2026-10-16 13:16:09 北京（允许时段 09:00-18:30 内）；末响应 13:17:49；总时长约 100 秒（上限 90 分钟）。
- 模型身份: model sha `4ac6a06b...`、server sha `037e0241...`、model_path 一致（MODEL_PIN.identity_ok=true）；chat template 7,764 chars（sha 已记录）。
- 52 项材料 pin: 运行前/后各核对一次均通过（PIN_CHECK_BEFORE.json / PIN_CHECK_AFTER.json）。
- 隔离: prompt 由白名单字段构造；实际运行中 C prompt 12/12 不含 actor 证据字段；B prompt 12/12 含完整 actor 输出；同题 B/C 使用同一份 actor 输出。
- 零内容性重试；零费用（USD 0，本地服务）；未新增依赖/权重；未修改现役服务。

## 2. 真实输出（actor，12 输入）

| 题 | variant | answer | 评分 |
|---|---|---|---|
| Q02 | original | accounts receivable, inventories, and net property, plant, and equipment | MATCH |
| Q02 | perturbed | accounts receivable, inventories, and net property, plant, and equipment | MATCH |
| Q03 | original | 14054 | MATCH |
| Q03 | perturbed | 14054 | MATCH |
| Q04 | original | -3 | MATCH |
| Q04 | perturbed | -3 | MATCH |
| Q05 | original | 31 January 2029 | MATCH |
| Q05 | perturbed | 31 January 2029 | MATCH |
| Q10 | original | 0.4707 | MATCH |
| Q10 | perturbed | 0.47 | MATCH |
| Q12 | original | 6 | MATCH |
| Q12 | perturbed | 6 | MATCH |

- 12/12 有效输出；12/12 对照开发性参考 MATCH；original 与 perturbed 逐题一致（与 PRESERVED 暂定判断一致；非 gold 验证）。
- actor 的 `evidence` 索引约定在题目/变体间不一致（0 基/1 基混用；部分疑似指向段落而非单元格）——见 §3。

## 3. 各核验方式的差异（本轮实际信号）

- A（简单规则基线，无模型调用）: 7 accept / 5 alarm。5 个 alarm 全部来自 evidence_bounds 检查，且均为索引约定错位（Q03 original 引用 c3、Q10 引用 r5、Q12 引用 r6 等超出 0 基边界）；在答案全部正确的事实下属于约定型假警报。→ 直接发现：当证据协议未定义索引约定时，机械边界规则测到的是约定噪声，而不是正确性。
- B（同源核验；全量 actor 输出可见）: 12/12 accept；典型理由为一致性检查 + 可复算时复算（如 `15363 - 1309 = 14054`）。
- C（同模型、独立上下文核验；仅见最终 answer）: 12/12 accept；独立重算并给出 own_answer（如 Q10: 自算 0.4709 vs actor 0.4707，判为容差内等价）。C 不是答案盲态、不是独立模型；B/C 差异同时包含证据链暴露与提示指令差异，本轮不单独归因于路径独立性。
- 描述性结论: 本轮面板为全匹配面板——B/C 无决策分化；A 的警报与语义正确性无关；没有出现能让三臂产生判别性差异的事件。

## 4. 失败与偏差清单（完整）

1. 预运行缺陷修复: GB10 侧 52-pin 核对最初对 7 个"LF+末尾 CRLF 混合行尾"文件误报失败；按 repo 规范（F-0907-2 双口径/LF 归一）新增 `execution_v1/material_pins_lf_v1.json`（LF 口径），核对器改为 raw / LF 口径 / 归一三选一；重跑通过（48 lf-caliber + 4 raw）。这是核对器缺陷修复，材料内容零变化。
2. RECEIPT 中 `tokens_unsettled` 的实际语义 = 已结算+未结算的承诺总量（本轮全结算，故与 tokens_settled 同值）；预算逻辑使用同一口径且正确；字段命名欠佳，保留原值不改。
3. 其余: 无请求失败、无超时、无 4xx/5xx、无崩溃、无窗口越界、无 pin 漂移。

## 5. 聚焦结果复核

- 委派的 Loop C 独立离线复核代理在 20 分钟预算内未交付（基础设施性卡死、无产物，已中断）——不计入独立评审；可在后续单列预算补做。
- 授权要求的一次聚焦复核由 Loop D 以确定性脚本完成并独立重算（不引用 RESULTS.json 结论）：
  - 账本: 36 reserve/36 settle 全 ok、重试 0、33,856 tokens、上限未触顶；
  - 镜像 87 文件哈希 0 失配；raw/ 独立重算 actor 12/12 有效且 MATCH、A 7/5、B 12 accept、C 12 accept；
  - 与 RESULTS.json 的 5 项交叉对照全部一致（all_match=true）。
- 记录: `execution_v1/reviews/LOOP_D_REVIEW_RECOMPUTE_v1.json`、`execution_v1/reviews/LOOP_D_FOCUSED_REVIEW_v1.md`。

## 6. 下一轮独立面板是否值得投入（Loop D 评估）

- 本轮证明: 管线端到端可运行；预算/隔离/续跑/拒绝机制真实生效；能产出可解释的真实系统结果；并定位"证据协议索引约定未定义"这一具体测量问题。
- 本轮未产生: B/C 分化、错答样本、共享盲点证据——全绿面板做不出机制结论。
- 建议: 有条件值得。(i) 先修证据协议（索引约定 + 单元格/段落类型），否则 A 类规则持续产生约定噪声；(ii) 样本必须包含能产生真实分歧/错误/歧义的事件（如加入 Q06 类探索案例或人工错答样本，同时保持 C 的独立上下文协议）；(iii) 若目标仍是共同盲点/共同误报，需要 reference-grounded 的 E/H/U 或错误样本，不能只靠 PRESERVED-only 全对题。满足 (i)+(ii) 前，在原 6 题上重复运行不值得。
- 成本视角: 本轮约 100 秒 / 33.9k tokens / USD 0，迭代成本极低；主要成本在面板设计与（如需）独立 gold。

## 7. 锚点文件

- 运行目录（GB10 + 本机镜像，87 文件，含 RECEIPT/MODEL_PIN/RESULTS/SUMMARY/RUN_MANIFEST）: `runs/20261016T051556Z_af4c2db6/`
- 入口代码: `execution_v1/tq3_runner.py` / `tq3_analyze.py` / `tq3_point_checks.py`（+ `material_pins_lf_v1.json`）
- 测试记录: `execution_v1/tests/point_checks_promaxgb10-0b48_20261016T051538Z.json` 等
- 授权: `run_card/RUN_AUTHORIZATION_20261016_v1.md`
