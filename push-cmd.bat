@echo off
echo.
echo ===============================================
echo   Push Eligendo Data Downloader to GitHub
echo   Repository: mevalerio/Eligendo-Downloader
echo ===============================================
echo.

REM Navigate to the project directory
cd /d "c:\Users\ficcadv2\Downloads\eligendo-data-downloader"

echo Step 1: Initialize Git repository...
git init
git branch -M main

echo.
echo Step 2: Configure Git user...
git config user.name "mevalerio"
git config user.email "your.email@example.com"

echo.
echo Step 3: Add all files...
git add .

echo.
echo Step 4: Create initial commit...
git commit -m "Initial release: Eligendo Data Downloader v1.0.0 - Complete Italian Municipal Election Analysis Tool"

echo.
echo Step 5: Add remote repository...
git remote add origin https://github.com/mevalerio/Eligendo-Downloader.git

echo.
echo Step 6: Push to GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS! Creating release tag...
    git tag -a v1.0.0 -m "Release v1.0.0: Initial municipal election data support"
    git push origin v1.0.0
    echo.
    echo Repository is now live at:
    echo https://github.com/mevalerio/Eligendo-Downloader
) else (
    echo.
    echo Push failed. You may need to authenticate with GitHub.
    echo Try the commands manually or check repository permissions.
)

echo.
pause
