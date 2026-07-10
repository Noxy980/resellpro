@echo off
echo Starting ResellPro...
echo.

cd /d "%~dp0"

echo [1/2] Starting backend...
start /B python backend\run.py
timeout /t 3 /nobreak > nul

echo [2/2] Starting desktop app...
cd desktop
if not exist node_modules (
    echo Installing dependencies...
    call npm install
)
call npm run dev
