[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('preflight', 'start', 'status', 'logs', 'stop')]
    [string]$Action,
    [ValidateSet('a', 'c')]
    [string]$Role,
    [string]$TaskId,
    [string]$PromptFile,
    [int]$TimeoutSeconds = 0,
    [int]$Lines = 40,
    [switch]$Smoke
)

$ErrorActionPreference = 'Stop'
$ssh = @(
    '-o', 'ServerAliveInterval=15',
    '-o', 'ServerAliveCountMax=4',
    '-o', 'ExitOnForwardFailure=yes',
    'jinrong-dev'
)
$remoteProject = '/home/testuser/wzh/projects/agents_final_tech'
$remoteLauncher = "$remoteProject/scripts/graph/loop_ac_launcher.sh"

if ($Action -eq 'preflight') {
    $suffix = if ($Smoke) { ' --smoke' } else { '' }
    & ssh @ssh "cd $remoteProject && bash scripts/graph/agent_env_preflight.sh && bash $remoteLauncher preflight$suffix"
    exit $LASTEXITCODE
}

if ($TaskId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$') {
    throw 'TaskId must match [A-Za-z0-9][A-Za-z0-9._-]{0,80}'
}

if ($Action -eq 'start') {
    if (-not $Role -or -not $PromptFile) { throw 'start requires -Role and -PromptFile' }
    if (-not (Test-Path -LiteralPath $PromptFile)) { throw "Prompt file not found: $PromptFile" }
    $remoteRun = "/home/testuser/wzh/loop_runs/$TaskId"
    $remotePrompt = "$remoteRun/$Role.prompt.md"
    & ssh @ssh "mkdir -p $remoteRun"
    & scp -o 'ServerAliveInterval=15' -o 'ServerAliveCountMax=4' $PromptFile "jinrong-dev:$remotePrompt"
    $timeoutArg = if ($TimeoutSeconds -gt 0) { " $TimeoutSeconds" } else { '' }
    & ssh @ssh "cd $remoteProject && bash $remoteLauncher start $Role $TaskId $remotePrompt$timeoutArg"
    exit $LASTEXITCODE
}

switch ($Action) {
    'status' { & ssh @ssh "cd $remoteProject && bash $remoteLauncher status $TaskId $Role" }
    'logs'   { & ssh @ssh "cd $remoteProject && bash $remoteLauncher logs $TaskId $Role $Lines" }
    'stop'   { & ssh @ssh "cd $remoteProject && bash $remoteLauncher stop $TaskId $Role" }
}
exit $LASTEXITCODE
