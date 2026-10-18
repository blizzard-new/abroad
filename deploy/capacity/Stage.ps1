# Isolated capacity stack. Windows PowerShell 5.1+, Docker Desktop. No production script is sourced.
param(
    [ValidateSet('Setup','Test','Status','Stop')][string]$Action = 'Status',
    [ValidateSet(1,2,4)][int]$Workers = 1,
    [ValidateRange(2,2000)][int]$Users = 100,
    [ValidateRange(60,7200)][int]$Seconds = 300
)
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$StageRoot = $PSScriptRoot
$RepoRoot = Split-Path -Parent (Split-Path -Parent $StageRoot)
$EnvPath = Join-Path $StageRoot '.env'
$Artifacts = Join-Path $StageRoot 'artifacts'
$Utf8 = New-Object System.Text.UTF8Encoding($false)
function Check([string]$What) { if ($LASTEXITCODE -ne 0) { throw "$What failed (exit $LASTEXITCODE)" } }
function Compose {
    & docker compose --project-name uniway-capacity --project-directory $StageRoot --env-file $EnvPath -f (Join-Path $StageRoot 'compose.yml') @args
    Check 'capacity compose'
}
function Hex([int]$Count) {
    $bytes = New-Object byte[] $Count
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return (($bytes | ForEach-Object { $_.ToString('x2') }) -join '')
}
function B64([byte[]]$Bytes) { return [Convert]::ToBase64String($Bytes).TrimEnd('=').Replace('+','-').Replace('/','_') }
function Key {
    $raw = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($raw) } finally { $rng.Dispose() }
    return (B64 $raw)
}
function Jwt([string]$Secret, [string]$Role) {
    $enc = [Text.Encoding]::UTF8
    $header = B64 ($enc.GetBytes('{"alg":"HS256","typ":"JWT"}'))
    $expiry = [DateTimeOffset]::UtcNow.AddYears(10).ToUnixTimeSeconds()
    $payload = B64 ($enc.GetBytes(('{"role":"'+$Role+'","iss":"supabase","exp":'+$expiry+'}')))
    $mac = New-Object Security.Cryptography.HMACSHA256 (,$enc.GetBytes($Secret))
    try { $sig = B64 ($mac.ComputeHash($enc.GetBytes($header+'.'+$payload))) } finally { $mac.Dispose() }
    return ($header+'.'+$payload+'.'+$sig)
}
function Db([string]$Sql) {
    Assert-Db
    $lines = Compose exec -T db psql -U supabase_admin -d postgres -X -A -t -v ON_ERROR_STOP=1 -c $Sql
    return ($lines -join "`n").Trim()
}
function Assert-Db {
    $id = (Compose ps -q db).Trim()
    if (-not $id) { throw 'Capacity database is not running' }
    $project = & docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}' $id
    Check 'database project check'
    if ($project -ne 'uniway-capacity') { throw 'Refusing a foreign database' }
}
function Wait-App {
    $deadline = (Get-Date).AddMinutes(5)
    do {
        try {
            $identity = Invoke-RestMethod 'http://127.0.0.1:18000/capacity/identity' -TimeoutSec 5
            if ($identity.run_id -eq $env:CAPACITY_RUN_ID) { return }
            throw 'Capacity identity mismatch'
        } catch { if ((Get-Date) -gt $deadline) { throw }; Start-Sleep -Seconds 2 }
    } while ($true)
}
if ($Action -eq 'Setup' -and -not (Test-Path $EnvPath)) {
    $jwt = Hex 32
    $settings = [ordered]@{
        CAPACITY_RUN_ID=(Hex 16); DB_PASSWORD=(Hex 24); JWT_SECRET=$jwt
        ANON_KEY=(Jwt $jwt 'anon'); SERVICE_ROLE_KEY=(Jwt $jwt 'service_role')
        VAULT_MASTER_KEY=(Key); EMAIL_VERIFICATION_SECRET=(Key)
    }
    [IO.File]::WriteAllText($EnvPath, (($settings.GetEnumerator() | ForEach-Object { $_.Key+'='+$_.Value }) -join "`n")+"`n", $Utf8)
}
if (-not (Test-Path $EnvPath)) { throw 'Run Stage.ps1 -Action Setup first' }
New-Item -ItemType Directory -Force $Artifacts | Out-Null
# The environment file and fixture directory contain test credentials. Restrict access before seeding.
& icacls $EnvPath /inheritance:r /grant:r ("{0}:F" -f $env:USERNAME) 'SYSTEM:F' 'Administrators:F' | Out-Null
Check 'settings ACL'
& icacls $Artifacts /inheritance:r /grant:r ("{0}:(OI)(CI)F" -f $env:USERNAME) 'SYSTEM:(OI)(CI)F' 'Administrators:(OI)(CI)F' | Out-Null
Check 'fixture ACL'
# Pin generated values even when the caller has similarly named production environment variables.
foreach ($line in [IO.File]::ReadAllLines($EnvPath)) {
    if ($line -match '^([A-Z_]+)=(.*)$') { [Environment]::SetEnvironmentVariable($Matches[1],$Matches[2],'Process') }
}
if ($env:CAPACITY_RUN_ID -notmatch '^[0-9a-f]{32}$' -or $env:DB_PASSWORD -notmatch '^[0-9a-f]{48}$') { throw 'Invalid capacity settings' }
$env:CAPACITY_WORKERS = "$Workers"
$env:CAPACITY_USERS = "$Users"
$env:CAPACITY_SECONDS = "$Seconds"
$env:CAPACITY_THREADS = '16'
$env:CAPACITY_CATALOGUES = '2'
$config = (Compose config --format json) | ConvertFrom-Json
if ($config.name -ne 'uniway-capacity') { throw 'Wrong compose project' }
foreach ($volume in $config.volumes.PSObject.Properties) {
    if ($volume.Value.name -notlike 'uniway-capacity_*') { throw 'Refusing a shared volume' }
}
foreach ($service in $config.services.PSObject.Properties) {
    if ($service.Value.PSObject.Properties.Name -contains 'ports') {
        foreach ($port in $service.Value.ports) {
            if ($port.host_ip -ne '127.0.0.1' -or $port.published -ne '18000') { throw 'Refusing a public or production port' }
        }
    }
}
if ($Action -eq 'Stop') { Compose stop; exit }
if ($Action -eq 'Status') { Compose ps; exit }
if ($Action -eq 'Setup') {
    Compose build app
    Compose up -d --wait db
    $null = Db ("alter role authenticator with login password '"+$env:DB_PASSWORD+"'; alter role supabase_storage_admin with login password '"+$env:DB_PASSWORD+"';")
    $null = Db 'create table if not exists public.uniway_schema_migrations (name text primary key, applied_at timestamptz not null default now())'
    $applied = (Db 'select name from public.uniway_schema_migrations') -split "`n"
    # Preserve Chinese and normalize CRLF without passing SQL through PowerShell's native stdin encoding.
    $tempDir = Join-Path ([IO.Path]::GetTempPath()) ('uniway-capacity-'+[Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory $tempDir | Out-Null
    try {
        foreach ($file in (Get-ChildItem (Join-Path $RepoRoot 'supabase\migrations') -Filter '*.sql' | Sort-Object Name)) {
            if ($applied -contains $file.Name) { continue }
            $tempFile = Join-Path $tempDir $file.Name
            [IO.File]::WriteAllText($tempFile, [IO.File]::ReadAllText($file.FullName,$Utf8).Replace("`r`n","`n"),$Utf8)
            Assert-Db
            Compose cp $tempFile 'db:/tmp/capacity-migration.sql'
            Compose exec -T -e PGCLIENTENCODING=UTF8 db psql -U postgres -d postgres -X -q -v ON_ERROR_STOP=1 -f /tmp/capacity-migration.sql
            $null = Db ("insert into public.uniway_schema_migrations(name) values ('"+$file.Name+"')")
        }
    } finally { Remove-Item -Recurse -Force $tempDir }
    Compose up -d --wait rest storage gateway
    Compose up -d ca-export app web
    Wait-App
    Compose exec -T app python /opt/selfhost/create_bucket.py
    # Bucket helper has a dedicated read-only mount (see compose.yml).
    Compose run --rm --no-deps seed
    Write-Host 'Isolated stack ready: http://127.0.0.1:18000. Production was not updated.'
    exit
}
# Test always rotates fixture sessions and recreates only the staging app with the requested workers.
Compose up -d --no-deps --force-recreate app
Wait-App
Compose run --rm --no-deps seed
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$report = '/artifacts/'+$stamp+'-w'+$Workers+'-u'+$Users+'.json'
Compose run --rm --no-deps load python /opt/capacity/load.py --users $Users --duration $Seconds --expect-workers $Workers --output $report
Compose stats --no-stream
Write-Host ('Report: '+$Artifacts+'\'+($report.Split('/')[-1]))
