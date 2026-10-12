# Every five minutes: is the site answering? If the local web service is down, bring the stack back up and say so in the log.
# Also warns (in the log) when the disk is nearly full. Runs as a scheduled task made by 07-setup-backup.ps1.
. "$PSScriptRoot\lib.ps1"
$ErrorActionPreference = 'Continue'
$logFile = Join-Path $script:UniwayHome 'logs\health.log'
New-Item -ItemType Directory -Force -Path (Split-Path $logFile) | Out-Null
function Log([string]$m) {
    Add-Content -Path $logFile -Value ('{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m)
    # keep the log small
    if ((Get-Item $logFile).Length -gt 5MB) { Move-Item -Force $logFile ($logFile + '.old') }
}
function Test-Url([string]$Url) {
    try { return ((Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 15).StatusCode -eq 200) } catch { return $false }
}

if (-not (Test-Url 'http://127.0.0.1:8000/health')) {
    Log 'local web service not answering - trying docker compose up -d'
    $null = & docker info 2>&1
    if ($LASTEXITCODE -ne 0) { Log 'Docker itself is not running (is Docker Desktop started? is the computer logged in?)'; exit 1 }
    Invoke-Compose up -d | Out-Null
    Start-Sleep -Seconds 60
    if (Test-Url 'http://127.0.0.1:8000/health') { Log 'recovered' } else { Log 'STILL DOWN after docker compose up -d: read: docker compose logs app' }
}

$e = Read-EnvFile
if ($e.Contains('DOMAIN') -and $e['DOMAIN'] -ne 'localhost') {
    if (-not (Test-Url ('https://{0}/health' -f $e['DOMAIN']))) { Log ('public address https://{0}/health is not answering (DNS, router forwarding, certificate or Caddy?)' -f $e['DOMAIN']) }
}

$free = [math]::Round((Get-PSDrive C).Free / 1GB)
if ($free -lt 50) { Log ("LOW DISK: only {0} GB free on C:" -f $free) }
