# 小模型矩阵 C1/C2 首批结果（批复 ② 执行, 错峰 :8007 探针）

> 状态: 活跃 | 更新: 2026-08-19 凌晨 | 类型: K4 设计（0250624）首批执行数据
> 口径: 固定题库 = K2 尺子（m2_eval_questions.json v3, 16 题冻结只读）; 检索 = 生产同口径
> （RAGService.smart_retrieve top_k=5 无 rerank）; 判分 = m2_eval_deterministic 同函数;
> 候选回答者经 scripts/run_matrix_candidate.py（本轮新增资产）打 /v1/chat/completions
> 基线: 生产快路 Qwen3.6-35B-A3B @:8004（thinking off, FORMAT_HINT）= 16/16

## 1 结果总表（GB10, 08-19 02:00-03:00 凌晨错峰, kiosk 暂停窗内测量）

| 候选 | 思考档 | Score | 总耗时 | 失败题 | 判定 |
|---|---|---|---|---|---|
| A3B :8004（基线） | off | **16/16** | ~2s/题 | — | 快路守擂成功 |
| C1 Qwen3-14B Q4 | off | 11/16 | 48.5s | q01/q05/q08/q11(富熙系)+q03(伯仕基金名), 均亚秒拒答 | NO-GO |
| C1 Qwen3-14B Q4 | xhigh | 14/16 | 6m23s | q08(富熙客户名) + adv_ocr_meta | NO-GO |
| C2 Qwen3-8B Q4 | off | 14/16 | 1m28s | q07(伯仕基金代码) + adv_multiturn | NO-GO |
| C2 Qwen3-8B Q4 | xhigh | **15/16** | 3m44s | q08(富熙客户名) | NO-GO（最优挑战者） |

逐个 go/no-go（批复 ② 口径）: C1 NO-GO, C2 NO-GO——替换生产快路/准路均需 16/16 零回归, 无候选达标。

## 2 洞察（论文 章 3 路由实验数据 + 业务选型）

1. **思考档位效应实锤**: 14B off→xhigh = 11→14（+3 题）; 8B = 14→15（+1 题）。档位是真实质量旋钮, 但**不能逆转候选与基线的排序**——A3B 快路 16/16 不是偶然, 是针对性调优（FORMAT_HINT/契约 prompt）的结果。
2. **8B > 14B 异常（如实记录, 未定论）**: 8B 两档均胜 14B。候选解释: 14B GGUF 为 7 月旧 snapshot（权重文件 07-10）、8B 量化批次更新; 或 14B thinking-off 模板行为异常（亚秒拒答模式集中在富熙 txt 样本, 疑上下文利用失败而非检索失败——source_required 全过证明检索到位）。**跟进项**: 换 14B 新权重或 llama-server 参数复测一次再定论, 本轮不恋战。
3. **共性难题 q08_fuxi_customer_name（掩码客户名）**: 14B-xhigh 与 8B-xhigh 均失败——小模型深度思考也解不出掩码姓名抽取, 该题入"路由难题集"（未来记忆感知路由实验的 hard 分层素材）。
4. **成本轴**: 8B xhigh 3m44s/16 题 ≈ 14s/题, 仍 >> A3B 快路 ~2s/题; 小模型不威胁快路, 但 8B 以 1/4 体量拿到 15/16——**潜在廉价 verifier/复核位**（准路 27B 的降级备选, 演示回滚场景的兜底候选）, 入 docs/32 再思考菜单。
5. **测量纪律**: kiosk 暂停窗（01:55-02:32）内 judge A/B 与矩阵不共用 :8006; 矩阵只用 :8007 + PG 检索, 零 :5050 流量, B4 计数不受污染。

## 3 工件与复现

- 报告: logs/graph/eval/matrix/{c1_qwen3_14b_think_off, c1_qwen3_14b_think_xhigh, c2_qwen3_8b_think_off, c2_qwen3_8b_think_xhigh}_report.json（GB10, gitignored; 含逐题答案/checks/延迟/token）
- runner: scripts/run_matrix_candidate.py（--label/--thinking/--only 复现任意格）
- 探针手册: llama-server 路径 /home/testuser/.lmstudio/extensions/backends/llama.cpp-linux-arm64-nvidia-cuda13-2.16.0/llama-server, 启动参数 -c 32768 -ngl 999 --flash-attn on, 权重 ~/wzh/models/gguf/{qwen3-14b,qwen3-8b,qwen3-4b}/; :8007 用毕即停（本轮已停, 内存归位）
- 内存算术实测: 14B ≈ +9GB / 8B ≈ +6GB, 与 K4 §3 预算门估算一致

## 4 待办（排期, 不阻塞）

- C3 Qwen3-4B Q4 与 C4 Qwen3-VL-8B（视觉专项）: 下个错峰窗
- 14B 异常复测（新权重或参数）
- 候选答案的 judge 四维打分（:8006 judge --input 候选报告）→ 质量轴补全
- NF 对候选答案跑（需 m2_eval_number_faithfulness.py 支持 --input 参数化, 小改）
