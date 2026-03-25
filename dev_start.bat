@echo off
set API_PORT=8000
set FRONTEND_PORT=4173
echo ===================================================
echo       Heimdall Development Environment
echo ===================================================
echo.
echo 1. Starting Backend (FastAPI :%API_PORT%)...
start "Heimdall Backend" cmd /k "call venv\Scripts\activate & set HEIMDALL_API_PORT=%API_PORT% & python -m uvicorn app.main:app --reload --port %API_PORT%"

echo 2. Starting Frontend (Vite :%FRONTEND_PORT%)...
start "Heimdall Frontend" cmd /k "cd frontend & set HEIMDALL_API_PORT=%API_PORT% & set HEIMDALL_FRONTEND_PORT=%FRONTEND_PORT% & npm run dev"

echo.
echo ===================================================
echo Services are starting...
echo Frontend: http://localhost:%FRONTEND_PORT%
echo Backend:  http://localhost:%API_PORT%/docs
echo ===================================================
echo.
echo Press any key to exit this launcher (services will keep running).
pause
