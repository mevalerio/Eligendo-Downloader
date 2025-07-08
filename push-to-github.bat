@echo off
echo.
echo ===============================================
echo   Eligendo Data Downloader - Push to GitHub
echo ===============================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed!
    echo.
    echo Please install Git first:
    echo 1. Go to: https://git-scm.com/download/win
    echo 2. Download and install Git for Windows
    echo 3. Restart this script
    echo.
    pause
    exit /b 1
)

echo Git is installed. Proceeding with repository setup...
echo.

REM Navigate to project directory
cd /d "%~dp0"

REM Initialize git repository
echo Initializing git repository...
git init
git branch -M main

REM Add all files
echo Adding files to git...
git add .

REM Create commit
echo Creating initial commit...
git commit -m "🇮🇹 Initial release: Eligendo Data Downloader v1.0.0

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

🎯 Ready for community use and contributions!"

REM Add remote repository
echo Adding remote repository...
git remote add origin https://github.com/mevalerio/Eligendo-Downloader.git

REM Push to GitHub
echo Pushing to GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ✅ SUCCESS: Repository pushed to GitHub!
    echo.
    echo Repository URL: https://github.com/mevalerio/Eligendo-Downloader
    echo.
    echo Creating release tag...
    git tag -a v1.0.0 -m "Release v1.0.0: Initial municipal election data support"
    git push origin v1.0.0
    echo.
    echo ✅ Release tag v1.0.0 created!
    echo.
    echo Next steps:
    echo 1. Visit: https://github.com/mevalerio/Eligendo-Downloader
    echo 2. Create a GitHub Release
    echo 3. Enable Issues and Discussions
    echo 4. Add repository topics
    echo.
) else (
    echo.
    echo ❌ ERROR: Failed to push to GitHub
    echo.
    echo This might be because:
    echo 1. You don't have permission to push to the repository
    echo 2. The repository doesn't exist yet
    echo 3. You need to authenticate with GitHub
    echo.
    echo Please check the repository exists and you have access:
    echo https://github.com/mevalerio/Eligendo-Downloader
    echo.
)

pause
