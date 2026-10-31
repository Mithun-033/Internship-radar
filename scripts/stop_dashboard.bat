@echo off
echo ========================================================
echo Stopping Internship Radar Background Services...
echo ========================================================

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo Terminating PID %%a on port 8000...
    taskkill /F /PID %%a >nul 2>&1
)

echo Internship Radar stopped successfully.
pause
