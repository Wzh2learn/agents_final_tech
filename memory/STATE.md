# memory/STATE.md
更新: 2026-08-16（模型升级专项 P0-P2 收口）

## 模式
守护模式 + **模型升级路线待拍板**。docs/23 已发送甲方（08-12）；导师包已发送（08-16，用户亲发）。等: ① 用户拍板模型切换路线 A/B ② 甲方首轮反馈 ③ 导师反馈。B4 观察窗: 双维度已达标（≥100 ask 于 08-16 达 513; ≥3 天自 08-12 起算），统计结论随甲方反馈行动。缓至甲方首轮反馈: 任务二 B 一期 / 场景 B / _cleanup_backup 删除 / Qoder PAT。

## Git
- HEAD: 9502da6 → +本次收口 commit（模型升级 P0-P2 资产入库; 实际 hash 见 dispatch_log 收口行）
- 三方对齐: GB10 commit+push → GitHub → 本机 fetch+merge
- 冻结工件未动: 甲方版 docx bc3785cb / 导师版 docx 929a8c65（六次冻结）/ 冻结节点三件

## 本轮战绩（模型升级专项 P0-P2）
- P0: 旧栈 :8004/:8005 完整 cmdline 录入（回滚依据）; 下载通道核实（HF 直连不通, hf-mirror/ModelScope 通, dockerproxy.net 镜像通）
- P1: Qwen3.8-27B-FP8（29GB）+ vllm-gb10:v0.27.1 镜像落盘; 探针 :8006 READY（GMEM=0.30, page cache 回收 SOP 定型）; 思考控制 4/4 PASS（off=零推理 / budget 被忽略 / effort low·medium·xhigh 单调 / high→400）
- P2 基准（全实测）: 三档矩阵 A_off p50=10.31s·p95=15.76s / B_low 23.82s / C_xhigh 60.60s; 确定性 16/16 零回归（旧栈对照 16/16, 1.3-1.9s/题）; 并发 3 流 makespan 2.9x 压缩但单请求劣化 7x（带宽受限坐实）; judge 交叉评 5.0×4（基线 4.94）; 视觉转写质量平手但候选 72-76s vs 旧栈 mmproj 29-31s
- **闸门: 质量 GO + 快路 FAIL（A_off p50 10.31s > 8s）→ 不全量替换**; 菜单 = 路线 A 双模型分工（推荐先行: A3B 留快路+视觉, 27B 接 agent 验证链/judge/深度问答）vs 路线 B Qwen3.8-35B-A3B MoE 探针, 见 docs/32 §2.4
- 新资产: scripts/m2_model_probe_benchmark.py / vllm_probe_serve.sh / m2_model_probe_p2_run.sh / gb10_reclaim_page_cache.sh + docs/32 + DECISIONS 模型卡; m2_eval_judge.py 健康检查补 /health 回退

## 服务
- :5050 UP（route=on, provider=local, embeddings=137, tmux coding-jinrong）
- :8004/:8005 UP（旧栈零改动, GGUF 保留 48h → 至 08-17 18:00）; :8100/:15432 UP; :8007 down
- **:8006 vLLM 探针 UP（tmux vllserve, 待拍板, 不接生产流量）**
- Loop B: 18:16 qa_canary 一次超时 FAIL = P2 视觉对照占用 :8004 的负载扰动（非代码回归）, 观察后续周期翻转; tmux 禁杀清单 + vllserve

## 质量基线
- pytest: 收口跑（GB10, 结果记 dispatch_log）; docs_lint 0/0（08-16）; sync_skills --check 21/21; 冻结节点 PASS
- eval 基线不变: 确定性 16/16 / judge 4.94（探针交叉评 5.0）; NF 候选侧重跑留 P3
- B4: asks≥513; agent 路 warm best 13.5s; 回滚 10-23s 实测

## 下一步（等用户/甲方/导师）
1. **用户拍板模型路线: A 双模型分工（推荐, 落地不动 :5050 代码）/ B MoE 探针 / 并行** → 批后走 P3
2. 甲方首轮反馈 → 解锁缓办清单 + A2 延迟修复优先级
3. 导师反馈 → docs/31/视频微调或科研线推进（NLPCC/CCIR 截稿日仍 pending 人工查）
4. 菜单待拍板（存量）: Docling NCAMC / OpenAI4S 接入科研线 / docs/28 #2→#1→#4（:8005 judge 分流项将被路线 A M3 覆盖, 拍板时合并）
5. 累计净值建议 + 产品份额①建议 apply 候选等窗口（走 SOP）
