---
# 机读元信息（面向未来 A→B→C 自动分发, 见 docs/29 附录前置清单 ①）
id: TASK-20260823-01
risk: low
window: 2026-08-22 晚已执行（23:30-00:53）  # 裁定与数据见 docs/experiments/2026-08-23_l1_thinking_matrix.md
premises:
  - id: P1
    claim: ":8006 qwen38-27b-fp8 健康(非 DSpark 回滚栈, GMEM 0.30 观察期)"
    falsify: "curl -sS http://127.0.0.1:8006/v1/models | grep qwen38-27b-fp8"
  - id: P2
    claim: "生产默认 thinking=OFF(opencode 两份配置均无 reasoning_effort)"
    falsify: "grep reasoning_effort opencode.json ~/.config/opencode/opencode.jsonc"
  - id: P3
    claim: "注入格式被 :8006 接受(chat_template_kwargs.enable_thinking + 顶层 reasoning_effort)"
    falsify: "动作序第 0 步冒烟: medium 1 问, reasoning_tokens>0 且 200"
  - id: P4
    claim: "fixture 冻结只读可用"
    falsify: "ls -la tests/fixtures/m2_eval_questions.json"
  - id: P5
    claim: "注入不影响生产默认口径(矩阵全程直连 :8006, 不经 :5050/opencode)"
    falsify: "opencode.json 与 ~/.config/opencode/opencode.jsonc 窗口前后 sha256 对比 + :5050 health/full 前后对比"
  - id: P6
    claim: "侧车状态不影响矩阵有效性: 矩阵腿全程直连 :8006(--endpoint 指向 8006), 不经 :5050/侧车"
    falsify: "grep endpoint 本卡动作序全部命令; 08-22 已实证(侧车重启+DB 重建后直连探针照常)"
  - id: P7
    claim: "窗口起点侧车状态已记录(供 B4 解读, 不构成矩阵前置)"
    falsify: "动作序第 0 步记一行侧车健康+agent 路完成状况入验收表"
acceptance:
  - "sha256sum opencode.json ~/.config/opencode/opencode.jsonc  # 与窗前快照一致"
  - "curl -sS http://127.0.0.1:5050/api/health/full  # 137/local/healthy 不变"
  - "git status --porcelain  # 窗口内无新增配置类 diff"
  - "ls logs/graph/eval/l1_medium_report.json logs/graph/eval/l1_xhigh_report.json logs/graph/eval/l1_nf_*.json logs/graph/eval/l1_judge_*.json"
rollback: "无配置变更, 无需回滚; 若误动生产配置 → git checkout 恢复 + sha256 对照快照"
redlines:
  - ":5050 不重启; :8004/:8006 配置不动(:8006 GMEM 0.30 观察期, 容器不重起)"
  - "不对外发送; 甲方数据零进入(fixture 为公开口径题库)"
  - "错峰执行, 与 B4 金丝雀争 :8006 slot 时如实注记噪声, 不掩饰(kiosk 08-20 起停摆待处置, 缺位=窗口利好)"
---

# 任务卡: L1 thinking 档位裁定矩阵 (medium / xhigh)

> 按 templates/task_card_template.md 体例。背景: 拍板一(08-22)——L2 更正坐实生产 m2-qa thinking 实际 OFF, "xhigh 轨迹超预算"旧归因作废; off 现状已有生产数据(B4 + 08-22 eval 16/16 PASS direct)不重跑, 本矩阵只补 medium / xhigh 两腿, 为"准路默认档"裁定提供质量×延迟数据。08-19 "xhigh 起步"批复标前提失效, 待本矩阵复测。

## 1. 目标

在回滚后的干净栈(:8006 非 DSpark)上, 跑 medium / xhigh 两腿固定题库, 产出三方对照表(off 用历史生产数据): 确定性 16 题通过率 / NF 9 题 / judge 四维均分 / 每题端到端 wall_ms 分布 / reasoning_tokens 分布。验收 = 三方对照表完整 + 还原验证全过 + go/no-go 建议一行。

go 判据(沿用队列口径): 质量不降(16/16, NF 0/9, judge ≥4.9)且延迟实质下降 → 该档可作准路默认候选报用户批窗口; 质量降 → 数据入账, 准路维持现状, 重心转"减 step"第一梯队。

## 2. 前提假设清单（必填）

| # | 假设 | 一分钟证伪方式 | 实测结论（执行前填） |
|---|------|----------------|----------------------|
| P1 | :8006 qwen38-27b-fp8 健康 | curl -sS http://127.0.0.1:8006/v1/models | ✅ 08-22 13:38 坐实(max_model_len 32768) |
| P2 | 生产默认 thinking=OFF | grep reasoning_effort opencode.json ~/.config/opencode/opencode.jsonc | ✅ 08-22 13:38 坐实(双配置 0 命中) |
| P3 | 注入格式被 :8006 接受 | 动作序第 0 步冒烟 1 问 | ✅ 08-22 23:49 冒烟复跑 PASS（首冒烟命中测量盲区: details.reasoning_tokens 本 build 不产, runner 补丁 fallback=len(reasoning), 报告 §三） |
| P4 | fixture 冻结只读 | ls -la tests/fixtures/m2_eval_questions.json | ✅ 08-22 13:38 坐实(6767B, 08-09) |
| P5 | 注入不影响生产默认口径 | sha256 前后对比 + health/full 前后对比 | ✅ sha256 前后窗一致（8cb44e40…/4e901f9e…）, health/full 137 一致 |
| P6 | 侧车状态不污染矩阵结论 | 动作序命令 --endpoint 均为 :8006 直连 | ✅ 08-22 实证: 侧车重启+DB 重建后直连探针照常; 腿不经侧车, 依赖不成立 |
| P7 | 窗口起点侧车状态已记录 | 第 0 步记侧车健康+agent 路状况入验收表 | ✅ 08-22 23:30 侧车 :4096=200; B4 段 3429 口径 65 尝试/11 完成 回落率 83.1% |

> 规则: P3/P5 未验证不许进腿; 冒烟失败 = 停下报用户, 不带假设硬跑。

## 3. 动作序

0. 前提复检 + 冒烟: P1/P2/P4 复跑一遍 → 记录 opencode.json 与 ~/.config/opencode/opencode.jsonc 的 sha256 快照 + :5050 health/full 快照 → 直连 :8006 冒烟 2 问(medium 1 问 + xhigh 1 问, 用 run_matrix_candidate.py --only 第 1 题), 确认 200 且 reasoning_tokens>0(xhigh)与响应正常; 任一失败 → 中止报用户
1. medium 腿(确定性 16 题):
   ./venv/bin/python scripts/run_matrix_candidate.py --endpoint http://127.0.0.1:8006/v1/chat/completions --model qwen38-27b-fp8 --label l1_medium --thinking medium --max-tokens 4096 --out logs/graph/eval/l1_medium_report.json
2. xhigh 腿(同题, 防截断 4096):
   ./venv/bin/python scripts/run_matrix_candidate.py --endpoint http://127.0.0.1:8006/v1/chat/completions --model qwen38-27b-fp8 --label l1_xhigh --thinking xhigh --max-tokens 4096 --out logs/graph/eval/l1_xhigh_report.json
3. NF 两腿(各 9 题, 直连同口径, --det-report 指向对应腿报告):
   ./venv/bin/python scripts/m2_eval_number_faithfulness.py --endpoint http://127.0.0.1:8006/v1/chat/completions --model qwen38-27b-fp8 --thinking medium --det-report logs/graph/eval/l1_medium_report.json --out logs/graph/eval/l1_nf_medium.json
   ./venv/bin/python scripts/m2_eval_number_faithfulness.py --endpoint http://127.0.0.1:8006/v1/chat/completions --model qwen38-27b-fp8 --thinking xhigh --det-report logs/graph/eval/l1_xhigh_report.json --out logs/graph/eval/l1_nf_xhigh.json
4. judge 两腿(走 :8004, 吃对应腿报告, 与基线同路径):
   ./venv/bin/python scripts/m2_eval_judge.py --input logs/graph/eval/l1_medium_report.json --report logs/graph/eval/l1_judge_medium.json
   ./venv/bin/python scripts/m2_eval_judge.py --input logs/graph/eval/l1_xhigh_report.json --report logs/graph/eval/l1_judge_xhigh.json
5. 汇总三方对照表入实验文档(建议 docs/experiments/2026-08-23_l1_thinking_matrix.md): off 列引 08-22 eval 与 B4 历史数据(记引用不重跑); 每腿列: 16 题通过数 / NF 未落地数 / judge 四维均分 / wall_ms p50·p95 / reasoning_tokens p50·p95·max; 附"agent 路端到端推算"注记(端到端 ≈ step 数 × 单步延迟, step 数另见减 step 菜单, 本矩阵只测单步直连)
6. 还原验证(验收清单第一项): sha256 复验两份 opencode 配置与快照一致 + :5050 health/full 复验 + git status 无配置类 diff + **窗口起点侧车状态行**(侧车健康与否 + agent 路当时完成状况, 供 B4 解读) → 全过才算收口

## 4. 中止条件

- 冒烟注入失败(400 / reasoning_tokens 恒为 0 / 响应异常) → 停下报用户, 不跑腿
- 任一腿脚本退出码 2(端点/集合不可用) → 停下, 查 :8006 健康; 不碰容器, 报用户
- 窗口内 :8006 health 异常或 Loop B model_topology 翻转 → 立即停, 记台账报用户
- Loop B 金丝雀争用导致单题延迟显著偏离(>2x 同腿中位) → 记噪声注记继续跑, 不中断(如实汇报)

## 5. 验收证据表

按 templates/acceptance_checklist_template.md 填写, 预置行:

| 声明 | 验证命令 | 实测值 |
|------|----------|--------|
| 生产配置未动(还原第一项) | sha256sum opencode.json ~/.config/opencode/opencode.jsonc 对比窗前快照 | ✅ 一致（8cb44e40…/4e901f9e…） |
| :5050 未受影响 | curl -sS http://127.0.0.1:5050/api/health/full | ✅ healthy 137/local 一致 |
| medium 腿完成 | jq '.overall' logs/graph/eval/l1_medium_report.json | FAIL 13/16（3 例未过构成见报告 §四） |
| xhigh 腿完成 | jq '.overall' logs/graph/eval/l1_xhigh_report.json | ✅ PASS 16/16 |
| NF/judge 四工件在位 | ls logs/graph/eval/l1_nf_*.json logs/graph/eval/l1_judge_*.json | ✅ 四工件在位 |
| 注入冒烟证据 | 冒烟响应 reasoning_tokens 值 | medium 606 / xhigh 517 字符（len fallback 口径） |

## 6. 汇报格式

三方对照表(off/medium/xhigh) + 每腿 wall_ms 与 reasoning_tokens 分布 + go/no-go 建议一行(引判据) + 还原验证结果 + 实际执行耗时 + 窗口内 :8006 slot 争用注记(有/无)。

## 7. 红线

- :5050 不重启; :8004/:8006 配置一律不动(:8006 GMEM 0.30 观察期, 容器不重起, 只读使用)
- 不对外发送; 甲方数据零进入(fixture 为公开口径题库)
- Loop B 不扰(窗口内 ALARM 记台账不处置)
- 错峰执行: kiosk 已正式关闭(08-20 停摆归因 = 窗前暂停未复活, 08-22 终判选项 B 确认关闭, 提案归档), 争 :8006 slot 仅与 Loop B 金丝雀(每 ~30min 周期 3-5 题, 单题 46-50s 超时回落或预算内完成)属预期, 延迟数字带噪声注记, 不修饰

## 口径注记

- 矩阵直连 :8006 单步延迟 ≠ agent 路端到端延迟; 准路根治延迟预期须拼接减 step 菜单(docs/experiments/2026-08-22_step_reduction_menu.md)的 step 算术, 不许外推
- reasoning_tokens 若 usage.completion_tokens_details 缺省, 退而记 reasoning 字段长度估算并注明口径
- 侧车修复与矩阵的关系(08-22 核实): 腿直连 :8006, 侧车修复不是矩阵硬前置; 若未来腿改经 route=on/agent 路, 则侧车健康+45s 预算为硬前置(当日实测 5-6 步 ≈46-60s 超预算, 见 #SIDECAR-VERDICT)
- 本卡与 08-19 "xhigh 起步"批复的关系: 该批复前提失效(见 THREADS 更正条目), 本矩阵即复测裁定, 结论出后由用户拍板准路默认档
