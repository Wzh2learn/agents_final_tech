# 元认知快照 · 2026-08-22 夜间（声明-实况对账审计）

背景: 08-22 白天教训（汇报"全绿"时 Loop B 已红 22h / 旧 daemon 跑旧脚本 / 侧车误诊）的第二次偿还。
范围: 项目声称状态与运行实况逐条对账; 只读 + 台账, 唯一代码动作 = T2 侧车启动器入库。
采集时点: 2026-08-22 22:19-22:35（GB10 本地时间）。

## 一、七项对账

### ① 端口与模型拓扑 —— 全部坐实
| 声称 | 实测 | 证据 |
|---|---|---|
| :5050 137/local 健康 | ✓ healthy, embeddings=137, provider=local | curl /api/health/full |
| :8004 A3B（M1 热路径锁定） | ✓ Qwen3.6-35B-A3B-Q4_K_M.gguf + mmproj, PID 2642808（07-29 起, LM Studio 后端） | /v1/models + ps |
| :8006 27B 非 DSpark 生产 | ✓ qwen38-27b-fp8, maxlen 32768, 容器 vllm-probe Up 23h（= 08-21 23:1x 回滚窗重起, vllm-gb10:v0.27.1-gb10.1） | /v1/models + docker ps |
| :8008 UP | ✓ qwen38-27b-fp8 | /v1/models |
| :8007 空闲 | ✓ 无响应 | curl 超时 |
| :8005 DOWN 断言 | ✓ 无响应（退位断言成立） | curl 超时 |
| 侧车 :4096 | ✓ HTTP 200, PID 1189803（14:37:35 起）, cmdline = opencode serve --port 4096 与启动器一致 | /proc/1189803/cmdline |
| :15432 PG | ✓ pgvector_15432 Up 5 weeks | docker ps |

### ② :5050 进程 env（拍板 c 执行证据）—— 坐实
三个进程（父 2104416 / worker 2104425 / 2104426）的 /proc/*/environ 均为
`OPENCODE_ASK_TIMEOUT=45` + `M2_OPENCODE_ROUTE=on`。"声称没动"经逐进程核验成立。

### ③ B4 修复后段（起点行 3429, 14:38:33）—— 冒烟通过
```
./venv/bin/python scripts/graph/b4_checkpoint.py 3429
- agent 尝试总数 (attempted): 57
- agent 完成数 (无回落): 11          → 完成率 19.3%
- 回落率: 80.7% (= 1 - 完成/尝试)
  - 超时回落 (latency>=45000ms): 46
- segment: line 3430..3486 (n=57); 最终路径 direct=46(全回落)/agent=11
- latency p50=48061ms p95=60471ms
```
与用户抽验口径（15:11 时 58 尝试/11 完成=19.0%）一致（差 1 为口径内尝试计数微差, 完成数吻合）。
**注意**: 该段流量 = 纯 Loop B 金丝雀（见漂移 D1）, 非 kiosk 演示流量。

### ④ Loop B 翻绿兑现链 —— 坐实
- 15:11:59 B4 完成行出现 → 15:14 周期 overall FAIL→PASS（#LOOP-B-FLIP, 已入 a7eb724）
- 21:53:43 周期复验 PASS（dirty_files=1 whitelisted=0, schema_suggestions 运行时豁免生效）
- 防旧脚本复发核验: daemon PID 3065474 启动 08-19 20:01:51, loop_b_verify.sh mtime 08-19 20:01:39 —— **无倒挂**（更新后 12s 重启）

### ⑤ 冻结资产盘点 —— 存在与 hash 核验
- 专利三件: F8A4B0…（md）/ 48FF2A…（docx v2）/ 7E39CF…（邮件草稿）与冻结台账逐字一致
- 甲方冻结件: docs/23_甲方阶段汇报_发送版.docx, md5 bc3785cb…（本次复验见收口记录）
- tests/baselines/scenario1_baseline.json 在位（门禁级冻结资产）
- 只核存在与 hash, 未碰内容

### ⑥ 已知问题台账 —— 交叉引用确认
- FK 竞争（超时删 session vs 在途运行）: 08-11 起, adapter 修复候选不阻塞（#SIDECAR-VERDICT / THREADS）
- 预热 2 overflow: 26963 tok 逼近 32768 上限 → 交叉引用为 L2 context 瘦身（27k→8-10k）的现成动机

### ⑦ 明晚 L1 窗口前置 —— 开窗即跑确认
- runbook = docs/experiments/2026-08-22_l1_matrix_runbook.md（sha 0e0d7d5b… 两端一致, 22:14 已修 L109 措辞）
- P6 已实证（腿直连 :8006, 侧车非硬前置）/ P7 窗口内填写; 还原清单 6 项完整（含窗口起点侧车状态行）
- 侧车健康（本快照①）+ :5050 env 未动（②）= 矩阵基线干净

## 二、漂移清单

| # | 漂移 | 证据 | 处置 |
|---|---|---|---|
| D1 | **kiosk 进程已停 2 天, 台账/汇报持续声称"播放中"** | B4 分小时: 08-20 22:00 起衰减（25→15 行/时）, 末行 08-20 23:55:19; 08-21/22 全天 ~8 行/时 = 纯 Loop B 金丝雀; ps 无 kiosk 进程; 仓库内无 kiosk runner 脚本（仅 08-21 方案文档） | 记台账 + 报用户; **归因定论（08-22 用户抽验更正）**: 停点 = B4 行 3092 = DSpark 窗口 v2 切换点, 正对"窗前暂停 kiosk"动作点, v1/v2 连败混乱中复活步骤漏掉 = "窗前暂停未复活"（原"疑楔死致死"作废: 楔死起点 22:46 后 kiosk 仍写 B4 至 23:55, 不相容）; 用户拍板不动不重建; 连带更正 #DSPARK-ROLLBACK(08-21 23:54)"已恢复"声称(见 dispatch 加注) |
| D2 | **:5050 运行 08-18 代码, 08-21 修复（fb94824, M1_B4_LOG_PATH）未生效** | uvicorn lstart 08-18 16:44:49; git log 显示 src/web/routers/m2.py 于 08-21 修改 | 记台账; 生效需 :5050 重启窗口, 不擅动; 下次重启窗顺带激活 |
| D3 | STATE/THREADS "kiosk 播放中"措辞 | 本快照 D1 | 本次收口更正 |
| D4 | python-sandbox 容器 Exited 5 个月残留 | docker ps -a | 记台账, 低优先, 不擅删 |
| D5 | （已修, 复验）#LOOP-B-FLIP 未提交 / runbook L109 陈旧 / _inbound_ 残留 | a7eb724 已带走; _inbound_ 实测不存在; git status 干净 | CLOSED |

## 三、T1 长跑进程普查表（倒挂检查）

| 进程 | 启动 | 载体 | 倒挂检查 |
|---|---|---|---|
| :5050 uvicorn（2104416+2 worker） | 08-18 16:44 | venv | **有**: src 代码 08-21 有改动（见 D2） |
| opencode 侧车（1189803） | 08-22 14:37 | ~/.opencode/bin + ~/.sidecar_env.bin | 无（今日新起, 与启动器一致） |
| mcp_server/vision/tabular（119001x） | 08-22 14:37 | 仓库 venv | 无（随侧车同起, 仓库代码最新） |
| :8004 llama-server（2642808） | 07-29 23:11 | LM Studio 后端 + 本地 GGUF | 无（二进制/权重未动） |
| Loop B daemon（3065474） | 08-19 20:01:51 | scripts/graph/loop_b_verify.sh | 无（脚本 20:01:39 更新, 12s 后重启） |
| vllm-probe 容器（:8006/:8008） | Up 23h | vllm-gb10:v0.27.1-gb10.1 | 无（08-21 回滚窗按 SOP 重起） |
| zhikuncode 容器 | Up 2 weeks | zhikuncode:latest | 不参与生产链路 |
| tmux 会话 | coding-jinrong(3 窗)/graph-loop-b/opencode-serve/thinking-proxy/vllserve | — | opencode-serve 窗内为已终止的旧启动器残影, 现侧车为脱离 tmux 的独立进程（启动器入库后可放回窗内运行） |
| crontab | 空 | — | 24h cron 已删, 无残留 |

## 四、48h 观察口径注记（影响判定）

- 观察窗: 08-22 14:37 → 08-24 晚; 段起点行 3429; 判定阈值: 完成率 <10% 或甲方要求 → 抬超时再议
- **样本构成 = 纯 Loop B 金丝雀**（~8 行/时, 含 OCR meta-query + 拒答题）, kiosk 流量缺位（D1）
- 当前完成率 19.3%（11/57）> 10% 阈值, 且与楔死前基线吻合; 若 kiosk 不恢复, 观察结论仅代表金丝雀题型

## 五、结论

声称-实况对账 7 项: ①②③④⑤⑥⑦ 全部坐实; 新发现漂移 4 项（D1-D4）, 其中 D1（kiosk 停摆 2 天无人发现）
是本日"声明必须带证据"教训的又一实例——台账声称的运行状态必须有进程级证据支撑。
今晚产出已使明晚 L1 窗口开窗即跑（⑦）。
