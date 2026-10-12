# Prove a backup works: restore the newest database dump into a throw-away database and compare row counts with the live one.
# Do this once after the first backup and then monthly. It never touches the live database.
#   powershell -ExecutionPolicy Bypass -File .\restore-test.ps1 [-Dump C:\uniway\backups\db\uniway-db-....dump]
param([string]$Dump = '')
. "$PSScriptRoot\lib.ps1"

if (-not $Dump) {
    $latest = Get-ChildItem -Path (Join-Path $script:UniwayHome 'backups\db') -Filter 'uniway-db-*.dump' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latest) { throw 'no database backup found: run backup.ps1 first' }
    $Dump = $latest.FullName
}
Write-Step ("Restoring {0} into a temporary database" -f $Dump)
$e = Read-EnvFile
$name = 'uniway-restore-test'
Invoke-Quiet { docker rm -f $name }
$image = (& docker inspect -f '{{.Config.Image}}' (Get-ContainerId 'db'))
& docker run -d --name $name -e POSTGRES_PASSWORD=restore-test-only -e JWT_SECRET=restore-test-only-jwt-secret-0123456789 $image | Out-Null
Assert-ExitCode 'starting the temporary database'
try {
    for ($i = 0; $i -lt 60; $i++) {
        Invoke-Quiet { docker exec $name pg_isready -U postgres -h localhost }
        if ($LASTEXITCODE -eq 0) { break }
        Start-Sleep -Seconds 2
    }
    & docker cp $Dump ($name + ':/tmp/restore.dump')
    Assert-ExitCode 'docker cp'
    # Into a brand-new database as the image's superuser (the dump carries the REST door's event triggers and extensions,
    # which only a superuser may create). Anything pg_restore complains about is shown, not hidden.
    & docker exec $name psql -U supabase_admin -d postgres -X -q -c 'create database restore_test'
    Assert-ExitCode 'creating the scratch database'
    $oldPref = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
    & docker exec $name pg_restore -U supabase_admin -d restore_test --no-owner /tmp/restore.dump 2>&1 | Select-Object -Last 8
    $restoreExit = $LASTEXITCODE
    $ErrorActionPreference = $oldPref
    if ($restoreExit -ne 0) { Write-Warn ("pg_restore finished with exit code {0}: check the lines above (a few harmless 'already exists' messages are normal)" -f $restoreExit) }
    $countSql = "select table_name || '=' || (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from public.%I', table_name), false, true, '')))[1]::text from information_schema.tables where table_schema = 'public' and table_type = 'BASE TABLE' order by 1"
    $restored = (& docker exec $name psql -U supabase_admin -d restore_test -X -A -t -c $countSql) | Where-Object { $_ -match '=' }
    $live = ((Invoke-DbPsql $countSql) -split "`n") | Where-Object { $_ -match '=' }
    $rm = @{}; foreach ($l in $restored) { $i = $l.LastIndexOf('='); $rm[$l.Substring(0, $i)] = [int64]$l.Substring($i + 1) }
    $bad = 0; $tables = 0
    foreach ($l in $live) {
        $i = $l.LastIndexOf('='); $t = $l.Substring(0, $i); $n = [int64]$l.Substring($i + 1); $tables++
        # the live database may have gained rows since the backup; a restore with MORE rows than live would be wrong
        if (-not $rm.ContainsKey($t)) { Write-Bad ("table {0} missing in the restore" -f $t); $bad++ }
        elseif ($rm[$t] -gt $n) { Write-Bad ("{0}: restore has {1} rows, live only {2}" -f $t, $rm[$t], $n); $bad++ }
    }
    # an empty restore must not pass: the restored rows have to be most of what the live database holds now
    $liveTotal = 0; foreach ($l in $live) { $liveTotal += [int64]$l.Substring($l.LastIndexOf('=') + 1) }
    $restoredTotal = 0; foreach ($v in $rm.Values) { $restoredTotal += $v }
    if ($liveTotal -gt 0 -and $restoredTotal -lt ($liveTotal * 0.8)) { Write-Bad ("restore holds {0} rows, live holds {1}" -f $restoredTotal, $liveTotal); $bad++ }
    if ($bad -eq 0) { Write-Ok ("restore test passed: {0} tables present, {1} rows restored (live now: {2})" -f $tables, $restoredTotal, $liveTotal) } else { throw "restore test FAILED ($bad problem(s))" }
} finally {
    Invoke-Quiet { docker rm -f $name }
}
