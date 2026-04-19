@echo off
echo Stopping Heimdall services...

set API_PORT=8000
set FRONTEND_PORT=4173

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%API_PORT%') do (
    taskkill /PID %%a /F 2>nul
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%FRONTEND_PORT%') do (
    taskkill /PID %%a /F 2>nul
)

echo Services stopped.
if /i not "%~1"=="--no-pause" pause
exit /b 0
