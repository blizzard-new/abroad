# Shared helpers for the self-hosting scripts. Dot-source it: . "$PSScriptRoot\lib.ps1"
# Plain ASCII on purpose: Windows PowerShell 5.1 reads scripts without a BOM in the system code page.
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$script:ScriptsDir = $PSScriptRoot
$script:DeployDir  = Split-Path -Parent $PSScriptRoot                         # deploy\selfhost
$script:RepoRoot   = Split-Path -Parent (Split-Path -Parent $script:DeployDir)
$script:EnvFile    = Join-Path $script:DeployDir '.env'
$script:ComposeFile = Join-Path $script:DeployDir 'docker-compose.yml'
$script:UniwayHome = if ($env:UNIWAY_HOME) { $env:UNIWAY_HOME } else { 'C:\uniway' }   # logs, backups, caddy

function Write-Step([string]$Message) { Write-Host ""; Write-Host ("==> " + $Message) -ForegroundColor Cyan }
function Write-Ok([string]$Message)   { Write-Host ("  [ OK ] " + $Message) -ForegroundColor Green }
function Write-Warn([string]$Message) { Write-Host ("  [WARN] " + $Message) -ForegroundColor Yellow }
function Write-Bad([string]$Message)  { Write-Host ("  [FAIL] " + $Message) -ForegroundColor Red }

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    return ([Security.Principal.WindowsPrincipal]$id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Assert-Admin {
    if (-not (Test-Admin)) { throw 'This step needs an elevated PowerShell: right-click PowerShell -> Run as administrator.' }
}

function Assert-ExitCode([string]$What) {
    if ($LASTEXITCODE -ne 0) { throw ("{0} failed (exit code {1})." -f $What, $LASTEXITCODE) }
}

# ---- the settings file (.env) ---------------------------------------------------------------------------------------
function Read-EnvFile {
    $map = [ordered]@{}
    if (-not (Test-Path $script:EnvFile)) { return $map }
    foreach ($line in [System.IO.File]::ReadAllLines($script:EnvFile)) {
        $t = $line.Trim()
        if ($t -eq '' -or $t.StartsWith('#')) { continue }
        $i = $t.IndexOf('=')
        if ($i -lt 1) { continue }
        $map[$t.Substring(0, $i).Trim()] = $t.Substring($i + 1).Trim()
    }
    return $map
}
function Write-EnvFile($Map) {
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add('# Written by scripts/02-generate-secrets.ps1. SECRET: never commit, never paste into chat.')
    foreach ($k in $Map.Keys) { $lines.Add(('{0}={1}' -f $k, $Map[$k])) }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($script:EnvFile, (($lines -join "`r`n") + "`r`n"), $utf8)
    # only the owner, administrators and the system may read it
    & icacls $script:EnvFile /inheritance:r /grant:r ("{0}:(F)" -f $env:USERNAME) 'SYSTEM:(F)' 'Administrators:(F)' | Out-Null
}

# ---- random values and the two Supabase-style keys ------------------------------------------------------------------
function New-RandomBytes([int]$Count) {
    $bytes = New-Object byte[] $Count
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $rng.Dispose()
    return ,$bytes
}
function ConvertTo-Base64Url([byte[]]$Bytes) {
    return [Convert]::ToBase64String($Bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
}
function New-RandomHex([int]$ByteCount) {
    return ((New-RandomBytes $ByteCount) | ForEach-Object { $_.ToString('x2') }) -join ''
}
function New-SupabaseJwt([string]$Secret, [string]$Role, [int]$Years = 10) {
    $iat = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $exp = [DateTimeOffset]::UtcNow.AddYears($Years).ToUnixTimeSeconds()
    $enc = [System.Text.Encoding]::UTF8
    $header  = ConvertTo-Base64Url ($enc.GetBytes('{"alg":"HS256","typ":"JWT"}'))
    $payload = ConvertTo-Base64Url ($enc.GetBytes(('{{"role":"{0}","iss":"supabase","iat":{1},"exp":{2}}}' -f $Role, $iat, $exp)))
    $hmac = New-Object System.Security.Cryptography.HMACSHA256 (,$enc.GetBytes($Secret))
    $sig = ConvertTo-Base64Url ($hmac.ComputeHash($enc.GetBytes($header + '.' + $payload)))
    $hmac.Dispose()
    return ($header + '.' + $payload + '.' + $sig)
}

function Invoke-Quiet([scriptblock]$Command) {
    # Run a native command whose error output (for example "No such container") is expected and unimportant.
    # Under $ErrorActionPreference = 'Stop', Windows PowerShell 5.1 would turn that output into a terminating error.
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $Command 2>&1 | Out-Null } finally { $ErrorActionPreference = $old }
}

# ---- docker compose --------------------------------------------------------------------------------------------------
function Invoke-Compose {
    # usage: Invoke-Compose up -d db
    & docker compose --project-directory $script:DeployDir -f $script:ComposeFile @args
}
function Get-ContainerId([string]$Service) {
    $id = (& docker compose --project-directory $script:DeployDir -f $script:ComposeFile ps -q $Service 2>$null)
    if ($id) { return ($id | Select-Object -First 1).Trim() }
    return $null
}
function Wait-Healthy([string]$Service, [int]$TimeoutSeconds = 300) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $id = Get-ContainerId $Service
        if ($id) {
            $state = (& docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $id 2>$null)
            if ($state -eq 'healthy' -or $state -eq 'running') { Write-Ok ("{0} is {1}" -f $Service, $state); return }
            if ($state -eq 'exited' -or $state -eq 'dead') { throw ("{0} stopped: run 'docker compose logs {0}' in deploy\selfhost" -f $Service) }
        }
        Start-Sleep -Seconds 3
    }
    throw ("{0} did not become healthy within {1} seconds" -f $Service, $TimeoutSeconds)
}

function Invoke-DbPsql([string]$Sql, [string]$User = 'postgres') {
    # ASCII SQL only (PowerShell 5.1 turns other characters into question marks on the way to a program).
    # Use -User supabase_admin for the few statements on reserved roles (the image's real superuser).
    $out = & docker compose --project-directory $script:DeployDir -f $script:ComposeFile exec -T db psql -U $User -d postgres -X -A -t -v ON_ERROR_STOP=1 -c $Sql
    Assert-ExitCode 'psql'
    return ($out -join "`n").Trim()
}

function Get-PublicBaseUrl {
    $e = Read-EnvFile
    if (-not $e.Contains('DOMAIN')) { throw '.env has no DOMAIN yet: run 02-generate-secrets.ps1' }
    return ('https://' + $e['DOMAIN'])
}

# ---- update preflight: what would stop "git merge --ff-only" ------------------------------------------------------------
# update.ps1 only fast-forwards, so git refuses when this folder has (a) edits to files the update also changes, or (b) files
# git does not track that the update wants to add. These helpers find those files, change nothing on their own, and can set
# them aside in a backup folder. File names are read as UTF-8 and never quoted, so names with spaces or Chinese characters
# are found exactly as they are on disk.

function Invoke-GitLines([string]$RepoRoot, [string[]]$GitArgs) {
    # Runs git in $RepoRoot and returns its output lines. Throws if git fails.
    $saved = $null
    try { $saved = [Console]::OutputEncoding; [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch { $saved = $null }
    $code = 0
    try {
        $lines = @(& git -C $RepoRoot -c core.quotepath=false @GitArgs)
        $code = $LASTEXITCODE
    } finally {
        if ($saved) { try { [Console]::OutputEncoding = $saved } catch { } }
    }
    if ($code -ne 0) { throw ("git {0} failed (exit code {1})." -f ($GitArgs -join ' '), $code) }
    return @($lines | Where-Object { $_ -ne '' })
}

function Invoke-GitOnPaths([string]$RepoRoot, [string[]]$GitArgs, [string[]]$Paths) {
    # Runs "git <GitArgs> -- <paths>". Plain ASCII paths go on the command line in small batches. A path with other
    # characters is handed over in a file instead, because Windows PowerShell 5.1 can garble such characters on the way to
    # a program. Paths are taken literally: a name like "a[1].json" is not a pattern.
    $ascii = @($Paths | Where-Object { $_ -cmatch '^[\x20-\x7E]+$' })
    $other = @($Paths | Where-Object { $_ -cnotmatch '^[\x20-\x7E]+$' })
    for ($i = 0; $i -lt $ascii.Count; $i += 40) {
        $last = [Math]::Min($i + 40, $ascii.Count) - 1
        $batch = @($ascii[$i..$last])
        & git -C $RepoRoot --literal-pathspecs @GitArgs -- @batch
        Assert-ExitCode ('git ' + ($GitArgs -join ' '))
    }
    if ($other.Count -gt 0) {
        $list = [System.IO.Path]::GetTempFileName()
        try {
            [System.IO.File]::WriteAllText($list, (($other -join [string][char]0) + [string][char]0), (New-Object System.Text.UTF8Encoding($false)))
            & git -C $RepoRoot --literal-pathspecs @GitArgs ('--pathspec-from-file=' + $list) --pathspec-file-nul
            Assert-ExitCode ('git ' + ($GitArgs -join ' ') + ' with a path list (needs git 2.25 or newer)')
        } finally { Remove-Item -LiteralPath $list -Force -ErrorAction SilentlyContinue }
    }
}

function Get-UpdateBlockers([string]$RepoRoot, [string]$Branch) {
    # Looks only; changes nothing. Run "git fetch origin <Branch>" first so origin/<Branch> is current.
    $remote = 'origin/' + $Branch
    $current = (@(Invoke-GitLines $RepoRoot @('rev-parse', '--abbrev-ref', 'HEAD')))[0]
    $info = [pscustomobject]@{
        Branch            = $Branch
        Current           = $current
        WrongBranch       = ($current -ne $Branch)
        Diverged          = $false
        LocalCommits      = @()
        TrackedBlockers   = @()
        TrackedKept       = @()
        UntrackedBlockers = @()
        StagedBlockers    = @()
        IncomingFiles     = 0
    }
    if ($info.WrongBranch) { return $info }

    & git -C $RepoRoot merge-base --is-ancestor HEAD $remote
    $ancestorCode = $LASTEXITCODE
    if ($ancestorCode -eq 1) {
        $info.Diverged = $true
        $info.LocalCommits = @(Invoke-GitLines $RepoRoot @('log', '--oneline', '-n', '10', ($remote + '..HEAD')))
        return $info
    }
    if ($ancestorCode -ne 0) { throw ("git could not compare HEAD with {0} (exit code {1}). Run 'git fetch origin {2}' first." -f $remote, $ancestorCode, $Branch) }

    $changed = @(Invoke-GitLines $RepoRoot @('diff', '--name-only', '--no-renames', 'HEAD', $remote))
    $added   = @(Invoke-GitLines $RepoRoot @('diff', '--name-only', '--no-renames', '--diff-filter=A', 'HEAD', $remote))
    $local   = @(Invoke-GitLines $RepoRoot @('diff', '--name-only', '--no-renames', 'HEAD'))
    $staged  = @(Invoke-GitLines $RepoRoot @('diff', '--cached', '--name-only', '--no-renames', '--diff-filter=A', 'HEAD'))
    $info.IncomingFiles = $changed.Count

    # (a) files in HEAD that the update changes and this folder has also edited (or deleted)
    $changedExisting = @($changed | Where-Object { $added -notcontains $_ })
    $info.TrackedBlockers = @($local | Where-Object { $changedExisting -contains $_ })
    $info.TrackedKept = @($local | Where-Object { $changed -notcontains $_ })
    # (b) files the update adds that already exist here (untracked), or that are staged but not committed
    foreach ($path in $added) {
        if ($staged -contains $path) { $info.StagedBlockers += $path; continue }
        if (Test-Path -LiteralPath (Join-Path $RepoRoot $path)) { $info.UntrackedBlockers += $path }
    }
    return $info
}

function Test-UpdateBlocked($Info) {
    return ($Info.WrongBranch -or $Info.Diverged -or (@($Info.TrackedBlockers).Count -gt 0) -or (@($Info.UntrackedBlockers).Count -gt 0) -or (@($Info.StagedBlockers).Count -gt 0))
}

function Test-UpdateCanSetAside($Info) {
    # Only edits and untracked files can be set aside automatically.
    return (-not ($Info.WrongBranch -or $Info.Diverged -or (@($Info.StagedBlockers).Count -gt 0)))
}

function Write-PathList([string[]]$Paths, [int]$Max = 12) {
    $all = @($Paths)
    for ($i = 0; $i -lt $all.Count; $i++) {
        if ($i -ge $Max) { Write-Host ("         ... and {0} more" -f ($all.Count - $Max)); break }
        Write-Host ("         " + $all[$i])
    }
}

function Write-UpdateReport($Info) {
    if ($Info.WrongBranch) {
        Write-Bad ("this folder is on branch '{0}', but the update is for '{1}'" -f $Info.Current, $Info.Branch)
        Write-Host ("         fix: run  git switch {0}  and then run update.ps1 again" -f $Info.Branch)
        return
    }
    Write-Ok ("on branch {0}" -f $Info.Current)
    if ($Info.Diverged) {
        Write-Bad ("this folder has commits that are not on origin/{0}, so the update cannot just fast-forward:" -f $Info.Branch)
        Write-PathList @($Info.LocalCommits)
        Write-Host "         fix: ask whoever set this up. Do not reset or delete anything until those commits are saved."
        return
    }
    Write-Ok ("no local commits in the way ({0} file(s) will change)" -f $Info.IncomingFiles)
    $tracked = @($Info.TrackedBlockers)
    if ($tracked.Count -gt 0) {
        Write-Bad ("{0} file(s) the update changes were also edited in this folder:" -f $tracked.Count)
        Write-PathList $tracked
    }
    $untracked = @($Info.UntrackedBlockers)
    if ($untracked.Count -gt 0) {
        Write-Bad ("{0} file(s) the update adds already exist here, and git does not track them:" -f $untracked.Count)
        Write-PathList $untracked
    }
    $staged = @($Info.StagedBlockers)
    if ($staged.Count -gt 0) {
        Write-Bad ("{0} file(s) the update adds are already staged here but not committed:" -f $staged.Count)
        Write-PathList $staged
        Write-Host "         fix: run  git restore --staged <file>  for each of them, then try again"
    }
    if (($tracked.Count + $untracked.Count + $staged.Count) -eq 0) { Write-Ok 'nothing is in the way' }
    $kept = @($Info.TrackedKept)
    if ($kept.Count -gt 0) {
        Write-Ok ("{0} other local change(s) are not in the way and will be left alone:" -f $kept.Count)
        Write-PathList $kept 6
    }
}

function Move-UpdateBlockersAside([string]$RepoRoot, $Info, [string]$BackupDir) {
    # Nothing is deleted. Edited files are copied to <BackupDir>\edited-files and then put back to the committed version.
    # Untracked files are moved to <BackupDir>\untracked-files. Both keep their path inside the program folder.
    $sep = [string][System.IO.Path]::DirectorySeparatorChar
    $editedDir = Join-Path $BackupDir 'edited-files'
    $untrackedDir = Join-Path $BackupDir 'untracked-files'
    New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
    $tracked = @($Info.TrackedBlockers)
    $untracked = @($Info.UntrackedBlockers)
    foreach ($path in $tracked) {
        $source = Join-Path $RepoRoot $path
        if (-not (Test-Path -LiteralPath $source)) { continue }          # deleted here: nothing to copy
        $dest = Join-Path $editedDir ($path.Replace('/', $sep))
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
        Copy-Item -LiteralPath $source -Destination $dest -Force
    }
    foreach ($path in $untracked) {
        $source = Join-Path $RepoRoot $path
        $dest = Join-Path $untrackedDir ($path.Replace('/', $sep))
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
        Move-Item -LiteralPath $source -Destination $dest -Force
    }
    if ($tracked.Count -gt 0) { Invoke-GitOnPaths $RepoRoot @('checkout', 'HEAD') $tracked }
    $head = (@(Invoke-GitLines $RepoRoot @('rev-parse', '--short', 'HEAD')))[0]
    $note = @(
        'These files were in the way of an update of the UniWay program folder.',
        ('Folder: ' + $RepoRoot),
        ('Commit before the update: ' + $head),
        ('Set aside on: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),
        '',
        'edited-files\      your edited copies of files the update changed. The folder now has the new version.',
        'untracked-files\   files that were not in git. The update added its own copies of them.',
        '',
        'To get one back, copy it to the same path inside the program folder. Delete this folder when you no longer need it.'
    ) -join "`r`n"
    [System.IO.File]::WriteAllText((Join-Path $BackupDir 'README.txt'), $note, (New-Object System.Text.UTF8Encoding($false)))
    Write-Ok ("set aside {0} edited and {1} untracked file(s) in {2}" -f $tracked.Count, $untracked.Count, $BackupDir)
}
