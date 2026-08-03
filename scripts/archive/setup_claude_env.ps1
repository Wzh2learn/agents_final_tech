# 设置Claude Code CLI的环境变量
if (-not $env:ANTHROPIC_AUTH_TOKEN) {
    throw "请先通过本机安全存储或用户环境变量设置 ANTHROPIC_AUTH_TOKEN。"
}

$env:ANTHROPIC_BASE_URL="https://anyrouter.top"

Write-Host "环境变量已设置：" -ForegroundColor Green
Write-Host "ANTHROPIC_AUTH_TOKEN 已设置（值不显示）"
Write-Host "ANTHROPIC_BASE_URL = $env:ANTHROPIC_BASE_URL"

Write-Host "`n现在你可以运行Claude Code CLI命令了。" -ForegroundColor Green
Write-Host "要进入交互模式，请输入: claude code" -ForegroundColor Yellow
