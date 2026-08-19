# DSpark Track 1 任务卡 v2: Route V 探针测量 (:8006 停机窗口内)

## 角色与背景
你是 Loop A 执行层。主线程已完成: drafter 下载校验 + 探针容器 vllm-dspark-v 启动 (:8007, 全规格)。
当前状态: 用户批准临时停 :8006 腾内存 (生产栈双 27B 并行不成立), 你在此窗口内完成全部 :8007 侧测量。
等价性对照 (:8006 侧) 由主线程在恢复后补跑 —— 你只负责收 golden 样本。
先读 docs/experiments/2026-08-19_dspark_drafter_ledger.md 与 docs/architecture/gb10_vllm_startup_sop.md 背景节。

## 红线
- 不碰 :8004/:5050/kiosk/Loop B/冻结节点; 不停不重启任何容器 (包括 vllm-dspark-v 自己, 收尾由主线程做)
- :8006 已停, 无需也不要尝试访问它
- 不 git add -A; 只 add 你新增的文件
- 无法判断 → 记 logs/graph/blocked_questions.md 跳过, 不恋战

## Step 0: 预检 (~5min)
1. cd ~/wzh/projects/agents_final_tech && git pull --ff-only
2. docker ps 应见 vllm-dspark-v; curl -s 127.0.0.1:8007/health 应 200 (若容器未 READY, 轮询 /tmp/dspark_v_serve.log 等 "Application startup complete", 最多再等 5min; 仍不成 → 记 blocked 停)
3. GET /v1/models 应含 qwen38-27b-fp8; 记 docker logs 中 gpu_blocks/KV cache size 行入报告

## Step 1: 投机解码激活验证 (~10min, 生死线)
- 短问 1 条 (默认模板 thinking off) → 200 + 非空, 记延迟
- curl -s 127.0.0.1:8007/metrics | grep -i spec_decode 取计数器; 再跑 3 条短问确认增长
- docker logs vllm-dspark-v 2>&1 | grep -ai speculative 留证据
- 无激活证据 → NO-GO 报告停

## Step 2: Golden 样本采集 (~20min, 等价性验证用, 两阶段设计)
全部 temperature=0, 请求与响应完整落 logs/graph/eval/dspark_route_v_golden.json (数组, 每条: name/request/response_text/reasoning/tool_calls/latency_ms):
a) lossless 组: 固定 2 prompt (1 中文金融: "嘉合基金对账单中期末持仓市值合计是多少? 请给出数字和出处表名"; 1 英文通用: "Explain in two sentences what a custodian bank does.")
b) thinking 组: 同 1 prompt 分别带 reasoning_effort=xhigh 与不带 (默认 off), 各 1 条; 再带 reasoning_effort=high 1 条 (预期 400, 记录)
c) 工具组: get_weather 工具定义 + "北京今天天气怎么样" 触发, 记 tool_calls 结构
d) 记录 chat template 行为注记 (默认 thinking off 模板下 reasoning 字段应为空)

## Step 3: 延迟矩阵 + 接受率 (~40min)
- ./venv/bin/python scripts/run_matrix_candidate.py --endpoint http://127.0.0.1:8007/v1/chat/completions --model qwen38-27b-fp8 --label dsaprk_route_v_think_off --thinking off
- 再跑 --thinking xhigh --label dsaprk_route_v_think_xhigh
- :8006 基线: ls logs/graph/eval/matrix/ 找既有 27B 基线工件; 有 → 引用(注明文件); 无 → 报告中注明"基线待主线程恢复 :8006 后补跑", 不阻塞
- 每题延迟 + p50/均值 + 确定性通过数 (16 题)
- 并发 3 流: 5 条固定短问 ×3 并发, 记墙钟 + 最长单条
- 接受率: 每档前后取 /metrics spec_decode 计数器, acceptance = accepted/drafts (写明口径), 按档记录; 快照写 logs/graph/eval/dspark_route_v_specstats.json

## Step 4: Track 3 门禁 run_eval 全套 (~30min)
- bash scripts/run_eval.sh 的调用方式以脚本实际参数为准 (先 head -60 scripts/run_eval.sh), 端点指向 :8007
- 判定: 确定性 16/16 + NF 0/9 + judge 四维 ≥ 基线 (16/16/0/4.94-5.0); 任一漂移 → NO-GO 如实记录
- judge 端点默认 :8004 (在跑), 不动配置

## Step 5: 报告 (~15min)
docs/experiments/2026-08-19_dspark_route_v_probe.md:
- 启动参数 + 内存算术 (CUDA free 33.92/121.63 预检失败 → :8006 停机窗口 → 全规格启动, 含 free/gpu_blocks 证据)
- 投机激活证据 + 冒烟
- golden 样本清单 (对照结论留白, 主线程补)
- 延迟矩阵表 (16 题 × off/xhigh + 并发)
- 接受率表 (按档) + Track 3 门禁结果
- 结论: GO / NO-GO / 条件 GO (数据说话, 不利数据也写)
台账 docs/experiments/2026-08-19_dspark_drafter_ledger.md "实测接受率" 表追加一行

## Step 6: 收尾
- 不停容器 (主线程统一处理停机序); 确认 :8004/:5050 未受影响 (各 1 个只读请求)
- git add 仅新文件; commit "probe(dspark): Route V :8007 测量 — <一句话结论>"; git push (失败记"待代推")
- 最终汇报: 激活 PASS/FAIL + golden 条数 + 矩阵 p50×2 档 + 接受率区间 + Track3 判定 + commit hash

## 环境须知
- apply_patch 不存在, heredoc 写文件; 首次写后 head -5 验证
- 大日志用 tail/grep 分块; bwrap 已旁路, namespace 错误记录后继续 (重试≤2)
- 长命令 nohup + 日志 + 轮询, 不阻塞会话