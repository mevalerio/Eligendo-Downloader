# GitHub Publication - Manual Steps

Write-Host "Eligendo Data Downloader - GitHub Publication" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Get user information
Write-Host "Step 1: Enter Your Information" -ForegroundColor Yellow
$username = Read-Host "Enter your GitHub username"
$email = Read-Host "Enter your email"
$name = Read-Host "Enter your full name"

if (-not $username) {
    Write-Host "GitHub username is required!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 2: Updating package.json..." -ForegroundColor Yellow

# Read and update package.json
$packageContent = Get-Content "package.json" -Raw
$packageContent = $packageContent -replace '"yourusername"', "`"$username`""
$packageContent = $packageContent -replace 'yourusername', $username
$packageContent = $packageContent -replace 'Your Name <your.email@example.com>', "$name <$email>"
Set-Content "package.json" $packageContent

Write-Host "Updated package.json with your information" -ForegroundColor Green

Write-Host ""
Write-Host "Step 3: Updating README.md..." -ForegroundColor Yellow

# Update README
$readmeContent = Get-Content "README.md" -Raw
$readmeContent = $readmeContent -replace 'yourusername', $username
Set-Content "README.md" $readmeContent

Write-Host "Updated README.md with your username" -ForegroundColor Green

Write-Host ""
Write-Host "Step 4: Testing build..." -ForegroundColor Yellow

# Test TypeScript build
try {
    & ".\node_modules\.bin\tsc.cmd"
    Write-Host "TypeScript build successful" -ForegroundColor Green
} catch {
    Write-Host "TypeScript build failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 5: Git setup..." -ForegroundColor Yellow

# Initialize git if needed
if (-not (Test-Path ".git")) {
    git init
    git branch -M main
    Write-Host "Git repository initialized" -ForegroundColor Green
}

# Configure git
git config user.name $name
git config user.email $email

# Create commit
git add .
git commit -m "Initial release: Eligendo Data Downloader v1.0.0

Features:
- Municipal election data processing for Italian cities  
- TypeScript API with multiple access methods
- PowerShell integration for Windows
- Comprehensive documentation"

Write-Host "Git commit created" -ForegroundColor Green

Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "==========" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create GitHub repository:" -ForegroundColor White
Write-Host "   - Go to: https://github.com/new" -ForegroundColor Gray
Write-Host "   - Name: eligendo-data-downloader" -ForegroundColor Gray
Write-Host "   - Description: TypeScript tool for Italian municipal election data" -ForegroundColor Gray
Write-Host "   - Make it Public" -ForegroundColor Gray
Write-Host "   - Do NOT initialize with README" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Push your code:" -ForegroundColor White
Write-Host "   git remote add origin https://github.com/$username/eligendo-data-downloader.git" -ForegroundColor Green
Write-Host "   git push -u origin main" -ForegroundColor Green
Write-Host ""
Write-Host "3. Create release:" -ForegroundColor White
Write-Host "   git tag -a v1.0.0 -m 'Release v1.0.0'" -ForegroundColor Green
Write-Host "   git push origin v1.0.0" -ForegroundColor Green
Write-Host ""
Write-Host "Your repository URL will be:" -ForegroundColor Cyan
Write-Host "https://github.com/$username/eligendo-data-downloader" -ForegroundColor Green
Write-Host ""
Write-Host "Press Enter to open GitHub..." -ForegroundColor Gray
Read-Host
Start-Process "https://github.com/new"
