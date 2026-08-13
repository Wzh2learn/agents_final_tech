<#
.SYNOPSIS
  远程 live 演示隧道：把 GB10 的 :5050 映射到本机，浏览器直开 /m1，配屏幕共享给导师演示。
.DESCRIPTION
  用法:  powershell -NoProfile -File scripts\dev_remote_demo.ps1
  行为:  1) 启动时自动清理上一次残留的同参数 ssh 隧道（自愈）
         2) 建立 ssh -N -L <port>:127.0.0.1:5050 jinrong-dev 隧道（仅本地转发，无公网暴露）
         3) 隧道就绪后自动打开 http://localhost:<port>/m1
         4) 本机 5050 被占用时自动切 15050 并在控制台明示实际地址
         5) Ctrl+C 或关窗退出即断隧道（异常强杀时下次启动自愈）
  故障:  页面 502/打不开时先查 GB10 侧 :5050 存活（ssh jinrong-dev "bash scripts/graph/status.sh"）。
#>
$ErrorActionPreference = 'Stop'

function Test-LocalPort([int]$p) {
    [bool](Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue)
}

function Stop-LeftoverTunnel {
    $left = Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*:127.0.0.1:5050*jinrong-dev*' }
    foreach ($p in $left) {
        Write-Host "[demo] 清理残留隧道 ssh pid=$($p.ProcessId)" -ForegroundColor Yellow
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
    if ($left) { Start-Sleep -Seconds 1 }
}

Stop-LeftoverTunnel

$localPort = 5050
if (Test-LocalPort 5050) {
    $localPort = 15050
    Write-Host "[demo] 本机 5050 被占用，改用 15050" -ForegroundColor Yellow
}
$url = "http://localhost:$localPort/m1"

Write-Host "[demo] 建立隧道: ssh -N -L ${localPort}:127.0.0.1:5050 jinrong-dev"
$ssh = Start-Process ssh -ArgumentList @(
    '-N', '-L', "${localPort}:127.0.0.1:5050",
    '-o', 'ExitOnForwardFailure=yes',
    '-o', 'ServerAliveInterval=15',
    'jinrong-dev'
) -PassThru
$pidFile = Join-Path $env:TEMP 'dev_remote_demo_ssh.pid'
Set-Content -Path $pidFile -Value $ssh.Id

$deadline = (Get-Date).AddSeconds(30)
$ready = $false
while ((Get-Date) -lt $deadline) {
    if ($ssh.HasExited) {
        Write-Host "[demo] SSH 提前退出 (code=$($ssh.ExitCode))：检查 ssh 配置/网络/端口" -ForegroundColor Red
        Remove-Item $pidFile -ErrorAction SilentlyContinue
        exit 1
    }
    if (Test-LocalPort $localPort) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:$localPort/api/health/full" -TimeoutSec 5 -UseBasicParsing
            if ($r.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 500 }
    }
    Start-Sleep -Seconds 1
}
if (-not $ready) {
    Write-Host "[demo] 30s 内隧道未就绪，退出" -ForegroundColor Red
    Stop-Process -Id $ssh.Id -Force -ErrorAction SilentlyContinue
    Remove-Item $pidFile -ErrorAction SilentlyContinue
    exit 1
}

Write-Host "[demo] 隧道就绪。演示地址: $url" -ForegroundColor Green
Write-Host "[demo] 屏幕共享此浏览器窗口；Ctrl+C 或关窗即断隧道" -ForegroundColor Cyan
Start-Process $url

try {
    while ($true) {
        if ($ssh.HasExited) {
            Write-Host "[demo] 隧道断开（SSH 退出），请重跑脚本" -ForegroundColor Yellow
            break
        }
        Start-Sleep -Seconds 2
    }
} finally {
    if (-not $ssh.HasExited) { Stop-Process -Id $ssh.Id -Force -ErrorAction SilentlyContinue }
    Remove-Item $pidFile -ErrorAction SilentlyContinue
    Write-Host "[demo] 隧道已断开"
}
