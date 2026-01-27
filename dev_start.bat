@echo off
echo ===================================================
echo       Heimdall Development Environment
echo ===================================================
echo.
echo 1. Starting Backend (FastAPI :5001)...
start "Heimdall Backend" cmd /k "call venv\Scripts\activate & python -m uvicorn app.main:app --reload --port 5001"

echo 2. Starting Frontend (Vite :5173)...
start "Heimdall Frontend" cmd /k "cd frontend & npm run dev"

echo.
echo ===================================================
echo Services are starting...
echo 🌍 Frontend: http://localhost:5173
echo 🔌 Backend:  http://localhost:5001/docs
echo ===================================================
echo.
echo Press any key to exit this launcher (services will keep running).
pause
