# Step 0: is this computer ready to be the server? Read-only: changes nothing.
#   powershell -ExecutionPolicy Bypass -File .\00-check.ps1
. "$PSScriptRoot\lib.ps1"
$problems = 0

function Check([string]$Name, [scriptblock]$Test, [string]$Fix) {
    try {
        $result = & $Test
        if ($result -is [string] -and $result) { Write-Ok ("{0}: {1}" -f $Name, $result); return }
        if ($result -eq $true) { Write-Ok $Name; return }
    } catch { }
    Write-Bad ("{0}. {1}" -f $Name, $Fix)
    $script:problems++
}

Write-Step 'Checking this computer'
Check 'Windows 10/11 (64-bit)' { $os = Get-CimInstance Win32_OperatingSystem; if ($os.OSArchitecture -like '64*') { $os.Caption } } 'Docker Desktop needs 64-bit Windows 10 or 11.'
Check 'Memory at least 16 GB' { $gb = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB); if ($gb -ge 16) { "$gb GB" } } 'The stack needs about 8-16 GB for itself.'
Check 'Free disk on C: at least 100 GB' { $gb = [math]::Round((Get-PSDrive C).Free / 1GB); if ($gb -ge 100) { "$gb GB free" } } 'The program image alone is about 2 GB and the database grows over time.'
Check 'Virtualization is on (needed by WSL2/Docker)' { (Get-CimInstance Win32_ComputerSystem).HypervisorPresent -eq $true } 'Turn on virtualization (SVM/VT-x) in the BIOS, and in Windows features: "Virtual Machine Platform" and "Windows Subsystem for Linux".'
Check 'WSL is installed' { $null = & wsl.exe --status 2>&1; $LASTEXITCODE -eq 0 } 'Run "wsl --install" in an administrator PowerShell, then restart.'
Check 'Docker command exists' { [bool](Get-Command docker -ErrorAction SilentlyContinue) } 'Install Docker Desktop: winget install -e --id Docker.DockerDesktop'
Check 'Docker engine is running' { $null = & docker info 2>&1; $LASTEXITCODE -eq 0 } 'Start Docker Desktop and wait until it says "Engine running".'
Check 'Docker Compose is available' { $v = (& docker compose version 2>&1); if ($LASTEXITCODE -eq 0) { ($v | Select-Object -First 1) } } 'Update Docker Desktop.'
Check 'Git is installed' { [bool](Get-Command git -ErrorAction SilentlyContinue) } 'Install Git: winget install -e --id Git.Git'
Check 'Nothing else is using ports 80 and 443' {
    $busy = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 80, 443 })
    if ($busy.Count -eq 0) { $true } else {
        $busy | ForEach-Object { $p = (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue); Write-Host ("        port {0} is used by {1}" -f $_.LocalPort, $(if ($p) { $p.ProcessName } else { $_.OwningProcess })) }
        $false }
} 'Stop that program (IIS, Skype, another web server) or Caddy cannot get a certificate.'

Write-Step 'Where the next step stands'
if (Test-Path $script:EnvFile) { Write-Ok 'deploy\selfhost\.env exists (secrets already generated)' } else { Write-Warn 'no .env yet - next: 02-generate-secrets.ps1' }
if (Test-Path (Join-Path $script:UniwayHome 'caddy\caddy.exe')) { Write-Ok 'Caddy is installed' } else { Write-Warn 'Caddy not installed yet - step 05' }

Write-Host ""
if ($problems -eq 0) { Write-Host 'All checks passed.' -ForegroundColor Green } else { Write-Host ("{0} check(s) need attention before going on." -f $problems) -ForegroundColor Red; exit 1 }
