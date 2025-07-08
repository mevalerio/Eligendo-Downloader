# 🚀 GitHub Publication Script

Write-Host "🇮🇹 Eligendo Data Downloader - GitHub Publication" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$ProjectName = "eligendo-data-downloader"
$ProjectDescription = "A comprehensive TypeScript-based tool for downloading and analyzing Italian municipal election data"

Write-Host "📋 Pre-Publication Checklist" -ForegroundColor Magenta
Write-Host "=============================" -ForegroundColor Magenta

# Function to ask user for input
function Get-UserInput {
    param([string]$Prompt, [string]$Default = "")
    
    if ($Default) {
        $input = Read-Host "$Prompt [$Default]"
        if ([string]::IsNullOrWhiteSpace($input)) { return $Default }
        return $input
    } else {
        return Read-Host $Prompt
    }
}

# Get user information
Write-Host "👤 GitHub User Information" -ForegroundColor Yellow
$GitHubUsername = Get-UserInput "Enter your GitHub username"
$GitHubEmail = Get-UserInput "Enter your GitHub email"
$AuthorName = Get-UserInput "Enter your full name" $GitHubUsername

if ([string]::IsNullOrWhiteSpace($GitHubUsername)) {
    Write-Host "❌ GitHub username is required!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔧 Updating Configuration Files..." -ForegroundColor Yellow

# Update package.json with user information
$packageJsonPath = "package.json"
$packageJson = Get-Content $packageJsonPath | ConvertFrom-Json

$packageJson.repository.url = "https://github.com/$GitHubUsername/eligendo-data-downloader.git"
$packageJson.homepage = "https://github.com/$GitHubUsername/eligendo-data-downloader#readme"
$packageJson.bugs.url = "https://github.com/$GitHubUsername/eligendo-data-downloader/issues"
$packageJson.author = "$AuthorName <$GitHubEmail>"

$packageJson | ConvertTo-Json -Depth 10 | Set-Content $packageJsonPath
Write-Host "✅ Updated package.json with your GitHub information" -ForegroundColor Green

# Update README.md badges
$readmePath = "README.md"
$readmeContent = Get-Content $readmePath -Raw
$readmeContent = $readmeContent -replace "yourusername", $GitHubUsername
$readmeContent = $readmeContent -replace "YOURUSERNAME", $GitHubUsername
Set-Content $readmePath $readmeContent
Write-Host "✅ Updated README.md with your GitHub username" -ForegroundColor Green

Write-Host ""
Write-Host "🔍 Running Pre-Publication Tests..." -ForegroundColor Yellow

# Test TypeScript compilation
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

# Test municipal data
try {
    $municipalData = Get-Content "data\municipal-election-data.json" | ConvertFrom-Json
    Write-Host "✅ Municipal data valid ($($municipalData.municipalities.Count) cities)" -ForegroundColor Green
} catch {
    Write-Host "❌ Municipal data invalid: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📝 Git Repository Setup" -ForegroundColor Magenta
Write-Host "=======================" -ForegroundColor Magenta

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "🔧 Initializing Git repository..." -ForegroundColor Yellow
    git init
    git branch -M main
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "✅ Git repository already exists" -ForegroundColor Green
}

# Configure git user (if not already configured)
$gitUserName = git config user.name
$gitUserEmail = git config user.email

if ([string]::IsNullOrWhiteSpace($gitUserName)) {
    git config user.name $AuthorName
    Write-Host "✅ Set git user.name to '$AuthorName'" -ForegroundColor Green
}

if ([string]::IsNullOrWhiteSpace($gitUserEmail)) {
    git config user.email $GitHubEmail
    Write-Host "✅ Set git user.email to '$GitHubEmail'" -ForegroundColor Green
}

Write-Host ""
Write-Host "📦 Creating Git Commit" -ForegroundColor Yellow
Write-Host "======================" -ForegroundColor Yellow

# Add all files
git add .

# Create commit
$commitMessage = @"
🇮🇹 Initial release: Eligendo Data Downloader v1.0.0

✨ Features:
- Municipal election data processing for Italian cities
- Advanced query system with TypeScript API
- PowerShell integration for Windows users
- Geographic breakdown by Province and Region
- Mock data for Milano, Roma, and Napoli
- Comprehensive documentation and examples

🔧 Technical:
- TypeScript-first architecture
- Multiple access methods (CLI, API, PowerShell)
- Statistical analysis and winner determination
- Extensible data processing pipeline
- GitHub Actions CI/CD setup
- Professional documentation structure

📚 Documentation:
- Complete API reference
- Getting started guide
- Contributing guidelines
- Security policy
- Publication guide

🎯 Ready for community use and contributions!
"@

git commit -m $commitMessage
Write-Host "✅ Git commit created successfully" -ForegroundColor Green

Write-Host ""
Write-Host "🌐 GitHub Repository Instructions" -ForegroundColor Magenta
Write-Host "=================================" -ForegroundColor Magenta

Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Create GitHub Repository:" -ForegroundColor White
Write-Host "   • Go to https://github.com/new" -ForegroundColor Gray
Write-Host "   • Repository name: eligendo-data-downloader" -ForegroundColor Gray
Write-Host "   • Description: $ProjectDescription" -ForegroundColor Gray
Write-Host "   • Make it Public ✅" -ForegroundColor Gray
Write-Host "   • DON'T initialize with README (we have one)" -ForegroundColor Gray
Write-Host ""

Write-Host "2. Add Remote and Push:" -ForegroundColor White
Write-Host "   Copy and run these commands:" -ForegroundColor Gray
Write-Host ""
Write-Host "   git remote add origin https://github.com/$GitHubUsername/eligendo-data-downloader.git" -ForegroundColor Green
Write-Host "   git push -u origin main" -ForegroundColor Green
Write-Host ""

Write-Host "3. Create Release:" -ForegroundColor White
Write-Host "   git tag -a v1.0.0 -m 'Release v1.0.0: Initial municipal data support'" -ForegroundColor Green
Write-Host "   git push origin v1.0.0" -ForegroundColor Green
Write-Host ""

Write-Host "4. GitHub Repository Setup:" -ForegroundColor White
Write-Host "   • Enable Issues for bug reports" -ForegroundColor Gray
Write-Host "   • Enable Discussions for community questions" -ForegroundColor Gray
Write-Host "   • Add topics: italian-elections, typescript, municipal-data, italy" -ForegroundColor Gray
Write-Host "   • Create GitHub Release with description from CHANGELOG.md" -ForegroundColor Gray
Write-Host ""

Write-Host "📊 Repository Statistics:" -ForegroundColor Cyan
$sourceFiles = (Get-ChildItem -Path "src" -Recurse -Filter "*.ts").Count
$docFiles = (Get-ChildItem -Path "docs" -Filter "*.md").Count
$scriptFiles = (Get-ChildItem -Filter "*.ps1").Count
$dataFiles = (Get-ChildItem -Path "data" -Filter "*.json").Count

Write-Host "   • TypeScript source files: $sourceFiles" -ForegroundColor White
Write-Host "   • Documentation files: $docFiles" -ForegroundColor White
Write-Host "   • PowerShell scripts: $scriptFiles" -ForegroundColor White
Write-Host "   • Data files: $dataFiles" -ForegroundColor White

Write-Host ""
Write-Host "🎉 Your repository is ready for GitHub!" -ForegroundColor Green
Write-Host ""
Write-Host "Repository URL: https://github.com/$GitHubUsername/eligendo-data-downloader" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to open GitHub in your browser..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Open GitHub in browser
Start-Process "https://github.com/new"

Write-Host ""
Write-Host "🚀 Happy publishing! Welcome to the open source community! 🇮🇹" -ForegroundColor Green
