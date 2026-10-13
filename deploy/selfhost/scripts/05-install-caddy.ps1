# Step 5 (administrator): install Caddy (the HTTPS front door) on Windows and make it start at every boot.
#   powershell -ExecutionPolicy Bypass -File .\05-install-caddy.ps1
# Before this: the domain's A record points to this home's fixed IP, and the router forwards TCP 80 and 443 to this computer.
#   -SkipService  only download, write and validate the Caddyfile (no administrator needed, nothing is started)
param([switch]$SkipService)
. "$PSScriptRoot\lib.ps1"
if (-not $SkipService) { Assert-Admin }

$e = Read-EnvFile
if (-not $e.Contains('DOMAIN') -or -not $e.Contains('ACME_EMAIL')) { throw '.env lacks DOMAIN / ACME_EMAIL: run 02-generate-secrets.ps1 first.' }
$dir = Join-Path $script:UniwayHome 'caddy'
$exe = Join-Path $dir 'caddy.exe'
New-Item -ItemType Directory -Force -Path $dir, (Join-Path $script:UniwayHome 'logs') | Out-Null

if (-not (Test-Path $exe)) {
    Write-Step 'Downloading Caddy (official release, checksum verified)'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/caddyserver/caddy/releases/latest' -Headers @{ 'User-Agent' = 'uniway-selfhost' }
    $zipAsset = $release.assets | Where-Object { $_.name -match '_windows_amd64\.zip$' } | Select-Object -First 1
    $sumAsset = $release.assets | Where-Object { $_.name -match '_checksums\.txt$' } | Select-Object -First 1
    if (-not $zipAsset -or -not $sumAsset) { throw 'could not find the Windows download in the latest Caddy release' }
    $zip = Join-Path $env:TEMP $zipAsset.name
    Invoke-WebRequest -Uri $zipAsset.browser_download_url -OutFile $zip -UseBasicParsing
    $sumsResponse = Invoke-WebRequest -Uri $sumAsset.browser_download_url -UseBasicParsing
    # GitHub serves the checksum list as a download, so the content can arrive as bytes rather than text
    $sums = if ($sumsResponse.Content -is [byte[]]) { [System.Text.Encoding]::UTF8.GetString($sumsResponse.Content) } else { [string]$sumsResponse.Content }
    $expected = ($sums -split "`n" | Where-Object { $_ -match [regex]::Escape($zipAsset.name) } | Select-Object -First 1)
    if (-not $expected) { throw 'checksum for the download not found' }
    $expected = ($expected -split '\s+')[0].ToLower()
    $actual = (Get-FileHash -Algorithm SHA512 -Path $zip).Hash.ToLower()
    if ($actual -ne $expected) { Remove-Item $zip -Force; throw 'Caddy download failed its checksum - not installing it.' }
    Expand-Archive -Path $zip -DestinationPath $dir -Force
    Remove-Item $zip -Force
    Write-Ok ("installed Caddy {0}" -f $release.tag_name)
} else { Write-Ok 'Caddy already installed' }

Write-Step 'Writing the Caddyfile'
$template = Get-Content -Raw -Path (Join-Path $script:DeployDir 'caddy\Caddyfile.template')
$text = $template.Replace('__DOMAIN__', $e['DOMAIN']).Replace('__ACME_EMAIL__', $e['ACME_EMAIL'])
$utf8 = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Join-Path $dir 'Caddyfile'), $text, $utf8)
& $exe validate --config (Join-Path $dir 'Caddyfile') --adapter caddyfile
Assert-ExitCode 'caddy validate'
Write-Ok 'Caddyfile is valid'

if ($SkipService) { Write-Host 'Stopped before the scheduled task (-SkipService).' -ForegroundColor Yellow; exit 0 }

Write-Step 'Starting Caddy at every boot (scheduled task, runs as SYSTEM)'
$taskName = 'UniWay-Caddy'
Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
$action = New-ScheduledTaskAction -Execute $exe -Argument ('run --config "{0}" --adapter caddyfile' -f (Join-Path $dir 'Caddyfile')) -WorkingDirectory $dir
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null
Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
Start-ScheduledTask -TaskName $taskName
Start-Sleep -Seconds 5
$state = (Get-ScheduledTask -TaskName $taskName).State
Write-Ok ("task '{0}' is {1}" -f $taskName, $state)

Write-Host ""
Write-Host ("Caddy is now answering for https://{0}. It asks Let's Encrypt for the certificate on the first visit; give it a minute." -f $e['DOMAIN']) -ForegroundColor Green
Write-Host 'If the certificate does not appear, check: DNS points here, the router forwards 80 and 443, and your ISP does not block them (log: C:\uniway\logs).'
