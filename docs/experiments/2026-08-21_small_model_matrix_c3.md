# 小模型矩阵 C3 — Qwen3-4B Q4 探针（N3 夜间错峰）

状态: 活跃 | 更新: 2026-08-21 01:40 | 类型: 小模型矩阵 C3（批复 ② 口径, 逐个 go/no-go）
工件: logs/graph/eval/matrix/c3_qwen3_4b_think_{off,xhigh}_report.json（GB10, gitignored）
预算门: 起探前 available 36G, 4B Q4 实测约 +3.5G, 余量 >30G → GO; :8007 探针, 用毕即停（已停）; 零下载（权重本地既有）

## 1 结果

| 候选 | 档位 | 得分 | 耗时特征 | 失败题 | go/no-go |
|---|---|---|---|---|---|
| A3B :8004（基线） | off | 16/16 | ~2s/题 | — | 守擂 |
| C3 Qwen3-4B Q4 | off | **14/16** | 0.2-2.9s/题, 16 题共 ~15s | q09_minan_end_date(218ms, 疑快拒), adv_ocr_meta | NO-GO |
| C3 Qwen3-4B Q4 | xhigh | 13/16 | 3.7-16.5s/题, 共 ~2.5min | q01_fuxi_total_assets, q05_fuxi_securities_value, q11_fuxi_security_names | NO-GO |

替换生产快路/准路需 16/16 零回归 → C3 双档 NO-GO。

## 2 洞察

1. **4B 出现"思考负增益"**：off 14 > xhigh 13，且两档失败题集不相交（off 挂 q09/adv_ocr_meta，xhigh 挂 q01/q05/q11 数值题）——4B 的深度思考不能稳定修复数值抽取，反而引入新错。对照 14B（11→14 正增益）/8B（14→15 弱正增益），思考档位效应非单调，存在模型容量门槛。
2. **q08_fuxi_customer_name（掩码客户名）在 4B 双档全过**——而 14B-xhigh 与 8B-xhigh 均失败。与 8B>14B 异常同向：更小模型在该题上反而更稳，进一步支持"候选量化批次/模板行为差异 > 参数量"假设；该题的"路由难题集"定性保留，但"小模型必败"结论不成立。
3. 成本轴：4B off 全程 ~15s（16 题），快于 A3B 基线 ~2s/题 的总和口径，但质量差 2 题——与 8B（15/16 xhigh）一起构成"廉价 verifier 候选梯队"，8B 仍优于 4B（质量轴），4B 优势仅在极致延迟场景。

## 3 待办更新（并入小模型矩阵待办）

- C4 Qwen3-VL-8B 视觉专项：下个错峰窗
- 14B 异常复测（新权重或参数）
- 候选答案 judge 四维打分（质量轴补全）