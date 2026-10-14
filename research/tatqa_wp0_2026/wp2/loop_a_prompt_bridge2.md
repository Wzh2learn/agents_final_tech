# WP-2 桥 v2 长期实现轮（L1–L4，零模型调用）— Loop A 执行卡

- task: `tatqa-wp2-bridge2-20261014`
- 背景与依据: `docs/research/WP2_BRIDGE_LONGTERM_ANALYSIS_v1.md`（根因+分层设计）；`skills/structured-output/SKILL.md`（可靠性层级与重试规则）。owner 指示"长期方案"。本卡**只做实现与离线资格：不进行任何模型调用、不跑 S4**。
- 范围: 仅 GB10 repo 内实现桥 v2 组件 + 离线资格 + 收据；不扰动 :8004/:8006 与生产服务；依赖变更仅允许 `pip --user` 级并记录；不 git 操作。
- 必读: analysis 文档；`S4B_*` 收据；`serve_transformers_actor.py`；`run_wp2_episode_collection_v2.py`；`research/tatqa_wp0_2026/wp1/implementation_contract.md`（两阶段字段规范）；`adapter.py`。

## L1 生成层：引导式解码（首选 outlines）
- 尝试 `python3.12 -m pip install --user outlines`（记录解析出的版本集合与 license；若冲突/失败 → 走备选）。
- 两个 **flat schema** 写入 `bridge_v2/BRIDGE_SCHEMAS_v2.json`（含 sha256）：
  - plan: `{"tool": enum["calc"], "params": {"expression": string，字符类 [0-9+\-*/(). ]，非空}}`
  - consume: 按 implementation_contract 的字段（row/periods/delta_source/delta_target/unit；数值按十进制字符类）——以合同为准。
- 新增 `bridge_v2/serve_transformers_actor_v2.py`：加载引导解码，设置不变（temp0/512/4096/600），端口 8112 约定不变。
- 备选（若 outlines 不可行）：实现最小自定义约束处理器（前缀强制 + 字符类 allowed-token 掩码，仅覆盖上述两个 flat schema），收据中说明选择与风险。

## L2 接口层：chat 格式 + 硬指令 + 1 示例
- `bridge_v2/prompt_v2.py`: tokenizer chat_template 构造 system+user；system 指令="Return exactly one JSON object; no prose, no code fences"；user=任务；**恰 1 个锁定示例**；产出 plan/consume 模板 sha256。

## L3 桥层：schema 校验 + 计数重试
- `bridge_v2/validate_v2.py`: 三路线解析（保留）→ 叠加 schema 校验（枚举/类型/字符类；never silently coerce）；失败路径全部持久化。
- 格式重试: 每 stage ≤1 次，把具体解析/校验错误回喂；每次请求照常计入预算（本卡不产生任何请求）。

## L4 离线资格（零模型调用）
- 单测: 合成语料（strict json / fenced / embedded / prose / truncated / schema 违约）覆盖 3 路线×校验；
- 重放: 对 `s4b_run/attempts/**` 8 份 raw 跑 parse+validate 并记录结果（散文样本预期被拒——佐证分层必要性，不得"调参拯救"）；
- 接线测试: 构造引导处理器（tokenizer 只读加载即可，不加载权重、不生成）并对 MOCK 输入 dry-run；明示未覆盖面。
- 产出: `research/tatqa_wp0_2026/wp2/bridge_v2/**` + `BRIDGE_V2_RECEIPT.json`（组件哈希、依赖 receipt、离线结果、未验证面）+ `BRIDGE_V2_REPORT.md`。

## 停止点
- 依赖安装破坏环境或需系统级变更 → 停报 BLOCKED（列最短人工步骤）。
- 完成后即停回报；**零模型调用；S4c 需另行批准**。