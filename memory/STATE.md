# memory/STATE.md — 当前快照（覆写式）| 快照: 2026-08-06 23:00 | 写入: Loop D（日间队列 1-5 执行中: A2 稳态化）

## 系统状态
- git: 三方对齐, 链: 100b025 → 62d21e3（Loop A flash 首任务: sources 遵从度）→ dbd9b09（B4 排期提案）→ 本快照
- 模型分工: Loop A = deepseek-v4-flash-0731（Token_Plan_Chat, :8100 代理 v3.2）; flash 首个正式任务 PASS（817s, 62d21e3, pytest 261/0 failed）; 其余槽位不变（见 DECISIONS.md）
- A2 灰度: route=on + OPENCODE_ASK_TIMEOUT=18（.env）; sources 遵从度修复实测 10/10 零空 sources; agent 路 p95=17.2s ✓; 发现争用尾部 42.8s（被弃 agent run 的 prefill 干扰直连回落, :8004 为 4 slot）→ B4 p95<20s 暂不达标, 修复选项见 docs/25 §4.3（abort 语义验证 或 :8005 隔离）
- 服务: :5050 up（22:3x 重启, 载入 timeout=18 + adapter 修复）; :4096 sidecar 重建（日间曾停摆, :5050 按设计静默降级无损）; :8004/:8005 LM Studio up; :8100 代理 v3.2 up; docker zhikuncode + pgvector_15432
- 质量: pytest 261 passed / 13 skipped / 0 failed（基线更新: +6 adapter 测试）; RAG QA 15/15
- Loop C: 审计进行中（62d21e3 + cf5df3d + a9ddfc4 + A2 配置）, claude -p 活跃, 判定将落 logs/graph/loop_c_audit_20260806_flash_fixes.md
- 数据集: TAT-DQA 7/7 文件完整 validate 通过（train.zip 1.17GB 已就位, 阻塞解除）
- 红线: 冻结节点零触碰; API key / 72B 未碰; Loop B 未扰动（22:06 PASS）

## 下一步（闸门顺序）
1. Loop C 审计判定落账 → 如有 CONDITIONAL 项按 receiving-code-review 分诊
2. 争用尾部修复拍板（abort 语义 vs :8005 隔离）→ 修复后灰度积累 ≥100 ask / 3 天 → B4 验收（docs/25 §4.3）
3. JSON 解析鲁棒性小修（嵌套引号, Loop A 候选任务）
4. B 阶段不启动, 等甲方/用户拍板

## 台账规则
- gap/遗留项台账唯一存放于 memory/THREADS.md, 其他文档只引用不复述
- STATE/THREADS 的 "已 X" 断言以 dispatch_log 验证条目时间戳为准回写（漂移案例 3 教训, 见 DECISIONS.md）
