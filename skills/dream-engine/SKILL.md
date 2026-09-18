---
name: dream-engine
version: 0.3.0
description: |
  认知梦境引擎。模拟人类做梦过程，从用户的研究笔记中发现远距离联想，产出研究 idea。
  触发词：做梦、联想、灵感、论文idea、研究方向、记忆整理、创意发散。
  示例：帮我做个梦、有什么研究灵感、跑一次联想、看看最近的idea、给这个idea评分。
metadata:
  author: user
  category: research-tools
  tags: [dream, cognition, research, paper, idea-generation]
allowed-tools: [Bash, Read, Write, Glob, Agent]
---

# Dream Engine — 认知梦境引擎

## 架构原则

- Claude Code IS the LLM — 不需要外部 API key
- Python 只做：文件 I/O、分块、图算法（NetworkX）、JSON 存储
- 所有推理（概念提取、碰撞对选择、做梦联想、分析、评分）由 Claude Code 内联完成

## 前置条件

1. 项目根目录需有 `config.yaml`（参考 skill 目录下 `config.template.yaml`）
2. Python 依赖：`pip install networkx pyyaml numpy jsonschema`
3. 首次使用需 `/dream ingest` 导入数据

## 命令约定

所有 Python 命令格式（不依赖用户主目录布局；2026-07-30 二轮修复：向上探域根后自动选两侧副本，.claude/config 任一侧、project 域内任意 cwd 均可执行，两侧同文本无需人工换前缀）：
```bash
# 定位 skill 目录：从当前目录向上找到含 skills/dream-engine 的域根，优先 .claude 侧
D=$PWD; while [ "$D" != "/" ] && [ ! -d "$D/.claude/skills/dream-engine" ] && [ ! -d "$D/skills/dream-engine" ]; do D=$(dirname "$D"); done
SKILL_DIR=$(ls -d "$D"/.claude/skills/dream-engine "$D"/skills/dream-engine 2>/dev/null | head -1)
PYTHONPATH="$SKILL_DIR/scripts" python3 -m dream_engine.helpers --config config.yaml <command> [args]
```

以下文档中简写为 `helpers <command>`。

---

## /dream ingest [path]

导入记忆节点。

```bash
helpers ingest [--path <路径>]
```

输出：`{"new_nodes": N, "total": M, "by_type": {...}}`

**gist 自动生成（新增节点 ≤ 50 时）：**
1. `helpers load-nodes --ids <缺gist节点id>`
2. 对每个节点生成一句话 gist（≤40字）：不是摘要，而是"只能记住一件事记什么"
3. `helpers update-gists --input /tmp/gists.json`

---

## /dream search "query"

语义搜索。

1. `helpers list-gists` → 获取全量 gist JSON 数组
2. 用你的推理能力找出最相关的 5-10 个节点
3. `helpers load-nodes --ids <ids>` → 加载完整内容，呈现给用户

---

## /dream run [--num N]

执行做梦周期，产出研究 idea。默认 N=3。

**步骤：**

1. **提取引力中心（gravity_centers）**
   如果 config.yaml 配置了 `gravity_center_source`，读取该文件提取 3-5 个未解决核心问题。否则用 config.yaml 中 `gravity_centers` 兜底值。

2. **发现远距离联想对**
   按优先级：
   - **有图谱**：`helpers run-activation --seed random`
   - **无图谱、≤ 500 节点**：`helpers list-gists`，你直接选 N 对最有"概念张力"的节点对
   - **无图谱、> 500 节点**：`helpers find-collisions --num 8`，你筛选最好的 N 对
   
   概念张力 = 看似无关但可能存在深层联系，组合后能产生研究问题。
   筛选规则：
   - 淘汰：两个节点都是工程/运维话题
   - 淘汰：联系一眼可见（同一子领域的标配组合）
   - 偏好：一个是现象/问题，另一个是来自不同子领域的方法
   - 偏好：至少一个与 gravity_centers 相关
   
   选定后 `helpers load-nodes --ids <ids>` 加载完整内容。

3. **做梦（创造模式）**
   对每组碰撞对，写一个荒诞的视觉场景（100字以内）。
   - 每个概念在场景中有对应物，越超现实越好
   - **禁止**：不分析、不写论文骨架、不评分

4. **醒来（分析模式）**
   读回梦境场景。对每个场景，**从场景出发分析，而非从原始文档出发**：
   - 被遗忘的变量：场景暗示了什么被现有研究忽视的因素？
   - 论文骨架：problem → insight → method → expected result
   - 最强反对意见（引用具体已有工作）
   - 最小验证实验（1天内可验证）

5. **独立评审（hostile reviewer via Agent）**
   对每个 idea，用 Agent tool 生成独立 agent 做 double-blind review（切断上下文锚定）。
   
   Agent prompt 只传 idea 摘要，不传梦境场景和原始内容：
   ```
   你是{config.yaml domain.reviewer_profile}。以下 idea 提交到顶会，请严格评审：
   Title: {title} | Problem: {problem} | Insight: {insight} | Method: {method} | Expected Result: {expected_result}
   攻击维度：(1) 和已有工作的区别 (2) 核心假设是否可验证 (3) 研究洞见还是工程优化
   输出纯 JSON: {"verdict": "weak|engineering_only|survive", "attack": "...", "suggested_improvement": "..."}
   ```
   
   处理：weak → 合并或删除（至少保 1 个）；engineering_only → confidence="engineering_only"，score_novelty/score_surprise < 0.3；survive → attack 写入 strongest_objection

6. **评分、输出与保存**
   对每个存活 idea：
   - `readable_abstract`（3-5句通俗解释）+ `illustration`（ASCII示意图）
   - 多维评分（0.0-1.0）：score_novelty, score_feasibility, score_soundness, score_surprise, score_applicability + score_rationale
   - 分类：score_novelty < 0.5 AND score_surprise < 0.5 → engineering_only
   - 组装 DreamResult JSON，写入 /tmp/dream_result.json
   - `helpers save-dream --input /tmp/dream_result.json`
   - 向用户呈现做梦报告（倒金字塔，按评分排序）

---

## /dream ideas [--limit N]

查看历史 idea。读取 `data/dreams/*.json`，格式化展示。

---

## /dream status

```bash
helpers status
```

---

## /dream rate <id> <1-5>

评分 + Hebbian 反馈（图谱存在时自动触发边权重更新）。

```bash
helpers rate --idea-id <id> --rating <N>
```

---

## /dream graph build

**可选，推荐节点 > 500 时使用。**

1. `helpers list-gists` → 读取 prompts/p1_extract.txt
2. 分批提取概念节点 → `helpers save-concepts --input /tmp/dream_concepts.json`
3. 可选：去重（prompts/p5_dedup.txt）、跨文档边（prompts/p2_edge_*.txt）

---

## /dream consolidate

**需要先构建图谱。** 运行 NREM 记忆巩固（选择性回放 → 全局下调 → 修剪）。

```bash
helpers consolidate
```

---

## /dream explore <idea_id>

深度探索 idea 的理论支撑和落地可行性。支持前 8 位 id 匹配。

1. 加载 idea → `helpers list-gists` → 找相关节点 → `helpers load-nodes`
2. 分析：理论支撑、差异分析、落地路径、风险评估、实验设计
3. 输出 mini research report

---

## 自然语言映射

| 用户说 | 执行 |
|--------|------|
| "帮我做个梦" / "有什么新灵感" | /dream run |
| "把这篇论文吃进去" / "ingest" | /dream ingest |
| "搜索 XXX" | /dream search |
| "看看最近的idea" | /dream ideas |
| "给5分" / "这个不行" | /dream rate |
| "深入看看这个idea" | /dream explore |
| "状态" | /dream status |
