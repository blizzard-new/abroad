# Step 4: apply the database migrations (supabase\migrations\*.sql, in order). Safe to run again: applied ones are skipped.
#   powershell -ExecutionPolicy Bypass -File .\04-apply-migrations.ps1
. "$PSScriptRoot\lib.ps1"

$migrations = Join-Path $script:RepoRoot 'supabase\migrations'
$files = @(Get-ChildItem -Path $migrations -Filter '*.sql' | Sort-Object Name)
if ($files.Count -eq 0) { throw "no migrations found in $migrations" }

Write-Step ("Applying up to {0} migrations" -f $files.Count)
Wait-Healthy 'db' 180

# The files hold Chinese text, so they are copied into the container and read there (piping them through
# Windows PowerShell 5.1 would turn every Chinese character into a question mark).
# They are copied with Unix line endings: Git for Windows may have checked them out with CRLF, and a migration that
# compares function text (several do, on purpose) would then see a different text and refuse to run, or build a
# function that differs from the one on the old server.
$staging = Join-Path $env:TEMP 'uniway-migrations'
if (Test-Path $staging) { Remove-Item -Recurse -Force $staging }
New-Item -ItemType Directory -Path $staging | Out-Null
$utf8 = New-Object System.Text.UTF8Encoding($false)
foreach ($f in $files) {
    $text = [System.IO.File]::ReadAllText($f.FullName, $utf8)
    [System.IO.File]::WriteAllText((Join-Path $staging $f.Name), $text.Replace("`r`n", "`n"), $utf8)
}
$dbId = Get-ContainerId 'db'
& docker exec $dbId rm -rf /tmp/uniway-migrations
& docker cp $staging ($dbId + ':/tmp/uniway-migrations')
Assert-ExitCode 'docker cp'
Remove-Item -Recurse -Force $staging

$null = Invoke-DbPsql 'create table if not exists public.uniway_schema_migrations (name text primary key, applied_at timestamptz not null default now())'
$applied = @{}
foreach ($row in ((Invoke-DbPsql 'select name from public.uniway_schema_migrations') -split "`n")) { if ($row.Trim()) { $applied[$row.Trim()] = $true } }

$count = 0
foreach ($f in $files) {
    if ($applied.ContainsKey($f.Name)) { continue }
    Write-Host ("  applying {0}" -f $f.Name)
    & docker exec -e PGCLIENTENCODING=UTF8 $dbId psql -U postgres -d postgres -X -q -v ON_ERROR_STOP=1 -f ('/tmp/uniway-migrations/' + $f.Name)
    Assert-ExitCode ("migration " + $f.Name)
    $null = Invoke-DbPsql ("insert into public.uniway_schema_migrations(name) values ('" + $f.Name.Replace("'", "''") + "')")
    $count++
}
& docker exec $dbId rm -rf /tmp/uniway-migrations
if ($count -eq 0) { Write-Ok 'database already up to date' } else { Write-Ok ("applied {0} migration(s)" -f $count) }
