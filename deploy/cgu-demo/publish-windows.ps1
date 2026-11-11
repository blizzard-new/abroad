# Default: validate a candidate only. -Apply explicitly installs it and restarts
# the shared Caddy HTTPS entrypoint, with rollback on failed health checks.
# Never calls the production Docker Compose stack or reads its .env.
param(
    [switch]$Apply,
    [string]$CaddyFile = 'C:\uniway\caddy\Caddyfile',
    [string]$CaddyExe = '',
    [ValidateRange(1024,65535)][int]$Port = 8765
)
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
if ($Port -eq 8000) { throw 'Do not route the demo to the main application port.' }
$CaddyFile = (Resolve-Path $CaddyFile).Path
if (-not $CaddyExe) { $CaddyExe = Join-Path (Split-Path -Parent $CaddyFile) 'caddy.exe' }
if (-not (Test-Path $CaddyExe)) { throw 'Caddy was not found. This script expects the existing Docker Desktop + Caddy setup.' }
$demo = Invoke-RestMethod -Uri ('http://127.0.0.1:' + $Port + '/health') -TimeoutSec 10
if ($demo.mode -ne 'cgu-demo') { throw 'The selected port is not a CGU demo. Nothing changed.' }
$originalHash = (Get-FileHash -Algorithm SHA256 $CaddyFile).Hash
$original = [IO.File]::ReadAllText($CaddyFile)
if ($original -match '(?i)demo\.uniway-tw\.com') { throw 'Caddy already mentions the demo domain; review the existing entry instead of adding a duplicate.' }
$candidate = $CaddyFile + '.cgu-demo.candidate'
$block = @"

# UniWay CGU demo: isolated process, no connection to the main data services.
demo.uniway-tw.com {
    encode zstd gzip
    request_body {
        max_size 256KB
    }
    reverse_proxy 127.0.0.1:$Port
}
"@
$prepared = $original + "`r`n" + $block + "`r`n"
if (Test-Path $candidate) {
    if ([IO.File]::ReadAllText($candidate) -ne $prepared) { throw 'An edited or stale candidate already exists. Preserve it and review before preparing another.' }
} else {
    [IO.File]::WriteAllText($candidate, $prepared, (New-Object Text.UTF8Encoding($false)))
}
$candidateHash = (Get-FileHash -Algorithm SHA256 $candidate).Hash
& $CaddyExe validate --config $candidate --adapter caddyfile
if ($LASTEXITCODE -ne 0) { throw 'Candidate failed Caddy validation. The live configuration is unchanged.' }
if (-not $Apply) {
    Write-Host ('Validated candidate: ' + $candidate)
    Write-Host 'Live proxy unchanged. Add the demo DNS record, then review the candidate.'
    Write-Host 'Run this script with -Apply in an elevated PowerShell to publish.'
    Write-Host 'Applying briefly restarts the shared HTTPS entrypoint; the main app/database are not restarted.'
    return
}
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw '-Apply requires an elevated PowerShell.' }
$task = Get-ScheduledTask -TaskName 'UniWay-Caddy' -ErrorAction Stop
$arguments = ($task.Actions.Arguments -join ' ')
if ($arguments.IndexOf($CaddyFile, [StringComparison]::OrdinalIgnoreCase) -lt 0) { throw 'UniWay-Caddy uses a different config; no live changes made.' }
$null = [Net.Dns]::GetHostAddresses('demo.uniway-tw.com')
$main = Invoke-RestMethod -Uri 'https://app.uniway-tw.com/health' -TimeoutSec 20
if ($main.status -ne 'ok') { throw 'Main site is not healthy before publication; no live changes made.' }
if ((Get-FileHash -Algorithm SHA256 $CaddyFile).Hash -ne $originalHash) { throw 'Live Caddyfile changed during review; rerun preparation.' }
if ((Get-FileHash -Algorithm SHA256 $candidate).Hash -ne $candidateHash) { throw 'Candidate changed during validation; no live changes made.' }
$backup = $CaddyFile + '.before-cgu-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff')
Copy-Item -LiteralPath $CaddyFile -Destination $backup
try {
    Copy-Item -LiteralPath $candidate -Destination $CaddyFile -Force
    Stop-ScheduledTask -TaskName 'UniWay-Caddy'
    Start-Sleep -Seconds 2
    Start-ScheduledTask -TaskName 'UniWay-Caddy'
    $healthy = $false
    for ($i = 0; $i -lt 40; $i++) {
        try {
            $liveDemo = Invoke-RestMethod -Uri 'https://demo.uniway-tw.com/health' -TimeoutSec 5
            $liveMain = Invoke-RestMethod -Uri 'https://app.uniway-tw.com/health' -TimeoutSec 5
            if ($liveDemo.mode -eq 'cgu-demo' -and $liveDemo.revision -eq $demo.revision -and $liveMain.status -eq 'ok') {
                $healthy = $true; break
            }
        } catch { }
        Start-Sleep -Seconds 3
    }
    if (-not $healthy) { throw 'Public demo or main health check failed; restoring the previous proxy config.' }
    Write-Host ('HTTPS health checks passed. Backup: ' + $backup)
    Write-Host 'Open https://demo.uniway-tw.com and verify the full journey before the event.'
} catch {
    if ((Get-FileHash -Algorithm SHA256 $CaddyFile).Hash -ne $candidateHash) {
        throw ('Caddyfile was edited concurrently. Refusing to overwrite those changes. Prior config: ' + $backup)
    }
    Copy-Item -LiteralPath $backup -Destination $CaddyFile -Force
    Stop-ScheduledTask -TaskName 'UniWay-Caddy'
    Start-Sleep -Seconds 2
    Start-ScheduledTask -TaskName 'UniWay-Caddy'
    throw
}
