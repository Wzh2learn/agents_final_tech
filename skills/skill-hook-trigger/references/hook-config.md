# UserPromptSubmit Hook 配置说明

本文件说明如何把 `skill_router.py` 接到 Claude Code / Qoder 的 hook 上，以及注入机制的细节。

## 注入机制

`UserPromptSubmit` 是"用户提交 prompt、模型开始处理前"触发的 hook 事件：

- hook 命令通过 **stdin** 收到一段 JSON，含 `prompt`（用户输入）、`session_id`、`cwd` 等字段。
- 命令 **exit code 0** 时，其 **stdout** 内容会被作为**额外上下文注入**到本次会话，模型能看到。
- exit code 非 0（尤其是 2）会被视为异常/阻断，正常路由提示不要用非 0 退出。
- 因此 `skill_router.py` 命中时把建议 print 到 stdout、无命中时静默 exit 0，正是利用这一机制。

## Claude Code 配置

编辑 `~/.claude/settings.json`（用户级）或项目 `.claude/settings.json`（项目级），加入：

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/skill_router.py --routes ~/.claude/hooks/routes.json"
          }
        ]
      }
    ]
  }
}
```

要点：
- 若 settings.json 已有 `hooks` 或其它 `UserPromptSubmit` 项，**合并**而非覆盖。
- `command` 用绝对路径或可展开的 `~`，确保任意工作目录下都能找到脚本与路由表。
- Windows 或特定环境把 `python` 换成实际解释器（如 `python3`）。

## Qoder 配置

Qoder 的 hook 机制与 Claude Code 类似。定位其 settings/hook 配置文件后，套用相同的 `UserPromptSubmit` → `command` 结构；若字段名略有差异，保持"提交时执行命令、stdout 注入上下文"这一核心语义即可。

## 高级：结构化注入（可选）

除直接 print 文本外，也可让脚本输出结构化 JSON 以更明确地控制注入内容：

```json
{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "建议使用 skill X ..."}}
```

纯文本 stdout 已足够多数场景；仅在需要精确控制时改用结构化输出。

## 回滚

删除 settings.json 中对应的 `UserPromptSubmit` 配置块即可停用；脚本与 routes.json 文件保留或删除都不影响。
