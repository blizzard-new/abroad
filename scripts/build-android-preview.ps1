param(
    [Parameter(Mandatory=$true)][string]$SigningDirectory,
    [string]$Flutter = "$env:USERPROFILE\development\flutter\bin\flutter.bat",
    [string]$BuildDirectory = "$env:LOCALAPPDATA\UniWayBuild",
    [string]$FirebaseConfig = ''
)
$ErrorActionPreference = 'Stop'
$taskRepo = Split-Path -Parent $PSScriptRoot
$taskSource = Join-Path $taskRepo 'mobile_flutter'
$taskOutput = Join-Path $taskRepo 'output\android'
$taskKey = Join-Path $SigningDirectory 'uniway-preview.p12'
$taskPasswordFile = Join-Path $SigningDirectory 'password.dpapi'
foreach ($taskRequired in @($Flutter,$taskKey,$taskPasswordFile)) {
    if (-not (Test-Path -LiteralPath $taskRequired)) { throw "Required file missing: $taskRequired" }
}
if ($FirebaseConfig) { $FirebaseConfig = (Resolve-Path -LiteralPath $FirebaseConfig).Path }
New-Item -ItemType Directory -Path $BuildDirectory,$taskOutput -Force | Out-Null
# /E copies source without deleting anything. English path avoids analyzer failures
# observed with non-ASCII paths on the tested Windows Flutter toolchain.
& robocopy $taskSource $BuildDirectory /E /XD .dart_tool build .gradle .git /XF local.properties GeneratedPluginRegistrant.java .flutter-plugins .flutter-plugins-dependencies /NFL /NDL /NJH /NJS /NP
if ($LASTEXITCODE -gt 7) { throw 'Source copy failed.' }
$taskFirebaseValues = @{}
if ($FirebaseConfig) {
    $taskFirebaseInput = Get-Content -LiteralPath $FirebaseConfig -Raw | ConvertFrom-Json
    foreach ($taskName in @('FIREBASE_PROJECT_ID','FIREBASE_APP_ID','FIREBASE_API_KEY','FIREBASE_SENDER_ID')) {
        $taskValue = $taskFirebaseInput.$taskName
        if ($taskValue -isnot [string] -or [string]::IsNullOrWhiteSpace($taskValue)) {
            throw "Public Firebase client setting missing: $taskName"
        }
        $taskFirebaseValues[$taskName] = $taskValue
    }
}
# FirebaseInitProvider needs native resources when FCM starts a cold process,
# before the Dart isolate can initialize Firebase. Only public client values go here.
$taskResourceNames = @{
    FIREBASE_PROJECT_ID='project_id'; FIREBASE_APP_ID='google_app_id';
    FIREBASE_API_KEY='google_api_key'; FIREBASE_SENDER_ID='gcm_defaultSenderId'
}
$taskXmlLines = @('<?xml version="1.0" encoding="utf-8"?>','<resources>')
foreach ($taskName in $taskFirebaseValues.Keys) {
    $taskEscaped = [System.Security.SecurityElement]::Escape($taskFirebaseValues[$taskName])
    $taskXmlLines += ('  <string name="{0}" translatable="false">{1}</string>' -f $taskResourceNames[$taskName],$taskEscaped)
}
$taskXmlLines += '</resources>'
$taskXmlLines | Set-Content -LiteralPath (Join-Path $BuildDirectory 'android\app\src\main\res\values\firebase_client.xml') -Encoding utf8
$taskClientDefines = Join-Path $BuildDirectory 'firebase-client-defines.json'
$taskFirebaseValues | ConvertTo-Json | Set-Content -LiteralPath $taskClientDefines -Encoding utf8
$taskSecret = Get-Content -LiteralPath $taskPasswordFile -Raw | ConvertTo-SecureString
$env:UNIWAY_KEYSTORE = $taskKey
$env:UNIWAY_STORE_PASSWORD = [System.Net.NetworkCredential]::new('', $taskSecret).Password
$env:UNIWAY_KEY_PASSWORD = $env:UNIWAY_STORE_PASSWORD
Push-Location $BuildDirectory
try {
    & $Flutter pub get
    if ($LASTEXITCODE -ne 0) { throw 'Dependency resolution failed.' }
    # Keep Flutter's build-time pub step: --no-pub can leave integration_test in
    # the release registrant (flutter/flutter#169336).
    $taskArgs = @('build','apk','--release','--dart-define=API_BASE_URL=https://app.uniway-tw.com/')
    if ($FirebaseConfig) { $taskArgs += "--dart-define-from-file=$taskClientDefines" }
    & $Flutter @taskArgs
    if ($LASTEXITCODE -ne 0) { throw 'APK build failed.' }
    $taskApk = Join-Path $taskOutput 'UniWay-2.1.0-preview.apk'
    Copy-Item -LiteralPath 'build\app\outputs\flutter-apk\app-release.apk' -Destination $taskApk
    $taskHash = (Get-FileHash -LiteralPath $taskApk -Algorithm SHA256).Hash.ToLowerInvariant()
    "$taskHash  UniWay-2.1.0-preview.apk" | Set-Content -LiteralPath (Join-Path $taskOutput 'SHA256SUMS.txt')
    Write-Output "APK: $taskApk"
    Write-Output "SHA256: $taskHash"
} finally {
    Pop-Location
    $env:UNIWAY_STORE_PASSWORD = $null
    $env:UNIWAY_KEY_PASSWORD = $null
    $env:UNIWAY_KEYSTORE = $null
}
