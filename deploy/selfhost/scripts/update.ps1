# Update to the newest code from GitHub, or go back to the previous version.
#   powershell -ExecutionPolicy Bypass -File .\update.ps1            (update)
#   powershell -ExecutionPolicy Bypass -File .\update.ps1 -Rollback  (undo the last update)
param([switch]$Rollback, [string]$Branch = '')   # default: the branch this folder is on
. "$PSScriptRoot\lib.ps1"

if ($Rollback) {
    Write-Step 'Going back to the previous program image'
    $prev = (& docker images -q uniway-app:prev 2>$null)
    if (-not $prev) { throw 'there is no previous image (uniway-app:prev) to go back to' }
    & docker tag uniway-app:prev uniway-app:local
    Invoke-Compose up -d --no-build app
    Assert-ExitCode 'docker compose up'
    Wait-Healthy 'app' 600
    Write-Host 'Rolled back. (The database was not touched; if the update changed it, restore a backup: see the guide.)' -ForegroundColor Yellow
    exit 0
}

Write-Step 'Taking a backup first'
& "$PSScriptRoot\backup.ps1" -SkipCloud
if ($LASTEXITCODE -ne 0) { throw 'backup failed - not updating' }

if (-not $Branch) { $Branch = (& git -C $script:RepoRoot rev-parse --abbrev-ref HEAD).Trim() }
Write-Step ("Fetching {0}" -f $Branch)
Push-Location $script:RepoRoot
try {
    & git fetch origin $Branch
    Assert-ExitCode 'git fetch'
    & git merge --ff-only ('origin/' + $Branch)
    Assert-ExitCode 'git merge (local changes in the way? ask whoever set this up)'
} finally { Pop-Location }

& "$PSScriptRoot\03-start.ps1"
& "$PSScriptRoot\verify.ps1"
