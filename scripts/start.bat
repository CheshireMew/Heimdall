@echo off
chcp 65001 >nul
set API_PORT=8000
set FRONTEND_PORT=4173
echo ======================================================================
echo                     Heimdall Startup Script
echo ======================================================================
echo.

:: Check if backend is already running
netstat -ano | findstr ":%API_PORT%" >nul
if %errorlevel% equ 0 (
    echo [WARNING] Port %API_PORT% is already in use. Backend might be running.
    echo.
)

:: Check if frontend is already running
netstat -ano | findstr ":%FRONTEND_PORT%" >nul
if %errorlevel% equ 0 (
    echo [WARNING] Port %FRONTEND_PORT% is already in use. Frontend might be running.
    echo.
)

echo [Step 1/3] Starting Backend (FastAPI)...
echo Backend will run on: http://localhost:%API_PORT%
echo API Documentation: http://localhost:%API_PORT%/docs
echo.

:: Start backend in new window
start "Heimdall Backend" cmd /k "cd /d %~dp0.. && set HEIMDALL_API_PORT=%API_PORT% && python -m uvicorn app.main:app --reload --reload-dir app --reload-dir config --reload-dir utils --reload-exclude data/* --reload-exclude logs/* --reload-exclude frontend/dist/* --port %API_PORT%"

:: Wait a bit for backend to start
timeout /t 3 /nobreak >nul

echo [Step 2/3] Starting Frontend (Vue + Vite)...
echo Frontend will run on: http://localhost:%FRONTEND_PORT%
echo.

:: Check if node_modules exists
if not exist "%~dp0..\frontend\node_modules" (
    echo [INFO] node_modules not found. Running npm install...
    cd /d %~dp0..\frontend
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] npm install failed. Please check your Node.js installation.
        pause
        exit /b 1
    )
)

:: Start frontend in new window
start "Heimdall Frontend" cmd /k "cd /d %~dp0..\frontend && set HEIMDALL_API_PORT=%API_PORT% && set HEIMDALL_FRONTEND_PORT=%FRONTEND_PORT% && npm run dev"

:: Wait for services to initialize
echo.
echo [Step 3/3] Waiting for services to start...
timeout /t 5 /nobreak >nul

echo.
echo ======================================================================
echo                         Startup Complete!
echo ======================================================================
echo.
echo Services:
echo   Backend:  http://localhost:%API_PORT%/docs
echo   Frontend: http://localhost:%FRONTEND_PORT%
echo.
echo Press any key to open browser...
pause >nul

:: Open browser
start http://localhost:%FRONTEND_PORT%

echo.
echo To stop services, close the Backend and Frontend windows.
echo.
