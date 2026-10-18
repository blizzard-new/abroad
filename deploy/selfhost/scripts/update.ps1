# Update to the newest code from GitHub, or go back to the previous version.
#   powershell -ExecutionPolicy Bypass -File .\update.ps1                (update)
#   powershell -ExecutionPolicy Bypass -File .\update.ps1 -CheckOnly     (only look: would anything stop the update? changes nothing)
#   powershell -ExecutionPolicy Bypass -File .\update.ps1 -SetAside      (update; first set aside files that are in the way)
#   powershell -ExecutionPolicy Bypass -File .\update.ps1 -Rollback      (undo the last update)
param([switch]$Rollback, [string]$Branch = '', [switch]$SetAside, [switch]$CheckOnly)   # default branch: the one this folder is on
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

if (-not $Branch) { $Branch = (& git -C $script:RepoRoot rev-parse --abbrev-ref HEAD).Trim() }

# Look first, before the backup and before anything is changed: git only fast-forwards, and it stops when this folder has
# edits to files the update changes, or untracked files the update wants to add.
Write-Step ("Checking that this folder can be updated to origin/{0}" -f $Branch)
& git -C $script:RepoRoot fetch origin $Branch
Assert-ExitCode 'git fetch'
$info = Get-UpdateBlockers $script:RepoRoot $Branch
Write-UpdateReport $info
$blocked = Test-UpdateBlocked $info

if ($CheckOnly) {
    if ($blocked) { Write-Host ''; Write-Host 'Check only: nothing was changed. The update would stop for the reasons above.' -ForegroundColor Yellow; exit 1 }
    Write-Host ''; Write-Host 'Check only: nothing is in the way. The update can go ahead.' -ForegroundColor Green
    exit 0
}

if ($blocked) {
    Write-Host ''
    if (-not (Test-UpdateCanSetAside $info)) {
        Write-Host 'This cannot be fixed automatically. Nothing was changed.' -ForegroundColor Yellow
        exit 1
    }
    if (-not $SetAside) {
        Write-Host 'Nothing was changed. To let the updater set the files above aside and carry on, run:' -ForegroundColor Yellow
        Write-Host '    powershell -ExecutionPolicy Bypass -File .\update.ps1 -SetAside'
        Write-Host ('They are copied or moved to ' + (Join-Path $script:UniwayHome 'backups\update-set-aside-<date>') + ' first; nothing is deleted.')
        exit 1
    }
}

Write-Step 'Taking a backup first'
& "$PSScriptRoot\backup.ps1" -SkipCloud
if ($LASTEXITCODE -ne 0) { throw 'backup failed - not updating' }

if ($blocked) {
    Write-Step 'Setting aside the files that are in the way'
    $setAsideDir = Join-Path $script:UniwayHome ('backups\update-set-aside-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    Move-UpdateBlockersAside $script:RepoRoot $info $setAsideDir
}

Write-Step ("Updating to origin/{0}" -f $Branch)
Push-Location $script:RepoRoot
try {
    & git merge --ff-only ('origin/' + $Branch)
    Assert-ExitCode 'git merge'
} finally { Pop-Location }

& "$PSScriptRoot\03-start.ps1"
& "$PSScriptRoot\verify.ps1"
