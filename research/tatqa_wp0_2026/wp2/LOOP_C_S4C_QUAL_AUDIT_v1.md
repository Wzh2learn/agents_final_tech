# WP-2 S4C 在线资格收尾 — Loop C 独立复核（v1）

> task: `tatqa-wp2-s4c-qual-20261014` | 审计者: fresh-context Loop C（独立复算）| 日期: 2026-10-14 | 总体判定: **PASS**
> 判定含义: 执行方 `FAIL_FINAL → STOP_THIS_PANEL_PERMANENT` 的规则判读与全部关键证据独立成立；**无异议**。
> 红线遵守: 零模型调用、零请求、零服务启停、未运行执行器/预检（任何模式）、零 git 写、未改任何被审对象；唯一写入件＝本文件。
> 披露: 本审计线程启动时任务消息未注入采样上下文（harness 投递缺口），任务原文经父线程会话日志恢复；恢复前后活动均为只读侦察，未触碰被审对象。

## 0. 方法与未验证面

**手段**: 本地＋GB10 双端逐件 `sha256sum` 独立重算；`git log/diff/status` 只读核对；GB10 只读重跑零模型诊断脚本（stdout）并与落盘输出对账；`ss -tln` 只读核对端口；字节级子串/哈希复算。

**未验证面（如实申报）**:
1. 渲染 token 数 [607,332,406] 未做字节级重渲染——重跑预检属被禁的 `run_s4c_qualification` 范围；决定渲染的全部组件哈希已 10/10 独立重算一致。
2. `payload_canonical_sha256` 未重算（规范化算法未在件内声明）；其输入字符串的 `task_prompt_sha256` 已由原文独立重算一致。
3. 除服务端计数器外，无独立通道证明运行窗口内"零其他网络外发"（安全计数全 0，未发现相反证据）。

## 1. 规则判读 — PASS（FAIL_FINAL 判读正确）

冻结卡原文（`S4C_ONLINE_QUALIFICATION_CARD.md` 判定节）:

- 「**FAIL**: 任一已发送探针不满足判定（含 criterion_failure / http_error / transport_failure）→ STOP_THIS_PANEL 永久（不再第五轮）。」
- 「**ENGINEERING_INCOMPLETE**: 零传输类工程故障（如服务启动失败、健康检查失败）；最多允许修复后重试一次（上限 2 次启动、共 2 轮执行）；冻结组件 / prompt / schema 一律不得改动；否则停报。」
- 依据行: 「通过 → 恢复 S4（S4c）；不通过 → STOP_THIS_PANEL 永久、不再第五轮」。

推导: 第 1 轮＝零传输工程故障（incident 1；`model_requests` 保持 0、未写 attempts/ledger），按 ENGINEERING_INCOMPLETE 消耗"一次修复重试"（卡 v1.1 修正记录）；第 2 轮探针 1 **已传输**（服务计数 0→1、全局预算 9→10）且 HTTP 400（`http_error`）→ 命中 FAIL 条款。零传输豁免不适用（存在传输）；修复额度已用尽（2 轮上限已到，不设第五轮）。未发现任何支持其他判读的文本路径。

## 2. 证据完整性 — PASS（逐件重算一致，双端）

- `raw_response.txt` sha256＝`432abf2e…6aa72`＝台账＝运行结果＝收据（本地＝GB10）。
- 台账 `ACTOR_CALL_LEDGER_QUAL.json`: http_status=400、criterion_met=false、counted_attempt=true、transport_retries=0；accounting: this_card_requests_attempted=1；budget: global_attempts_used_before=9、this_card_max_requests=3、hard cap 300。
- `request.json`（sha `27ded023…` 双端一致）: model=`tatqa-wp2-qwen3-8b-b968826d`、schema_stage=plan、max_tokens=512、temperature=0、n=1、transmission_state=about_to_transmit（persist-first）；`task_prompt_sha256=f24f86dd…bbd4` 与 `PROBES_FROZEN.json` probes[0] 一致，且由 prompt 原文独立重算一致、字符串逐字相同。
- 冻结件双端重算: 卡 `25038c0f…`、probes 文件 `061f871f…`、runner `d7afa021…`（v1.1）、生成器 `9a8ac83c…`、validator `c4fc4feb…` —— 全部一致。
- 预检 `PREFLIGHT_RENDER_RECEIPT.json`: status=PASS、runner=v1.1、tokens=[607,332,406]、component_hashes.all_match=true（10/10 独立重算一致）、源链接哈希一致（失败 prompt `6c5be077…` 在 `s4b_run/attempts/S4_history-01-wp2_3ab739eb_r2_p0-plan-3/prompt.txt` 就地复算确认；协议收据 `58d76d37…` 复算一致）；round-1 预检件按声明归档在位。
- `attempts/` 恰好 1 个探针目录（request/raw/failure_record 3 件）；`completion.txt`/`validation_result.json` 缺失（http_error 下符合预期）。

## 3. 冻结件不可变性 — PASS

- 5 个 bridge_v2 组件本地＋GB10 重算与 `BRIDGE_V2_RECEIPT.json` 逐项一致（constrained_decoding_v2.py `5ee7ab8a…`、prompt_v2.py `f4b20727…`、validate_v2.py `c4fc4feb…`、serve_transformers_actor_v2.py `f3182bd2…`、BRIDGE_SCHEMAS_v2.json `dc144259…`）。
- `git diff 6bed50c`、`git diff 0e429f7` 对 bridge_v2 均为空；`git status` 干净；bridge_v2 最后触达提交＝`7512687`（早于冻卡 `6bed50c` 与修复 `0e429f7`）；双端 HEAD 均为 `0e429f7`。事故后无任何组件修复/漂移。

## 4. 根因可复现性 — PASS（GB10 零模型复跑逐字段一致）

重跑 `processor_interface_diagnosis.py`（stdout）与 `processor_interface_diagnosis_output.json`（sha `653ca698…`，双端一致）逐字段一致:

- transformers `5.14.1`；`LogitsProcessor.__call__`＝`(self, input_ids, scores)`（input_ids 前位）；
- 真实调用点 `generation/utils.py:2910`: `next_token_scores = logits_processor(input_ids, next_token_logits)`；
- `(input_ids, scores)` → `OverflowError: out of range integral type conversion attempted`（traceback: `constrained_decoding_v2.py:303 → :283 tokenizer.decode`）；
- `(scores, input_ids)`（离线干跑所用约定）→ 不抛错；
- `decode([-12])`、`decode([10**10])` 复现同一 OverflowError；`decode([0])` 正常。

执行方根因声称成立；离线资格未走真实调用路径的覆盖缺口与其 `unverified_surfaces=["online GPU constrained decoding"]` 披露吻合。附注: 探针 context（1437 字符 JSON）经字节级复核为 plan-3 源 prompt 的 verbatim 子串（provenance 声明成立）；probe 尾部指令脚手架与源 prompt 段落存在差异（STAGE 标记位置、省略 FORMAT_EXAMPLE 段），不影响任何冻结 pin。

## 5. 服务生命周期 — PASS

- service_stopped.txt=SIGTERM；port_8112_after="8112 released"；prod_ports_after=8004/8006 原样；llama_pid_after=pid 2642808 存活（现况 8004 仍在听）；mem_after available 38264MB；service_log_traceback_count=0（我对 `service.log` 逐条重扫 Traceback＝0）；health_before_stop: model_requests=1、status=READY。
- GB10 现况只读复核: 8112 未监听（已释放）、8004/8006 正常在听；未向 8004 发任何请求。
- 小观察（非阻断）: 卡"产物"清单列的 `service/SERVICE_STOP_RECEIPT.json` 无同名件；停止证据由 `service_stopped.txt` 等现件承担（收据未引用该文件名，实质完备）。

## 6. 收据 vs 证据 — PASS

- `S4C_ONLINE_QUALIFICATION_RECEIPT.json` 全部 pin（卡/probes/runner/validator/5 组件/预检/探针/会计 9→10/incidents 1&2/probes_not_run 两条/service_lifecycle）逐项对上；`components_unchanged_post_hoc=true` 有 git 一手支撑；未发现任何不一致。
- 会计四路一致: 本卡 1 请求、0 传输重试、judge/db/training/生产调用全 0。

## 7. FAIL 后无泄漏 — PASS

- 台账 / attempts / 运行结果 / 服务 model_requests 四路一致＝1；无第二、第三探针写入。
- wp2 无 S4c/S5–S9 产物；GB10 `git status` 未跟踪集合＝既知结果包 9 项（与本地一致），无额外文件。

## 8. 结论与异议

**PASS（无异议）**。次要观察（不改判定）: §5 的停止收据命名、§0 的未验证面、§4 附注的 probe/源 prompt 脚手架差异；建议纳入 Loop D 收尾提交的披露清单。

---

审计者: Loop C（/root/loopc_s4c_audit，fresh context）| 本文件为本次审计唯一写入件 | 2026-10-14
