# Run in a separate clone. Builds and starts ONLY the CGU demo container.
# Plain ASCII for Windows PowerShell 5.1.
param([switch]$SkipBuild, [ValidateRange(1024,65535)][int]$Port = 8765)
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
if ($Port -eq 8000) { throw 'Port 8000 belongs to the main site. Use 8765 or another unused port.' }
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$compose = @('compose', '-p', 'uniway-cgu-demo', '--project-directory', $PSScriptRoot,
    '--env-file', (Join-Path $PSScriptRoot 'demo.env.example'), '-f', (Join-Path $PSScriptRoot 'compose.yml'))
function Check-Exit([string]$Step) { if ($LASTEXITCODE -ne 0) { throw ($Step + ' failed.') } }
$sourceChanges = & git -C $repo status --porcelain --untracked-files=all -- src deploy/cgu-demo scripts/harden_image_ca.py .dockerignore README.md pyproject.toml uv.lock
Check-Exit 'Source status'
if ($sourceChanges) { throw 'Commit or set aside source edits and untracked build inputs before building a fixed version.' }
$revision = & git -C $repo rev-parse HEAD
Check-Exit 'git rev-parse'
$revision = $revision.Trim()
$osType = & docker info --format '{{.OSType}}'
Check-Exit 'Docker Desktop (start Docker Desktop first)'
if ($osType.Trim() -ne 'linux') { throw 'Switch Docker Desktop to Linux containers.' }
& docker compose version
Check-Exit 'Docker Compose'
$old = @{}
foreach ($key in @('CGU_DEMO_IMAGE','CGU_DEMO_REVISION','CGU_DEMO_PORT')) {
    $old[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
}
try {
    $env:CGU_DEMO_REVISION = $revision
    $env:CGU_DEMO_IMAGE = 'uniway-cgu-demo:' + $revision.Substring(0,12)
    $env:CGU_DEMO_PORT = [string]$Port
    $container = & docker @compose ps -q demo
    Check-Exit 'Read demo container status'
    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($listener) {
        $binding = if ($container) { (& docker port $container 8000/tcp) -join '' } else { '' }
        if ($binding -ne ('127.0.0.1:' + $Port)) { throw ('Port ' + $Port + ' is in use by another process.') }
    }
    & docker @compose config --quiet
    Check-Exit 'Demo configuration'
    if (-not $SkipBuild) {
        Write-Host ('Building isolated CGU image at ' + $revision)
        & docker @compose build demo
        Check-Exit 'Demo image build'
    }
    & docker @compose up -d --no-deps --no-build demo
    Check-Exit 'Start demo'
    $ready = $false
    for ($i = 0; $i -lt 120; $i++) {
        try {
            $health = Invoke-RestMethod -Uri ('http://127.0.0.1:' + $Port + '/health') -TimeoutSec 3
            if ($health.mode -eq 'cgu-demo' -and $health.revision -eq $revision) { $ready = $true; break }
        } catch { }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { throw 'Demo did not become ready. Inspect only the uniway-cgu-demo container logs.' }
    & docker @compose exec -T demo python /opt/demo-verify.py --url http://127.0.0.1:8000 --proxy-check
    Check-Exit 'Demo isolation and persistence smoke test'
    Write-Host ('CGU demo is ready on loopback port ' + $Port + '. Main site and database were not restarted.')
    Write-Host 'Next: prepare the Caddy candidate with publish-windows.ps1 (no -Apply yet).'
    Write-Host 'A demo container restart clears its synthetic workspaces. No automatic Git updates are configured.'
} finally {
    foreach ($key in $old.Keys) { [Environment]::SetEnvironmentVariable($key, $old[$key], 'Process') }
}
