@echo off
setlocal
cd /d "%~dp0\.."

echo ========================================================
echo Starting Internship Radar (GPU, AI & Systems)...
echo ========================================================

netstat -ano | findstr :8000 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [INFO] Internship Radar backend is already running on port 8000.
    start "" http://localhost:8000
    exit /b 0
)

echo [INFO] Launching background server and collection engine...
start "Internship Radar Backend" /B python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

:: Wait briefly for server startup
timeout /t 2 /nobreak >nul

echo [INFO] Opening Internship Radar in default browser...
start "" http://localhost:8000

exit /b 0
