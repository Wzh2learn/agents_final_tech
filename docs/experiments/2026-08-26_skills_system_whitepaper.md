# Skills 体系白皮书 v1（2026-08-26, 只读梳理）

状态: 活跃 | 更新: 2026-08-26 | 取代/被取代: 无

## ① 三层分发实况

- **仓库 `skills/` = source of truth**: 34 件（2026-08-26 实测, check_skill_sync.sh PASS）。
- **分发层 `scripts/graph/sync_skills.sh`**: 幂等 cp -r, A-list 26 件 → `~/.codex/skills/`（Loop A 执行层）,
  C-list 15 件 → `~/.claude/skills/`（Loop C 审计层）; 不触碰未列名 skill（如 neat-freak 个人件）。
- **漂移检测双闸**: `check_skill_sync.sh`（repo↔分发列表双向: MISSING_DIST/GHOST, 08-09 事故产物）+
  `sync_skills.sh --check`（repo↔两端安装 diff -rq）。08-26 实测: 34 件全登记 PASS / GB10 两端 39 安装项一致 PASS。
- **案例（08-25 GB10 漂移先例链）**: 08-06 两 SKILL.md 缺失重跑修复 → 08-09 m2-rag-playbook 在库未分发
  催生 check_skill_sync.sh → 08-23 #HYG-SKILLS 本机 16/21 漂移修至 21/21 → 08-25 skills-loop-engineering
  精华归位（735813b）同步更新 A/C 双列并分发。教训固化: 归位新 skill 必须同 commit 更新分发列表（钩子级未强制, 靠 check 闸）。

## ② 四 Loop 配属实况（AGENTS 注册表逐件核, 08-26）

- Loop A（Codex CLI, 执行层）26 配属; Loop C（Claude Code, 审计层）15 配属; 双配属 5 件
  （jinrong-docs-sync / m2-rag-playbook / agent-prompt-contracts / verify-before-done / evaluator-calibration）= 执行与审计同基线。
- Loop B 纯 bash 验证层零 skill（设计内）; Loop D 指挥层用本地全套（含个人件 neat-freak v3.0.0 等 44 目录）。
- 注册表 41 行与分发列表逐件吻合; DEPRECATED 1 件（verification-before-completion, 被 verify-before-done 取代, 目录保留）。

**项目特有 skill 逐件一句角色**:
- graph-loop-rules: 冻结节点/生产后端/API key 红线, OpenCode agent 通用准入闸
- jinrong-docs-sync: 文档四层结构 + INDEX 单一入口治理
- m1-gap-triage: 解析失败"读原文→补 synonyms→重跑→报 delta"playbook
- m2-rag-playbook: RAG 问答失败模式对策手册（检索空/数值缺/脱敏/跨文档）
- agent-prompt-contracts: 4 条已验证 prompt 契约（verbatim 首查/FORMAT_HINT/bash 先行/只读 summary）, 治理规则 5 强制同 commit 补录
- eval-harness: grader 隔离/judge prompt 可见/基线入 git 的 eval 骨架
- evaluator-calibration: LLM 评审校准（rubric 锚定/禁读生成者推理/引用式判据）, 08-25 judge 事故对症
- experiment-autopsy: 实验尸检四步法 + tradeoff 前沿共线检验
- sprint-contract: 写码前谓词化 done 契约（交付物/验收/范围外）
- self-eval-bias: 同上下文自夸偏倚检测（侧线抽验机制的理论依据）
- verify-before-done: 11 条假完成捷径清单 + 本轮实跑完成门（取代 verification-before-completion）
- 同源治理件: shift-notes（交接信 git）/ context-budget（上下文纪律, 与 L2 瘦身同源）/ tool-restraint（工具克制, 对应 sidecar 元数据病灶）/ spec-first / broken-window-check / decision-record（ADR↔DECISIONS）
- 审计件: repo-audit（对抗式治理审计）/ readme-audit（INDEX 入口审计）

## ③ 生命周期治理

- 安装仅 Loop D（治理规则 1: 搜索→克隆审计→安装→注册表+skills/→分发）; 其余 49 件源仓库库存不入仓（规则 6）。
- 弃用只标记不删除（规则 4）: verification-before-completion = 先例（注册表 DEPRECATED + 目录保留）。
  **漂移**: 该件 SKILL.md 头部未注明 DEPRECATED（规则 4 要求双注记）, 入 §⑤。
- 钩链: install_hooks.sh 生成 pre-commit 链 = 冻结守卫（pre-commit, 2026-08-06 既有）链首 + 三守卫
  （cjk-byte-check / index-guard / large-file-guard）; 安装器绝不覆盖冻结守卫。
- neat-freak v3.0.0 合并案: 方法论（声明-实况对账）已并入本仓治理（08-22 侧线全文档审计方法栏 + neat 收口规则）,
  实体留个人安装不入仓 = "方法论合并、实体不入仓"模式案例（v3.0.0 合并案源出 skills-loop-engineering）。

## ④ 研究生产层 vs 运维治理层分置

- 运维治理层: ②中红线/文档/eval/治理件 —— 保系统不塌。
- 研究生产层（论文主线武器, 注册表科研线标注）: research-writing-skill（正文/摘要/rebuttal 中文优先）/
  scientific-toolkit-skill（计算/统计/配图, 含 paper-lookup 与 citation-management 子技能）/
  office-academic-skill（学术 Word/PPT）/ paper-polish-and-audit（投稿前审计）/ recsys-toolkit（career/defense 双模式）。
- **论文工作流推荐装配序**: ① research-writing-skill 定稿叙事 → ② scientific-toolkit-skill 出实验/图/统计
  → ③ citation-management 引文 BibTeX → ④ paper-polish-and-audit 投稿前审计 → ⑤ office-academic-skill 出 Word/PPT 交付件。
  （evaluator-calibration 兼跨两层: 论文 judge 实验与运维 eval 同用。）

## ⑤ 已知漂移/欠账清单

1. verification-before-completion SKILL.md 头部缺 DEPRECATED 注记（治理规则 4 双注记未满足）——修=头部加一行, 待代码窗。
2. 源仓库 skills-loop-engineering 漏打包 **audit-inventory.sh**（归位 735813b 未含）: 与 readme-audit/repo-audit 互补的盘点件,
   候选动作=按治理规则 1 评估引入或回推上游清单; 只记不动。
3. 分发列表更新无钩子级强制（靠 check_skill_sync.sh 事后闸）——候选升级: index-guard 式 pre-commit 闸; 只记不动。
4. 本机（Windows）autocrlf 致 .sh CRLF, sync_skills.sh 本机不可执行（08-23 #WORDING-FIX 定性: GB10 为准）——结构性, 记账。
