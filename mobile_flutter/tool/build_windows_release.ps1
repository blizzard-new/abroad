param(
    [Parameter(Mandatory = $true)]
    [string]$ApiBaseUrl,
    [string]$FlutterPath = "$env:USERPROFILE\development\flutter\bin\flutter.bat",
    [string]$MirrorPath = "$env:USERPROFILE\development\exchange_guide_flutter_release_nav"
)

$ErrorActionPreference = "Stop"

$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$allowedRoot = [System.IO.Path]::GetFullPath((Join-Path $env:USERPROFILE "development"))
$mirrorRoot = [System.IO.Path]::GetFullPath($MirrorPath)

if (-not $mirrorRoot.StartsWith($allowedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "MirrorPath must stay inside $allowedRoot"
}
if ($mirrorRoot.TrimEnd('\') -eq $allowedRoot.TrimEnd('\')) {
    throw "MirrorPath cannot be the development root itself"
}
if (-not (Test-Path -LiteralPath $FlutterPath)) {
    throw "Flutter was not found at $FlutterPath"
}

New-Item -ItemType Directory -Force -Path $mirrorRoot | Out-Null

robocopy $projectRoot $mirrorRoot /MIR `
    /XD build .dart_tool .gradle .idea artifacts ephemeral `
    /XF *.iml | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw "Project mirror failed with robocopy exit code $LASTEXITCODE"
}

Push-Location $mirrorRoot
try {
    & $FlutterPath pub get
    if ($LASTEXITCODE -ne 0) { throw "flutter pub get failed" }

    & $FlutterPath analyze --no-pub
    if ($LASTEXITCODE -ne 0) { throw "flutter analyze failed" }

    & $FlutterPath test --no-pub
    if ($LASTEXITCODE -ne 0) { throw "flutter test failed" }

    & $FlutterPath build apk --release "--dart-define=API_BASE_URL=$ApiBaseUrl"
    if ($LASTEXITCODE -ne 0) { throw "flutter build apk failed" }
}
finally {
    Pop-Location
}

$sourceApk = Join-Path $mirrorRoot "build\app\outputs\flutter-apk\app-release.apk"
$artifactDirectory = Join-Path $projectRoot "artifacts"
$targetApk = Join-Path $artifactDirectory "exchange-guide-flutter-phone.apk"

New-Item -ItemType Directory -Force -Path $artifactDirectory | Out-Null
Copy-Item -LiteralPath $sourceApk -Destination $targetApk -Force

$hash = Get-FileHash -LiteralPath $targetApk -Algorithm SHA256
Write-Output "APK: $targetApk"
Write-Output "SHA256: $($hash.Hash)"
