# 18 - 过夜 Loop D 监督收尾（neat-freak 收尾，2026-07-30）

> 窗口：2026-07-30 ~01:00–~03:40 CST，由本机 Codex 作为 Loop D（战略/指挥层）自主监督执行。
> 本文是 neat-freak 收尾：把代码、运行态、文档、规则、记忆、工作区六面对齐到唯一现役事实。

## 1. 本窗口完成的增量（均已 commit + push，三方 git 对齐至 5ec81ab）

| commit | 内容 | 验证 |
|---|---|---|
| ee44100 | M1 解析器：表头信息 kv 块路由到 header_meta；标准名优先匹配 | 真实样本 unmapped 5→3；pytest 18/18；:5050 端点重启生效 |
| 42e8f45 | codex 模型切换助手 switch_codex_model.sh + AGENTS 切换说明 | 远程实测 glm↔qwen 双向切换 + 代理 :8100=200 |
| 5ec81ab | 72B vs 35B 有界对比（脱敏汇总） | 72B 加载→跑→kill，端口释放；原始输出在 ~/wzh/ 不入库 |

## 2. M1 解析（P1）结论

- 真实甲方样本 unmapped 由 5 降到 3，靠两个真缺陷修复（非刷指标）：
  (a) PDF 把"表头信息区"误识成网格表 → 现路由到表头区 KV 提取（信息不丢，只是归位）；
  (b) 证券市值 被 资产市值 的别名"影子"抢占 → 加"标准名==列名"优先级 4，列名即标准名时优先该字段。
- 剩余 3 个 unmapped（财汇局征费 / 备注 / 配号日期）是 schema 未建模的列，正是甲方 UI"新增字段"
  应喂入的冷启动候选——保留它们是正确行为，压到 0 反而是过拟合单一样本、抹掉冷启动信号。

## 3. 模型切换（P3）结论

- glm-5.2 / deepseek-v4-pro 在千问 Token Plan 只说 Chat Completions；responses2chat 代理(:8100)
  把 Responses→Chat，已验证 codex exec 端到端通。
- 切换助手 scripts/switch_codex_model.sh [qwen|glm|deepseek] 改 ~/.codex/config.toml 的
  model/model_provider，glm/deepseek 自动确保代理在跑。默认 qwen3.8-max-preview（直连）。

## 4. 72B vs 35B（P2）结论

- 延迟是有效结论：72B ≈248s vs 35B ≈17s/次结构化抽取 → 72B 在 GB10 不适合在线 M1 抽取；
  35B 是可行的本地 LLM 抽取引擎（但主 M1 引擎是已加固的规则解析器，不需 LLM）。
- strict_json 两模型皆 bad 是 harness 限制，非模型能力：/no_think + 去围栏后仍未出严格 JSON，
  系 Qwen3 思考模板与 llama.cpp 的交互（答案落在 prose/reasoning_content）；需 thinking-disable
  调优（服务端 --chat-template-kwargs enable_thinking=false 或解析 reasoning_content），属定性
  prompt 工程，留交互会话做。原始模型输出在 ~/wzh/p2_raw_72b_vs_35b.md（含客户值，不入库）。
- 72B 仅本有界运行加载，跑完即 kill，端口 8006 已释放；未整夜常驻。

## 5. 战略层仲裁记录（我故意没做的事，及理由）

- 未启动 Loop A 自主写代码：让 LLM 在无人监督下整夜写代码正是 Graph Engineering 文章警告的
  反模式（古德哈特 + 向上盲视）。Loop A 的执行改由"我监督下有界增量"完成；Loop A 自动执行留待
  用户评估风险偏好后开启。
- 未把 72B 整夜常驻 / 未做严格 JSON 调优：前者有共享内存 OOM-killer 波及在线 35B 的风险；
  后者是定性调优，需用户在场看输出。两者都记录为"有界尝试/延后交互"，而非悄悄跳过。
- 客户原始对账单与抽取 JSON 一律不入库：脱敏汇总入库，原始留 ~/wzh/。

## 6. Graph Engineering 运行态

- Loop B（独立验证守护）常驻：tmux graph-loop-b，每 30 分钟跑冻结节点 hash + pytest 18 +
  curl 锚点 + 模型健康，写 logs/graph/verify-report.json。这是"持续盯着"的硬保障，不依赖本机在线。
- Loop D 影子：tmux graph-loop-d 每 10 分钟写 /tmp/graph_dashboard.txt。
- Loop C（质量审计）：按需单次触发，不整夜 daemon（无新产出时空转无意义）。
- Loop A：见第 5 节，故意未自动启动。

## 7. neat-freak 六面对齐

| 面 | 状态 | 证据 |
|---|---|---|
| 代码 | verified-current | m1_statement_parser 两修复 + switch 助手，已 commit，三方对齐 5ec81ab |
| 运行态 | verified-current | :5050 端点用新解析器；:8100 代理在跑；:8004/:8005 健康；72B 已停 |
| 文档 | changed-and-verified | 本文 + docs/17 演进行 + AGENTS 切换说明 + 各 experiments 报告 |
| 规则 | verified-current | AGENTS.md 含切换方法与边界；冻结节点 hash 与远程 schema 一致 |
| 记忆 | not-applicable | 本作用域无获准长期记忆；结论均落入 docs |
| 工作区 | verified-current | 三方 git 5ec81ab；远程仅 .qoder 未跟踪（qoder cli 配置，预期） |

## 8. 待用户定夺 / 交互会话建议（按价值排序）

1. M1 页面浏览器验收：三面板对账单工作台（m1.html/js/css + /api/m1/parse-file）已就位但
   未浏览器实测；启动 :5000/:5050 打开 /m1 上传一份真实对账单看三面板渲染。
2. 严格 JSON 调优（让 P2 变成真正的质量对比）：在 :8004/:8006 用 enable_thinking=false 或
   解析 reasoning_content，重跑 2 样本，肉眼看 ~/wzh/p2_raw 判断 72B 是否"抽得更全"。
3. 是否把 3 个冷启动列建模：若甲方希望 备注/财汇局征费/配号日期 进标准 schema，Loop D 授权
   加字段 + 刷新冻结 hash；否则保留为"新增字段"候选。
4. 是否开启 Loop A 自动执行：若接受"无人监督写代码"的风险，可用 graph_orchestrator.sh start
   拉起 Loop A 并让 Loop B 制衡；否则维持"我监督下有界增量"。
5. 72B 使用策略：仅在需要时临时加载（参考 P2 延迟），用完即 kill；在线 M1 用规则解析器或 35B。

## 9. 常用操作速查

- 看 Loop B 最新结论：ssh jinrong-dev "cat ~/wzh/projects/agents_final_tech/logs/graph/verify-report.json"
- 看战略 dashboard：ssh jinrong-dev "cat /tmp/graph_dashboard.txt"
- 切 codex 模型：ssh jinrong-dev "bash ~/wzh/projects/agents_final_tech/scripts/switch_codex_model.sh glm"
- 看 72B 原始抽取（含客户值）：ssh jinrong-dev "cat ~/wzh/p2_raw_72b_vs_35b.md"

---
收尾人：Loop D（本机 Codex），2026-07-30。