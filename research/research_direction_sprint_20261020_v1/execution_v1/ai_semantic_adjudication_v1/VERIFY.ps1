$ErrorActionPreference = 'Stop'
$executionRoot = Split-Path -Parent $PSScriptRoot
$adjudication = Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'ADJUDICATION.json') | ConvertFrom-Json
$draft = Get-Content -Raw -LiteralPath (Join-Path $executionRoot 'experience_scope/SCOPE_TASK_DRAFT.json') | ConvertFrom-Json
$issues = @()
$anchorCount = 0

foreach ($inputFile in $adjudication.source_inputs) {
    $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $executionRoot $inputFile.path)).Hash.ToLower()
    if ($actualHash -ne $inputFile.sha256) { $issues += 'INPUT_CHANGED: ' + $inputFile.path }
}
$taskIds = @($adjudication.cases.task_id)
if ($taskIds.Count -ne 24 -or @($taskIds | Select-Object -Unique).Count -ne 24) { $issues += 'CASE_COUNT_OR_DUPLICATE' }
if (@(Compare-Object @($draft.tasks.task_id) $taskIds).Count) { $issues += 'TASK_ID_MISMATCH' }
foreach ($ruling in @('KEEP_DEVELOPMENT', 'REPAIR_AND_REVIEW', 'EXCLUDE_CURRENT')) {
    if (@($adjudication.cases | Where-Object ruling -eq $ruling).Count -ne $adjudication.counts.$ruling) { $issues += 'COUNT: ' + $ruling }
}
if ($adjudication.reviewer.human_confirmed -or $adjudication.reviewer.blind_review) { $issues += 'REVIEWER_IDENTITY' }
foreach ($case in $adjudication.cases) {
    $task = $draft.tasks | Where-Object task_id -eq $case.task_id
    foreach ($anchor in $case.anchors) {
        $candidate = $task.actor_view.candidates | Where-Object candidate_id -eq $anchor.candidate_id
        if (!$candidate -or !$candidate.text.Contains($anchor.quote)) { $issues += 'ANCHOR: ' + $case.task_id + '/' + $anchor.candidate_id }
        $anchorCount++
    }
    foreach ($minimalSet in $case.minimal_sufficient_sets) {
        foreach ($candidateId in $minimalSet) {
            if ($task.actor_view.candidates.candidate_id -notcontains $candidateId) { $issues += 'CANDIDATE_ID: ' + $case.task_id + '/' + $candidateId }
        }
        if (@($minimalSet | Select-Object -Unique).Count -ne @($minimalSet).Count) { $issues += 'DUPLICATE_MINIMAL_SET_ID: ' + $case.task_id }
    }
    if ($case.ruling -eq 'KEEP_DEVELOPMENT' -and @($case.minimal_sufficient_sets).Count -eq 0) { $issues += 'MISSING_MINIMAL_SET: ' + $case.task_id }
    if ($case.ruling -ne 'KEEP_DEVELOPMENT' -and @($case.minimal_sufficient_sets).Count -gt 0) { $issues += 'ACCIDENTAL_REPAIR_ADMISSION: ' + $case.task_id }
}
$retainedAuto = @($adjudication.cases | Where-Object { $_.ruling -eq 'KEEP_DEVELOPMENT' -and $_.task_id.StartsWith('ESD_') } | ForEach-Object task_id)
$retainedEnergy = @($adjudication.cases | Where-Object { $_.ruling -eq 'KEEP_DEVELOPMENT' -and $_.task_id.StartsWith('ESH_') } | ForEach-Object task_id)
if ($retainedAuto.Count -ne 7 -or $retainedEnergy.Count -ne 6) { $issues += 'SPLIT_COUNT' }
if (@(Compare-Object $retainedAuto @($adjudication.qualified_development_ids)).Count) { $issues += 'AUTO_LIST' }
if (@(Compare-Object $retainedEnergy @($adjudication.qualified_future_development_ids)).Count) { $issues += 'ENERGY_LIST' }
$grossCase = $adjudication.cases | Where-Object task_id -eq 'ESD_006'
$grossProfit = 171606 - 151065
$grossMargin = $grossProfit / 171606 * 100
if ($grossCase.canonical_answer.derived_gross_profit -ne $grossProfit -or [Math]::Abs($grossCase.canonical_answer.derived_gross_margin_percent - $grossMargin) -gt 0.01) { $issues += 'GROSS_PROFIT_ARITHMETIC' }
$teslaCase = $adjudication.cases | Where-Object task_id -eq 'ESD_010'
if (@($teslaCase.minimal_sufficient_sets).Count -ne 1 -or @($teslaCase.minimal_sufficient_sets[0]).Count -ne 1 -or $teslaCase.minimal_sufficient_sets[0][0] -ne 'cand_003') { $issues += 'TESLA_SUFFICIENT_SUBSET' }
foreach ($file in Get-ChildItem -LiteralPath $PSScriptRoot -File | Where-Object { $_.Extension -in @('.md', '.json', '.ps1') }) {
    foreach ($line in Get-Content -LiteralPath $file.FullName) {
        if ($line -match '[ \t]+$' -or $line -match '^(<<<<<<<|=======|>>>>>>>)') { $issues += 'WHITESPACE_OR_CONFLICT: ' + $file.Name; break }
    }
}
$result = [ordered]@{
    schema = 'finrank_ai_adjudication_verification_v1'
    verification_environment = 'LOCAL_WINDOWS_POWERSHELL; artifact checks only, not GB10 runtime or semantic proof'
    issues = @($issues)
    cases = $taskIds.Count
    counts = $adjudication.counts
    anchors_checked = $anchorCount
    protected_input_files_unchanged = @($adjudication.source_inputs).Count
    development_tasks = $retainedAuto.Count
    future_development_tasks = $retainedEnergy.Count
    arithmetic = [ordered]@{
        gm_gross_profit = $grossProfit
        gm_gross_margin_percent = [Math]::Round($grossMargin, 6)
        roa_parent_income_percent = [Math]::Round(6008 / ((279761 + 273064) / 2) * 100, 6)
        roa_consolidated_income_percent = [Math]::Round(5963 / ((279761 + 273064) / 2) * 100, 6)
        tesla_cash_debt_ratio = [Math]::Round(14923 / 7907, 6)
        tesla_cash_interest_ratio = [Math]::Round(14923 / 277, 6)
        ctra_days = [Math]::Round(577 / (2800 / 1000), 6)
    }
    verification_limit = 'Checks traceability, input preservation, IDs and arithmetic; does not independently prove semantic uniqueness, task difficulty, tool implementation, memory gain or publication readiness.'
}
$result | ConvertTo-Json -Depth 8
if ($issues.Count) { exit 1 }
