# TQ-4 运行独立复核 v1（聚焦：真实输出 / 回执与账本 / 评分与决策复算 / 隔离 / 报告一致性）

> 2026-10-16｜复核方：委派独立复核代理 `loopc_tq4run_review`（fresh context；非 TQ-4 运行作者）｜只读独立复算：零模型调用、零网络、零冻结件修改
> 复核对象：run `20261016T082849Z_430d927a`（TQ-4）运行产物（`runs/…/` 84 文件）+ `execution_v1/TQ4_RUN_RETURN.md` + execution_v1 运行层记录
> 机器记录：`reviews/POST_RUN_RECOMPUTE_v1.json`；复算脚本：`reviews/POST_RUN_RECOMPUTE_v1.py`（全部检查可复跑）
> 证据截止：2026-10-16 约 17:15（Asia/Shanghai）

## 0. 交付说明（供编排层登记）

- 本件为延迟交付：原委派任务简报未送达复核代理（沿用本 harness 已知消息投递故障背景）。复核范围按授权 S3 条款重建：
  “用真实输出做一次离线聚焦独立复核”。全部检查均为本次实跑，不引用既有分析输出作判据。
- 只读边界：未修改任何运行产物、冻结材料、清单或报告；交付前已清除复核自身产生的字节码残留（见 §5）。
- 编排层收尾建议（4 项）：① 将本件 3 个文件登记进 TQ-4 收尾清单（与前置复核同流程）；② 将 §4 N-1/N-6 建议转写进 `CHAIN_RETURN.md` 偏差节；③ TQ-5 运行前先落 config/执行层快照机制（N-1）；④ 如引用“点检 13/13”“首请求 16:28:49”“B 有效决策分母”等表述，按 §4 精确化。

## 1. 结论摘要

| 范围 | 结论 | 依据（本次实跑） |
|---|---|---|
| A 运行完整性/回执 | **PASS_WITH_NOTE** | RUN_MANIFEST 84/84（哈希+字节数）一致；RECEIPT 与账本 36/36/0/40,205 全对账；材料 pin 49/49 独立重算 0 失配；模型 pin 与授权常量一致。注记 N-1（config pin 不可复现） |
| B 预算/窗口/参数一致性 | **PASS** | 36 次尝试、0 重试、40,205 token；首请求 16:29:02 北京（窗口内）、时长 194s；36/36 请求参数逐项一致；串行 0 违规 |
| C Part 1 复算 | **PASS**（注记 N-7） | 4/4 评分逐字段一致（含 detail）；4/4 legal；B/C 决策 4/4 一致；N1 事件字段级核实 |
| D Part 2 复算 | **PASS**（注记 N-2） | 12/12 决策复算一致；B 11/12 有效；C 12/12；矩阵复现（machine 口径）+ 严格口径记录；重复刺激 6/6 规范哈希一致、决策一致 |
| E 输入隔离 | **PASS** | 36 份 prompt 泄漏词 0 命中；B 完整见证据 JSON、C 仅见答案；模板标记 16/16+16/16+4/4 |
| F 报告一致性 | **PASS_WITH_NOTES** | 边界声明齐全；关键数字对账；注记 N-3/N-4/N-5/N-6 |

无阻断性问题；非阻断注记 8 条（§4）。

## 2. 复核方法

- 只读独立重执行：从 raw/prompts/ledger/manifest 原始件出发，自写重算（清单哈希、账本数学、窗口/串行、评分、合法性、决策抽取、矩阵、重复对比较、隔离扫描、报告对账）。
- 口径同源约束：仅评分复用 `execution_v1/tq4_scoring_entry_v21.py`（其包级语义已由前置独立复核 A 项 PASS，且 v2→v2.1 仅 bool 硬化）；其余全部为本次独立实现，不导入 runner/analyzer 既有结果。
- 已知限制：本地离线复核，无 GB10 侧直接复验；无生成调用；复核时点部分后续产物（closeout/、TQ-5 准备）不属本件范围。

## 3. 逐项结果

### A 运行完整性与回执

- `RUN_MANIFEST.json`（self_excluded）84 条：逐项 sha256+bytes 一致、0 缺件；册外盘上文件仅 RUN_MANIFEST 自身。
- 账本对账：reserve 36 / settle 36 / retry 0 / settled=40,205 = raw 侧 token 总和；首 reserve 08:29:02Z → 末 settle 08:32:16Z；settle(i) ≤ reserve(i+1) 全序成立（串行 0 违规）。
- 回执字段（gen_attempts/retries/tokens/steps/first_request/status）与账本逐项一致。
- aux 账本 145 行 = 72 次发送（apply-template 36 + tokenize 36）+ 72 次完成 + 1 次 service-meta；与“aux ops 72”一致。
- 材料 pin：PIN_CHECK_BEFORE/AFTER ok=true（49 项，lf-caliber 47 + raw 2）；本次按 LF 口径独立重算 49 项 0 失配；`source_manifest_sha256` 与包 MANIFEST 一致。
- 模型 pin：model/sha=4ac6a0…、server/sha=037e02…、path/model_id/base_url 与授权文本一致；identity_ok=true。
- RUN_META 哈希：runner raw 一致、authorization raw/lf 一致、templates 仅 LF 口径一致（差 1 个 CR 字节，EOL 级）；**config 两口径均不一致** → N-1。

### B 预算、窗口与参数一致性

- 36/36 raw：`request.params` 逐项等于冻结参数（T=0 / top_p=1 / seed=20261016 / max_tokens=2048 / stream=false / json_object / enable_thinking=false）；model_id、URL、HTTP 200、retry=false、variant=perturbed 全成立。
- 预算：尝试 36≤40、重试 0≤4、token 40,205≤400,000；窗口：16:29:02 启动 ∈ 09:00–18:30、日期 ∈ allowed_dates、时长 194s ≤ 90min。

### C Part 1 复算（4 行）

- 独立复算 N1 `1.5%`、N2 `$22,448`、N3 `0.68%`、N4 `63.4`：评分状态+detail 逐字段与存储一致；合法性 4/4 legal（issues 空）；B/C 决策 4/4 与存储一致。
- N1 关键事件（字段级复核）：B=alarm（`contradiction_points` 3 条，含 “category error” 原词）；C=alarm（含 “semantically awkward” 原词）；双方均围绕“百分比均值 vs investment 语义错位”。**张力注记**：C 的 `contradiction_points=[]` 且 reason 末尾转向接受措辞（“I will accept it …”）；结论以决策字段为准（=alarm），叙事引用时见 N-7。
- N1 参考 derivation `(2% + 1%) / 2 = 1.5`（reference 文件）；“评分 MATCH 与核验 alarm 分属不同测量层”与证据一致。

### D Part 2 复算（12 候选）

- 决策复算 12/12 与存储一致；有效性：B 11/12（Q04-C2 invalid）、C 12/12。
- Q04-C2 损坏输出复核：content 5,178 字符，`json.loads` 失败（“Invalid control character … char 5113”），finish_reason=stop，completion_tokens=1,236 —— 与 §4 陈述逐项一致；prose 中确含引用质疑与 alarm 意图，但按规则仅记 invalid（不从 prose 取判，规则执行正确）。
- 矩阵：machine 口径（decision 缺省回退 ledger_state，含 “done”）与存储矩阵完全一致；严格口径（invalid 显式）记录于复算 JSON：correct+illegal 的 B = alarm2/invalid1。
- 重复刺激对：6/6 对 messages 规范序列化哈希一致（等价“逐字节相同”声明）；6/6 对 C 决策一致。B 侧同题合法/非法引用变体的提示不同（Q02 抽样核实；全 12 例证据嵌入已验证），C 侧相同（6/6）——与“C 看不到引用”一致。
- 构造合法性：12/12 机械重算与 label 一致。

### E 输入隔离

- 全 36 prompt 内容扫描（answer_kind / evidence_legality / candidate_id / frozen_design_target / support_target / injection / v4_label / checker_verdict / “correct+” / “incorrect+” / “variant” / “perturbed”）0 命中。
- B 提示逐字嵌入 `{task_id,answer,evidence}` 完整 JSON（12/12 候选、4/4 自然任务均为 True）；C 提示含答案文本、均不含证据 JSON 或 “evidence” 字样（16/16）。
- 模板标记计数：B “Candidate answer (from another system):” 16/16；C “Candidate final answer:” 16/16；actor 4/4。

### F 报告一致性

- `TQ4_RUN_RETURN.md` 关键数字对账：36/36、1/36、6/6、40,205、4/4 等成立；边界声明（NOT_ESTABLISHED / NOT_ASSESSED / 无 confirmatory / 重复刺激注记）在场。
- 点检记录：pre-run 序列（16:27:22 一次模板提取失败 → 16:27:37 起全过；16:28:34 最后全过）各 14 项；run 于其后启动。运行后另有两次复跑记录（16:46–16:47，最终全过；属运行后复核动作）。→ N-4。
- 时间锚点：正文“首请求 16:28:49”实为 run 创建/模型 pin 时刻；首 reserve = 16:29:02（回执口径）。→ N-5。
- “镜像 84 文件双端核对”：本地未见专用回执件（仅叙事；closeout/CHAIN_RETURN.md 为 17:13 复述）。→ N-6。

## 4. 非阻断注记（8 条）

- **N-1（低-中；可追溯性）**：`RUN_META.config_sha256=3ec70955…` 与本机 `chain_config_tq4.json` raw（0141ce92…）/LF（5259fd5c…）均不符；该文件 mtime=16:30:45 落在 run 窗口内，记录时点版本未留存。影响边界：实际执行的调度/载荷由 raw+prompts+ledger 全量可复核（本件已独立复算），结论不受影响；属“记录不可复验”缺口。建议：运行前将 config 与 execution_v1 关键件（runner/评分入口/分析器）复制并入 run dir、纳入 manifest/pin 后再记哈希；TQ-5 沿用前请先落此机制。
- **N-2（低；呈现一致性）**：`SUMMARY.md`/machine 矩阵将解析失败的 B-Q04-C2 记为 “done”（analyzer 的 ledger_state 回退），而 §4 正确记为 `json_parse_error`/invalid。建议下一版本将 parse-fail 显式渲染为 `invalid`，避免 “done” 被误读为决策值。
- **N-3（低；表述精度）**：§4 句“B 有效决策分母 = 35”不准确：35 为全输出有效数（35/36）；B 自身有效决策为 15/16（Part 1 4/4、Part 2 11/12）。建议改为“全 run 有效输出 35/36；B 有效决策 15/16”。
- **N-4（低；引用精度）**：§4 “点检 13/13” 与本地记录（最新 pre-run 文件 14 项全过）不符；建议引用“14/14（含 material_pin_check_full）”或注明排除口径；GB10 侧同跑记录不在本地、本件无法复验。
- **N-5（低；时间锚点）**：§1 “首请求 16:28:49”应为 16:29:02（首 reserve；回执 first_request_utc=08:29:02Z）；“3 分 27 秒”为创建→末响应口径（严格首请求口径 3 分 14 秒）。建议以账本/回执值作正文口径。
- **N-6（低；回执留存）**：“84 文件双端逐一哈希核对 0 失配”目前仅叙事（本地无专用回执/双端哈希清单；本件已验证本地 84/84 与 master ledger 72/72 镜像一致性）。建议把双端核对落成 receipts 件（含两端 hash 列表）。
- **N-7（低；叙事精度）**：N1 事件引文归属与内部张力：'category error' 为 B 原词、'semantically awkward' 为 C 原词；C 的 `contradiction_points` 为空且 reason 尾句为接受措辞。若 CHAIN_RETURN/增补稿引用该事件，建议按“决策字段=alarm；C reason 内部存在张力”精确表述。
- **N-8（提示；字段命名）**：回执 `tokens_unsettled`=40,205 实为 held-netting 值（=已结算），名称极易误读为“尚未结算”。建议未来改名（如 `tokens_held_net`）。

## 5. 边界与声明

- 本复核为只读独立复算：无模型调用、无网络、未修改任何运行产物/冻结件/清单/报告；树内唯一写痕为复核交付 3 文件（本件、复算脚本、复算 JSON）。复核期间由 py_compile 生成的 `reviews/__pycache__` 已在交付前以路径校验方式清除，最终树内无新增字节码。
- “独立”指复核方非运行作者且全部检查为本次实跑重算；复核方可以访问包内状态文件，但本件不依赖其结论。
- 本件不改变 canonical 记录、不签发 gold、不构成对 TQ-5/论文结论的预判；scientific_gold_validity 维持 NOT_ESTABLISHED。
