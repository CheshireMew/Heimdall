@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%dev_start.ps1"

if not exist "%PS_SCRIPT%" (
  echo dev_start.ps1 not found: "%PS_SCRIPT%"
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo Launcher failed with exit code %EXIT_CODE%.
)

exit /b %EXIT_CODE%
