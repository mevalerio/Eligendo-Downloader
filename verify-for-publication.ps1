# 🔍 Pre-Publication Verification Script

Write-Host "🇮🇹 Eligendo Data Downloader - Pre-Publication Verification" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$ErrorCount = 0

# Function to test a command and report results
function Test-Command {
    param(
        [string]$Name,
        [scriptblock]$Command,
        [string]$SuccessMessage = "✅ PASSED",
        [string]$FailureMessage = "❌ FAILED"
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow
    
    try {
        $result = & $Command
        if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq $null) {
            Write-Host "$SuccessMessage" -ForegroundColor Green
            return $true
        } else {
            Write-Host "$FailureMessage (Exit code: $LASTEXITCODE)" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "$FailureMessage (Exception: $($_.Exception.Message))" -ForegroundColor Red
        return $false
    }
}

# Function to test file existence
function Test-FileExists {
    param([string]$FilePath, [string]$Description)
    
    Write-Host "Checking: $Description" -ForegroundColor Yellow
    
    if (Test-Path $FilePath) {
        Write-Host "✅ Found: $FilePath" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ Missing: $FilePath" -ForegroundColor Red
        return $false
    }
}

Write-Host "📋 1. File Structure Verification" -ForegroundColor Magenta
Write-Host "================================" -ForegroundColor Magenta

$RequiredFiles = @(
    @{ Path = "README.md"; Description = "Main README file" },
    @{ Path = "LICENSE"; Description = "MIT License file" },
    @{ Path = "package.json"; Description = "Package configuration" },
    @{ Path = "tsconfig.json"; Description = "TypeScript configuration" },
    @{ Path = ".gitignore"; Description = "Git ignore file" },
    @{ Path = "CHANGELOG.md"; Description = "Changelog file" },
    @{ Path = "SECURITY.md"; Description = "Security policy" },
    @{ Path = "PUBLISH_GUIDE.md"; Description = "Publication guide" },
    @{ Path = "src\main.ts"; Description = "Main entry point" },
    @{ Path = "src\eligendo-api.ts"; Description = "API interface" },
    @{ Path = "src\services\municipal-query-service.ts"; Description = "Query service" },
    @{ Path = "data\municipal-election-data.json"; Description = "Municipal data" },
    @{ Path = "docs\API_REFERENCE.md"; Description = "API documentation" },
    @{ Path = "docs\GETTING_STARTED.md"; Description = "Getting started guide" },
    @{ Path = "docs\CONTRIBUTING.md"; Description = "Contributing guidelines" },
    @{ Path = "demo-query.ps1"; Description = "PowerShell demo script" },
    @{ Path = "run-municipal-demo.ps1"; Description = "Municipal demo script" }
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-FileExists $File.Path $File.Description)) {
        $ErrorCount++
    }
}

Write-Host ""
Write-Host "🔧 2. TypeScript Compilation" -ForegroundColor Magenta
Write-Host "============================" -ForegroundColor Magenta

if (-not (Test-Command "TypeScript Compilation" { .\node_modules\.bin\tsc.cmd } "✅ TypeScript compiled successfully" "❌ TypeScript compilation failed")) {
    $ErrorCount++
}

Write-Host ""
Write-Host "📊 3. Demo Script Testing" -ForegroundColor Magenta
Write-Host "=========================" -ForegroundColor Magenta

if (-not (Test-Command "Municipal Demo" { .\run-municipal-demo.ps1 } "✅ Municipal demo executed successfully" "❌ Municipal demo failed")) {
    $ErrorCount++
}

if (-not (Test-Command "Query Demo - Milano" { .\demo-query.ps1 Milano } "✅ Milano query executed successfully" "❌ Milano query failed")) {
    $ErrorCount++
}

Write-Host ""
Write-Host "📄 4. Documentation Verification" -ForegroundColor Magenta
Write-Host "================================" -ForegroundColor Magenta

# Check README contains required sections
$readme = Get-Content "README.md" -Raw
$requiredSections = @("Features", "Quick Start", "Usage", "API", "Installation")

foreach ($section in $requiredSections) {
    if ($readme -match $section) {
        Write-Host "✅ README contains '$section' section" -ForegroundColor Green
    } else {
        Write-Host "❌ README missing '$section' section" -ForegroundColor Red
        $ErrorCount++
    }
}

# Check package.json has repository info
$packageJson = Get-Content "package.json" | ConvertFrom-Json
if ($packageJson.repository -and $packageJson.repository.url) {
    Write-Host "✅ Package.json has repository URL" -ForegroundColor Green
} else {
    Write-Host "⚠️  Package.json missing repository URL (needs update before publishing)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🗂️ 5. Data Verification" -ForegroundColor Magenta
Write-Host "=======================" -ForegroundColor Magenta

try {
    $municipalData = Get-Content "data\municipal-election-data.json" | ConvertFrom-Json
    Write-Host "✅ Municipal data JSON is valid" -ForegroundColor Green
    Write-Host "📊 Found $($municipalData.Count) municipalities" -ForegroundColor Cyan
    
    $cities = $municipalData | Select-Object -ExpandProperty municipality
    Write-Host "🏛️  Cities: $($cities -join ', ')" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Municipal data JSON is invalid" -ForegroundColor Red
    $ErrorCount++
}

Write-Host ""
Write-Host "🔒 6. Security Check" -ForegroundColor Magenta
Write-Host "===================" -ForegroundColor Magenta

# Check for sensitive files that shouldn't be committed
$sensitivePatterns = @("*.key", "*.pem", ".env", "secrets.*", "config/production.*")
$foundSensitive = $false

foreach ($pattern in $sensitivePatterns) {
    $files = Get-ChildItem -Path "." -Recurse -Force -Name $pattern -ErrorAction SilentlyContinue
    if ($files) {
        Write-Host "⚠️  Found potentially sensitive files: $($files -join ', ')" -ForegroundColor Yellow
        $foundSensitive = $true
    }
}

if (-not $foundSensitive) {
    Write-Host "✅ No sensitive files detected" -ForegroundColor Green
}

# Check .gitignore exists and has basic patterns
$gitignore = Get-Content ".gitignore" -Raw -ErrorAction SilentlyContinue
if ($gitignore -match "node_modules" -and $gitignore -match "\.env") {
    Write-Host "✅ .gitignore has essential patterns" -ForegroundColor Green
} else {
    Write-Host "⚠️  .gitignore may be missing important patterns" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Final Report" -ForegroundColor Magenta
Write-Host "===============" -ForegroundColor Magenta

if ($ErrorCount -eq 0) {
    Write-Host "🎉 ALL CHECKS PASSED! Ready for GitHub publication!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Update package.json with your GitHub username" -ForegroundColor White
    Write-Host "2. Follow the PUBLISH_GUIDE.md instructions" -ForegroundColor White
    Write-Host "3. Create your GitHub repository" -ForegroundColor White
    Write-Host "4. Push your code and create a release" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 Your Eligendo Data Downloader is ready to go live!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Found $ErrorCount issue(s) that should be fixed before publication" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please review the errors above and fix them before publishing." -ForegroundColor White
}

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
