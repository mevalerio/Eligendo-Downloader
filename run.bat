@echo off
echo Starting Eligendo Data Downloader...
echo.

REM Add Node.js to PATH for this session
set PATH=%PATH%;C:\Users\ficcadv2\node-js

REM Compile TypeScript
echo Compiling TypeScript...
node node_modules\typescript\lib\tsc.js
if errorlevel 1 (
    echo Compilation failed!
    pause
    exit /b 1
)

echo Compilation successful!
echo.

REM Run the application
echo Running application...
node dist\main.js

echo.
echo Application finished. Press any key to exit...
pause > nul
