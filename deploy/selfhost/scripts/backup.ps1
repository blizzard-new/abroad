# Daily backup: database dump + uploaded-document files + the settings file, kept on disk and copied (encrypted) to Google Drive.
# Run by the scheduled task made in 07-setup-backup.ps1, or by hand:  powershell -ExecutionPolicy Bypass -File .\backup.ps1
param(
    [switch]$SkipCloud,           # keep it on this computer only
    [int]$KeepDaily = 14,         # how many daily backups to keep on disk
    [int]$KeepWeekly = 8,         # plus one per week (Sundays)
    [int]$KeepMonthly = 6         # plus one per month (the 1st)
)
. "$PSScriptRoot\lib.ps1"

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$dbDir = Join-Path $script:UniwayHome 'backups\db'
$stDir = Join-Path $script:UniwayHome 'backups\storage'
$logFile = Join-Path $script:UniwayHome ('logs\backup-' + (Get-Date -Format 'yyyyMM') + '.log')
New-Item -ItemType Directory -Force -Path $dbDir, $stDir, (Split-Path $logFile) | Out-Null

function Log([string]$m) { $line = ('{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m); Add-Content -Path $logFile -Value $line; Write-Host $line }

try {
    Log 'backup started'
    $dbId = Get-ContainerId 'db'
    if (-not $dbId) { throw 'the database container is not running' }

    # 1. the database (custom format: compressed, restorable table by table)
    $inside = "/tmp/uniway-$stamp.dump"
    & docker exec $dbId pg_dump -U postgres -d postgres -Fc --no-owner --exclude-table-data=public.uniway_schema_migrations -f $inside
    Assert-ExitCode 'pg_dump'
    $dumpFile = Join-Path $dbDir ("uniway-db-$stamp.dump")
    & docker cp ($dbId + ':' + $inside) $dumpFile
    Assert-ExitCode 'docker cp (dump)'
    & docker exec $dbId rm -f $inside
    if ((Get-Item $dumpFile).Length -lt 1024) { throw 'the dump is suspiciously small - not trusting this backup' }
    Log ("database dump {0:N1} MB" -f ((Get-Item $dumpFile).Length / 1MB))

    # 2. uploaded documents (encrypted by the program before they are stored; the volume holds ciphertext)
    $stFile = ("uniway-storage-$stamp.tar.gz")
    # GNU tar with --xattrs: the file store keeps each object's content type and checksum in extended attributes of the file,
    # and a copy that drops them (busybox tar does) comes back unreadable (HTTP 500 "extended attribute does not exist").
    & docker run --rm -v uniway_storage:/data:ro -v ("{0}:/out" -f $stDir) python:3.12-slim tar --xattrs '--xattrs-include=user.*' -czf ("/out/" + $stFile) -C /data .
    Assert-ExitCode 'storage archive'
    Log ("storage archive {0:N1} MB" -f ((Get-Item (Join-Path $stDir $stFile)).Length / 1MB))

    # 2b. which files exist (the rows of the storage tables), so the file store can be put back together with the files themselves
    $metaInside = "/tmp/uniway-meta-$stamp.sql"
    & docker exec $dbId pg_dump -U supabase_admin -d postgres --data-only --inserts --column-inserts -t storage.buckets -t storage.objects -f $metaInside
    Assert-ExitCode 'pg_dump (storage metadata)'
    $metaFile = Join-Path $stDir ("uniway-storage-meta-$stamp.sql")
    & docker cp ($dbId + ':' + $metaInside) $metaFile
    Assert-ExitCode 'docker cp (storage metadata)'
    & docker exec $dbId rm -f $metaInside

    # 2c. cryptographic manifest binding DB dump + storage archive + storage metadata SQL (RPO 24h / RTO 4h, Spec 14.3, T33)
    $stArchivePath = Join-Path $stDir $stFile
    $manifestObj = [ordered]@{
        backup_format_version = '1.1'
        stamp                 = $stamp
        created_at            = (Get-Date).ToUniversalTime().ToString('o')
        rpo_target_hours      = 24
        rto_target_hours      = 4
        db_dump_file          = (Split-Path -Leaf $dumpFile)
        db_dump_bytes         = (Get-Item $dumpFile).Length
        db_dump_sha256        = (Get-FileHash -Algorithm SHA256 $dumpFile).Hash.ToLowerInvariant()
        storage_archive_file  = $stFile
        storage_archive_bytes = (Get-Item $stArchivePath).Length
        storage_archive_sha256 = (Get-FileHash -Algorithm SHA256 $stArchivePath).Hash.ToLowerInvariant()
        storage_meta_file     = (Split-Path -Leaf $metaFile)
        storage_meta_bytes    = (Get-Item $metaFile).Length
        storage_meta_sha256   = (Get-FileHash -Algorithm SHA256 $metaFile).Hash.ToLowerInvariant()
    }
    $manifestPath = Join-Path $stDir ("uniway-manifest-$stamp.json")
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($manifestPath, ($manifestObj | ConvertTo-Json -Depth 4), $utf8NoBom)
    Log ("manifest written {0}" -f (Split-Path -Leaf $manifestPath))

    # 3. the settings file (secrets!) - it only ever leaves this computer through the encrypted remote
    $secretsDir = Join-Path $script:UniwayHome 'backups\secrets'
    New-Item -ItemType Directory -Force -Path $secretsDir | Out-Null
    Copy-Item -Path $script:EnvFile -Destination (Join-Path $secretsDir ("env-$stamp.txt")) -Force
    & icacls $secretsDir /inheritance:r /grant:r ("{0}:(OI)(CI)(F)" -f $env:USERNAME) 'SYSTEM:(OI)(CI)(F)' 'Administrators:(OI)(CI)(F)' | Out-Null

    # 4. keep N daily, N weekly (Sunday), N monthly (1st); delete the rest
    function Prune([string]$Dir, [string]$Filter) {
        $files = @(Get-ChildItem -Path $Dir -Filter $Filter | Sort-Object LastWriteTime -Descending)
        $keep = New-Object 'System.Collections.Generic.HashSet[string]'
        $files | Select-Object -First $KeepDaily | ForEach-Object { [void]$keep.Add($_.FullName) }
        $files | Where-Object { $_.LastWriteTime.DayOfWeek -eq 'Sunday' } | Select-Object -First $KeepWeekly | ForEach-Object { [void]$keep.Add($_.FullName) }
        $files | Where-Object { $_.LastWriteTime.Day -eq 1 } | Select-Object -First $KeepMonthly | ForEach-Object { [void]$keep.Add($_.FullName) }
        $files | Where-Object { -not $keep.Contains($_.FullName) } | ForEach-Object { Remove-Item $_.FullName -Force; Log ('pruned ' + $_.Name) }
    }
    Prune $dbDir 'uniway-db-*.dump'
    Prune $stDir 'uniway-storage-*.tar.gz'
    Prune $stDir 'uniway-storage-meta-*.sql'
    Prune $stDir 'uniway-manifest-*.json'
    Prune $secretsDir 'env-*.txt'

    # 5. copy to Google Drive through the encrypted rclone remote (nothing readable ever reaches Google)
    if (-not $SkipCloud) {
        $rclone = Get-Command rclone -ErrorAction SilentlyContinue
        $remotes = if ($rclone) { (& rclone listremotes) } else { @() }
        if ($rclone -and ($remotes -contains 'gdrive-crypt:')) {
            & rclone copy (Join-Path $script:UniwayHome 'backups') 'gdrive-crypt:uniway-backups' --transfers 2 --log-file (Join-Path $script:UniwayHome 'logs\rclone.log') --log-level INFO
            Assert-ExitCode 'rclone copy'
            # Drive keeps files 120 days longer than the local copies; older ones are removed
            & rclone delete 'gdrive-crypt:uniway-backups' --min-age 120d --log-file (Join-Path $script:UniwayHome 'logs\rclone.log') --log-level INFO
            & rclone rmdirs 'gdrive-crypt:uniway-backups' --leave-root 2>$null
            Log 'copied to Google Drive (encrypted)'
        } else {
            Log 'WARNING: rclone remote "gdrive-crypt" is not set up - backups stayed on this computer only (run 07-setup-backup.ps1)'
        }
    }
    Log 'backup finished OK'
} catch {
    Log ('BACKUP FAILED: ' + $_.Exception.Message)
    exit 1
}
