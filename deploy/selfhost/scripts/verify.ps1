# Is everything working? Runs the end-to-end checks inside the stack and, when a real domain is configured, from the outside too.
#   powershell -ExecutionPolicy Bypass -File .\verify.ps1 [-ExpectedIp 1.2.3.4]
param([string]$ExpectedIp = '')
. "$PSScriptRoot\lib.ps1"
$e = Read-EnvFile
$failed = 0

Write-Step 'Inside the stack (web service, database REST door, private storage)'
Invoke-Compose exec -T -e ("SMOKE_ANON_KEY=" + $e['ANON_KEY']) app python /opt/selfhost/smoke.py
if ($LASTEXITCODE -ne 0) { $failed++ }

Write-Step 'Containers'
Invoke-Compose ps --format 'table {{.Service}}\t{{.State}}\t{{.Status}}'

if ($e.Contains('DOMAIN') -and $e['DOMAIN'] -ne 'localhost') {
    $domain = $e['DOMAIN']
    Write-Step ("From the outside: https://{0}" -f $domain)
    try {
        $ips = @(Resolve-DnsName -Name $domain -Type A -ErrorAction Stop | Where-Object { $_.Type -eq 'A' } | ForEach-Object { $_.IPAddress })
        Write-Ok ("DNS: {0} -> {1}" -f $domain, ($ips -join ', '))
        if ($ExpectedIp -and ($ips -notcontains $ExpectedIp)) { Write-Bad ("DNS does not point to {0}" -f $ExpectedIp); $failed++ }
    } catch { Write-Bad ('DNS lookup failed: ' + $_.Exception.Message); $failed++ }
    try {
        $r = Invoke-WebRequest -Uri ("https://{0}/health" -f $domain) -UseBasicParsing -TimeoutSec 30
        Write-Ok ("HTTPS /health = {0} (certificate accepted)" -f $r.StatusCode)
        if ($r.Headers['Strict-Transport-Security']) { Write-Ok 'HSTS header present' } else { Write-Bad 'HSTS header missing'; $failed++ }
    } catch { Write-Bad ('HTTPS request failed: ' + $_.Exception.Message); $failed++ }
    try {
        $http = Invoke-WebRequest -Uri ("http://{0}/health" -f $domain) -UseBasicParsing -TimeoutSec 30 -MaximumRedirection 0 -ErrorAction SilentlyContinue
    } catch { $http = $_.Exception.Response }
    if ($http -and ([int]$http.StatusCode -in 301, 302, 307, 308)) { Write-Ok 'plain http redirects to https' } else { Write-Warn 'could not confirm the http -> https redirect (port 80 reachable?)' }
    Write-Warn 'Not checkable from here: that the router forwards 80/443 from the INTERNET (use an outside port checker) and the upload cap (see the guide).'
} else {
    Write-Warn 'DOMAIN is localhost: only the inside checks were run.'
}

Write-Host ""
if ($failed -eq 0) { Write-Host 'VERIFY: everything passed.' -ForegroundColor Green } else { Write-Host ("VERIFY: {0} area(s) failed - read the FAIL lines above." -f $failed) -ForegroundColor Red; exit 1 }
