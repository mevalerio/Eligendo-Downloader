# 🔍 Simple Pre-Publication Check

Write-Host "🇮🇹 Eligendo Data Downloader - Publication Check" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Test TypeScript compilation
Write-Host "🔧 Testing TypeScript compilation..." -ForegroundColor Yellow
try {
    & ".\node_modules\.bin\tsc.cmd"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ TypeScript compilation successful" -ForegroundColor Green
    } else {
        Write-Host "❌ TypeScript compilation failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ TypeScript compilation error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test data file
Write-Host "📊 Testing data file..." -ForegroundColor Yellow
try {
    $data = Get-Content "data\municipal-election-data.json" | ConvertFrom-Json
    Write-Host "✅ Municipal data file is valid ($($data.municipalities.Count) cities)" -ForegroundColor Green
} catch {
    Write-Host "❌ Municipal data file is invalid: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test demo script
Write-Host "🎯 Testing demo script..." -ForegroundColor Yellow
try {
    & ".\run-municipal-demo.ps1"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Demo script works correctly" -ForegroundColor Green
    } else {
        Write-Host "❌ Demo script failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Demo script error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 ALL CHECKS PASSED! Ready for GitHub publication!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Update package.json with your GitHub username" -ForegroundColor White
Write-Host "2. Follow PUBLISH_GUIDE.md for GitHub setup" -ForegroundColor White
Write-Host "3. Create repository and push code" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Your project is ready to go live!" -ForegroundColor Green
