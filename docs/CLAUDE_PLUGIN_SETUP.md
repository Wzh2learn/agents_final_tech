# Claude / Anthropic 插件（VS Code）配置说明

我已在工作区添加了一个 VS Code 设置文件来把你提供的 Anthropic 相关环境变量注入到 VS Code 的集成终端：

- 文件：`.vscode/settings.json`
- 注入的环境变量：`ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_BASE_URL`

注意：把密钥写入仓库文件会泄露凭据（如果仓库会被推到远端）。建议把真实密钥从仓库移除，改用以下任意一种更安全的方式：

1. 在本机 PowerShell 配置文件中设置（建议）
   - 临时（当前 PowerShell 会话）设置：

```powershell
$env:ANTHROPIC_AUTH_TOKEN = "sk-mdNzHw36Xdido9tC5SzX6TKTue26K4WPhOtqsuIw3IeS1bSo"
$env:ANTHROPIC_BASE_URL = "https://anyrouter.top"
```

   - 持久（将写入你的 PowerShell 用户配置文件 `$PROFILE`，以后打开 PowerShell 生效）：

```powershell
'$env:ANTHROPIC_AUTH_TOKEN = "sk-mdNzHw36Xdido9tC5SzX6TKTue26K4WPhOtqsuIw3IeS1bSo"' >> $PROFILE
'$env:ANTHROPIC_BASE_URL = "https://anyrouter.top"' >> $PROFILE
# 然后重启 PowerShell 或 VS Code
```

2. 使用 Windows 的 setx（会在新会话生效）：

```powershell
setx ANTHROPIC_AUTH_TOKEN "sk-mdNzHw36Xdido9tC5SzX6TKTue26K4WPhOtqsuIw3IeS1bSo"
setx ANTHROPIC_BASE_URL "https://anyrouter.top"
# 注意：setx 写入后需要重启终端或登出/登录才能在新会话看到变量
```

3. 使用 VS Code 的 Secrets/Settings（某些 Claude 插件可能支持在扩展设置中填写 API key）或使用系统级环境变量管理工具。

如何让 VS Code 的扩展读取这些变量：

- 如果你在 PowerShell 中设置了环境变量并用 VS Code 从该 PowerShell 启动（或在 VS Code 中启动集成终端），大多数插件会自动从环境读取。
- 我已在 `.vscode/settings.json` 中把变量注入到 `terminal.integrated.env.windows`，这会让 VS Code 集成终端以及从里面启动的进程看到变量。

重要安全提示
- 请不要把包含真实密钥的工作区设置提交到远端仓库。如果需要，我可以把 `.vscode/settings.json` 改为使用占位符，并把真实密钥放到你的本地 PowerShell profile 或提供一个不提交的 `.env.local` 文件。

如果你希望我：

1. 把刚写入的真实密钥替换为占位符（例如 `ANTHROPIC_AUTH_TOKEN="<PASTE_YOUR_KEY_HERE>"`）并把真实设置步骤写入本地 docs（更安全），或
2. 直接把密钥从仓库文件删除并给出一套更安全的自动化脚本（例如使用 `direnv`、Windows Credential Manager 或 VS Code Secret Storage），

请告诉我你更偏好的方式，我会继续执行并把 todo 完成。
