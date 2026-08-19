# DSpark Track 1 任务卡: Route V 探针 (vLLM 原生 dsaprk, 不换栈/不重量化)

## 角色与背景
你是 Loop A 执行层。本任务是 DSpark 加速专项 Track 1 主探针: 用 vLLM 原生投机解码 (--speculative-config method=dspark) 挂载 DSpark drafter, 目标模型沿用现有 Qwen3.8-27B-FP8 权重 (与 :8006 同源, 只读挂载, 不是换栈), 实测等价性 + 延迟 + 接受率。一切结论证据说话, 数据如实记录 (包括不利数据)。背景知识在 docs/experiments/2026-08-19_dspark_drafter_ledger.md (先读)。

## 红线 (开工前必读)
- 零触碰: :8006/:8004/:5050 容器与配置、opencode.json、kiosk、Loop B、冻结节点 (tests/baselines/、tests/fixtures/m2_eval_questions.json、~/wzh/m1_samples/、scripts/graph/frozen_hashes.txt)
- 对 :8006 只允许只读推理请求 (跑基线用); 禁止 docker/配置改动
- 不重启任何现有服务; 只创建/销毁你自己起的探针容器 vllm-dspark-v
- 不跑 run_eval.sh 全套 (Track 3 的事); 不跑 pytest
- 不 git add -A; 只 add 你新增的文件
- 连续 2 次启动失败或遇无法判断的问题: 写报告 + 记 logs/graph/blocked_questions.md + 停, 不恋战

## Step 0: 预检 (~5min)
1. cd ~/wzh/projects/agents_final_tech && git pull --ff-only (拉取 vllm_probe_serve.sh 的 DRAFTER_DIR 扩展与本任务卡; 若 pull 因 config/schema_suggestions.json 脏被拒, 该文件已白名单豁免, git stash push config/schema_suggestions.json 后 pull 再 stash pop)
2. ss -ltn | grep 8007 应为空 (探针端口空闲); docker ps 应见 vllm-probe (:8006) 在跑, 记录其 STATUS 供收尾比对
3. drafter 权重校验 (主线程已在下载到 ~/wzh/models/hf/Qwen3.8-27B-DSpark-vLLM):
   - 若 tmux 会话 dsaprk-dl 还在跑 → 等它结束 (tmux capture-pane 看进度), 不要重复下载
   - sha256sum model.safetensors 必须 = 9d26d5e637551c244d543c67c790bd0947f360e005c569e5851a185ffe692786
   - grep -q Qwen3DSparkModel config.json (一行架构改动必须在)
   - 文件清单 6 件: .gitattributes README.md config.json dflash.py dspark.py model.safetensors
   - 若缺失/校验不过, 用锁定 revision 补下:
     BASE=https://hf-mirror.com/Doopeworld/Qwen3.8-27B-DSpark-vLLM/resolve/ebaa0919226a29408fa2c8f3efc493e98189c7ed
     for f in .gitattributes README.md config.json dflash.py dspark.py model.safetensors; do curl -fL --retry 3 -o "$f" "$BASE/$f"; done
     下完复验 sha256; 仍不过 → 停, 记 blocked

## Step 0.5: 启动前内存回收 (SOP 必做, ~2min)
    cd ~/wzh/projects/agents_final_tech
    bash scripts/gb10_reclaim_page_cache.sh 35
- SOP (docs/architecture/gb10_vllm_startup_sop.md) §0 第一步: 统一内存 page cache 不被 CUDA 计为可用, 不回收必撞 FM1
- free -g available 应升至 35GB+ (08-16 实测 15.6→38); 记录前后值入报告
- 回收对生产栈实测无感; 若期间 :5050/:8004 出现异常 → 立即停止并汇报
## Step 1: 起探针容器 (~7-15min, 冷启动约 7min)
    cd ~/wzh/projects/agents_final_tech
    CONTAINER_NAME=vllm-dspark-v PORT=8007 \
    DRAFTER_DIR=$HOME/wzh/models/hf/Qwen3.8-27B-DSpark-vLLM \
    CHAT_TEMPLATE=$HOME/wzh/vllm_cache/qwen38_think_off_default.jinja \
    nohup bash scripts/vllm_probe_serve.sh > /tmp/dspark_v_serve.log 2>&1 &
- tail /tmp/dspark_v_serve.log 等 "Application startup complete" (超时 20min, 记实际耗时)
- GMEM=0.30 固定 (SOP 红线: 只许调低不许调高)。drafter 多占 ~2.7GB 会挤 KV 预算, 若启动报 KV 预算负/不足 → 加 MAXLEN=16384 重试 (GMEM 不动, KV 需求减半); 仍失败 → 记 blocked 停, 不擅抬 GMEM (生产栈在跑)
- 仍失败: tail -100 启动日志入报告, 停, 记 blocked

## Step 2: 冒烟 + 投机解码激活验证 (~10min)
- GET 127.0.0.1:8007/v1/models → 应含 qwen38-27b-fp8
- 短问 1 条 (默认模板 thinking off) → 200 + 非空回答, 记延迟
- 投机激活证据 (项目生死线): curl -s 127.0.0.1:8007/metrics | grep -i spec_decode 取计数器 (num_drafts / num_emitted / num_accepted_tokens 类), 或 docker logs vllm-dspark-v | grep -i speculative; 再跑 3 条短问确认计数器增长。无计数器或不增长 → 查启动日志 speculative config 解析段, 修到激活为止; 实在无法激活 → NO-GO 写报告停
- 记录首个 spec stats 快照 (基准点)

## Step 3: 等价性验证 (对照 :8006, ~20min)
所有请求同 body (仅端点不同), 除注明外 temperature=0:
a) 无损性: 固定 2 条 prompt (1 中文金融问答 + 1 英文通用), 两端输出必须逐字一致 (投机解码理论无损, 目标模型相同)。不一致 → 先核对采样/模板参数一致性再重跑; 仍不一致 → P0 记录, 结论 NO-GO
b) thinking 档位: reasoning_effort=xhigh 时两端 reasoning 均非空; 默认 (模板 thinking off) 两端 reasoning 均空。唯一有效旋钮是 reasoning_effort low/medium/xhigh ("high" 非法应两端同样 400 —— 验证行为一致)
c) 工具调用: 传 get_weather 简单工具定义 + 触发问, 两端 qwen3_xml 解析出 tool_calls (name + arguments 可 JSON 解析)
d) 逐项记 PASS/FAIL + 证据片段 (请求 body + 响应前 200 字符) 入报告

## Step 4: 延迟矩阵 + 接受率 (~30-40min)
- 用 scripts/run_matrix_candidate.py (GB10 venv: ./venv/bin/python):
  ./venv/bin/python scripts/run_matrix_candidate.py --endpoint http://127.0.0.1:8007/v1/chat/completions --model qwen38-27b-fp8 --label dsaprk_route_v_think_off --thinking off
  再跑 --thinking xhigh --label dsaprk_route_v_think_xhigh
  :8006 基线: 若 logs/graph/eval/matrix/ 已有 08-19 :8006 工件直接引用 (注明文件); 否则补跑 --endpoint http://127.0.0.1:8006/v1/chat/completions --label baseline_8006_think_off / _xhigh
- 记每题延迟 + p50/均值 + 确定性通过数 (16 题)
- 并发 3 流: 5 条固定短问 × 3 并发 (python threads 或 curl 后台), 记墙钟 + 最长单条, 两端各一次
- 接受率: 每档前后取 :8007/metrics spec_decode 计数器, acceptance = accepted/drafts (或 emitted-1 口径, 写明算法), 按档记录 (预期: 结构化/工具题高、自由文本低; README 参考区间 2.18-4.79)
- 接受率快照写 logs/graph/eval/dspark_route_v_specstats.json

## Step 5: 报告 + 台账 (~15min)
- docs/experiments/2026-08-19_dspark_route_v_probe.md: 启动参数 (GMEM 实际值/容器/挂载) + 启动耗时 + 冒烟证据 + 等价性表 (a-d PASS/FAIL) + 延迟矩阵表 (off/xhigh × :8006/:8007 + 并发) + 接受率表 (按档) + 结论 (GO / NO-GO / 条件 GO + 一句话理由)
- docs/experiments/2026-08-19_dspark_drafter_ledger.md "实测接受率" 表追加一行实测
- 不改其他既有文件

## Step 6: 收尾 (~5min)
- docker stop vllm-dspark-v (--rm 自清), ss -ltn 确认 :8007 释放, docker ps 确认 vllm-probe STATUS 与 Step 0 记录一致 (未受影响)
- git add 仅新文件; commit "probe(dspark): Route V :8007 — <一句话结论>"; git push (失败记 "push 待主线程代推", 不纠缠)
- 最终汇报: 启动耗时 + GMEM 实际值 + 等价性 4 项结果 + 延迟关键数 (off/xhigh p50 × 两端) + 接受率区间 + 结论 + commit hash

## 环境须知 (必读)
- apply_patch 工具不存在: 写文件一律 cat > path <<'EOF' heredoc; 首次写文件后 head -5 验证落盘
- 读大文件分块 (tail -n 100 / sed -n); 禁止 cat 整个日志
- bwrap 沙箱已旁路 (--dangerously-bypass-approvals-and-sandbox), 若仍报 namespace 错误记录后继续, 重试不超过 2 次
- 长命令 (模型加载/跑分) 用 nohup + 日志文件 + 轮询, 不阻塞会话