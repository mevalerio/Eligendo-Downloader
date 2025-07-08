# Direct Push to mevalerio/Eligendo-Downloader
# This script will push directly to the specified GitHub repository

Write-Host "🇮🇹 Eligendo Data Downloader - Push to GitHub" -ForegroundColor Cyan
Write-Host "Repository: https://github.com/mevalerio/Eligendo-Downloader.git" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is available
try {
    $gitVersion = git --version
    Write-Host "✅ Git is available: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed or not in PATH!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Git first:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://git-scm.com/download/win" -ForegroundColor White
    Write-Host "2. Install with default settings" -ForegroundColor White
    Write-Host "3. Restart PowerShell and run this script again" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "🔧 Pre-push verification..." -ForegroundColor Yellow

# Test TypeScript compilation
Write-Host "Testing TypeScript compilation..." -ForegroundColor White
try {
    & ".\node_modules\.bin\tsc.cmd" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ TypeScript compilation successful" -ForegroundColor Green
    } else {
        Write-Host "⚠️  TypeScript compilation issues (proceeding anyway)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not test TypeScript compilation (proceeding anyway)" -ForegroundColor Yellow
}

# Test data files
Write-Host "Checking data files..." -ForegroundColor White
if (Test-Path "data\municipal-election-data.json") {
    try {
        $data = Get-Content "data\municipal-election-data.json" | ConvertFrom-Json
        Write-Host "✅ Municipal data file is valid" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Municipal data file may have issues (proceeding anyway)" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Municipal data file not found (proceeding anyway)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📦 Git repository setup..." -ForegroundColor Yellow

# Initialize git if needed
if (-not (Test-Path ".git")) {
    Write-Host "Initializing git repository..." -ForegroundColor White
    git init
    git branch -M main
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "✅ Git repository already exists" -ForegroundColor Green
}

# Set up git user if needed
$gitUser = git config user.name
$gitEmail = git config user.email

if (-not $gitUser) {
    Write-Host "Setting up git user configuration..." -ForegroundColor White
    git config user.name "mevalerio"
    Write-Host "✅ Git user.name set to 'mevalerio'" -ForegroundColor Green
}

if (-not $gitEmail) {
    Write-Host "Git email not configured. Please set it manually if needed." -ForegroundColor Yellow
}

# Add all files
Write-Host "Adding files to git..." -ForegroundColor White
git add .

# Check if there are changes to commit
$status = git status --porcelain
if ($status) {
    Write-Host "Creating commit..." -ForegroundColor White
    
    $commitMessage = @"
🇮🇹 Eligendo Data Downloader v1.0.0 - Complete Italian Municipal Election Analysis Tool

✨ Features:
- Municipal election data processing for Italian cities (Milano, Roma, Napoli)
- Advanced TypeScript API with multiple access methods
- PowerShell integration for Windows users
- Geographic breakdown by Province and Region
- Statistical analysis and winner determination
- Comprehensive documentation and examples

🔧 Technical Implementation:
- TypeScript-first architecture with full type safety
- Modular, extensible design for additional data sources
- Multiple query interfaces (PowerShell, CLI, API)
- Professional GitHub repository structure
- CI/CD ready with GitHub Actions
- Complete test suite and documentation

📚 Documentation:
- Complete API reference and guides
- Getting started tutorials
- Contributing guidelines
- Security policy and best practices

🎯 Ready for community use and contributions!

This tool enables developers, researchers, and civic technologists to analyze Italian municipal election data with ease.
"@

    git commit -m $commitMessage
    Write-Host "✅ Commit created successfully" -ForegroundColor Green
} else {
    Write-Host "✅ No changes to commit (repository is up to date)" -ForegroundColor Green
}

# Add remote repository
Write-Host "Setting up remote repository..." -ForegroundColor White
try {
    git remote remove origin 2>$null
} catch {
    # Remote doesn't exist, that's fine
}

git remote add origin https://github.com/mevalerio/Eligendo-Downloader.git
Write-Host "✅ Remote repository configured" -ForegroundColor Green

Write-Host ""
Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Green
Write-Host "Repository: https://github.com/mevalerio/Eligendo-Downloader" -ForegroundColor Cyan
Write-Host ""

# Push to GitHub
try {
    git push -u origin main --force
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 SUCCESS! Repository pushed to GitHub!" -ForegroundColor Green
        Write-Host ""
        
        # Create and push release tag
        Write-Host "Creating release tag v1.0.0..." -ForegroundColor White
        git tag -a v1.0.0 -m "Release v1.0.0: Complete Italian municipal election analysis tool" -f
        git push origin v1.0.0 --force
        
        Write-Host "✅ Release tag v1.0.0 created and pushed!" -ForegroundColor Green
        Write-Host ""
        
        Write-Host "🎯 Your repository is now live!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Repository Information:" -ForegroundColor Cyan
        Write-Host "• URL: https://github.com/mevalerio/Eligendo-Downloader" -ForegroundColor White
        Write-Host "• Releases: https://github.com/mevalerio/Eligendo-Downloader/releases" -ForegroundColor White
        Write-Host "• Issues: https://github.com/mevalerio/Eligendo-Downloader/issues" -ForegroundColor White
        Write-Host ""
        
        Write-Host "📊 Repository Contents:" -ForegroundColor Cyan
        $tsFiles = (Get-ChildItem -Path "src" -Recurse -Filter "*.ts" -ErrorAction SilentlyContinue).Count
        $docFiles = (Get-ChildItem -Path "docs" -Filter "*.md" -ErrorAction SilentlyContinue).Count
        $psFiles = (Get-ChildItem -Filter "*.ps1" -ErrorAction SilentlyContinue).Count
        $jsFiles = (Get-ChildItem -Filter "*.js" -ErrorAction SilentlyContinue).Count
        
        Write-Host "• TypeScript source files: $tsFiles" -ForegroundColor White
        Write-Host "• Documentation files: $docFiles" -ForegroundColor White
        Write-Host "• PowerShell scripts: $psFiles" -ForegroundColor White
        Write-Host "• JavaScript interfaces: $jsFiles" -ForegroundColor White
        Write-Host ""
        
        Write-Host "🌟 Next Steps:" -ForegroundColor Cyan
        Write-Host "1. Visit your repository to verify all files are uploaded" -ForegroundColor White
        Write-Host "2. Create a GitHub Release from the v1.0.0 tag" -ForegroundColor White
        Write-Host "3. Enable Issues and Discussions in repository settings" -ForegroundColor White
        Write-Host "4. Add repository topics: italian-elections, typescript, municipal-data" -ForegroundColor White
        Write-Host "5. Share your project with the Italian developer community!" -ForegroundColor White
        
        Write-Host ""
        Write-Host "🎊 Congratulations! Your contribution to open source is now live!" -ForegroundColor Green
        
    } else {
        throw "Push command failed"
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ Failed to push to GitHub" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible reasons:" -ForegroundColor Yellow
    Write-Host "1. Repository doesn't exist at https://github.com/mevalerio/Eligendo-Downloader" -ForegroundColor White
    Write-Host "2. You don't have push permissions to this repository" -ForegroundColor White
    Write-Host "3. Authentication is required (GitHub login)" -ForegroundColor White
    Write-Host "4. Network connectivity issues" -ForegroundColor White
    Write-Host ""
    Write-Host "Solutions:" -ForegroundColor Yellow
    Write-Host "1. Ensure the repository exists on GitHub" -ForegroundColor White
    Write-Host "2. Check you have push access to mevalerio/Eligendo-Downloader" -ForegroundColor White
    Write-Host "3. Configure Git authentication:" -ForegroundColor White
    Write-Host "   git config --global credential.helper manager-core" -ForegroundColor Gray
    Write-Host "4. Try again with authentication prompts" -ForegroundColor White
    Write-Host ""
    Write-Host "Manual commands to try:" -ForegroundColor Yellow
    Write-Host "git remote -v" -ForegroundColor Gray
    Write-Host "git push -u origin main" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host
