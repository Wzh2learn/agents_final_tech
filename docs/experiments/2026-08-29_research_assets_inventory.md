# 科研自动化资产台账（GB10 ~/wzh/research/ 五件）

> 状态: 活跃（台账件, 新资产即登记） | 更新: 2026-08-29 | 取代/被取代: 无
> 纪律: 不开新服务不跑重工具（论文优先, 工具克制, 08-29 用户卡）; 红线照旧

| 资产 | 位置 | 来源/版本 | 状态 | 用途与处置 |
|---|---|---|---|---|
| OpenAI4S | ~/wzh/research/openai4s_probe | PKU-YuanGroup/OpenAI4S @ ec37053 | 已克隆未运行 | 科学智能基准/工具库; **挂长期候选**, 论文优先不启动（用户卡明示） |
| tabfm | ~/wzh/research/tabfm | google-research/tabfm @ d8678b6（v1.0.1） | 已克隆未运行 | 表格基础模型相邻资产; 与表头映射主线弱相关, 备用不改 |
| academic_skills_audit | ~/wzh/research/academic_skills_audit | zLanqing/codex-claude-academic-skills @ 7ed6377（08-13 克隆） | **08-29 漂移检查: 上游无新提交, 三件技能与上游逐文件零差异, 不回灌** | 本仓学术技能源仓库（research-writing/office-academic/scientific-toolkit 三件）; 漂移复查随季度复审 |
| m0_lit | ~/wzh/research/m0_lit | 5 篇记忆/自进化全文（网页转储 + batch 元数据） | **08-29 已接入科研线 Phase 2（相关工作三簇补强, 见 related_work_v3）** | MemoryAgentBench / Evo-Memory / RecMem / Q-Evolve / Self-Evolving Coding Agents 综述 |
| openai4s_data_probe | ~/wzh/research/openai4s_data_probe | 空工作区（openai4s.db + artifacts/logs 脚手架） | 空置 | 随 OpenAI4S 长期候选, 不单独处置 |

## 漂移检查记录（08-29）

- academic_skills_audit: `git ls-remote origin HEAD` = 7ed6377 = 本地 HEAD（上游未动）;
  `diff -rq` 三件技能目录与仓内 skills/ 零差异 → **无实质更新, 不回灌, 记账**
- 同步链备查: 上游有更新时 = 拉新 → 审变更 → 入仓 skills/ → sync_skills.sh 两端 → 注册表核对
