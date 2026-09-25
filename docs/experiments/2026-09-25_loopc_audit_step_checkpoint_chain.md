# Loop C 独立审计：FinQA 步级 checkpoint 全链路（暂存数据 → 论文所引数字）

> Dispatched by Loop D on 2026-09-25. 生成者不自验：三个运行器、其测试与五份文档的作者不是审稿载体。
> Mode: evidence packet inline（三个运行器全文 + 三份测试全文 + 五份文档 + 全链路重跑对照 + 稿件 §6 两段），
> no tools, 1 turn, cost not reported by bare mode. Packet sha256
> `826905f8050845b11c5d644a564354ebdab1fc0b22f6e764191e8311e2de15e9`（178 438 bytes）。
> 审计基线 head = `e357e11280e1a57302273363af25874bcd780fb2`。GB10 PID 3903468，约 12 分钟，正常退出、stderr 空。
> **VERDICT: PASS_WITH_NOTES**（无 HIGH 发现；2 MEDIUM + 6 LOW）。
> Body below is the session final message verbatim; assembled by Loop D without edits.
>
> 派发方式偏差如实记录：首次派发以 `-p "$(cat packet)"` 传参，因 packet 178 KB 触发
> `nohup: 参数列表过长` 而立即退出（stderr 74 B，无输出）；改为 stdin 重定向
> （`claude --bare --model … < packet`）后成功。先用小 prompt 验证 stdin 通路（返回 STDIN_OK）再派发，
> 未换模型、未缩减 packet 内容。该偏差只影响传输方式，不影响审计范围与证据。

## Loop D 处置记录（不属于逐字正文）

审计的**引用门判定为「可以保留（是）」**：小论文 §6 对 0.0298 / 0.2233 的引用在本审计后成立，
理由是 (1) 结果件头部的前置条件「未经独立 Loop C 审计前不得被论文引用」由本件满足，判定
PASS_WITH_NOTES 且无 HIGH；(2) 所引数字与 artifact 链一致（0.0298 = 44/1478、0.2233 = 330/1478，
审计人自行算术复核通过）；(3) 引用的是边界量而非被禁的性能量，detection 与 localization 数字未出现在 §6；
(4) 两读法同时出现、配对正确、未取优；(5) untested / failed 区分正确。

| Finding | 严重度 | 处置 | 落点与时序 |
|---|---|---|---|
| F1 scorer 三条真实守卫（`corpus_row_not_in_layers` / `corpus_record_count_mismatch` / `invalid_corpus_record`）与 V2-4 核心守卫 `v1_reproduction_mismatch` 无负例测试 | MEDIUM | 已修 | 新增 4 个负例测试 + 1 个 CLI 级双跑逐字节测试（含 `executed_at` 不在产物、两读法块齐备、frozen 锚点回写）；实现在本审计件提交**之后**的提交中 |
| F1 附带：`_assert_reproduces_v1` 在 v1 件缺 counts/metrics 键时循环空转通过 | MEDIUM | 已修 | 新增 `v1_artifact_shape_invalid` 守卫（四个 section 任一缺失或为空即 fail-closed）+ 1 个遍历四键的负例测试 |
| F2 `test_build_is_deterministic_and_seed_is_an_input` 为空断言：seed 被完全忽略时照样通过（`summary["seed"]` 只是参数回显） | MEDIUM | 已修 | 拆为两个测试：`test_build_is_deterministic`（同 seed 逐字相同）与 `test_seed_actually_changes_fault_selection`（11 个 seed × 5 个 sample_id 下 (step_index, family) 至少两种取值，且同 seed 同 sample 结果稳定）；测试名不再声称未验证的性质 |
| F8 scorer 只校验内部一致性，不与预注册 R1 冻结常量比对，理论上「自洽但不同」的三件套可被打分而不触发任何守卫；且 scorer 未对称校验 summary 的 contract_version / namespace | LOW（结构性） | 已修 | **动因先登记于本件**（治理惯例：先登记再实现），随后新增必填参数 `--frozen-corpus-sha256` 与 `--frozen-layers-manifest-sha256`（值须从预注册 R1 逐字转录，不符即 `frozen_corpus_sha256_mismatch` / `frozen_layers_manifest_mismatch`），并增 `invalid_summary_contract_version` / `invalid_summary_namespace` 两守卫；两值回写进产物 `bindings` 以留痕。属 R1 绑定的实现收紧，未改任何口径语义，故不需新预注册版本 |
| F3 `_close` 实现为统一「相等 OR 相对差 ≤1e-9」，与 R4 字面「两侧均可精确表示时要求相等，否则用相对容差」存在偏离窗口 | LOW | 不改代码，登记偏离 | 按审计建议**不改代码**（V2-3 禁止借升版动比较规则，且无动机）。偏离窗口仅存在于「两个可精确表示的值相对差 <1e-9 且不为 0」，对短小数位 gold res 与 prec=50 的商实际不可达；方向上只可能多判 match，但 direct 路数字被 v1 复现守卫钉死，且停止条件在更严格读法下只会更早触发（match 单调不增），0.2233 与 0.5 之间裕度巨大 ⇒ 已发布结论不受影响。本段即审计要求的 append-only 登记 |
| F4 `res_as_arg` 对 `#N` 引用的 res 只按 num/pct 解析，不接受 `const_*` 形（而 `resolve_arg` 接受），与 R2「递归按本文法解析」字面不完全一致 | LOW | 不改代码，登记偏离 | 实测 res 词汇中不存在 const 形（res 形态仅 num / pct / bool / 7 个畸形值），故无实际偏离；方向保守（只会多判 UNEVALUABLE，压低而非抬高保真度）。若未来出现 const 形 res，须走新版本预注册，不得原位放宽。本段即审计要求的 append-only 登记 |
| F7 v2 结果件 §3.3 称 `clean_false_flag_rate = 0` 为「负对照成立」，但在 R5 定义下 faithful ⇒ 无 flagged，该比率是分析恒等式而非经验负对照 | LOW | 不改结果件正文，登记更正 | 按审计建议不原位改结果件。更正登记于此：该 0.0 应称**定义性核对（analytic identity）**，不是经验负对照；经验负对照的真实载体是测试断言（`test_clean_faithful_and_no_false_flag_r7` 等）。后续任何引用不得把它当作经验证据 |
| F5 稿件 §6 把「停止条件先于任何检测器冻结」说满一格（实际 stop threshold 冻结于 v1 检测器已出结果之后、v2 任何输出之前） | LOW | 已修 | 稿件改为「contents and fault families were fixed before any detector existed, and whose percent-convention stop threshold was pre-registered before the second detector run produced any output」 |
| F6 稿件 §6 的 0.0298 / 0.2233 未带分母，违反 R5.5「引用时必须带分母」（同段对 322/467 做到了） | LOW | 已修 | 补「(44 and 330 matches out of 1 478 percent-form steps, respectively)」 |

审计同时确认（无 Finding）：未发现空断言 / 恒真断言 / 被改名或跳过的测试（F2 除外，已修）；
未发现分母被悄悄缩小的路径；未发现停止条件被绕过；未发现「换读法救结果」的代码路径
（读法只在 pct 分支起作用，未知读法抛错，不存在第三条读法或运行时选择开关）；
未发现五份文档中的过度主张；两种读法确有构造性非空转测试
（`test_two_percent_readings_disagree_where_v1_measured_divergence` 断言同一步两读法结论不同）。

审计人自行声明的证据局限（原样保留，不淡化）：附录 E 的全链路重跑对照由 Loop D（生成者侧）提供，
审计人未亲自执行代码；其对 E 的核验是内部一致性 + 与记录值交叉核对 + 独立算术复核，证据强度低于亲自执行，
结论已按此降权。附录 E 实测：在 head `e357e11`（比原始构建晚三个提交）重跑全链路，
M=1 与 M=8 的 corpus sha256 与记录值逐字相同（`03cf47c3…` / `7f3ad604…`），
layers_manifest_sha256 相同（`94379823…` / `9fc84f2b…`），两读法的 counts 与 metrics 全部相同，
v1 复现守卫未触发 fail-closed。
# Loop C 独立审计报告 —— FinQA 步级 checkpoint 链路（暂存数据 → 论文引用数字）

审计基线：`e357e11280e1a57302273363af25874bcd780fb2`（附录 A0）。
审计方式：纯文书审计（按指令未调用任何工具、未执行代码）。所有行号以函数名 / 测试名 / 文档章节代替。
证据局限性声明（先行）：附录 E 的重跑对照由 Loop D（生成者侧）提供，本人未亲自执行；本审计对 E 的核验是**其内部一致性 + 与 C3/C4/C5 记录值的交叉核对 + 独立算术复核**，证据强度低于亲自执行，结论中已按此降权。

---

## VERDICT: **PASS_WITH_NOTES**

无 HIGH 发现。未发现空断言 / 恒真断言 / 被改名或跳过的测试；未发现分母被悄悄缩小的路径；未发现停止条件被绕过；未发现「换读法救结果」的代码路径；未发现五份文档中的过度主张。存在 2 项 MEDIUM（守卫负例测试覆盖缺口、冻结值锚定停留在文档层）与 6 项 LOW。

---

## 逐条清单核对（1–7）

### 1. 规格与实现一致 —— **通过（含 2 项 LOW 备注）**

**V2-1(1) 双读法并列计算、并列上报**：真实生效，非其中一路被静默忽略。
- `READINGS = (READING_DIRECT, READING_SCALED)`；`main()._run()` 对两种读法各跑一遍 `aggregate(score_corpus(...))`，产物 `by_reading` 含两路完整 counts/metrics/denominators/strata，stdout 两路都打印，产物含 `readings` 字段（满足 V2-4(2)）。
- 读法只在 `step_verdict` 的 `form == "pct"` 分支起作用（`READING_SCALED` 时 `value *= 100`）；未知读法抛 `unknown_percent_reading`——不存在第三条读法或运行时选择读法的开关。
- `#N` 下游消费规则（尾数 ÷ 100）在 `res_as_arg` 中与读法无关，符合 V2-1(1)「`#N` 规则不变」。
- 关键非空转测试存在：`test_two_percent_readings_disagree_where_v1_measured_divergence` 构造性地断言同一步在两读法下结论**不同**（direct→mismatch，scaled→match），满足 V2-4(1) 第一条；`test_num_form_verdicts_are_reading_independent` 锁住 num 层读法无关。
- 结构性小加分：`_assert_reproduces_v1(first[READING_DIRECT], ...)` 显式引用 `READING_DIRECT`，若有人从 `READINGS` 删掉 direct 路，main 直接 KeyError——「只报 scaled」在代码层走不通。

**V2-1(2) root_cause 指标**：`score_record` 中 `min(mutant_run["flagged"]) == injected`，与规格逐字一致；`test_root_cause_hits_cascade_where_exact_does_not` 构造了 exact 失败而 root_cause 命中的级联例，满足 V2-4(1) 第二条。

**V2-1(3) 三定位指标同时输出**：`aggregate` 的 metrics 与 metric_denominators 恒含 exact / inclusive / root_cause 三项；`test_all_three_localization_metrics_are_reported_together` 机械断言缺一即失败。

**V2-2 继承条款**：R1（`verify_bindings`：corpus sha、摘要一致性、层摘要重算、行归属集合）、R2（`resolve_arg` 穷尽文法，不可解析一律 None→UNEVALUABLE，`none`/自由文本「never guessed, never zero」）、R3（`compute` 十族语义 + 除零/平局/exp 非有限/未知族全部 None）、R5 分母纪律、R6 六维分层（step_strata 三维 + example_strata 五维，键全集恰为规格六维；稀有层从不并入 other）、R7 正反例（逐条对上了：忠实 2 步 divide、const_m1、#N 链、pct 链、res_scale 检出+exact、minus 上 arg_swap 检出；负例 none/除零/平局/未知族/篡改 fail-closed/commit 非 40-hex 不写文件）——均已实现且有对应测试。

**容差 1e-9**：`REL_TOL = Decimal("1e-9")` 模块级常量，仅被 `_close` 引用；无 CLI 参数、无环境变量、无第二处比较捷径；产物 `prereg.relative_tolerance` 如实登记。未被绕过。**但** `_close` 的实现是「相等 OR 相对差 ≤1e-9」的统一规则，而 R4 字面是「两侧均可精确表示时要求相等，否则用容差」——见 Finding F3（LOW，且已论证不影响任何已发布结论）。

### 2. 分母纪律（R5）—— **通过**

- `faithful = not clean_run["flagged"] and not clean_run["unevaluable"]`：UNEVALUABLE 既不当真也不当假，单独计数（`steps_unevaluable` 进 totals 与分层）。
- detection / 三 localization / false_flag 只在 `if faithful:` 分支累加；`interpretation_fidelity` 分母 = faithful + unfaithful = 全记录数；每个指标的分母在 `metric_denominators` 显式输出。
- `_ratio` 在分母为 0 时返回 `None` 而非伪造数值。
- 记录级丢失路径全部 fail-closed：空行跳过后由 `corpus_record_count_mismatch` 兜底（`len(scored) != expected` 即抛）；行不属已授权层抛 `corpus_row_not_in_layers`。**找不到任何一条「分母缩小后指标照常产出」的路径。**
- 算术复核（本人独立计算）：322/1970=0.16345178 ✓；467/1970=0.23705584 ✓；319/322=0.99068323 ✓；464/467=0.99357602 ✓；151/319=0.47335423（=v1 §3 的 120+31 / 288+31 ✓）；244/464=0.52586207（=C5 §4 的 147+97 ✓）；M=8：33/212=0.15566038 ✓、46/212=0.21698113 ✓、15/33=0.45454545 ✓、22/46=0.47826087 ✓。
- 跨文档步级对账全部闭合：num 2571+518+7=3096、pct 44+1429+5=1478、bool 8、other 1，合计 4583 = 语料件「注入例内步数合计」= op 族求和 = 变体位求和（86+2280+2217）✓；direct match 2623=2571+44+8、scaled match 2909=2571+330+8 ✓；mismatch 族级求和 1638+4+59+82+164=1947 ✓。scaled−direct 的 match 差 286 恰等于 pct 层差（330−44）且 num 层逐字不变——与 C5 §3.1「差异 100% 落在 pct 层」自洽。
- 备注（不构成 finding）：`clean_false_flag_rate` 在 R5 定义下恒为 0（faithful 定义已排除 flagged），规格自己写明「按定义应为 0」；C5 §3 称其「负对照成立」在字面上是同义反复，真正的经验负对照是测试套件里的忠实例断言。见 F7（LOW）。

### 3. 停止条件是否被尊重（V2-3）—— **通过**

- 触发核验：pct 保真度 direct 44/1478=0.02977→0.0298，scaled 330/1478=0.22327→0.2233，双双 <0.5，停止条件**确实满足且确实被宣布触发**（C5 §1），对照宇宙同判（8/160=0.05、39/160=0.24375→0.2438，与 C5 §2 一致）。
- 代码中不存在绕过路径：无读法选择开关、无阈值参数、无容差参数、无分母参数；两读法恒并列产出。
- 文档中不存在放宽：C5 §1 明写「不得通过改分母、改容差、改族语义、改故障定义或再换一个百分号读法来提升」；§7 明写「不得只引用 mantissa_scaled」；未开 v3；v1 结果原样保留且被 `_assert_reproduces_v1` 机器锚定为可比（Appendix E「v1_reproduction_guard passed」）。
- 稳健性附注：即便按 R4 字面的更严格比较（见 F3），match 只会更少、保真度只会更低，停止结论在两个方向上都不可翻转——停止条件不是靠容差边界「险胜/险败」的。

### 4. fail-closed 是否真实 —— **基本通过，覆盖有缺口（MEDIUM ×1）**

守卫真实可触发（代码检视）：输入 sha 不符 / 不在 manifest（split、adapter）、层摘要重算不符（adapter `load_layers`、scorer `verify_bindings`）、corpus sha 不符、摘要与 corpus sha 不一致、行不属已授权层、记录数不符、commit 非 40-hex 不写文件、零连接 connect 即抛——三个运行器全部具备，且 `SplitError/AdapterError/ScorerError` 在 `__main__` 统一转 `SystemExit(2)`。

测试覆盖核对（逐条）：

| 守卫 | split (B1) | adapter (B2) | scorer (B3) |
|---|---|---|---|
| 输入哈希篡改 | ✓ | ✓ | —（经 corpus sha 覆盖） |
| 层摘要重算 | ✓（digest 口径测试） | ✓ tamper 测试 | ✓ tamper 测试 |
| corpus sha / 摘要一致性 | — | — | ✓（两路 tamper 均测） |
| **记录数一致** | — | — | **✗ 无负例测试** |
| **行归属（not_in_layers）** | ✓（ confinment 正向测试） | ✓（confined_to_assigned 正向） | **✗ 无负例测试** |
| commit 40-hex 不写文件 | ✓ | ✓ | ✓ |
| 零连接 | ✓ | ✓ | ✓ |
| **v1 复现守卫（V2-4 核心）** | — | — | **✗ 无 `v1_reproduction_mismatch` 负例测试** |
| CLI 双跑逐字节 + 无墙钟 | ✓ | ✓ | **✗ 仅函数级确定性测试** |

- 未发现「实际上不会失败」的既有测试：无 skip、无空断言；B1/B2/B3 的关键断言均为可失败断言。特别核验过两个易空转点：(a) B2 `test_arg_swap_never_targets_a_commutative_family` 的条件断言——fixture 中 BB 例两步的 res 均非数值（"yes"/"no"），res_scale 必不可用而 minus/compare_larger 非交换且两 arg 不同，故该例**必然**产生 arg_swap 记录，断言非空转；(b) B2 `test_no_detection_or_localization_metric_is_published` 的禁词键扫描对 dict 键全覆盖，非恒真。
- 但 B2 `test_build_is_deterministic_and_seed_is_an_input` 名实不符：它未断言 seed 43 的语料与 seed 42 **不同**（若 seed 被忽略，该测试照样通过）——见 F2（MEDIUM，按用户规则这不属「不会失败的测试」，因其计数断言仍可失败，故不升 HIGH，但必须修）。
- scorer 三条守卫（记录数、行归属、v1 复现）代码真实、路径必经，但缺负例测试——见 F1（MEDIUM）。`_assert_reproduces_v1` 的潜在静默弱化路径（v1 件缺某 section 键时 `expected = {}` 空循环通过）被 step_strata 的全等比较部分兜住（v1 缺 step_strata 时 `{} != 非空` 必抛），且 Appendix E 显示其对真实 v1 件通过——非空转有运行时正证据，但无「能触发」的负证据。

### 5. 可复现性（附录 E）—— **通过，证据强度按声明降级**

- head 一致：E 头部 `e357e11280e1a57302273363af25874bcd780fb2` = A0 基线 ✓。
- corpus sha256 逐字核对：M=1 `03cf47c3…900d3f` 与 C1 §1、C3 §3、C4 §4、C5 §8 逐字相同 ✓；M=8 `7f3ad604…4ed04` 逐字相同 ✓。E 的 artifacts 段两个文件的 sha256sum 输出亦与之一致 ✓。
- layers_manifest_sha256：M=1 `94379823…d760b`、M=8 `9fc84f2b…d056a6`，与 C1/C3/C4/C5 记录值逐字相同 ✓。
- counts/metrics 对照：E 打印的两宇宙 × 两读法共 24 个 metric 值，本人逐一与 C4 §1、C5 §2 表格比对，**全部相同**（0.16345178 / 0.99068323 / 0.47335423 / 1.0 / 1.0 / 0.0；0.23705584 / 0.99357602 / 0.52586207 / 1.0 / 1.0 / 0.0；M=8 六项同 C5）✓。
- 内部一致性：`counts_vs_recorded True / metrics_vs_recorded True` 为 Loop D 脚本自报布尔值，本身证明力弱；但 E 打印的**数值本身**可与文档独立比对且全部吻合，加上本人的分母/求和算术复核全部闭合（见第 2 条），一致性不依赖那两个布尔值。
- 体积对账：E「5.6M /tmp/repro_20260925」与 C3 §7「合计 5.6 MB」一致 ✓。
- **明确声明**：E 由生成者侧（Loop D）产出，本人无法执行代码验证其确实运行于 e357e11、也无法重算任何 sha256；「e357e11 与 aa0adaf 之间 scorer 字节未变」这一点仅由「重跑值与记录值全等 + v1 守卫通过」间接支持。本项结论的证据强度**低于亲自执行**，属「文书可得的最高强度」。

### 6. 稿件引用是否越界（附录 F）—— **通过（含 2 项 LOW 措辞修正）**

- 数字一致：0.0298 / 0.2233 与 C5 §1 一致 ✓；1970 条 ✓；322 / 467、16.3% / 23.7% 与 C5 §2 分母及 §7 一致，且配对正确（322↔0.0298 读法、467↔0.2233 读法）✓；第一段引用的 7134 / 2409 UID / 768 簇 / 2–11 列 / dev 层为空 / K=10 与 D1 §4、D2 §6 一致 ✓。
- 禁引性能量：F 全文**未出现** 0.99068 / 0.99358 / localization 1.0，也未出现任何 detection rate；322/467 只作为分母边界量出现，并明写「reported to bound the route, not as a capability」✓。
- 两读法同时出现 ✓（"under one percent convention and 0.2233 under the other"），且未取较好者作头条——头条是停止条件本身 ✓。
- untested vs failed：「Criterion (ii) has not been tested」「remains untested rather than failed」——区分正确 ✓；「the route was stopped rather than re-parameterized」如实 ✓。
- 两处措辞问题见 F5（先占性从句不精确）与 F6（pct 保真度未带分母 1478）。

### 7. 是否存在过度主张 —— **通过**

逐份扫描 C1–C5：
- 无「验证了步级 checkpoint 检测有效」类句子；相反，C4 §5 与 C5 §7 各有整节「不得主张」，C5 §4 主动把 root_cause=1.0 定性为「构造性成立的健全性检查，**不是**有信息量的性能结果」——这是反向的自我限权，值得记录。
- 无「复现了冻结 Stage E 口径」类句子；C3 §5、C4 §5、C5 §7 三处显式禁止该表述，C1 R8 / C2 V2-5 在规格层禁止。
- C4 §2「这正好验证了 R3……的设计意图」中的「验证」对象是**分层上报这一设计**能让偏差显形（有数据支持：变体位 42.8% vs 43.6%），不是检测能力，不构成越界。
- C5 §5 对 num 层 518/3096 残余「不归因、不猜测」，C5 §6「not identifiable from public metadata alone」带明确的范围限定词（D-C 批准范围内）。
- C2 V2-1(2) 对「exact/inclusive 差距在 v1 已可见」做了事前披露而非事后合理化，动因段（V2-0）在 v2 分数产生前冻结——文书链条自洽。

---

## Findings

**F1 · MEDIUM · `tests/test_finqa_step_checkpoint_scorer.py`（B3 整体）+ `research/finqa_step_checkpoint_scorer.py`（`score_corpus`、`_assert_reproduces_v1`）**
scorer 的三条真实守卫无负例测试：`corpus_row_not_in_layers`、`corpus_record_count_mismatch`、`invalid_corpus_record`，以及 V2-4 的核心守卫 `v1_reproduction_mismatch`。`_assert_reproduces_v1` 原文：`expected = v1.get(v1_key) or {}` —— 若 v1 件形状异常（缺 counts/metrics 键），对应循环空转通过，仅 step_strata 全等比较兜底。当前唯一「能触发」的证据是 Appendix E 的正向通过记录。
建议修法：在 B3 增加 4 个负例——(a) `_bindings_fixture` 的 layers 中删去 sample "a" 后调 `score_corpus`，断言 code == `corpus_row_not_in_layers`；(b) summary 的 `corpus_records` 改为 2，断言 `corpus_record_count_mismatch`；(c) 语料行删去 `fault` 键，断言 `invalid_corpus_record`；(d) 加载 v1 分数 JSON、把 `metrics.interpretation_fidelity` 改一位小数后调 `_assert_reproduces_v1`，断言 `v1_reproduction_mismatch`（同一测试顺带覆盖「v1 件缺 counts 键但 step_strata 在」时空转是否被兜住）。

**F2 · MEDIUM · `tests/test_finqa_step_checkpoint_adapter.py::test_build_is_deterministic_and_seed_is_an_input`（B2）**
测试名声称「seed is an input」，但全部断言（seed 43 的 injected 计数 == seed 42、`other["seed"] == 43`、4 条记录）在 seed 被完全忽略时**照样通过**——`summary["seed"]` 只是参数回显。seed 实际参与 `plan_fault` 的 `bucket(INDEX_SALT + ":" + str(seed), ...)`（代码核实无误），但该性质无测试锁定。
建议修法：改为对 seeds 42–52 收集各自语料的 `(sample_id, fault.step_index, fault.family)` 元组集，断言至少两个 seed 产出不同的故障选择；或直接断言 `bucket(INDEX_SALT+":42", sid, n) != bucket(INDEX_SALT+":43", sid, n)` 对若干构造 sid 成立。

**F3 · LOW · `research/finqa_step_checkpoint_scorer.py::_close` vs 预注册 v1 R4（C1 §4）/ v2 V2-2**
R4 字面：「两侧均可精确表示时要求相等，否则用相对容差 1e-9」。实现是统一的「相等 OR |a−b| ≤ 1e-9·max(|a|,|b|)」。偏离窗口仅存在于「两个可精确表示的值相对差 <1e-9 且不为 0」——对短小数位的 gold res 与 prec=50 商实际不可达；方向上只可能多判 match（理论上抬高保真度），但 direct 路数字被 v1 复现守卫钉死，且停止条件在更严格读法下只会更早触发（match 单调不增），0.2233 与 0.5 之间裕度巨大，任何已发布结论不受影响。
建议修法：不改代码（V2-3 禁止借升版动比较规则，且无动机）；在下一份 append-only 结果件或审计记录中登记该实现与字面规格的偏离窗口及其无影响论证，即可。

**F4 · LOW · `research/finqa_step_checkpoint_scorer.py::res_as_arg` vs R2「递归按本文法解析」**
`#N` 引用的 res 只按 num/pct 两形解析，不接受 `const_*` 形（`resolve_arg` 接受）。实测 res 词汇（D2 §1：res 形态为 num/pct/bool/7 个畸形值）中不存在 const 形 res，故无实际偏离；方向保守（只会多判 UNEVALUABLE，压低而非抬高保真度）。
建议修法：append-only 备注一句即可；若未来出现 const 形 res，须走新版本预注册，不得原位放宽。

**F5 · LOW · 附录 F（小论文 §6）第二段第一、二句**
原文：「a corpus of 1970 frozen step-level records **whose contents, fault families and stop condition were fixed before any detector existed**」。语料内容与故障族确实先于任何检测器冻结（C3/C1 时序 ✓），但停止条件（V2-3）冻结于 v1 检测器已存在并已出结果之后、v2 任何输出之前（C2 冻结时刻声明原文：「本件提交时，仓内与 GB10 上不存在任何 **v2** 检测器输出」）。现措辞把先占性说满了一格。
建议修法：改为「…whose contents and fault families were fixed before any detector existed, and whose percent-convention stop threshold was pre-registered before the second detector run produced any output」。

**F6 · LOW · 附录 F（小论文 §6）第二段 vs R5.5「引用时必须带分母」**
原文：「fidelity of the reconstructed step semantics on percent-form results was 0.0298 under one percent convention and 0.2233 under the other」——未带分母。0.0298 = 44/1478、0.2233 = 330/1478（C5 §1），R5.5 要求引用带分母；同段后文对 322/467 做到了，对这两个头条数字没有。
建议修法：插入「(44 and 330 matches out of 1 478 percent-form steps, respectively)」。

**F7 · LOW · C5 §3.3（「负对照成立」）**
原文：「负对照成立：两读法、两宇宙下 clean_false_flag_rate 均为 0.0，忠实例零误报」。在 R5 定义下 faithful ⇒ 无 flagged，该比率为分析恒等式 0，不构成经验负对照（规格 C1 R5.3 自己注明「按定义应为 0」）。实现无误、文档措辞略强。
建议修法：append-only 备注将其改称「定义性核对（analytic identity）」，并指出经验负对照的真实载体是 B3 的忠实例断言（`test_clean_faithful_and_no_false_flag_r7` 等）。不要求改 C5 正文（结果件不原位改）。

**F8 · LOW · `research/finqa_step_checkpoint_scorer.py`（冻结值锚定）与 `main()`（summary 元数据未校验）**
scorer 校验的是**内部一致性**（corpus 文件 ↔ CLI sha ↔ summary ↔ layers 摘要重算 ↔ 行归属 ↔ 记录数），但不把任何值与预注册 R1 / C3 §3 冻结的常量（`03cf47c3…`、`b6a522ca…`、`94379823…`）比对；理论上存在「自洽但不同」的 corpus+summary+layers 三件套被打分而不触发任何守卫的路径，实际锚定靠文档层人工比对 + Appendix E 重建（E 中重建语料哈希回到 `03cf47c3…`，事实上闭环）。另：scorer 不校验 summary 的 `contract_version`/`namespace`（adapter 的 `load_layers` 对 layers 做了同类校验，scorer 未对称做）。
建议修法：为 scorer 增加必填 `--frozen-corpus-sha256` 与 `--frozen-layers-manifest-sha256`（值须从预注册 R1 逐字转录），与 CLI/summary 值不符即 fail-closed 并登记于 bindings；同时断言 `summary["contract_version"] == "finqa-step-checkpoint-corpus-v1"` 且 `summary["namespace"] == "finqa"`。此为收紧而非改语义，不需新预注册版本（属 R1 绑定的实现强化），但按治理惯例应先在结果件/审计记录中登记动因。

---

## 引用门判定

**小论文 §6 对 0.0298 / 0.2233 的引用：可以保留（是）。**

理由：
1. C5 头部的前置条件（「未经独立 Loop C 审计前不得被论文引用」）由本审计满足，结论 PASS_WITH_NOTES，无 HIGH 发现；按治理惯例，维护者应将本审计落为 Loop C 记录件后，把 `paper_result` 标记按既有流程翻转（append-only，不改结果件正文）。
2. 所引数字与 artifact 链一致：0.0298 = 44/1478、0.2233 = 330/1478，与 C5 §1、Appendix E 逐字吻合，本人算术复核通过。
3. 引用的是**边界量**（停止条件的触发证据），非被禁的性能量；detection 0.99068/0.99358 与 localization 1.0 未在 §6 出现；322/467 只作分母边界并明写「to bound the route, not as a capability」。
4. 两读法同时出现、配对正确、未取优；untested / failed 区分正确。
5. 附带条件（非阻断，建议随下次稿件修订落实）：F5 的先占性措辞与 F6 的分母补注。若维护者选择先改后引，两改动均为一句级编辑，不触碰任何数字。

---

## 3 项下一步建议

1. **补 scorer 守卫负例测试（对应 F1，最高优先）**：新增 4 个测试分别触发 `corpus_row_not_in_layers`、`corpus_record_count_mismatch`、`invalid_corpus_record`、`v1_reproduction_mismatch`（改 v1 分数 JSON 一位小数即可），并补一个 scorer CLI 级双跑逐字节 + `"executed_at" not in payload` 测试，与 B1/B2 的同名测试对齐。这是把「fail-closed 真实」从代码检视证据升级为机器证据的最小增量，不动任何运行器语义。
2. **把冻结值锚定从文档层收进代码层（对应 F8）**：scorer 增加 `--frozen-corpus-sha256` / `--frozen-layers-manifest-sha256` 必填参数并 fail-closed 比对，同时断言 summary 的 contract_version 与 namespace。动机与差异按治理惯例先在 append-only 记录件登记，再实现；不触及 V2-3 禁止的任何口径。
3. **稿件两处一句级修订 + 审计落档（对应 F5/F6 与引用门）**：§6 改先占性从句为「stop threshold pre-registered before the second detector run produced any output」，并在 0.0298/0.2233 后补「(44 and 330 of 1 478 percent-form steps)」；随后将本审计作为 Loop C 记录件入库，翻转 C5 头部的 `paper_result` 标记。三项均为 append-only / 措辞级操作，不改任何冻结判据、冻结 hash 或已发布数字。
