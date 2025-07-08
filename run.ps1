Write-Host "Starting Eligendo Data Downloader..." -ForegroundColor Green
Write-Host ""

# Add Node.js to PATH for this session
$env:PATH += ";C:\Users\ficcadv2\node-js"

# Compile TypeScript
Write-Host "Compiling TypeScript..." -ForegroundColor Yellow
& node node_modules\typescript\lib\tsc.js

if ($LASTEXITCODE -ne 0) {
    Write-Host "Compilation failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Compilation successful!" -ForegroundColor Green
Write-Host ""

# Run the main application
Write-Host "Running main application..." -ForegroundColor Yellow
& node dist\main.js

Write-Host ""
Write-Host "Application finished. Press Enter to exit..." -ForegroundColor Green
Read-Host
