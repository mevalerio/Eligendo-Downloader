param(
    [string]$SharedDataDir = $env:ELIGENDO_SHARED_DATA_DIR,
    [string]$LocalDataDir = (Join-Path $env:LOCALAPPDATA "Eligendo"),
    [string]$Python = "python",
    [double]$CheckpointHours = 6.0
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($SharedDataDir)) {
    throw "Set ELIGENDO_SHARED_DATA_DIR to the synced ElectionData folder."
}

$shared = [System.IO.Path]::GetFullPath($SharedDataDir)
$local = [System.IO.Path]::GetFullPath($LocalDataDir)
$database = Join-Path $local "eligendo.sqlite3"
$logs = Join-Path $shared "logs"
New-Item -ItemType Directory -Force -Path $local, $logs | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$transcript = Join-Path $logs "reconcile-$env:COMPUTERNAME-$stamp.log"

Start-Transcript -Path $transcript | Out-Null
try {
    & $Python -m app.data_portability checkout `
        --store $shared --database $database
    if ($LASTEXITCODE -ne 0) { throw "Database checkout failed." }

    if ([string]::IsNullOrWhiteSpace($env:ELIGENDO_REQUEST_INTERVAL_SECONDS)) {
        $env:ELIGENDO_REQUEST_INTERVAL_SECONDS = "0.8"
    }
    & $Python -u -m app.reconcile_all `
        --database $database `
        --checkpoint-store $shared `
        --checkpoint-hours $CheckpointHours
    if ($LASTEXITCODE -ne 0) { throw "Reconciliation failed." }
}
finally {
    Stop-Transcript | Out-Null
}
