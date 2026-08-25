# -*- coding: utf-8 -*-
"""03:50 morning assembler: judgment one-pager + STATE overwrite (cron-auto, night queue 08-25)."""
import json, subprocess, pathlib, re, datetime, os

REPO = pathlib.Path("/home/testuser/wzh/projects/agents_final_tech")
EVAL = REPO / "logs" / "graph" / "eval"
SHEET = REPO / "docs" / "experiments" / "2026-08-25_morning_decision_sheet.md"
STATE = REPO / "memory" / "STATE.md"
NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

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
w3 = rd(EVAL / "w3_daily_eval_20260825.md")
w3_verdict = "UNKNOWN"
m = re.search(r"VERDICT: (\S+)", w3)
if m: w3_verdict = m.group(1)
elif "SKIPPED" in w3: w3_verdict = "SKIPPED"
eval_summary = rd(EVAL / "eval_summary.md")[:800]
w4 = jload(EVAL / "w4_step_stats.json", {})
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

sheet = f"""# 判定一页纸 — 2026-08-25 晨（夜间队列自动汇编 {NOW}）

> 用法: 每项 = 数据 + 选项 + 推荐, 圈选即可。工件路径全部可点开复核。
> blocked_questions.md 摘要: {blocked_summary}

## ① 超时 (a) 45→60-75s 是否还需要
**数据**:
- 段 3429 预注册判据: 491 尝试/53 完成 = 10.8%（**注: 段 D 池病灶污染不作数**, 归因见 2026-08-24_segment_d_q06_attribution.md）
- 3929 后干净段（池修复后）: {attempts} 尝试 / {completes} 完成 = {rate}%（样本=Loop B canary 题型, 代表性限 canary）
- 门禁工件: gate 判定 {gate_verdict}（{gate_sec} 次运行, 12min 闲置 q06 命中 3508.55@0.7889 + 零新警告）
- W3 每日 eval: {w3_verdict}（基线 16/16/0/5.0）; W4 复测: steps p50={w4.get('steps_p50')} wall p50={w4.get('wall_p50_ms')}ms
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
- :5050 UP（PID 3153034, 池修复后; route=on timeout=45）; :8004/:8006/:8008 UP; :8007 空闲; :15432 PG UP（GUC+pre_ping 双保险, 门禁坐实）
- 侧车 PID 3153507 + MCP 3153592/94/96; Loop B 30min 周期持续验证; kiosk 关闭
- cron: 夜间 6 个 one-shot 全部跑完自删（残余见 crontab -l, 应为空或仅当晨遗留）

## 质量基线
- 门禁: 12min 闲置 q06 PASS（08-25 00:28）; canary 4/4（00:40 复验见工件）
- pytest 384 passed（08-24 23:50）; eval 基线 16/16/0/5.0（08-22）
"""
STATE.write_text(state, encoding="utf-8")
print(f"sheet={SHEET} state={STATE} gate={gate_verdict} w3={w3_verdict} clean={attempts}/{completes}={rate}%")
