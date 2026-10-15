# Step 7 (administrator): daily backups to disk and, encrypted, to Google Drive; plus the five-minute health check.
#   powershell -ExecutionPolicy Bypass -File .\07-setup-backup.ps1
#
# Google Drive part, one time and by hand (it needs YOU to sign in to Google in a browser):
#   1. winget install -e --id Rclone.Rclone        (then open a new PowerShell window)
#   2. rclone config  ->  n (new remote)  ->  name: gdrive  ->  storage: drive  ->  leave client id/secret empty
#      (better: your own OAuth client, see the guide)  ->  scope 1 (full access)  ->  auto config: y  -> sign in in the browser
#   3. rclone config  ->  n  ->  name: gdrive-crypt  ->  storage: crypt  ->  remote: gdrive:uniway-crypt
#      ->  filename encryption: standard  ->  directory name encryption: true  ->  password: g (generate, 128 bits)  ->  same for salt
#   4. WRITE DOWN both generated passwords in your password manager. Without them the backups cannot be decrypted, ever.
. "$PSScriptRoot\lib.ps1"
Assert-Admin

Write-Step 'Is rclone ready?'
$rclone = Get-Command rclone -ErrorAction SilentlyContinue
if (-not $rclone) {
    Write-Warn 'rclone is not installed yet - backups will be kept on this computer only until it is (see the steps at the top of this script).'
} else {
    $remotes = (& rclone listremotes)
    if ($remotes -contains 'gdrive-crypt:') { Write-Ok 'rclone remote gdrive-crypt: found' } else { Write-Warn 'rclone is installed but the remote "gdrive-crypt" does not exist yet - do steps 2 and 3 above.' }
}

function Register-Daily([string]$Name, [string]$ScriptFile, [string]$Time, [string]$Extra = '') {
    Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
    $arg = '-NoProfile -ExecutionPolicy Bypass -File "{0}" {1}' -f (Join-Path $PSScriptRoot $ScriptFile), $Extra
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arg
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time
    $principal = New-ScheduledTaskPrincipal -UserId $script:RunAs -LogonType Interactive -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 3)
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
    Write-Ok ("scheduled '{0}' daily at {1}" -f $Name, $Time)
}

Write-Step 'Scheduled tasks'
# Docker Desktop's engine runs inside the signed-in user's session, so these tasks run as that user (not as SYSTEM).
$script:RunAs = '{0}\{1}' -f $env:USERDOMAIN, $env:USERNAME
Write-Host ('  tasks will run as ' + $script:RunAs + ' while that user is signed in')
Register-Daily 'UniWay-DailySourceCheck' 'daily-source-check.ps1' '03:00'
Register-Daily 'UniWay-Backup' 'backup.ps1' '04:00'

Get-ScheduledTask -TaskName 'UniWay-Health' -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "{0}"' -f (Join-Path $PSScriptRoot 'healthcheck.ps1'))
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date -RepetitionInterval (New-TimeSpan -Minutes 5)
$principal = New-ScheduledTaskPrincipal -UserId $script:RunAs -LogonType Interactive -RunLevel Highest
Register-ScheduledTask -TaskName 'UniWay-Health' -Action $action -Trigger $trigger -Principal $principal -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 4)) | Out-Null
Write-Ok "scheduled 'UniWay-Health' every 5 minutes"

Write-Step 'Take the first backup now (and then run restore-test.ps1 to prove it can be restored)'
& "$PSScriptRoot\backup.ps1"
