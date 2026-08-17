# 声明-实况对账审计报告（2026-08-18 凌晨, T2）

主题: 所有"声称的状态"与运行实况逐条对账。起因: 08-17 P0 事故（汇报说全绿时
Loop B 红了 22h、旧 daemon 跑旧脚本、guard 被误诊）。本报告为"声明必须带证据"
治理规则的实例存档。

## 1. 长跑进程普查（mtime vs 启动时间, 倒挂=进程跑旧代码）
| 进程 | 启动 | 对应代码 mtime | 判定 |
|------|------|----------------|------|
| :5050 uvicorn (pid 1554230) | 08-18 00:21 | src 最新 opencode_adapter.py 08-17 00:14 | OK |
| opencode serve (1483419) | 08-17 22:49:11 | opencode.json 22:49:00 | OK（11s 余量, 记为紧边界） |
| vLLM docker (1497196) | 08-17 23:04:31 | vllm_probe_serve.sh 23:03:55 | OK（cmdline 含 qwen3_xml+APC 坐实） |
| thinking-proxy (1510547) | 08-17 23:20:06 | thinking_inject_proxy.py 22:25:13 | OK |
| Loop B daemon (1498339) | 08-17 23:05:01 | loop_b_verify.sh 08-17 00:31 | OK |
| :8100 responses2chat_proxy (1679515) | 08-08 00:35 | 同名 py 08-08 00:23 | OK |
| :8004 llama-server (2642808) | 07-29 23:11 | GGUF 权重静态 | OK |
| MCP 三件套 (1483806-810) | sidecar 子进程 22:49 | mcp_server*.py 无更晚改动 | OK |
**倒挂: 0**。治理规则实例化: 此普查脚本化候选（status.sh 增 mtime 对比列）记菜单, 演示后做。

## 2. 关键声明 vs 实测
| 声明 | 实测 | 判定 |
|------|------|------|
| 三方 HEAD 16d1246 | status.sh GB10=GitHub 对齐 | OK |
| 端口 5050/4096/8004/8100/15432 UP, 8005 down | status.sh 快照一致 | OK |
| :8004 模型 Qwen3.6-35B-A3B / :8006 qwen38-27b-fp8 | /v1/models 双 ID 坐实 | OK |
| :5050 env route=on timeout=45 | /proc environ 坐实（T1 终态复验） | OK |
| 冻结节点 5 件 hash | status.sh frozen_hashes PASS | OK |
| eval v2: 16/16 / NF 0/9 / judge 5.0×4 | eval_summary.md 08-16 23:23 一致 | OK + **新鲜度注**: 基线早于 P0 修复（qwen3_xml/APC）, 演示后重跑刷新口径 |
| B4 累计 | status.sh asks=1111 (agent=101 含 A3B 时代) vs STATE 快照 1092@23:30 | OK（快照时点一致） |
| docs/23 冻结 hash bc3785cb | 未重生成（冻结窗） | OK |

## 3. 近三日汇报抽查
1. **08-17 夜间 loop 汇报**: T5"完整周期无误报 PASS"措辞已于 P0 收口更正（实为新脚本前台结果, daemon 未重载）→ 已闭环。
2. **P0 专项汇报**: 4 条 agent 完成（23:15/23:20/23:38/23:39）B4 坐实; APC 78% 命中率复算 89376/114842=77.8% 坐实; **演练 6/8 口径决议**: b4 日志 23:16-23:20 窗实落 8 条 fallback（17:03×2/17:50×2/18:37/19:08/19:23/19:55）= 发 8 落 8, 台账"8 条"准确; "6" 为过程中 tail -7 截断假象, 非台账错误。
3. **T1 彩排汇报**: C1 51.3s 回落如实记; A3 1.1s 为页面恢复上次解析态（非 OCR 实耗）, 首传预期 16-71s 已在脚本注明。

## 4. 新发现（记账, 演示后处置）
- m1harness tmux pane 承载进程已死（残 shutdown 警告）; MCP 三件套实为 sidecar 子进程活着 → pane 演示后可吸收关闭。
- zhikuncode 容器 running 2 weeks（Q1 休眠资产已记）— 仅记。
- 拒答答案仍带"3 条来源"toggle（直连路拒答含检索候选）— 演示口头带过, 演示后评修。
- eval 基线新鲜度（§2 注）— 演示后 run_eval.sh 重跑。
- status.sh 增 mtime 倒挂对比列 — 菜单。

## 5. 治理规则
"声明必须带证据": 任何汇报数字须附工件/日志出处; 进程类声明须附 mtime-vs-starttime
或 environ 证据; 本次无证据声明 = 0 漂移（除已注新鲜度项）。
