# Put a backup back: the database rows (public schema), the list of stored files, and the encrypted files themselves.
# Use it on a NEW computer after a disaster (steps 3 and 5 first, so an empty database and the secrets in .env exist),
# or to roll the system back to an earlier day.  It replaces what is in the database now.
#   powershell -ExecutionPolicy Bypass -File .\08-restore-backup.ps1                      (newest backup)
#   powershell -ExecutionPolicy Bypass -File .\08-restore-backup.ps1 -Stamp 20261012-040000 -Force
param(
    [string]$Stamp = '',      # the yyyyMMdd-HHmmss in the backup file names; default = the newest database backup
    [switch]$Force            # needed when the database already holds accounts
)
. "$PSScriptRoot\lib.ps1"

$dbDir = Join-Path $script:UniwayHome 'backups\db'
$stDir = Join-Path $script:UniwayHome 'backups\storage'
if (-not $Stamp) {
    $latest = Get-ChildItem -Path $dbDir -Filter 'uniway-db-*.dump' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latest) { throw "no database backup found in $dbDir" }
    $Stamp = $latest.BaseName.Substring('uniway-db-'.Length)
}
$dump = Join-Path $dbDir ("uniway-db-$Stamp.dump")
$meta = Join-Path $stDir ("uniway-storage-meta-$Stamp.sql")
$files = Join-Path $stDir ("uniway-storage-$Stamp.tar.gz")
if (-not (Test-Path $dump)) { throw "missing $dump" }
Write-Step ("Restoring backup {0}" -f $Stamp)
Write-Host ("  database : {0}" -f $dump)
Write-Host ("  file list: {0}" -f $(if (Test-Path $meta) { $meta } else { '(none in this backup)' }))
Write-Host ("  files    : {0}" -f $(if (Test-Path $files) { $files } else { '(none in this backup)' }))

Wait-Healthy 'db' 180
$accounts = [int](Invoke-DbPsql 'select count(*) from public.exchange_accounts')
if ($accounts -gt 0 -and -not $Force) { throw ("the database already has {0} account(s); this would replace them. Use -Force if that is what you want." -f $accounts) }

Write-Step 'Stopping the web service and the file store'
Invoke-Compose stop app storage

Write-Step 'Clearing the current rows'
$null = Invoke-DbPsql "set client_min_messages to warning; do `$`$ declare r record; begin for r in select tablename from pg_tables where schemaname = 'public' and tablename <> 'uniway_schema_migrations' loop execute format('truncate table public.%I restart identity cascade', r.tablename); end loop; end `$`$"
$null = Invoke-DbPsql 'set client_min_messages to warning; truncate table storage.objects, storage.buckets cascade' 'supabase_admin'

Write-Step 'Loading the database rows'
$e = Read-EnvFile
$dbId = Get-ContainerId 'db'
& docker cp $dump ($dbId + ':/tmp/restore.dump')
Assert-ExitCode 'docker cp'
# the record of which migrations ran belongs to the database being restored INTO, not to the backup, so it is left out
& docker exec $dbId sh -c "pg_restore -l /tmp/restore.dump | grep -v uniway_schema_migrations > /tmp/restore.list"
Assert-ExitCode 'listing the backup'
$env:PGPASSWORD = $e['DB_PASSWORD']
try {
    & docker exec -e PGPASSWORD $dbId pg_restore -h 127.0.0.1 -U supabase_admin -d postgres --data-only --disable-triggers --no-owner -n public --exit-on-error -L /tmp/restore.list /tmp/restore.dump
    Assert-ExitCode 'pg_restore'
} finally { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
& docker exec $dbId rm -f /tmp/restore.dump /tmp/restore.list

if (Test-Path $meta) {
    Write-Step 'Loading the list of stored files'
    & docker cp $meta ($dbId + ':/tmp/storage-meta.sql')
    Assert-ExitCode 'docker cp'
    & docker exec -e PGCLIENTENCODING=UTF8 $dbId psql -U supabase_admin -d postgres -X -q -v ON_ERROR_STOP=1 -f /tmp/storage-meta.sql
    Assert-ExitCode 'loading the storage metadata'
    & docker exec $dbId rm -f /tmp/storage-meta.sql
}

if (Test-Path $files) {
    Write-Step 'Putting the encrypted files back'
    # root inside the container (needed to set the extended attributes), GNU tar with --xattrs (see backup.ps1)
    & docker run --rm -v uniway_storage:/data python:3.12-slim find /data -mindepth 1 -delete
    Assert-ExitCode 'emptying the file store'
    & docker run --rm -v uniway_storage:/data -v ("{0}:/in:ro" -f $stDir) python:3.12-slim tar --xattrs '--xattrs-include=user.*' -xzf ("/in/uniway-storage-$Stamp.tar.gz") -C /data
    Assert-ExitCode 'restoring the storage files'
}

Write-Step 'Starting everything again'
Invoke-Compose up -d storage app
Assert-ExitCode 'docker compose up'
Wait-Healthy 'storage' 120
Wait-Healthy 'app' 600
$counts = Invoke-DbPsql "select (select count(*) from public.exchange_accounts) || ' accounts, ' || (select count(*) from public.exchange_analytics_events) || ' usage events, ' || (select count(*) from storage.objects) || ' stored files'"
Write-Host ""
Write-Host ("Restored: {0}. Run verify.ps1 next." -f $counts) -ForegroundColor Green
