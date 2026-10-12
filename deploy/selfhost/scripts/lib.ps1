# Shared helpers for the self-hosting scripts. Dot-source it: . "$PSScriptRoot\lib.ps1"
# Plain ASCII on purpose: Windows PowerShell 5.1 reads scripts without a BOM in the system code page.
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$script:ScriptsDir = $PSScriptRoot
$script:DeployDir  = Split-Path -Parent $PSScriptRoot                         # deploy\selfhost
$script:RepoRoot   = Split-Path -Parent (Split-Path -Parent $script:DeployDir)
$script:EnvFile    = Join-Path $script:DeployDir '.env'
$script:ComposeFile = Join-Path $script:DeployDir 'docker-compose.yml'
$script:UniwayHome = 'C:\uniway'                                               # logs, backups, caddy

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
