Write-Host "Starting Eligendo Municipal Election Demo..." -ForegroundColor Green
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

# Run the municipal demo
Write-Host "Running municipal election demo with Italian cities..." -ForegroundColor Yellow
& node dist\municipal-demo.js

Write-Host ""
Write-Host "Municipal demo finished. Check data/municipal-election-data.json for saved results." -ForegroundColor Green
Write-Host "Press Enter to exit..." -ForegroundColor Green
Read-Host
