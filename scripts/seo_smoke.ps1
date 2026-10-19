param(
    [string]$BaseUrl = "https://app.uniway-tw.com",
    [string]$Python = "python",
    [string]$Output = "artifacts/seo-smoke.json"
)
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try {
    $Compose = @("compose", "--env-file", "deploy/selfhost/.env", "-f", "deploy/selfhost/docker-compose.yml")
    $ContainerId = & docker @Compose ps -q app
    if ($LASTEXITCODE -ne 0 -or -not $ContainerId) { throw "App container not found" }
    $State = & docker inspect --format '{{json .State}}' $ContainerId | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw "Cannot inspect app container" }
    $Restarts = & docker inspect --format '{{.RestartCount}}' $ContainerId
    if ($LASTEXITCODE -ne 0) { throw "Cannot inspect restart count" }
    [pscustomobject]@{ Status = $State.Status; Health = $State.Health.Status; RestartCount = $Restarts; StartedAt = $State.StartedAt } | Format-List
    if ($State.Status -ne "running" -or $State.Health.Status -ne "healthy") { throw "Wait for the app health check to become healthy before SEO acceptance" }
    & $Python scripts/check_seo.py --base-url $BaseUrl --json-output $Output
    if ($LASTEXITCODE -ne 0) { throw "SEO smoke check failed" }
    Write-Host "SEO HTTP checks passed. This does not establish Google indexing or field Core Web Vitals."
} finally { Pop-Location }
