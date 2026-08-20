# B4 切换点 checkpoint（ interim + 24h 布防）— DSpark 生产观察期

状态: 活跃 | 更新: 2026-08-21 00:40 | 类型: N1 固定动作（DSpark 切换点 08-20 23:48 / B4 行 3092）
工件: scripts/graph/b4_checkpoint.py（本次沉淀）; logs/graph/b4_checkpoint_20260821_0032.md（GB10）; cron 一次性任务 23:50

## 1 interim 段统计（切换点 3092 起, 00:00-00:33）

- 段内 n=12，其中 **5 条疑似测试/缓存流量**（latency <100ms：行 3093/3097/3098/3099/3100）
- 真实流量 n=7：全部为 agent 路尝试 **45-50s 超时回落**（p50 45.7s / p95 49.9s），直连快路 0 条真实请求
- status 全部 ok（未见 empty/error 状态）；content=null 暂无结构化信号，24h checkpoint 结合 sidecar 日志查

## 2 发现与处置：pytest 流量污染生产 B4 日志（已修，无需重启）

**证据**：00:04:08 同秒 4 条 0ms 记录（含 1 条 route=agent/fell_back=false）；app.log 同时刻出现 `GET http://testserver/api/metrics`（httpx TestClient 特征）与 `opencode sidecar unhealthy ... fallback` 日志；pytest_latest.txt 00:25 有子集运行（Loop B 周期）。
**影响**：切换点后的"1 次 agent 完成"（行 3098）**重分类为测试流量**——切换点后真实 agent 完成数维持 **0**。
**修复**（生产进程行为不变，无需重启 :5050）：
- src/web/routers/m2.py：`_B4_LOG` 支持 `M1_B4_LOG_PATH` env 覆盖（生产无此 env，默认路径不变）
- tests/conftest.py：模块顶部 setdefault 指向 /tmp/b4_ask_log_tests.jsonl
- 验证：tests/test_m2_multiturn.py 20 passed 前后生产日志行数 3104 不变，scratch 收到 3 行测试流量
**边界**：打活 :5050 的 e2e 测试/eval 流量仍入 B4——这是用户既定口径（"eval 套件每天经 :5050 生产端点跑一遍积累真实样本"），不属污染；checkpoint 脚本以 <100ms 启发式 + 行号清单双口径标记可疑行。

## 3 生产接受率续测（/metrics spec_decode 计数器）

- drafts=856 / accepted=1141 → **接受率 1.33 tokens/draft**（切换窗实测 1.26，探针固定题库 3.31）
- 投机解码在生产持续激活；接受率随真实负载（长思考 xhigh 为主）略升但仍远低于探针短答负载——探针高估生产收益的结论维持

## 4 eval route=agent 标签异常审计（B4 为准）

eval 中间行曾出现 route=agent 35850/38677ms 标签，与 B4 全 fell_back 矛盾。以 B4 为权威口径：该标签来自 eval runner 对响应对侧元数据的推断（有 duration_ms ≠ 未回落），非真实 agent 完成。处置：差异记账，eval 代码观察期内不动；24h checkpoint 若再现以 B4 行号逐条对质。

## 5 判定与 24h 布防

- interim 样本过小，不作回滚判定；如实观察项：**DSpark 接受率 1.33 尚未把 agent 路压进 45s 超时内**（真实流量 7/7 超时回落），与"探针 3.31 高估"一致，收益兑现需要接受率或超时预算再评估——列入明日分布分析，不在观察期动配置
- 24h checkpoint：cron 一次性任务 08-21 23:50 跑 `scripts/graph/b4_checkpoint.py 3092`（报告落 logs/graph/b4_checkpoint_*.md + cron 输出）；判定按批复 ③：回落率 >60% 第一怀疑 content=null，查无解释报用户拍板，不恋战
- 24h 后需人工删除 cron 条目（条目自带注释标记）