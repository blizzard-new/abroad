[CmdletBinding()]
param(
    [string]$BaseUrl = "http://127.0.0.1:11434",
    [string]$ChatModel = "gemma4:12b",
    [string]$EmbeddingModel = "embeddinggemma"
)

$ErrorActionPreference = "Stop"

function Stop-Check {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

try {
    $parsedBaseUrl = [Uri]$BaseUrl
} catch {
    Stop-Check "Ollama base URL is invalid."
}

$allowedHosts = @("127.0.0.1", "::1", "localhost")
if (
    $parsedBaseUrl.Scheme -ne "http" -or
    $parsedBaseUrl.Port -ne 11434 -or
    $allowedHosts -notcontains $parsedBaseUrl.Host -or
    ($parsedBaseUrl.AbsolutePath -notin @("", "/")) -or
    $parsedBaseUrl.UserInfo -or
    $parsedBaseUrl.Query -or
    $parsedBaseUrl.Fragment
) {
    Stop-Check "Ollama must use the fixed loopback endpoint on port 11434."
}

if ($ChatModel -ne "gemma4:12b") {
    Stop-Check "The approved chat model is gemma4:12b."
}
if ($EmbeddingModel -ne "embeddinggemma") {
    Stop-Check "The approved embedding model is embeddinggemma."
}
if ($ChatModel.Contains("cloud") -or $EmbeddingModel.Contains("cloud")) {
    Stop-Check "Cloud model tags are not allowed."
}

$ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
$ollamaExecutable = if ($ollamaCommand) {
    $ollamaCommand.Source
} else {
    Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
}
if (-not (Test-Path -LiteralPath $ollamaExecutable)) {
    Stop-Check "Ollama is not installed for the current user."
}

$versionOutput = (& $ollamaExecutable --version 2>&1 | Out-String).Trim()
$baseApiUrl = $BaseUrl.TrimEnd("/")
try {
    $apiVersion = Invoke-RestMethod -Uri "$baseApiUrl/api/version" -TimeoutSec 5
    $tags = Invoke-RestMethod -Uri "$baseApiUrl/api/tags" -TimeoutSec 10
} catch {
    Stop-Check "Ollama is installed but its loopback API is unavailable."
}

$listeners = @(
    Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalPort -eq 11434 }
)
$unsafeListeners = @(
    $listeners |
        Where-Object { $_.LocalAddress -notin @("127.0.0.1", "::1") }
)
if (-not $listeners) {
    Stop-Check "No Ollama listener was found on port 11434."
}
if ($unsafeListeners) {
    Stop-Check "Ollama is listening beyond loopback; stop it before using the prototype."
}

$modelNames = @(
    $tags.models |
        ForEach-Object {
            if ($_.name) { [string]$_.name }
            elseif ($_.model) { [string]$_.model }
        }
)
$chatPresent = $modelNames -contains $ChatModel
$embeddingPresent = (
    $modelNames -contains $EmbeddingModel -or
    $modelNames -contains "$EmbeddingModel`:latest"
)
if (-not $chatPresent) {
    Stop-Check "The approved chat model is not installed."
}
if (-not $embeddingPresent) {
    Stop-Check "The approved embedding model is not installed."
}

$nvidiaCommand = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if (-not $nvidiaCommand) {
    Stop-Check "nvidia-smi is unavailable; the approved GPU cannot be verified."
}
$gpuRows = @(
    & $nvidiaCommand.Source `
        --query-gpu=name,memory.total,driver_version `
        --format=csv,noheader,nounits 2>$null |
        ForEach-Object {
            $fields = @($_ -split ",", 3 | ForEach-Object { $_.Trim() })
            if ($fields.Count -ne 3 -or $fields[1] -notmatch "^\d+$") {
                Stop-Check "nvidia-smi returned an invalid GPU inventory."
            }
            [pscustomobject]@{
                name = $fields[0]
                memory_total_mib = [int]$fields[1]
                driver_version = $fields[2]
            }
        }
)
$approvedGpu = @(
    $gpuRows |
        Where-Object {
            $_.name -like "*RTX 5060 Ti*" -and $_.memory_total_mib -ge 15000
        }
)
if (-not $approvedGpu) {
    Stop-Check "The approved RTX 5060 Ti with at least 15000 MiB VRAM was not found."
}

$modelStore = Join-Path $env:USERPROFILE ".ollama\models"
$modelStoreDriveRoot = [System.IO.Path]::GetPathRoot($modelStore)
$modelStoreDrive = [System.IO.DriveInfo]::new($modelStoreDriveRoot)
$minimumFreeDiskBytes = 5GB
if (-not $modelStoreDrive.IsReady -or $modelStoreDrive.AvailableFreeSpace -lt $minimumFreeDiskBytes) {
    Stop-Check "The Ollama model drive must have at least 5 GiB free."
}

[pscustomobject]@{
    status = "ready"
    ollama_cli = $versionOutput
    ollama_api = [string]$apiVersion.version
    base_url = $baseApiUrl
    listeners = @($listeners | ForEach-Object { "$($_.LocalAddress):$($_.LocalPort)" })
    chat_model = $ChatModel
    embedding_model = $EmbeddingModel
    installed_models = $modelNames
    gpu = $gpuRows
    model_store = $modelStore
    disk_free_gib = [math]::Round(
        $modelStoreDrive.AvailableFreeSpace / 1GB,
        2
    )
} | ConvertTo-Json -Depth 4
