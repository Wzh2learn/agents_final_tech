[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$userHome = $env:USERPROFILE
$paths = [ordered]@{
    CODEX_HOME = Join-Path $userHome '.codex'
    CLAUDE_CONFIG_DIR = Join-Path $userHome '.claude'
    OPENALEX_CONFIG = Join-Path $userHome '.config\openalex.env'
    CODEX_API_ENV = Join-Path $userHome '.codex\token_plan.env'
    CODEX_AUTH_FILE = Join-Path $userHome '.codex\auth.json'
    AGENT_RUNTIME_ROOT = Join-Path $userHome 'wzh\loop_runs'
    AGENT_PROJECT_ROOT = 'D:\AIRcommend\JinRongAgents\agents_final_tech'
}

$pathsFile = Join-Path $userHome '.config\jinrongagents\paths.env'
if (Test-Path -LiteralPath $pathsFile) {
    foreach ($line in Get-Content -LiteralPath $pathsFile) {
        if ($line -match '^\s*([A-Z0-9_]+)\s*=\s*"?([^"]*)"?\s*$') {
            $name = $Matches[1]
            $value = $Matches[2].Replace('${USERPROFILE}', $userHome).Replace('$USERPROFILE', $userHome).Replace('${HOME}', $userHome).Replace('$HOME', $userHome).Replace('${CODEX_HOME}', $paths.CODEX_HOME).Replace('$CODEX_HOME', $paths.CODEX_HOME)
            if ($paths.Contains($name)) { $paths[$name] = $value }
        }
    }
}

foreach ($name in @('CODEX_HOME', 'CLAUDE_CONFIG_DIR', 'OPENALEX_CONFIG')) {
    $path = $paths[$name]
    $exists = Test-Path -LiteralPath $path
    Write-Output ("{0}={1} present={2}" -f $name, $path, $exists)
    if (-not $exists) { exit 1 }
}

$envExists = Test-Path -LiteralPath $paths.CODEX_API_ENV
$authExists = Test-Path -LiteralPath $paths.CODEX_AUTH_FILE
Write-Output ("CODEX_API_ENV={0} present={1}" -f $paths.CODEX_API_ENV, $envExists)
Write-Output ("CODEX_AUTH_FILE={0} present={1}" -f $paths.CODEX_AUTH_FILE, $authExists)
if (-not ($envExists -or $authExists)) {
    Write-Error 'Missing Codex auth carrier: token_plan.env or auth.json'
    exit 1
}

foreach ($name in $paths.Keys) {
    Write-Output ("{0}={1}" -f $name, $paths[$name])
}

codex --version
claude --version
Write-Output 'agent_env_preflight: PASS; secret values not read or printed'
