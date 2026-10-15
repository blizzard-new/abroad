# Daily official source check for all 6 supported home universities (NTU, NTPU, NCU, CGU, CCU, TKU).
# Triggered automatically by Windows Task Scheduler ('UniWay-DailySourceCheck') at 03:00 AM daily
# (with StartWhenAvailable catch-up if the PC was off/asleep), or manually at any time.
. "$PSScriptRoot\lib.ps1"

$logDir = "C:\uniway\logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logFile = Join-Path $logDir "daily-source-check.log"

function Write-CheckLog([string]$Msg) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Msg
    Add-Content -Path $logFile -Value $line -Encoding UTF8
    Write-Host $line
}

Write-CheckLog "Starting scheduled official source check for all registered home universities..."
$headers = @{
    "X-Admin-Id"   = "system_daily_scheduler"
    "X-Admin-Role" = "super_admin"
}

try {
    $sourcesResp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/admin/sources" -Headers $headers -TimeoutSec 15
    foreach ($src in $sourcesResp.items) {
        $body = @{
            action              = "fetch"
            resource_url        = $src.entry_url
            force_unconditional = $false
            reason              = "Daily 03:00 scheduled source check"
        } | ConvertTo-Json -Compress
        $res = Invoke-RestMethod -Uri ("http://127.0.0.1:8000/admin/sources/{0}/refresh" -f $src.id) `
            -Method Post -Headers $headers -ContentType "application/json; charset=utf-8" -Body $body -TimeoutSec 15
        Write-CheckLog ("Enqueued source check for {0} ({1}) -> job_id={2} status={3}" -f $src.id, $src.entry_url, $res.job_id, $res.status)
    }
    Write-CheckLog ("Completed daily source check enqueue for {0} universities." -f $sourcesResp.total)
} catch {
    Write-CheckLog ("ERROR during daily source check: {0}" -f $_.Exception.Message)
    exit 1
}
