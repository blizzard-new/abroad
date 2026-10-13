# Step 6: copy the data from the current Supabase cloud project into this computer's database.
# Read-only on the cloud side. Run it on the day of the switch (and once earlier as a rehearsal: use -Rehearsal).
#
# Where to get the connection values: Supabase dashboard > the project > Connect > "Session pooler" (it works over IPv4;
# the "Direct connection" needs IPv6, which home lines often lack). The user name looks like postgres.<project ref>.
#
#   powershell -ExecutionPolicy Bypass -File .\06-migrate-from-cloud.ps1 -SourceHost aws-0-ap-southeast-2.pooler.supabase.com -SourceUser postgres.abcdefgh
param(
    [Parameter(Mandatory = $true)][string]$SourceHost,
    [Parameter(Mandatory = $true)][string]$SourceUser,
    [int]$SourcePort = 5432,
    [string]$SourceDb = 'postgres',
    [switch]$SkipAnalytics,     # leave out the anonymous page-view statistics (the biggest tables)
    [switch]$Rehearsal,         # only count the rows on both sides; change nothing
    [switch]$Force              # replace the local data even if it already has accounts in it
)
. "$PSScriptRoot\lib.ps1"

$e = Read-EnvFile
if (-not $e.Contains('DB_PASSWORD')) { throw '.env is missing: run 02-generate-secrets.ps1 and 03-start.ps1 first.' }
if ($env:UNIWAY_SOURCE_PASSWORD) {
    $plain = $env:UNIWAY_SOURCE_PASSWORD          # for unattended rehearsals; normally you type it below
} else {
    $secure = Read-Host ("Database password for {0}@{1} (typed hidden, never saved)" -f $SourceUser, $SourceHost) -AsSecureString
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
}
$work = Join-Path $script:UniwayHome 'backups\migration'
New-Item -ItemType Directory -Force -Path $work | Out-Null
$countSql = "select table_name || '=' || (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from public.%I', table_name), false, true, '')))[1]::text from information_schema.tables where table_schema = 'public' and table_type = 'BASE TABLE' and table_name <> 'uniway_schema_migrations' order by 1"

function Get-SourceCounts {
    $env:PGPASSWORD = $plain
    try {
        $out = & docker run --rm -e PGPASSWORD postgres:17-alpine psql -h $SourceHost -p $SourcePort -U $SourceUser -d $SourceDb -X -A -t -c $countSql
        Assert-ExitCode 'reading the cloud database'
    } finally { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
    return @($out | Where-Object { $_ -match '=' })
}
function ConvertTo-CountMap([string[]]$Lines) {
    $m = [ordered]@{}
    foreach ($l in $Lines) { $i = $l.LastIndexOf('='); $m[$l.Substring(0, $i)] = [int64]$l.Substring($i + 1) }
    return $m
}

Write-Step 'Counting rows in the cloud database'
$src = ConvertTo-CountMap (Get-SourceCounts)
Write-Ok ("{0} tables, {1} rows" -f $src.Count, (($src.Values | Measure-Object -Sum).Sum))

Wait-Healthy 'db' 120
$dst = ConvertTo-CountMap (((Invoke-DbPsql $countSql) -split "`n") | Where-Object { $_ -match '=' })
$localRows = (($dst.Values | Measure-Object -Sum).Sum)
Write-Ok ("local database: {0} tables, {1} rows" -f $dst.Count, $localRows)
# A freshly migrated database already holds a few seed rows; those come across from the cloud too, so they are cleared first.
# Real user data here (accounts) means this is not a fresh install: stop unless -Force.
$localAccounts = if ($dst.Contains('exchange_accounts')) { $dst['exchange_accounts'] } else { 0 }
if ($localAccounts -gt 0 -and -not $Force) { throw ('the local database already has {0} account(s) - this does not look like a fresh install. Use -Force only if you really mean to replace them.' -f $localAccounts) }
$missing = @($src.Keys | Where-Object { -not $dst.Contains($_) })
if ($missing.Count -gt 0) { throw ("these cloud tables do not exist locally (run 04-apply-migrations.ps1?): " + ($missing -join ', ')) }

if ($Rehearsal) { Write-Host 'Rehearsal only: nothing was changed.' -ForegroundColor Yellow; exit 0 }

Write-Step 'Pausing the web service so nothing is written during the copy'
Invoke-Compose stop app

if ($localRows -gt 0) {
    Write-Step 'Clearing the local seed rows'
    $null = Invoke-DbPsql "set client_min_messages to warning; do `$`$ declare r record; begin for r in select tablename from pg_tables where schemaname = 'public' and tablename <> 'uniway_schema_migrations' loop execute format('truncate table public.%I restart identity cascade', r.tablename); end loop; end `$`$"
}

Write-Step 'Dumping the cloud data (data only, public schema)'
$exclude = @()
if ($SkipAnalytics) { $exclude = @('--exclude-table-data=public.exchange_analytics_events', '--exclude-table-data=public.exchange_analytics_api_hourly') }
$env:PGPASSWORD = $plain
try {
    & docker run --rm -e PGPASSWORD -v ("{0}:/out" -f $work) postgres:17-alpine pg_dump -h $SourceHost -p $SourcePort -U $SourceUser -d $SourceDb --data-only --schema=public --no-owner --no-privileges --exclude-table=public.uniway_schema_migrations -Fc -f /out/cloud-data.dump @exclude
    Assert-ExitCode 'pg_dump'
} finally { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
Write-Ok ("dump written: {0:N1} MB" -f ((Get-Item (Join-Path $work 'cloud-data.dump')).Length / 1MB))

Write-Step 'Loading it into the local database'
$dbId = Get-ContainerId 'db'
& docker cp (Join-Path $work 'cloud-data.dump') ($dbId + ':/tmp/cloud-data.dump')
Assert-ExitCode 'docker cp'
& docker exec -e PGPASSWORD=$($e['DB_PASSWORD']) $dbId pg_restore -h 127.0.0.1 -U supabase_admin -d postgres --data-only --disable-triggers --no-owner --exit-on-error /tmp/cloud-data.dump
Assert-ExitCode 'pg_restore'
& docker exec $dbId rm -f /tmp/cloud-data.dump

Write-Step 'Comparing row counts, table by table'
$after = ConvertTo-CountMap (((Invoke-DbPsql $countSql) -split "`n") | Where-Object { $_ -match '=' })
$bad = 0
foreach ($t in $src.Keys) {
    $skipped = $SkipAnalytics -and ($t -like 'exchange_analytics_*')
    if ($skipped) { continue }
    if ($after[$t] -ne $src[$t]) { Write-Bad ("{0}: cloud {1}, local {2}" -f $t, $src[$t], $after[$t]); $bad++ }
}
if ($bad -eq 0) { Write-Ok 'every table has the same number of rows as the cloud' } else { throw ("{0} table(s) differ - do not switch over; read the lines above" -f $bad) }

Write-Step 'Starting the web service again'
Invoke-Compose up -d app
Wait-Healthy 'app' 600
Write-Host ""
Write-Host 'Data copied and verified.' -ForegroundColor Green
