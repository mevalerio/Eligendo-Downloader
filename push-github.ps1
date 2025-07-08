# Push to GitHub Script
# Repository: https://github.com/mevalerio/Eligendo-Downloader.git

Write-Host "🇮🇹 Eligendo Data Downloader - Push to GitHub" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    $gitVersion = git --version
    Write-Host "✅ Git is installed: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Git first:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://git-scm.com/download/win" -ForegroundColor White
    Write-Host "2. Download and install Git for Windows" -ForegroundColor White
    Write-Host "3. Restart this script" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "🔧 Setting up repository..." -ForegroundColor Yellow

# Navigate to script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Initialize git repository
Write-Host "Initializing git repository..." -ForegroundColor White
try {
    git init 2>$null
    git branch -M main 2>$null
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Repository might already be initialized" -ForegroundColor Yellow
}

# Add all files
Write-Host "Adding files to git..." -ForegroundColor White
git add .

# Check git user configuration
$gitUser = git config user.name
$gitEmail = git config user.email

if (-not $gitUser -or -not $gitEmail) {
    Write-Host ""
    Write-Host "⚙️  Git user configuration needed:" -ForegroundColor Yellow
    
    if (-not $gitUser) {
        $userName = Read-Host "Enter your full name"
        git config user.name $userName
    }
    
    if (-not $gitEmail) {
        $userEmail = Read-Host "Enter your email address"
        git config user.email $userEmail
    }
    
    Write-Host "✅ Git user configured" -ForegroundColor Green
}

# Create commit
Write-Host "Creating initial commit..." -ForegroundColor White
$commitMessage = @"
🇮🇹 Initial release: Eligendo Data Downloader v1.0.0

✨ Features:
- Municipal election data processing for Italian cities
- Advanced TypeScript API with multiple access methods
- PowerShell integration for Windows users
- Geographic breakdown by Province and Region
- Mock data for Milano, Roma, and Napoli
- Comprehensive documentation and examples

🔧 Technical:
- TypeScript-first architecture with full type safety
- Modular, extensible design for additional data sources
- Professional GitHub repository setup
- CI/CD ready with GitHub Actions
- Complete documentation and API reference

🎯 Ready for community use and contributions!
"@

git commit -m $commitMessage

# Add remote repository
Write-Host "Adding remote repository..." -ForegroundColor White
try {
    git remote add origin https://github.com/mevalerio/Eligendo-Downloader.git 2>$null
} catch {
    Write-Host "⚠️  Remote origin might already exist" -ForegroundColor Yellow
}

# Push to GitHub
Write-Host ""
Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Yellow
Write-Host "Repository: https://github.com/mevalerio/Eligendo-Downloader" -ForegroundColor Cyan

try {
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ SUCCESS: Repository pushed to GitHub!" -ForegroundColor Green
        Write-Host ""
        
        # Create release tag
        Write-Host "Creating release tag v1.0.0..." -ForegroundColor White
        git tag -a v1.0.0 -m "Release v1.0.0: Initial municipal election data support"
        git push origin v1.0.0
        
        Write-Host "✅ Release tag v1.0.0 created!" -ForegroundColor Green
        Write-Host ""
        
        Write-Host "🎉 Your repository is now live on GitHub!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Next steps:" -ForegroundColor Cyan
        Write-Host "1. Visit: https://github.com/mevalerio/Eligendo-Downloader" -ForegroundColor White
        Write-Host "2. Create a GitHub Release from the v1.0.0 tag" -ForegroundColor White
        Write-Host "3. Enable Issues and Discussions in repository settings" -ForegroundColor White
        Write-Host "4. Add repository topics: italian-elections, typescript, municipal-data" -ForegroundColor White
        Write-Host ""
        Write-Host "Repository Statistics:" -ForegroundColor Cyan
        $tsFiles = (Get-ChildItem -Path "src" -Recurse -Filter "*.ts" -ErrorAction SilentlyContinue).Count
        $docFiles = (Get-ChildItem -Path "docs" -Filter "*.md" -ErrorAction SilentlyContinue).Count
        $psFiles = (Get-ChildItem -Filter "*.ps1" -ErrorAction SilentlyContinue).Count
        Write-Host "- TypeScript files: $tsFiles" -ForegroundColor White
        Write-Host "- Documentation files: $docFiles" -ForegroundColor White
        Write-Host "- PowerShell scripts: $psFiles" -ForegroundColor White
        
    } else {
        throw "Push failed"
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ Failed to push to GitHub" -ForegroundColor Red
    Write-Host ""
    Write-Host "This might be because:" -ForegroundColor Yellow
    Write-Host "1. You don't have permission to push to the repository" -ForegroundColor White
    Write-Host "2. The repository doesn't exist yet on GitHub" -ForegroundColor White
    Write-Host "3. You need to authenticate with GitHub" -ForegroundColor White
    Write-Host ""
    Write-Host "Please ensure:" -ForegroundColor Yellow
    Write-Host "- The repository exists: https://github.com/mevalerio/Eligendo-Downloader" -ForegroundColor White
    Write-Host "- You have push access to the repository" -ForegroundColor White
    Write-Host "- You're authenticated with GitHub (use 'git config --global credential.helper manager-core')" -ForegroundColor White
}

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host
