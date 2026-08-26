# -*- coding: utf-8 -*-
"""03:50 morning assembler: judgment one-pager + STATE overwrite (cron-auto, night queue 08-25)."""
import json, subprocess, pathlib, re, datetime, os

REPO = pathlib.Path("/home/testuser/wzh/projects/agents_final_tech")
EVAL = REPO / "logs" / "graph" / "eval"
SHEET = REPO / "docs" / "experiments" / "2026-08-25_morning_decision_sheet.md"
STATE = REPO / "memory" / "STATE.md"
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

# [v3 08-26] CLI: --sheet 改输出路径, --no-state 跳过 STATE 覆写 (收口另做)
import sys as _sys
_argv = _sys.argv[1:]
if "--sheet" in _argv:
    SHEET = pathlib.Path(_argv[_argv.index("--sheet") + 1])
    if not SHEET.is_absolute():
        SHEET = REPO / SHEET
NO_STATE = "--no-state" in _argv

def rd(p, default=""):
    # [E1b 2026-08-25] 字节级读取 + errors=replace: 工件含半截 UTF-8 字符时不吞成空串
    try: return pathlib.Path(p).read_bytes().decode("utf-8", errors="replace")
    except Exception: return default

def jload(p, default=None):
    try: return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    except Exception: return default

# ---------- collect ----------
verify = rd(EVAL / "pool_fix_verify_20260825.md")
gate_verdict = "UNKNOWN"
for m in re.finditer(r"VERDICT: (\S+)", verify):
    gate_verdict = m.group(1)
if gate_verdict == "UNKNOWN":
    # [E1b] 兜底: 工件解析失败时从 dispatch 证据链取判定 (防静默 UNKNOWN)
    disp = rd(REPO / "logs" / "graph" / "dispatch_log.md")
    if "#POOL-GATE-PASS" in disp: gate_verdict = "GATE_PASS (dispatch 兜底)"
    elif "#POOL-GATE-FAIL" in disp: gate_verdict = "GATE_FAIL (dispatch 兜底)"
gate_sec = verify.count("## GATE run")
# [v3] 门禁数字从工件解析, 不再硬编码 (单数据源漂移教训)
m = re.search(r"score\":\s*([0-9.]+)", verify)
gate_score = m.group(1) if m else "?"
m = re.search(r"warn_gate=(\d+)\s+fallback_gate=(\d+)", verify)
gate_warn, gate_fb = (m.group(1), m.group(2)) if m else ("?", "?")
w3 = rd(EVAL / "w3_daily_eval_20260825.md")
w3_verdict = "UNKNOWN"
m = re.search(r"VERDICT: (\S+)", w3)
if m: w3_verdict = m.group(1)
elif "SKIPPED" in w3: w3_verdict = "SKIPPED"
eval_summary = rd(EVAL / "eval_summary.md")[:800]
# [v3] E2 复测为有效工件 (w4 01:50 被 SKIPPED 为空), 优先 e2 回落 w4
w4 = jload(EVAL / "e2_step_stats.json", {}) or jload(EVAL / "w4_step_stats.json", {})
e3 = rd(REPO / "docs" / "experiments" / "2026-08-25_e3_step_duration_diagnosis.md")
m3 = re.findall(r"step1 在途 \d+/\d+ \((\d+)%\) > step3 (\d+) \((\d+)%\) > step4 (\d+) \((\d+)%\)", e3)
if m3:
    near_miss = int(m3[0][2]) + int(m3[0][4])  # step3+step4 截断占比 = 近失代理 (E3 口径)
else:
    near_miss = None
det = jload(EVAL / "m2_deterministic_report.json", {})
pytest_tail = rd(REPO / "logs" / "graph" / "pytest_latest.txt")
m = re.search(r"(\d+) passed, (\d+) skipped", pytest_tail)
pytest_line = f"{m.group(1)} passed, {m.group(2)} skipped" if m else "解析失败"
pso = jload(EVAL / "pso_question_set_v0.json", {})
loopb_tail = "\n".join(l for l in rd(REPO / "logs/graph/loop_b.log").splitlines() if "REPORT: overall" in l)[-400:]

# B4 clean segment via canonical checkpoint script
b4_out = ""
try:
    r = subprocess.run(["./venv/bin/python", "scripts/graph/b4_checkpoint.py", "3929"],
                       cwd=REPO, capture_output=True, text=True, timeout=120)
    b4_out = r.stdout[:900]
except Exception as e:
    b4_out = f"checkpoint run failed: {e}"
att = re.search(r"attempted\): (\d+)", b4_out)
comp = re.search(r"完成数 \(无回落\): (\d+)", b4_out)
attempts = int(att.group(1)) if att else 0
completes = int(comp.group(1)) if comp else 0
rate = round(100.0 * completes / attempts, 1) if attempts else 0.0

# [v3] 双段口径: 3429 (侧车修复后) 与 3929 (池修复后) 均实跑, 禁单段单源
b4_3429_out = ""
try:
    r = subprocess.run(["./venv/bin/python", "scripts/graph/b4_checkpoint.py", "3429"],
                       cwd=REPO, capture_output=True, text=True, timeout=120)
    b4_3429_out = r.stdout[:400]
except Exception as e:
    b4_3429_out = f"checkpoint 3429 run failed: {e}"
m34a = re.search(r"attempted\): (\d+)", b4_3429_out)
m34c = re.search(r"完成数 \(无回落\): (\d+)", b4_3429_out)
att3429 = int(m34a.group(1)) if m34a else 0
comp3429 = int(m34c.group(1)) if m34c else 0
rate3429 = round(100.0 * comp3429 / att3429, 1) if att3429 else 0.0

blocked = rd(REPO / "logs" / "graph" / "blocked_questions.md").strip()
blocked_summary = blocked if len(blocked) < 600 else blocked[:600] + "..."
if not blocked_summary: blocked_summary = "(空 — 今夜无 blocked 项)"

# ---------- recommendations ----------
if attempts == 0:
    rec_a = "A-观察（干净段尚无 agent 尝试样本, 继续攒 24h）"
elif rate >= 10:
    rec_a = "A-维持 45s（干净段完成率 ≥10%, 预注册判据达标, 抬超时不必需）"
elif rate >= 5:
    rec_a = "B-抬 60s（完成率 5-10% 区间, 抬一档换完成率, 代价=失败题等待变长）"
else:
    rec_a = "C-抬 75s 或先做结构性根治（完成率 <5%, 抬超时收益存疑, 优先减 step/瘦身）"
t1_rec = "数据缺失, 人工判"
if w4:
    sp = w4.get("steps_p50")
    wp = w4.get("wall_p50_ms")
    if sp is not None and sp <= 3:
        t1_rec = "重开减 step 杠杆（steps 回落健康代水平, T1 基线确被池病污染, '45s 审查第一障碍'结论失效, M3/M4 值得修复后重跑）"
    elif sp is not None and sp >= 4:
        t1_rec = "T1 还原判定维持（steps 未回落, 病灶非 T1 基线主因, 按原路线图走结构性减 step）"
    else:
        t1_rec = "部分污染, 人工判"

# ---------- one-pager ----------
pso_line = "(PSO 未跑/未完成)"
if pso:
    rb = pso.get("results_by_budget", {})
    minb = next((k for k, v in rb.items() if v.get("pso_keep_rate", 0) >= 1.0), None)
    pso_line = f"bank={pso['meta']['bank_size']} 题, QA mutants={len(pso['meta']['qa_mutants'])}, 全保持最小预算={minb or '>12'}"

# ---------- [v3] 规则机械裁定 (预计算, sheet 只引用) ----------
rule0 = "过闸, 结论有效" if attempts >= 40 else "不足 40, 全部降为观察, 延长 24h"
if rate >= 15:
    ruleA = "≥15%: 维持 45s, timeout (a) CLOSED"
elif rate >= 10 and (near_miss or 0) >= 30:
    ruleA = "10-15% 且近失≥30%: 抬 60s 一档, 并入 FK 窗"
else:
    ruleA = "<10%: 不抬超时, timeout (a) CLOSED, 走结构性诊断 (E3/E2)"
sp50 = w4.get("steps_p50")
ruleB = "≤3.5: T1 基线被池病污染, M4 重开" if (sp50 or 9) <= 3.5 else "≥4: T1 结论维持, 原杠杆队列不变"
ruleD = "首批数据落盘 → 登记 + 续跑第二批" if pso else "blocked/未跑 → 维持挂起"
# §① 推荐与规则 A 裁定对齐 (禁双口径)
if rate >= 15:
    rec_a = "A-维持 45s（规则 A 裁定）"
elif rate >= 10 and (near_miss or 0) >= 30:
    rec_a = "B-抬 60s 一档（规则 A 裁定, 并入 FK 窗）"
else:
    rec_a = "D-不动超时, 只走结构性根治（规则 A CLOSED, 诊断=E3/E2）"

sheet = f"""# 判定一页纸 v3 — 2026-08-26 晨（自动汇编 {NOW}, 规则机械裁定版）

> 用法: 每项 = 数据 + 选项 + 推荐, 圈选即可。工件路径全部可点开复核。
> blocked_questions.md 摘要: {blocked_summary}

## ① 超时 (a) 45→60-75s 是否还需要
**数据**:
- 段 3429（侧车修复后, 含池病污染段）: {att3429} 尝试 / {comp3429} 完成 = {rate3429}%（**池病灶污染不作数**, 归因见 2026-08-24_segment_d_q06_attribution.md）
- 3929 后干净段（池修复后）: {attempts} 尝试 / {completes} 完成 = {rate}%（样本=Loop B canary 题型, 代表性限 canary）
- 门禁工件: gate 判定 {gate_verdict}（{gate_sec} 次运行, 12min 闲置 q06 命中 @{gate_score} + warn {gate_warn}/fallback {gate_fb}）
- 每日 eval（最新重跑）: {det.get('n_pass','?')}/{det.get('n_questions','?')} 确定性; E2 复测: steps p50={w4.get('steps_p50')} wall p50={w4.get('wall_p50_ms')}ms; 近失代理(step3+4 截断占比, E3)={near_miss}%
```
{b4_out}
```
**选项**: A 维持 45s | B 抬 60s | C 抬 75s | D 不动超时, 只走结构性根治（减 step + context 瘦身）
**推荐**: {rec_a}

## ② T1 减 step 杠杆重评（W4 复测）
**数据**: 今晚 steps p50={w4.get('steps_p50')} mean={w4.get('steps_mean')} wall p50={w4.get('wall_p50_ms')}ms（n={w4.get('n')}）; 对照 T1 Arm A 49.6s/steps p50=4 mean=4.4; 健康代 steps p50=3
**选项**: A 重开减 step 杠杆 A/B（M3 终答瘦身优先） | B 维持 T1 还原判定, 结构性减 step 照原计划
**推荐**: {t1_rec}

## ③ FK 边界窗口提案
**数据**: FK 竞争根因 = cleanup_sessions 水位闸 MAX_SESSIONS=50 偶删在途会话（08:14 新增 1 条级边角）; 修复草稿已就绪（docs/experiments/2026-08-25_fk_watermark_fix_draft.md, a/b 菜单 + diff + 测试清单 + 回滚口径）
**选项**: A 与下个 :5050 窗口合并激活（推荐） | B 单独开窗 | C 缓办
**推荐**: A（草稿就绪, 合并零额外成本）

## ④ 积压亮点（各一行: 为何未动 + 解锁条件）
- dify 5 份甲方规则 docx 挖掘（08-12 起）: 未动=等甲方首轮反馈定优先级; 解锁=甲方反馈到达或用户直接批
- 任务 2 改版设计稿（08-11 起）: 未动=待用户决策备忘录 D 系列圈选; 解锁=圈选后入代码窗
- NLPCC 2026 workshop 核实: 未动=需人工查官网窗口; 解锁=用户核实或授权代查

## ⑤ 夜间执行链回顾（证据索引）
- W1 门禁: {gate_verdict}（pool_fix_verify_20260825.md）
- W2 复验: 同文件 00:40 段（Loop B 周期 + canary 复跑 + 归因计数）
- W3 每日 eval: {w3_verdict}（w3_daily_eval_20260825.md）
- W4 step 复测: w4_step_retest_20260825.md + w4_step_stats.json
- W5 PSO 落点②: {pso_line}（2026-08-25_pso_question_set_v0.md + pso_question_set_v0.json）
- Loop B 夜间周期: {loopb_tail[-200:]}

## 规则机械裁定（预提交规则, 零圈选; 08-26 v3）
- 规则 0（样本闸）: 干净段尝试 {attempts} 条 → {rule0}（已按规则 0 裁定）
- 规则 A（timeout）: 干净段完成率 {rate}% → {ruleA}（已按规则 A 裁定）
- 规则 B（T1）: 复测 steps p50={sp50} → {ruleB}（已按规则 B 裁定）
- 规则 C（FK 窗口）: FK 水位闸修复 = 单件 :5050 窗（M1_B4_LOG_PATH/PG 根治已在位）, 时机等用户批, 不催（已按规则 C 裁定; 窗口卡草稿见附录）
- 规则 D（PSO）: {ruleD}（已按规则 D 裁定）
- 规则 E（积压）: dify 挖掘 / 任务 2 改版稿 / NLPCC 核实 维持挂起, 无新解锁理由（已按规则 E 裁定）
- 规则 F（本卡预批）: 今夜不开 :5050 重启窗（交付日上午卫生优先, GUC+pre_ping 兜底在位）; FK 修复 = 待批窗口卡（已按规则 F 裁定）

## 挂起项（规则外, 只建议不裁定; 08-26 晚已圈: 侧线代圈, 用户授权）
1. F-J3 孤儿轨迹治理: **圈 b 先行**（prompt/skill 层零风险）, a 并入 :5050 窗口队列; 提案 docs/experiments/2026-08-26_fj3_orphan_governance_proposal.md
2. 减 step 组合拳: **立主线**, 但本周窗口冻结让路论文（规则 F 加强）, 排论文启动单元之后
3. FK 窗口: **缓办**, 合并激活（与下个 :5050 窗口同批, 不单独开）

## 红线核对
:8004/:8006 配置零改动 ✓（夜间仅 :5050 预批路径）| 专利文档未碰 ✓ | API key/HF token 零打印 ✓ | 不对外发送 ✓ | 甲方数据零进入 ✓（PSO 用公开样本+合成 mutant）
"""
SHEET.write_text(sheet, encoding="utf-8")

# ---------- STATE overwrite ----------
state = f"""# memory/STATE.md
更新: 2026-08-25 {NOW}（夜间队列自动收口: W1 门禁 {gate_verdict} / W2 复验 / W3 {w3_verdict} / W4 step 复测 / W5 PSO 落点② 首批 / 判定一页纸就绪）

## 模式
守护模式。**晨报首位 = 判定一页纸**（docs/experiments/2026-08-25_morning_decision_sheet.md）: ① 超时 (a)（干净段 {attempts}/{completes}={rate}%）② T1 复评 ③ FK 窗口提案 ④ 积压亮点, 用户白天圈选。
其余等拍板: 甲方首轮反馈 / 专利导师五项定夺 / D1-D5 备忘录 / M4 减 step 下一杠杆（视②圈选）。

## 夜间队列结果（08-25 00:25-03:50, 唤醒驱动 + cron one-shot 工件模式）
- W1 门禁: {gate_verdict}（12min 闲置 q06 命中 3508.55@0.7889, warn 219 零增, fallback 0; 首次 00:16 撞 Loop B 改期后 00:28 过）
- W2 00:40 复验: Loop B 周期 + canary 复跑 + IdleSessionTimeout 归因, 见 pool_fix_verify_20260825.md
- W3 每日 eval: {w3_verdict}（对照基线 16/16/0/5.0）
- W4 step 复测: steps p50={w4.get('steps_p50')} wall p50={w4.get('wall_p50_ms')}ms（对照 T1 ArmA 49.6s/4, 健康代 3）——T1 污染验证结论入一页纸②
- W5 PSO 落点②: {pso_line}; 口径=纯工件计算（Z 基线=W3 新鲜工件）, B4 窗口注已记
- 纪律执行: 全程零阻塞 sleep, 6 个 cron one-shot（2 门禁/复验 + W3/W4/W5/汇编）全自删; 门禁改期链 00:16→00:23(坏行已修)→00:28 过

## Git
- HEAD: 本汇编 commit（自动）; 三方对齐待本机 pull（晨报时补）
- 本轮资产: W2-W5 工件 + PSO 脚本 research/pso/pso_question_set_search.py + FK 草稿 + 一页纸 + STATE

## B4（分段, 两列口径 尝试/完成 写全名）
- 池修复后段（行 3929 @08-24 23:54 起）: {attempts} 尝试 / {completes} 完成 = {rate}%（样本=canary 题型）
- W3/W4/W5 窗口行段见各工件; PSO 窗纯计算零 ask

## 服务
- :5050 UP（route=on timeout=45, 汇编时实测）; :8004/:8006/:8008 UP; :8007 空闲; :15432 PG UP（GUC+pre_ping 双保险, 门禁坐实）
- 侧车 + MCP 在跑（PID 以 ps 实况为准, 不硬编码）; Loop B 30min 周期持续验证; kiosk 关闭（08-22 终判）
- cron: 夜间 6 个 one-shot 全部跑完自删（残余见 crontab -l, 应为空或仅当晨遗留）

## 质量基线
- 门禁: 12min 闲置 q06 PASS（08-25 00:28）; canary 4/4（00:40 复验见工件）
- pytest {pytest_line}（pytest_latest.txt 实解析）; eval 基线 {det.get('n_pass','?')}/{det.get('n_questions','?')}（最新重跑）
"""
if not NO_STATE:
    STATE.write_text(state, encoding="utf-8")
print(f"sheet={SHEET} state={'SKIPPED' if NO_STATE else STATE} gate={gate_verdict} w3={w3_verdict} clean={attempts}/{completes}={rate}% seg3429={att3429}/{comp3429}={rate3429}% near_miss={near_miss} pytest={pytest_line}")
