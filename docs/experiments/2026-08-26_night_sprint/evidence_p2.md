# Phase 2 证据（judge 修复 F-J1/F-J2, 08-26 凌晨）

## F-J1 None 安全化
- 病灶: `_judge_avg` 对 01:51 工件（四维 avg=null/n=0）走 float(None) 炸; 且即便不炸,
  旧路径会给 0 分静默拖树（违反"缺工件显式降级"设计）。
- 修复: scripts/eval_checkpoint_aggregate.py diff 25 行（闸 ≤30）:
  avg=null|n=0 → 返回 val=None → `_mapped_leaf_score` 回落 missing_score(5) + degraded=True + reason 显式。
- 单测: tests/test_eval_checkpoint_aggregate.py 新增 TestFJ1JudgeUnusableArtifact 三例
  （sentinel/叶子降级/全树不炸, 工件形状=01:51 summary 逐字复刻）; 23 passed。
- 回滚点: 修改前 commit 7d3dd52。

## F-J2 隔离闸
- 病灶: W3 judge 用 :8006 override, 被 NF 孤儿轨迹自我饱和（归因报告证据 3/4）。
- 修复: scripts/run_eval.sh 加 wait_judge_idle: 端点为 :8006 时轮询 vLLM
  running+waiting==0（15s×40=10min 上限）, 不达显式跳过 judge（JD_RC=3, 不静默打分）。
- 重跑协议: 串行（run_eval 本就顺序）+ 闸; 今晚重跑带 M2_JUDGE_ENDPOINT=:8006 保持与 k1 基线可比。

## eval 重跑（进行中, 结果见收口时 v3 一页纸与本报告回填）
- 基线对照: 16/16 确定性 / NF 0 幻觉 / judge 出数或显式失败。
- 规则 J: avg>=4.5 且零 unusable → docs/31 写实数+重生成 docx; 否则诚实口径。
