# Security review of this computer. READ-ONLY: it changes nothing, it only looks and tells you what to fix.
#   powershell -ExecutionPolicy Bypass -File .\security-check.ps1          (run it in an administrator PowerShell)
# Run it after hardening the computer, then once a month. Everything it prints is safe to paste into a chat; it never prints a
# password, a key, or the new name of the administrator account.
. "$PSScriptRoot\lib.ps1"
$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$script:fails = 0
$script:warns = 0
function Result([string]$Status, [string]$Text) {
    if ($Status -eq 'OK') { Write-Ok $Text }
    elseif ($Status -eq 'WARN') { Write-Warn $Text; $script:warns++ }
    else { Write-Bad $Text; $script:fails++ }
}
function Info([string]$Text) { Write-Host ('         ' + $Text) }
function Safe([string]$Name, [scriptblock]$Block) {
    try { & $Block } catch { Result 'WARN' ("{0}: could not be checked ({1})" -f $Name, $_.Exception.Message) }
}
function Test-PrivateAddress([string]$Ip) {
    if (-not $Ip -or $Ip -eq '-' -or $Ip -eq '::1' -or $Ip -eq '::') { return $true }
    if ($Ip -match '^(127\.|10\.|192\.168\.|169\.254\.|172\.(1[6-9]|2[0-9]|3[01])\.|fe80|fc|fd)') { return $true }
    if ($Ip -match '^100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.') { return $true }      # Tailscale / carrier-grade NAT range
    return $false
}

$isAdmin = Test-Admin
Write-Step 'Security review (read-only)'
if (-not $isAdmin) { Write-Warn 'Not running as administrator: the password policy and sign-in history cannot be read. Right-click PowerShell > Run as administrator.' }

# ---- accounts ----------------------------------------------------------------------------------------------------
Write-Step 'Accounts'
$adminName = ''
Safe 'administrator account' {
    $users = @(Get-LocalUser)
    $builtin = $users | Where-Object { $_.SID.Value -like 'S-1-5-21-*-500' } | Select-Object -First 1
    if (-not $builtin) { Result 'WARN' 'the built-in administrator account was not found'; return }
    $script:adminName = $builtin.Name
    if ($builtin.Name -eq 'Administrator') { Result 'WARN' 'the built-in administrator account still has the default name "Administrator", the first name every password-guessing bot tries (Rename-LocalUser)' }
    else { Result 'OK' 'the built-in administrator account was renamed (it is not called "Administrator")' }
    $enabled = @($users | Where-Object { $_.Enabled })
    Info ('enabled local accounts: ' + (($enabled | ForEach-Object { if ($_.SID.Value -like 'S-1-5-21-*-500') { '(built-in administrator)' } else { $_.Name } }) -join ', '))
    if ($enabled.Count -gt 2) { Result 'WARN' ('{0} local accounts are enabled: remove the ones nobody uses (Disable-LocalUser)' -f $enabled.Count) }
}

Safe 'automatic sign-in' {
    $w = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'
    if ($w.AutoAdminLogon -eq '1') {
        Info 'automatic sign-in is on (needed so the site comes back after a restart); anyone who can touch this computer gets in, so keep it somewhere safe'
        $name = $w.DefaultUserName
        $acct = Get-LocalUser -Name $name -ErrorAction SilentlyContinue
        if ($acct -and $acct.PasswordExpires) {
            Result 'FAIL' ('the password of the automatic-sign-in account expires on {0}: after that the site stays down after a restart. Run: Set-LocalUser -Name <that account> -PasswordNeverExpires $true' -f $acct.PasswordExpires.ToString('yyyy-MM-dd'))
        } else { Result 'OK' 'the password of the automatic-sign-in account does not expire' }
    } else { Result 'WARN' 'automatic sign-in is off: after a power cut or an update restart the site stays down until someone signs in' }
}

Safe 'password and lockout policy' {
    if (-not $isAdmin) { return }
    $tmp = Join-Path $env:TEMP ('secpol-' + [guid]::NewGuid().ToString('N') + '.inf')
    & secedit.exe /export /cfg $tmp /areas SECURITYPOLICY | Out-Null
    $txt = Get-Content -Path $tmp
    Remove-Item $tmp -Force -ErrorAction SilentlyContinue
    function Get-Policy([string]$Key) {
        $line = $txt | Where-Object { $_ -match ('^\s*' + $Key + '\s*=') } | Select-Object -First 1
        if ($line) { return [int](($line -split '=')[1].Trim()) } else { return $null }
    }
    $min = Get-Policy 'MinimumPasswordLength'
    $bad = Get-Policy 'LockoutBadCount'
    $dur = Get-Policy 'LockoutDuration'
    if ($null -eq $min -or $min -lt 14) { Result 'WARN' ('minimum password length is {0}: set it to at least 14 (net accounts /minpwlen:14)' -f $min) } else { Result 'OK' ('minimum password length is {0}' -f $min) }
    if ($null -eq $bad -or $bad -eq 0) { Result 'FAIL' 'account lockout is OFF: a guessing bot can try passwords all day (net accounts /lockoutthreshold:10)' }
    else { Result 'OK' ('an account locks for {0} minutes after {1} failed sign-ins' -f $dur, $bad) }
}

# ---- how the computer can be reached ------------------------------------------------------------------------------------
Write-Step 'Remote access and the firewall'
Safe 'firewall profiles' {
    $off = @(Get-NetFirewallProfile | Where-Object { $_.Enabled -ne 'True' })
    if ($off.Count -gt 0) { Result 'FAIL' ('the Windows firewall is OFF for: ' + (($off | ForEach-Object { $_.Name }) -join ', ') + ' (Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True)') }
    else { Result 'OK' 'the Windows firewall is on for every network type' }
}

Safe 'remote desktop' {
    $ts = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server'
    if ($ts.fDenyTSConnections -ne 0) { Result 'OK' 'Remote Desktop is turned off'; return }
    $rdp = Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp'
    $port = [string]$rdp.PortNumber
    if ($rdp.UserAuthentication -eq 1) { Result 'OK' 'Remote Desktop requires network-level authentication' } else { Result 'FAIL' 'Remote Desktop does not require network-level authentication' }
    $rules = @(Get-NetFirewallPortFilter -Protocol TCP | Where-Object { $_.LocalPort -eq $port } | Get-NetFirewallRule |
        Where-Object { $_.Enabled -eq 'True' -and $_.Direction -eq 'Inbound' -and $_.Action -eq 'Allow' })
    $open = 0; $scopes = @()
    foreach ($r in $rules) {
        $remote = @(($r | Get-NetFirewallAddressFilter).RemoteAddress)
        if ($remote -contains 'Any') { $open++ } else { $scopes += $remote }
    }
    if ($rules.Count -eq 0) { Result 'OK' ('Remote Desktop (TCP {0}) has no inbound firewall rule: it cannot be reached from the network' -f $port) }
    elseif ($open -gt 0) { Result 'FAIL' ('Remote Desktop (TCP {0}) is allowed from ANY address by {1} firewall rule(s): limit it to Tailscale and the local network (see the guide, security chapter)' -f $port, $open) }
    else { Result 'OK' ('Remote Desktop (TCP {0}) is only allowed from: {1}' -f $port, (($scopes | Select-Object -Unique) -join ', ')) }
}

Safe 'VPN' {
    $ts = @(Get-Service -Name 'Tailscale*' -ErrorAction SilentlyContinue)
    if ($ts.Count -gt 0 -and ($ts | Where-Object { $_.Status -eq 'Running' })) { Result 'OK' 'Tailscale is installed and running (remote access can go through it instead of the open internet)' }
    else { Result 'WARN' 'no Tailscale found: without a VPN, remote access depends on exposing Remote Desktop to the internet' }
}

Safe 'listening ports' {
    $listen = @(Get-NetTCPConnection -State Listen | Where-Object { $_.LocalAddress -notin @('127.0.0.1', '::1') -and $_.LocalPort -lt 49152 })
    $rows = @($listen | Group-Object LocalPort | Sort-Object { [int]$_.Name } | ForEach-Object {
        $p = Get-Process -Id ($_.Group[0].OwningProcess) -ErrorAction SilentlyContinue
        '{0} ({1})' -f $_.Name, $(if ($p) { $p.ProcessName } else { '?' }) })
    Info ('ports listening beyond this computer: ' + ($rows -join ', '))
    $risky = @($listen | Where-Object { $_.LocalPort -in @(21, 23, 139, 445, 1433, 2375, 3306, 5432, 5985, 5986, 6379, 27017) } | Select-Object -ExpandProperty LocalPort -Unique)
    if ($risky.Count -gt 0) { Result 'WARN' ('listening on ports that are often attacked: {0}. Make sure the firewall does not allow them from the internet' -f ($risky -join ', ')) }
    else { Result 'OK' 'nothing listens on the usual attack targets (SMB, databases, WinRM, the Docker API)' }
    $v6 = @(Get-NetIPAddress -AddressFamily IPv6 -ErrorAction SilentlyContinue | Where-Object { $_.IPAddress -notmatch '^(fe80|::1|fd|fc)' })
    if ($v6.Count -gt 0) { Result 'WARN' 'this computer has a public IPv6 address: the router IPv6 firewall alone decides what reaches it (the Windows firewall limits above also cover IPv6)' }
}

Safe 'docker' {
    $null = & docker info 2>&1
    if ($LASTEXITCODE -ne 0) { Result 'WARN' 'Docker is not running: the containers could not be checked'; return }
    $rows = @(& docker ps --format '{{.Names}}|{{.Ports}}')
    $wide = @($rows | Where-Object { $_ -match '(0\.0\.0\.0|\[::\]|:::)\d' })
    if ($wide.Count -gt 0) { Result 'FAIL' ('a container publishes a port on every address: ' + (($wide | ForEach-Object { ($_ -split '\|')[0] }) -join ', ')) }
    else { Result 'OK' 'no container publishes a port beyond this computer (only the web service on 127.0.0.1)' }
    $names = @($rows | ForEach-Object { ($_ -split '\|')[0] })
    $unknown = @($names | Where-Object { $_ -notmatch '^uniway-(app|db|rest|storage|gateway)-\d+$' -and $_ -notmatch 'ca-export' })
    if ($unknown.Count -gt 0) { Result 'WARN' ('containers that are not part of UniWay: ' + ($unknown -join ', ')) }
}

Safe 'the settings file' {
    if (-not (Test-Path $script:EnvFile)) { Result 'WARN' '.env was not found'; return }
    $bad = @((Get-Acl $script:EnvFile).Access | Where-Object { $_.IdentityReference.Value -match '(^|\\)(Everyone|Users|Authenticated Users)$' -and $_.AccessControlType -eq 'Allow' })
    if ($bad.Count -gt 0) { Result 'FAIL' '.env (it holds every key and password) can be read by ordinary users: run 02-generate-secrets.ps1 again or fix the file permissions' }
    else { Result 'OK' '.env can only be read by administrators and the system' }
}

Safe 'folder permissions' {
    foreach ($sub in 'backups', 'caddy') {
        $p = Join-Path $script:UniwayHome $sub
        if (-not (Test-Path $p)) { continue }
        $bad = @((Get-Acl $p).Access | Where-Object { $_.IdentityReference.Value -match '(^|\\)(Everyone|Users|Authenticated Users)$' -and $_.AccessControlType -eq 'Allow' })
        if ($bad.Count -gt 0) { Result 'WARN' ("{0} can be accessed by ordinary users: run 01-prepare-windows.ps1 again to lock down its permissions" -f $p) }
        else { Result 'OK' ("{0} is restricted to administrators and the system" -f $p) }
    }
}

# ---- what has been happening ------------------------------------------------------------------------------------------------
Write-Step 'Sign-in history'
if (-not $isAdmin) { Write-Warn 'skipped (needs administrator)' }
else {
    Safe 'failed sign-ins' {
        $events = @(Get-WinEvent -FilterXml '<QueryList><Query Id="0" Path="Security"><Select Path="Security">*[System[(EventID=4625) and TimeCreated[timediff(@SystemTime) &lt;= 86400000]]]</Select></Query></QueryList>' -MaxEvents 20000 -ErrorAction SilentlyContinue)
        $ips = @($events | ForEach-Object { $d = @{}; ([xml]$_.ToXml()).Event.EventData.Data | ForEach-Object { $d[$_.Name] = $_.'#text' }; $d['IpAddress'] } | Where-Object { $_ -and -not (Test-PrivateAddress $_) })
        if ($events.Count -eq 0) { Result 'OK' 'no failed sign-ins in the last 24 hours' }
        else {
            $top = ($ips | Group-Object | Sort-Object Count -Descending | Select-Object -First 5 | ForEach-Object { '{0} x{1}' -f $_.Name, $_.Count }) -join ', '
            Result 'WARN' ('{0} failed sign-ins in the last 24 hours, {1} of them from internet addresses. After the remote-access door is closed this should fall to about 0. Top sources: {2}' -f $events.Count, $ips.Count, $(if ($top) { $top } else { 'none from the internet' }))
        }
    }
    Safe 'lockouts' {
        $n = @(Get-WinEvent -FilterXml '<QueryList><Query Id="0" Path="Security"><Select Path="Security">*[System[(EventID=4740) and TimeCreated[timediff(@SystemTime) &lt;= 86400000]]]</Select></Query></QueryList>' -ErrorAction SilentlyContinue).Count
        if ($n -eq 0) { Result 'OK' 'no account was locked out in the last 24 hours' } else { Result 'WARN' ('an account was locked out {0} time(s) in the last 24 hours (someone guessing passwords, or a stored wrong password)' -f $n) }
    }
    Safe 'successful sign-ins from the internet' {
        $xml = '<QueryList><Query Id="0" Path="Security"><Select Path="Security">*[System[(EventID=4624) and TimeCreated[timediff(@SystemTime) &lt;= 604800000]]] and *[EventData[Data[@Name="LogonType"]="10" or Data[@Name="LogonType"]="3"]]</Select></Query></QueryList>'
        $hits = @(Get-WinEvent -FilterXml $xml -MaxEvents 5000 -ErrorAction SilentlyContinue | ForEach-Object {
            $d = @{}; ([xml]$_.ToXml()).Event.EventData.Data | ForEach-Object { $d[$_.Name] = $_.'#text' }
            if ($d['IpAddress'] -and -not (Test-PrivateAddress $d['IpAddress'])) {
                [pscustomobject]@{ Time = $_.TimeCreated.ToString('yyyy-MM-dd HH:mm'); Type = $d['LogonType']; User = $(if ($d['TargetUserName'] -eq $script:adminName) { '(admin)' } else { $d['TargetUserName'] }); IP = $d['IpAddress'] } } })
        if ($hits.Count -eq 0) { Result 'OK' 'no successful network or Remote Desktop sign-in from an internet address in the last 7 days' }
        else {
            Result 'FAIL' ('{0} successful sign-in(s) from internet addresses in the last 7 days. If one of them is not you, treat the computer as broken into (see the guide, "if it is broken into")' -f $hits.Count)
            $hits | Select-Object -First 8 | ForEach-Object { Info ('{0}  type {1}  {2}  from {3}' -f $_.Time, $_.Type, $_.User, $_.IP) }
        }
    }
    Safe 'security log size' {
        $mb = [math]::Round((Get-WinEvent -ListLog Security).MaximumSizeInBytes / 1MB)
        if ($mb -lt 128) { Result 'WARN' ('the security log keeps only {0} MB: a flood of attacks can push the evidence out (wevtutil sl Security /ms:268435456)' -f $mb) } else { Result 'OK' ('the security log keeps {0} MB' -f $mb) }
    }
}

# ---- keeping up to date and keeping copies ------------------------------------------------------------------------------
Write-Step 'Protection, updates and backups'
Safe 'antivirus' {
    $mp = Get-MpComputerStatus
    if (-not $mp.RealTimeProtectionEnabled) { Result 'FAIL' 'Microsoft Defender real-time protection is OFF' }
    elseif ($mp.AntivirusSignatureAge -gt 3) { Result 'WARN' ('the antivirus definitions are {0} days old (Update-MpSignature)' -f $mp.AntivirusSignatureAge) }
    else { Result 'OK' 'Microsoft Defender is on and up to date' }
}
Safe 'windows updates' {
    $last = Get-HotFix | Where-Object { $_.InstalledOn } | Sort-Object InstalledOn -Descending | Select-Object -First 1
    if (-not $last) { Result 'WARN' 'could not read the date of the last Windows update' }
    else {
        $days = [int]((Get-Date) - $last.InstalledOn).TotalDays
        if ($days -gt 45) { Result 'WARN' ('the last Windows update was installed {0} days ago: install the pending updates (Settings > Windows Update)' -f $days) }
        else { Result 'OK' ('the last Windows update was installed {0} days ago' -f $days) }
    }
}
Safe 'backups' {
    $dir = Join-Path $script:UniwayHome 'backups\db'
    $newest = Get-ChildItem -Path $dir -Filter 'uniway-db-*.dump' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $newest) { Result 'FAIL' 'no database backup was found'; return }
    $hours = [int]((Get-Date) - $newest.LastWriteTime).TotalHours
    if ($hours -gt 36) { Result 'FAIL' ('the newest backup is {0} hours old: the nightly backup is not running (check the UniWay-Backup scheduled task)' -f $hours) }
    else { Result 'OK' ('the newest backup is {0} hours old' -f $hours) }
    $log = Get-ChildItem -Path (Join-Path $script:UniwayHome 'logs') -Filter 'backup-*.log' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($log) {
        $tail = @(Get-Content -Path $log.FullName -Tail 40)
        if ($tail | Where-Object { $_ -match 'copied to Google Drive' }) { Result 'OK' 'the backup is also copied (encrypted) to Google Drive' }
        else { Result 'WARN' 'the latest backups were not copied to Google Drive (is the gdrive-crypt remote set up?)' }
    }
    Info 'reminder: keep a third copy on an external disk that is NOT plugged in all the time, so a thief with the Drive login cannot delete every copy'
}

Write-Host ""
if ($script:fails -eq 0 -and $script:warns -eq 0) { Write-Host 'SECURITY: nothing to fix.' -ForegroundColor Green }
elseif ($script:fails -eq 0) { Write-Host ('SECURITY: {0} thing(s) to look at (WARN). Nothing is critical.' -f $script:warns) -ForegroundColor Yellow }
else { Write-Host ('SECURITY: {0} problem(s) to fix first (FAIL), {1} to look at (WARN).' -f $script:fails, $script:warns) -ForegroundColor Red; exit 1 }
