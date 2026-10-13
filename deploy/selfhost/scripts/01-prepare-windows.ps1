# Step 1 (administrator): make Windows behave like a server - never sleep, open only the web ports, cap the upload speed.
#   powershell -ExecutionPolicy Bypass -File .\01-prepare-windows.ps1 [-UploadMbps 250]
param(
    [int]$UploadMbps = 250      # Jerry: "keep upload at 250, leave at least 50 for me" on a 300 Mbps line (Mbps = megabits per second)
)
. "$PSScriptRoot\lib.ps1"
Assert-Admin

Write-Step 'Folders'
foreach ($d in 'logs', 'backups\db', 'backups\storage', 'caddy') {
    New-Item -ItemType Directory -Force -Path (Join-Path $script:UniwayHome $d) | Out-Null
}
Write-Ok ("created {0}\{{logs,backups,caddy}}" -f $script:UniwayHome)

Write-Step 'Power: never sleep or hibernate while plugged in (the screen may still turn off)'
& powercfg /change standby-timeout-ac 0 | Out-Null
& powercfg /change hibernate-timeout-ac 0 | Out-Null
& powercfg /change disk-timeout-ac 0 | Out-Null
Write-Ok 'standby, hibernate and disk-sleep timeouts set to "never" on AC power'
Write-Warn 'Still do by hand: Settings > Windows Update > Advanced options > Active hours (so updates do not restart the computer while people use the site), and choose "Notify to schedule restart".'

Write-Step 'Firewall: allow inbound web traffic to Caddy only'
$caddy = Join-Path $script:UniwayHome 'caddy\caddy.exe'
Get-NetFirewallRule -DisplayName 'UniWay Caddy web' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -DisplayName 'UniWay Caddy web' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 80, 443 -Program $caddy -Profile Any | Out-Null
Write-Ok 'inbound TCP 80 and 443 allowed for caddy.exe (the rule applies once Caddy is installed in step 5)'
Write-Warn 'Nothing else is opened: the web service (8000), database and storage listen only inside this computer.'
Write-Warn 'Never forward port 3389 (Remote Desktop) from the router to the internet; use a VPN such as Tailscale to reach this computer from outside.'

Write-Step ("Upload cap: {0} Mbps for the web server" -f $UploadMbps)
try {
    Get-NetQosPolicy -Name 'UniWay upload cap' -ErrorAction SilentlyContinue | Remove-NetQosPolicy -Confirm:$false
    New-NetQosPolicy -Name 'UniWay upload cap' -AppPathNameMatchCondition 'caddy.exe' -ThrottleRateActionBitsPerSecond ([int64]$UploadMbps * 1000000) | Out-Null
    Write-Ok ("Windows QoS policy 'UniWay upload cap' = {0} Mbps for caddy.exe" -f $UploadMbps)
    Write-Warn 'Check it once with a real download from outside (see the guide, section on bandwidth). If Windows ignores it, set the same cap in the router (QoS / bandwidth control) instead.'
} catch {
    Write-Warn ('Could not create the QoS policy: ' + $_.Exception.Message)
    Write-Warn 'Set the upload cap in the router instead (QoS / bandwidth control), 250 Mbps for this computer.'
}

Write-Host ""
Write-Host 'Step 1 done.' -ForegroundColor Green
