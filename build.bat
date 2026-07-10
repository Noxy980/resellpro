@echo off
echo ========================================
echo   ResellPro - Build Windows Installer
echo ========================================
echo.

cd /d "%~dp0desktop"

echo [1/3] Installation des dependances...
call npm install
if errorlevel 1 goto :error

echo [2/3] Compilation de l'application...
call npm run build
if errorlevel 1 goto :error

echo [3/3] Creation de l'installateur .exe...
call npm run dist:win
if errorlevel 1 goto :error

echo.
echo ========================================
echo   Build termine !
echo   Installateur : desktop\release\
echo ========================================
pause
exit /b 0

:error
echo.
echo ERREUR lors du build. Verifiez que Node.js et Python sont installes.
pause
exit /b 1
