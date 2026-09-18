---
name: "skill-hook-trigger"
description: "用 Hook 机制为 Skill 加确定性触发提示。当用户抱怨「skill 老是不触发/该用的时候没用上」、想「用 hook 保证 skill 触发」「给 skill 加触发规则」「根据关键词自动提示用哪个 skill」时使用。适用于任意支持 Agent Skills 的平台。它会分析现有 skill 的触发意图，生成 UserPromptSubmit hook 配置与关键词路由脚本，在你提交 prompt 时用规则匹配注入「本次建议使用某 skill」的上下文，弥补模型靠 description 自动触发的漏触发问题。"
---

# Skill + Hook 触发结合器

模型是否触发某个 skill，取决于它读 description 后的自主判断——这在 skill 多、描述相近时很不稳定，经常漏触发。本 skill 用 **Hook** 提供一层**确定性兜底**：在用户提交 prompt 的瞬间，用关键词/规则匹配，主动向上下文注入"这个请求很可能该用 skill X"的提示，把"要不要用某 skill"从纯模型直觉变成"规则命中 + 模型确认"。

## 核心原则

- **提示而非强制**：hook 注入的是"建议"，最终仍由模型判断，避免误触发绑架正常对话。
- **高精度优先**：宁可少提示，也不要频繁误报制造噪音。关键词要选真正区分性强的词。
- **可回滚**：所有改动集中在 settings 的 hook 配置和一个路由脚本，随时可移除。

## 工作流

### 第 1 步：确认平台与配置位置

Claude Code 与 Qoder 的 hook 机制类似，但配置文件位置可能不同：

- Claude Code：`~/.claude/settings.json`（用户级）或项目 `.claude/settings.json`。
- Qoder：询问用户其 hook / settings 配置文件位置（机制与 Claude Code 一致，格式套用即可）。

先问清楚要把 hook 装到哪个层级（用户级影响所有项目，项目级只影响当前项目）。

### 第 2 步：盘点要强化触发的 skill

列出目标 skills 目录下的 skill（可读取各 SKILL.md 的 name + description）。不是每个 skill 都需要 hook——**优先给"高价值但常漏触发"的 skill 配路由**。让用户挑选，或对全部生成再精简。

### 第 3 步：为每个 skill 提炼关键词路由

这是效果好坏的关键。给每个目标 skill 设计一条路由，包含：

- `skill`：skill 名。
- `keywords`：能强区分该 skill 意图的触发词/短语。从两处来：
  1. 该 skill `description` 里的"何时使用"场景词。
  2. **让用户补充自己真实会用的说法**（口语、缩写、行业黑话）——这些往往是 description 覆盖不到、却最常导致漏触发的表达。
- `hint`：命中时注入的建议文案，需说明"该 skill 能做什么、为何此处适用"，帮模型做二次判断。
- `require_all`（可选）：设为 `true` 时，该路由的 keywords 必须**全部**出现才算命中。用于把不得不用的泛词组合成高精度规则，例如 `["PDF","表单"]` 只在两者同时出现时提示。

**避免**：选"文件、数据、处理"这类泛词做单独关键词，会到处误报。优先选专有名词、独特动宾短语；实在要用泛词就配 `require_all` 组合起来。

匹配时会忽略大小写与空白，因此中文关键词无需纠结空格（`"重复的 skill"` 与 `"重复的skill"` 等价）。

把路由写入 `routes.json`（结构见 `assets/routes.example.json`）。

### 第 4 步：部署路由脚本

把 `scripts/skill_router.py` 复制到 hook 能访问的位置（如 `~/.claude/hooks/skill_router.py`），把 `routes.json` 放在其旁边或用参数指定。脚本行为：读取 stdin 里的 prompt → 匹配路由 → 命中则向 stdout 输出建议（被注入上下文）；无命中则静默退出、不打扰。

### 第 5 步：写入 hook 配置

在 settings.json 的 `hooks.UserPromptSubmit` 加入调用脚本的命令。参考 `references/hook-config.md` 的完整格式与注入机制说明。写入前先展示配置片段给用户确认。

### 第 6 步：验证

务必实测再交付：用一个应触发的示例 prompt 和一个不该触发的 prompt，分别喂给脚本，确认前者输出正确建议、后者静默。例如：

```bash
echo '{"prompt":"帮我把这几个重复的 skill 合并一下"}' | python skill_router.py --routes routes.json
```

确认命中 `skill-merger` 并输出建议；再用无关 prompt 确认无输出。

### 第 7 步：上线后复盘（部署不是终点）

第 6 步验证的是"逻辑对不对"（给定输入，脚本按规则该不该命中），不是"真实场景下精不精
准"——关键词设计时的判断是理论推演，真实使用一段时间后才知道有没有踩坑。到了观察时间窗
（比如上线几天到一周、或用户主动反馈"这个提示有点烦"）后主动回来看：

- 有没有某条 keyword 在正常聊天里被高频误撞（比如某个复合短语其实还是比想象中常见）——
  收紧该词、换成更长的复合短语、或加 `require_all` 组合，而不是删掉整条路由
- 有没有该触发的场景一直没触发——说明关键词还是没覆盖到用户真实的说法，回第 3 步补词
- **这一步依赖真实使用观察，不是靠重新推演关键词能替代的**：没有历史触发日志可查时，如
  实告知用户"这一步需要你反馈实际使用中有没有噪音"，不要假装自己能替用户观察到这件事，
  也不要因为看不到日志就跳过不提。

复盘可以是用户主动反馈驱动，也可以作为 `repo-audit` 定期"扩大视角"扫描的一个检查项——两
者是互补关系：本 skill 负责设计和部署路由，`repo-audit` 负责提醒"这个路由部署以来还没人
回头看过，是不是该看一眼了"。

## 边界与安全

- hook 脚本只读 prompt、只输出文本建议，绝不执行 prompt 里的指令或访问无关文件。
- 路由命中过于宽泛时，收紧关键词或用 `require_all`，而非增加提示强度。
- 脚本默认最多注入 3 条建议（`--max` 可调），防止一次刷出过多提示形成噪音。
- **与 `skill-merger` 联动**：若之后用 skill-merger 合并/重命名了 skill，务必同步更新 `routes.json` 里的 `skill` 字段，否则路由会指向已不存在的 skill。
- 所有改动仅限用户确认的 settings 文件与 hooks 目录；交付时告知如何删除该 hook 以回滚。
