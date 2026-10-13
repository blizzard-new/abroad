# Step 3: build the web service image and start everything (database, storage, gateway, web service).
#   powershell -ExecutionPolicy Bypass -File .\03-start.ps1 [-SkipBuild]
# The first run downloads about 1 GB of images and builds the program image: expect 10-20 minutes. Later runs take seconds.
param([switch]$SkipBuild)
. "$PSScriptRoot\lib.ps1"

if (-not (Test-Path $script:EnvFile)) { throw 'deploy\selfhost\.env is missing: run 02-generate-secrets.ps1 first.' }
$null = & docker info 2>&1
if ($LASTEXITCODE -ne 0) { throw 'Docker is not running. Start Docker Desktop and wait for "Engine running".' }

if (-not $SkipBuild) {
    Write-Step 'Building the web service image (uniway-app:local)'
    # keep the previous image as :prev so a bad update can be rolled back (scripts/update.ps1 -Rollback)
    $old = (& docker images -q uniway-app:local)
    if ($old) { & docker tag uniway-app:local uniway-app:prev }
    Invoke-Compose build app
    Assert-ExitCode 'docker compose build'
}

Write-Step 'Starting the database'
Invoke-Compose up -d db
Assert-ExitCode 'docker compose up db'
Wait-Healthy 'db' 300

# The database image creates the REST and storage roles without a password; give them the one from .env.
# (Roles live outside the database dumps, so this also has to run again after restoring a backup onto a new machine.)
Write-Step 'Setting the passwords of the REST and storage database roles'
$pw = (Read-EnvFile)['DB_PASSWORD']
if ($pw -notmatch '^[0-9a-f]{32,}$') { throw 'DB_PASSWORD in .env has an unexpected shape (expected hex)' }
$null = Invoke-DbPsql ("alter role authenticator with login password '" + $pw + "'") 'supabase_admin'
$null = Invoke-DbPsql ("alter role supabase_storage_admin with login password '" + $pw + "'") 'supabase_admin'
Write-Ok 'role passwords set'

Write-Step 'Starting the REST door, storage and the gateway'
Invoke-Compose up -d rest storage gateway
Assert-ExitCode 'docker compose up'
foreach ($s in 'rest', 'storage', 'gateway') { Wait-Healthy $s 300 }

Write-Step 'Database tables and functions'
& "$PSScriptRoot\04-apply-migrations.ps1"
if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) { throw 'migrations failed' }

Write-Step 'Starting the web service'
Invoke-Compose up -d app
Assert-ExitCode 'docker compose up app'
Write-Host '  creating the private storage bucket for uploaded documents'
Invoke-Compose exec -T app python /opt/selfhost/create_bucket.py
Assert-ExitCode 'create_bucket'
Wait-Healthy 'app' 600

Write-Host ""
Write-Host 'The stack is running. Next: 05-install-caddy.ps1 (HTTPS), then verify.ps1.' -ForegroundColor Green
Write-Host '(The first minutes after a start are slow: the program warms its caches in the background.)'
