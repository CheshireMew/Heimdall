@echo off
echo Stopping Heimdall services...

set API_PORT=8000
set FRONTEND_PORT=4173

:: Kill backend (port 8000)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%API_PORT%') do (
    taskkill /PID %%a /F 2>nul
)

:: Kill frontend (port 4173)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%FRONTEND_PORT%') do (
    taskkill /PID %%a /F 2>nul
)

echo Services stopped.
pause
